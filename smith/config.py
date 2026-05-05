"""Environment detection and bind-shell status probing."""

from __future__ import annotations

import json
import os
import socket
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


CONTAINER_SCRIPTS_DIR = "/usr/local/lib/attacker"

DEFAULTS = {
    "AGENT_NS": "agent-namespace",
    "BIND_PORT": "4444",
    "NEO_UI_SVC": "",  # derived from AGENT_NS if empty
    "ATTACKER_NS": "attacker",
}

SA_TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"
SA_CA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"


@dataclass
class PodInfo:
    """Discovered Kubernetes pod with connectivity state."""

    name: str
    ip: str
    status: str
    namespace: str
    shell_open: bool = False


def _detect_scripts_dir() -> str:
    """Find the scripts directory — container path or local dev fallback.

    Priority: SMITH_SCRIPTS_DIR env > container path > local scripts/attacks/.
    """
    env_override = os.environ.get("SMITH_SCRIPTS_DIR")
    if env_override:
        return env_override

    if os.path.isdir(CONTAINER_SCRIPTS_DIR):
        return CONTAINER_SCRIPTS_DIR

    # Walk up from this file to find scripts/attacks/ (local dev)
    here = Path(__file__).resolve().parent
    for ancestor in [here, here.parent, here.parent.parent]:
        candidate = ancestor / "scripts" / "attacks"
        if (candidate / "lib.sh").is_file():
            return str(candidate)

    return CONTAINER_SCRIPTS_DIR


def is_local_dev() -> bool:
    """True when running outside the container (no SA token, no container scripts dir)."""
    return (
        not os.path.isfile(SA_TOKEN_PATH)
        and not os.path.isdir(CONTAINER_SCRIPTS_DIR)
    )


@dataclass
class SmithConfig:
    """Runtime configuration resolved from environment."""

    agent_ns: str
    bind_port: int
    neo_ui_svc: str
    attacker_ns: str
    scripts_dir: str
    local_dev: bool

    @classmethod
    def from_env(cls) -> SmithConfig:
        agent_ns = os.environ.get("AGENT_NS", DEFAULTS["AGENT_NS"])
        bind_port = int(os.environ.get("BIND_PORT", DEFAULTS["BIND_PORT"]))
        attacker_ns = os.environ.get("ATTACKER_NS", DEFAULTS["ATTACKER_NS"])
        neo_ui_svc = os.environ.get(
            "NEO_UI_SVC", f"neo-ui.{agent_ns}.svc:3458"
        )
        return cls(
            agent_ns=agent_ns,
            bind_port=bind_port,
            neo_ui_svc=neo_ui_svc,
            attacker_ns=attacker_ns,
            scripts_dir=_detect_scripts_dir(),
            local_dev=is_local_dev(),
        )


def _query_k8s_pods(config: SmithConfig) -> list[dict] | None:
    """Query k8s API for Neo agent pods. Returns raw items list or None."""
    if not os.path.isfile(SA_TOKEN_PATH):
        return None
    try:
        token = open(SA_TOKEN_PATH).read().strip()
        url = (
            f"https://kubernetes.default.svc/api/v1/namespaces/"
            f"{config.agent_ns}/pods?labelSelector=app.kubernetes.io/name=neo"
        )
        result = subprocess.run(
            [
                "curl", "-sk",
                "-H", f"Authorization: Bearer {token}",
                "--cacert", SA_CA_PATH,
                url,
            ],
            capture_output=True, text=True, timeout=5,
        )
        data = json.loads(result.stdout)
        return data.get("items", [])
    except Exception:
        return None


def resolve_agent_ip(config: SmithConfig) -> str | None:
    """Resolve the first Neo agent pod IP via k8s API. Returns None on failure."""
    items = _query_k8s_pods(config)
    if not items:
        return None
    try:
        ip = items[0]["status"]["podIP"]
        return ip if ip and ip != "null" else None
    except (KeyError, IndexError):
        return None


def discover_agent_pods(config: SmithConfig) -> list[PodInfo]:
    """Discover all Neo agent pods with IP, status, and bind-shell state."""
    items = _query_k8s_pods(config)
    if not items:
        return []

    pods: list[PodInfo] = []
    for item in items:
        ip = item.get("status", {}).get("podIP", "")
        if not ip or ip == "null":
            continue
        phase = item.get("status", {}).get("phase", "Unknown")
        name = item.get("metadata", {}).get("name", "unknown")
        ns = item.get("metadata", {}).get("namespace", config.agent_ns)
        shell_open = check_bind_shell(ip, config.bind_port)
        pods.append(PodInfo(
            name=name, ip=ip, status=phase,
            namespace=ns, shell_open=shell_open,
        ))
    return pods


def check_bind_shell(host: str, port: int, timeout: float = 2.0) -> bool:
    """TCP-probe the bind shell port. Returns True if connectable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False
