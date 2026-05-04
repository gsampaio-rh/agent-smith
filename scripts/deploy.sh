#!/usr/bin/env bash
# Deploy attacker infrastructure:
#   1. attack chart — attacker deployment + NetworkPolicy + RBAC + Route
#   2. Build attacker image (ttyd + attack scripts)
#
# Note: target-apps chart is managed by the-matrix-infra repo.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/config.sh"

ATTACK_CHART="$PROJECT_ROOT/chart/attack"
ATTACK_RELEASE="${ATTACK_RELEASE:-neo-attack}"

echo "============================================================"
echo " Agent Smith | Deploy Attacker"
echo "============================================================"
echo ""
echo "  Attack release:   $ATTACK_RELEASE"
echo "  Agent NS:         $AGENT_NS"
echo "  Attacker NS:      $ATTACKER_NS"
echo ""

echo "── Phase 1: Installing attack chart (Deployment + NetworkPolicy + Route) ──"
helm upgrade --install "$ATTACK_RELEASE" "$ATTACK_CHART" \
  --set agentNamespace="$AGENT_NS" \
  --set attackerNamespace="$ATTACKER_NS" \
  --wait --timeout 120s
echo ""

echo "── Phase 2: Building attacker image ──"

ATTACKER_BUILD_CONTEXT=$(mktemp -d)
trap 'rm -rf "$ATTACKER_BUILD_CONTEXT"' EXIT

cp -r "$BUILD_DIR"/* "$ATTACKER_BUILD_CONTEXT/"
cp -r "$SCRIPT_DIR/payloads" "$ATTACKER_BUILD_CONTEXT/payloads"

oc start-build "$ATTACKER_BC_NAME" \
  --from-dir="$ATTACKER_BUILD_CONTEXT" \
  -n "$ATTACKER_NS" \
  --follow
echo ""

echo "── Phase 3: Rolling out attacker deployment ──"
oc rollout restart deployment/attacker -n "$ATTACKER_NS"
oc rollout status deployment/attacker -n "$ATTACKER_NS" --timeout=60s
echo ""

echo "── Verifying ──"
echo "  attacker:"
oc get deploy -n "$ATTACKER_NS" -o name 2>/dev/null | sed 's/^/    /'
ATTACKER_HOST=$(oc get route neo-attacker -n "$ATTACKER_NS" -o jsonpath='{.spec.host}' 2>/dev/null || echo "not found")
echo "  route: https://$ATTACKER_HOST"

echo ""
echo "Attacker deployed."
echo ""
echo "Next steps:"
echo "  1. Open attacker terminal: https://$ATTACKER_HOST"
echo "  2. Run: full-attack.sh"
echo "  3. Or step-by-step: trigger.sh -> wait-shell.sh -> connect.sh -> exploit.sh"
