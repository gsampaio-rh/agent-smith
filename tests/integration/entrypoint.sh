#!/usr/bin/env bash
set -euo pipefail

echo "=== Mock Neo Agent ==="

# Generate self-signed TLS cert for the K8s API mock (port 443)
mkdir -p /etc/mock-k8s
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout /etc/mock-k8s/tls.key \
  -out /etc/mock-k8s/tls.crt \
  -days 1 -subj "/CN=kubernetes.default.svc" \
  -addext "subjectAltName=DNS:kubernetes.default.svc,DNS:localhost,IP:127.0.0.1" \
  2>/dev/null

# SA token + CA for the agent's own Python code (K8S_API_PREAMBLE reads these)
SA_DIR="/var/run/secrets/kubernetes.io/serviceaccount"
mkdir -p "$SA_DIR"
echo "mock-token-for-integration-tests" > "$SA_DIR/token"
cp /etc/mock-k8s/tls.crt "$SA_DIR/ca.crt"

# Also write to shared volume so the attacker container can read them
SHARED_DIR="/mnt/shared-sa"
if [[ -d "$SHARED_DIR" ]]; then
  cp "$SA_DIR/token" "$SHARED_DIR/token"
  cp "$SA_DIR/ca.crt" "$SHARED_DIR/ca.crt"
  echo "[agent] SA token + CA written to shared volume"
fi

# Create agent workspace dirs that attack scripts expect
mkdir -p /opt/app-root/src/.claude/skills

# Redirect kubernetes.default.svc to localhost for the agent's own K8s API calls
echo "127.0.0.1 kubernetes.default.svc" >> /etc/hosts

# Start bind shell listener (persistent, accepts multiple connections)
echo "[agent] starting bind shell on :4444"
ncat -lk 4444 -e /bin/bash &

# Start mock HTTP servers (Neo UI on :3458, K8s API on :443)
echo "[agent] starting mock servers"
exec python3 /opt/mock/mock_server.py
