from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON-COMPLIANT"


@dataclass(frozen=True)
class GovernancePolicy:
    """Validated governance policy loaded from policy.json."""

    policy_version: str
    policy_name: str
    required_labels: tuple[str, ...]
    forbidden_ports: tuple[int, ...]


@dataclass(frozen=True)
class Violation:
    """A single compliance violation for a container."""

    rule: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContainerAuditResult:
    """Audit outcome for one running container."""

    timestamp: str
    container_id: str
    container_name: str
    status: ComplianceStatus
    violations: list[Violation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "container_id": self.container_id,
            "container_name": self.container_name,
            "status": self.status.value,
            "violations": [
                {
                    "rule": v.rule,
                    "message": v.message,
                    "details": v.details,
                }
                for v in self.violations
            ],
        }


@dataclass
class AuditReport:
    """Full audit run across all inspected containers."""

    audit_id: str
    started_at: str
    completed_at: str
    policy_name: str
    policy_version: str
    summary: dict[str, int]
    results: list[ContainerAuditResult] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "policy": {
                "name": self.policy_name,
                "version": self.policy_version,
            },
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results],
            "errors": self.errors,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
