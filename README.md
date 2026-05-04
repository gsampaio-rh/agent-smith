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

# Cleanup
make clean
```

## Structure

```
build/          Attacker container image (Dockerfile + scripts)
chart/attack/   Helm chart: attacker deployment + NetworkPolicy
docs/           Specs, research, and project plan
scripts/        Deploy, cleanup, payloads
tests/          Helm template tests
```

## Kill Chain

1. `trigger.sh` — sends prompt to Neo via `/api/chat` to read poisoned logs
2. `wait-shell.sh` — polls for bind shell on `:4444`
3. `connect.sh` — injects takeover payloads through bind shell
4. `exploit.sh` — triggers exploitation prompt

Or run `full-attack.sh` for the full sequence.

## Post-Breach Attacks

After the bind shell is open, individual attack scripts run through `ncat`:

| Script | Category | What it does |
|---|---|---|
| `attack-recon.sh` | Recon | RBAC, DNS discovery, cloud metadata, env vars |
| `attack-steal-secrets.sh` | Credential theft | Read k8s Secrets + ConfigMaps |
| `attack-steal-tokens.sh` | Credential theft | SA token pivoting |
| `attack-lateral-db.sh` | Lateral movement | Connect to databases |
| `attack-agent-worm.sh` | Lateral movement | Infect other Neo agents |
| `attack-persist-claude.sh` | Persistence | Stealth CLAUDE.md poisoning |
| `attack-persist-cronjob.sh` | Persistence | CronJob bind shell reopener |
| `attack-exfil-dns.sh` | Exfiltration | DNS tunneling |
| `attack-miner.sh` | Sabotage | Crypto-miner CPU spike |
| `attack-scale-zero.sh` | Sabotage | Scale deployment to zero |
| `attack-log-flood.sh` | Sabotage | Log flooding |
| `attack-hijack-model.sh` | AI-specific | Redirect LLM endpoint |

All scripts support `--help`.

## Tests

```bash
make test
```
