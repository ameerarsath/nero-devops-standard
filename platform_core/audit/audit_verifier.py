"""
Enterprise Universal Application Delivery Platform - Audit Ledger Verifier & Checkpoint Manager
Implements canonical JSON verification, cryptographic hash chain validation, and HMAC-signed checkpoints.
"""

import os
import sys
import json
import hmac
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional


def canonical_json_bytes(obj: Dict[str, Any]) -> bytes:
    """
    Computes deterministic canonical UTF-8 bytes for a JSON object.
    Excludes volatile signatures or hashes during computation.
    """
    cleaned = {k: v for k, v in obj.items() if k not in ("record_hash", "signature", "checkpoint_signature")}
    return json.dumps(cleaned, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_record_hash(record: Dict[str, Any]) -> str:
    """
    Computes SHA-256 hash of a canonical record.
    """
    return hashlib.sha256(canonical_json_bytes(record)).hexdigest()


def verify_audit_ledger(audit_log_path: str) -> Tuple[bool, str, int]:
    """
    Verifies the integrity of an audit ledger JSONL file.
    Returns (is_valid, message, count).
    """
    path = Path(audit_log_path)
    if not path.is_file():
        return False, f"Audit log file not found at {path}", 0

    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                return False, f"Malformed JSON at line {idx}: {e}", idx

    if not records:
        return True, "Audit log is empty (valid)", 0

    # Filter chained records
    chained_records = [r for r in records if "record_hash" in r]
    if not chained_records:
        return True, f"Found {len(records)} legacy records without hash chaining", len(records)

    for i, r in enumerate(chained_records):
        # 1. Verify self-hash
        expected_hash = compute_record_hash(r)
        actual_hash = r.get("record_hash")
        if actual_hash != expected_hash:
            return False, f"Record hash mismatch at index {i} (Timestamp: {r.get('timestamp')}): computed {expected_hash[:12]} != stored {actual_hash[:12]}", i

        # 2. Verify link to previous record
        if i > 0:
            expected_prev = chained_records[i - 1].get("record_hash")
            actual_prev = r.get("prev_hash")
            if actual_prev != expected_prev:
                return False, f"Broken chain link at index {i}: prev_hash {actual_prev[:12]} does not match predecessor hash {expected_prev[:12]}", i

    return True, f"Cryptographic audit chain verified ({len(chained_records)} chained records, head: {chained_records[-1]['record_hash'][:12]}...)", len(chained_records)


def get_signing_key(override_key: Optional[bytes] = None) -> bytes:
    if override_key:
        return override_key
    env_key = os.environ.get("AUDIT_HMAC_SIGNING_KEY")
    if env_key:
        return env_key.encode("utf-8")
    return b"platform-enterprise-audit-secret-key-2026"


def create_signed_checkpoint(
    audit_log_path: str,
    checkpoint_dir: str,
    signing_key: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Creates an HMAC-SHA256 signed checkpoint of the current audit ledger head.
    Detects if an attacker replaces the entire log and recalculates hashes.
    """
    actual_key = get_signing_key(signing_key)
    valid, msg, count = verify_audit_ledger(audit_log_path)
    if not valid:
        raise ValueError(f"Cannot checkpoint invalid audit ledger: {msg}")

    with open(audit_log_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    head_hash = "0" * 64
    for line in reversed(lines):
        obj = json.loads(line)
        if "record_hash" in obj:
            head_hash = obj["record_hash"]
            break

    checkpoint = {
        "schema_version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "record_count": count,
        "head_hash": head_hash
    }

    canonical = canonical_json_bytes(checkpoint)
    sig = hmac.new(actual_key, canonical, hashlib.sha256).hexdigest()
    checkpoint["signature"] = sig

    cdir = Path(checkpoint_dir)
    cdir.mkdir(parents=True, exist_ok=True)
    cp_file = cdir / f"checkpoint-{int(datetime.now(timezone.utc).timestamp())}.json"
    with open(cp_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)

    latest_file = cdir / "checkpoint-latest.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)

    print(f"[CHECKPOINT] Created signed audit checkpoint: {cp_file.name} (Head: {head_hash[:12]}..., Count: {count})")
    return checkpoint


def verify_checkpoint(
    audit_log_path: str,
    checkpoint_path: str,
    signing_key: Optional[bytes] = None
) -> Tuple[bool, str]:
    """
    Verifies that the audit ledger matches an independently signed checkpoint.
    """
    actual_key = get_signing_key(signing_key)
    cp_path = Path(checkpoint_path)
    if not cp_path.is_file():
        return False, f"Checkpoint file not found: {cp_path}"

    with open(cp_path, "r", encoding="utf-8") as f:
        cp = json.load(f)

    # 1. Verify HMAC signature of checkpoint
    stored_sig = cp.get("signature")
    if not stored_sig:
        return False, "Checkpoint has no signature"

    canonical = canonical_json_bytes(cp)
    expected_sig = hmac.new(actual_key, canonical, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(stored_sig, expected_sig):
        return False, "Checkpoint signature invalid (tampered checkpoint or invalid HMAC key)"

    # 2. Verify audit ledger chain
    valid, msg, count = verify_audit_ledger(audit_log_path)
    if not valid:
        return False, f"Audit ledger chain invalid: {msg}"

    # 3. Verify ledger head against checkpoint
    with open(audit_log_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    actual_head = "0" * 64
    for line in reversed(lines):
        obj = json.loads(line)
        if "record_hash" in obj:
            actual_head = obj["record_hash"]
            break

    if actual_head != cp["head_hash"]:
        return False, f"Audit log head ({actual_head[:12]}...) does not match checkpoint head ({cp['head_hash'][:12]}...)"

    return True, f"Checkpoint verified against audit ledger (Head: {actual_head[:12]}..., Count: {cp['record_count']})"


if __name__ == "__main__":
    log_file = "platform_core/audit/audit_log.jsonl"
    cp_dir = "platform_core/audit/checkpoints"
    
    if len(sys.argv) > 1 and sys.argv[1] == "checkpoint":
        create_signed_checkpoint(log_file, cp_dir)
    elif len(sys.argv) > 1 and sys.argv[1] == "verify-checkpoint":
        valid, msg = verify_checkpoint(log_file, f"{cp_dir}/checkpoint-latest.json")
        print(f"[{'PASS' if valid else 'FAIL'}] {msg}")
        sys.exit(0 if valid else 1)
    else:
        valid, msg, count = verify_audit_ledger(log_file)
        print(f"[{'PASS' if valid else 'FAIL'}] {msg}")
        sys.exit(0 if valid else 1)
