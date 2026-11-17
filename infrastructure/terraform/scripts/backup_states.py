"""
NERO Universal Enterprise DevOps Automation Platform
Terraform State Immutability & Pre-Apply Snapshot Backup (A1-INF-001)

Creates atomic, timestamped snapshots of Terraform state prior to plan/apply,
and provides idempotent restore capabilities.
"""

import os
import shutil
import glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List


def create_state_backup(env_dir: str, max_backups: int = 10) -> Optional[str]:
    """
    Creates a timestamped snapshot of terraform.tfstate in the target environment directory.
    Returns the backup filename if created, None if no state existed.
    """
    env_path = Path(env_dir).resolve()
    state_file = env_path / "terraform.tfstate"
    if not state_file.is_file():
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_file = env_path / f"terraform.tfstate.{timestamp}.bak"

    shutil.copy2(state_file, backup_file)

    # Prune old backups beyond max_backups
    backups = sorted(glob.glob(str(env_path / "terraform.tfstate.*.bak")))
    if len(backups) > max_backups:
        for old in backups[:-max_backups]:
            try:
                os.remove(old)
            except OSError:
                pass

    return str(backup_file)


def restore_state_backup(env_dir: str, backup_file: Optional[str] = None) -> str:
    """
    Restores the specified backup, or the most recent snapshot, to terraform.tfstate.
    """
    env_path = Path(env_dir).resolve()
    state_file = env_path / "terraform.tfstate"

    if backup_file:
        target_backup = Path(backup_file).resolve()
    else:
        backups = sorted(glob.glob(str(env_path / "terraform.tfstate.*.bak")))
        if not backups:
            raise FileNotFoundError(f"No state backup found in {env_dir}")
        target_backup = Path(backups[-1])

    if not target_backup.is_file():
        raise FileNotFoundError(f"Backup file not found: {target_backup}")

    shutil.copy2(target_backup, state_file)
    return str(target_backup)


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    bak = create_state_backup(target)
    if bak:
        print(f"[OK] State snapshot created: {bak}")
    else:
        print(f"[INFO] No existing state file to snapshot in {target}")
