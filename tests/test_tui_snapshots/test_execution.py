"""Snapshot tests for the execution screen."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from smith.app import SmithApp
from smith.config import PodInfo
from smith.registry import get_attack
from smith.screens.execution import ExecutionScreen, ScreenPhase


@pytest.fixture(autouse=True)
def mock_k8s():
    with (
        patch("smith.app.resolve_agent_ip", return_value=None),
        patch("smith.app.check_bind_shell", return_value=False),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_subprocess():
    """Mock asyncio.create_subprocess_exec to avoid running real scripts."""
    import asyncio

    class FakeStreamReader:
        async def __aiter__(self):
            yield b"@PHASE Recon\n"
            yield b"mock output line\n"
            yield b"@FINDING info Test finding message\n"
            yield b"@LOOT secrets test-secret/key\n"
            yield b"@RESULT success Test complete\n"

    class FakeProcess:
        stdout = FakeStreamReader()
        async def wait(self):
            return 0

    async def fake_create_subprocess_exec(*args, **kwargs):
        return FakeProcess()

    with patch(
        "smith.screens.execution.asyncio.create_subprocess_exec",
        side_effect=fake_create_subprocess_exec,
    ):
        yield


@pytest.fixture()
def mock_target() -> PodInfo:
    return PodInfo(
        name="neo-test-pod",
        ip="10.0.0.42",
        status="Running",
        namespace="agent-namespace",
        shell_open=True,
    )


class TestExecution:
    async def test_execution_screen_starts_in_briefing(self, mock_target) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            screen = ExecutionScreen(attack, target=mock_target)
            app.push_screen(screen)
            await pilot.pause()
            assert screen._screen_phase == ScreenPhase.BRIEFING

    async def test_briefing_shows_attack_name(self, mock_target) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            app.push_screen(ExecutionScreen(attack, target=mock_target))
            await pilot.pause()
            assert app.screen.__class__.__name__ == "ExecutionScreen"

    async def test_enter_starts_execution(self, mock_target) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            screen = ExecutionScreen(attack, target=mock_target)
            app.push_screen(screen)
            await pilot.pause()
            assert screen._screen_phase == ScreenPhase.BRIEFING
            await pilot.press("enter")
            await pilot.pause(delay=0.5)

    async def test_escape_from_briefing_pops_screen(self, mock_target) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            screen = ExecutionScreen(attack, target=mock_target)
            app.push_screen(screen)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert app.screen.__class__.__name__ != "ExecutionScreen"

    async def test_execution_without_target(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("trigger")
            screen = ExecutionScreen(attack)
            app.push_screen(screen)
            await pilot.pause()
            assert screen._screen_phase == ScreenPhase.BRIEFING
