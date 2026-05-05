"""Main menu screen — categorized attack list + detail preview sidebar."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import OptionList, Static

from smith.registry import Attack, ATTACKS_BY_ID
from smith.widgets.banner import Banner
from smith.widgets.phase_list import PhaseList
from smith.widgets.result_tracker import ResultSummaryWidget


class AttackPreview(Static):
    """Right-side panel showing details for the highlighted attack."""

    def update_attack(self, attack: Attack | None) -> None:
        if attack is None:
            self.update("[dim]Select an attack to see details[/dim]")
            return

        shell = "[red]yes[/red]" if attack.requires_bind_shell else "[green]no[/green]"

        lines = [
            f"[bold {attack.phase.color}]{attack.name}[/]",
            f"[dim]{'─' * 40}[/dim]",
            "",
            f"{attack.description}",
            "",
            f"[bold]Technique:[/bold]  {attack.technique}",
            f"[bold]Phase:[/bold]      [{attack.phase.color}]{attack.phase.label}[/]",
            f"[bold]Bind shell:[/bold] {shell}",
            f"[bold]Impact:[/bold]     {attack.impact}",
        ]

        if attack.loot_types:
            lines.append(f"[bold]Loot:[/bold]       {', '.join(attack.loot_types)}")

        lines += ["", "[dim]Press Enter to run  •  ? for help[/dim]"]
        self.update("\n".join(lines))


class MainMenuScreen(Screen):
    """Two-column layout: attack list (left) + preview (right)."""

    BINDINGS = [
        ("q", "request_quit", "Quit"),
        ("question_mark", "help", "Help"),
        ("r", "refresh_status", "Refresh"),
    ]

    CSS = """
    MainMenuScreen {
        layout: vertical;
    }

    #banner {
        height: auto;
        color: $success;
        text-align: center;
    }

    #main-content {
        height: 1fr;
    }

    #attack-list {
        width: 1fr;
        min-width: 36;
        border-right: solid $primary-background;
    }

    #attack-preview {
        width: 2fr;
        padding: 1 2;
    }

    #result-summary {
        height: 1;
        background: $primary-background-darken-1;
        padding: 0 1;
    }

    #help-bar {
        height: 1;
        dock: bottom;
        background: $primary-background;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Banner(id="banner")
        with Horizontal(id="main-content"):
            yield PhaseList(id="attack-list")
            yield AttackPreview(id="attack-preview")
        yield ResultSummaryWidget(
            tracker=getattr(self.app, "result_tracker", None),  # type: ignore[arg-type]
            id="result-summary",
        )
        yield Static(
            "  [bold]↑↓[/] Navigate  [bold]Enter[/] Run  "
            "[bold]r[/] Refresh  [bold]q[/] Quit  [bold]?[/] Help",
            id="help-bar",
        )

    def on_screen_resume(self) -> None:
        """Refresh result summary when returning from execution screen."""
        summary = self.query("ResultSummaryWidget")
        if summary:
            summary.first().refresh_summary()

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        if event.option.id:
            attack = ATTACKS_BY_ID.get(event.option.id)
            preview = self.query_one("#attack-preview", AttackPreview)
            preview.update_attack(attack)

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        if event.option.id:
            attack = ATTACKS_BY_ID.get(event.option.id)
            if attack:
                from smith.config import PodInfo
                from smith.screens.target_picker import TargetPicker

                def on_target_selected(target: PodInfo | None) -> None:
                    if target is not None:
                        from smith.screens.execution import ExecutionScreen
                        self.app.push_screen(ExecutionScreen(attack, target=target))

                self.app.push_screen(TargetPicker(), callback=on_target_selected)

    def action_request_quit(self) -> None:
        self.app.exit()

    def action_help(self) -> None:
        self.notify(
            "↑↓ to navigate • Enter to run attack • "
            "r to refresh status • q to quit",
            title="Keyboard Shortcuts",
            timeout=5,
        )

    def action_refresh_status(self) -> None:
        self.notify("Refreshing status...", timeout=2)
