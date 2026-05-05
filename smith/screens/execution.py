"""Execution screen — live output pane with progress spinner."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import LoadingIndicator, RichLog, Static

from smith.registry import Attack
from smith.runner import ScriptRunner
from smith.widgets.result_tracker import AttackResult, AttackStatus


class ExecutionScreen(Screen):
    """Stream script output in real time with visual progress feedback."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("q", "force_quit", "Quit"),
    ]

    CSS = """
    ExecutionScreen {
        layout: vertical;
    }

    #exec-header {
        height: 3;
        padding: 0 2;
        background: $primary-background;
    }

    #exec-spinner {
        height: 1;
        padding: 0 2;
    }

    #exec-output {
        height: 1fr;
        border: solid $primary-background;
        padding: 0 1;
    }

    #exec-footer {
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
        self._running = False
        self._exit_code: int | None = None

    def compose(self) -> ComposeResult:
        a = self._attack
        yield Static(
            f"\n[bold {a.phase.color}]Running:[/] {a.name}  "
            f"[dim]({a.script})[/dim]",
            id="exec-header",
        )
        yield LoadingIndicator(id="exec-spinner")
        yield RichLog(highlight=True, markup=True, id="exec-output")
        yield Static(
            "  [bold]Esc[/] Back (after completion)  [bold]q[/] Quit",
            id="exec-footer",
        )

    def on_mount(self) -> None:
        self._running = True
        self.run_worker(self._execute(), exclusive=True)

    async def _execute(self) -> None:
        log = self.query_one("#exec-output", RichLog)
        footer = self.query_one("#exec-footer", Static)
        spinner = self.query_one("#exec-spinner", LoadingIndicator)
        runner = ScriptRunner()

        log.write(f"[dim]$ {self._attack.script}[/dim]\n")

        proc = await asyncio.create_subprocess_exec(
            "bash", runner._script_path(self._attack),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        assert proc.stdout is not None
        async for line in proc.stdout:
            log.write(line.decode(errors="replace").rstrip())

        exit_code = await proc.wait()
        self._exit_code = exit_code
        self._running = False
        spinner.display = False

        if exit_code == 0:
            log.write("\n[green bold]✓ Completed successfully[/]")
            status = AttackStatus.SUCCESS
        else:
            log.write(f"\n[red bold]✗ Exited with code {exit_code}[/]")
            status = AttackStatus.FAILURE

        self._record_result(status, exit_code)

        footer.update(
            "  [bold]Esc[/] Back  [bold]q[/] Quit  │  "
            f"Exit: {'[green]0[/]' if exit_code == 0 else f'[red]{exit_code}[/]'}"
        )

    def _record_result(self, status: AttackStatus, exit_code: int) -> None:
        tracker = getattr(self.app, "result_tracker", None)
        if tracker:
            tracker.record(AttackResult(
                attack_id=self._attack.id,
                attack_name=self._attack.name,
                status=status,
                exit_code=exit_code,
            ))

    def action_go_back(self) -> None:
        if not self._running:
            self.app.pop_screen()

    def action_force_quit(self) -> None:
        self.app.exit()
