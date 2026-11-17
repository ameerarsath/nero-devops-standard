"""
NERO Programme 1 — Phase A2 Integration Test Suite
test_onboarding.py: Universal Application Onboarding and Multi-App Catalog Verification (A2-TST-001)
"""

import pytest
from pathlib import Path

from platform_core.engine.catalog import ApplicationCatalog, PortAllocationManager
from platform_core.engine.parser import parse_and_validate_spec, inspect_spec_capabilities
from platform_core.engine.resolver import resolve_environment_context
from platform_core.engine.inspector import RepositoryInspector, generate_candidate_spec


TARGET_APPS = [
    {
        "id": "hotel-billing",
        "spec_path": "app.spec.yaml",
        "has_infra": True,
        "has_container": True,
        "has_frontend": True,
        "ports": {"develop": 8085, "qa": 8087, "prod": 8089}
    },
    {
        "id": "sample-node-service",
        "spec_path": "applications/sample-node-service/app.spec.yaml",
        "has_infra": False,
        "has_container": True,
        "has_frontend": False,
        "ports": {"develop": 8091, "qa": 8092, "prod": 8093}
    },
    {
        "id": "sample-python-worker",
        "spec_path": "applications/sample-python-worker/app.spec.yaml",
        "has_infra": True,
        "has_container": True,
        "has_frontend": False,
        "ports": {"develop": 8095, "qa": 8096, "prod": 8097}
    },
    {
        "id": "sample-go-service",
        "spec_path": "applications/sample-go-service/app.spec.yaml",
        "has_infra": False,
        "has_container": True,
        "has_frontend": False,
        "ports": {"develop": 8101, "qa": 8102, "prod": 8103}
    }
]


class TestUniversalApplicationOnboarding:

    def test_01_all_target_apps_registered_in_catalog(self):
        catalog = ApplicationCatalog("platform_core/catalog/applications.yaml")
        app_ids = [app.id for app in catalog.list_applications()]

        for target in TARGET_APPS:
            assert target["id"] in app_ids, f"Application {target['id']} missing from central catalog"

    def test_02_port_allocations_and_zero_collision(self):
        catalog = ApplicationCatalog("platform_core/catalog/applications.yaml")
        allocated_ports = set()

        for target in TARGET_APPS:
            for env, expected_port in target["ports"].items():
                resolved_port = catalog.get_port_for_environment(target["id"], env)
                assert resolved_port == expected_port, f"Port mismatch for {target['id']} in {env}: {resolved_port} != {expected_port}"
                assert resolved_port not in allocated_ports, f"Port collision detected for port {resolved_port} in {target['id']} ({env})"
                allocated_ports.add(resolved_port)

    def test_03_specification_validation_and_capabilities(self):
        for target in TARGET_APPS:
            spec = parse_and_validate_spec(target["spec_path"], workspace_root=".")
            assert spec.metadata.name == target["id"]

            caps = inspect_spec_capabilities(spec)
            assert caps["has_infra"] == target["has_infra"], f"Infrastructure capability mismatch for {target['id']}"
            assert caps["has_container"] == target["has_container"], f"Container capability mismatch for {target['id']}"
            assert caps["has_frontend"] == target["has_frontend"], f"Frontend capability mismatch for {target['id']}"

    def test_04_environment_context_resolution_across_all_environments(self):
        for target in TARGET_APPS:
            for env in ["develop", "qa", "prod"]:
                ctx = resolve_environment_context(
                    app_id=target["id"],
                    environment=env,
                    target_platform="floci",
                    account_topology="multi_account",
                    in_docker=False
                )
                assert ctx.app_id == target["id"]
                assert ctx.environment == env
                assert ctx.ecs_host_port == target["ports"][env]
                assert ctx.target_platform == "floci"

    def test_05_dynamic_new_application_onboarding_lifecycle(self, tmp_path):
        # 1. Create a mock new microservice repo
        new_svc_dir = tmp_path / "new-analytics-api"
        new_svc_dir.mkdir()
        (new_svc_dir / "package.json").write_text('{"name": "new-analytics-api", "version": "1.0.0"}', encoding="utf-8")
        (new_svc_dir / "package-lock.json").write_text('{"lockfileVersion": 3}', encoding="utf-8")
        (new_svc_dir / "server.js").write_text('const http = require("http");', encoding="utf-8")

        # 2. Inspect repository
        inspector = RepositoryInspector(str(new_svc_dir))
        report = inspector.inspect()
        assert "nodejs" in report.detected_technologies
        assert report.has_lockfiles is True

        # 3. Generate candidate spec
        candidate = generate_candidate_spec(report, app_id="new-analytics-api")
        spec_file = new_svc_dir / "app.spec.yaml"
        import yaml
        with open(spec_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(candidate, f)

        # 4. Copy catalog to tmp_path to test dynamic registration without altering production catalog
        cat_file = tmp_path / "test_applications.yaml"
        cat_file.write_text(Path("platform_core/catalog/applications.yaml").read_text(encoding="utf-8"), encoding="utf-8")

        catalog = ApplicationCatalog(str(cat_file))
        new_app = catalog.register_application(
            spec=str(spec_file),
            trusted_repository="https://github.com/enterprise/new-analytics-api.git",
            workspace_root=str(new_svc_dir)
        )

        assert new_app.id == "new-analytics-api"
        # Dynamic port allocator should allocate next available ports >= 8104 without collision
        dev_port = catalog.get_port_for_environment("new-analytics-api", "develop")
        qa_port = catalog.get_port_for_environment("new-analytics-api", "qa")
        prod_port = catalog.get_port_for_environment("new-analytics-api", "prod")

        assert dev_port >= 8100
        assert qa_port > dev_port
        assert prod_port > qa_port

        # 5. Must validate deployment request successfully
        auth_entry = catalog.validate_deployment_request(
            app_id="new-analytics-api",
            environment="develop",
            platform="floci",
            topology="multi_account",
            branch="main",
            repository_url="https://github.com/enterprise/new-analytics-api.git"
        )
        assert auth_entry.id == "new-analytics-api"
