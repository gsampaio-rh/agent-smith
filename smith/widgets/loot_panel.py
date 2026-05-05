"""Post-attack loot summary panel."""

from __future__ import annotations

from textual.widgets import Static

from smith.output_parser import FindingEvent, LootEvent, ResultEvent

_LOOT_ICONS: dict[str, str] = {
    "secrets": "🔑",
    "tokens": "🎟",
    "credentials": "🔐",
    "configmaps": "📋",
    "rbac-rules": "📜",
    "service-map": "🗺",
    "env-vars": "📦",
    "cloud-metadata": "☁",
    "shell-access": "🐚",
    "agent-control": "🤖",
    "db-access": "🗄",
    "pod-list": "📡",
    "worm-results": "🐛",
    "persistence-config": "⚓",
    "exfil-proof": "📤",
}


class LootPanel(Static):
    """Renders a summary of stolen artifacts after attack completion."""

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._loot: list[LootEvent] = []
        self._findings: list[FindingEvent] = []
        self._result: ResultEvent | None = None

    def set_data(
        self,
        loot: list[LootEvent],
        findings: list[FindingEvent],
        result: ResultEvent | None,
        exit_code: int,
    ) -> None:
        self._loot = loot
        self._findings = findings
        self._result = result
        self._build_display(exit_code)

    def _build_display(self, exit_code: int) -> None:
        lines: list[str] = []

        # Result header
        if self._result:
            if self._result.status == "success":
                lines.append(f"[green bold]✓ {self._result.summary}[/]")
            else:
                lines.append(f"[red bold]✗ {self._result.summary}[/]")
        elif exit_code == 0:
            lines.append("[green bold]✓ Attack completed successfully[/]")
        else:
            lines.append(f"[red bold]✗ Exited with code {exit_code}[/]")

        lines.append("")

        # Loot section
        if self._loot:
            lines.append("[bold]Loot Collected:[/bold]")
            lines.append(f"[dim]{'─' * 40}[/dim]")

            grouped: dict[str, list[str]] = {}
            for item in self._loot:
                grouped.setdefault(item.loot_type, []).append(item.data)

            for loot_type, items in grouped.items():
                icon = _LOOT_ICONS.get(loot_type, "•")
                lines.append(f"  {icon} [bold]{loot_type}[/bold] ({len(items)} item{'s' if len(items) != 1 else ''})")
                for data in items[:5]:
                    lines.append(f"      {data}")
                if len(items) > 5:
                    lines.append(f"      ... and {len(items) - 5} more")
            lines.append("")

        # Findings summary
        if self._findings:
            from collections import Counter

            counts = Counter(f.severity.value for f in self._findings)
            parts = []
            for sev in ["critical", "high", "medium", "low", "info"]:
                if counts.get(sev, 0):
                    parts.append(f"{sev}: {counts[sev]}")
            lines.append(f"[bold]Findings:[/bold]  {' │ '.join(parts)}")
            lines.append("")

        if not self._loot and not self._findings:
            lines.append("[dim]No loot or findings recorded.[/dim]")
            lines.append("")

        self.update("\n".join(lines))
