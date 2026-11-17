"""
Unit tests for Application Specification Parser and Security Constraints.
"""

import os
import tempfile
from pathlib import Path
from platform_core.engine.parser import parse_and_validate_spec
from platform_core.engine.errors import SpecValidationError


def test_valid_hotel_billing_spec():
    root = Path(__file__).resolve().parent.parent.parent
    spec_file = root / "app.spec.yaml"
    assert spec_file.is_file(), f"Spec file not found at {spec_file}"
    
    spec = parse_and_validate_spec(str(spec_file), workspace_root=str(root))
    assert spec.apiVersion == "platform.enterprise.com/v1"
    assert spec.kind == "Application"
    assert spec.metadata.name == "hotel-billing"
    assert len(spec.spec.components) == 2
    
    backend = next(c for c in spec.spec.components if c.name == "backend")
    assert backend.type == "container-service"
    assert backend.runtime.port == 8082
    assert backend.runtime.health_check.path == "/actuator/health"
    
    frontend = next(c for c in spec.spec.components if c.name == "frontend")
    assert frontend.type == "static-site"
    assert frontend.deployment.adapter == "s3-static"
    assert frontend.build.dist_dir == "dist"
    print("PASS: test_valid_hotel_billing_spec")


def test_reject_path_traversal():
    malicious_yaml = """
apiVersion: platform.enterprise.com/v1
kind: Application
metadata:
  name: malicious-app
  version: "1.0.0"
spec:
  components:
    - name: backend
      type: container-service
      source:
        context: "../../etc/shadow"
      build:
        adapter: dockerfile
      runtime:
        port: 8080
      deployment:
        adapter: ecs
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(malicious_yaml)
        f_path = f.name
        
    try:
        parse_and_validate_spec(f_path)
        assert False, "Expected SpecValidationError for path traversal"
    except SpecValidationError as e:
        assert "context" in str(e) or "path" in str(e).lower()
        print("PASS: test_reject_path_traversal - Rejected relative escape")
    finally:
        os.remove(f_path)


def test_reject_unknown_field():
    unknown_field_yaml = """
apiVersion: platform.enterprise.com/v1
kind: Application
metadata:
  name: bad-app
  version: "1.0.0"
  unauthorized_field: "injected"
spec:
  components:
    - name: backend
      type: container-service
      source:
        context: backend
      build:
        adapter: dockerfile
      runtime:
        port: 8080
      deployment:
        adapter: ecs
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(unknown_field_yaml)
        f_path = f.name
        
    try:
        parse_and_validate_spec(f_path)
        assert False, "Expected SpecValidationError for unauthorized field"
    except SpecValidationError as e:
        print("PASS: test_reject_unknown_field - Rejected unknown field")
    finally:
        os.remove(f_path)


def test_reject_duplicate_port():
    dup_port_yaml = """
apiVersion: platform.enterprise.com/v1
kind: Application
metadata:
  name: bad-app
  version: "1.0.0"
spec:
  components:
    - name: service-a
      type: container-service
      source:
        context: backend
      build:
        adapter: dockerfile
      runtime:
        port: 8080
      deployment:
        adapter: ecs
    - name: service-b
      type: container-service
      source:
        context: backend
      build:
        adapter: dockerfile
      runtime:
        port: 8080
      deployment:
        adapter: ecs
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(dup_port_yaml)
        f_path = f.name
        
    try:
        parse_and_validate_spec(f_path)
        assert False, "Expected SpecValidationError for duplicate port mapping"
    except SpecValidationError as e:
        assert "Duplicate port" in str(e)
        print("PASS: test_reject_duplicate_port - Detected port collision")
    finally:
        os.remove(f_path)


if __name__ == "__main__":
    test_valid_hotel_billing_spec()
    test_reject_path_traversal()
    test_reject_unknown_field()
    test_reject_duplicate_port()
    print("ALL PARSER TESTS PASSED!")
