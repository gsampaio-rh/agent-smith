"""Script execution with output streaming."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Generator

from smith.config import SmithConfig
from smith.registry import Attack, get_attack


@dataclass
class RunResult:
    """Result of a script execution."""

    attack_id: str
    exit_code: int
    output: str
    timed_out: bool = False


@dataclass
class ScriptRunner:
    """Execute attack scripts by ID."""

    script_dir: str = ""
    env_overrides: dict[str, str] = field(default_factory=dict)
    timeout: int = 300

    def __post_init__(self) -> None:
        if not self.script_dir:
            self.script_dir = SmithConfig.from_env().scripts_dir

    def _script_path(self, attack: Attack) -> str:
        return os.path.join(self.script_dir, attack.script)

    def run(self, attack_id: str) -> RunResult:
        """Run a script synchronously, capturing all output."""
        attack = get_attack(attack_id)
        path = self._script_path(attack)
        env = {**os.environ, **self.env_overrides}

        try:
            proc = subprocess.run(
                ["bash", path],
                capture_output=True,
                text=True,
                env=env,
                timeout=self.timeout,
            )
            return RunResult(
                attack_id=attack_id,
                exit_code=proc.returncode,
                output=proc.stdout + proc.stderr,
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                attack_id=attack_id,
                exit_code=-1,
                output=f"Timed out after {self.timeout}s",
                timed_out=True,
            )

    def stream(self, attack_id: str) -> Generator[str, None, RunResult]:
        """Run a script, yielding output lines as they arrive.

        The final return value is a RunResult (access via StopIteration.value).
        """
        attack = get_attack(attack_id)
        path = self._script_path(attack)
        env = {**os.environ, **self.env_overrides}

        proc = subprocess.Popen(
            ["bash", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        lines: list[str] = []
        assert proc.stdout is not None
        for line in proc.stdout:
            lines.append(line)
            yield line

        proc.wait()
        return RunResult(
            attack_id=attack_id,
            exit_code=proc.returncode,
            output="".join(lines),
        )
