.PHONY: deploy build clean test help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

deploy: ## Deploy attack infrastructure (attacker pod + NetworkPolicy + build)
	./scripts/deploy.sh

build: ## Build attacker container image only
	@TMPDIR=$$(mktemp -d) && \
	  trap "rm -rf $$TMPDIR" EXIT && \
	  cp -r build/* "$$TMPDIR/" && \
	  cp -r scripts/payloads "$$TMPDIR/payloads" && \
	  oc start-build $${ATTACKER_BC_NAME:-neo-attacker} --from-dir="$$TMPDIR" -n $${ATTACKER_NS:-attacker} --follow

clean: ## Remove attack infrastructure
	./scripts/cleanup.sh

test: ## Run Helm template tests
	bash tests/attack-chart.test.sh
