"""
NERO Universal Enterprise DevOps Automation Platform
Concurrent Multi-Threaded Stress Test for Audit Ledger Locking (A1-AUD-001)

Spawns concurrent worker threads appending events simultaneously to assert
that file locking serializes writes with zero corruption and 100% hash chain validity.
"""

import os
import shutil
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from platform_core.audit.audit_logger import append_audit_record
from platform_core.audit.audit_verifier import verify_audit_ledger


class TestConcurrentAuditLocking(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_concurrent_thread_append_integrity(self):
        total_threads = 10
        records_per_thread = 5
        total_expected_records = total_threads * records_per_thread

        def worker(thread_idx):
            for i in range(records_per_thread):
                append_audit_record(
                    workspace_root=self.test_dir,
                    app_id="stress-test-app",
                    environment="develop",
                    target_platform="floci",
                    account_topology="multi_account",
                    action=f"THREAD_ACTION_{thread_idx}_{i}",
                    status="SUCCESS",
                    details={"thread_id": thread_idx, "iteration": i}
                )

        with ThreadPoolExecutor(max_workers=total_threads) as executor:
            futures = [executor.submit(worker, t) for t in range(total_threads)]
            for f in futures:
                f.result()

        audit_file = os.path.join(self.test_dir, "platform_core", "audit", "audit_log.jsonl")
        self.assertTrue(os.path.isfile(audit_file), "Audit log file must exist")

        # Verify complete cryptographic chain
        valid, msg, count = verify_audit_ledger(audit_file)
        self.assertTrue(valid, f"Cryptographic audit chain must remain intact under concurrency: {msg}")
        self.assertEqual(count, total_expected_records, f"Expected {total_expected_records} records, got {count}")


if __name__ == "__main__":
    unittest.main()
