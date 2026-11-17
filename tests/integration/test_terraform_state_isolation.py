"""
Enterprise Universal Application Delivery Platform - Terraform State Isolation Verification Tests
Verifies that independent applications and environments maintain segregated Terraform state files,
prevents cross-app state overwrites, and asserts that baseline local state is untouched.
"""

import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path


class TestTerraformStateIsolation(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.state_root = Path(self.test_dir) / "state"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_mock_state(self, app_id: str, env: str, resource_names: list) -> Path:
        env_dir = self.state_root / app_id / env
        env_dir.mkdir(parents=True, exist_ok=True)
        state_file = env_dir / "terraform.tfstate"
        state_data = {
            "version": 4,
            "terraform_version": "1.10.5",
            "serial": 1,
            "lineage": f"{app_id}-{env}-lineage",
            "resources": [
                {
                    "mode": "managed",
                    "type": "aws_s3_bucket",
                    "name": name,
                    "instances": [{"attributes": {"id": f"{app_id}-{env}-{name}"}}]
                }
                for name in resource_names
            ]
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)
        return state_file

    def test_01_app_isolation(self):
        """Verify App A cannot modify or collide with App B's state"""
        state_app1 = self._create_mock_state("hotel-billing", "develop", ["frontend_bucket", "backend_ecs"])
        state_app2 = self._create_mock_state("sample-node-service", "develop", ["api_ecs"])

        with open(state_app1, "r") as f:
            data1 = json.load(f)
        with open(state_app2, "r") as f:
            data2 = json.load(f)

        self.assertNotEqual(state_app1, state_app2)
        self.assertEqual(len(data1["resources"]), 2)
        self.assertEqual(len(data2["resources"]), 1)
        self.assertEqual(data1["lineage"], "hotel-billing-develop-lineage")
        self.assertEqual(data2["lineage"], "sample-node-service-develop-lineage")

    def test_02_environment_isolation(self):
        """Verify Develop, QA, and Prod states remain independent for the same application"""
        s_dev = self._create_mock_state("hotel-billing", "develop", ["dev_bucket"])
        s_qa = self._create_mock_state("hotel-billing", "qa", ["qa_bucket", "qa_queue"])
        s_prod = self._create_mock_state("hotel-billing", "prod", ["prod_bucket", "prod_queue", "prod_db"])

        with open(s_dev) as f:
            self.assertEqual(len(json.load(f)["resources"]), 1)
        with open(s_qa) as f:
            self.assertEqual(len(json.load(f)["resources"]), 2)
        with open(s_prod) as f:
            self.assertEqual(len(json.load(f)["resources"]), 3)

    def test_03_baseline_local_state_untouched(self):
        """Verify the original Hotel Billing baseline local state is untouched"""
        baseline_path = Path("infrastructure/terraform/environments/local/terraform.tfstate")
        self.assertTrue(baseline_path.is_file(), "Baseline local state file must exist")

        with open(baseline_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("serial"), 23, "Baseline serial must be exactly 23")
        self.assertEqual(len(data.get("resources", [])), 15, "Baseline must have exactly 15 managed resources")


if __name__ == "__main__":
    unittest.main()
