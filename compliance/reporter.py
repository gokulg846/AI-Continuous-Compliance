from __future__ import annotations

import json
import logging
from pathlib import Path

from compliance.exceptions import ReportError
from compliance.models import AuditReport

logger = logging.getLogger(__name__)


class Reporter:
    """Persists structured audit evidence to disk."""

    def __init__(self, output_path: str | Path) -> None:
        self._output_path = Path(output_path)

    @property
    def output_path(self) -> Path:
        return self._output_path

    def write(self, report: AuditReport) -> Path:
        payload = report.to_dict()
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with self._output_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
                handle.write("\n")
        except OSError as exc:
            raise ReportError(
                f"Failed to write audit log to {self._output_path}: {exc}"
            ) from exc

        logger.info("Audit report written to %s", self._output_path)
        return self._output_path

    def append_run(self, report: AuditReport) -> Path:
        """Append a run to an existing audit log history file."""
        history = self._read_existing_history()
        history.append(report.to_dict())
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with self._output_path.open("w", encoding="utf-8") as handle:
                json.dump(history, handle, indent=2)
                handle.write("\n")
        except OSError as exc:
            raise ReportError(
                f"Failed to append audit log to {self._output_path}: {exc}"
            ) from exc

        logger.info("Audit run appended to %s", self._output_path)
        return self._output_path

    def _read_existing_history(self) -> list[dict]:
        if not self._output_path.exists():
            return []

        try:
            with self._output_path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            raise ReportError(
                f"Unable to read existing audit log {self._output_path}: {exc}"
            ) from exc

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return [data]

        raise ReportError(
            f"Existing audit log must be a JSON object or array: {self._output_path}"
        )
