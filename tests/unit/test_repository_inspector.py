"""
NERO Programme 1 — Phase A2 Test Suite
test_repository_inspector.py: Unit tests for RepositoryInspector and candidate spec generation (A2-INS-001, A2-INS-002)
"""

import json
import pytest
from pathlib import Path
import yaml

from platform_core.engine.inspector import RepositoryInspector, generate_candidate_spec
from platform_core.engine.models import ApplicationSpec
from platform_core.engine.parser import parse_and_validate_spec


class TestRepositoryInspector:

    def test_01_inspect_node_service(self):
        inspector = RepositoryInspector("applications/sample-node-service")
        report = inspector.inspect()

        assert "nodejs" in report.detected_technologies
        assert report.has_lockfiles is True
        assert any("package-lock.json" in l for l in report.lockfiles_found)
        assert len(report.components) >= 1

        node_comp = report.components[0]
        assert node_comp.language == "javascript"
        assert node_comp.framework == "express"
        assert node_comp.suggested_adapter in ["dockerfile", "node"]
        assert node_comp.detected_port == 8080
        assert node_comp.health_path == "/health"

    def test_02_inspect_python_worker(self):
        inspector = RepositoryInspector("applications/sample-python-worker")
        report = inspector.inspect()

        assert "python" in report.detected_technologies
        assert report.has_lockfiles is True
        assert any("requirements.txt" in l for l in report.lockfiles_found)
        assert len(report.components) >= 1

        worker_comp = report.components[0]
        assert worker_comp.type == "worker"
        assert worker_comp.language == "python"
        assert worker_comp.detected_port == 8000
        assert worker_comp.health_path == "/health"

    def test_03_inspect_root_multi_component(self):
        inspector = RepositoryInspector(".")
        report = inspector.inspect()

        assert "java" in report.detected_technologies
        assert "nodejs" in report.detected_technologies
        assert "python" in report.detected_technologies

        comp_names = [c.name for c in report.components]
        assert "backend" in comp_names
        assert "frontend" in comp_names
        assert "rds-postgres" in report.detected_dependencies

    def test_04_generate_candidate_spec_and_validate_schema(self, tmp_path):
        inspector = RepositoryInspector("applications/sample-node-service")
        report = inspector.inspect()

        candidate = generate_candidate_spec(report, app_id="sample-node-service")
        assert candidate["apiVersion"] == "platform.nero/v1"
        assert candidate["kind"] == "Application"
        assert candidate["metadata"]["name"] == "sample-node-service"
        assert len(candidate["spec"]["components"]) >= 1

        # Must strictly validate under Pydantic ApplicationSpec model
        spec_obj = ApplicationSpec.model_validate(candidate)
        assert spec_obj.metadata.name == "sample-node-service"
        assert spec_obj.spec.components[0].runtime.port == 8080

        # Must be serializable to valid YAML and parseable by parse_and_validate_spec
        spec_file = tmp_path / "app.spec.yaml"
        with open(spec_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(candidate, f)

        # Context is '.', so workspace_root=applications/sample-node-service
        loaded_spec = parse_and_validate_spec(
            str(spec_file),
            workspace_root="applications/sample-node-service"
        )
        assert loaded_spec.metadata.name == "sample-node-service"

    def test_05_ambiguity_and_missing_lockfile(self, tmp_path):
        # Create a raw python script without requirements or Dockerfile
        raw_app = tmp_path / "raw_script"
        raw_app.mkdir()
        (raw_app / "script.py").write_text("print('hello')", encoding="utf-8")

        inspector = RepositoryInspector(str(raw_app))
        report = inspector.inspect()

        assert "python" in report.detected_technologies
        assert report.has_lockfiles is False
        assert len(report.ambiguous_structures) >= 1
        assert any("Lockfile missing" in a for a in report.ambiguous_structures)
