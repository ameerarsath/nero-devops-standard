"""
Enterprise Universal Application Delivery Platform - Centralized Platform Configuration
Validates environment definitions, enforces active environment boundaries, and prevents
silent real-AWS fallback.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

from platform_core.engine.errors import ConfigurationError, SecurityPolicyError


class EnvironmentConfigModel(BaseModel):
    type: Literal["simulator", "aws"]
    enabled: bool = True
    status: str = Field("ACTIVE", pattern=r"^[A-Z_]+$")
    endpoint: Optional[str] = None
    in_docker_endpoint: Optional[str] = None
    region: str = Field(..., pattern=r"^[a-z0-9-]+$")
    account_namespace: Optional[str] = None
    authentication: str
    aws_profile: Optional[str] = None
    allow_real_aws_fallback: bool = False
    description: Optional[str] = None

    @field_validator("allow_real_aws_fallback")
    @classmethod
    def validate_no_fallback(cls, v: bool) -> bool:
        if v is True:
            raise SecurityPolicyError(
                "Enterprise Security Policy Violation: Silent real-AWS fallback is strictly prohibited. "
                "'allow_real_aws_fallback' must remain False."
            )
        return v

    @model_validator(mode="after")
    def validate_simulator_endpoints(self) -> "EnvironmentConfigModel":
        if self.type == "simulator":
            if not self.endpoint:
                raise ValueError("Simulator environment must define 'endpoint'")
            if not self.account_namespace:
                self.account_namespace = "000000000000"
        return self


class DeploymentConfigModel(BaseModel):
    active_environment: str
    allowed_environments: List[str] = Field(default_factory=lambda: ["floci-local", "aws-production"])


class PlatformMetadataModel(BaseModel):
    version: str
    description: Optional[str] = None


class PlatformConfigModel(BaseModel):
    platform: PlatformMetadataModel
    deployment: DeploymentConfigModel
    environments: Dict[str, EnvironmentConfigModel]

    @model_validator(mode="after")
    def validate_active_environment_exists(self) -> "PlatformConfigModel":
        active = self.deployment.active_environment
        if active not in self.environments:
            raise ValueError(
                f"Active environment '{active}' is not defined in environments: {list(self.environments.keys())}"
            )
        active_env = self.environments[active]
        if not active_env.enabled:
            raise ValueError(f"Active environment '{active}' is marked disabled (enabled=False).")
        return self


def load_platform_config(config_path: Optional[str] = None) -> PlatformConfigModel:
    """
    Loads and validates the central platform configuration from YAML.
    """
    if not config_path:
        # Search relative to repository root or current file
        candidates = [
            Path("platform_config.yaml"),
            Path(__file__).resolve().parent.parent.parent / "platform_config.yaml"
        ]
        config_file = next((c for c in candidates if c.is_file()), None)
        if not config_file:
            raise ConfigurationError("Central platform configuration file 'platform_config.yaml' not found.")
    else:
        config_file = Path(config_path)
        if not config_file.is_file():
            raise ConfigurationError(f"Platform configuration file not found at '{config_path}'")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
        return PlatformConfigModel.model_validate(raw_data)
    except Exception as e:
        raise ConfigurationError(f"Failed validating platform_config.yaml: {e}") from e


def get_active_environment_config(config_path: Optional[str] = None) -> EnvironmentConfigModel:
    """
    Returns the resolved EnvironmentConfigModel for the currently active deployment environment.
    """
    cfg = load_platform_config(config_path)
    active_name = cfg.deployment.active_environment
    return cfg.environments[active_name]


def export_json_schema(target_path: Optional[str] = None) -> str:
    """
    Generates and optionally writes the JSON Schema for the platform configuration.
    """
    schema = PlatformConfigModel.model_json_schema()
    schema_str = json.dumps(schema, indent=2)
    if target_path:
        out_file = Path(target_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(schema_str)
    return schema_str
