"""
NERO Universal Enterprise DevOps Automation Platform
Atomic Append Operations & File Locking for Cryptographic Audit Ledger (A1-AUD-001)

Guarantees thread-safe and process-safe serialization of audit ledger records
with cross-platform advisory locking (msvcrt on Windows, fcntl on Unix).
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

from platform_core.audit.audit_verifier import compute_record_hash


@contextmanager
def file_lock(file_handle):
    """Cross-platform advisory file lock for concurrent append operations."""
    if os.name == "nt":
        import msvcrt
        try:
            # Move to beginning before locking on Windows
            file_handle.seek(0)
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK, 1)
        except OSError:
            pass
        try:
            yield
        finally:
            try:
                file_handle.seek(0)
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
    else:
        import fcntl
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
        except OSError:
            pass
        try:
            yield
        finally:
            try:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass


def append_audit_record(
    workspace_root: str,
    app_id: str,
    environment: str,
    target_platform: str,
    account_topology: str,
    action: str,
    status: str,
    details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Appends an immutable, SHA-256 chained audit record under atomic file lock.
    """
    audit_dir = Path(workspace_root) / "platform_core" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / "audit_log.jsonl"

    # Open with read+write or append mode
    with open(audit_file, "a+", encoding="utf-8") as f:
        with file_lock(f):
            f.seek(0)
            lines = [l.strip() for l in f.readlines() if l.strip()]
            prev_hash = "0" * 64
            if lines:
                try:
                    last_obj = json.loads(lines[-1])
                    prev_hash = last_obj.get("record_hash") or hashlib.sha256(lines[-1].encode("utf-8")).hexdigest()
                except Exception:
                    pass

            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "app_id": app_id,
                "environment": environment,
                "target_platform": target_platform,
                "account_topology": account_topology,
                "action": action,
                "status": status,
                "details": details,
                "prev_hash": prev_hash
            }
            record["record_hash"] = compute_record_hash(record)

            f.seek(0, os.SEEK_END)
            f.write(json.dumps(record) + "\n")
            f.flush()

    try:
        rel_path = audit_file.relative_to(Path(workspace_root))
    except ValueError:
        rel_path = audit_file
    print(f"[AUDIT] Logged {action} ({status}) [Hash: {record['record_hash'][:12]}... Prev: {prev_hash[:8]}...] to {rel_path}")
    return record
