#!/usr/bin/env bash
# Deploy attack infrastructure via Helm (two charts) + build attacker image:
#   1. target-apps — inventory-app with poisoned logs + RBAC
#   2. attack — attacker deployment + NetworkPolicy + RBAC + Route
#   3. Build attacker image (ttyd + attack scripts)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/config.sh"

TARGET_CHART="$PROJECT_ROOT/chart/target-apps"
ATTACK_CHART="$PROJECT_ROOT/chart/attack"
TARGET_RELEASE="${TARGET_RELEASE:-neo-target}"
ATTACK_RELEASE="${ATTACK_RELEASE:-neo-attack}"
AGENT_SA="${TARGET_RELEASE%%-target*}"

echo "============================================================"
echo " Agent Smith | Deploy Attack Infrastructure"
echo "============================================================"
echo ""
echo "  Target release:   $TARGET_RELEASE"
echo "  Attack release:   $ATTACK_RELEASE"
echo "  Agent NS:         $AGENT_NS"
echo "  Agent SA:         $AGENT_SA"
echo ""

echo "── Phase 1: Installing target-apps (inventory-app + RBAC) ──"
helm upgrade --install "$TARGET_RELEASE" "$TARGET_CHART" \
  --set agentNamespace="$AGENT_NS" \
  --set agentServiceAccount="$AGENT_SA" \
  --wait --timeout 120s
echo ""

echo "── Phase 2: Installing attack chart (Deployment + NetworkPolicy + Route) ──"
helm upgrade --install "$ATTACK_RELEASE" "$ATTACK_CHART" \
  --set agentNamespace="$AGENT_NS" \
  --wait --timeout 120s
echo ""

echo "── Phase 3: Building attacker image ──"

ATTACKER_BUILD_CONTEXT=$(mktemp -d)
trap 'rm -rf "$ATTACKER_BUILD_CONTEXT"' EXIT

cp -r "$BUILD_DIR"/* "$ATTACKER_BUILD_CONTEXT/"
cp -r "$SCRIPT_DIR/payloads" "$ATTACKER_BUILD_CONTEXT/payloads"

oc start-build "$ATTACKER_BC_NAME" \
  --from-dir="$ATTACKER_BUILD_CONTEXT" \
  -n "$ATTACKER_NS" \
  --follow
echo ""

echo "── Phase 4: Rolling out attacker deployment ──"
oc rollout restart deployment/attacker -n "$ATTACKER_NS"
oc rollout status deployment/attacker -n "$ATTACKER_NS" --timeout=60s
echo ""

echo "── Verifying resources ──"
echo "  target-apps:"
oc get deploy -n target-apps -o name 2>/dev/null | sed 's/^/    /'
echo "  attacker:"
oc get deploy -n "$ATTACKER_NS" -o name 2>/dev/null | sed 's/^/    /'
echo "  attacker route:"
ATTACKER_HOST=$(oc get route neo-attacker -n "$ATTACKER_NS" -o jsonpath='{.spec.host}' 2>/dev/null || echo "not found")
echo "    https://$ATTACKER_HOST"

echo ""
echo "Attack infrastructure deployed."
echo ""
echo "Next steps:"
echo "  1. Open attacker terminal: https://$ATTACKER_HOST"
echo "  2. Run: full-attack.sh"
echo "  3. Or step-by-step: trigger.sh -> wait-shell.sh -> connect.sh -> exploit.sh"
echo "  4. Cleanup: ./scripts/cleanup.sh"
