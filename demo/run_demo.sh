#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/demo/docker-compose.demo.yml"
AUDIT_LOG="$ROOT_DIR/demo/audit_log.json"
SAMPLE_AUDIT_LOG="$ROOT_DIR/demo/sample_audit_log.json"
POLICY="$ROOT_DIR/policy.json"
PREFIX="cc-demo"

cd "$ROOT_DIR"

step() {
  echo
  echo "============================================================"
  echo "  $1"
  echo "============================================================"
}

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd python3

run_sample_demo() {
  step "Docker is unavailable; showing sample audit evidence"
  cp "$SAMPLE_AUDIT_LOG" "$AUDIT_LOG"
  python3 "$ROOT_DIR/demo/print_report.py" "$AUDIT_LOG"

  cat <<EOF

Sample demo complete.

Docker is required for the live container audit, but this fallback still shows
the compliance evidence format and PASS/FAIL output for portfolio review.

To run the live demo:
  1. Install Docker Desktop or Docker Engine
  2. Start Docker
  3. Re-run: ./demo/run_demo.sh

EOF
}

if ! has_cmd docker; then
  run_sample_demo
  exit 0
fi

if ! docker info >/dev/null 2>&1; then
  run_sample_demo
  exit 0
fi

step "1/5  Install Python dependencies"
python3 -m pip install -q -r requirements.txt

step "2/5  Start demo containers (1 compliant, 2 violations)"
docker compose -f "$COMPOSE_FILE" up -d

step "3/5  Show running demo containers"
docker ps --filter "name=${PREFIX}-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

step "4/5  Run compliance audit against demo containers"
set +e
python3 -m compliance.main \
  --policy "$POLICY" \
  --output "$AUDIT_LOG" \
  --container-prefix "$PREFIX"
AUDIT_EXIT_CODE=$?
set -e

if [[ "$AUDIT_EXIT_CODE" -eq 0 ]]; then
  echo "Audit finished with no violations."
elif [[ "$AUDIT_EXIT_CODE" -eq 1 ]]; then
  echo "Audit found expected demo violations; continuing to print evidence."
else
  echo "Audit failed unexpectedly with exit code $AUDIT_EXIT_CODE" >&2
  exit "$AUDIT_EXIT_CODE"
fi

step "5/5  Human-readable audit summary"
python3 "$ROOT_DIR/demo/print_report.py" "$AUDIT_LOG"

cat <<EOF

Demo complete.

Artifacts for your portfolio:
  - Structured evidence : demo/audit_log.json
  - Sample output       : demo/sample_audit_log.json
  - Repo                : https://github.com/gokulg846/AI-Continuous-Compliance

Cleanup:
  docker compose -f demo/docker-compose.demo.yml down

Record a 60-second demo:
  1. Run this script
  2. Show policy.json rules
  3. Show docker ps output
  4. Show the printed FAIL/PASS summary
  5. Open demo/audit_log.json to show structured evidence
EOF
