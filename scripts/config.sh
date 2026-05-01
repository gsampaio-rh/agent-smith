#!/usr/bin/env bash
# Agent Smith — configuration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"

if [[ -f "$PROJECT_ROOT/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$PROJECT_ROOT/.env"
  set +a
fi

export AGENT_NS="${AGENT_NS:-agent-namespace}"
export ATTACKER_NS="${ATTACKER_NS:-attacker}"
export BIND_PORT="${BIND_PORT:-4444}"
export NEO_UI_SVC="${NEO_UI_SVC:-neo-ui.${AGENT_NS}.svc:3458}"
export ATTACKER_BC_NAME="${ATTACKER_BC_NAME:-neo-attacker}"
