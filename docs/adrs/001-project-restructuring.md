# ADR-001: Project Restructuring — Flat Python Layout

**Status:** Accepted
**Date:** 2026-05-05
**Deciders:** @gsampaio

## Context

The original project layout placed the Python package, its tests, and `pyproject.toml` inside `build/smith/`, and attack scripts inside `build/scripts/`. This coupling to the Docker build context created several problems:

1. **Non-standard Python layout** — `build/smith/pyproject.toml` with `build/smith/smith/` as the package directory. Tools, IDEs, and contributors expect `pyproject.toml` at the repo root.
2. **Nested venv** — `.venv` lived at `build/smith/.venv`, making `make venv` and `make test-smith` use non-obvious paths (`cd build/smith && ...`).
3. **Tests scattered** — Python tests in `build/smith/tests/`, shell tests in `tests/`. Two separate test directories for no good reason.
4. **Attack scripts coupled to build context** — `build/scripts/` existed solely because the Dockerfile `COPY scripts/` expected them there. The Makefile already assembles a temp dir for the build context, so the filesystem layout doesn't need to mirror the Dockerfile.

### Options Considered

1. **Keep as-is** — live with the nested structure.
2. **Flatten with src layout** — `pyproject.toml` at root, `src/smith/` for source.
3. **Flatten with flat layout** — `pyproject.toml` at root, `smith/` directly at root.

## Decision

Option 3 — flat layout with `smith/` at root.

## Rationale

- `pyproject.toml` at root is the universal convention; every Python tool (pytest, pip, IDEs) finds it automatically.
- Flat layout (`smith/` at root) is the simplest structure — no extra `src/` wrapper directory. Widely used by projects like Django, Flask, and Requests.
- Single `tests/` directory for Python + shell tests — pytest ignores `.sh` files, no conflicts.
- Attack scripts under `scripts/attacks/` are logically grouped with other scripts (`deploy.sh`, `cleanup.sh`) rather than hidden inside `build/`.

## Trade-offs

- **Build context assembly** — the Makefile `build` target and `deploy.sh` explicitly copy `scripts/attacks/`, `pyproject.toml`, and `smith/` into the temp build context. Slightly more lines in the build target, but the intent is clearer.
- **Path updates** — `config.py` local-dev detection, `conftest.py` fixtures, and `test_smoke.sh` all needed path adjustments.
- **No import guard** — flat layout allows importing `smith` without installing it (unlike `src` layout). Acceptable for this project since it's not a published library.

## Consequences

- `make venv` / `make test-smith` now operate at project root.
- `build/` contains only container artifacts: `Dockerfile`, `entrypoint.sh`, `motd.sh`.
- Contributors see a standard Python project layout on first clone.
