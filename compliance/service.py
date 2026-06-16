from __future__ import annotations

import logging
import signal
import threading
from dataclasses import dataclass

from compliance.auditor import Auditor
from compliance.exceptions import ComplianceError
from compliance.models import AuditReport
from compliance.policy_ingestor import PolicyIngestor
from compliance.reporter import Reporter

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    policy_path: str
    output_path: str
    interval_seconds: int = 300
    append_history: bool = False


class ComplianceService:
    """Orchestrates policy ingestion, auditing, and reporting."""

    def __init__(self, config: ServiceConfig) -> None:
        self._config = config
        self._stop_event = threading.Event()

    def run_once(self) -> AuditReport:
        policy = PolicyIngestor(self._config.policy_path).load()
        report = Auditor(policy).run_audit()

        reporter = Reporter(self._config.output_path)
        if self._config.append_history:
            reporter.append_run(report)
        else:
            reporter.write(report)

        logger.info(
            "Audit complete: %d compliant, %d non-compliant",
            report.summary["compliant"],
            report.summary["non_compliant"],
        )
        return report

    def run_forever(self) -> None:
        self._register_signal_handlers()
        logger.info(
            "Starting continuous compliance service (interval=%ss)",
            self._config.interval_seconds,
        )

        while not self._stop_event.is_set():
            try:
                self.run_once()
            except ComplianceError:
                logger.exception("Audit cycle failed")
            except Exception:
                logger.exception("Unexpected error during audit cycle")

            if self._stop_event.wait(self._config.interval_seconds):
                break

        logger.info("Continuous compliance service stopped")

    def stop(self) -> None:
        self._stop_event.set()

    def _register_signal_handlers(self) -> None:
        def handle_signal(signum: int, _frame: object | None) -> None:
            logger.info("Received signal %s, shutting down", signum)
            self.stop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, handle_signal)
            except ValueError:
                # Signal handlers can only be registered on the main thread.
                logger.debug("Skipping signal handler registration for %s", sig)
