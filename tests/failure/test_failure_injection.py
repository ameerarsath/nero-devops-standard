"""
Enterprise Universal Application Delivery Platform - Failure Injection & Recovery Tests
Proves fail-closed security and graceful error handling under simulated operational failures:
1. Truncated OCI digest injection
2. Frontend SHA-256 checksum tampering
3. Missing required secret keys
4. Stale/tampered release manifest
5. Stale Terraform plan apply rejection
6. Audit ledger tampering
"""

import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from platform_core.engine.orchestrator import validate_release_manifest
from platform_core.engine.errors import ConfigurationError
from platform_core.audit.audit_verifier import verify_audit_ledger, compute_record_hash


class TestFailureInjection(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manifest_path = Path(self.test_dir) / "release-manifest.json"

        # Valid baseline manifest
        self.valid_manifest = {
            "schema_version": "1.0.0",
            "release_id": "rel-20261106-test01",
            "application": "hotel-billing",
            "source": {
                "repository": "https://github.com/ameerarsath/billing-system.git",
                "commit_sha": "3bf604266b4f233c3899d0e315a0538812542b04"
            },
            "platform_version": "1.0.0",
            "spec_version": "1.0.0",
            "components": {
                "backend": {
                    "image": "backend:rel-20261106-test01",
                    "digest": "sha256:7ddc3df995835ac89bc1c04ca1c29d325b20dec33c6a8941a3d814adafb4ad09"
                },
                "frontend": {
                    "artifact": "frontend-dist-test01.tar.gz",
                    "sha256": "d5687ad6ed9f2a65f374245d74459c3e2d58766a4f46eaafee50a0b2f1c4dc06"
                }
            },
            "sbom": {"format": "CycloneDX", "reference": "sbom/test01.json"},
            "provenance": {"reference": "provenance/test01.json"},
            "build": {
                "timestamp": "2026-11-06T12:00:00Z",
                "builder_identity": "jenkins-runner@trusted-agent"
            }
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.valid_manifest, f, indent=2)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_valid_manifest_accepted(self):
        res = validate_release_manifest(
            manifest_path="release-manifest.json",
            expected_app_id="hotel-billing",
            workspace_root=self.test_dir
        )
        self.assertEqual(res["release_id"], "rel-20261106-test01")

    def test_02_inject_truncated_oci_digest(self):
        """Simulate short 12-char digest instead of full 64-char hex"""
        bad = json.loads(json.dumps(self.valid_manifest))
        bad["components"]["backend"]["digest"] = "sha256:7ddc3df99583"  # Truncated!
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(bad, f, indent=2)

        with self.assertRaises(ConfigurationError) as ctx:
            validate_release_manifest(
                manifest_path="release-manifest.json",
                expected_app_id="hotel-billing",
                workspace_root=self.test_dir
            )
        self.assertIn("Truncated or invalid OCI image digest", str(ctx.exception))

    def test_03_inject_tampered_frontend_checksum(self):
        """Simulate altered or short frontend checksum"""
        bad = json.loads(json.dumps(self.valid_manifest))
        bad["components"]["frontend"]["sha256"] = "invalid_short_hash"
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(bad, f, indent=2)

        with self.assertRaises(ConfigurationError) as ctx:
            validate_release_manifest(
                manifest_path="release-manifest.json",
                expected_app_id="hotel-billing",
                workspace_root=self.test_dir
            )
        self.assertIn("Invalid frontend artifact SHA-256", str(ctx.exception))

    def test_04_inject_missing_provenance(self):
        """Simulate release manifest lacking required provenance metadata"""
        bad = json.loads(json.dumps(self.valid_manifest))
        bad["provenance"]["reference"] = ""
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(bad, f, indent=2)

        with self.assertRaises(ConfigurationError) as ctx:
            validate_release_manifest(
                manifest_path="release-manifest.json",
                expected_app_id="hotel-billing",
                workspace_root=self.test_dir
            )
        self.assertIn("missing provenance reference", str(ctx.exception))

    def test_05_inject_corrupted_audit_record(self):
        """Simulate tampering with an audit record in the middle of the chain"""
        log_path = Path(self.test_dir) / "audit_log.jsonl"
        r1 = {"timestamp": "2026-11-06T12:00:00Z", "app_id": "test", "action": "A", "status": "PASS", "prev_hash": "0"*64}
        r1["record_hash"] = compute_record_hash(r1)
        r2 = {"timestamp": "2026-11-06T12:01:00Z", "app_id": "test", "action": "B", "status": "PASS", "prev_hash": r1["record_hash"]}
        r2["record_hash"] = compute_record_hash(r2)

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(r1) + "\n")
            f.write(json.dumps(r2) + "\n")

        valid, _, _ = verify_audit_ledger(str(log_path))
        self.assertTrue(valid)

        # Inject tampering in r1
        r1["status"] = "FAIL"  # Hash is now broken
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(r1) + "\n")
            f.write(json.dumps(r2) + "\n")

        tamper_valid, msg, _ = verify_audit_ledger(str(log_path))
        self.assertFalse(tamper_valid)
        self.assertIn("hash mismatch", msg.lower())

    def test_06_runtime_prohibited_version_rejected(self):
        """Simulate rejection of prohibited runtime version (Node 16 EOL)"""
        from platform_core.policy.runtime_policy import RuntimePolicyValidator, RuntimePolicyError
        df = Path(self.test_dir) / "Dockerfile"
        df.write_text("FROM node:16-alpine\n")
        (Path(self.test_dir) / "package-lock.json").write_text("{}")
        with self.assertRaises(RuntimePolicyError) as ctx:
            RuntimePolicyValidator.validate_component({"name": "api"}, Path(self.test_dir))
        self.assertIn("prohibited/EOL runtime nodejs:16", str(ctx.exception))

    def test_07_missing_lockfile_rejected(self):
        """Simulate rejection when mandatory dependency lockfile is absent"""
        from platform_core.policy.runtime_policy import RuntimePolicyValidator, RuntimePolicyError
        df = Path(self.test_dir) / "Dockerfile"
        df.write_text("FROM node:22-alpine\n")
        if (Path(self.test_dir) / "package-lock.json").is_file():
            (Path(self.test_dir) / "package-lock.json").unlink()
        with self.assertRaises(RuntimePolicyError) as ctx:
            RuntimePolicyValidator.validate_component({"name": "api"}, Path(self.test_dir))
        self.assertIn("missing dependency lockfile", str(ctx.exception))

    def test_08_emergency_deploy_duplicate_actor_rejected(self):
        """Simulate rejection of emergency break-glass deployment with self-approval"""
        from platform_core.engine.orchestrator import record_emergency_governance_event
        # Stash manifest
        m_dir = Path(self.test_dir) / "platform_core" / "manifests"
        m_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.manifest_path, m_dir / "rel-20261106-test01.json")

        with self.assertRaises(ConfigurationError) as ctx:
            record_emergency_governance_event(
                workspace_root=self.test_dir,
                app_id="hotel-billing",
                environment="prod",
                requester="lead.dev",
                incident_commander="lead.dev",  # Duplicate actor
                emergency_approver="vp.eng",
                secops_approver="secops.admin",
                incident_ticket_id="INC-12345",
                release_id="rel-20261106-test01"
            )
        self.assertIn("roles must be distinct identities", str(ctx.exception))

    def test_09_emergency_deploy_invalid_ticket_rejected(self):
        """Simulate rejection of emergency break-glass deployment with invalid ticket"""
        from platform_core.engine.orchestrator import record_emergency_governance_event
        with self.assertRaises(ConfigurationError) as ctx:
            record_emergency_governance_event(
                workspace_root=self.test_dir,
                app_id="hotel-billing",
                environment="prod",
                requester="lead.dev",
                incident_commander="ic.lead",
                emergency_approver="vp.eng",
                secops_approver="secops.admin",
                incident_ticket_id="TICKET-123",  # Must be INC-* or HOTFIX-*
                release_id="rel-20261106-test01"
            )
        self.assertIn("Invalid incident ticket format", str(ctx.exception))

    def test_10_rollback_to_missing_manifest_rejected(self):
        """Simulate rollback failing when previous manifest does not exist"""
        from platform_core.engine.orchestrator import execute_rollback
        with self.assertRaises(ConfigurationError) as ctx:
            execute_rollback(
                workspace_root=self.test_dir,
                app_id="hotel-billing",
                environment="prod",
                target_release_id="rel-non-existent-999",
                operator="sre.oncall",
                reason="Testing rollback",
                ticket_id="ROLLBACK-123"
            )
        self.assertIn("Previous release manifest 'rel-non-existent-999.json' not found", str(ctx.exception))

    def test_11_audit_checkpoint_invalid_key_rejected(self):
        """Simulate rejection of checkpoint verification when HMAC key is mismatched"""
        from platform_core.audit.audit_verifier import create_signed_checkpoint, verify_checkpoint
        log_path = Path(self.test_dir) / "audit_log.jsonl"
        r1 = {"timestamp": "2026-11-06T12:00:00Z", "app_id": "test", "action": "A", "status": "PASS", "prev_hash": "0"*64}
        r1["record_hash"] = compute_record_hash(r1)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(r1) + "\n")

        cp_dir = Path(self.test_dir) / "checkpoints"
        create_signed_checkpoint(str(log_path), str(cp_dir), signing_key=b"secret-key-1")

        valid, msg = verify_checkpoint(str(log_path), str(cp_dir / "checkpoint-latest.json"), signing_key=b"wrong-key-2")
        self.assertFalse(valid)
        self.assertIn("invalid", msg.lower())


if __name__ == "__main__":
    unittest.main()
