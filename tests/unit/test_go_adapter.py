"""
NERO Programme 1 — Phase A2 Test Suite
test_go_adapter.py: Unit tests for GoBuildAdapter and Go 1.27.3 runtime policy (A2-ADP-002)
"""

import pytest
from pathlib import Path

from platform_core.adapters.build.go_adapter import GoBuildAdapter, STANDARD_GO_DOCKERFILE
from platform_core.adapters.base import BasePlatformAdapter
from platform_core.policy.runtime_policy import (
    RuntimePolicyValidator,
    RuntimeStatus,
    RuntimePolicyError,
    RUNTIME_LIFECYCLE_MATRIX,
    check_dockerfile_non_root
)
from platform_core.engine.models import ComponentModel, SourceModel, BuildModel, RuntimeModel, DeploymentModel


class TestGoAdapterAndRuntimePolicy:

    def test_01_go_adapter_polymorphism(self):
        adapter = GoBuildAdapter()
        assert isinstance(adapter, BasePlatformAdapter)
        assert adapter.adapter_name == "build.go"
        assert adapter.version == "1.0.0"

    def test_02_go_lifecycle_policy_matrix(self):
        assert "go" in RUNTIME_LIFECYCLE_MATRIX
        assert RUNTIME_LIFECYCLE_MATRIX["go"]["1.27.3"]["status"] == RuntimeStatus.SUPPORTED
        assert RUNTIME_LIFECYCLE_MATRIX["go"]["1.22"]["status"] == RuntimeStatus.PROHIBITED

    def test_03_standard_go_dockerfile_non_root_compliance(self, tmp_path):
        df_path = tmp_path / "Dockerfile"
        df_path.write_text(STANDARD_GO_DOCKERFILE.format(port=8080), encoding="utf-8")

        compliant, reason, user = check_dockerfile_non_root(df_path)
        assert compliant is True
        assert "nonroot" in user

        # Policy validator must not raise
        RuntimePolicyValidator.enforce_non_root_policy(df_path, component_name="go-service")

    def test_04_prohibited_go_version_rejected(self, tmp_path):
        comp_dict = {
            "name": "legacy-go",
            "type": "container-service",
            "source": {"context": ".", "dockerfile": "Dockerfile"},
            "build": {"adapter": "go"},
            "runtime": {
                "name": "go",
                "version": "1.22",
                "port": 8080
            }
        }
        df_path = tmp_path / "Dockerfile"
        df_path.write_text("FROM golang:1.22-alpine\nUSER 65532\n", encoding="utf-8")

        with pytest.raises(RuntimePolicyError) as exc_info:
            RuntimePolicyValidator.validate_component(comp_dict, tmp_path)
        assert "prohibited/EOL runtime" in str(exc_info.value)

    def test_05_sample_go_service_specification_valid(self):
        from platform_core.engine.parser import parse_and_validate_spec
        spec_path = "applications/sample-go-service/app.spec.yaml"
        spec = parse_and_validate_spec(spec_path, workspace_root=".")
        assert spec.metadata.name == "sample-go-service"
        assert spec.spec.components[0].build.adapter == "go"
        assert spec.spec.components[0].runtime.version == "1.27.3"
