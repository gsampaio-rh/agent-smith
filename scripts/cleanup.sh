#!/usr/bin/env bash
# Clean up attack infrastructure: uninstall both Helm releases and call reset API.
set -euo pipefail

ATTACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ATTACK_DIR/../config.sh"

TARGET_RELEASE="${TARGET_RELEASE:-neo-target}"
ATTACK_RELEASE="${ATTACK_RELEASE:-neo-attack}"

echo "============================================================"
echo " Neo | Cleanup Attack"
echo "============================================================"
echo ""

echo "── Uninstalling Helm releases ──"
for release in "$ATTACK_RELEASE" "$TARGET_RELEASE"; do
  if helm status "$release" &>/dev/null; then
    helm uninstall "$release"
    echo "  Release $release uninstalled."
  else
    echo "  Release $release not found — skipping."
  fi
done

echo ""
echo "── Deleting attack namespaces ──"
for ns in attacker target-apps; do
  if oc get namespace "$ns" &>/dev/null; then
    oc delete namespace "$ns" --wait=false
    echo "  Namespace $ns deletion initiated."
  else
    echo "  Namespace $ns not found — skipping."
  fi
done

echo ""
echo "── Calling reset API ──"
UI_HOST=$(oc get route "${TARGET_RELEASE%%-target*}-ui" -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || true)
if [[ -n "$UI_HOST" ]]; then
  HTTP_CODE=$(curl -sk -X POST "https://$UI_HOST/api/state/reset" -o /dev/null -w "%{http_code}" 2>&1)
  echo "  Reset response: HTTP $HTTP_CODE"
else
  echo "  WARNING: Could not resolve UI route — reset API not called."
  echo "  Manually run: curl -X POST https://<UI_HOST>/api/state/reset"
fi

echo ""
echo "Cleanup complete."
