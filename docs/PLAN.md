# Plan: Agent Smith

**Status:** Sprint 2 (in progress)
**Date:** 2026-05-04
**Related:** [Kill Chain Spec](specs/kill-chain.md) | [Post-Breach Research](research/post-breach-analysis.md)

Conventions: `[ ]` = pending | `[x]` = done | `[!]` = blocked | **Gate** = required criterion

---

## Sprint 1 — Core Attack Infrastructure

```
Progress: [████████████████████] 100%
```

- [x] Attacker Helm chart (Deployment, NetworkPolicy, RBAC, Route, BuildConfig)
- [x] Attacker container image (UBI9 + ttyd + ncat + scripts)
- [x] In-cluster kill-chain scripts (trigger → wait → connect → exploit)
- [x] Host-side deploy/cleanup scripts
- [x] Helm template tests for attack chart
- [x] Move target-apps chart to the-matrix-infra repo
- [x] Remove stale `build/attacker/` duplicate directory
- [x] Align script comments with kill-chain spec phase definitions

**Gate:** `make deploy` + `make test` pass cleanly on OpenShift cluster

---

## Sprint 2 — Post-Breach Attack Scripts

```
Progress: [████████████████████] 100%
```

All scripts run via bind shell (ncat) from the attacker pod. Each accepts `--help`.

### Recon & Credential Theft
- [x] `attack-recon.sh` — RBAC enumeration, DNS service discovery, cloud metadata, env vars
- [x] `attack-steal-secrets.sh` — Read k8s Secrets + ConfigMaps from target namespace
- [x] `attack-steal-tokens.sh` — SA token pivoting across namespaces

### Lateral Movement
- [x] `attack-lateral-db.sh` — Discover and connect to databases (Postgres, Redis, MySQL, MongoDB)
- [x] `attack-agent-worm.sh` — Agent-to-agent prompt injection propagation

### Persistence
- [x] `attack-persist-claude.sh` — Stealth CLAUDE.md poisoning (subtle insider threat)
- [x] `attack-persist-cronjob.sh` — CronJob that re-opens bind shell every 5 minutes

### Exfiltration
- [x] `attack-exfil-dns.sh` — DNS tunneling via subdomain-encoded queries

### Sabotage
- [x] `attack-miner.sh` — Crypto-miner simulation (CPU exhaustion, visible on Grafana)
- [x] `attack-scale-zero.sh` — Scale deployments to 0 replicas via k8s API PATCH
- [x] `attack-log-flood.sh` — Generate log noise to hinder incident response

### AI-Specific
- [x] `attack-hijack-model.sh` — Redirect ANTHROPIC_BASE_URL to hostile LLM endpoint

### Infrastructure
- [x] `lib.sh` — Added `run_on_agent()` helper and `K8S_API_PREAMBLE` constant
- [x] `motd.sh` — Updated attacker terminal banner with post-breach commands

**Gate:** All scripts pass `--help` and follow existing conventions
