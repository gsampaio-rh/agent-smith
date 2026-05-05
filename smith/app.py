"""Textual TUI application root."""

from __future__ import annotations

from textual.app import App

from smith.config import SmithConfig, check_bind_shell, resolve_agent_ip
from smith.screens.main_menu import MainMenuScreen
from smith.widgets.result_tracker import ResultTracker
from smith.widgets.status_bar import StatusBar


class SmithApp(App):
    """Agent Smith TUI — interactive red-team toolkit."""

    TITLE = "Agent Smith"
    SUB_TITLE = "Red Team Toolkit"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary-background;
        color: $text;
        padding: 0 1;
    }
    """

    SCREENS = {
        "main": MainMenuScreen,
    }

    def __init__(self, guided: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.result_tracker = ResultTracker()
        self._guided = guided

    def compose(self):  # type: ignore[override]
        yield StatusBar()

    def on_mount(self) -> None:
        if self._guided:
            from smith.screens.guided import GuidedScreen
            self.push_screen(GuidedScreen())
        else:
            self.push_screen("main")
        self._refresh_status()
        self.set_interval(10.0, self._refresh_status)

    def action_quit(self) -> None:
        self.exit()

    def _refresh_status(self) -> None:
        cfg = SmithConfig.from_env()
        bar = self.query_one(StatusBar)
        bar.namespace = cfg.agent_ns
        bar.local_dev = cfg.local_dev

        if cfg.local_dev:
            bar.agent_ip = "localhost"
            bar.shell_open = False
            # In dev mode, enable all attacks for UI testing
            phase_list = self.screen.query("PhaseList")
            if phase_list:
                phase_list.first().set_bind_shell(True)
            return

        agent_ip = resolve_agent_ip(cfg)
        bar.agent_ip = agent_ip or "unknown"

        if agent_ip:
            bar.shell_open = check_bind_shell(agent_ip, cfg.bind_port)
        else:
            bar.shell_open = False

        phase_list = self.screen.query("PhaseList")
        if phase_list:
            phase_list.first().set_bind_shell(bar.shell_open)
