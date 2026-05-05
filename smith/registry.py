"""Attack registry — metadata for all attack scripts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Phase(Enum):
    """Kill-chain phase with display label and Rich color."""

    KILL_CHAIN = ("Kill Chain", "bright_white")
    RECON = ("Recon", "dodger_blue1")
    CREDENTIAL_THEFT = ("Credential Theft", "yellow")
    LATERAL = ("Lateral Movement", "dark_orange")
    PERSISTENCE = ("Persistence", "red")
    EXFIL = ("Exfiltration", "purple")
    SABOTAGE = ("Sabotage", "magenta")
    AI_SPECIFIC = ("AI-Specific", "cyan")

    def __init__(self, label: str, color: str) -> None:
        self.label = label
        self.color = color


@dataclass(frozen=True)
class Attack:
    """Single attack script metadata."""

    id: str
    name: str
    script: str
    phase: Phase
    description: str
    requires_bind_shell: bool
    env_vars: list[str] = field(default_factory=list)


ATTACKS: list[Attack] = [
    # ── Kill Chain ────────────────────────────────────────────
    Attack(
        id="full-attack",
        name="Full Attack Sequence",
        script="full-attack.sh",
        phase=Phase.KILL_CHAIN,
        description="Run the complete kill chain: trigger → wait-shell → connect → exploit.",
        requires_bind_shell=False,
        env_vars=["AGENT_NS", "NEO_UI_SVC", "BIND_PORT"],
    ),
    Attack(
        id="trigger",
        name="Trigger Prompt Injection",
        script="trigger.sh",
        phase=Phase.KILL_CHAIN,
        description="Send trigger prompt so the agent reads poisoned logs in target-apps.",
        requires_bind_shell=False,
        env_vars=["NEO_UI_SVC", "AGENT_NS"],
    ),
    Attack(
        id="wait-shell",
        name="Wait for Bind Shell",
        script="wait-shell.sh",
        phase=Phase.KILL_CHAIN,
        description="Poll until bind shell on agent pod is listening on BIND_PORT.",
        requires_bind_shell=False,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="connect",
        name="Connect & Inject Payloads",
        script="connect.sh",
        phase=Phase.KILL_CHAIN,
        description="Connect to bind shell and inject takeover payloads (CLAUDE.md + skill).",
        requires_bind_shell=False,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="exploit",
        name="Send Exploitation Prompt",
        script="exploit.sh",
        phase=Phase.KILL_CHAIN,
        description="Send exploitation prompt via neo-ui after takeover payloads are injected.",
        requires_bind_shell=False,
        env_vars=["NEO_UI_SVC", "AGENT_NS"],
    ),
    Attack(
        id="hold-shell",
        name="Hold Shell Connection",
        script="hold-shell.sh",
        phase=Phase.KILL_CHAIN,
        description="Hold an open ncat connection so net-monitor shows compromised phase on the map.",
        requires_bind_shell=False,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    # ── Recon & Credential Theft ─────────────────────────────
    Attack(
        id="recon",
        name="Reconnaissance",
        script="attack-recon.sh",
        phase=Phase.RECON,
        description="Enumerate SA permissions, DNS service discovery, cloud metadata, env vars.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="steal-secrets",
        name="Steal Secrets & ConfigMaps",
        script="attack-steal-secrets.sh",
        phase=Phase.CREDENTIAL_THEFT,
        description="Read Secrets and ConfigMaps from target namespace, decode base64 values.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="steal-tokens",
        name="SA Token Pivoting",
        script="attack-steal-tokens.sh",
        phase=Phase.CREDENTIAL_THEFT,
        description="Extract ServiceAccount tokens from other namespaces and test permissions.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    # ── Lateral Movement ─────────────────────────────────────
    Attack(
        id="lateral-db",
        name="Database Lateral Movement",
        script="attack-lateral-db.sh",
        phase=Phase.LATERAL,
        description="Discover database services via DNS and attempt TCP connections.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="agent-worm",
        name="Agent-to-Agent Worm",
        script="attack-agent-worm.sh",
        phase=Phase.LATERAL,
        description="Discover other Neo agent pods and inject prompt payloads to propagate.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    # ── Persistence ──────────────────────────────────────────
    Attack(
        id="persist-claude",
        name="Stealth CLAUDE.md Poisoning",
        script="attack-persist-claude.sh",
        phase=Phase.PERSISTENCE,
        description="Inject subtle CLAUDE.md modifications for covert insider-threat behavior.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="persist-cronjob",
        name="CronJob Bind Shell Reopener",
        script="attack-persist-cronjob.sh",
        phase=Phase.PERSISTENCE,
        description="Create a CronJob that re-opens bind shell every 5 minutes, survives pod restarts.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    # ── Exfiltration ─────────────────────────────────────────
    Attack(
        id="exfil-dns",
        name="DNS Tunneling Exfiltration",
        script="attack-exfil-dns.sh",
        phase=Phase.EXFIL,
        description="Exfiltrate data by encoding it as DNS subdomain queries, bypasses NetworkPolicy.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT", "EXFIL_DOMAIN"],
    ),
    # ── Sabotage ─────────────────────────────────────────────
    Attack(
        id="miner",
        name="Crypto-Miner Simulation",
        script="attack-miner.sh",
        phase=Phase.SABOTAGE,
        description="CPU exhaustion via Python processes, visible spike on Grafana.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="scale-zero",
        name="Scale Deployments to Zero",
        script="attack-scale-zero.sh",
        phase=Phase.SABOTAGE,
        description="Scale target deployments to 0 replicas via k8s API PATCH.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="log-flood",
        name="Log Flooding",
        script="attack-log-flood.sh",
        phase=Phase.SABOTAGE,
        description="Generate massive log output to fill storage and hinder incident response.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    # ── AI-Specific ──────────────────────────────────────────
    Attack(
        id="hijack-model",
        name="Redirect LLM Endpoint",
        script="attack-hijack-model.sh",
        phase=Phase.AI_SPECIFIC,
        description="Override ANTHROPIC_BASE_URL in .bashrc to redirect to a hostile LLM server.",
        requires_bind_shell=True,
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
]

ATTACKS_BY_ID: dict[str, Attack] = {a.id: a for a in ATTACKS}


def get_attack(attack_id: str) -> Attack:
    """Look up an attack by ID, raise ValueError if not found."""
    if attack_id not in ATTACKS_BY_ID:
        available = ", ".join(sorted(ATTACKS_BY_ID))
        raise ValueError(f"Unknown attack '{attack_id}'. Available: {available}")
    return ATTACKS_BY_ID[attack_id]


def attacks_by_phase() -> dict[Phase, list[Attack]]:
    """Return attacks grouped by phase, preserving registration order."""
    grouped: dict[Phase, list[Attack]] = {}
    for attack in ATTACKS:
        grouped.setdefault(attack.phase, []).append(attack)
    return grouped
