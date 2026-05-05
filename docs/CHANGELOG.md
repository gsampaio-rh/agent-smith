# Changelog: Agent Smith

**Related:** [PLAN.md](PLAN.md) | [ADRs](adrs/) | [Kill Chain Spec](specs/kill-chain.md)

---

## Sprint 3 — Attacker TUI Experience

**Date:** 2026-05-04
**Status:** Complete

### Key Outcomes

- **`smith` TUI** — Textual-based interactive terminal replaces raw bash + MOTD as the default attacker experience. Launches automatically via `ttyd` on container start.
- **CLI parity** — `smith run <id>`, `smith list`, `smith plan`, `smith status` cover all non-interactive use cases.
- **Guided mode** — `smith --guided` provides step-by-step workshop walkthrough with prev/next navigation.
- **Visual feedback** — animated banner, color-coded phase indicators, progress spinners, session result tracker.
- **Testing** — 85 Python tests (unit, CLI, TUI snapshots) + container smoke tests validating all 18 scripts.
- **Backward compat** — all `*.sh` scripts remain standalone-runnable with `--help`.

### Decisions

| ADR | Decision |
|-----|----------|
| [ADR-001](adrs/001-project-restructuring.md) | Flat Python layout (`smith/` at root); moved attack scripts under `scripts/attacks/` |

---

## Sprint 2 — Post-Breach Attack Scripts

**Date:** 2026-05-03
**Status:** Complete

### Key Outcomes

- **12 post-breach scripts** covering recon, credential theft, lateral movement, persistence, exfiltration, sabotage, and AI-specific attacks — all runnable via bind shell (`ncat`) from the attacker pod.
- **`lib.sh`** — shared library with `run_on_agent()` helper and `K8S_API_PREAMBLE` for consistent script structure.
- **`motd.sh`** — terminal banner listing available post-breach commands.
- Every script accepts `--help` and follows consistent conventions (color output, error handling, idempotent).

### Scripts Delivered

| Category | Scripts |
|----------|---------|
| Recon & credential theft | `attack-recon.sh`, `attack-steal-secrets.sh`, `attack-steal-tokens.sh` |
| Lateral movement | `attack-lateral-db.sh`, `attack-agent-worm.sh` |
| Persistence | `attack-persist-claude.sh`, `attack-persist-cronjob.sh` |
| Exfiltration | `attack-exfil-dns.sh` |
| Sabotage | `attack-miner.sh`, `attack-scale-zero.sh`, `attack-log-flood.sh` |
| AI-specific | `attack-hijack-model.sh` |

---

## Sprint 1 — Core Attack Infrastructure

**Date:** 2026-05-02
**Status:** Complete

### Key Outcomes

- **Helm chart** (`chart/attack/`) — Deployment, Service, Route, ServiceAccount, Role, RoleBinding, BuildConfig, ImageStream, NetworkPolicy for the attacker pod.
- **Container image** — UBI9 minimal with `ttyd` 1.7.7 (SHA256-pinned), `ncat`, `jq`, Python 3.12.
- **Kill-chain scripts** — `trigger.sh`, `wait-shell.sh`, `connect.sh`, `exploit.sh`, `full-attack.sh`, `hold-shell.sh`.
- **Host-side ops** — `deploy.sh` (Helm install + image build + rollout), `cleanup.sh`, `config.sh`.
- **38 Helm template tests** — validate Deployment shape, RBAC, NetworkPolicy, Route, BuildConfig, custom values.
- **Target-apps chart** moved to [the-matrix-infra](https://github.com/gsampaio-rh/the-matrix-infra) repo.
