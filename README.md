# Agent Smith

Adversary tooling for The Matrix workshop. Deploys:

- **attacker**: ttyd-based container with attack scripts, NetworkPolicy for bind shell

> **Note:** The `target-apps` chart (poisoned inventory-app + RBAC) is managed by [the-matrix-infra](https://github.com/gsampaio-rh/the-matrix-infra).

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
