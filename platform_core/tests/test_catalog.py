"""
Unit tests for Enterprise Application Catalog and Security Policies.
"""

from pathlib import Path
from platform_core.engine.catalog import ApplicationCatalog
from platform_core.engine.errors import SecurityPolicyError
from platform_core.engine.parser import parse_and_validate_spec


def test_catalog_approved_app():
    catalog = ApplicationCatalog()
    app = catalog.get_application("hotel-billing")
    assert app.id == "hotel-billing"
    assert "develop" in app.allowed_environments
    assert "qa" in app.allowed_environments
    assert "prod" in app.allowed_environments
    print("PASS: test_catalog_approved_app")


def test_catalog_reject_unregistered_app():
    catalog = ApplicationCatalog()
    try:
        catalog.get_application("unauthorized-crypto-miner")
        assert False, "Expected SecurityPolicyError for unregistered application"
    except SecurityPolicyError as e:
        assert "not registered" in str(e)
        print("PASS: test_catalog_reject_unregistered_app - Blocked unapproved app")


def test_catalog_validate_valid_deployment():
    root = Path(__file__).resolve().parent.parent.parent
    spec_file = root / "app.spec.yaml"
    spec = parse_and_validate_spec(str(spec_file))
    
    catalog = ApplicationCatalog()
    entry = catalog.validate_deployment_request(
        app_id="hotel-billing",
        environment="develop",
        platform="floci",
        topology="multi_account",
        branch="devops/jenkins-floci-local-lab",
        repository_url="https://github.com/ameerarsath/billing-system.git",
        spec=spec
    )
    assert entry.id == "hotel-billing"
    print("PASS: test_catalog_validate_valid_deployment")


def test_catalog_reject_unauthorized_branch():
    catalog = ApplicationCatalog()
    try:
        catalog.validate_deployment_request(
            app_id="hotel-billing",
            environment="develop",
            platform="floci",
            topology="multi_account",
            branch="untrusted-hacker-branch"
        )
        assert False, "Expected SecurityPolicyError for untrusted branch"
    except SecurityPolicyError as e:
        assert "not permitted" in str(e)
        print("PASS: test_catalog_reject_unauthorized_branch - Blocked unauthorized branch")


def test_catalog_reject_rogue_repository():
    catalog = ApplicationCatalog()
    try:
        catalog.validate_deployment_request(
            app_id="hotel-billing",
            environment="develop",
            platform="floci",
            topology="multi_account",
            branch="main",
            repository_url="https://github.com/attacker/malicious-repo.git"
        )
        assert False, "Expected SecurityPolicyError for rogue repository"
    except SecurityPolicyError as e:
        assert "does not match trusted catalog repository" in str(e)
        print("PASS: test_catalog_reject_rogue_repository - Blocked rogue repo URL")


if __name__ == "__main__":
    test_catalog_approved_app()
    test_catalog_reject_unregistered_app()
    test_catalog_validate_valid_deployment()
    test_catalog_reject_unauthorized_branch()
    test_catalog_reject_rogue_repository()
    print("ALL CATALOG TESTS PASSED!")
