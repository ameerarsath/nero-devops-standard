"""
Enterprise Universal Application Delivery Platform - Engine CLI Interface
Exposes platform engine capabilities to Jenkins pipelines, shell scripts, and operators
with deterministic exit codes (A1-FND-002) and console log masking (A1-SEC-002).
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

from platform_core.engine.parser import parse_and_validate_spec
from platform_core.engine.catalog import ApplicationCatalog
from platform_core.engine.resolver import resolve_environment_context
from platform_core.engine.errors import (
    PlatformException,
    ConfigurationError,
    SpecValidationError,
    CatalogAuthorizationError,
    SecurityPolicyError,
    InfrastructureError,
    DeploymentError,
    DeploymentVerificationError,
    GovernancePolicyError,
    EXIT_CODE_SUCCESS,
    EXIT_CODE_GENERAL_ERROR,
    EXIT_CODE_SPEC_ERROR,
    EXIT_CODE_CATALOG_ERROR,
    EXIT_CODE_POLICY_ERROR,
    EXIT_CODE_INFRA_ERROR,
    EXIT_CODE_DEPLOY_ERROR,
    EXIT_CODE_VERIFY_ERROR,
    EXIT_CODE_GOVERNANCE_ERROR,
)
from platform_core.engine import orchestrator


class SecretScrubber:
    """
    Wraps an output stream (stdout/stderr) and transparently scrubs known secret patterns
    including JWT tokens, credentials, and passwords (A1-SEC-002).
    """

    def __init__(self, target_stream):
        self.target_stream = target_stream

    def write(self, s):
        if not s:
            return
        # Redact JWT tokens
        cleaned = re.sub(r'ey[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-+/=]{10,}', '****[REDACTED_JWT]****', s)
        # Redact URI passwords (e.g. postgres://user:password@host)
        cleaned = re.sub(r'(://[^:]+:)([^@/]+)(@)', r'\1****[REDACTED]****\3', cleaned)
        # Redact common key-value credential expressions
        cleaned = re.sub(r'(?i)(password|jwt_secret|api_key|secret_key|private_key|token)["\']?\s*[:=]\s*["\']?([^"\'\s,;]+)', r'\1=****[REDACTED]****', cleaned)
        self.target_stream.write(cleaned)

    def flush(self):
        self.target_stream.flush()

    def isatty(self):
        return getattr(self.target_stream, 'isatty', lambda: False)()


def cmd_inspect_spec(args):
    try:
        from platform_core.engine.parser import parse_and_validate_spec, inspect_spec_capabilities
        spec = parse_and_validate_spec(args.spec, workspace_root=args.workspace)
        caps = inspect_spec_capabilities(spec)

        if args.has_container:
            print("true" if caps["has_container"] else "false")
        elif args.has_frontend:
            print("true" if caps["has_frontend"] else "false")
        elif args.has_infra:
            print("true" if caps["has_infra"] else "false")
        elif args.has_worker:
            print("true" if caps["has_worker"] else "false")
        elif args.format == "shell":
            print(f"APP_ID='{caps['app_id']}'")
            print(f"HAS_CONTAINER='{'true' if caps['has_container'] else 'false'}'")
            print(f"HAS_FRONTEND='{'true' if caps['has_frontend'] else 'false'}'")
            print(f"HAS_WORKER='{'true' if caps['has_worker'] else 'false'}'")
            print(f"HAS_INFRA='{'true' if caps['has_infra'] else 'false'}'")
            print(f"CONTAINER_COMPS='{','.join(caps['container_components'])}'")
            print(f"FRONTEND_COMPS='{','.join(caps['frontend_components'])}'")
            print(f"WORKER_COMPS='{','.join(caps['worker_components'])}'")
        else:
            print(json.dumps(caps, indent=2))
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_onboard_app(args):
    try:
        from platform_core.engine.parser import parse_and_validate_spec
        from platform_core.engine.catalog import ApplicationCatalog
        spec = parse_and_validate_spec(args.spec, workspace_root=args.workspace)
        catalog = ApplicationCatalog(args.catalog)
        entry = catalog.register_application(
            spec=spec,
            trusted_repository=args.repo,
            display_name=args.display_name,
            security_tier=args.security_tier,
            workspace_root=args.workspace or "."
        )
        print(f"[OK] Application '{entry.id}' successfully registered in central catalog.")
        print(f"     Security Tier   : {entry.security_tier}")
        print(f"     Allocated Ports : {entry.allocated_ports}")
        print(f"     Allowed Envs    : {entry.allowed_environments}")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_list_apps(args):
    try:
        from platform_core.engine.catalog import ApplicationCatalog
        catalog = ApplicationCatalog(args.catalog)
        apps = catalog.list_applications()
        if args.format == "json":
            print(json.dumps([a.model_dump() for a in apps], indent=2))
        else:
            print(f"{'APPLICATION ID':<25} {'SECURITY TIER':<25} {'ALLOCATED PORTS':<30} {'REPOSITORY'}")
            print(f"{'-' * 25} {'-' * 25} {'-' * 30} {'-' * 30}")
            for a in apps:
                port_str = ", ".join(f"{k}:{v}" for k, v in a.allocated_ports.items()) or "None"
                print(f"{a.id:<25} {a.security_tier:<25} {port_str:<30} {a.trusted_repository}")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_inspect_repo(args):
    try:
        from platform_core.engine.inspector import RepositoryInspector
        import yaml
        inspector = RepositoryInspector(args.dir)
        report = inspector.inspect()
        if args.emit_candidate:
            app_id = args.app or Path(args.dir).resolve().name
            candidate_spec = inspector.generate_candidate_spec(app_id=app_id)
            cand_path = Path(args.emit_candidate)
            with open(cand_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(candidate_spec, f, sort_keys=False, indent=2)
            print(f"[OK] Candidate specification emitted to: {cand_path}")

        if args.format == "json":
            print(json.dumps(report.model_dump(), indent=2))
        else:
            print(f"=== Repository Inspection: {report.repository_path} ===")
            print(f"Detected Technologies: {report.detected_technologies}")
            print(f"Lockfiles Found:       {report.lockfiles_found}")
            print(f"Discovered Components ({len(report.components)}):")
            for c in report.components:
                print(f"  - [{c.type}] {c.name}: language={c.language}, adapter={c.suggested_adapter}, context={c.context_path}")
            if report.ambiguous_structures:
                print(f"Warnings/Ambiguities:  {report.ambiguous_structures}")
        sys.exit(EXIT_CODE_SUCCESS)
    except Exception as e:
        print(f"[ERROR] Repository inspection failed: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE_SPEC_ERROR)


def cmd_validate(args):
    try:
        spec = parse_and_validate_spec(args.spec, workspace_root=args.workspace)
        print(f"[OK] Application Specification '{spec.metadata.name}' v{spec.metadata.version} is VALID.")
        print(f"     Components: {[c.name for c in spec.spec.components]}")
        print(f"     Dependencies: {[d.name for d in spec.spec.dependencies]}")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_check_catalog(args):
    try:
        catalog = ApplicationCatalog(args.catalog)
        spec = None
        if args.spec and Path(args.spec).is_file():
            spec = parse_and_validate_spec(args.spec)

        entry = catalog.validate_deployment_request(
            app_id=args.app,
            environment=args.env,
            platform=args.platform,
            topology=args.topology,
            branch=args.branch,
            repository_url=args.repo,
            spec=spec
        )
        print(f"[OK] Application '{entry.id}' is AUTHORIZED for {args.env} on {args.platform} ({args.topology}).")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_resolve(args):
    try:
        ctx = resolve_environment_context(
            app_id=args.app,
            environment=args.env,
            target_platform=args.platform,
            account_topology=args.topology,
            region=args.region,
            in_docker=args.in_docker
        )
        if args.format == "json":
            print(json.dumps(ctx.model_dump(), indent=2))
        elif args.format == "shell":
            for k, v in ctx.model_dump().items():
                if v is not None:
                    # Export shell variable
                    val_str = str(v)
                    print(f"PLATFORM_{k.upper()}='{val_str}'")
        else:
            print(f"App ID:           {ctx.app_id}")
            print(f"Environment:      {ctx.environment}")
            print(f"Target Platform:  {ctx.target_platform}")
            print(f"Account Topology: {ctx.account_topology}")
            print(f"Account ID:       {ctx.account_id}")
            print(f"Secret Name:      {ctx.secret_name}")
            print(f"ECS Host Port:    {ctx.ecs_host_port}")
            print(f"S3 Bucket Prefix: {ctx.s3_bucket_prefix}")
            print(f"Approval Gates:   {ctx.governance_gates}")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_build_release(args):
    try:
        manifest = orchestrator.build_release(
            app_id=args.app,
            spec_path=args.spec,
            workspace_root=args.workspace or ".",
            release_id=args.release_id,
            force_rebuild=getattr(args, "force_rebuild", False)
        )
        print(f"[SUCCESS] Build & Release manifest completed (Release ID: {manifest['release_id']})")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_emergency_deploy(args):
    try:
        manifest = orchestrator.record_emergency_governance_event(
            workspace_root=args.workspace or ".",
            app_id=args.app,
            environment=args.env,
            requester=args.requester,
            incident_commander=args.incident_commander,
            emergency_approver=args.emergency_approver,
            secops_approver=args.secops_approver,
            incident_ticket_id=args.ticket,
            release_id=args.release_id
        )
        print(f"[SUCCESS] Emergency break-glass deployment authorized for {args.app} on {args.env} (Ticket: {args.ticket}, Release: {args.release_id})")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_rollback(args):
    try:
        manifest = orchestrator.execute_rollback(
            workspace_root=args.workspace or ".",
            app_id=args.app,
            environment=args.env,
            target_release_id=args.release_id,
            operator=args.operator,
            reason=args.reason or "Post-deployment regression",
            ticket_id=args.ticket
        )
        print(f"[SUCCESS] Rollback staged to previous release {args.release_id} for {args.app} on {args.env}")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_record_governance(args):
    try:
        orchestrator.record_governance_event(
            workspace_root=args.workspace or ".",
            app_id=args.app,
            environment=args.env,
            requester=args.requester,
            qa_approver=args.qa_approver,
            ops_approver=args.ops_approver,
            change_ticket_id=args.ticket,
            release_id=args.release_id
        )
        print(f"[SUCCESS] Governance two-person approval recorded for {args.app} on {args.env} (Ticket: {args.ticket})")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_validate_manifest(args):
    try:
        manifest = orchestrator.validate_release_manifest(
            manifest_path=args.manifest or "release-manifest.json",
            expected_app_id=args.app,
            workspace_root=args.workspace or "."
        )
        print(f"[SUCCESS] Release manifest verified (Release: {manifest['release_id']}, App: {manifest['application']})")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_tf_plan(args):
    try:
        plan_file = orchestrator.plan_infrastructure(
            app_id=args.app,
            environment=args.env,
            target_platform=args.platform,
            account_topology=args.topology,
            workspace_root=args.workspace or ".",
            in_docker=args.in_docker
        )
        print(f"[SUCCESS] Terraform plan generated: {plan_file}")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_tf_apply(args):
    try:
        res = orchestrator.apply_infrastructure(
            app_id=args.app,
            environment=args.env,
            target_platform=args.platform,
            account_topology=args.topology,
            plan_filename=args.plan,
            workspace_root=args.workspace or ".",
            in_docker=args.in_docker
        )
        print(f"[SUCCESS] Terraform apply completed. Outputs saved to infra-outputs.{args.env}.json")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_deploy_frontend(args):
    try:
        res = orchestrator.deploy_frontend_assets(
            app_id=args.app,
            environment=args.env,
            target_platform=args.platform,
            account_topology=args.topology,
            bucket_name=args.bucket,
            dist_dir=args.dist,
            workspace_root=args.workspace or ".",
            in_docker=args.in_docker
        )
        print(f"[SUCCESS] Frontend deployed to S3 bucket '{res['bucket_name']}'")
        print(f"          Website URL: {res['website_url']}")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_deploy_container(args):
    try:
        res = orchestrator.deploy_container_workload(
            app_id=args.app,
            environment=args.env,
            target_platform=args.platform,
            account_topology=args.topology,
            component_name=args.component,
            image_ref=args.image,
            host_port=args.host_port,
            workspace_root=args.workspace or ".",
            in_docker=args.in_docker
        )
        print(f"[SUCCESS] Container workload deployed: {res['container_name']} (Status: {res['status']})")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def cmd_verify(args):
    try:
        res = orchestrator.verify_deployment(
            app_id=args.app,
            environment=args.env,
            target_platform=args.platform,
            account_topology=args.topology,
            bucket_name=args.bucket,
            ecs_host=args.ecs_host,
            workspace_root=args.workspace or ".",
            in_docker=args.in_docker
        )
        print(f"[SUCCESS] Deployment verification PASSED ({len(res['checks'])} synthetic checks verified)")
        sys.exit(EXIT_CODE_SUCCESS)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)


def main():
    # Install SecretScrubber (A1-SEC-002)
    sys.stdout = SecretScrubber(sys.stdout)
    sys.stderr = SecretScrubber(sys.stderr)

    parser = argparse.ArgumentParser(description="Enterprise Application Delivery Platform Engine CLI")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate app.spec.yaml against JSON Schema and Pydantic rules")
    p_val.add_argument("--spec", default="app.spec.yaml", help="Path to app.spec.yaml")
    p_val.add_argument("--workspace", default=None, help="Root directory for filesystem confinement check")
    p_val.set_defaults(func=cmd_validate)

    # check-catalog
    p_cat = subparsers.add_parser("check-catalog", help="Check application authorization against catalog")
    p_cat.add_argument("--app", required=True, help="Application identifier")
    p_cat.add_argument("--env", required=True, help="Target environment")
    p_cat.add_argument("--platform", default="floci", choices=["floci", "floci-local", "aws"], help="Target platform")
    p_cat.add_argument("--topology", default="multi_account", choices=["multi_account", "single_account"], help="Account topology")
    p_cat.add_argument("--branch", default=None, help="Source Git branch")
    p_cat.add_argument("--repo", default=None, help="Source Git repository URL")
    p_cat.add_argument("--spec", default=None, help="Path to app.spec.yaml")
    p_cat.add_argument("--catalog", default=None, help="Path to applications.yaml")
    p_cat.set_defaults(func=cmd_check_catalog)

    # Auto-detect containerized execution context
    is_in_docker = os.path.exists("/.dockerenv") or bool(os.environ.get("JENKINS_HOME")) or os.environ.get("IN_DOCKER") == "true"

    # resolve
    p_res = subparsers.add_parser("resolve", help="Resolve infrastructure and security context")
    p_res.add_argument("--app", required=True, help="Application identifier")
    p_res.add_argument("--env", required=True, help="Target environment")
    p_res.add_argument("--platform", default="floci", choices=["floci", "floci-local", "aws"], help="Target platform")
    p_res.add_argument("--topology", default="multi_account", choices=["multi_account", "single_account"], help="Account topology")
    p_res.add_argument("--region", default="ap-south-1", help="Target Region")
    p_res.add_argument("--in-docker", action=argparse.BooleanOptionalAction, default=is_in_docker, help="Resolve endpoints for Docker network")
    p_res.add_argument("--format", default="shell", choices=["shell", "json", "human"], help="Output format")
    p_res.set_defaults(func=cmd_resolve)

    # build-release
    p_bld = subparsers.add_parser("build-release", help="Build components and generate release manifest")
    p_bld.add_argument("--app", default="hotel-billing", help="Application identifier")
    p_bld.add_argument("--spec", default="app.spec.yaml", help="Path to app.spec.yaml")
    p_bld.add_argument("--workspace", default=None, help="Workspace root directory")
    p_bld.add_argument("--release-id", default=None, help="Release ID (auto-generated if omitted)")
    p_bld.add_argument("--force-rebuild", action="store_true", default=False, help="Force rebuild")
    p_bld.set_defaults(func=cmd_build_release)

    # validate-manifest
    p_val_m = subparsers.add_parser("validate-manifest", help="Cryptographically validate release manifest")
    p_val_m.add_argument("--app", default="hotel-billing", help="Expected application identifier")
    p_val_m.add_argument("--manifest", default="release-manifest.json", help="Path to release manifest")
    p_val_m.add_argument("--workspace", default=None, help="Workspace root directory")
    p_val_m.set_defaults(func=cmd_validate_manifest)

    # tf-plan
    p_plan = subparsers.add_parser("tf-plan", help="Execute Terraform plan for target environment")
    p_plan.add_argument("--app", default="hotel-billing", help="Application identifier")
    p_plan.add_argument("--env", required=True, choices=["develop", "qa", "prod", "canary"], help="Target environment")
    p_plan.add_argument("--platform", default="floci", choices=["floci", "floci-local", "aws"], help="Target platform")
    p_plan.add_argument("--topology", default="multi_account", choices=["multi_account", "single_account"], help="Account topology")
    p_plan.add_argument("--workspace", default=None, help="Workspace root directory")
    p_plan.add_argument("--in-docker", action=argparse.BooleanOptionalAction, default=is_in_docker, help="Resolve endpoints for Docker network")
    p_plan.set_defaults(func=cmd_tf_plan)

    # tf-apply
    p_app = subparsers.add_parser("tf-apply", help="Execute Terraform apply for target environment")
    p_app.add_argument("--app", default="hotel-billing", help="Application identifier")
    p_app.add_argument("--env", required=True, choices=["develop", "qa", "prod", "canary"], help="Target environment")
    p_app.add_argument("--platform", default="floci", choices=["floci", "floci-local", "aws"], help="Target platform")
    p_app.add_argument("--topology", default="multi_account", choices=["multi_account", "single_account"], help="Account topology")
    p_app.add_argument("--plan", default=None, help="Plan filename (defaults to tfplan.<env>)")
    p_app.add_argument("--workspace", default=None, help="Workspace root directory")
    p_app.add_argument("--in-docker", action=argparse.BooleanOptionalAction, default=is_in_docker, help="Resolve endpoints for Docker network")
    p_app.set_defaults(func=cmd_tf_apply)

    # deploy-frontend
    p_dep = subparsers.add_parser("deploy-frontend", help="Deploy frontend static assets to S3 bucket")
    p_dep.add_argument("--app", default="hotel-billing", help="Application identifier")
    p_dep.add_argument("--env", required=True, choices=["develop", "qa", "prod"], help="Target environment")
    p_dep.add_argument("--platform", default="floci", choices=["floci", "floci-local", "aws"], help="Target platform")
    p_dep.add_argument("--topology", default="multi_account", choices=["multi_account", "single_account"], help="Account topology")
    p_dep.add_argument("--bucket", default=None, help="Destination S3 bucket name (auto-detected if omitted)")
    p_dep.add_argument("--dist", default=None, help="Frontend distribution directory")
    p_dep.add_argument("--workspace", default=None, help="Workspace root directory")
    p_dep.add_argument("--in-docker", action=argparse.BooleanOptionalAction, default=is_in_docker, help="Resolve endpoints for Docker network")
    p_dep.set_defaults(func=cmd_deploy_frontend)

    # deploy-container
    p_dep_c = subparsers.add_parser("deploy-container", help="Deploy container workload to Floci or AWS ECS")
    p_dep_c.add_argument("--app", default="sample-node-service", help="Application identifier")
    p_dep_c.add_argument("--env", required=True, choices=["develop", "qa", "prod", "canary"], help="Target environment")
    p_dep_c.add_argument("--platform", default="floci", choices=["floci", "floci-local", "aws"], help="Target platform")
    p_dep_c.add_argument("--topology", default="multi_account", choices=["multi_account", "single_account"], help="Account topology")
    p_dep_c.add_argument("--component", default=None, help="Component name (e.g. api, backend, worker)")
    p_dep_c.add_argument("--image", default=None, help="Container image URI or tag")
    p_dep_c.add_argument("--host-port", type=int, default=None, help="Host port mapping for local Floci")
    p_dep_c.add_argument("--workspace", default=None, help="Workspace root directory")
    p_dep_c.add_argument("--in-docker", action=argparse.BooleanOptionalAction, default=is_in_docker, help="Resolve endpoints for Docker network")
    p_dep_c.set_defaults(func=cmd_deploy_container)

    # verify
    p_ver = subparsers.add_parser("verify", help="Execute synthetic health checks and record audit")
    p_ver.add_argument("--app", default="hotel-billing", help="Application identifier")
    p_ver.add_argument("--env", required=True, choices=["develop", "qa", "prod", "canary"], help="Target environment")
    p_ver.add_argument("--platform", default="floci", choices=["floci", "floci-local", "aws"], help="Target platform")
    p_ver.add_argument("--topology", default="multi_account", choices=["multi_account", "single_account"], help="Account topology")
    p_ver.add_argument("--bucket", default=None, help="Frontend S3 bucket name (auto-detected if omitted)")
    p_ver.add_argument("--ecs-host", default=None, help="ECS host for synthetic check")
    p_ver.add_argument("--workspace", default=None, help="Workspace root directory")
    p_ver.add_argument("--in-docker", action=argparse.BooleanOptionalAction, default=is_in_docker, help="Resolve endpoints for Docker network")
    p_ver.set_defaults(func=cmd_verify)

    # record-governance
    p_gov = subparsers.add_parser("record-governance", help="Record two-person production governance approval")
    p_gov.add_argument("--app", default="hotel-billing", help="Application identifier")
    p_gov.add_argument("--env", required=True, choices=["develop", "qa", "prod"], help="Target environment")
    p_gov.add_argument("--requester", default="admin", help="Deployment requester identity")
    p_gov.add_argument("--qa-approver", required=True, help="QA approver identity")
    p_gov.add_argument("--ops-approver", required=True, help="Operations/SRE approver identity")
    p_gov.add_argument("--ticket", required=True, help="Change ticket identifier")
    p_gov.add_argument("--release-id", default=None, help="Approved release ID")
    p_gov.add_argument("--workspace", default=None, help="Workspace root directory")
    p_gov.set_defaults(func=cmd_record_governance)

    # emergency-deploy
    p_emg = subparsers.add_parser("emergency-deploy", help="Authorize and execute emergency break-glass production deployment")
    p_emg.add_argument("--app", default="hotel-billing", help="Application identifier")
    p_emg.add_argument("--env", required=True, choices=["develop", "qa", "prod"], help="Target environment")
    p_emg.add_argument("--release-id", required=True, help="Existing immutable release ID to deploy")
    p_emg.add_argument("--requester", required=True, help="Emergency requester identity")
    p_emg.add_argument("--incident-commander", required=True, help="Authorized incident commander")
    p_emg.add_argument("--emergency-approver", required=True, help="Independent emergency approver")
    p_emg.add_argument("--secops-approver", required=True, help="SecOps approver")
    p_emg.add_argument("--ticket", required=True, help="INC-* or HOTFIX-* ticket ID")
    p_emg.add_argument("--workspace", default=None, help="Workspace root directory")
    p_emg.set_defaults(func=cmd_emergency_deploy)

    # rollback
    p_rbk = subparsers.add_parser("rollback", help="Staged rollback to an existing verified release without rebuild")
    p_rbk.add_argument("--app", default="hotel-billing", help="Application identifier")
    p_rbk.add_argument("--env", required=True, choices=["develop", "qa", "prod"], help="Target environment")
    p_rbk.add_argument("--release-id", required=True, help="Target immutable release ID to restore")
    p_rbk.add_argument("--operator", required=True, help="Operator initiating the rollback")
    p_rbk.add_argument("--ticket", required=True, help="Change, Incident, or Rollback ticket ID")
    p_rbk.add_argument("--reason", default="Post-deployment regression", help="Rollback justification")
    p_rbk.add_argument("--workspace", default=None, help="Workspace root directory")
    p_rbk.set_defaults(func=cmd_rollback)

    # inspect-spec
    p_ins = subparsers.add_parser("inspect-spec", help="Inspect application spec and report capability summary")
    p_ins.add_argument("--spec", default="app.spec.yaml", help="Path to application specification")
    p_ins.add_argument("--workspace", default=None, help="Workspace root directory")
    p_ins.add_argument("--format", default="text", choices=["text", "json", "shell"], help="Output format")
    p_ins.add_argument("--has-container", action="store_true", help="Return true/false if spec has container components")
    p_ins.add_argument("--has-frontend", action="store_true", help="Return true/false if spec has frontend static components")
    p_ins.add_argument("--has-infra", action="store_true", help="Return true/false if spec has infrastructure dependencies")
    p_ins.add_argument("--has-worker", action="store_true", help="Return true/false if spec has worker components")
    p_ins.set_defaults(func=cmd_inspect_spec)

    # onboard-app
    p_onb = subparsers.add_parser("onboard-app", help="Register an application into the central catalog")
    p_onb.add_argument("--spec", required=True, help="Path to application specification")
    p_onb.add_argument("--repo", required=True, help="Trusted repository URL")
    p_onb.add_argument("--catalog", default=None, help="Catalog file path")
    p_onb.add_argument("--display-name", default=None, help="Human-readable display name")
    p_onb.add_argument("--security-tier", default=None, choices=["tier-1-business-critical", "tier-2-standard"], help="Security tier")
    p_onb.add_argument("--workspace", default=None, help="Workspace root directory")
    p_onb.set_defaults(func=cmd_onboard_app)

    # list-apps
    p_lst = subparsers.add_parser("list-apps", help="List all registered applications in catalog")
    p_lst.add_argument("--catalog", default=None, help="Catalog file path")
    p_lst.add_argument("--format", default="text", choices=["text", "json"], help="Output format")
    p_lst.set_defaults(func=cmd_list_apps)

    # inspect-repo
    p_rep = subparsers.add_parser("inspect-repo", help="Inspect source repository and detect components")
    p_rep.add_argument("--dir", required=True, help="Path to repository root")
    p_rep.add_argument("--emit-candidate", default=None, help="Path to write candidate app.spec.yaml")
    p_rep.add_argument("--app", default=None, help="Application identifier")
    p_rep.add_argument("--format", default="text", choices=["text", "json"], help="Output format")
    p_rep.set_defaults(func=cmd_inspect_repo)

    args = parser.parse_args()
    try:
        args.func(args)
    except PlatformException as e:
        print(f"[ERROR] [{e.code.value}] {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)
    except Exception as e:
        print(f"[FATAL_UNHANDLED_ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(EXIT_CODE_GENERAL_ERROR)


if __name__ == "__main__":
    main()
