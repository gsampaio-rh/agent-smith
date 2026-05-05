"""Attack detail screen — description, env vars, expected output preview."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from smith.registry import Attack


class AttackDetailScreen(Screen):
    """Full-page detail view for a single attack."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("r", "run_attack", "Run"),
        ("q", "force_quit", "Quit"),
    ]

    CSS = """
    AttackDetailScreen {
        layout: vertical;
        padding: 1 2;
    }

    #detail-content {
        height: 1fr;
    }

    #detail-help {
        height: 1;
        dock: bottom;
        background: $primary-background;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, attack: Attack) -> None:
        super().__init__()
        self._attack = attack

    def compose(self) -> ComposeResult:
        a = self._attack
        env = "\n".join(f"    {v}" for v in a.env_vars) if a.env_vars else "    none"
        shell = "[red]Required[/red]" if a.requires_bind_shell else "[green]Not required[/green]"

        content = (
            f"[bold {a.phase.color}]{a.name}[/]\n"
            f"[dim]{'━' * 50}[/dim]\n\n"
            f"{a.description}\n\n"
            f"[bold]Script:[/bold]       {a.script}\n"
            f"[bold]Phase:[/bold]        [{a.phase.color}]{a.phase.label}[/]\n"
            f"[bold]Bind Shell:[/bold]   {shell}\n"
            f"[bold]Env Vars:[/bold]\n{env}\n"
        )

        yield Vertical(Static(content), id="detail-content")
        yield Static(
            "  [bold]r[/] Run  [bold]Esc[/] Back  [bold]q[/] Quit",
            id="detail-help",
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_force_quit(self) -> None:
        self.app.exit()

    def action_run_attack(self) -> None:
        from smith.screens.execution import ExecutionScreen
        self.app.switch_screen(ExecutionScreen(self._attack))
