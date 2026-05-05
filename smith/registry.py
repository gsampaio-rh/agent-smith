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
    """Single attack script metadata with visualization enrichment."""

    id: str
    name: str
    script: str
    phase: Phase
    description: str
    requires_bind_shell: bool
    technique: str
    impact: str
    briefing: str
    loot_types: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
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
        technique="T1059.004",
        impact="Full compromise of the AI agent — remote code execution, data theft, persistence.",
        briefing=(
            "Executes the entire kill chain in sequence: sends a crafted prompt "
            "to the Neo agent that tricks it into reading poisoned logs, waits for "
            "the bind shell to open, injects takeover payloads (CLAUDE.md + skill), "
            "and sends the exploitation prompt."
        ),
        loot_types=["shell-access", "agent-control"],
        steps=[
            "Send trigger prompt via Neo UI /api/chat",
            "Poll agent pod until bind shell opens on BIND_PORT",
            "Inject malicious CLAUDE.md and k8s-ops skill via bind shell",
            "Send exploitation prompt to weaponize the hijacked agent",
        ],
        env_vars=["AGENT_NS", "NEO_UI_SVC", "BIND_PORT"],
    ),
    Attack(
        id="trigger",
        name="Trigger Prompt Injection",
        script="trigger.sh",
        phase=Phase.KILL_CHAIN,
        description="Send trigger prompt so the agent reads poisoned logs in target-apps.",
        requires_bind_shell=False,
        technique="T1190",
        impact="Agent begins executing attacker-controlled instructions from poisoned log data.",
        briefing=(
            "Sends a crafted prompt to the Neo UI /api/chat endpoint. The prompt "
            "instructs the agent to read pod logs in the target-apps namespace, "
            "where poisoned log entries contain a bind-shell payload."
        ),
        loot_types=[],
        steps=[
            "Resolve agent pod IP via K8s API",
            "Build trigger prompt with K8s API instructions",
            "POST prompt to Neo UI /api/chat",
            "Verify HTTP 202 acceptance",
        ],
        env_vars=["NEO_UI_SVC", "AGENT_NS"],
    ),
    Attack(
        id="wait-shell",
        name="Wait for Bind Shell",
        script="wait-shell.sh",
        phase=Phase.KILL_CHAIN,
        description="Poll until bind shell on agent pod is listening on BIND_PORT.",
        requires_bind_shell=False,
        technique="T1571",
        impact="Confirms the agent executed the payload — bind shell is live.",
        briefing=(
            "After the trigger prompt, the agent reads poisoned logs that contain "
            "a Python bind-shell payload. This step polls the agent pod's BIND_PORT "
            "with ncat until a TCP listener appears (up to 120s)."
        ),
        loot_types=["shell-access"],
        steps=[
            "Resolve agent pod IP",
            "Poll TCP port with ncat -z every 2 seconds",
            "Report when bind shell is detected or timeout",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="connect",
        name="Connect & Inject Payloads",
        script="connect.sh",
        phase=Phase.KILL_CHAIN,
        description="Connect to bind shell and inject takeover payloads (CLAUDE.md + skill).",
        requires_bind_shell=False,
        technique="T1059.006",
        impact="Agent's instruction set replaced — all future actions controlled by attacker.",
        briefing=(
            "Connects to the bind shell and writes a malicious CLAUDE.md and "
            "k8s-ops.md skill file into the agent's .claude directory. These "
            "files override the agent's behavior for all subsequent interactions."
        ),
        loot_types=["agent-control"],
        steps=[
            "Resolve agent pod IP",
            "Base64-encode CLAUDE.md override and k8s-ops skill payloads",
            "Pipe encoded payloads through ncat to bind shell",
            "Verify TAKEOVER_COMPLETE marker in output",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="exploit",
        name="Send Exploitation Prompt",
        script="exploit.sh",
        phase=Phase.KILL_CHAIN,
        description="Send exploitation prompt via neo-ui after takeover payloads are injected.",
        requires_bind_shell=False,
        technique="T1059.004",
        impact="Agent acts on injected CLAUDE.md — executes attacker objectives autonomously.",
        briefing=(
            "After the takeover payloads are in place, sends an exploitation "
            "prompt to the Neo UI that triggers the agent to act on the "
            "injected CLAUDE.md instructions. The agent now operates as an "
            "insider threat."
        ),
        loot_types=[],
        steps=[
            "Build exploitation prompt",
            "POST to Neo UI /api/chat",
            "Verify HTTP 202 acceptance",
        ],
        env_vars=["NEO_UI_SVC", "AGENT_NS"],
    ),
    Attack(
        id="hold-shell",
        name="Hold Shell Connection",
        script="hold-shell.sh",
        phase=Phase.KILL_CHAIN,
        description="Hold an open ncat connection so net-monitor shows compromised phase on the map.",
        requires_bind_shell=False,
        technique="T1571",
        impact="Sustained C2 channel visible on the network topology map.",
        briefing=(
            "Keeps an established ncat session to the bind shell alive so "
            "the network monitor detects a persistent 'established' connection "
            "and the Neo UI map transitions to the compromised visual state."
        ),
        loot_types=[],
        steps=[
            "Resolve agent pod IP",
            "Verify bind shell port is open",
            "Pipe sleep infinity into ncat to hold connection",
            "Trap SIGINT/SIGTERM for clean disconnect",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    # ── Recon ─────────────────────────────────────────────────
    Attack(
        id="recon",
        name="Reconnaissance",
        script="attack-recon.sh",
        phase=Phase.RECON,
        description="Enumerate SA permissions, DNS service discovery, cloud metadata, env vars.",
        requires_bind_shell=True,
        technique="T1613",
        impact="Full map of blast radius — RBAC permissions, internal services, cloud metadata, sensitive env vars.",
        briefing=(
            "Runs a comprehensive reconnaissance sweep from inside the "
            "compromised agent pod. Enumerates ServiceAccount RBAC permissions "
            "across namespaces, discovers internal services via DNS, probes "
            "cloud metadata endpoints, and dumps environment variables "
            "flagging sensitive keys."
        ),
        loot_types=["rbac-rules", "service-map", "env-vars", "cloud-metadata"],
        steps=[
            "SelfSubjectRulesReview for target-apps, default, kube-system, agent NS",
            "DNS lookups for postgres, redis, mongodb, elasticsearch, kafka, etc.",
            "HTTP probes to AWS/GCP/Azure metadata endpoints",
            "Dump and flag sensitive environment variables",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    # ── Credential Theft ──────────────────────────────────────
    Attack(
        id="steal-secrets",
        name="Steal Secrets & ConfigMaps",
        script="attack-steal-secrets.sh",
        phase=Phase.CREDENTIAL_THEFT,
        description="Read Secrets and ConfigMaps from target namespace, decode base64 values.",
        requires_bind_shell=True,
        technique="T1552.007",
        impact="Database credentials, API keys, and configuration data exfiltrated from Kubernetes Secrets.",
        briefing=(
            "Uses the compromised pod's ServiceAccount to read all Kubernetes "
            "Secrets and ConfigMaps in the target namespace. Base64-decodes "
            "secret data fields to reveal passwords, tokens, and connection strings."
        ),
        loot_types=["secrets", "configmaps", "credentials"],
        steps=[
            "GET /api/v1/namespaces/{ns}/secrets via K8s API",
            "Decode base64 data fields for each Secret",
            "GET /api/v1/namespaces/{ns}/configmaps",
            "Display ConfigMap key-value pairs",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="steal-tokens",
        name="SA Token Pivoting",
        script="attack-steal-tokens.sh",
        phase=Phase.CREDENTIAL_THEFT,
        description="Extract ServiceAccount tokens from other namespaces and test permissions.",
        requires_bind_shell=True,
        technique="T1528",
        impact="Privilege escalation via stolen ServiceAccount tokens — access to additional namespaces.",
        briefing=(
            "Enumerates kubernetes.io/service-account-token secrets across "
            "multiple namespaces. Decodes each token and uses it to perform "
            "a SelfSubjectRulesReview, revealing the effective RBAC permissions "
            "that each stolen identity grants."
        ),
        loot_types=["tokens", "rbac-rules"],
        steps=[
            "List secrets in kube-system, default, target-apps, monitoring",
            "Filter for type kubernetes.io/service-account-token",
            "Decode and extract bearer tokens",
            "Test each token's permissions via SelfSubjectRulesReview",
        ],
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
        technique="T1021",
        impact="Database access from compromised pod — potential data breach via lateral pivot.",
        briefing=(
            "Performs DNS service discovery for common database names (postgres, "
            "mysql, redis, mongodb) across namespaces, then attempts TCP connections "
            "and lightweight protocol handshakes to confirm accessibility."
        ),
        loot_types=["service-map", "db-access"],
        steps=[
            "DNS resolve postgres/mysql/redis/mongodb across namespaces",
            "TCP connect to discovered endpoints",
            "Redis PING, Postgres startup, MySQL handshake probes",
            "Report reachable databases",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="agent-worm",
        name="Agent-to-Agent Worm",
        script="attack-agent-worm.sh",
        phase=Phase.LATERAL,
        description="Discover other Neo agent pods and inject prompt payloads to propagate.",
        requires_bind_shell=True,
        technique="T1570",
        impact="Cascading compromise — worm propagates prompt injection across all Neo agent pods.",
        briefing=(
            "Lists all Neo agent pods in the namespace via the K8s API, then "
            "POSTs a worm prompt to each peer agent's Neo UI endpoint. The "
            "prompt tricks each agent into reading the same poisoned logs, "
            "causing them to open their own bind shells."
        ),
        loot_types=["pod-list", "worm-results"],
        steps=[
            "List Neo pods via K8s API (labelSelector=app.kubernetes.io/name=neo)",
            "Identify self by IP and skip",
            "POST worm prompt to each peer's neo-ui:3458/api/chat",
            "Report infection count",
        ],
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
        technique="T1546",
        impact="Agent silently leaks data and suppresses security alerts — persistent insider threat.",
        briefing=(
            "Unlike the blatant takeover in connect.sh, this attack appends "
            "subtle, legitimate-looking instructions to CLAUDE.md. The agent "
            "is nudged to include environment details in responses, report "
            "security as clean, and never redact sensitive values — all "
            "disguised as standard operating procedures."
        ),
        loot_types=["persistence-config"],
        steps=[
            "Read existing CLAUDE.md and backup original",
            "Craft stealth payload disguised as project instructions",
            "Append payload to CLAUDE.md",
            "Verify modified file size",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="persist-cronjob",
        name="CronJob Bind Shell Reopener",
        script="attack-persist-cronjob.sh",
        phase=Phase.PERSISTENCE,
        description="Create a CronJob that re-opens bind shell every 5 minutes, survives pod restarts.",
        requires_bind_shell=True,
        technique="T1053.007",
        impact="Bind shell re-opens automatically every 5 minutes — survives pod restarts and scaling.",
        briefing=(
            "Creates a Kubernetes CronJob disguised as 'app-health-check' that "
            "runs every 5 minutes. The job container executes a Python bind-shell "
            "one-liner, ensuring the attacker maintains access even if the "
            "original pod is restarted or scaled."
        ),
        loot_types=["persistence-config"],
        steps=[
            "Build CronJob manifest (app-health-check, */5 schedule)",
            "POST CronJob to batch/v1 API",
            "Handle 201 (created), 409 (exists), 403 (denied)",
        ],
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
        technique="T1048.003",
        impact="Data leaves the cluster via DNS — bypasses NetworkPolicy, firewalls, and egress controls.",
        briefing=(
            "Encodes stolen data as base32 chunks in DNS subdomain queries. "
            "Since DNS queries go through cluster DNS (kube-dns/CoreDNS), they "
            "bypass NetworkPolicy and most egress controls. The attacker's DNS "
            "server captures the queries to reconstruct the data."
        ),
        loot_types=["secrets", "env-vars", "exfil-proof"],
        steps=[
            "Read secrets from target-apps namespace",
            "Base32-encode data into 50-byte chunks",
            "Issue DNS queries: {chunk}.{seq}.{label}.{exfil-domain}",
            "Fallback to env vars if secrets inaccessible",
        ],
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
        technique="T1496",
        impact="CPU maxed out across all cores — service degradation visible on Grafana dashboards.",
        briefing=(
            "Spawns one CPU-intensive Python worker per core that performs "
            "repeated large exponentiation (2^1000000). Creates a dramatic "
            "and immediate CPU spike visible on Grafana, simulating a "
            "crypto-miner or resource-abuse attack."
        ),
        loot_types=[],
        steps=[
            "Detect CPU core count on agent pod",
            "Spawn one worker process per core",
            "Each worker runs tight exponentiation loop for N seconds",
            "Report completion and duration",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="scale-zero",
        name="Scale Deployments to Zero",
        script="attack-scale-zero.sh",
        phase=Phase.SABOTAGE,
        description="Scale target deployments to 0 replicas via k8s API PATCH.",
        requires_bind_shell=True,
        technique="T1489",
        impact="Target deployment serves zero traffic — service outage without deletion.",
        briefing=(
            "PATCHes a Deployment's replica count to zero via the K8s API. "
            "More subtle than deletion: the Deployment still exists in the "
            "cluster (no alerts from missing resources), but serves no traffic."
        ),
        loot_types=[],
        steps=[
            "GET deployment current state and replica count",
            "Build JSON Patch to set /spec/replicas to 0",
            "PATCH deployment via apps/v1 API",
            "Report old → new replica count",
        ],
        env_vars=["AGENT_NS", "BIND_PORT"],
    ),
    Attack(
        id="log-flood",
        name="Log Flooding",
        script="attack-log-flood.sh",
        phase=Phase.SABOTAGE,
        description="Generate massive log output to fill storage and hinder incident response.",
        requires_bind_shell=True,
        technique="T1565.001",
        impact="Log storage saturated — incident responders buried under noise.",
        briefing=(
            "Writes thousands of realistic-looking but fake log lines to stdout "
            "on the agent pod. Pollutes the log pipeline, fills storage quotas, "
            "and makes forensic analysis significantly harder."
        ),
        loot_types=[],
        steps=[
            "Generate randomized structured log lines (timestamp, level, component)",
            "Write N lines to stdout at max throughput",
            "Flush periodically to ensure delivery to log pipeline",
            "Report volume and rate",
        ],
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
        technique="T1557",
        impact="All LLM API calls go to attacker — prompt interception + response manipulation.",
        briefing=(
            "Modifies the agent's .bashrc to export ANTHROPIC_BASE_URL pointing "
            "to an attacker-controlled LLM endpoint. Future Claude Code invocations "
            "send all prompts (including secrets in context) to the hostile server, "
            "which can return manipulated responses."
        ),
        loot_types=["env-vars", "persistence-config"],
        steps=[
            "Read existing .bashrc content",
            "Remove any prior ANTHROPIC_BASE_URL lines",
            "Append export ANTHROPIC_BASE_URL={hostile-url}",
            "Set env var in current session",
        ],
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
