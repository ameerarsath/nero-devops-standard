"""
NERO Platform - Specification Schema v2 & Validation Tests (A2-SCH-001 - A2-SCH-004)
Tests Pydantic v2 models, JSON Schema 2020-12, backward compatibility, and path confinement.
"""

import os
import tempfile
import unittest
from pathlib import Path

from platform_core.engine.models import ApplicationSpec
from platform_core.engine.parser import (
    parse_and_validate_spec,
    inspect_spec_capabilities,
    normalize_and_migrate_spec
)
from platform_core.engine.errors import SpecValidationError


class TestSpecV2ModelsAndValidation(unittest.TestCase):

    def setUp(self):
        self.workspace_root = Path(__file__).resolve().parent.parent.parent

    def test_01_backward_compatibility_existing_specs(self):
        """Verifies that existing v1 application specifications validate without changes."""
        spec_candidates = [
            self.workspace_root / "app.spec.yaml",
            self.workspace_root / "applications" / "sample-node-service" / "app.spec.yaml",
            self.workspace_root / "applications" / "sample-python-worker" / "app.spec.yaml"
        ]

        for sc in spec_candidates:
            self.assertTrue(sc.is_file(), f"Specification file missing: {sc}")
            spec = parse_and_validate_spec(str(sc), workspace_root=str(self.workspace_root))
            self.assertIsInstance(spec, ApplicationSpec)
            self.assertIn(spec.apiVersion, ["platform.enterprise.com/v1", "platform.enterprise.com/v2"])
            self.assertTrue(len(spec.spec.components) >= 1)
            # Verify normalized id is present
            self.assertEqual(spec.metadata.id, spec.metadata.name)

    def test_02_parse_v2_specification(self):
        """Verifies parsing of modern v2 application specification with expanded fields."""
        v2_yaml = """
apiVersion: platform.enterprise.com/v2
kind: Application
metadata:
  name: sample-go-service
  version: "1.0.0"
  id: sample-go-service
  description: "Enterprise Go Microservice"
  owner: "team-platform@enterprise.com"
  team: "core-banking"
  repository: "https://github.com/enterprise/sample-go-service.git"
  securityTier: "tier-2-standard"
  labels:
    service: "payment"
spec:
  components:
    - name: api
      type: container-service
      source:
        context: "applications/sample-node-service"
        dockerfile: "Dockerfile"
      build:
        adapter: "go"
        command: "go build -v -o /app/server"
      runtime:
        name: "go"
        language: "go"
        version: "1.27.3"
        base_image: "gcr.io/distroless/static-debian12:nonroot"
        port: 8080
        health_check:
          path: "/health"
          type: "http"
      deployment:
        adapter: "ecs"
        desired_count: 2
        local_port: 8101
        strategy: "rolling"
  dependencies:
    - name: payment-db
      type: "rds-postgres"
      engine_version: "16"
  observability:
    metrics_path: "/metrics"
    logging_format: "json"
"""
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(v2_yaml)
            temp_path = f.name

        try:
            spec = parse_and_validate_spec(temp_path, workspace_root=str(self.workspace_root))
            self.assertEqual(spec.apiVersion, "platform.enterprise.com/v2")
            self.assertEqual(spec.metadata.name, "sample-go-service")
            self.assertEqual(spec.metadata.team, "core-banking")
            self.assertEqual(spec.spec.components[0].runtime.version, "1.27.3")
            self.assertEqual(spec.spec.components[0].deployment.local_port, 8101)
            self.assertIsNotNone(spec.spec.observability)
            self.assertEqual(spec.spec.observability.metrics_path, "/metrics")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_03_reject_unknown_field_extra_forbid(self):
        """Verifies strict rejection of unauthorized extra fields."""
        bad_yaml = """
apiVersion: platform.enterprise.com/v1
kind: Application
metadata:
  name: bad-app
  version: "1.0.0"
  unauthorized_field_injection: "malicious_payload"
spec:
  components:
    - name: api
      type: container-service
      source:
        context: "applications/sample-node-service"
      build:
        adapter: "dockerfile"
      runtime:
        port: 8080
      deployment:
        adapter: "ecs"
"""
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(bad_yaml)
            temp_path = f.name

        try:
            with self.assertRaises(SpecValidationError):
                parse_and_validate_spec(temp_path, workspace_root=str(self.workspace_root))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_04_reject_path_traversal_context(self):
        """Verifies that directory traversal sequences ('..') in context are rejected."""
        traversal_yaml = """
apiVersion: platform.enterprise.com/v1
kind: Application
metadata:
  name: traversal-app
  version: "1.0.0"
spec:
  components:
    - name: api
      type: container-service
      source:
        context: "../../etc/shadow"
      build:
        adapter: "dockerfile"
      runtime:
        port: 8080
      deployment:
        adapter: "ecs"
"""
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(traversal_yaml)
            temp_path = f.name

        try:
            with self.assertRaises(SpecValidationError) as ctx:
                parse_and_validate_spec(temp_path, workspace_root=str(self.workspace_root))
            self.assertIn("..", str(ctx.exception))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_05_inspect_spec_capabilities(self):
        """Verifies capability inspection for driving universal pipeline execution."""
        spec_path = self.workspace_root / "app.spec.yaml"
        spec = parse_and_validate_spec(str(spec_path), workspace_root=str(self.workspace_root))
        caps = inspect_spec_capabilities(spec)

        self.assertEqual(caps["app_id"], "hotel-billing")
        self.assertTrue(caps["has_container"])
        self.assertTrue(caps["has_frontend"])
        self.assertTrue(caps["has_infra"])
        self.assertIn("backend", caps["container_components"])
        self.assertIn("frontend", caps["frontend_components"])
        self.assertIn("database", caps["dependencies"])


if __name__ == "__main__":
    unittest.main()
