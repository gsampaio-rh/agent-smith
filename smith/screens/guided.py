"""Guided workshop walkthrough — step-by-step attack sequence with prompts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from smith.cli import DEMO_SEQUENCE
from smith.registry import get_attack


class GuidedScreen(Screen):
    """Step-by-step workshop walkthrough."""

    BINDINGS = [
        ("enter", "run_current", "Run"),
        ("n", "next_step", "Next"),
        ("p", "prev_step", "Previous"),
        ("escape", "go_back", "Back"),
        ("q", "force_quit", "Quit"),
    ]

    CSS = """
    GuidedScreen {
        layout: vertical;
        padding: 1 2;
    }

    #guided-header {
        height: 3;
        background: $primary-background;
        padding: 0 2;
    }

    #guided-content {
        height: 1fr;
        padding: 1 2;
    }

    #guided-footer {
        height: 1;
        dock: bottom;
        background: $primary-background;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._step = 0
        self._attacks = [
            get_attack(aid) for aid in DEMO_SEQUENCE
            if aid in {a.id for a in __import__("smith.registry", fromlist=["ATTACKS"]).ATTACKS}
        ]

    def compose(self) -> ComposeResult:
        yield Static("", id="guided-header")
        yield Static("", id="guided-content")
        yield Static(
            "  [bold]Enter[/] Run  [bold]n[/] Next  [bold]p[/] Prev  "
            "[bold]Esc[/] Back  [bold]q[/] Quit",
            id="guided-footer",
        )

    def on_mount(self) -> None:
        self._render_step()

    def _render_step(self) -> None:
        if not self._attacks:
            return

        attack = self._attacks[self._step]
        total = len(self._attacks)
        progress = f"Step {self._step + 1}/{total}"

        bar_width = 30
        filled = int((self._step + 1) / total * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        header = self.query_one("#guided-header", Static)
        header.update(
            f"\n[bold]Guided Workshop Mode[/bold]  │  {progress}  [{bar}]"
        )

        shell = "[red]bind shell required[/red]" if attack.requires_bind_shell else "[green]no bind shell needed[/green]"

        content = self.query_one("#guided-content", Static)
        content.update(
            f"[bold {attack.phase.color}]{attack.name}[/]\n"
            f"[dim]{'━' * 50}[/dim]\n\n"
            f"{attack.description}\n\n"
            f"[bold]Script:[/bold]     {attack.script}\n"
            f"[bold]Phase:[/bold]      [{attack.phase.color}]{attack.phase.label}[/]\n"
            f"[bold]Requires:[/bold]   {shell}\n\n"
            f"[dim]Press Enter to run this step, or n/p to navigate.[/dim]"
        )

    def action_run_current(self) -> None:
        if self._attacks:
            from smith.screens.execution import ExecutionScreen
            self.app.push_screen(ExecutionScreen(self._attacks[self._step]))

    def action_next_step(self) -> None:
        if self._step < len(self._attacks) - 1:
            self._step += 1
            self._render_step()

    def action_prev_step(self) -> None:
        if self._step > 0:
            self._step -= 1
            self._render_step()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_force_quit(self) -> None:
        self.app.exit()
