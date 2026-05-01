#!/usr/bin/env bash
# Test chart/attack/ Helm template rendering.
# Validates: Deployment, Service, Route, SA, Role, RoleBinding,
#            BuildConfig, ImageStream, NetworkPolicy, Namespace.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHART_DIR="$PROJECT_ROOT/chart/attack"
PASS=0
FAIL=0

assert_contains() {
  local desc="$1" haystack="$2" needle="$3"
  if echo "$haystack" | grep -q "$needle"; then
    echo "  PASS: $desc"; PASS=$((PASS+1))
  else
    echo "  FAIL: $desc (expected '$needle')"; FAIL=$((FAIL+1))
  fi
}

assert_not_contains() {
  local desc="$1" haystack="$2" needle="$3"
  if echo "$haystack" | grep -q "$needle"; then
    echo "  FAIL: $desc (should NOT contain '$needle')"; FAIL=$((FAIL+1))
  else
    echo "  PASS: $desc"; PASS=$((PASS+1))
  fi
}

echo "=== attack chart template tests ==="

OUTPUT=$(helm template neo-attack "$CHART_DIR" 2>&1)

# Attacker namespace
assert_contains "attacker namespace created" "$OUTPUT" "name: attacker"
assert_contains "attacker ns has name label" "$OUTPUT" "name: attacker"

# Deployment (replaces old Pod)
assert_contains "Deployment created" "$OUTPUT" "kind: Deployment"
assert_not_contains "no bare Pod" "$OUTPUT" "kind: Pod"
assert_contains "Deployment uses SA" "$OUTPUT" "serviceAccountName: attacker"
assert_contains "Deployment has ttyd port" "$OUTPUT" "containerPort: 7681"
assert_contains "Deployment has AGENT_NS env" "$OUTPUT" "name: AGENT_NS"
assert_contains "Deployment has NEO_UI_SVC env" "$OUTPUT" "name: NEO_UI_SVC"
assert_contains "Deployment has BIND_PORT env" "$OUTPUT" "name: BIND_PORT"

# Service
assert_contains "Service created" "$OUTPUT" "kind: Service"
assert_contains "Service name" "$OUTPUT" "name: neo-attacker"
assert_contains "Service port 7681" "$OUTPUT" "port: 7681"

# Route
assert_contains "Route created" "$OUTPUT" "kind: Route"
assert_contains "Route targets neo-attacker" "$OUTPUT" "name: neo-attacker"
assert_contains "Route TLS edge" "$OUTPUT" "termination: edge"

# ServiceAccount
assert_contains "ServiceAccount created" "$OUTPUT" "kind: ServiceAccount"

# Role + RoleBinding
assert_contains "Role created" "$OUTPUT" "kind: Role"
assert_contains "Role name" "$OUTPUT" "name: attacker-pod-reader"
assert_contains "Role allows pods" "$OUTPUT" 'resources:.*\|pods'
assert_contains "RoleBinding created" "$OUTPUT" "kind: RoleBinding"

# BuildConfig + ImageStream
assert_contains "BuildConfig created" "$OUTPUT" "kind: BuildConfig"
assert_contains "BuildConfig name" "$OUTPUT" "name: neo-attacker"
assert_contains "ImageStream created" "$OUTPUT" "kind: ImageStream"
assert_contains "ImageStream name" "$OUTPUT" "name: neo-attacker"
assert_contains "BuildConfig docker strategy" "$OUTPUT" "dockerfilePath: Dockerfile"

# NetworkPolicy
assert_contains "NetworkPolicy created" "$OUTPUT" "name: allow-bind-shell"
assert_contains "NetworkPolicy in agent-namespace" "$OUTPUT" "namespace: agent-namespace"
assert_contains "NetworkPolicy port 4444" "$OUTPUT" "port: 4444"
assert_contains "NetworkPolicy allows UI port" "$OUTPUT" "port: 3458"
assert_contains "NetworkPolicy allows terminal port" "$OUTPUT" "port: 7681"

# Should NOT contain target-apps resources
assert_not_contains "no inventory-app" "$OUTPUT" "inventory-app"
assert_not_contains "no poisoned-logs" "$OUTPUT" "poisoned-logs"

# Custom values
echo ""
echo "--- Custom values ---"
CUSTOM=$(helm template custom-rel "$CHART_DIR" \
  --set agentNamespace=my-ns \
  --set attackerNamespace=my-atk \
  --set bindShellPort=5555 \
  --set agentServiceName=custom-ui \
  --set image.attacker.name=my-attacker \
  --set image.attacker.tag=v2 2>&1)

assert_contains "custom agent namespace in NetworkPolicy" "$CUSTOM" "namespace: my-ns"
assert_contains "custom attacker namespace" "$CUSTOM" "namespace: my-atk"
assert_contains "custom bind port" "$CUSTOM" "port: 5555"
assert_contains "custom service name in NEO_UI_SVC" "$CUSTOM" "custom-ui.my-ns.svc:3458"
assert_contains "custom image name in BuildConfig" "$CUSTOM" "name: my-attacker"
assert_contains "custom image tag" "$CUSTOM" "my-attacker:v2"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]] || exit 1
