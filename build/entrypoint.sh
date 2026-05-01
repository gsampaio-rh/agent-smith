#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " Neo | Attacker Terminal"
echo "============================================================"
echo "  AGENT_NS:    ${AGENT_NS:-agent-namespace}"
echo "  NEO_UI_SVC:  ${NEO_UI_SVC:-neo-ui.agent-namespace.svc:3458}"
echo "  BIND_PORT:   ${BIND_PORT:-4444}"
echo "============================================================"
echo ""

TTYD_ARGS=(-p 7681 --writable)

if [[ -n "${TTYD_CREDENTIAL:-}" ]]; then
  TTYD_ARGS+=(--credential "$TTYD_CREDENTIAL")
fi

exec ttyd "${TTYD_ARGS[@]}" bash --login
