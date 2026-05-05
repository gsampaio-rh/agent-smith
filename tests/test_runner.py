"""Tests for the script runner."""

from __future__ import annotations

import os
import stat
import tempfile

import pytest

from smith.runner import ScriptRunner


@pytest.fixture()
def tmp_scripts(tmp_path):
    """Create temp scripts that exit 0 and exit 1."""
    ok = tmp_path / "ok.sh"
    ok.write_text("#!/usr/bin/env bash\necho 'hello'\nexit 0\n")
    ok.chmod(ok.stat().st_mode | stat.S_IEXEC)

    fail = tmp_path / "fail.sh"
    fail.write_text("#!/usr/bin/env bash\necho 'oops' >&2\nexit 42\n")
    fail.chmod(fail.stat().st_mode | stat.S_IEXEC)

    slow = tmp_path / "slow.sh"
    slow.write_text("#!/usr/bin/env bash\nsleep 60\n")
    slow.chmod(slow.stat().st_mode | stat.S_IEXEC)

    return tmp_path


class TestScriptRunner:
    def _runner(self, script_dir: str) -> ScriptRunner:
        return ScriptRunner(script_dir=script_dir, timeout=5)

    def test_run_success(self, tmp_scripts, monkeypatch) -> None:
        monkeypatch.setattr(
            "smith.runner.get_attack",
            lambda aid: type("A", (), {"script": "ok.sh"})(),
        )
        runner = self._runner(str(tmp_scripts))
        result = runner.run("ok")
        assert result.exit_code == 0
        assert "hello" in result.output
        assert not result.timed_out

    def test_run_failure(self, tmp_scripts, monkeypatch) -> None:
        monkeypatch.setattr(
            "smith.runner.get_attack",
            lambda aid: type("A", (), {"script": "fail.sh"})(),
        )
        runner = self._runner(str(tmp_scripts))
        result = runner.run("fail")
        assert result.exit_code == 42
        assert "oops" in result.output

    def test_run_timeout(self, tmp_scripts, monkeypatch) -> None:
        monkeypatch.setattr(
            "smith.runner.get_attack",
            lambda aid: type("A", (), {"script": "slow.sh"})(),
        )
        runner = ScriptRunner(script_dir=str(tmp_scripts), timeout=1)
        result = runner.run("slow")
        assert result.timed_out
        assert result.exit_code == -1

    def test_invalid_attack_id_raises(self) -> None:
        runner = ScriptRunner()
        with pytest.raises(ValueError, match="Unknown attack"):
            runner.run("does-not-exist")

    def test_stream_yields_lines(self, tmp_scripts, monkeypatch) -> None:
        monkeypatch.setattr(
            "smith.runner.get_attack",
            lambda aid: type("A", (), {"script": "ok.sh"})(),
        )
        runner = self._runner(str(tmp_scripts))
        lines = list(runner.stream("ok"))
        assert any("hello" in line for line in lines)
