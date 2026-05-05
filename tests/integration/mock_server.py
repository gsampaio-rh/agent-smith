"""Mock Neo agent: HTTP API (/api/chat) + K8s API stub.

Runs two HTTP servers:
  - Port 3458: Neo UI API (POST /api/chat returns 202)
  - Port 6443: Fake K8s API with self-signed TLS (pods, secrets, configmaps,
    deployments, cronjobs, selfsubjectrulesreviews)
"""

from __future__ import annotations

import json
import ssl
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

NEO_PORT = 3458
K8S_PORT = 443

AGENT_POD_IP = "agent"

# --- Canned K8s API responses ---

PODS_RESPONSE = {
    "apiVersion": "v1",
    "kind": "PodList",
    "items": [
        {
            "metadata": {
                "name": "neo-agent-0",
                "namespace": "agent-namespace",
                "labels": {"app.kubernetes.io/name": "neo"},
            },
            "status": {"podIP": AGENT_POD_IP, "phase": "Running"},
        }
    ],
}

SECRETS_RESPONSE = {
    "apiVersion": "v1",
    "kind": "SecretList",
    "items": [
        {
            "metadata": {"name": "db-credentials", "namespace": "target-apps"},
            "type": "Opaque",
            "data": {
                "username": "YWRtaW4=",  # admin
                "password": "czNjcjN0",  # s3cr3t
            },
        }
    ],
}

CONFIGMAPS_RESPONSE = {
    "apiVersion": "v1",
    "kind": "ConfigMapList",
    "items": [
        {
            "metadata": {"name": "app-config", "namespace": "target-apps"},
            "data": {"DATABASE_URL": "postgres://db.target-apps.svc:5432/app"},
        }
    ],
}

DEPLOYMENT_RESPONSE = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {"name": "inventory-app", "namespace": "target-apps"},
    "spec": {"replicas": 3},
}

DEPLOYMENTS_LIST_RESPONSE = {
    "apiVersion": "apps/v1",
    "kind": "DeploymentList",
    "items": [DEPLOYMENT_RESPONSE],
}

RULES_REVIEW_RESPONSE = {
    "apiVersion": "authorization.k8s.io/v1",
    "kind": "SelfSubjectRulesReview",
    "status": {
        "resourceRules": [
            {"verbs": ["get", "list"], "resources": ["pods", "secrets"]},
            {"verbs": ["create"], "resources": ["cronjobs"]},
            {"verbs": ["patch"], "resources": ["deployments"]},
        ]
    },
}

CRONJOB_CREATED_RESPONSE = {
    "apiVersion": "batch/v1",
    "kind": "CronJob",
    "metadata": {"name": "app-health-check", "namespace": "agent-namespace"},
}

POD_LOG_RESPONSE = "2026-05-05T08:00:00Z INFO  inventory-app started\n"


class NeoUIHandler(BaseHTTPRequestHandler):
    """Mock Neo UI — responds to POST /api/chat with 202."""

    def do_POST(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        self.rfile.read(content_len)

        if self.path == "/api/chat":
            body = json.dumps({"response": "ok", "id": "mock-123"}).encode()
            self.send_response(202)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_GET(self) -> None:
        self.send_error(404)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[neo-ui] {fmt % args}")


class K8sAPIHandler(BaseHTTPRequestHandler):
    """Mock K8s API — handles GET/POST/PATCH for common resources."""

    def _respond(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = self.path

        if "/pods" in path and "/log" in path:
            data = POD_LOG_RESPONSE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif "/pods" in path:
            self._respond(200, PODS_RESPONSE)
        elif "/secrets" in path:
            self._respond(200, SECRETS_RESPONSE)
        elif "/configmaps" in path:
            self._respond(200, CONFIGMAPS_RESPONSE)
        elif "/deployments/" in path:
            self._respond(200, DEPLOYMENT_RESPONSE)
        elif "/deployments" in path:
            self._respond(200, DEPLOYMENTS_LIST_RESPONSE)
        else:
            self._respond(200, {"apiVersion": "v1", "kind": "Status", "status": "ok"})

    def do_POST(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        self.rfile.read(content_len)

        if "selfsubjectrulesreviews" in self.path:
            self._respond(201, RULES_REVIEW_RESPONSE)
        elif "/cronjobs" in self.path:
            self._respond(201, CRONJOB_CREATED_RESPONSE)
        else:
            self._respond(201, {"status": "created"})

    def do_PATCH(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        self.rfile.read(content_len)

        if "/deployments/" in self.path:
            patched = dict(DEPLOYMENT_RESPONSE)
            patched["spec"] = {"replicas": 0}
            self._respond(200, patched)
        else:
            self._respond(200, {"status": "patched"})

    def do_DELETE(self) -> None:
        self._respond(200, {"status": "deleted"})

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[k8s-api] {fmt % args}")


def run_neo_ui() -> None:
    server = HTTPServer(("0.0.0.0", NEO_PORT), NeoUIHandler)
    print(f"[neo-ui] listening on :{NEO_PORT}")
    server.serve_forever()


def run_k8s_api() -> None:
    server = HTTPServer(("0.0.0.0", K8S_PORT), K8sAPIHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain("/etc/mock-k8s/tls.crt", "/etc/mock-k8s/tls.key")
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print(f"[k8s-api] listening on :{K8S_PORT} (TLS)")
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=run_neo_ui, daemon=True).start()
    threading.Thread(target=run_k8s_api, daemon=True).start()

    print("[mock-server] all services started")

    # Block forever
    threading.Event().wait()
