"""Footer status bar — agent IP, bind shell state, namespace, elapsed time."""

from __future__ import annotations

import time

from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    """Bottom bar showing live environment status."""

    agent_ip: reactive[str] = reactive("unknown")
    shell_open: reactive[bool] = reactive(False)
    namespace: reactive[str] = reactive("agent-namespace")
    local_dev: reactive[bool] = reactive(False)
    start_time: float = 0.0

    def on_mount(self) -> None:
        self.start_time = time.monotonic()
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        self.refresh()

    def render(self) -> str:
        elapsed = int(time.monotonic() - self.start_time)
        m, s = divmod(elapsed, 60)

        if self.local_dev:
            mode = "[yellow]● DEV LOCAL[/]"
        elif self.shell_open:
            mode = "[green]● SHELL OPEN[/]"
        else:
            mode = "[red]● SHELL CLOSED[/]"

        parts = [f"  {mode}"]

        if not self.local_dev:
            parts.append(f"Agent: [bold]{self.agent_ip}[/]")

        parts.append(f"NS: [cyan]{self.namespace}[/]")
        parts.append(f"Time: {m:02d}:{s:02d}")

        return "  │  ".join(parts)
