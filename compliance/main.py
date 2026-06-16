#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys

from compliance.exceptions import ComplianceError
from compliance.service import ComplianceService, ServiceConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Continuous Compliance agent for Docker containers",
    )
    parser.add_argument(
        "--policy",
        default="policy.json",
        help="Path to governance policy JSON file (default: policy.json)",
    )
    parser.add_argument(
        "--output",
        default="audit_log.json",
        help="Path to audit evidence output file (default: audit_log.json)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a background service with periodic audits",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Audit interval in seconds when running as daemon (default: 300)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append each audit run to output file as a history array",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    return parser


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    if args.interval < 1:
        logging.error("--interval must be at least 1 second")
        return 2

    config = ServiceConfig(
        policy_path=args.policy,
        output_path=args.output,
        interval_seconds=args.interval,
        append_history=args.append,
    )
    service = ComplianceService(config)

    try:
        if args.daemon:
            service.run_forever()
            return 0

        report = service.run_once()
        if report.summary["non_compliant"] > 0 or report.errors:
            return 1
        return 0
    except ComplianceError as exc:
        logging.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logging.info("Interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
