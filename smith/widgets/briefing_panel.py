"""Pre-attack briefing panel — technique, impact, steps, target info."""

from __future__ import annotations

from textual.widgets import Static

from smith.config import PodInfo
from smith.registry import Attack


class BriefingPanel(Static):
    """Shows attack details and target info before execution starts."""

    def __init__(self, attack: Attack, target: PodInfo | None = None, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._attack = attack
        self._target = target
        self._render_content()

    def _render_content(self) -> None:
        a = self._attack
        t = self._target

        lines = [
            f"[bold {a.phase.color}]{a.name}[/]",
            f"[dim]{'━' * 56}[/dim]",
            "",
            f"[bold]Technique:[/bold]  {a.technique}",
            f"[bold]Phase:[/bold]      [{a.phase.color}]{a.phase.label}[/]",
            f"[bold]Impact:[/bold]     {a.impact}",
            "",
        ]

        if t:
            shell = "[green]open[/green]" if t.shell_open else "[red]closed[/red]"
            lines += [
                "[bold]Target:[/bold]",
                f"  Pod:    {t.name}",
                f"  IP:     {t.ip}",
                f"  Status: [cyan]{t.status}[/cyan]",
                f"  Shell:  {shell}",
                "",
            ]

        lines += ["[bold]Briefing:[/bold]", f"  {a.briefing}", ""]

        if a.steps:
            lines.append("[bold]Attack Steps:[/bold]")
            for i, step in enumerate(a.steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        if a.loot_types:
            loot = ", ".join(a.loot_types)
            lines.append(f"[bold]Expected Loot:[/bold]  {loot}")
            lines.append("")

        lines.append("[dim]Press Enter to begin attack  │  Esc to cancel[/dim]")

        self.update("\n".join(lines))
