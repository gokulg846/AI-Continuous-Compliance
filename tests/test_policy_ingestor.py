import json
import tempfile
import unittest
from pathlib import Path

from compliance.exceptions import PolicyError
from compliance.policy_ingestor import PolicyIngestor


class PolicyIngestorTest(unittest.TestCase):
    def write_policy(self, payload):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        policy_path = Path(temp_dir.name) / "policy.json"
        policy_path.write_text(json.dumps(payload), encoding="utf-8")
        return policy_path

    def test_loads_valid_policy(self):
        policy_path = self.write_policy(
            {
                "policy_version": "1.0",
                "policy_name": "test-policy",
                "required_labels": ["owner", "env"],
                "forbidden_ports": [6379, 3306],
            }
        )

        policy = PolicyIngestor(policy_path).load()

        self.assertEqual(policy.policy_name, "test-policy")
        self.assertEqual(policy.required_labels, ("owner", "env"))
        self.assertEqual(policy.forbidden_ports, (6379, 3306))

    def test_rejects_missing_required_keys(self):
        policy_path = self.write_policy(
            {
                "policy_version": "1.0",
                "policy_name": "test-policy",
                "required_labels": ["owner"],
            }
        )

        with self.assertRaisesRegex(PolicyError, "forbidden_ports"):
            PolicyIngestor(policy_path).load()

    def test_rejects_boolean_forbidden_ports(self):
        policy_path = self.write_policy(
            {
                "policy_version": "1.0",
                "policy_name": "test-policy",
                "required_labels": ["owner"],
                "forbidden_ports": [True],
            }
        )

        with self.assertRaisesRegex(PolicyError, "forbidden_ports"):
            PolicyIngestor(policy_path).load()


if __name__ == "__main__":
    unittest.main()
