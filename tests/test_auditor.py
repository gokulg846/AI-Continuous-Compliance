import unittest

from compliance.auditor import Auditor
from compliance.models import ComplianceStatus, GovernancePolicy


class FakeContainer:
    def __init__(self, name, labels, ports):
        self.id = f"{name}-id"
        self.name = name
        self.labels = labels
        self.attrs = {
            "NetworkSettings": {
                "Ports": ports,
            }
        }

    def reload(self):
        return None


class FakeContainers:
    def __init__(self, containers):
        self._containers = containers

    def list(self):
        return self._containers


class FakeClient:
    def __init__(self, containers):
        self.containers = FakeContainers(containers)
        self.closed = False

    def ping(self):
        return True

    def close(self):
        self.closed = True


class AuditorTest(unittest.TestCase):
    def setUp(self):
        self.policy = GovernancePolicy(
            policy_version="1.0",
            policy_name="test-policy",
            required_labels=("owner", "env"),
            forbidden_ports=(6379, 3306),
        )

    def test_compliant_container_has_no_violations(self):
        container = FakeContainer(
            name="demo-good",
            labels={"owner": "platform", "env": "prod"},
            ports={"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "18080"}]},
        )

        report = Auditor(
            self.policy,
            client_factory=lambda: FakeClient([container]),
        ).run_audit()

        self.assertEqual(report.summary["containers_audited"], 1)
        self.assertEqual(report.summary["compliant"], 1)
        self.assertEqual(report.results[0].status, ComplianceStatus.COMPLIANT)
        self.assertEqual(report.results[0].violations, [])

    def test_missing_labels_and_forbidden_host_port_are_violations(self):
        container = FakeContainer(
            name="demo-bad",
            labels={"owner": "data"},
            ports={"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "6379"}]},
        )

        report = Auditor(
            self.policy,
            client_factory=lambda: FakeClient([container]),
        ).run_audit()

        self.assertEqual(report.summary["non_compliant"], 1)
        violation_rules = [violation.rule for violation in report.results[0].violations]
        violation_messages = [
            violation.message for violation in report.results[0].violations
        ]

        self.assertIn("required_labels", violation_rules)
        self.assertIn("forbidden_ports", violation_rules)
        self.assertIn("Missing required label: env", violation_messages)
        self.assertIn("Forbidden port is exposed: 6379", violation_messages)

    def test_container_prefix_limits_audit_scope(self):
        included = FakeContainer(
            name="cc-demo-included",
            labels={"owner": "platform", "env": "prod"},
            ports={},
        )
        excluded = FakeContainer(
            name="other-container",
            labels={},
            ports={"6379/tcp": [{"HostIp": "0.0.0.0", "HostPort": "6379"}]},
        )

        report = Auditor(
            self.policy,
            client_factory=lambda: FakeClient([included, excluded]),
            container_name_prefix="cc-demo",
        ).run_audit()

        self.assertEqual(report.summary["containers_audited"], 1)
        self.assertEqual(report.results[0].container_name, "cc-demo-included")


if __name__ == "__main__":
    unittest.main()
