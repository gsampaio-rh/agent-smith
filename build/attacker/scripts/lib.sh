#!/usr/bin/env bash
# Shared helpers for in-cluster attack scripts.

AGENT_NS="${AGENT_NS:-agent-namespace}"
NEO_UI_SVC="${NEO_UI_SVC:-neo-ui.${AGENT_NS}.svc:3458}"
BIND_PORT="${BIND_PORT:-4444}"
PROMPTS_FILE="/data/prompts.json"
PAYLOADS_DIR="/data/payloads"
AGENT_HOME="/opt/app-root/src"

SA_TOKEN_PATH="/var/run/secrets/kubernetes.io/serviceaccount/token"
SA_CA_PATH="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

resolve_agent_ip() {
  local token api_url
  if [[ ! -f "$SA_TOKEN_PATH" ]]; then
    echo "ERROR: SA token not found at $SA_TOKEN_PATH" >&2
    return 1
  fi
  token=$(cat "$SA_TOKEN_PATH")
  api_url="https://kubernetes.default.svc/api/v1/namespaces/${AGENT_NS}/pods?labelSelector=app.kubernetes.io/name=neo"
  curl -sk -H "Authorization: Bearer $token" \
    --cacert "$SA_CA_PATH" \
    "$api_url" | jq -r '.items[0].status.podIP'
}

resolve_prompt() {
  local key="$1"
  local env k8s raw
  env=$(jq -r '.environment' "$PROMPTS_FILE")
  k8s=$(jq -r '.k8sPattern' "$PROMPTS_FILE")
  raw=$(jq -r ".$key" "$PROMPTS_FILE")
  echo "$raw $env $k8s"
}

post_prompt() {
  local prompt="$1"
  curl -s -X POST "http://${NEO_UI_SVC}/api/chat" \
    -H 'Content-Type: application/json' \
    -d "$(jq -n --arg p "$prompt" '{prompt: $p}')" \
    -w "\n%{http_code}" 2>&1
}

banner() {
  echo "════════════════════════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════════════════════════"
}
