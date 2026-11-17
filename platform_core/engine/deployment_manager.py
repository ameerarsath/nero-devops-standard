"""
NERO Universal Enterprise DevOps Automation Platform - Deployment Manager Subsystem (A1-COR-001)
Responsible for infrastructure provisioning, container deployments, static site sync, and synthetic health verification.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from platform_core.engine.resolver import resolve_environment_context, ResolvedEnvironmentContext
from platform_core.adapters.infrastructure.terraform_adapter import TerraformInfrastructureAdapter
from platform_core.adapters.deployment.s3_adapter import S3FrontendDeploymentAdapter
from platform_core.adapters.deployment.ecs_adapter import ECSDeploymentAdapter
from platform_core.adapters.verification.health_verifier import HealthVerificationAdapter
from platform_core.audit.audit_logger import append_audit_record


def get_frontend_bucket(context: ResolvedEnvironmentContext, workspace_root: str = ".") -> str:
    """
    Extracts the active S3 frontend bucket name from the environment's Terraform state.
    """
    tf_dir = Path(workspace_root) / context.terraform_dir
    state_file = tf_dir / "terraform.tfstate"
    if state_file.is_file():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
                for res in state_data.get("resources", []):
                    if res.get("module") == "module.frontend_website" and res.get("type") == "aws_s3_bucket":
                        instances = res.get("instances", [])
                        if instances:
                            return instances[0].get("attributes", {}).get("id")
        except Exception as e:
            print(f"[WARN] Error reading terraform state for bucket: {e}", file=sys.stderr)

    env_short = "dev" if context.environment == "develop" else context.environment
    return f"billing-{env_short}-{context.environment}-frontend"


def plan_infrastructure(
    app_id: str,
    environment: str,
    target_platform: str = "floci",
    account_topology: str = "multi_account",
    workspace_root: str = ".",
    in_docker: bool = True
) -> str:
    """
    Executes Terraform Plan for the targeted environment.
    """
    ctx = resolve_environment_context(
        app_id=app_id,
        environment=environment,
        target_platform=target_platform,
        account_topology=account_topology,
        in_docker=in_docker
    )

    tf_adapter = TerraformInfrastructureAdapter()
    plan_file = tf_adapter.plan(ctx, workspace_root=workspace_root)
    return plan_file


def apply_infrastructure(
    app_id: str,
    environment: str,
    target_platform: str = "floci",
    account_topology: str = "multi_account",
    plan_filename: Optional[str] = None,
    workspace_root: str = ".",
    in_docker: bool = True
) -> Dict[str, Any]:
    """
    Executes Terraform Apply for the targeted environment.
    """
    ctx = resolve_environment_context(
        app_id=app_id,
        environment=environment,
        target_platform=target_platform,
        account_topology=account_topology,
        in_docker=in_docker
    )

    if not plan_filename:
        plan_filename = f"tfplan.{environment}"

    tf_adapter = TerraformInfrastructureAdapter()
    result = tf_adapter.apply(ctx, workspace_root=workspace_root, plan_filename=plan_filename)

    # Save outputs
    out_file = Path(workspace_root) / f"infra-outputs.{environment}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result.outputs, f, indent=2)

    return result.model_dump()


def deploy_frontend_assets(
    app_id: str,
    environment: str,
    target_platform: str = "floci",
    account_topology: str = "multi_account",
    bucket_name: Optional[str] = None,
    dist_dir: Optional[str] = None,
    workspace_root: str = ".",
    in_docker: bool = True
) -> Dict[str, Any]:
    """
    Syncs static frontend assets to S3.
    """
    ctx = resolve_environment_context(
        app_id=app_id,
        environment=environment,
        target_platform=target_platform,
        account_topology=account_topology,
        in_docker=in_docker
    )

    if not bucket_name:
        bucket_name = get_frontend_bucket(ctx, workspace_root=workspace_root)

    if not dist_dir:
        spec_candidates = [
            Path(workspace_root) / "applications" / app_id / "app.spec.yaml",
            Path(workspace_root) / "app.spec.yaml"
        ]
        found_dist = None
        for sc in spec_candidates:
            if sc.is_file():
                try:
                    from platform_core.engine.parser import parse_and_validate_spec
                    parsed = parse_and_validate_spec(str(sc), workspace_root=workspace_root)
                    if parsed.metadata.name == app_id:
                        fe_comps = [c for c in parsed.spec.components if c.type == "static-site"]
                        if fe_comps:
                            found_dist = str(Path(workspace_root) / fe_comps[0].source.context / (fe_comps[0].build.dist_dir or "dist"))
                            break
                except Exception:
                    pass
        dist_dir = found_dist or str(Path(workspace_root) / "frontend" / "dist")

    s3_adapter = S3FrontendDeploymentAdapter()
    result = s3_adapter.deploy(ctx, bucket_name=bucket_name, dist_dir=dist_dir)
    return result.model_dump()


def verify_deployment(
    app_id: str,
    environment: str,
    target_platform: str = "floci",
    account_topology: str = "multi_account",
    bucket_name: Optional[str] = None,
    ecs_host: Optional[str] = None,
    workspace_root: str = ".",
    in_docker: bool = True
) -> Dict[str, Any]:
    """
    Runs synthetic health verification on S3 and ECS backend.
    """
    ctx = resolve_environment_context(
        app_id=app_id,
        environment=environment,
        target_platform=target_platform,
        account_topology=account_topology,
        in_docker=in_docker
    )

    if not bucket_name:
        if app_id == "hotel-billing":
            bucket_name = get_frontend_bucket(ctx, workspace_root=workspace_root)
        else:
            bucket_name = None

    if not ecs_host:
        ecs_host = "host.docker.internal" if in_docker else "localhost"

    verifier = HealthVerificationAdapter()
    report = verifier.verify(ctx, s3_bucket=bucket_name, ecs_host=ecs_host)

    # Record audit via atomic audit logger
    append_audit_record(
        workspace_root=workspace_root,
        app_id=app_id,
        environment=environment,
        target_platform=target_platform,
        account_topology=account_topology,
        action="DEPLOYMENT_VERIFICATION",
        status="PASSED" if report.all_passed else "FAILED",
        details=report.model_dump()
    )

    return report.model_dump()


def deploy_container_workload(
    app_id: str,
    environment: str,
    target_platform: str = "floci",
    account_topology: str = "multi_account",
    component_name: Optional[str] = None,
    image_ref: Optional[str] = None,
    host_port: Optional[int] = None,
    workspace_root: str = ".",
    in_docker: bool = True
) -> Dict[str, Any]:
    """
    Deploys container workloads to Floci ECS simulation or AWS ECS Fargate
    with cross-platform port conflict self-healing (A1-COR-002).
    """
    ctx = resolve_environment_context(
        app_id=app_id,
        environment=environment,
        target_platform=target_platform,
        account_topology=account_topology,
        in_docker=in_docker
    )

    ecs_adapter = ECSDeploymentAdapter()

    # 1. Inspect app.spec.yaml for component and port definitions
    container_port = 8080
    spec_candidates = [
        Path(workspace_root) / "applications" / app_id / "app.spec.yaml",
        Path(workspace_root) / "app.spec.yaml"
    ]
    app_spec = None
    for sc in spec_candidates:
        if sc.is_file():
            try:
                from platform_core.engine.parser import parse_and_validate_spec
                parsed = parse_and_validate_spec(str(sc), workspace_root=workspace_root)
                if parsed.metadata.name == app_id:
                    app_spec = parsed
                    break
            except Exception:
                pass

    if app_spec:
        container_comps = [c for c in app_spec.spec.components if c.type in ("container-service", "worker-service", "worker")]
        if container_comps:
            if not component_name:
                component_name = container_comps[0].name
            target_comp = next((c for c in container_comps if c.name == component_name), container_comps[0])
            if target_comp.runtime and target_comp.runtime.port:
                container_port = target_comp.runtime.port

    if not component_name:
        component_name = "backend" if app_id == "hotel-billing" else "api"

    # 2. Resolve image reference from manifest (if matching app) or docker images
    if not image_ref:
        manifest_path = Path(workspace_root) / "release-manifest.json"
        if manifest_path.is_file():
            try:
                with open(manifest_path, "r", encoding="utf-8") as mf:
                    mdata = json.load(mf)
                    if mdata.get("application") == app_id:
                        comps = mdata.get("components", {})
                        if component_name in comps:
                            image_ref = comps[component_name].get("image_tag") or comps[component_name].get("image_digest")
            except Exception:
                pass

    if not image_ref:
        insp = subprocess.run(["docker", "images", "--format={{.Repository}}:{{.Tag}}", component_name], capture_output=True, text=True)
        tags = [line.strip() for line in insp.stdout.splitlines() if line.strip() and not line.endswith(":<none>")]
        if tags:
            image_ref = tags[0]
        else:
            image_ref = f"{component_name}:latest"

    # Deterministic host port mapping from catalog resolver (Issue B and C remediation)
    if not host_port:
        host_port = ctx.ecs_host_port

    env_vars = {
        "ENVIRONMENT": environment,
        "PORT": str(container_port),
        "HOST_PORT": str(host_port),
        "AWS_REGION": ctx.region,
        "FLOCI_ENDPOINT": ctx.floci_endpoint or "http://floci:4566",
    }
    if app_id == "hotel-billing" and target_platform in ("floci", "floci-local"):
        short_env = "dev" if environment == "develop" else environment
        rds_port = 7002 if environment == "develop" else (7003 if environment == "qa" else 7004)
        env_vars.update({
            "SPRING_PROFILES_ACTIVE": environment,
            "SPRING_DATASOURCE_URL": f"jdbc:postgresql://172.29.0.2:{rds_port}/hotel_billing_{short_env}",
            "SPRING_DATASOURCE_USERNAME": "postgres",
            "SPRING_DATASOURCE_PASSWORD": f"postgres_{short_env}",
            "AWS_DEFAULT_REGION": "us-east-1",
            "JWT_SECRET": "404E635266556A586E3272357538782F413F4428472B4B6250645367566B5970",
            "JWT_EXPIRATION": "86400000",
            "APP_FRONTEND_URL": f"http://localhost:300{1 if environment == 'develop' else (2 if environment == 'qa' else 3)}",
            "APP_BACKEND_URL": f"http://localhost:{host_port}"
        })

    result = ecs_adapter.deploy(
        context=ctx,
        component_name=component_name,
        image_ref=image_ref,
        container_port=container_port,
        host_port=host_port,
        env_vars=env_vars
    )

    append_audit_record(
        workspace_root=workspace_root,
        app_id=app_id,
        environment=environment,
        target_platform=target_platform,
        account_topology=account_topology,
        action="DEPLOY_CONTAINER_WORKLOAD",
        status="SUCCESS",
        details=result.model_dump()
    )

    return result.model_dump()
