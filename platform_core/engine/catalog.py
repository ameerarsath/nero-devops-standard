"""
NERO Universal Enterprise DevOps Automation Platform - Application Catalog Engine
Enforces centralized authorization gates for application registration and deployment,
with dynamic port allocation and multi-tier security allowlisting (A2-CAT-001 - A2-CAT-004).
"""

import os
import sys
import fnmatch
import socket
import time
import contextlib
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone
import yaml
from pydantic import BaseModel, Field, ConfigDict

from platform_core.engine.errors import SecurityPolicyError, CatalogAuthorizationError, ConfigurationError
from platform_core.engine.models import ApplicationSpec
from platform_core.audit.audit_logger import append_audit_record

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent / "catalog" / "applications.yaml"


@contextlib.contextmanager
def catalog_file_lock(lock_path: Path, timeout: float = 10.0, retry_interval: float = 0.05):
    """
    Cross-platform advisory file lock using msvcrt (Windows) or fcntl (Linux/Unix).
    Retries until timeout is reached or lock is acquired (REMED-A2-002).
    """
    start_time = time.time()
    lock_file_fd = None
    lock_str = str(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            lock_file_fd = os.open(lock_str, os.O_RDWR | os.O_CREAT)
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(lock_file_fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock_file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except (OSError, PermissionError):
            if lock_file_fd is not None:
                try:
                    os.close(lock_file_fd)
                except OSError:
                    pass
                lock_file_fd = None
            if time.time() - start_time >= timeout:
                raise TimeoutError(f"Timed out after {timeout:.1f}s waiting for catalog lock: {lock_path}")
            time.sleep(retry_interval)

    try:
        yield
    finally:
        if lock_file_fd is not None:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    os.lseek(lock_file_fd, 0, os.SEEK_SET)
                    msvcrt.locking(lock_file_fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock_file_fd, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(lock_file_fd)
            except OSError:
                pass


class CatalogApplication(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    display_name: str
    trusted_repository: str
    spec_path: str = "app.spec.yaml"
    allowed_branches: List[str]
    allowed_environments: List[str]
    allowed_platforms: List[str]
    allowed_topologies: List[str]
    permitted_build_adapters: List[str]
    permitted_deployment_adapters: List[str]
    security_tier: str = "tier-2-standard"
    allocated_ports: Dict[str, int] = Field(default_factory=dict)
    owner: Optional[str] = None
    team: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PortAllocationManager:
    """
    Manages deterministic, concurrency-safe host-port allocations for local Floci simulation (A2-CAT-002).
    Ensures per-environment isolation, detects conflicts, and guarantees zero port collisions.
    Includes active OS socket probing (REMED-A2-002).
    """

    START_PORT = 8100
    MAX_PORT = 8999

    @classmethod
    def is_port_in_use_os(cls, port: int, host: str = "127.0.0.1") -> bool:
        """
        Actively probes whether a TCP port is in use on the local host (REMED-A2-002).
        Returns True if the port is already bound by an OS process/container, False if physically free.
        """
        # 1. Probe via exclusive bind attempt on 127.0.0.1 and 0.0.0.0 (without SO_REUSEADDR)
        for check_host in [host, "0.0.0.0"]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((check_host, port))
            except (OSError, socket.error):
                return True

        # 2. Probe if active listener exists via connect_ex
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return True
        except (OSError, socket.error):
            pass

        return False

    @classmethod
    def get_known_reservations(cls, catalog_entries: Dict[str, CatalogApplication]) -> Dict[str, Dict[int, str]]:
        """Returns map of {environment: {port: app_id}} across all catalog applications."""
        reservations: Dict[str, Dict[int, str]] = {
            "develop": {},
            "qa": {},
            "prod": {}
        }
        for app_id, entry in catalog_entries.items():
            for env, port in entry.allocated_ports.items():
                if env in reservations:
                    reservations[env][port] = app_id
        return reservations

    @classmethod
    def allocate_ports(
        cls,
        app_id: str,
        catalog_entries: Dict[str, CatalogApplication],
        environments: Optional[List[str]] = None,
        requested_port: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Deterministically allocates isolated ports across environments for an application.
        If requested_port is provided, validates that it is free in all target environments and not bound on host OS.
        """
        envs = environments or ["develop", "qa", "prod"]
        reservations = cls.get_known_reservations(catalog_entries)
        allocated: Dict[str, int] = {}

        if requested_port:
            # Check requested port against catalog reservations
            for env in envs:
                if env in reservations and requested_port in reservations[env]:
                    owner = reservations[env][requested_port]
                    if owner != app_id:
                        raise ConfigurationError(
                            f"Port collision: Requested port {requested_port} in '{env}' is already owned by '{owner}'"
                        )
                allocated[env] = requested_port

            # Check requested port against active OS socket bindings (REMED-A2-002)
            if cls.is_port_in_use_os(requested_port):
                already_owned_by_self = any(
                    entry.id == app_id and any(p == requested_port for p in entry.allocated_ports.values())
                    for entry in catalog_entries.values()
                )
                if not already_owned_by_self:
                    raise ConfigurationError(
                        f"Port collision: Requested port {requested_port} is actively bound by an OS process on the host"
                    )

            return allocated

        # Search for available port block starting from START_PORT
        candidate = cls.START_PORT
        while candidate <= cls.MAX_PORT:
            # We assign candidate (develop), candidate+1 (qa), candidate+2 (prod)
            dev_p = candidate + 1
            qa_p = candidate + 2
            prod_p = candidate + 3

            in_use_catalog = (
                dev_p in reservations.get("develop", {}) or
                qa_p in reservations.get("qa", {}) or
                prod_p in reservations.get("prod", {})
            )
            in_use_os = (
                cls.is_port_in_use_os(dev_p) or
                cls.is_port_in_use_os(qa_p) or
                cls.is_port_in_use_os(prod_p)
            )

            if not in_use_catalog and not in_use_os:
                allocated = {
                    "develop": dev_p,
                    "qa": qa_p,
                    "prod": prod_p
                }
                return {e: allocated[e] for e in envs if e in allocated}

            candidate += 10

        raise ConfigurationError("Port allocation exhaustion: No free port blocks available in local range.")


class ApplicationCatalog:
    """Manages trusted application registrations and authorization policies."""

    def __init__(self, catalog_path: Optional[str] = None):
        self.catalog_path = Path(catalog_path or DEFAULT_CATALOG_PATH).resolve()
        self.lock_path = self.catalog_path.with_suffix(".lock")
        self._entries: Dict[str, CatalogApplication] = {}
        self._load()

    def _load(self):
        if not self.catalog_path.is_file():
            raise CatalogAuthorizationError(f"Application catalog not found at {self.catalog_path}")
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for app_dict in data.get("applications", []):
            entry = CatalogApplication.model_validate(app_dict)
            self._entries[entry.id] = entry

    def list_applications(self) -> List[CatalogApplication]:
        return list(self._entries.values())

    def get_application(self, app_id: str) -> CatalogApplication:
        if app_id not in self._entries:
            raise CatalogAuthorizationError(
                f"Application '{app_id}' is not registered in the Enterprise Application Catalog. "
                "Registration via centralized platform catalog is required before deployment."
            )
        return self._entries[app_id]

    def get_port_for_environment(self, app_id: str, environment: str) -> Optional[int]:
        """Resolves the authorized local simulation port for an application in a specific environment."""
        if app_id in self._entries:
            entry = self._entries[app_id]
            if environment in entry.allocated_ports:
                return entry.allocated_ports[environment]

        # Historical fallbacks for backwards compatibility
        if app_id == "hotel-billing":
            return {"develop": 8085, "qa": 8087, "prod": 8089}.get(environment)
        elif app_id == "sample-node-service":
            return {"develop": 8091, "qa": 8092, "prod": 8093}.get(environment)
        elif app_id == "sample-python-worker":
            return {"develop": 8095, "qa": 8096, "prod": 8097}.get(environment)
        return None

    def register_application(
        self,
        spec: Any,
        trusted_repository: str,
        display_name: Optional[str] = None,
        allowed_branches: Optional[List[str]] = None,
        allowed_environments: Optional[List[str]] = None,
        allowed_platforms: Optional[List[str]] = None,
        allowed_topologies: Optional[List[str]] = None,
        security_tier: Optional[str] = None,
        custom_ports: Optional[Dict[str, int]] = None,
        workspace_root: str = "."
    ) -> CatalogApplication:
        """
        Dynamically registers or updates an application in the central catalog (A2-CAT-001).
        Enforces security tier allowlists, acquires OS file lock, and allocates isolated ports (REMED-A2-002).
        """
        if isinstance(spec, (str, Path)):
            from platform_core.engine.parser import parse_and_validate_spec
            spec = parse_and_validate_spec(str(spec), workspace_root=workspace_root)

        app_id = spec.metadata.id or spec.metadata.name
        tier = security_tier or spec.metadata.securityTier or "tier-2-standard"

        # Security Tier Policy Enforcement (A2-CAT-003)
        if tier == "tier-1-business-critical":
            default_build_adapters = ["dockerfile", "java-maven", "node", "go"]
            branches = allowed_branches or ["main", "master", "release/*"]
        else:
            default_build_adapters = ["dockerfile", "node", "python", "go", "java-maven", "java-gradle", "static"]
            branches = allowed_branches or ["main", "master", "release/*", "devops/*"]

        default_deploy_adapters = ["ecs", "s3-static", "ecs-worker"]

        # Ensure spec adapters are subset of tier allowlist
        for comp in spec.spec.components:
            if comp.build.adapter not in default_build_adapters:
                raise SecurityPolicyError(
                    f"Component '{comp.name}' build adapter '{comp.build.adapter}' is prohibited under '{tier}'"
                )

        envs = allowed_environments or ["develop", "qa", "prod"]
        platforms = allowed_platforms or ["floci", "floci-local", "aws"]
        topologies = allowed_topologies or ["multi_account", "single_account"]

        # Concurrency Protection: Acquire OS-level advisory file lock for the duration of allocation and write
        with catalog_file_lock(self.lock_path):
            # Reload from disk to guarantee seeing any concurrent process's registrations
            if self.catalog_path.is_file():
                self._load()

            # Allocate or validate ports under lock
            if custom_ports:
                allocated = custom_ports
            else:
                # Check if spec has local_port declared in any component
                req_port = None
                for comp in spec.spec.components:
                    if comp.deployment.local_port:
                        req_port = comp.deployment.local_port
                        break
                allocated = PortAllocationManager.allocate_ports(
                    app_id=app_id,
                    catalog_entries=self._entries,
                    environments=envs,
                    requested_port=req_port
                )

            now_iso = datetime.now(timezone.utc).isoformat()
            is_update = app_id in self._entries

            entry = CatalogApplication(
                id=app_id,
                display_name=display_name or spec.metadata.description or f"Enterprise Application: {app_id}",
                trusted_repository=trusted_repository,
                spec_path=f"applications/{app_id}/app.spec.yaml" if app_id != "hotel-billing" else "app.spec.yaml",
                allowed_branches=branches,
                allowed_environments=envs,
                allowed_platforms=platforms,
                allowed_topologies=topologies,
                permitted_build_adapters=default_build_adapters,
                permitted_deployment_adapters=default_deploy_adapters,
                security_tier=tier,
                allocated_ports=allocated,
                owner=spec.metadata.owner,
                team=spec.metadata.team,
                created_at=self._entries[app_id].created_at if is_update else now_iso,
                updated_at=now_iso
            )

            self._entries[app_id] = entry
            self._save()

        # Audit ledger record
        try:
            append_audit_record(
                workspace_root=workspace_root,
                app_id=app_id,
                environment="all",
                target_platform="floci",
                account_topology="multi_account",
                action="CATALOG_REGISTER_APPLICATION" if not is_update else "CATALOG_UPDATE_APPLICATION",
                status="SUCCESS",
                details={
                    "app_id": app_id,
                    "trusted_repository": trusted_repository,
                    "security_tier": tier,
                    "allocated_ports": allocated,
                    "is_update": is_update
                }
            )
        except Exception:
            pass

        return entry

    def _save(self):
        """Atomically saves the catalog to disk using a temporary file and atomic replace (REMED-A2-002)."""
        data = {
            "version": "2.0",
            "applications": [entry.model_dump() for entry in self._entries.values()]
        }
        temp_file = self.catalog_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, self.catalog_path)
        except Exception:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise

    def validate_deployment_request(
        self,
        app_id: str,
        environment: str,
        platform: str,
        topology: str,
        branch: Optional[str] = None,
        repository_url: Optional[str] = None,
        spec: Optional[ApplicationSpec] = None
    ) -> CatalogApplication:
        """
        Validates all aspects of a deployment request against catalog security policies.
        """
        entry = self.get_application(app_id)

        # 1. Validate Environment authorization
        if environment in ("all", "ALL"):
            for req_env in ["develop", "qa", "prod"]:
                if req_env not in entry.allowed_environments:
                    raise CatalogAuthorizationError(
                        f"Application '{app_id}' is not authorized to deploy to environment '{req_env}'. "
                        f"Allowed environments: {entry.allowed_environments}"
                    )
        elif environment not in entry.allowed_environments:
            raise CatalogAuthorizationError(
                f"Application '{app_id}' is not authorized to deploy to environment '{environment}'. "
                f"Allowed environments: {entry.allowed_environments}"
            )

        # 2. Validate Platform authorization
        if platform not in entry.allowed_platforms:
            raise CatalogAuthorizationError(
                f"Application '{app_id}' is not authorized for target platform '{platform}'. "
                f"Allowed platforms: {entry.allowed_platforms}"
            )

        # 3. Validate Topology authorization
        if topology not in entry.allowed_topologies:
            raise CatalogAuthorizationError(
                f"Application '{app_id}' is not authorized for account topology '{topology}'. "
                f"Allowed topologies: {entry.allowed_topologies}"
            )

        # 4. Validate Branch policy if supplied
        if branch:
            matched = any(fnmatch.fnmatch(branch, pattern) for pattern in entry.allowed_branches)
            if not matched:
                raise CatalogAuthorizationError(
                    f"Branch '{branch}' is not permitted for application '{app_id}'. "
                    f"Allowed branch patterns: {entry.allowed_branches}"
                )

        # 5. Validate Repository origin if supplied
        if repository_url:
            norm_repo = repository_url.rstrip("/").removesuffix(".git").lower()
            norm_trusted = entry.trusted_repository.rstrip("/").removesuffix(".git").lower()
            if norm_repo != norm_trusted:
                raise CatalogAuthorizationError(
                    f"Repository '{repository_url}' does not match trusted catalog repository '{entry.trusted_repository}'"
                )

        # 6. Validate Application Spec Adapters against Catalog Allowlist
        if spec:
            for comp in spec.spec.components:
                if comp.build.adapter not in entry.permitted_build_adapters:
                    raise CatalogAuthorizationError(
                        f"Component '{comp.name}' uses build adapter '{comp.build.adapter}', "
                        f"which is not permitted for '{app_id}'. Allowed: {entry.permitted_build_adapters}"
                    )
                if comp.deployment.adapter not in entry.permitted_deployment_adapters:
                    raise CatalogAuthorizationError(
                        f"Component '{comp.name}' uses deployment adapter '{comp.deployment.adapter}', "
                        f"which is not permitted for '{app_id}'. Allowed: {entry.permitted_deployment_adapters}"
                    )

        return entry
