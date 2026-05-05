#!/usr/bin/env bash
# Integration tests: spin up attacker + mock agent, run every attack end-to-end.
# Requires: Docker (or Podman with docker-compose compatibility)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/compose.yaml"

# Auto-detect container runtime
if command -v docker &>/dev/null; then
  COMPOSE="docker compose"
elif command -v podman &>/dev/null; then
  COMPOSE="podman compose"
  # Avoid credential-store errors when podman delegates to docker-compose
  export DOCKER_CONFIG="${DOCKER_CONFIG:-/dev/null}"
else
  echo "ERROR: Neither docker nor podman found." >&2
  exit 1
fi

PASS=0
FAIL=0
SKIP=0

run_attack() {
  local id="$1"
  local expect_exit="${2:-0}"
  local timeout="${3:-60}"

  local exit_code=0
  $COMPOSE -f "$COMPOSE_FILE" exec -T attacker \
    timeout "$timeout" smith run "$id" >/dev/null 2>&1 || exit_code=$?

  # timeout(1) returns 124 on timeout — treat as failure unless expected
  if [[ "$exit_code" -eq 124 && "$expect_exit" == "timeout-ok" ]]; then
    echo "  PASS: $id (timed out as expected)"
    PASS=$((PASS + 1))
    return
  fi

  if [[ "$expect_exit" == "nonzero" && "$exit_code" -ne 0 ]]; then
    echo "  PASS: $id (exit $exit_code, expected non-zero)"
    PASS=$((PASS + 1))
  elif [[ "$expect_exit" != "nonzero" && "$expect_exit" != "timeout-ok" && "$exit_code" -eq "$expect_exit" ]]; then
    echo "  PASS: $id"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $id (exit $exit_code, expected $expect_exit)"
    # Show last 20 lines of output for debugging
    $COMPOSE -f "$COMPOSE_FILE" exec -T attacker \
      timeout "$timeout" smith run "$id" 2>&1 | tail -20 || true
    FAIL=$((FAIL + 1))
  fi
}

cleanup() {
  echo ""
  echo "--- Cleanup ---"
  $COMPOSE -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Smith Integration Tests ==="
echo ""

echo "--- Building images ---"
$COMPOSE -f "$COMPOSE_FILE" build --quiet
echo ""

echo "--- Starting stack ---"
$COMPOSE -f "$COMPOSE_FILE" up -d --wait
echo ""

# Give the shared SA volume a moment to sync
sleep 2

echo "--- Verifying agent readiness ---"
$COMPOSE -f "$COMPOSE_FILE" exec -T attacker \
  bash -c 'ncat -z agent 4444 && curl -sf http://agent:3458/api/chat -X POST -H "Content-Type: application/json" -d "{\"prompt\":\"test\"}" -o /dev/null -w "%{http_code}"' \
  && echo "  Agent ready (bind shell + HTTP)" \
  || { echo "  FAIL: Agent not ready"; exit 1; }
echo ""

echo "--- Kill chain attacks ---"
run_attack "trigger"
run_attack "wait-shell"
run_attack "connect"
run_attack "exploit"
echo ""

echo "--- Post-breach: Recon & Credential Theft ---"
run_attack "recon"
run_attack "steal-secrets"
run_attack "steal-tokens"
echo ""

echo "--- Post-breach: Lateral Movement ---"
run_attack "lateral-db"
run_attack "agent-worm"
echo ""

echo "--- Post-breach: Persistence ---"
run_attack "persist-claude"
run_attack "persist-cronjob"
echo ""

echo "--- Post-breach: Exfiltration ---"
run_attack "exfil-dns"
echo ""

echo "--- Post-breach: Sabotage ---"
run_attack "miner" 0 30
run_attack "scale-zero"
run_attack "log-flood"
echo ""

echo "--- Post-breach: AI-Specific ---"
run_attack "hijack-model"
echo ""

echo "--- Special: hold-shell (timeout test) ---"
run_attack "hold-shell" "timeout-ok" 5
echo ""

echo "--- Special: full-attack (sequential) ---"
run_attack "full-attack" 0 120
echo ""

echo "=== Results ==="
echo "  $PASS passed, $FAIL failed, $SKIP skipped"
echo ""
[[ $FAIL -eq 0 ]] || exit 1
