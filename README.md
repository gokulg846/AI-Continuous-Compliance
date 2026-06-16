# AI Continuous Compliance

A modular Python agent that audits **running Docker containers** against a JSON **governance policy** and writes structured compliance evidence. Built as the foundation for an enterprise Architecture Control module — extensible, testable, and production-ready.

```
policy.json  →  Policy Ingestor  →  Auditor (Docker SDK)  →  Reporter  →  audit_log.json
```

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Live Demo](#live-demo)
- [Governance Policy](#governance-policy)
- [CLI Reference](#cli-reference)
- [Audit Output](#audit-output)
- [Project Structure](#project-structure)
- [Error Handling](#error-handling)
- [Scaling to Production](#scaling-to-production)
- [Extending the Agent](#extending-the-agent)

---

## Features

- **Policy-driven auditing** — define governance rules in a single `policy.json` file
- **Label enforcement** — require mandatory tags (`owner`, `env`, `security_tier`, etc.)
- **Port restrictions** — detect containers exposing sensitive ports (SSH, Docker API, databases)
- **Structured evidence** — every audit produces timestamped JSON with per-container violations
- **Modular architecture** — separate Policy Ingestor, Auditor, and Reporter components
- **One-shot or daemon mode** — run on demand, on a schedule, or as a background service
- **CI-friendly exit codes** — non-zero when violations are found
- **Runnable demo** — includes a Docker Compose scenario for portfolio presentations

---

## How It Works

The agent follows a three-stage pipeline orchestrated by `ComplianceService`:

```text
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ policy.json │────▶│  PolicyIngestor  │────▶│ GovernancePolicy│
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      │
                                                      ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Docker.sock │────▶│     Auditor      │────▶│   AuditReport   │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │    Reporter     │
                                             └────────┬────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │ audit_log.json  │
                                             └─────────────────┘
```

### Audit cycle

1. **Policy Ingestor** loads and validates `policy.json`. Invalid policy fails fast — before any Docker connection is attempted.
2. **Auditor** connects to the Docker daemon, lists running containers, and inspects each one:
   - **Labels** — verifies every key in `required_labels` is present and non-empty
   - **Ports** — checks whether any forbidden container port or host-published port is exposed
3. **Reporter** writes the full audit report to `audit_log.json`, including summary counts and per-container violations.
4. The process exits with code `1` if any container is non-compliant (useful for CI/CD gates).

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Docker | Engine or Desktop with socket access |
| OS | Linux, macOS, or Windows with WSL2 |

The agent needs read access to the Docker socket (`/var/run/docker.sock` by default, or `DOCKER_HOST`).

---

## Installation

```bash
git clone https://github.com/gokulg846/AI-Continuous-Compliance.git
cd AI-Continuous-Compliance

python3 -m pip install -r requirements.txt
```

---

## Quick Start

### Run a one-shot audit

```bash
python3 -m compliance.main \
  --policy policy.json \
  --output audit_log.json
```

### Run as a background service

Audit every 5 minutes with graceful shutdown on `SIGINT` / `SIGTERM`:

```bash
python3 -m compliance.main \
  --daemon \
  --interval 300 \
  --append \
  --output audit_log.json
```

### View results

```bash
python3 demo/print_report.py audit_log.json
```

---

## Live Demo

```bash
chmod +x demo/run_demo.sh
./demo/run_demo.sh
```

This script:

1. Installs dependencies
2. Starts 3 containers via Docker Compose (1 compliant, 2 intentional violations)
3. Runs the compliance audit
4. Prints a human-readable PASS/FAIL summary

### Demo containers

| Container | Scenario | Expected Result |
|-----------|----------|-----------------|
| `cc-demo-compliant-web` | All required labels, safe port mapping | `COMPLIANT` |
| `cc-demo-rogue-api` | Missing governance labels | `NON-COMPLIANT` |
| `cc-demo-exposed-db` | Exposes forbidden port 6379 (Redis) | `NON-COMPLIANT` |

### Manual demo steps

```bash
# Start the scenario
docker compose -f demo/docker-compose.demo.yml up -d

# Show the policy
cat policy.json

# Audit only demo containers (ignores other running containers)
python3 -m compliance.main \
  --policy policy.json \
  --output demo/audit_log.json \
  --container-prefix cc-demo

# Print results
python3 demo/print_report.py demo/audit_log.json

# Cleanup
docker compose -f demo/docker-compose.demo.yml down
```

A sample audit report is committed at [`demo/sample_audit_log.json`](demo/sample_audit_log.json) for viewers who cannot run Docker locally.

For resume bullet points and a screen-recording script, see [`demo/DEMO.md`](demo/DEMO.md).

---

## Governance Policy

Policies are defined in `policy.json` at the repository root (or any path passed via `--policy`).

### Schema

| Field | Type | Description |
|-------|------|-------------|
| `policy_version` | `string` | Semantic version of the policy document |
| `policy_name` | `string` | Human-readable policy identifier |
| `required_labels` | `string[]` | Docker label keys that must be present and non-empty |
| `forbidden_ports` | `int[]` | Container or host-published ports that must not be exposed |

### Example
# Continuous Compliance Agent

A modular Python service that audits running Docker containers against a JSON governance policy and writes structured compliance evidence.

## Architecture

```
policy.json
    │
    ▼
PolicyIngestor ──► GovernancePolicy
                        │
                        ▼
                    Auditor ──► AuditReport
                        │            │
                   Docker SDK         ▼
                                  Reporter ──► audit_log.json
```

| Module | Responsibility |
|--------|----------------|
| `compliance/policy_ingestor.py` | Load and validate `policy.json` |
| `compliance/auditor.py` | Connect to Docker, inspect containers, detect violations |
| `compliance/reporter.py` | Persist structured audit evidence |
| `compliance/service.py` | Orchestrate one-shot or continuous audit cycles |
| `compliance/main.py` | CLI entry point |

## Policy Schema

```json
{
  "policy_version": "1.0",
  "policy_name": "enterprise-governance-baseline",
  "required_labels": [
    "owner",
    "env",
    "security_tier"
  ],
  "forbidden_ports": [
    22,
    2375,
    2376,
    3306,
    5432,
    6379,
    27017
  ]
}
```

### Rule details

**`required_labels`** — Enterprise teams use labels for accountability and blast-radius control. A container missing `owner`, `env`, or `security_tier` is flagged as non-compliant.

**`forbidden_ports`** — Publishing database, cache, or administrative ports increases attack surface. The auditor inspects `NetworkSettings.Ports` and flags a forbidden port if it appears as either the container port (`6379/tcp`) or the host-published port (`HostPort: 6379`).

---

## CLI Reference

```
usage: python3 -m compliance.main [options]

options:
  --policy PATH            Path to governance policy JSON (default: policy.json)
  --output PATH            Path to audit evidence output (default: audit_log.json)
  --daemon                 Run as a background service with periodic audits
  --interval SECONDS       Audit interval in daemon mode (default: 300)
  --append                 Append each run to output as a JSON array history
  --container-prefix TEXT  Only audit containers whose names start with this prefix
  --log-level LEVEL        DEBUG | INFO | WARNING | ERROR (default: INFO)
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | All containers compliant, no errors |
| `1` | Violations found, fatal error, or audit failure |
| `2` | Invalid CLI arguments |
| `130` | Interrupted (`Ctrl+C`) |

---

## Audit Output

Each audit produces a JSON report with a summary and per-container results.

### Top-level structure

```json
{
  "audit_id": "uuid",
  "started_at": "2026-06-16T18:30:00+00:00",
  "completed_at": "2026-06-16T18:30:01+00:00",
  "policy": {
    "name": "enterprise-governance-baseline",
    "version": "1.0"
  },
  "summary": {
    "containers_audited": 3,
    "compliant": 1,
    "non_compliant": 2
  },
  "results": [ "... per-container entries ..." ],
  "errors": []
}
```

### Per-container entry

```json
{
  "timestamp": "2026-06-16T18:30:00+00:00",
  "container_id": "abc123def456",
  "container_name": "cc-demo-rogue-api",
  "required_labels": ["owner", "env", "security_tier"],
  "forbidden_ports": [22, 2375, 3306]
}
```

- **required_labels**: Docker label keys that must be present and non-empty on every running container.
- **forbidden_ports**: Container ports that must not be published/exposed.

## Quick Start

```bash
pip install -r requirements.txt

# One-shot audit (requires Docker socket access)
python -m compliance.main --policy policy.json --output audit_log.json

# Continuous background service (audit every 5 minutes)
python -m compliance.main --daemon --interval 300

# Append each run to a history log
python -m compliance.main --daemon --append --output audit_log.json
```

## Audit Output

Each container entry in `audit_log.json` includes:

```json
{
  "timestamp": "2026-06-16T12:00:00+00:00",
  "container_id": "abc123...",
  "container_name": "web-api",
  "status": "NON-COMPLIANT",
  "violations": [
    {
      "rule": "required_labels",
      "message": "Missing required label: owner",
      "details": {
        "label": "owner",
        "present_labels": []
      }
    }
  ]
}
```

Status values: `COMPLIANT` or `NON-COMPLIANT`.

---

## Project Structure

```text
AI-Continuous-Compliance/
├── compliance/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── service.py           # Orchestrator (one-shot + daemon loop)
│   ├── policy_ingestor.py   # Policy Ingestor — load & validate policy.json
│   ├── auditor.py           # Auditor — Docker SDK inspection & rule checks
│   ├── reporter.py          # Reporter — persist structured evidence
│   ├── models.py            # Dataclasses (GovernancePolicy, AuditReport, etc.)
│   └── exceptions.py        # Domain exceptions
├── demo/
│   ├── docker-compose.demo.yml   # Demo containers (compliant + violations)
│   ├── run_demo.sh               # One-command demo runner
│   ├── print_report.py           # Human-readable report printer
│   ├── sample_audit_log.json     # Example output for portfolio
│   └── DEMO.md                   # Resume / screen-recording guide
├── policy.json              # Default governance policy
├── requirements.txt
└── README.md
```

### Module responsibilities

| Module | File | Role |
|--------|------|------|
| Policy Ingestor | `policy_ingestor.py` | Load, validate, and parse `policy.json` |
| Auditor | `auditor.py` | Connect to Docker, inspect containers, detect violations |
| Reporter | `reporter.py` | Write or append structured audit evidence |
| Service | `service.py` | Wire modules together; support daemon mode |
| CLI | `main.py` | Argument parsing, logging, exit codes |

---

## Error Handling

The agent uses layered error handling so failures are explicit and auditable:

| Failure | Behavior |
|---------|----------|
| Missing or invalid `policy.json` | `PolicyError` — audit aborts before Docker connection |
| Docker daemon unreachable | `DockerConnectionError` — audit aborts with clear message |
| Single container inspect failure | Logged and recorded in `report.errors`; other containers still audited |
| Docker API error mid-audit | `AuditError` — audit aborts; client closed in `finally` block |
| Cannot write `audit_log.json` | `ReportError` — evidence is not silently dropped |

In daemon mode, a failed audit cycle is logged and the service continues on the next interval.

---

## Scaling to Production

### Daemon deployment (systemd)

```ini
[Unit]
Description=Continuous Compliance Agent
After=docker.service

[Service]
WorkingDirectory=/opt/ai-continuous-compliance
ExecStart=/usr/bin/python3 -m compliance.main --daemon --interval 300 --append --output /var/log/compliance/audit_log.json
Restart=on-failure
Environment=DOCKER_HOST=unix:///var/run/docker.sock

[Install]
WantedBy=multi-user.target
```

### Docker sidecar

Build the project into an image, mount the Docker socket read-only, and run the agent alongside your workloads:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY compliance/ compliance/
COPY policy.json policy.json
CMD ["python", "-m", "compliance.main", "--daemon", "--interval", "300"]
```

```yaml
services:
  compliance-agent:
    build: .
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./policy.json:/etc/compliance/policy.json:ro
      - ./audit_logs:/var/log/compliance
    command:
      - python
      - -m
      - compliance.main
      - --daemon
      - --interval
      - "300"
      - --append
      - --policy
      - /etc/compliance/policy.json
      - --output
      - /var/log/compliance/audit_log.json
```

### Enterprise integration paths

| Goal | Approach |
|------|----------|
| Policy hot-reload | Policy is re-read every cycle in `run_once()` — update `policy.json` without restart |
| New compliance rules | Add `_check_*` methods to `Auditor` and extend `PolicyIngestor` validation |
| SIEM / webhook push | Subclass `Reporter` or add a `Publisher` after `run_once()` |
| Multi-host auditing | Replace `docker.from_env()` with a host registry iterator |
| REST API | Wrap `ComplianceService.run_once()` in FastAPI or gRPC |

---

## Extending the Agent

To add a new rule (e.g. required image registry):

1. Add the field to `policy.json` and validate it in `PolicyIngestor`.
2. Add a field to the `GovernancePolicy` dataclass in `models.py`.
3. Implement a `_check_*` method in `Auditor` and call it from `_audit_container()`.
4. Violations automatically flow through to `audit_log.json` via the existing `Violation` model.

The `Auditor` accepts an injectable `client_factory` for unit testing without a live Docker socket.

---

## License

This project is open source. See the repository for license details.
      "details": { "label": "owner", "present_labels": ["env"] }
    }
  ]
}
```

Exit codes: `0` = all compliant, `1` = violations or errors, `130` = interrupted.

## Scaling to Production

1. **Daemon mode** — `--daemon` runs periodic audits with graceful `SIGINT`/`SIGTERM` shutdown.
2. **Policy hot-reload** — reload `policy.json` each cycle (already done in `run_once()`).
3. **Extend rules** — add new check methods to `Auditor` and corresponding policy keys in `PolicyIngestor`.
4. **Integrate downstream** — replace or wrap `Reporter.write()` to push to SIEM, webhooks, or a message bus.
5. **Deploy** — run as a systemd unit or sidecar container mounting `/var/run/docker.sock` read-only.

## Error Handling

- **Policy errors** — invalid or missing policy fails fast before Docker connection.
- **Docker connection errors** — surfaced as `DockerConnectionError` with clear messages.
- **Per-container failures** — logged and recorded in `report.errors`; other containers still audited.
- **Report write failures** — raised as `ReportError` without silently dropping evidence.
