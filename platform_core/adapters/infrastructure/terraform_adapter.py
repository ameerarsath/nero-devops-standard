"""
Enterprise Universal Application Delivery Platform - Terraform Infrastructure Adapter
Manages Terraform state, state backups, idempotent secret imports, validation, planning, and applying.
"""

import os
import subprocess
import shutil
import json
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from platform_core.adapters import BaseAdapter, AdapterRequest, AdapterResult
from platform_core.engine.resolver import ResolvedEnvironmentContext
from platform_core.engine.errors import PlatformErrorCode, InfrastructureError
from infrastructure.terraform.scripts.backup_states import create_state_backup, restore_state_backup


class InfrastructureResult(BaseModel):
    environment: str
    target_platform: str
    plan_file: Optional[str] = None
    applied: bool = False
    outputs: Dict[str, Any] = Field(default_factory=dict)


class TerraformInfrastructureAdapter(BaseAdapter):

    def __init__(self):
        super().__init__(adapter_name="infra.terraform", version="1.0.0")

    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        if not shutil.which("terraform"):
            self.handle_error(PlatformErrorCode.CONFIGURATION_ERROR, "Terraform binary not found on PATH")
        return True

    def _run_cmd(self, cmd: list, cwd: str, check: bool = True, context: Optional[ResolvedEnvironmentContext] = None) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["TF_IN_AUTOMATION"] = "1"
        env["TF_INPUT"] = "0"
        
        # Automatically detect and use cached terraform plugin directory if inside Jenkins
        if not env.get("TF_DATA_DIR") and context:
            candidate = f"/var/jenkins_home/.terraform-data-{context.environment}"
            if Path(candidate).is_dir():
                env["TF_DATA_DIR"] = candidate
        
        print(f"[{self.adapter_name}] Executing: {' '.join(cmd)} (cwd: {cwd})")
        res = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
        if check and res.returncode != 0:
            self.handle_error(
                PlatformErrorCode.INFRASTRUCTURE_FAILURE,
                f"Command failed ({res.returncode}): {res.stderr}\n{res.stdout}"
            )
        return res

    def import_secret_if_exists(self, context: ResolvedEnvironmentContext, workspace_root: str):
        """
        Idempotently checks if the secret already exists in Floci/AWS,
        and imports it into state if missing, preventing ResourceExistsException.
        """
        tf_dir = str(Path(workspace_root) / context.terraform_dir)
        secret_arn = None

        if context.target_platform in ["floci", "floci-local"]:
            # Direct REST query to Floci Secrets Manager
            endpoint = context.floci_endpoint or "http://floci:4566"
            try:
                body = json.dumps({"SecretId": context.secret_name}).encode("utf-8")
                req = urllib.request.Request(
                    f"{endpoint}/",
                    data=body,
                    headers={
                        "X-Amz-Target": "secretsmanager.DescribeSecret",
                        "Content-Type": "application/x-amz-json-1.1",
                        "Authorization": f"AWS4-HMAC-SHA256 Credential={context.account_id}/20261106/us-east-1/secretsmanager/aws4_request, SignedHeaders=content-type;host;x-amz-target, Signature=mock"
                    }
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode())
                    secret_arn = data.get("ARN")
            except Exception:
                pass

        if secret_arn:
            # Check if already in state
            list_res = self._run_cmd(["terraform", "state", "list"], cwd=tf_dir, check=False, context=context)
            target_res = "module.app_secrets.aws_secretsmanager_secret.app_secrets"
            if target_res not in list_res.stdout:
                print(f"[{self.adapter_name}] Importing pre-existing secret '{secret_arn}' into Terraform state...")
                var_args = [
                    f"-var=floci_endpoint={context.floci_endpoint}",
                    f"-var=aws_account_id={context.account_id}"
                ] if context.target_platform in ["floci", "floci-local"] else []
                self._run_cmd(["terraform", "import"] + var_args + [target_res, secret_arn], cwd=tf_dir, check=False, context=context)

    def plan(self, context: ResolvedEnvironmentContext, workspace_root: str) -> str:
        self.validate_prerequisites({})
        tf_dir = str(Path(workspace_root) / context.terraform_dir)

        # 0. Pre-Plan State Backup (A1-INF-001)
        backup_path = create_state_backup(tf_dir)
        if backup_path:
            print(f"[{self.adapter_name}] Pre-plan state backup created: {backup_path}")
        
        # 1. Preflight Format & Syntax Validation (A1-INF-002)
        fmt_res = self._run_cmd(["terraform", "fmt", "-check"], cwd=tf_dir, check=False, context=context)
        if fmt_res.returncode != 0:
            print(f"[{self.adapter_name}] [NOTICE] Terraform formatting check flagged deviations: {fmt_res.stdout.strip()}")

        self._run_cmd(["terraform", "validate"], cwd=tf_dir, check=True, context=context)

        # 2. Idempotent Secret Import
        self.import_secret_if_exists(context, workspace_root)

        # 3. Generate Plan
        plan_filename = f"tfplan.{context.environment}"
        cmd = ["terraform", "plan", "-out", plan_filename, "-no-color"]
        if context.target_platform in ["floci", "floci-local"]:
            cmd.extend([
                f"-var=floci_endpoint={context.floci_endpoint}",
                f"-var=aws_account_id={context.account_id}"
            ])
            if context.ecs_host_port:
                cmd.append(f"-var=ecs_host_port={context.ecs_host_port}")

        self._run_cmd(cmd, cwd=tf_dir, context=context)
        print(f"[{self.adapter_name}] Generated Terraform plan: {plan_filename}")
        return plan_filename

    def apply(self, context: ResolvedEnvironmentContext, workspace_root: str, plan_filename: str) -> InfrastructureResult:
        tf_dir = str(Path(workspace_root) / context.terraform_dir)

        # 0. Pre-Apply State Backup (A1-INF-001)
        backup_path = create_state_backup(tf_dir)
        if backup_path:
            print(f"[{self.adapter_name}] Pre-apply state backup created: {backup_path}")

        cmd = ["terraform", "apply", "-input=false", plan_filename]
        self._run_cmd(cmd, cwd=tf_dir, context=context)

        # Extract outputs
        out_res = self._run_cmd(["terraform", "output", "-json"], cwd=tf_dir, check=False, context=context)
        outputs = {}
        if out_res.returncode == 0 and out_res.stdout.strip():
            try:
                raw_out = json.loads(out_res.stdout)
                outputs = {k: v.get("value") for k, v in raw_out.items()}
            except Exception:
                pass
        
        # Fallback to direct state file reading if outputs dict is empty
        if not outputs:
            state_file = Path(tf_dir) / "terraform.tfstate"
            if state_file.is_file():
                try:
                    with open(state_file, "r") as sf:
                        s_data = json.load(sf)
                        raw_outputs = s_data.get("outputs", {})
                        outputs = {k: v.get("value") for k, v in raw_outputs.items()}
                except Exception:
                    pass

        print(f"[{self.adapter_name}] Terraform apply completed successfully.")
        return InfrastructureResult(
            environment=context.environment,
            target_platform=context.target_platform,
            plan_file=plan_filename,
            applied=True,
            outputs=outputs
        )

    def execute(self, request: AdapterRequest) -> AdapterResult:
        """Executes the requested infrastructure operation."""
        action = request.action.lower()
        if action == "backup":
            env_dir = request.parameters.get("env_dir", ".")
            path = create_state_backup(env_dir)
            return AdapterResult(
                adapter_name=self.adapter_name,
                success=True,
                data={"backup_path": path}
            )
        elif action == "restore":
            env_dir = request.parameters.get("env_dir", ".")
            backup_file = request.parameters.get("backup_file")
            restored = restore_state_backup(env_dir, backup_file)
            return AdapterResult(
                adapter_name=self.adapter_name,
                success=True,
                data={"restored_file": restored}
            )
        return super().execute(request)
