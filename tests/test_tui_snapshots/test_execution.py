"""Snapshot tests for the execution screen."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from smith.app import SmithApp
from smith.registry import get_attack
from smith.screens.execution import ExecutionScreen


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

    async def fake_read():
        return b""

    class FakeStreamReader:
        async def __aiter__(self):
            yield b"mock output line\n"

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


class TestExecution:
    async def test_execution_screen_renders(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            app.push_screen(ExecutionScreen(attack))
            await pilot.pause()
            assert app.screen.__class__.__name__ == "ExecutionScreen"

    async def test_execution_shows_header(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            app.push_screen(ExecutionScreen(attack))
            await pilot.pause()

    async def test_escape_blocked_while_running(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            screen = ExecutionScreen(attack)
            app.push_screen(screen)
            # Give the screen time to mount and start the worker
            await pilot.pause(delay=0.5)
            # Force running state to simulate long-running script
            screen._running = True
            await pilot.press("escape")
            await pilot.pause(delay=0.2)
            # Should still be on execution screen since script is "running"
            assert app.screen.__class__.__name__ == "ExecutionScreen"
