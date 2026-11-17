"""
NERO Universal Enterprise DevOps Automation Platform - Three-Party Governance Rule Tests (A1-AUD-002)
Verifies strict separation of duties: requester != qa_approver, requester != ops_approver, qa_approver != ops_approver,
case-insensitive identity matching, empty submitter rejection, and valid ITIL change ticket format.
"""

import os
import shutil
import tempfile
import unittest

from platform_core.engine.orchestrator import record_governance_event
from platform_core.engine.errors import ConfigurationError, GovernancePolicyError, EXIT_CODE_GOVERNANCE_ERROR
from platform_core.audit.audit_verifier import verify_audit_ledger


class TestGovernanceRules(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_valid_three_person_approval(self):
        # Requester: alice, QA: bob, Ops: charlie
        record_governance_event(
            workspace_root=self.test_dir,
            app_id="hotel-billing",
            environment="prod",
            requester="alice.developer",
            qa_approver="bob.qa",
            ops_approver="charlie.sre",
            change_ticket_id="CHG-20261106-9999",
            release_id="rel-20261106-v3qual01"
        )
        audit_file = os.path.join(self.test_dir, "platform_core", "audit", "audit_log.jsonl")
        valid, msg, count = verify_audit_ledger(audit_file)
        self.assertTrue(valid, msg)
        self.assertEqual(count, 1)

    def test_02_reject_requester_equals_qa(self):
        with self.assertRaises(ConfigurationError) as ctx:
            record_governance_event(
                workspace_root=self.test_dir,
                app_id="hotel-billing",
                environment="prod",
                requester="alice.developer",
                qa_approver="alice.developer",
                ops_approver="charlie.sre",
                change_ticket_id="CHG-20261106-9999"
            )
        self.assertIn("cannot approve their own release", str(ctx.exception))

    def test_03_reject_requester_equals_ops(self):
        with self.assertRaises(ConfigurationError) as ctx:
            record_governance_event(
                workspace_root=self.test_dir,
                app_id="hotel-billing",
                environment="prod",
                requester="alice.developer",
                qa_approver="bob.qa",
                ops_approver="alice.developer",
                change_ticket_id="CHG-20261106-9999"
            )
        self.assertIn("cannot approve their own release", str(ctx.exception))

    def test_04_reject_qa_equals_ops(self):
        with self.assertRaises(ConfigurationError) as ctx:
            record_governance_event(
                workspace_root=self.test_dir,
                app_id="hotel-billing",
                environment="prod",
                requester="alice.developer",
                qa_approver="bob.qa",
                ops_approver="bob.qa",
                change_ticket_id="CHG-20261106-9999"
            )
        self.assertIn("cannot be identical", str(ctx.exception))

    def test_05_reject_invalid_ticket_format(self):
        with self.assertRaises(ConfigurationError) as ctx:
            record_governance_event(
                workspace_root=self.test_dir,
                app_id="hotel-billing",
                environment="prod",
                requester="alice.developer",
                qa_approver="bob.qa",
                ops_approver="charlie.sre",
                change_ticket_id="INVALID-TICKET-123"
            )
        self.assertIn("Invalid change ticket format", str(ctx.exception))

    def test_06_reject_case_insensitive_duplicate_approvers(self):
        with self.assertRaises(ConfigurationError) as ctx:
            record_governance_event(
                workspace_root=self.test_dir,
                app_id="hotel-billing",
                environment="prod",
                requester="ALICE.DEV",
                qa_approver="BOB.QA",
                ops_approver="bob.qa",
                change_ticket_id="CHG-20261108-001"
            )
        self.assertIn("cannot be identical", str(ctx.exception))

    def test_07_reject_empty_or_none_ticket(self):
        for bad_ticket in ["", None, "   "]:
            with self.assertRaises(ConfigurationError) as ctx:
                record_governance_event(
                    workspace_root=self.test_dir,
                    app_id="hotel-billing",
                    environment="prod",
                    requester="alice.dev",
                    qa_approver="bob.qa",
                    ops_approver="charlie.sre",
                    change_ticket_id=bad_ticket
                )
            self.assertIn("Invalid change ticket format", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
