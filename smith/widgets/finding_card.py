"""Finding card widget — renders @FINDING events as colored entries."""

from __future__ import annotations

from textual.widgets import RichLog

from smith.output_parser import FindingEvent, FindingSeverity

_SEVERITY_STYLES: dict[FindingSeverity, tuple[str, str]] = {
    FindingSeverity.INFO: ("blue", "ℹ"),
    FindingSeverity.LOW: ("cyan", "▪"),
    FindingSeverity.MEDIUM: ("yellow", "▲"),
    FindingSeverity.HIGH: ("dark_orange", "◆"),
    FindingSeverity.CRITICAL: ("red bold", "⚠"),
}


class FindingStream(RichLog):
    """Scrolling log of findings discovered during attack execution."""

    def __init__(self, **kwargs) -> None:
        super().__init__(highlight=False, markup=True, **kwargs)
        self._count = 0

    def add_finding(self, finding: FindingEvent) -> None:
        style, icon = _SEVERITY_STYLES.get(
            finding.severity, ("white", "•")
        )
        self._count += 1
        self.write(
            f"[{style}]{icon} [{finding.severity.value.upper()}][/{style}] "
            f"{finding.message}"
        )

    @property
    def count(self) -> int:
        return self._count
