#!/usr/bin/env bash
# Clean up attack infrastructure: uninstall Helm release, delete namespace, call reset API.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

ATTACK_RELEASE="${ATTACK_RELEASE:-neo-attack}"

echo "============================================================"
echo " Neo | Cleanup Attack"
echo "============================================================"
echo ""

echo "── Uninstalling Helm release ──"
if helm status "$ATTACK_RELEASE" &>/dev/null; then
  helm uninstall "$ATTACK_RELEASE"
  echo "  Release $ATTACK_RELEASE uninstalled."
else
  echo "  Release $ATTACK_RELEASE not found — skipping."
fi

echo ""
echo "── Deleting attacker namespace ──"
if oc get namespace "$ATTACKER_NS" &>/dev/null; then
  oc delete namespace "$ATTACKER_NS" --wait=false
  echo "  Namespace $ATTACKER_NS deletion initiated."
else
  echo "  Namespace $ATTACKER_NS not found — skipping."
fi

echo ""
echo "── Calling reset API ──"
UI_HOST=$(oc get route neo-ui -n "$AGENT_NS" -o jsonpath='{.spec.host}' 2>/dev/null || true)
if [[ -n "$UI_HOST" ]]; then
  HTTP_CODE=$(curl -sk -X POST "https://$UI_HOST/api/state/reset" -o /dev/null -w "%{http_code}" 2>&1)
  echo "  Reset response: HTTP $HTTP_CODE"
else
  echo "  WARNING: Could not resolve UI route — reset API not called."
  echo "  Manually run: curl -X POST https://<UI_HOST>/api/state/reset"
fi

echo ""
echo "Cleanup complete."
