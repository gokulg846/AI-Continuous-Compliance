#!/usr/bin/env python3
"""Pretty-print audit_log.json for live demos and screen recordings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print a human-readable audit summary")
    parser.add_argument(
        "audit_log",
        nargs="?",
        default="demo/audit_log.json",
        help="Path to audit_log.json (default: demo/audit_log.json)",
    )
    return parser


def print_report(path: Path) -> int:
    if not path.exists():
        print(f"Audit log not found: {path}", file=sys.stderr)
        return 1

    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    policy = data.get("policy", {})
    summary = data.get("summary", {})

    print()
    print("=" * 60)
    print("  CONTINUOUS COMPLIANCE AUDIT REPORT")
    print("=" * 60)
    print(f"  Policy : {policy.get('name', 'unknown')} v{policy.get('version', '?')}")
    print(f"  Audit  : {data.get('audit_id', 'n/a')}")
    print(f"  Window : {data.get('started_at', '?')} -> {data.get('completed_at', '?')}")
    print("-" * 60)
    print(
        f"  Containers audited : {summary.get('containers_audited', 0)}"
    )
    print(f"  Compliant          : {summary.get('compliant', 0)}")
    print(f"  Non-compliant      : {summary.get('non_compliant', 0)}")
    print("=" * 60)

    for result in data.get("results", []):
        status = result.get("status", "UNKNOWN")
        marker = "PASS" if status == "COMPLIANT" else "FAIL"
        print()
        print(f"[{marker}] {result.get('container_name', 'unknown')}")
        print(f"       ID   : {result.get('container_id', 'unknown')[:12]}")
        print(f"       Time : {result.get('timestamp', 'unknown')}")

        violations = result.get("violations", [])
        if not violations:
            print("       No violations")
            continue

        print("       Violations:")
        for violation in violations:
            print(f"         - [{violation.get('rule')}] {violation.get('message')}")

    errors = data.get("errors", [])
    if errors:
        print()
        print("Errors:")
        for error in errors:
            print(f"  - {error.get('container_id', 'unknown')}: {error.get('error')}")

    print()
    return 0


def main() -> int:
    args = build_parser().parse_args()
    return print_report(Path(args.audit_log))


if __name__ == "__main__":
    raise SystemExit(main())
