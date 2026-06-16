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
python3 -m compliance.main --policy policy.json --output audit_log.json

# Continuous background service (audit every 5 minutes)
python3 -m compliance.main --daemon --interval 300

# Append each run to a history log
python3 -m compliance.main --daemon --append --output audit_log.json
```

## Live Demo (for resume / portfolio)

Run a full end-to-end demo with one command:

```bash
chmod +x demo/run_demo.sh
./demo/run_demo.sh
```

This starts 3 containers (1 compliant, 2 intentional violations), runs the audit, and prints a PASS/FAIL summary. See [demo/DEMO.md](demo/DEMO.md) for a screen-recording script and resume bullet points.

```bash
# Audit only demo containers (useful when other containers are running)
python3 -m compliance.main \
  --policy policy.json \
  --output demo/audit_log.json \
  --container-prefix cc-demo

python3 demo/print_report.py demo/audit_log.json
```

Example output is committed at `demo/sample_audit_log.json` for portfolio viewers who cannot run Docker locally.

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
