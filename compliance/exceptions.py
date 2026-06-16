"""Domain-specific exceptions for the compliance agent."""


class ComplianceError(Exception):
    """Base exception for compliance agent failures."""


class PolicyError(ComplianceError):
    """Raised when policy loading or validation fails."""


class DockerConnectionError(ComplianceError):
    """Raised when the agent cannot connect to the Docker daemon."""


class AuditError(ComplianceError):
    """Raised when an audit run fails in a non-recoverable way."""


class ReportError(ComplianceError):
    """Raised when audit results cannot be persisted."""
