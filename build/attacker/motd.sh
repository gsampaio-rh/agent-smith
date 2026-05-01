#!/usr/bin/env bash
# Login banner for the attacker web terminal.
cat <<'BANNER'

══════════════════════════════════════════════
   ATTACKER TERMINAL — Neo Red Team
══════════════════════════════════════════════

  Available commands:

    full-attack.sh    Run full attack sequence
    trigger.sh        Send poisoned log prompt
    wait-shell.sh     Wait for bind shell on :4444
    connect.sh        Connect + inject payloads
    exploit.sh        Send exploitation prompt
    hold-shell.sh     Hold connection open (shows attacker on map)

  All commands support --help for usage info.

══════════════════════════════════════════════
BANNER

echo "  Config:"
echo "    AGENT_NS     = ${AGENT_NS:-agent-namespace}"
echo "    NEO_UI_SVC   = ${NEO_UI_SVC:-neo-ui.agent-namespace.svc:3458}"
echo "    BIND_PORT    = ${BIND_PORT:-4444}"
echo ""
