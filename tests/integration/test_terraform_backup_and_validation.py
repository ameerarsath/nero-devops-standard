"""
NERO Universal Enterprise DevOps Automation Platform
Integration Tests for Terraform State Backup and Preflight Validation (A1-INF-001, A1-INF-002)
"""

import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from infrastructure.terraform.scripts.backup_states import create_state_backup, restore_state_backup
from platform_core.adapters.infrastructure.terraform_adapter import TerraformInfrastructureAdapter
from platform_core.adapters.base import AdapterRequest
from platform_core.engine.resolver import ResolvedEnvironmentContext
from platform_core.engine.errors import InfrastructureError


class TestTerraformBackupAndValidation(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.state_file = Path(self.test_dir) / "terraform.tfstate"
        self.baseline_state = {
            "version": 4,
            "terraform_version": "1.17.1",
            "serial": 23,
            "lineage": "test-lineage-123",
            "outputs": {"app_url": {"value": "http://localhost:8085"}},
            "resources": []
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.baseline_state, f, indent=2)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_create_state_backup_and_restore(self):
        # 1. Create snapshot
        backup_path = create_state_backup(self.test_dir)
        self.assertIsNotNone(backup_path)
        self.assertTrue(Path(backup_path).is_file())

        # 2. Corrupt original state
        with open(self.state_file, "w", encoding="utf-8") as f:
            f.write("CORRUPTED STATE DATA")

        # 3. Restore snapshot
        restored = restore_state_backup(self.test_dir, backup_path)
        self.assertEqual(restored, backup_path)

        # 4. Verify original content restored
        with open(self.state_file, "r", encoding="utf-8") as f:
            restored_data = json.load(f)
        self.assertEqual(restored_data["serial"], 23)
        self.assertEqual(restored_data["outputs"]["app_url"]["value"], "http://localhost:8085")

    def test_02_adapter_execute_backup_action(self):
        adapter = TerraformInfrastructureAdapter()
        req = AdapterRequest(
            action="backup",
            target="terraform",
            parameters={"env_dir": self.test_dir}
        )
        res = adapter.execute(req)
        self.assertTrue(res.success)
        self.assertIn("backup_path", res.data)
        self.assertTrue(Path(res.data["backup_path"]).is_file())


if __name__ == "__main__":
    unittest.main()
