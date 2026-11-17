"""
NERO Universal Enterprise DevOps Automation Platform - Repository Metadata Inspector Engine
Performs non-intrusive, read-only inspection of source repositories to identify candidate architectures,
lockfiles, frameworks, and generate proposed candidate specifications (A2-INS-001 - A2-INS-003).
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field


class ComponentDiscovery(BaseModel):
    name: str
    type: str  # container-service | static-site | worker
    language: str
    framework: Optional[str] = None
    context_path: str
    dockerfile_path: Optional[str] = None
    lockfile: Optional[str] = None
    suggested_adapter: str
    detected_port: Optional[int] = None
    health_path: str = "/health"
    confidence: float = 1.0


class DiscoveryReport(BaseModel):
    repository_path: str
    detected_technologies: List[str] = Field(default_factory=list)
    components: List[ComponentDiscovery] = Field(default_factory=list)
    detected_dependencies: List[str] = Field(default_factory=list)
    has_lockfiles: bool = True
    lockfiles_found: List[str] = Field(default_factory=list)
    ambiguous_structures: List[str] = Field(default_factory=list)


class RepositoryInspector:
    """
    Non-intrusive AST and filesystem inspection engine.
    Never executes untrusted code from repository during inspection.
    """

    def __init__(self, repo_dir: str):
        self.repo_dir = Path(repo_dir).resolve()
        if not self.repo_dir.is_dir():
            raise ValueError(f"Repository directory not found: {repo_dir}")

    def inspect(self) -> DiscoveryReport:
        components: List[ComponentDiscovery] = []
        technologies: set = set()
        dependencies: set = set()
        lockfiles: List[str] = []
        ambiguities: List[str] = []

        # 1. Search for sub-contexts (e.g. backend, frontend, applications/*, or root)
        candidate_dirs = [self.repo_dir]
        for sub in ["backend", "frontend", "api", "web", "worker", "cmd/server"]:
            sub_p = self.repo_dir / sub
            if sub_p.is_dir():
                candidate_dirs.append(sub_p)

        # Check applications/ subdirectory if mono-repo
        apps_p = self.repo_dir / "applications"
        if apps_p.is_dir():
            for child in apps_p.iterdir():
                if child.is_dir():
                    candidate_dirs.append(child)

        # Remove parent repo if specific components were discovered
        if len(candidate_dirs) > 1 and self.repo_dir in candidate_dirs:
            # Check if root is just container or if it has sub-components
            has_subcomponents = any(d != self.repo_dir for d in candidate_dirs)
            if has_subcomponents:
                candidate_dirs.remove(self.repo_dir)

        for d in candidate_dirs:
            rel_context = str(d.relative_to(self.repo_dir)).replace("\\", "/")
            if rel_context == ".":
                rel_context = "."
            comp_name = d.name.lower().replace("_", "-")
            if comp_name == ".":
                comp_name = "api"

            # Check for Go
            go_mod = d / "go.mod"
            if go_mod.is_file():
                technologies.add("go")
                lock = "go.sum" if (d / "go.sum").is_file() else None
                if lock:
                    lockfiles.append(f"{rel_context}/go.sum")
                df = "Dockerfile" if (d / "Dockerfile").is_file() else None
                components.append(ComponentDiscovery(
                    name=comp_name,
                    type="container-service",
                    language="go",
                    framework="gin/standard",
                    context_path=rel_context,
                    dockerfile_path=df,
                    lockfile=lock,
                    suggested_adapter="go" if not df else "dockerfile",
                    detected_port=8080,
                    health_path="/health"
                ))
                continue

            # Check for Node.js
            pkg_json = d / "package.json"
            if pkg_json.is_file():
                technologies.add("nodejs")
                is_frontend = (
                    (d / "vite.config.ts").is_file() or
                    (d / "vite.config.js").is_file() or
                    (d / "src" / "App.tsx").is_file() or
                    (d / "public" / "index.html").is_file()
                )
                lock = None
                if (d / "package-lock.json").is_file():
                    lock = "package-lock.json"
                    lockfiles.append(f"{rel_context}/package-lock.json")
                elif (d / "yarn.lock").is_file():
                    lock = "yarn.lock"
                    lockfiles.append(f"{rel_context}/yarn.lock")
                else:
                    ambiguities.append(f"Node.js component at '{rel_context}' is missing a lockfile.")

                df = "Dockerfile" if (d / "Dockerfile").is_file() else None

                if is_frontend:
                    components.append(ComponentDiscovery(
                        name="frontend" if comp_name in (".", "web", "src") else comp_name,
                        type="static-site",
                        language="typescript" if (d / "tsconfig.json").is_file() else "javascript",
                        framework="react/vite",
                        context_path=rel_context,
                        dockerfile_path=df,
                        lockfile=lock,
                        suggested_adapter="node",
                        detected_port=None,
                        health_path="/index.html"
                    ))
                else:
                    components.append(ComponentDiscovery(
                        name="api" if comp_name in (".", "server", "backend") else comp_name,
                        type="container-service",
                        language="javascript",
                        framework="express",
                        context_path=rel_context,
                        dockerfile_path=df,
                        lockfile=lock,
                        suggested_adapter="dockerfile" if df else "node",
                        detected_port=8080,
                        health_path="/health"
                    ))
                continue

            # Check for Java (Maven / Gradle)
            pom_xml = d / "pom.xml"
            if pom_xml.is_file():
                technologies.add("java")
                lockfiles.append(f"{rel_context}/pom.xml")
                df = "Dockerfile" if (d / "Dockerfile").is_file() else None
                dependencies.add("rds-postgres")
                components.append(ComponentDiscovery(
                    name="backend" if comp_name in (".", "api") else comp_name,
                    type="container-service",
                    language="java",
                    framework="spring-boot",
                    context_path=rel_context,
                    dockerfile_path=df,
                    lockfile="pom.xml",
                    suggested_adapter="dockerfile" if df else "java-maven",
                    detected_port=8082,
                    health_path="/actuator/health"
                ))
                continue

            # Check for Python
            req_txt = d / "requirements.txt"
            pyproject = d / "pyproject.toml"
            has_py_files = any(d.glob("*.py"))
            if req_txt.is_file() or pyproject.is_file() or has_py_files:
                technologies.add("python")
                lock = None
                if req_txt.is_file():
                    lock = "requirements.txt"
                    lockfiles.append(f"{rel_context}/requirements.txt")
                elif pyproject.is_file():
                    lock = "pyproject.toml"
                    lockfiles.append(f"{rel_context}/pyproject.toml")
                else:
                    ambiguities.append(f"Lockfile missing: Python component at '{rel_context}' has no requirements.txt or pyproject.toml.")

                df = "Dockerfile" if (d / "Dockerfile").is_file() else None

                # Inspect if worker or web
                is_worker = (d / "worker.py").is_file() or "worker" in comp_name
                components.append(ComponentDiscovery(
                    name="worker" if is_worker else comp_name,
                    type="worker" if is_worker else "container-service",
                    language="python",
                    framework="fastapi/queue",
                    context_path=rel_context,
                    dockerfile_path=df,
                    lockfile=lock,
                    suggested_adapter="dockerfile" if df else "python",
                    detected_port=8000,
                    health_path="/health"
                ))
                continue

            # Check for standalone Dockerfile
            df_only = d / "Dockerfile"
            if df_only.is_file():
                technologies.add("container-dockerfile")
                components.append(ComponentDiscovery(
                    name=comp_name,
                    type="container-service",
                    language="polyglot",
                    context_path=rel_context,
                    dockerfile_path="Dockerfile",
                    suggested_adapter="dockerfile",
                    detected_port=8080,
                    health_path="/health"
                ))

        return DiscoveryReport(
            repository_path=str(self.repo_dir),
            detected_technologies=sorted(list(technologies)),
            components=components,
            detected_dependencies=sorted(list(dependencies)),
            has_lockfiles=len(ambiguities) == 0,
            lockfiles_found=lockfiles,
            ambiguous_structures=ambiguities
        )

    def generate_candidate_spec(
        self,
        app_id: str,
        owner: str = "engineering@enterprise.com",
        security_tier: str = "tier-2-standard"
    ) -> Dict[str, Any]:
        """
        Generates a non-authoritative candidate application specification (A2-INS-002).
        Requires human review before catalog authorization.
        """
        report = self.inspect()
        comps = []
        for c in report.components:
            comp_dict = {
                "name": c.name,
                "type": c.type,
                "source": {
                    "context": c.context_path
                },
                "build": {
                    "adapter": c.suggested_adapter
                },
                "deployment": {
                    "adapter": "s3-static" if c.type == "static-site" else "ecs"
                }
            }
            if c.dockerfile_path:
                comp_dict["source"]["dockerfile"] = c.dockerfile_path

            if c.type in ("container-service", "worker"):
                comp_dict["runtime"] = {
                    "name": c.language,
                    "language": c.language,
                    "port": c.detected_port or 8080,
                    "health_check": {
                        "path": c.health_path,
                        "type": "http"
                    }
                }
                if c.language == "go":
                    comp_dict["runtime"]["version"] = "1.27.3"
                    comp_dict["runtime"]["base_image"] = "gcr.io/distroless/static-debian12:nonroot"

            if c.type == "static-site":
                comp_dict["build"]["dist_dir"] = "dist"
                comp_dict["deployment"]["spa_routing"] = True

            comps.append(comp_dict)

        spec = {
            "apiVersion": "platform.nero/v1",
            "kind": "Application",
            "metadata": {
                "name": app_id,
                "version": "1.0.0",
                "id": app_id,
                "description": f"Candidate application specification for {app_id}",
                "owner": owner,
                "securityTier": security_tier,
                "labels": {
                    "onboarding_mode": "automated_candidate"
                }
            },
            "spec": {
                "components": comps,
                "dependencies": [{"name": "primary-db", "type": "rds-postgres"}] if "rds-postgres" in report.detected_dependencies else []
            }
        }
        return spec


def generate_candidate_spec(
    source: Any,
    app_id: str,
    owner: str = "engineering@enterprise.com",
    security_tier: str = "tier-2-standard"
) -> Dict[str, Any]:
    """
    Convenience function to generate a candidate specification from either
    a DiscoveryReport or a RepositoryInspector or directory path.
    """
    if isinstance(source, DiscoveryReport):
        # Build candidate directly from DiscoveryReport
        comps = []
        for c in source.components:
            comp_dict = {
                "name": c.name,
                "type": c.type,
                "source": {
                    "context": c.context_path
                },
                "build": {
                    "adapter": c.suggested_adapter
                },
                "deployment": {
                    "adapter": "s3-static" if c.type == "static-site" else "ecs"
                }
            }
            if c.dockerfile_path:
                comp_dict["source"]["dockerfile"] = c.dockerfile_path

            if c.type in ("container-service", "worker"):
                comp_dict["runtime"] = {
                    "name": c.language,
                    "language": c.language,
                    "port": c.detected_port or 8080,
                    "health_check": {
                        "path": c.health_path,
                        "type": "http"
                    }
                }
                if c.language == "go":
                    comp_dict["runtime"]["version"] = "1.27.3"
                    comp_dict["runtime"]["base_image"] = "gcr.io/distroless/static-debian12:nonroot"

            if c.type == "static-site":
                comp_dict["build"]["dist_dir"] = "dist"
                comp_dict["deployment"]["spa_routing"] = True

            comps.append(comp_dict)

        return {
            "apiVersion": "platform.nero/v1",
            "kind": "Application",
            "metadata": {
                "name": app_id,
                "version": "1.0.0",
                "id": app_id,
                "description": f"Candidate application specification for {app_id}",
                "owner": owner,
                "securityTier": security_tier,
                "labels": {
                    "onboarding_mode": "automated_candidate"
                }
            },
            "spec": {
                "components": comps,
                "dependencies": [{"name": "primary-db", "type": "rds-postgres"}] if "rds-postgres" in source.detected_dependencies else []
            }
        }
    elif isinstance(source, RepositoryInspector):
        return source.generate_candidate_spec(app_id=app_id, owner=owner, security_tier=security_tier)
    else:
        inspector = RepositoryInspector(str(source))
        return inspector.generate_candidate_spec(app_id=app_id, owner=owner, security_tier=security_tier)

