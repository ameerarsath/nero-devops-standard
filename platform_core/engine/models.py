"""
NERO Universal Enterprise DevOps Automation Platform - Pydantic Data Models
Strongly-typed validation models for application specifications (A2-SCH-001).
Fully compliant with Pydantic v2 (ConfigDict, extra="forbid", strict validation).
"""

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import re


class MetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(..., pattern=r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
    version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9.]+)?$")
    id: Optional[str] = Field(None, pattern=r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
    description: Optional[str] = Field(None, max_length=500)
    owner: Optional[str] = Field(None, max_length=100)
    team: Optional[str] = Field(None, max_length=100)
    repository: Optional[str] = Field(None, max_length=300)
    securityTier: Optional[Literal["tier-1-business-critical", "tier-2-standard"]] = "tier-2-standard"
    labels: Optional[Dict[str, str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def populate_default_id(self) -> "MetadataModel":
        if not self.id:
            self.id = self.name
        return self


class SourceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: str = Field(...)
    dockerfile: Optional[str] = Field(None)
    branch_restrictions: Optional[List[str]] = Field(default_factory=list)

    @field_validator("context", "dockerfile")
    @classmethod
    def validate_safe_relative_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # Reject path traversal, absolute paths, or leading slashes / drive letters
        if ".." in v or v.startswith("/") or v.startswith("\\") or ":" in v:
            raise ValueError(f"Path must be relative and cannot contain '..' or drive letters: {v}")
        return v


class BuildModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adapter: Literal["dockerfile", "java-maven", "java-gradle", "node", "python", "go", "static"]
    target_stage: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_-]+$")
    dist_dir: Optional[str] = Field(None)
    command: Optional[str] = Field(None, max_length=200)

    @field_validator("dist_dir")
    @classmethod
    def validate_dist_dir(cls, v: Optional[str]) -> Optional[str]:
        if v and (".." in v or v.startswith("/") or v.startswith("\\") or ":" in v):
            raise ValueError(f"dist_dir must be a relative safe directory path: {v}")
        return v


class HealthCheckModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., pattern=r"^/[a-zA-Z0-9/_.-]*$")
    type: Optional[Literal["http", "tcp", "process"]] = "http"
    interval_seconds: int = Field(15, ge=5, le=300)
    timeout_seconds: int = Field(5, ge=2, le=60)
    healthy_threshold: int = Field(2, ge=1, le=10)


class RuntimeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    language: Optional[str] = None
    version: Optional[str] = None
    base_image: Optional[str] = None
    lockfile: Optional[str] = None
    command: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    cpu_units: Optional[Literal[128, 256, 512, 1024, 2048, 4096]] = 256
    memory_mb: Optional[Literal[256, 512, 1024, 2048, 4096, 8192]] = 512
    health_check: Optional[HealthCheckModel] = None


class DeploymentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adapter: Literal["ecs", "s3-static", "ecs-worker"]
    desired_count: Optional[int] = Field(1, ge=1, le=50)
    spa_routing: Optional[bool] = False
    local_port: Optional[int] = Field(None, ge=1024, le=65535)
    strategy: Optional[Literal["rolling", "recreate"]] = "rolling"


class ComponentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., pattern=r"^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$")
    type: Literal["container-service", "static-site", "worker", "scheduled-task"]
    source: SourceModel
    build: BuildModel
    runtime: Optional[RuntimeModel] = None
    deployment: DeploymentModel

    @model_validator(mode="after")
    def validate_component_consistency(self) -> "ComponentModel":
        if self.type == "container-service":
            if not self.runtime or self.runtime.port is None:
                raise ValueError(f"Component '{self.name}' of type 'container-service' must specify runtime.port")
            if self.deployment.adapter != "ecs":
                raise ValueError(f"Component '{self.name}' of type 'container-service' must use deployment.adapter 'ecs'")
        elif self.type == "static-site":
            if self.deployment.adapter != "s3-static":
                raise ValueError(f"Component '{self.name}' of type 'static-site' must use deployment.adapter 's3-static'")
            if not self.build.dist_dir:
                raise ValueError(f"Component '{self.name}' of type 'static-site' must specify build.dist_dir")
        elif self.type == "worker":
            if self.deployment.adapter not in ("ecs", "ecs-worker"):
                raise ValueError(f"Component '{self.name}' of type 'worker' must use deployment.adapter 'ecs' or 'ecs-worker'")
        return self


class DependencyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., pattern=r"^[a-z0-9][a-z0-9_-]{1,30}[a-z0-9]$")
    type: Literal["rds-postgres", "dynamodb", "sqs", "sns", "redis"]
    engine_version: Optional[str] = None
    allocated_storage_gb: Optional[int] = Field(20, ge=5, le=1000)
    hash_key: Optional[str] = "id"


class SecretFieldModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., pattern=r"^[a-zA-Z0-9_.-]+$")
    description: Optional[str] = Field(None, max_length=200)
    required: bool = True
    provider: Optional[Literal["platform-managed", "custom"]] = "platform-managed"
    reference: Optional[str] = None


class SecretsModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    schema_: List[SecretFieldModel] = Field(default_factory=list, alias="schema")


class ObservabilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics_path: Optional[str] = "/metrics"
    logging_format: Optional[Literal["json", "text"]] = "json"


class SpecModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    components: List[ComponentModel] = Field(..., min_length=1, max_length=20)
    dependencies: Optional[List[DependencyModel]] = Field(default_factory=list)
    secrets: Optional[SecretsModel] = None
    environments: Optional[List[str]] = Field(default_factory=list)
    observability: Optional[ObservabilityModel] = None

    @model_validator(mode="after")
    def validate_unique_component_names(self) -> "SpecModel":
        names = set()
        ports = set()
        for comp in self.components:
            if comp.name in names:
                raise ValueError(f"Duplicate component name detected: '{comp.name}'")
            names.add(comp.name)

            if comp.runtime and comp.runtime.port:
                if comp.runtime.port in ports:
                    raise ValueError(f"Duplicate port mapping {comp.runtime.port} in component '{comp.name}'")
                ports.add(comp.runtime.port)
        return self


class ApplicationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    apiVersion: Literal["platform.enterprise.com/v1", "platform.enterprise.com/v2", "platform.nero/v1"]
    kind: Literal["Application"]
    metadata: MetadataModel
    spec: SpecModel
