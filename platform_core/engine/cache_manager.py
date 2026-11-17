"""
NERO Universal Enterprise DevOps Automation Platform
Hash-Based Build Cache Management (A3-BLD-002)

Provides deterministic, content-addressable build cache key generation,
manifest storage, and cache invalidation across polyglot components.
"""

import hashlib
import json
import logging
import os
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("nero.engine.cache_manager")

DEFAULT_CACHE_DIR = os.path.join(os.getcwd(), ".nero_cache")


class BuildCacheManager:
    """Manages content-addressable build artifact caches and metadata."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.manifest_dir = os.path.join(self.cache_dir, "manifests")
        os.makedirs(self.manifest_dir, exist_ok=True)

    def compute_cache_key(
        self,
        app_id: str,
        component_name: str,
        context_dir: str,
        runtime_version: str,
        lockfile_path: Optional[str] = None,
        build_args: Optional[Dict[str, Any]] = None
    ) -> str:
        """Computes deterministic SHA-256 cache key from build inputs."""
        hasher = hashlib.sha256()
        # Identity
        hasher.update(f"{app_id}:{component_name}:{runtime_version}".encode("utf-8"))

        # Build args
        if build_args:
            for k in sorted(build_args.keys()):
                hasher.update(f"{k}={build_args[k]}".encode("utf-8"))

        # Lockfile content hash if present
        if lockfile_path and os.path.isfile(lockfile_path):
            try:
                with open(lockfile_path, "rb") as f:
                    hasher.update(f.read())
            except Exception as e:
                logger.warning(f"Could not read lockfile {lockfile_path} for cache key: {e}")

        # Source files hash (walk context_dir excluding transient files)
        if os.path.isdir(context_dir):
            file_hashes = []
            for root, dirs, files in os.walk(context_dir):
                # Ignore transient/build directories
                dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "target", "dist", ".venv", "__pycache__", ".pytest_cache")]
                for file_name in sorted(files):
                    if file_name.endswith((".pyc", ".class", ".log", ".tmp")):
                        continue
                    full_path = os.path.join(root, file_name)
                    try:
                        with open(full_path, "rb") as f:
                            file_hashes.append(hashlib.md5(f.read()).hexdigest())
                    except Exception:
                        pass
            hasher.update("".join(file_hashes).encode("utf-8"))

        cache_key = hasher.hexdigest()
        return cache_key

    def has_cache(self, cache_key: str) -> bool:
        """Checks if a valid, unexpired cache entry exists."""
        manifest_path = os.path.join(self.manifest_dir, f"{cache_key}.json")
        if not os.path.isfile(manifest_path):
            return False
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("expires_at", 0) > time.time():
                return True
        except Exception:
            pass
        return False

    def get_cached_artifact(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached artifact metadata if valid."""
        if not self.has_cache(cache_key):
            return None
        manifest_path = os.path.join(self.manifest_dir, f"{cache_key}.json")
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache manifest {cache_key}: {e}")
            return None

    def store_cache(
        self,
        cache_key: str,
        artifact_metadata: Dict[str, Any],
        ttl_seconds: int = 86400 * 7  # 7 days
    ) -> None:
        """Stores artifact metadata under cache key."""
        now = time.time()
        record = {
            "cache_key": cache_key,
            "created_at": now,
            "expires_at": now + ttl_seconds,
            "artifact": artifact_metadata
        }
        manifest_path = os.path.join(self.manifest_dir, f"{cache_key}.json")
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
            logger.info(f"Stored build cache entry for [{cache_key[:12]}]")
        except Exception as e:
            logger.error(f"Failed to write cache manifest: {e}")

    def invalidate_component(self, app_id: str, component_name: str) -> int:
        """Removes all cache entries for a specific application component."""
        count = 0
        for fname in os.listdir(self.manifest_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.manifest_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    art = data.get("artifact", {})
                    if art.get("app_id") == app_id and art.get("component") == component_name:
                        os.remove(fpath)
                        count += 1
                except Exception:
                    pass
        return count
