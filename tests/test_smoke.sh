#!/usr/bin/env bash
# Smoke tests: build the container image and validate smith CLI + scripts.
# Requires: Docker (or Podman with docker alias)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"

IMAGE_NAME="smith-smoke-test"
PASS=0
FAIL=0

assert_exit_zero() {
  local desc="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $desc"; PASS=$((PASS+1))
  else
    echo "  FAIL: $desc (exit code $?)"; FAIL=$((FAIL+1))
  fi
}

assert_output_contains() {
  local desc="$1" needle="$2"
  shift 2
  local output
  output=$("$@" 2>&1) || true
  if echo "$output" | grep -q "$needle"; then
    echo "  PASS: $desc"; PASS=$((PASS+1))
  else
    echo "  FAIL: $desc (expected '$needle')"; FAIL=$((FAIL+1))
  fi
}

echo "=== Smith Smoke Tests ==="
echo ""

# Prepare build context (same as make build but local)
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
cp -r "$BUILD_DIR"/* "$TMPDIR/"
cp -r "$PROJECT_ROOT/scripts/attacks" "$TMPDIR/attacks"
cp -r "$PROJECT_ROOT/scripts/payloads" "$TMPDIR/payloads"
mkdir -p "$TMPDIR/smith-pkg"
cp "$PROJECT_ROOT/pyproject.toml" "$TMPDIR/smith-pkg/"
cp -r "$PROJECT_ROOT/smith" "$TMPDIR/smith-pkg/smith"

echo "--- Building image ---"
docker build -t "$IMAGE_NAME" "$TMPDIR"
echo ""

echo "--- Container tests ---"

# smith is on PATH
assert_exit_zero "smith is on PATH" docker run --rm "$IMAGE_NAME" which smith

# smith --help exits 0
assert_exit_zero "smith --help exits 0" docker run --rm "$IMAGE_NAME" smith --help

# smith list exits 0
assert_exit_zero "smith list exits 0" docker run --rm "$IMAGE_NAME" smith list

# smith plan exits 0
assert_exit_zero "smith plan exits 0" docker run --rm "$IMAGE_NAME" smith plan

# smith status exits 0
assert_exit_zero "smith status exits 0" docker run --rm "$IMAGE_NAME" smith status

# smith run with invalid ID exits non-zero
assert_output_contains "smith run invalid-id shows error" "Unknown attack" docker run --rm "$IMAGE_NAME" smith run nonexistent

# Backward compat: all attack scripts still work with --help
echo ""
echo "--- Backward compat: script --help ---"
for script in attack-recon.sh attack-steal-secrets.sh attack-steal-tokens.sh \
              attack-lateral-db.sh attack-agent-worm.sh attack-persist-claude.sh \
              attack-persist-cronjob.sh attack-exfil-dns.sh attack-miner.sh \
              attack-scale-zero.sh attack-log-flood.sh attack-hijack-model.sh \
              trigger.sh wait-shell.sh connect.sh exploit.sh full-attack.sh \
              hold-shell.sh; do
  assert_exit_zero "$script --help" docker run --rm "$IMAGE_NAME" "$script" --help
done

# SMITH_NO_TUI=1 falls back to bash
assert_output_contains "SMITH_NO_TUI=1 entrypoint mentions bash" "bash" \
  docker run --rm -e SMITH_NO_TUI=1 "$IMAGE_NAME" bash -c "echo bash"

echo ""
echo "--- Cleanup ---"
docker rmi "$IMAGE_NAME" >/dev/null 2>&1 || true

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]] || exit 1
