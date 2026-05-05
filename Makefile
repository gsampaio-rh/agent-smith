.PHONY: deploy build clean test test-smith test-smoke test-integration dev dev-down venv help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

deploy: ## Deploy attack infrastructure (attacker pod + NetworkPolicy + build)
	./scripts/deploy.sh

build: ## Build attacker container image only
	@TMPDIR=$$(mktemp -d) && \
	  trap "rm -rf $$TMPDIR" EXIT && \
	  cp -r build/* "$$TMPDIR/" && \
	  cp -r scripts/attacks "$$TMPDIR/attacks" && \
	  cp -r scripts/payloads "$$TMPDIR/payloads" && \
	  mkdir -p "$$TMPDIR/smith-pkg" && \
	  cp pyproject.toml "$$TMPDIR/smith-pkg/" && \
	  cp -r smith "$$TMPDIR/smith-pkg/smith" && \
	  oc start-build $${ATTACKER_BC_NAME:-neo-attacker} --from-dir="$$TMPDIR" -n $${ATTACKER_NS:-attacker} --follow

clean: ## Remove attack infrastructure
	./scripts/cleanup.sh

test: test-smith ## Run all tests (Helm + Python)
	bash tests/attack-chart.test.sh

venv: ## Create Python venv and install smith + dev deps
	python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

test-smith: ## Run Python unit + TUI tests (creates venv if missing)
	@test -d .venv || $(MAKE) venv
	.venv/bin/python -m pytest tests/ -v

test-smoke: ## Run container smoke tests (requires Docker)
	bash tests/test_smoke.sh

test-integration: ## Run end-to-end integration tests (requires Docker)
	bash tests/integration/run.sh

dev: ## Start mock agent + attacker and drop into interactive shell
	@COMPOSE=""; \
	if command -v docker >/dev/null 2>&1; then COMPOSE="docker compose"; \
	elif command -v podman >/dev/null 2>&1; then COMPOSE="podman compose"; export DOCKER_CONFIG="$${DOCKER_CONFIG:-/dev/null}"; \
	else echo "ERROR: Neither docker nor podman found." >&2; exit 1; fi; \
	$$COMPOSE -f tests/integration/compose.yaml up -d --build --wait && \
	echo "" && \
	echo "Mock agent running (HTTP :3458 + bind shell :4444 + K8s API :443)" && \
	echo "Dropping into attacker container... try: smith, smith list, smith run trigger" && \
	echo "" && \
	$$COMPOSE -f tests/integration/compose.yaml exec attacker bash

dev-down: ## Stop and remove dev containers
	@COMPOSE=""; \
	if command -v docker >/dev/null 2>&1; then COMPOSE="docker compose"; \
	elif command -v podman >/dev/null 2>&1; then COMPOSE="podman compose"; export DOCKER_CONFIG="$${DOCKER_CONFIG:-/dev/null}"; \
	else echo "ERROR: Neither docker nor podman found." >&2; exit 1; fi; \
	$$COMPOSE -f tests/integration/compose.yaml down -v --remove-orphans
