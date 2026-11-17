"""
Unit tests for Environment and Account Topology Resolver.
"""

import os
from platform_core.engine.resolver import resolve_environment_context
from platform_core.engine.errors import ConfigurationError


def test_floci_multi_account_resolution():
    ctx_dev = resolve_environment_context(
        app_id="hotel-billing",
        environment="develop",
        target_platform="floci",
        account_topology="multi_account"
    )
    assert ctx_dev.account_id == "111122223333"
    assert ctx_dev.secret_name == "hotel-billing-dev/app-secrets"
    assert ctx_dev.ecs_host_port == 8085
    assert ctx_dev.approval_required is False
    assert ctx_dev.floci_endpoint == "http://floci:4566"

    ctx_qa = resolve_environment_context(
        app_id="hotel-billing",
        environment="qa",
        target_platform="floci",
        account_topology="multi_account"
    )
    assert ctx_qa.account_id == "444455556666"
    assert ctx_qa.secret_name == "hotel-billing-qa/app-secrets"
    assert ctx_qa.ecs_host_port == 8087
    assert ctx_qa.approval_required is False

    ctx_prod = resolve_environment_context(
        app_id="hotel-billing",
        environment="prod",
        target_platform="floci",
        account_topology="multi_account"
    )
    assert ctx_prod.account_id == "777788889999"
    assert ctx_prod.secret_name == "hotel-billing-prod/app-secrets"
    assert ctx_prod.ecs_host_port == 8089
    assert ctx_prod.approval_required is True
    assert "qa-technical-approval" in ctx_prod.governance_gates
    assert "ops-release-approval" in ctx_prod.governance_gates
    print("PASS: test_floci_multi_account_resolution")


def test_floci_single_account_resolution():
    for env in ["develop", "qa", "prod"]:
        ctx = resolve_environment_context(
            app_id="hotel-billing",
            environment=env,
            target_platform="floci",
            account_topology="single_account"
        )
        assert ctx.account_id == "000000000000"
        # Hierarchical secret names in single account
        assert ctx.secret_name == f"hotel-billing/{env}/app-secrets"
    print("PASS: test_floci_single_account_resolution")


def test_real_aws_multi_account_resolution():
    os.environ["AWS_PROD_ACCOUNT_ID"] = "123456789012"
    os.environ["AWS_PROD_ROLE_ARN"] = "arn:aws:iam::123456789012:role/CustomProdRole"
    os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = "999999999999"
    try:
        ctx = resolve_environment_context(
            app_id="hotel-billing",
            environment="prod",
            target_platform="aws",
            account_topology="multi_account"
        )
        assert ctx.account_id == "123456789012"
        assert ctx.role_arn == "arn:aws:iam::123456789012:role/CustomProdRole"
        assert ctx.floci_endpoint is None
        print("PASS: test_real_aws_multi_account_resolution")
    finally:
        os.environ.pop("AWS_PROD_ACCOUNT_ID", None)
        os.environ.pop("AWS_PROD_ROLE_ARN", None)
        os.environ.pop("AWS_MANAGEMENT_ACCOUNT_ID", None)


def test_real_aws_missing_credentials_fails_closed():
    # Never invent account IDs
    os.environ["AWS_REAL_CLOUD_ENABLED"] = "true"
    os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = "999999999999"
    os.environ.pop("AWS_DEVELOP_ACCOUNT_ID", None)
    try:
        resolve_environment_context(
            app_id="hotel-billing",
            environment="develop",
            target_platform="aws",
            account_topology="multi_account"
        )
        assert False, "Expected ConfigurationError when AWS account variable is missing"
    except ConfigurationError as e:
        assert "AWS_DEVELOP_ACCOUNT_ID" in str(e)
        print("PASS: test_real_aws_missing_credentials_fails_closed - Fail-closed enforcement")
    finally:
        os.environ.pop("AWS_REAL_CLOUD_ENABLED", None)
        os.environ.pop("AWS_MANAGEMENT_ACCOUNT_ID", None)


def test_reject_invalid_inputs():
    try:
        resolve_environment_context("app", "staging", "floci", "multi_account")
        assert False
    except ConfigurationError:
        pass

    try:
        resolve_environment_context("app", "develop", "azure", "multi_account")
        assert False
    except ConfigurationError:
        pass

    try:
        resolve_environment_context("app", "develop", "floci", "invalid_topology")
        assert False
    except ConfigurationError:
        pass
    print("PASS: test_reject_invalid_inputs")


if __name__ == "__main__":
    test_floci_multi_account_resolution()
    test_floci_single_account_resolution()
    test_real_aws_multi_account_resolution()
    test_real_aws_missing_credentials_fails_closed()
    test_reject_invalid_inputs()
    print("ALL RESOLVER TESTS PASSED!")
