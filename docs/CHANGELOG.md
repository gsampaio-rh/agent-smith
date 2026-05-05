# Changelog: Agent Smith

**Related:** [PLAN.md](PLAN.md) | [ADRs](adrs/) | [Kill Chain Spec](specs/kill-chain.md)

---

## Sprint 4 — Attack Visualization & Pod Targeting

**Date:** 2026-05-05
**Status:** Complete

### Key Outcomes

- **Per-attack pod targeting** — new `TargetPicker` screen discovers all Neo pods via K8s API and lets the user choose a target before each attack. Pods are listed with name, IP, status, and bind-shell state.
- **CLI targeting** — `smith run <id> --target <ip>` passes `AGENT_POD_IP` to scripts, skipping pod discovery.
- **Multi-pod support** — `discover_agent_pods()` returns all Neo pods (not just the first). `lib.sh` respects `AGENT_POD_IP` env var for direct targeting.
- **Enriched attack registry** — every attack now includes MITRE ATT&CK technique ID, impact summary, multi-line briefing, expected loot types, and human-readable attack steps.
- **Structured output parser** — `smith/output_parser.py` parses `@PHASE`, `@TARGET`, `@FINDING`, `@LOOT`, `@RESULT` markers from script stdout into typed events consumed by the TUI in real time.
- **Script markers** — all 18 attack scripts instrumented with structured output markers. Markers are transparent in raw terminal mode.
- **Three-phase execution screen** — Briefing (technique, impact, steps, target info) → Live Execution (split layout with phase tracker + finding stream + raw output) → Results (loot summary + findings count).
- **4 new widgets** — `BriefingPanel`, `PhaseProgress`, `FindingStream`, `LootPanel`.
- **Tests** — 145 tests passing (31 new: output parser, pod discovery, enriched registry fields, updated TUI snapshots).

### New Files

| File | Purpose |
|------|---------|
| `smith/output_parser.py` | Parse `@MARKER` lines from script stdout |
| `smith/screens/target_picker.py` | Per-attack pod selection screen |
| `smith/widgets/briefing_panel.py` | Pre-attack technique/impact/steps display |
| `smith/widgets/phase_progress.py` | Live phase tracker with status indicators |
| `smith/widgets/finding_card.py` | Scrolling severity-colored findings log |
| `smith/widgets/loot_panel.py` | Post-attack loot summary grouped by type |
| `tests/test_output_parser.py` | Parser unit tests |

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
