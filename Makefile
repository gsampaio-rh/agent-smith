.PHONY: deploy build clean test test-smith test-smoke venv help

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
