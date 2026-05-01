#!/usr/bin/env bash
# Test chart/target-apps/ Helm template rendering (inventory-app + RBAC).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHART_DIR="$PROJECT_ROOT/chart/target-apps"
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

echo "=== target-apps chart template tests ==="

OUTPUT=$(helm template neo-target "$CHART_DIR" 2>&1)

# Namespace
assert_contains "target-apps namespace created" "$OUTPUT" "name: target-apps"

# ConfigMap
assert_contains "poisoned-logs ConfigMap" "$OUTPUT" "name: poisoned-logs"
assert_contains "ConfigMap in target-apps ns" "$OUTPUT" "namespace: target-apps"
assert_contains "payload contains diagnostic text" "$OUTPUT" "DIAGNOSTIC"

# Deployment
assert_contains "inventory-app Deployment" "$OUTPUT" "name: inventory-app"
assert_contains "inventory-app in target-apps" "$OUTPUT" "namespace: target-apps"
assert_contains "uses alpine image" "$OUTPUT" "alpine"

# RBAC (namespace-scoped Role + RoleBinding)
assert_contains "Role created" "$OUTPUT" "neo-target-target-reader"
assert_contains "Role is namespace-scoped" "$OUTPUT" "kind: Role"
assert_contains "RoleBinding created" "$OUTPUT" "neo-target-agent-target-access"
assert_contains "RoleBinding is namespace-scoped" "$OUTPUT" "kind: RoleBinding"
assert_contains "RBAC binds to neo SA" "$OUTPUT" "name: neo"
assert_contains "RBAC grants pods/log access" "$OUTPUT" "pods/log"
assert_contains "Role in target namespace" "$OUTPUT" "namespace: target-apps"

# Should NOT contain attacker resources
assert_not_contains "no attacker pod" "$OUTPUT" "kind: Pod"
assert_not_contains "no NetworkPolicy" "$OUTPUT" "NetworkPolicy"

# Custom values
echo ""
echo "--- Custom values ---"
CUSTOM=$(helm template custom-rel "$CHART_DIR" \
  --set agentNamespace=my-ns \
  --set agentServiceAccount=my-sa \
  --set targetNamespace=my-targets 2>&1)

assert_contains "custom target namespace" "$CUSTOM" "namespace: my-targets"
assert_contains "custom SA binding" "$CUSTOM" "name: my-sa"
assert_contains "custom release in Role name" "$CUSTOM" "custom-rel-target-reader"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]] || exit 1
