"""Animated ASCII banner header widget."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static

BANNER_LINES = [
    "",
    "   ╔═══════════════════════════════════════════════════╗",
    "   ║     _                    _     ____        _ _    ║",
    "   ║    / \\   __ _  ___ _ __ | |_  / ___| _ __ (_| |_  ║",
    "   ║   / _ \\ / _` |/ _ | '_ \\| __| \\___ \\| '_ \\| | __| ║",
    "   ║  / ___ | (_| |  __| | | | |_   ___) | | | | | |_  ║",
    "   ║ /_/   \\_\\__, |\\___|_| |_|\\__| |____/|_| |_|_|\\__| ║",
    "   ║         |___/                                      ║",
    "   ║                                                    ║",
    "   ║         Red Team Toolkit — The Matrix Workshop     ║",
    "   ╚═══════════════════════════════════════════════════╝",
    "",
]

BANNER_FULL = "\n".join(BANNER_LINES)


class Banner(Static):
    """ASCII art banner with line-by-line reveal animation on mount."""

    revealed: reactive[int] = reactive(0)

    def __init__(self, animate: bool = True, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._animate = animate

    def on_mount(self) -> None:
        if self._animate:
            self.revealed = 0
            self._timer = self.set_interval(0.06, self._reveal_next)
        else:
            self.revealed = len(BANNER_LINES)
            self.update(BANNER_FULL)

    def _reveal_next(self) -> None:
        self.revealed += 1
        if self.revealed >= len(BANNER_LINES):
            self._timer.stop()

    def watch_revealed(self, value: int) -> None:
        visible = BANNER_LINES[:value]
        self.update("\n".join(visible))
