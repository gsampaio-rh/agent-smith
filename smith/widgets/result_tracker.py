"""Track and display attack results across a session."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from textual.widgets import Static


class AttackStatus(Enum):
    SUCCESS = ("success", "green", "✓")
    FAILURE = ("failure", "red", "✗")
    TIMEOUT = ("timeout", "yellow", "⏱")
    RUNNING = ("running", "blue", "⟳")

    def __init__(self, label: str, color: str, icon: str) -> None:
        self.label_ = label
        self.color = color
        self.icon = icon


@dataclass
class AttackResult:
    attack_id: str
    attack_name: str
    status: AttackStatus
    exit_code: int = 0


class ResultTracker:
    """In-memory session tracker for attack run results."""

    def __init__(self) -> None:
        self._results: list[AttackResult] = []

    def record(self, result: AttackResult) -> None:
        self._results.append(result)

    @property
    def results(self) -> list[AttackResult]:
        return list(self._results)

    @property
    def summary(self) -> dict[AttackStatus, int]:
        counts: dict[AttackStatus, int] = {}
        for r in self._results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    def clear(self) -> None:
        self._results.clear()


class ResultSummaryWidget(Static):
    """Render a compact summary of attack results."""

    def __init__(self, tracker: ResultTracker, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._tracker = tracker

    def refresh_summary(self) -> None:
        summary = self._tracker.summary
        if not summary:
            self.update("[dim]No attacks run yet[/dim]")
            return

        parts = []
        for status in AttackStatus:
            count = summary.get(status, 0)
            if count:
                parts.append(f"[{status.color}]{status.icon} {count} {status.label_}[/{status.color}]")

        total = len(self._tracker.results)
        self.update(f"  Results: {' │ '.join(parts)}  [dim]({total} total)[/dim]")
