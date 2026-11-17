"""
Enterprise Universal Application Delivery Platform - Environment & Topology Resolver
Calculates all target cloud parameters, account IDs, assume roles, and secret paths.
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from platform_core.engine.errors import ConfigurationError, SecurityPolicyError


class ResolvedEnvironmentContext(BaseModel):
    app_id: str
    environment: str
    target_platform: str
    account_topology: str
    region: str
    account_id: str
    role_arn: Optional[str] = None
    secret_name: str
    secret_arn: str
    resource_prefix: str
    ecs_host_port: Optional[int] = None
    s3_bucket_prefix: str
    terraform_dir: str
    floci_endpoint: Optional[str] = None
    approval_required: bool = False
    governance_gates: list[str] = Field(default_factory=list)
    oci_registry_endpoint: str = "localhost:5100"


def resolve_environment_context(
    app_id: str,
    environment: str,
    target_platform: str = "floci",
    account_topology: str = "multi_account",
    region: str = "ap-south-1",
    in_docker: bool = True,
    caller_account_id: Optional[str] = None
) -> ResolvedEnvironmentContext:
    """
    Deterministically computes the complete infrastructure and security context.
    """
    env_clean = environment.lower().strip()
    platform_clean = target_platform.lower().strip()
    topology_clean = account_topology.lower().strip()

    valid_envs = {"develop", "qa", "prod"}
    if env_clean not in valid_envs:
        raise ConfigurationError(f"Invalid environment '{environment}'. Must be one of {valid_envs}")

    valid_platforms = {"floci", "floci-local", "aws"}
    if platform_clean not in valid_platforms:
        raise ConfigurationError(f"Invalid target platform '{target_platform}'. Must be one of {valid_platforms}")

    # Normalize 'floci-local' alias to internal platform key 'floci'
    if platform_clean == "floci-local":
        platform_clean = "floci"

    valid_topologies = {"multi_account", "single_account"}
    if topology_clean not in valid_topologies:
        raise ConfigurationError(f"Invalid account topology '{account_topology}'. Must be one of {valid_topologies}")

    valid_regions = {"ap-south-1", "us-east-1", "us-west-2", "eu-west-1"}
    region_clean = region.lower().strip()
    if region_clean not in valid_regions:
        raise ConfigurationError(
            f"Enterprise Policy Violation: Unauthorized AWS region '{region}'. Must be one of {sorted(valid_regions)}."
        )

    env_short_map = {
        "develop": "dev",
        "qa": "qa",
        "prod": "prod"
    }
    short_env = env_short_map[env_clean]

    # 1. Resolve Account ID and Role ARN
    if platform_clean == "floci":
        floci_ep = "http://floci:4566" if in_docker else "http://localhost:4566"
        role_arn = None
        if topology_clean == "multi_account":
            # Documented dedicated Floci simulation accounts
            account_map = {
                "develop": "111122223333",
                "qa": "444455556666",
                "prod": "777788889999"
            }
            account_id = account_map[env_clean]
        else:
            # Single-account simulated namespace
            account_id = "000000000000"
    else:  # Real AWS Cloud
        floci_ep = None
        # Verify if Real AWS Cloud is enabled in centralized platform configuration
        try:
            from platform_core.engine.platform_config import load_platform_config
            p_cfg = load_platform_config()
            aws_cfg = p_cfg.environments.get("aws-production")
            if aws_cfg and (not aws_cfg.enabled or aws_cfg.status == "UNCONFIGURED"):
                # Require explicit override via AWS_REAL_CLOUD_ENABLED or explicit test env setup
                is_override = os.environ.get("AWS_REAL_CLOUD_ENABLED", "").lower() == "true"
                is_explicit_test = any(os.environ.get(f"AWS_{e.upper()}_ACCOUNT_ID") for e in ["develop", "qa", "prod"]) or os.environ.get("AWS_SHARED_ACCOUNT_ID") or os.environ.get("AWS_ACCOUNT_ID") or os.environ.get("AWS_MANAGEMENT_ACCOUNT_ID")
                if not is_override and not is_explicit_test:
                    raise SecurityPolicyError(
                        "Enterprise Security Policy Violation: Real AWS deployment target is marked 'UNCONFIGURED' and disabled "
                        "in platform_config.yaml. The platform is running in Floci-First local mode. "
                        "Target 'floci' / 'floci-local' or configure real AWS environment explicitly."
                    )
        except ConfigurationError:
            pass
        if topology_clean == "multi_account":
            env_var_key = f"AWS_{env_clean.upper()}_ACCOUNT_ID"
            account_id = os.environ.get(env_var_key)
            if not account_id:
                # Do not invent account IDs; raise explicit ConfigurationError
                raise ConfigurationError(
                    f"Real AWS multi-account deployment requires environment variable '{env_var_key}' to be set"
                )
            role_arn = os.environ.get(
                f"AWS_{env_clean.upper()}_ROLE_ARN",
                f"arn:aws:iam::{account_id}:role/{app_id}-{short_env}-DeploymentRole"
            )
        else:
            account_id = os.environ.get("AWS_SHARED_ACCOUNT_ID") or os.environ.get("AWS_ACCOUNT_ID")
            if not account_id:
                raise ConfigurationError(
                    "Real AWS single-account deployment requires environment variable 'AWS_SHARED_ACCOUNT_ID' or 'AWS_ACCOUNT_ID'"
                )
            role_arn = os.environ.get(
                f"AWS_DEPLOY_ROLE_ARN",
                f"arn:aws:iam::{account_id}:role/{app_id}-SingleAccountDeploymentRole"
            )

        if role_arn:
            if not role_arn.startswith("arn:aws:iam::") or ":role/" not in role_arn:
                raise ConfigurationError(
                    f"Enterprise Policy Violation: Invalid deployment role ARN format: '{role_arn}'. "
                    f"Must match 'arn:aws:iam::<account_id>:role/<role_name>'."
                )

        # Enterprise Guardrail: Fail-closed verification of AWS Organizations Management Account
        mgmt_account = os.environ.get("AWS_MANAGEMENT_ACCOUNT_ID")
        if not mgmt_account:
            raise SecurityPolicyError(
                "Enterprise Security Policy Violation: AWS Organizations Management Account boundary is not established. "
                "'AWS_MANAGEMENT_ACCOUNT_ID' must be configured to verify non-management isolation before AWS deployment."
            )
        if account_id == mgmt_account:
            raise SecurityPolicyError(
                f"Enterprise Policy Violation: Direct workload deployment to AWS Organizations Management Account ({account_id}) is strictly prohibited."
            )

        # Enterprise Guardrail: Caller Account vs Target Account Verification
        caller_acc = caller_account_id or os.environ.get("AWS_CALLER_ACCOUNT_ID")
        if caller_acc and caller_acc != account_id:
            raise SecurityPolicyError(
                f"Enterprise Policy Violation: Authenticated caller account ID ({caller_acc}) does not match "
                f"authorized target account ID ({account_id})."
            )

    # 2. Resolve Secret Names & ARNs
    if topology_clean == "multi_account":
        secret_name = f"{app_id}-{short_env}/app-secrets"
    else:
        # Hierarchical namespace in single account
        secret_name = f"{app_id}/{env_clean}/app-secrets"

    secret_arn = f"arn:aws:secretsmanager:{region}:{account_id}:secret:{secret_name}"

    # 3. Resolve Resource Prefixes & Ports
    resource_prefix = f"{app_id}-{short_env}"
    s3_bucket_prefix = f"{app_id}-{short_env}-{env_clean}-frontend"

    # Dynamic Port Allocation via Catalog Engine (A2-CAT-002)
    ecs_host_port = None
    if platform_clean == "floci":
        try:
            from platform_core.engine.catalog import ApplicationCatalog
            cat = ApplicationCatalog()
            ecs_host_port = cat.get_port_for_environment(app_id, env_clean)
        except Exception:
            # Safe backward compatibility fallback
            if app_id == "sample-node-service":
                ecs_host_port = {"develop": 8091, "qa": 8092, "prod": 8093}.get(env_clean)
            elif app_id == "sample-python-worker":
                ecs_host_port = {"develop": 8095, "qa": 8096, "prod": 8097}.get(env_clean)
            else:
                ecs_host_port = {"develop": 8085, "qa": 8087, "prod": 8089}.get(env_clean)

    # 4. Resolve Governance Gates
    if env_clean == "prod":
        approval_required = True
        gates = ["qa-technical-approval", "ops-release-approval"]
    else:
        approval_required = False
        gates = []

    if platform_clean == "aws":
        terraform_dir = "infrastructure/terraform/environments/aws"
    else:
        terraform_dir = f"infrastructure/terraform/environments/{env_clean}"

    if platform_clean == "floci":
        oci_registry = "localhost:5100"
    else:
        oci_registry = f"{account_id}.dkr.ecr.{region_clean}.amazonaws.com"

    return ResolvedEnvironmentContext(
        app_id=app_id,
        environment=env_clean,
        target_platform=platform_clean,
        account_topology=topology_clean,
        region=region,
        account_id=account_id,
        role_arn=role_arn,
        secret_name=secret_name,
        secret_arn=secret_arn,
        resource_prefix=resource_prefix,
        ecs_host_port=ecs_host_port,
        s3_bucket_prefix=s3_bucket_prefix,
        terraform_dir=terraform_dir,
        floci_endpoint=floci_ep,
        approval_required=approval_required,
        governance_gates=gates,
        oci_registry_endpoint=oci_registry
    )
