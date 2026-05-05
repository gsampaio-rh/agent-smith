"""Live phase tracker — displays attack phases with status indicators."""

from __future__ import annotations

from enum import Enum

from textual.reactive import reactive
from textual.widgets import Static


class PhaseStatus(Enum):
    PENDING = ("pending", "dim", "○")
    ACTIVE = ("active", "bold yellow", "◉")
    DONE = ("done", "green", "●")


class PhaseProgress(Static):
    """Renders a vertical list of phases with live status updates."""

    current_phase: reactive[str] = reactive("")

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._phases: list[str] = []
        self._completed: set[str] = set()

    def set_phase(self, name: str) -> None:
        if name and name not in self._phases:
            self._phases.append(name)
        if self._phases:
            previous = [p for p in self._phases if p != name]
            self._completed.update(previous)
        self.current_phase = name

    def watch_current_phase(self, _value: str) -> None:
        self._render_phases()

    def _render_phases(self) -> None:
        if not self._phases:
            self.update("[dim]Waiting for phases...[/dim]")
            return

        lines = ["[bold]Phases[/bold]", ""]
        for phase in self._phases:
            if phase == self.current_phase:
                status = PhaseStatus.ACTIVE
            elif phase in self._completed:
                status = PhaseStatus.DONE
            else:
                status = PhaseStatus.PENDING
            lines.append(
                f"  [{status.value[1]}]{status.value[2]} {phase}[/{status.value[1]}]"
            )
        self.update("\n".join(lines))

    def mark_all_done(self) -> None:
        self._completed.update(self._phases)
        self._render_phases()
