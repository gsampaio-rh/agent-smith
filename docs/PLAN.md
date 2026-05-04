# Plan: Agent Smith

**Status:** Sprint 1 (in progress)
**Date:** 2026-05-04
**Related:** [Kill Chain Spec](specs/kill-chain.md) | [Post-Breach Research](research/post-breach-analysis.md)

Conventions: `[ ]` = pending | `[x]` = done | `[!]` = blocked | **Gate** = required criterion

---

## Sprint 1 — Core Attack Infrastructure

```
Progress: [████████████████░░░░] ~80%
```

- [x] Attacker Helm chart (Deployment, NetworkPolicy, RBAC, Route, BuildConfig)
- [x] Attacker container image (UBI9 + ttyd + ncat + scripts)
- [x] In-cluster kill-chain scripts (trigger → wait → connect → exploit)
- [x] Host-side deploy/cleanup scripts
- [x] Helm template tests for attack chart
- [x] Move target-apps chart to the-matrix-infra repo
- [ ] Remove stale `build/attacker/` duplicate directory
- [ ] Align script comments with kill-chain spec phase definitions

**Gate:** `make deploy` + `make test` pass cleanly on OpenShift cluster

---

## Sprint 2 — Post-Breach Expansion

```
Progress: [░░░░░░░░░░░░░░░░░░░░] 0%
```

- [ ] DNS tunneling exfiltration demo (P1 from post-breach analysis)
- [ ] Lateral movement to DB visualization on Map (P1)
- [ ] Crypto-miner simulation for Grafana demo (P2)
- [ ] Agent-to-agent worm propagation (P2, requires multi-pod setup)
