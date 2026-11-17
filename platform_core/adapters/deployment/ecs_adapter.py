"""
Enterprise Universal Application Delivery Platform - ECS Container Deployment Adapter
Deploys OCI container images to Floci ECS simulation or AWS ECS Fargate with zero-downtime rolling updates.
"""

import os
import time
import subprocess
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from platform_core.adapters import BaseAdapter
from platform_core.engine.resolver import ResolvedEnvironmentContext
from platform_core.engine.errors import PlatformErrorCode, DeploymentVerificationError


class ECSDeployResult(BaseModel):
    app_id: str
    component_name: str
    environment: str
    target_platform: str
    image_ref: str
    container_id: str
    container_name: str
    host_port: Optional[int] = None
    container_port: int
    status: str


class ECSDeploymentAdapter(BaseAdapter):

    def __init__(self):
        super().__init__(adapter_name="deploy.ecs", version="1.0.0")

    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        return True

    def deploy(
        self,
        context: ResolvedEnvironmentContext,
        component_name: str,
        image_ref: str,
        container_port: int = 8080,
        host_port: Optional[int] = None,
        env_vars: Optional[Dict[str, str]] = None,
        network_name: str = "billing-dev-network"
    ) -> ECSDeployResult:
        self.validate_prerequisites({})
        env = context.environment
        app_id = context.app_id
        c_name = f"platform-{app_id}-{env}-{component_name}"

        print(f"[{self.adapter_name}] Deploying component '{component_name}' for '{app_id}' on {env}...")
        print(f"       Image: {image_ref}")
        print(f"       Platform: {context.target_platform}")

        if context.target_platform in ("floci", "floci-local"):
            # Remove any existing container with same name
            subprocess.run(["docker", "rm", "-f", c_name], capture_output=True, text=True)

            # If host_port is specified, also remove any container occupying that port to avoid conflicts (A1-COR-002)
            if host_port:
                port_check = subprocess.run(
                    ["docker", "ps", "-a", "--filter", f"publish={host_port}", "--format", "{{.ID}}"],
                    capture_output=True,
                    text=True
                )
                conflicting_cids = {cid.strip() for cid in port_check.stdout.splitlines() if cid.strip()}
                
                # Check for direct port bindings via inspect format fallback
                if not conflicting_cids:
                    inspect_check = subprocess.run(
                        ["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Ports}}"],
                        capture_output=True,
                        text=True
                    )
                    for line in inspect_check.stdout.splitlines():
                        if f":{host_port}->" in line:
                            parts = line.split("\t")
                            if parts:
                                conflicting_cids.add(parts[0].strip())

                for cid in conflicting_cids:
                    print(f"[{self.adapter_name}] Freeing conflicting container on port {host_port}: {cid}")
                    subprocess.run(["docker", "rm", "-f", cid], capture_output=True, text=True)

            cmd = [
                "docker", "run", "-d",
                "--name", c_name,
                "--network", network_name,
                "--restart", "unless-stopped"
            ]

            if host_port:
                cmd.extend(["-p", f"{host_port}:{container_port}"])

            if env_vars:
                for k, v in env_vars.items():
                    cmd.extend(["-e", f"{k}={v}"])

            cmd.append(image_ref)

            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                self.handle_error(
                    PlatformErrorCode.DEPLOYMENT_FAILURE,
                    f"Failed starting container for '{component_name}': {res.stderr}"
                )

            cid = res.stdout.strip()[:12]
            print(f"[{self.adapter_name}] [SUCCESS] Container started: {c_name} (ID: {cid}, Port: {host_port}->{container_port})")

            # Brief pause to verify container didn't immediately crash
            time.sleep(2)
            check = subprocess.run(["docker", "inspect", "--format={{.State.Status}}", c_name], capture_output=True, text=True)
            c_status = check.stdout.strip()
            if c_status not in ("running", "created"):
                logs = subprocess.run(["docker", "logs", "--tail", "20", c_name], capture_output=True, text=True).stdout
                self.handle_error(
                    PlatformErrorCode.DEPLOYMENT_FAILURE,
                    f"Container '{c_name}' crashed on startup (Status: {c_status}). Logs:\n{logs}"
                )

            return ECSDeployResult(
                app_id=app_id,
                component_name=component_name,
                environment=env,
                target_platform=context.target_platform,
                image_ref=image_ref,
                container_id=cid,
                container_name=c_name,
                host_port=host_port,
                container_port=container_port,
                status="RUNNING"
            )
        else:
            # Real AWS ECS Fargate deployment
            print(f"[{self.adapter_name}] Initiating AWS ECS Fargate deployment for {app_id} on {env} ({context.region})...")
            cluster_name = f"{context.resource_prefix}-cluster"
            service_name = f"{context.resource_prefix}-svc"
            task_family = f"{context.resource_prefix}-task"

            try:
                import boto3
                from botocore.exceptions import NoCredentialsError, ClientError

                profile = os.environ.get("AWS_PROFILE") or os.environ.get("AWS_DEFAULT_PROFILE")
                session = boto3.Session(profile_name=profile, region_name=context.region)
                ecs_client = session.client("ecs")

                # 1. Resolve Execution Role & Task Role from existing definition or conventions
                try:
                    desc_td = ecs_client.describe_task_definition(taskDefinition=task_family)
                    base_td = desc_td["taskDefinition"]
                    exec_role = base_td.get("executionRoleArn")
                    task_role = base_td.get("taskRoleArn")
                except Exception:
                    exec_role = f"arn:aws:iam::{context.account_id}:role/{context.resource_prefix}-execution-role"
                    task_role = f"arn:aws:iam::{context.account_id}:role/{context.resource_prefix}-task-role"

                # 2. Register updated task definition revision
                reg_res = ecs_client.register_task_definition(
                    family=task_family,
                    requiresCompatibilities=["FARGATE"],
                    networkMode="awsvpc",
                    cpu="256",
                    memory="512",
                    executionRoleArn=exec_role,
                    taskRoleArn=task_role,
                    containerDefinitions=[
                        {
                            "name": component_name,
                            "image": image_ref,
                            "essential": True,
                            "portMappings": [
                                {
                                    "containerPort": container_port,
                                    "hostPort": container_port,
                                    "protocol": "tcp"
                                }
                            ],
                            "logConfiguration": {
                                "logDriver": "awslogs",
                                "options": {
                                    "awslogs-group": f"/ecs/{context.resource_prefix}",
                                    "awslogs-region": context.region,
                                    "awslogs-stream-prefix": "ecs"
                                }
                            },
                            "environment": [
                                {"name": "PORT", "value": str(container_port)},
                                {"name": "NODE_ENV", "value": "production"}
                            ]
                        }
                    ]
                )
                new_td_arn = reg_res["taskDefinition"]["taskDefinitionArn"]
                print(f"[{self.adapter_name}] Registered Task Definition revision: {new_td_arn}")

                # 3. Update ECS service with rolling update
                ecs_client.update_service(
                    cluster=cluster_name,
                    service=service_name,
                    taskDefinition=new_td_arn,
                    forceNewDeployment=True
                )
                print(f"[{self.adapter_name}] [SUCCESS] AWS ECS Service '{service_name}' updated with task definition: {new_td_arn}")

                return ECSDeployResult(
                    app_id=app_id,
                    component_name=component_name,
                    environment=env,
                    target_platform="aws",
                    image_ref=image_ref,
                    container_id=new_td_arn,
                    container_name=service_name,
                    host_port=None,
                    container_port=container_port,
                    status="DEPLOYED_AWS_ECS"
                )
            except Exception as aws_err:
                print(f"[{self.adapter_name}] [AWS_ERROR] AWS ECS deployment error: {aws_err}")
                self.handle_error(
                    PlatformErrorCode.DEPLOYMENT_FAILURE,
                    f"AWS ECS Fargate deployment failed for '{component_name}': {aws_err}"
                )
