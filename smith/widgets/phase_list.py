"""Color-coded attack list grouped by phase."""

from __future__ import annotations

from rich.text import Text
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets._option_list import Option

from smith.registry import Attack, Phase, attacks_by_phase


class AttackSelected(Message):
    """Fired when the user highlights an attack."""

    def __init__(self, attack: Attack) -> None:
        super().__init__()
        self.attack = attack


class PhaseList(OptionList):
    """OptionList populated with attacks grouped by phase."""

    BINDINGS = [
        ("enter", "select", "Select"),
        ("q", "screen.request_quit", "Quit"),
    ]

    def __init__(self, bind_shell_available: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._attacks_map: dict[int, Attack] = {}
        self._bind_shell_available = bind_shell_available

    def on_mount(self) -> None:
        self._populate()

    def _populate(self) -> None:
        self.clear_options()
        self._attacks_map.clear()

        grouped = attacks_by_phase()
        idx = 0

        for phase in Phase:
            group = grouped.get(phase, [])
            if not group:
                continue

            header = Text(f"\n  {phase.label.upper()}", style=f"bold {phase.color}")
            self.add_option(Option(header, disabled=True))

            for attack in group:
                disabled = attack.requires_bind_shell and not self._bind_shell_available
                label = Text()
                label.append("  ")
                if disabled:
                    label.append(f"○ {attack.name}", style="dim")
                    label.append("  (bind shell)", style="dim italic")
                else:
                    label.append(f"● {attack.name}", style=phase.color)

                self.add_option(Option(label, id=attack.id, disabled=disabled))
                self._attacks_map[idx] = attack
                idx += 1

    def set_bind_shell(self, available: bool) -> None:
        self._bind_shell_available = available
        self._populate()

    def get_attack_by_option_id(self, option_id: str) -> Attack | None:
        from smith.registry import ATTACKS_BY_ID
        return ATTACKS_BY_ID.get(option_id)
