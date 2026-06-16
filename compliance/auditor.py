from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol

import docker
from docker.errors import DockerException
from docker.models.containers import Container

from compliance.exceptions import AuditError, DockerConnectionError
from compliance.models import (
    AuditReport,
    ComplianceStatus,
    ContainerAuditResult,
    GovernancePolicy,
    Violation,
    utc_now_iso,
)

logger = logging.getLogger(__name__)


class DockerClientFactory(Protocol):
    def __call__(self) -> docker.DockerClient: ...


class Auditor:
    """Audits running containers against a governance policy."""

    def __init__(
        self,
        policy: GovernancePolicy,
        client_factory: DockerClientFactory | None = None,
        container_name_prefix: str | None = None,
    ) -> None:
        self._policy = policy
        self._client_factory = client_factory or docker.from_env
        self._container_name_prefix = container_name_prefix

    def run_audit(self) -> AuditReport:
        audit_id = str(uuid.uuid4())
        started_at = utc_now_iso()
        results: list[ContainerAuditResult] = []
        errors: list[dict[str, str]] = []

        try:
            client = self._client_factory()
        except DockerException as exc:
            raise DockerConnectionError(
                f"Failed to connect to Docker daemon: {exc}"
            ) from exc

        try:
            if not client.ping():
                raise DockerConnectionError("Docker daemon did not respond to ping")

            containers = client.containers.list()
            if self._container_name_prefix:
                containers = [
                    container
                    for container in containers
                    if self._container_name(container).startswith(
                        self._container_name_prefix
                    )
                ]
                logger.info(
                    "Auditing %d container(s) matching prefix '%s'",
                    len(containers),
                    self._container_name_prefix,
                )
            else:
                logger.info("Auditing %d running container(s)", len(containers))

            for container in containers:
                try:
                    results.append(self._audit_container(container))
                except Exception as exc:
                    container_id = getattr(container, "id", "unknown")
                    message = f"Failed to audit container {container_id}: {exc}"
                    logger.exception(message)
                    errors.append(
                        {
                            "container_id": container_id,
                            "error": str(exc),
                        }
                    )
        except DockerException as exc:
            raise AuditError(f"Docker API error during audit: {exc}") from exc
        finally:
            client.close()

        summary = self._build_summary(results)
        return AuditReport(
            audit_id=audit_id,
            started_at=started_at,
            completed_at=utc_now_iso(),
            policy_name=self._policy.policy_name,
            policy_version=self._policy.policy_version,
            summary=summary,
            results=results,
            errors=errors,
        )

    def _audit_container(self, container: Container) -> ContainerAuditResult:
        container.reload()
        labels = container.labels or {}
        exposed_ports = self._extract_exposed_ports(container)

        violations: list[Violation] = []
        violations.extend(self._check_required_labels(labels))
        violations.extend(self._check_forbidden_ports(exposed_ports))

        status = (
            ComplianceStatus.COMPLIANT
            if not violations
            else ComplianceStatus.NON_COMPLIANT
        )

        return ContainerAuditResult(
            timestamp=utc_now_iso(),
            container_id=container.id or "unknown",
            container_name=self._container_name(container),
            status=status,
            violations=violations,
        )

    def _check_required_labels(self, labels: dict[str, str]) -> list[Violation]:
        violations: list[Violation] = []
        for required_label in self._policy.required_labels:
            value = labels.get(required_label)
            if value is None or not str(value).strip():
                violations.append(
                    Violation(
                        rule="required_labels",
                        message=f"Missing required label: {required_label}",
                        details={
                            "label": required_label,
                            "present_labels": sorted(labels.keys()),
                        },
                    )
                )
        return violations

    def _check_forbidden_ports(self, exposed_ports: set[int]) -> list[Violation]:
        violations: list[Violation] = []
        forbidden_exposed = sorted(
            port for port in self._policy.forbidden_ports if port in exposed_ports
        )
        for port in forbidden_exposed:
            violations.append(
                Violation(
                    rule="forbidden_ports",
                    message=f"Forbidden port is exposed: {port}",
                    details={
                        "port": port,
                        "exposed_ports": sorted(exposed_ports),
                    },
                )
            )
        return violations

    def _extract_exposed_ports(self, container: Container) -> set[int]:
        exposed: set[int] = set()
        ports: dict[str, Any] | None = container.attrs.get("NetworkSettings", {}).get(
            "Ports"
        )

        if not ports:
            return exposed

        for container_port, bindings in ports.items():
            if bindings is None:
                continue

            port_number = self._parse_port_key(container_port)
            if port_number is not None:
                exposed.add(port_number)

        return exposed

    @staticmethod
    def _parse_port_key(port_key: str) -> int | None:
        # Docker port keys look like "8080/tcp" or "8080/udp".
        host_port = port_key.split("/", 1)[0]
        try:
            return int(host_port)
        except ValueError:
            return None

    @staticmethod
    def _container_name(container: Container) -> str:
        names = container.name or ""
        return names.lstrip("/")

    @staticmethod
    def _build_summary(results: list[ContainerAuditResult]) -> dict[str, int]:
        compliant = sum(
            1 for result in results if result.status == ComplianceStatus.COMPLIANT
        )
        non_compliant = len(results) - compliant
        return {
            "containers_audited": len(results),
            "compliant": compliant,
            "non_compliant": non_compliant,
        }
