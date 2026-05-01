# Agent Smith

Adversary tooling for The Matrix workshop. Deploys:

- **target-apps**: inventory-app with poisoned logs + RBAC granting the Neo agent read access
- **attacker**: ttyd-based container with attack scripts, NetworkPolicy for bind shell

## Quick Start

```bash
# Set agent namespace (where neo lives)
export AGENT_NS=agent-namespace

# Deploy everything (charts + build)
make deploy

# Run full automated attack
make auto-attack

# Cleanup
make clean
```

## Structure

```
build/          Attacker container image (Dockerfile + scripts)
chart/attack/   Helm chart: attacker deployment + NetworkPolicy
chart/target-apps/  Helm chart: poisoned inventory-app + RBAC
scripts/        Deploy, attack automation, payloads
tests/          Helm template tests
```

## Attack Flow

1. `trigger.sh` — sends prompt to Neo via `/api/chat` to read poisoned logs
2. `wait-shell.sh` — polls for bind shell on `:4444`
3. `connect.sh` — injects takeover payloads through bind shell
4. `exploit.sh` — triggers exploitation prompt

## Tests

```bash
make test
```
