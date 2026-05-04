#!/usr/bin/env bash
# Login banner for the attacker web terminal.
cat <<'BANNER'

══════════════════════════════════════════════════════════════
   ATTACKER TERMINAL — Neo Red Team
══════════════════════════════════════════════════════════════

  Kill Chain:
    full-attack.sh          Run full attack sequence
    trigger.sh              Send poisoned log prompt
    wait-shell.sh           Wait for bind shell on :4444
    connect.sh              Connect + inject payloads
    exploit.sh              Send exploitation prompt
    hold-shell.sh           Hold connection open (map)

  Post-Breach Attacks:
    attack-recon.sh         Recon: RBAC, DNS, cloud, env
    attack-steal-secrets.sh Steal k8s secrets + configmaps
    attack-steal-tokens.sh  Pivot via SA token theft
    attack-lateral-db.sh    Lateral movement to databases
    attack-agent-worm.sh    Worm: infect other agents
    attack-persist-claude.sh  Stealth CLAUDE.md poisoning
    attack-persist-cronjob.sh CronJob bind shell reopener
    attack-exfil-dns.sh     DNS tunneling exfiltration
    attack-miner.sh         Crypto-miner CPU exhaustion
    attack-scale-zero.sh    Scale deployment to zero
    attack-log-flood.sh     Log flooding sabotage
    attack-hijack-model.sh  Redirect LLM endpoint

  All commands support --help for usage info.

══════════════════════════════════════════════════════════════
BANNER

echo "  Config:"
echo "    AGENT_NS     = ${AGENT_NS:-agent-namespace}"
echo "    NEO_UI_SVC   = ${NEO_UI_SVC:-neo-ui.agent-namespace.svc:3458}"
echo "    BIND_PORT    = ${BIND_PORT:-4444}"
echo ""
