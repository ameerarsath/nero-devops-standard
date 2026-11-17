"""
Enterprise Universal Application Delivery Platform - Audit Tamper Detection Tests
Proves cryptographic detection of modified records, deleted records, log truncation, and full log replacement.
"""

import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from platform_core.audit.audit_verifier import (
    verify_audit_ledger,
    create_signed_checkpoint,
    verify_checkpoint,
    compute_record_hash
)


class TestAuditTamperDetection(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test_audit_log.jsonl")
        self.cp_dir = os.path.join(self.test_dir, "checkpoints")
        self.key = b"enterprise-test-hmac-key"

        # Create a valid 4-record audit chain
        records = []
        prev = "0" * 64
        for i in range(4):
            rec = {
                "timestamp": f"2026-11-06T12:0{i}:00Z",
                "app_id": "hotel-billing",
                "environment": "develop",
                "action": f"STEP_{i}",
                "status": "PASSED",
                "prev_hash": prev
            }
            rec["record_hash"] = compute_record_hash(rec)
            prev = rec["record_hash"]
            records.append(rec)

        with open(self.log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        # Create signed checkpoint
        create_signed_checkpoint(self.log_file, self.cp_dir, signing_key=self.key)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_valid_chain(self):
        valid, msg, count = verify_audit_ledger(self.log_file)
        self.assertTrue(valid, msg)
        self.assertEqual(count, 4)

        cp_valid, cp_msg = verify_checkpoint(self.log_file, os.path.join(self.cp_dir, "checkpoint-latest.json"), signing_key=self.key)
        self.assertTrue(cp_valid, cp_msg)

    def test_02_detect_modified_intermediate_record(self):
        # Tamper with record 1
        with open(self.log_file, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f]

        records[1]["status"] = "FAILED"  # Attacker changed status without valid hash
        with open(self.log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        valid, msg, idx = verify_audit_ledger(self.log_file)
        self.assertFalse(valid)
        self.assertIn("hash mismatch", msg.lower())
        self.assertEqual(idx, 1)

    def test_03_detect_deleted_intermediate_record(self):
        # Delete record 1
        with open(self.log_file, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f]

        del records[1]
        with open(self.log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        valid, msg, idx = verify_audit_ledger(self.log_file)
        self.assertFalse(valid)
        self.assertIn("broken chain link", msg.lower())

    def test_04_detect_log_truncation(self):
        # Truncate to first 2 records
        with open(self.log_file, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f]

        with open(self.log_file, "w", encoding="utf-8") as f:
            for r in records[:2]:
                f.write(json.dumps(r) + "\n")

        # The partial chain is internally valid, but fails against checkpoint
        cp_valid, cp_msg = verify_checkpoint(self.log_file, os.path.join(self.cp_dir, "checkpoint-latest.json"), signing_key=self.key)
        self.assertFalse(cp_valid)
        self.assertIn("does not match checkpoint head", cp_msg)

    def test_05_detect_full_log_replacement_and_recomputation(self):
        # Attacker replaces the entire log with fabricated records and recomputes valid hashes
        fake_records = []
        prev = "0" * 64
        for i in range(4):
            rec = {
                "timestamp": f"2026-11-06T12:0{i}:00Z",
                "app_id": "malicious-app",
                "environment": "prod",
                "action": "UNAUTHORIZED_DEPLOY",
                "status": "PASSED",
                "prev_hash": prev
            }
            rec["record_hash"] = compute_record_hash(rec)
            prev = rec["record_hash"]
            fake_records.append(rec)

        with open(self.log_file, "w", encoding="utf-8") as f:
            for r in fake_records:
                f.write(json.dumps(r) + "\n")

        # Internal chain is valid
        valid, msg, _ = verify_audit_ledger(self.log_file)
        self.assertTrue(valid)

        # BUT checkpoint verification strictly fails!
        cp_valid, cp_msg = verify_checkpoint(self.log_file, os.path.join(self.cp_dir, "checkpoint-latest.json"), signing_key=self.key)
        self.assertFalse(cp_valid)
        self.assertIn("does not match checkpoint head", cp_msg)


if __name__ == "__main__":
    unittest.main()
