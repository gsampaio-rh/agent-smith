"""Target picker screen — discover and select a Neo agent pod."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import LoadingIndicator, OptionList, Static
from textual.widgets._option_list import Option

from smith.config import PodInfo, SmithConfig, discover_agent_pods


class TargetPicker(Screen[PodInfo | None]):
    """Lists discovered Neo pods and lets the user pick one."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("r", "refresh", "Refresh"),
    ]

    CSS = """
    TargetPicker {
        layout: vertical;
        align: center middle;
    }

    #picker-title {
        height: 3;
        padding: 1 2;
        text-align: center;
    }

    #picker-list {
        height: 1fr;
        min-height: 8;
        margin: 0 4;
        border: solid $primary-background;
    }

    #picker-spinner {
        height: 3;
    }

    #picker-footer {
        height: 1;
        dock: bottom;
        background: $primary-background;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._pods: list[PodInfo] = []

    def compose(self) -> ComposeResult:
        yield Static(
            "\n[bold]Select Target Pod[/bold]",
            id="picker-title",
        )
        yield LoadingIndicator(id="picker-spinner")
        yield OptionList(id="picker-list")
        yield Static(
            "  [bold]Enter[/] Select  [bold]r[/] Refresh  [bold]Esc[/] Cancel",
            id="picker-footer",
        )

    def on_mount(self) -> None:
        self.query_one("#picker-list", OptionList).display = False
        self.run_worker(self._discover(), exclusive=True)

    async def _discover(self) -> None:
        import asyncio

        cfg = SmithConfig.from_env()

        if cfg.local_dev:
            self._pods = [
                PodInfo(
                    name="neo-local-dev",
                    ip="agent" if _is_compose_env() else "127.0.0.1",
                    status="Running",
                    namespace=cfg.agent_ns,
                    shell_open=True,
                ),
            ]
        else:
            self._pods = await asyncio.to_thread(discover_agent_pods, cfg)

        spinner = self.query_one("#picker-spinner", LoadingIndicator)
        spinner.display = False

        option_list = self.query_one("#picker-list", OptionList)
        option_list.display = True

        if not self._pods:
            option_list.add_option(
                Option("[dim]No pods found — press r to retry[/dim]", disabled=True)
            )
            return

        for pod in self._pods:
            shell = "[green]shell open[/green]" if pod.shell_open else "[red]no shell[/red]"
            label = (
                f"  {pod.name}  │  {pod.ip}  │  "
                f"[cyan]{pod.status}[/cyan]  │  {shell}"
            )
            option_list.add_option(Option(label, id=pod.name))

        option_list.focus()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        if event.option.id:
            pod = next((p for p in self._pods if p.name == event.option.id), None)
            self.dismiss(pod)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_refresh(self) -> None:
        option_list = self.query_one("#picker-list", OptionList)
        option_list.clear_options()
        option_list.display = False
        spinner = self.query_one("#picker-spinner", LoadingIndicator)
        spinner.display = True
        self.run_worker(self._discover(), exclusive=True)


def _is_compose_env() -> bool:
    """True when running inside docker/podman compose (agent hostname resolves)."""
    import socket

    try:
        socket.getaddrinfo("agent", None)
        return True
    except socket.gaierror:
        return False
