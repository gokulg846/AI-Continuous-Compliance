from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from compliance.exceptions import PolicyError
from compliance.models import GovernancePolicy


class PolicyIngestor:
    """Loads and validates governance policy definitions from JSON."""

    REQUIRED_TOP_LEVEL_KEYS = frozenset(
        {"policy_version", "policy_name", "required_labels", "forbidden_ports"}
    )

    def __init__(self, policy_path: str | Path) -> None:
        self._policy_path = Path(policy_path)

    @property
    def policy_path(self) -> Path:
        return self._policy_path

    def load(self) -> GovernancePolicy:
        raw = self._read_policy_file()
        self._validate_schema(raw)
        return self._parse_policy(raw)

    def _read_policy_file(self) -> dict[str, Any]:
        if not self._policy_path.exists():
            raise PolicyError(f"Policy file not found: {self._policy_path}")

        if not self._policy_path.is_file():
            raise PolicyError(f"Policy path is not a file: {self._policy_path}")

        try:
            with self._policy_path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise PolicyError(
                f"Invalid JSON in policy file {self._policy_path}: {exc}"
            ) from exc
        except OSError as exc:
            raise PolicyError(
                f"Unable to read policy file {self._policy_path}: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise PolicyError("Policy root must be a JSON object")

        return data

    def _validate_schema(self, data: dict[str, Any]) -> None:
        missing = self.REQUIRED_TOP_LEVEL_KEYS - data.keys()
        if missing:
            raise PolicyError(
                f"Policy missing required keys: {sorted(missing)}"
            )

        if not isinstance(data["policy_version"], str) or not data["policy_version"]:
            raise PolicyError("policy_version must be a non-empty string")

        if not isinstance(data["policy_name"], str) or not data["policy_name"]:
            raise PolicyError("policy_name must be a non-empty string")

        if not isinstance(data["required_labels"], list):
            raise PolicyError("required_labels must be a list")

        for index, label in enumerate(data["required_labels"]):
            if not isinstance(label, str) or not label.strip():
                raise PolicyError(
                    f"required_labels[{index}] must be a non-empty string"
                )

        if not isinstance(data["forbidden_ports"], list):
            raise PolicyError("forbidden_ports must be a list")

        for index, port in enumerate(data["forbidden_ports"]):
            if (
                isinstance(port, bool)
                or not isinstance(port, int)
                or port < 1
                or port > 65535
            ):
                raise PolicyError(
                    f"forbidden_ports[{index}] must be an integer "
                    "between 1 and 65535"
                )

    def _parse_policy(self, data: dict[str, Any]) -> GovernancePolicy:
        return GovernancePolicy(
            policy_version=data["policy_version"],
            policy_name=data["policy_name"],
            required_labels=tuple(data["required_labels"]),
            forbidden_ports=tuple(data["forbidden_ports"]),
        )
