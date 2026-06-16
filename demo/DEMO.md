# Resume Demo Guide

Use this guide to record a 60–90 second demo and describe the project on your resume.

## What This Project Does (30-second pitch)

> I built a Continuous Compliance agent that connects to the Docker socket, audits every running container against a governance policy, and writes structured evidence to JSON. The policy enforces required labels like `owner` and `env`, and blocks sensitive ports like Redis and MySQL from being exposed. The architecture is modular — Policy Ingestor, Auditor, and Reporter — so new compliance rules can be added without rewriting the core engine.

## How It Works

```text
policy.json  -->  PolicyIngestor  -->  GovernancePolicy
                                           |
                                           v
                                    Auditor (Docker SDK)
                                           |
                         +-----------------+------------------+
                         |                                    |
                  inspect labels                         inspect ports
                         |                                    |
                         v                                    v
                 required_labels check              forbidden_ports check
                         |                                    |
                         +-----------------+------------------+
                                           |
                                           v
                                    AuditReport
                                           |
                                           v
                                   audit_log.json
```

### Step-by-step flow

1. **Policy Ingestor** reads `policy.json` and validates the schema before touching Docker.
2. **Auditor** connects to `/var/run/docker.sock` and lists running containers.
3. For each container it checks:
   - **Labels**: are `owner`, `env`, and `security_tier` present?
   - **Ports**: is any forbidden port (e.g. 6379) exposed as a container port or host-published port?
4. **Reporter** writes `audit_log.json` with timestamp, container ID, status, and violations.
5. Exit code `1` if any container is non-compliant — useful for CI gates.

## Run the Live Demo (5 minutes)

### Prerequisites

- Docker Desktop or Docker Engine running
- Python 3.10+

### One command

```bash
chmod +x demo/run_demo.sh
./demo/run_demo.sh
```

### What the demo spins up

| Container | Purpose | Expected result |
|-----------|---------|-----------------|
| `cc-demo-compliant-web` | Has all required labels, safe port | COMPLIANT |
| `cc-demo-rogue-api` | Missing governance labels | NON-COMPLIANT |
| `cc-demo-exposed-db` | Exposes forbidden port 6379 (Redis) | NON-COMPLIANT |

### Manual walkthrough (good for screen recording)

```bash
# Terminal 1 — start the scenario
docker compose -f demo/docker-compose.demo.yml up -d
docker ps --filter name=cc-demo

# Terminal 2 — show the policy
cat policy.json

# Terminal 2 — run the audit
python3 -m pip install -r requirements.txt
python3 -m compliance.main \
  --policy policy.json \
  --output demo/audit_log.json \
  --container-prefix cc-demo
# Exit code 1 is expected here because the demo intentionally creates violations.

# Terminal 2 — show the results
python3 demo/print_report.py demo/audit_log.json
cat demo/audit_log.json

# Cleanup
docker compose -f demo/docker-compose.demo.yml down
```

## Resume Bullet Points

Pick 2–3 of these:

- Built a **Continuous Compliance agent** in Python using the Docker SDK to audit running containers against a JSON governance policy and emit structured audit evidence.
- Designed a **modular architecture** (Policy Ingestor / Auditor / Reporter) to support extensible enterprise governance rules.
- Implemented compliance checks for **mandatory container labels** and **forbidden exposed ports**, with per-container violation reporting.
- Added **daemon mode** for periodic background audits with graceful shutdown and policy hot-reload each cycle.
- Created a **demo environment** with compliant and non-compliant containers for live security posture demonstrations.

## Suggested Resume Line

**AI Continuous Compliance** | Python, Docker SDK, JSON  
*Automated governance auditing for Docker workloads — validates required labels and forbidden ports, outputs structured compliance evidence, supports continuous background monitoring.*

## GitHub / Portfolio Tips

1. Add a 60-second screen recording (policy → docker ps → audit → PASS/FAIL output).
2. Link to the repo: https://github.com/gokulg846/AI-Continuous-Compliance
3. Include `demo/sample_audit_log.json` in your README or portfolio site as example output when reviewers cannot run Docker.
4. Mention exit codes: the agent returns non-zero when violations exist, making it CI-friendly.

## Interview Talking Points

- **Why labels?** Enterprise teams tag workloads with owner, environment, and security tier for accountability and blast-radius control.
- **Why forbidden ports?** Exposing database/cache ports (6379, 3306) to the host increases attack surface.
- **How would you scale this?** Run as a systemd service or sidecar, push reports to SIEM/webhooks, add image scanning and signature verification as new Auditor rules.
- **Error handling?** Policy fails fast; per-container errors do not stop the full audit; Docker connection failures are explicit.
