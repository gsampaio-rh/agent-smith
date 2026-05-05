# Agent Smith

Adversary tooling for The Matrix workshop. Deploys an attacker pod on OpenShift with a web terminal (`ttyd`) running **`smith`** — an interactive TUI for orchestrating a red-team kill chain and post-breach attacks against a Neo agent.

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

Once deployed, open the attacker Route in a browser. The `smith` TUI launches automatically inside the web terminal.

## Smith TUI

`smith` is the primary interface for running attacks. It launches by default when the container starts (via `ttyd`).

```bash
smith              # interactive TUI (default)
smith --guided     # step-by-step workshop walkthrough
smith run <id>     # run a single attack non-interactively
smith list         # list all attacks grouped by phase
smith plan         # show recommended demo sequence
smith status       # show bind shell state, agent IP, namespace config
```

**Features:**
- Categorized attack menu (kill chain + post-breach)
- Per-attack detail panel with description, env vars, and expected output
- Live output streaming with color-coded log levels
- Status bar showing agent IP, bind shell state, namespace, elapsed time
- Guided mode for workshop walkthroughs

Set `SMITH_NO_TUI=1` or pass `--no-tui` to fall back to raw bash.

## Kill Chain

The core attack sequence (runnable individually or via `smith run full-attack`):

1. **trigger** — sends prompt to Neo via `/api/chat` to read poisoned logs
2. **wait-shell** — polls for bind shell on `:4444`
3. **connect** — injects takeover payloads through bind shell
4. **exploit** — triggers exploitation prompt

## Post-Breach Attacks

After the bind shell is open, post-breach attacks run through `ncat` on the agent pod:

| ID | Category | What it does |
|---|---|---|
| `recon` | Recon | RBAC, DNS discovery, cloud metadata, env vars |
| `steal-secrets` | Credential theft | Read k8s Secrets + ConfigMaps |
| `steal-tokens` | Credential theft | SA token pivoting |
| `lateral-db` | Lateral movement | Connect to databases |
| `agent-worm` | Lateral movement | Infect other Neo agents |
| `persist-claude` | Persistence | Stealth CLAUDE.md poisoning |
| `persist-cronjob` | Persistence | CronJob bind shell reopener |
| `exfil-dns` | Exfiltration | DNS tunneling |
| `miner` | Sabotage | Crypto-miner CPU spike |
| `scale-zero` | Sabotage | Scale deployment to zero |
| `log-flood` | Sabotage | Log flooding |
| `hijack-model` | AI-specific | Redirect LLM endpoint |

All attacks support `smith run <id>` or standalone `*.sh --help`.

## Structure

```
smith/              Python package — TUI, CLI, attack registry, runner
tests/              Python unit/TUI tests + Helm template tests + smoke tests
scripts/
  attacks/          Kill-chain and post-breach bash scripts
  payloads/         Prompt injection payloads
  deploy.sh         Host-side deployment orchestration
  cleanup.sh        Teardown attacker infrastructure
  config.sh         Shared environment defaults
build/
  Dockerfile        Attacker container (UBI9 + ttyd + Python + smith)
  entrypoint.sh     Container entrypoint (smith → ttyd)
  motd.sh           Terminal banner
chart/attack/       Helm chart: Deployment, NetworkPolicy, RBAC, Route, BuildConfig
docs/               Specs, research, project plan, changelog
pyproject.toml      Python project config
```

## Development

```bash
# Create venv and install smith + dev deps
make venv

# Run Python tests (creates venv if missing)
make test-smith

# Run all tests (Python + Helm)
make test

# Run container smoke tests (requires Docker)
make test-smoke
```
