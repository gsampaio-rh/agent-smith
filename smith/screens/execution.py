"""Execution screen — three-phase attack experience: Briefing → Live → Results."""

from __future__ import annotations

import asyncio
from enum import Enum

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import LoadingIndicator, RichLog, Static

from smith.config import PodInfo
from smith.output_parser import (
    FindingEvent,
    LootEvent,
    PhaseEvent,
    ResultEvent,
    TargetEvent,
    parse_line,
)
from smith.registry import Attack
from smith.runner import ScriptRunner
from smith.widgets.briefing_panel import BriefingPanel
from smith.widgets.finding_card import FindingStream
from smith.widgets.loot_panel import LootPanel
from smith.widgets.phase_progress import PhaseProgress
from smith.widgets.result_tracker import AttackResult, AttackStatus


class ScreenPhase(Enum):
    BRIEFING = "briefing"
    LIVE = "live"
    RESULTS = "results"


class ExecutionScreen(Screen):
    """Stream script output with pre-attack briefing and post-attack results."""

    BINDINGS = [
        ("enter", "proceed", "Proceed"),
        ("escape", "go_back", "Back"),
        ("q", "force_quit", "Quit"),
    ]

    CSS = """
    ExecutionScreen {
        layout: vertical;
    }

    #briefing-container {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }

    #live-container {
        height: 1fr;
    }

    #live-sidebar {
        width: 32;
        border-right: solid $primary-background;
        padding: 1;
        overflow-y: auto;
    }

    #phase-tracker {
        height: auto;
        min-height: 4;
    }

    #finding-stream {
        height: 1fr;
        border-top: solid $primary-background;
        margin-top: 1;
    }

    #exec-output {
        width: 1fr;
        padding: 0 1;
    }

    #exec-spinner {
        height: 1;
        padding: 0 2;
    }

    #results-container {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }

    #exec-footer {
        height: 1;
        dock: bottom;
        background: $primary-background;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, attack: Attack, target: PodInfo | None = None) -> None:
        super().__init__()
        self._attack = attack
        self._target = target
        self._screen_phase = ScreenPhase.BRIEFING
        self._running = False
        self._exit_code: int | None = None
        self._findings: list[FindingEvent] = []
        self._loot: list[LootEvent] = []
        self._result: ResultEvent | None = None

    def compose(self) -> ComposeResult:
        # Briefing phase
        yield Vertical(
            BriefingPanel(self._attack, self._target),
            id="briefing-container",
        )

        # Live execution phase (hidden initially)
        with Horizontal(id="live-container"):
            with Vertical(id="live-sidebar"):
                yield PhaseProgress(id="phase-tracker")
                yield FindingStream(id="finding-stream")
            yield RichLog(highlight=True, markup=True, id="exec-output")

        yield LoadingIndicator(id="exec-spinner")

        # Results phase (hidden initially)
        yield Vertical(
            LootPanel(id="loot-panel"),
            id="results-container",
        )

        yield Static(
            "  [bold]Enter[/] Begin Attack  [bold]Esc[/] Cancel  [bold]q[/] Quit",
            id="exec-footer",
        )

    def on_mount(self) -> None:
        self._show_phase(ScreenPhase.BRIEFING)

    def _show_phase(self, phase: ScreenPhase) -> None:
        self._screen_phase = phase

        briefing = self.query_one("#briefing-container")
        live = self.query_one("#live-container")
        spinner = self.query_one("#exec-spinner", LoadingIndicator)
        results = self.query_one("#results-container")
        footer = self.query_one("#exec-footer", Static)

        briefing.display = phase == ScreenPhase.BRIEFING
        live.display = phase == ScreenPhase.LIVE
        spinner.display = phase == ScreenPhase.LIVE
        results.display = phase == ScreenPhase.RESULTS

        if phase == ScreenPhase.BRIEFING:
            footer.update(
                "  [bold]Enter[/] Begin Attack  [bold]Esc[/] Cancel  [bold]q[/] Quit"
            )
        elif phase == ScreenPhase.LIVE:
            footer.update(
                "  [bold]q[/] Quit  │  Attack running..."
            )
        elif phase == ScreenPhase.RESULTS:
            ec = self._exit_code or 0
            ec_text = f"[green]0[/]" if ec == 0 else f"[red]{ec}[/]"
            footer.update(
                f"  [bold]Esc[/] Back  [bold]q[/] Quit  │  Exit: {ec_text}"
            )

    def action_proceed(self) -> None:
        if self._screen_phase == ScreenPhase.BRIEFING:
            self._start_execution()
        elif self._screen_phase == ScreenPhase.RESULTS:
            self.app.pop_screen()

    def action_go_back(self) -> None:
        if self._screen_phase == ScreenPhase.BRIEFING:
            self.app.pop_screen()
        elif self._screen_phase == ScreenPhase.RESULTS:
            self.app.pop_screen()

    def action_force_quit(self) -> None:
        self.app.exit()

    def _start_execution(self) -> None:
        self._show_phase(ScreenPhase.LIVE)
        self._running = True
        self.run_worker(self._execute(), exclusive=True)

    async def _execute(self) -> None:
        log = self.query_one("#exec-output", RichLog)
        phase_tracker = self.query_one("#phase-tracker", PhaseProgress)
        finding_stream = self.query_one("#finding-stream", FindingStream)

        runner = ScriptRunner()
        env_overrides: dict[str, str] = {}
        if self._target:
            env_overrides["AGENT_POD_IP"] = self._target.ip

        log.write(f"[dim]$ {self._attack.script}[/dim]")
        if self._target:
            log.write(f"[dim]  target: {self._target.name} ({self._target.ip})[/dim]")
        log.write("")

        env = {**__import__("os").environ, **env_overrides}
        proc = await asyncio.create_subprocess_exec(
            "bash", runner._script_path(self._attack),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )

        assert proc.stdout is not None
        async for raw_line in proc.stdout:
            line = raw_line.decode(errors="replace").rstrip()
            event = parse_line(line)

            if event is None:
                log.write(line)
                continue

            if isinstance(event, PhaseEvent):
                phase_tracker.set_phase(event.name)
            elif isinstance(event, TargetEvent):
                log.write(f"[cyan]⎯ Target: {event.ip} {event.pod_name}[/cyan]")
            elif isinstance(event, FindingEvent):
                self._findings.append(event)
                finding_stream.add_finding(event)
            elif isinstance(event, LootEvent):
                self._loot.append(event)
            elif isinstance(event, ResultEvent):
                self._result = event

        exit_code = await proc.wait()
        self._exit_code = exit_code
        self._running = False

        spinner = self.query_one("#exec-spinner", LoadingIndicator)
        spinner.display = False

        phase_tracker.mark_all_done()

        if exit_code == 0:
            status = AttackStatus.SUCCESS
        else:
            status = AttackStatus.FAILURE

        self._record_result(status, exit_code)
        self._show_results(exit_code)

    def _show_results(self, exit_code: int) -> None:
        loot_panel = self.query_one("#loot-panel", LootPanel)
        loot_panel.set_data(
            loot=self._loot,
            findings=self._findings,
            result=self._result,
            exit_code=exit_code,
        )
        self._show_phase(ScreenPhase.RESULTS)

    def _record_result(self, status: AttackStatus, exit_code: int) -> None:
        tracker = getattr(self.app, "result_tracker", None)
        if tracker:
            tracker.record(AttackResult(
                attack_id=self._attack.id,
                attack_name=self._attack.name,
                status=status,
                exit_code=exit_code,
            ))
