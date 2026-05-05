"""Snapshot tests for the main menu screen."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from smith.app import SmithApp


@pytest.fixture(autouse=True)
def mock_k8s():
    """Prevent real k8s/network calls during TUI tests."""
    with (
        patch("smith.app.resolve_agent_ip", return_value=None),
        patch("smith.app.check_bind_shell", return_value=False),
    ):
        yield


class TestMainMenu:
    async def test_app_launches(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert app.title == "Agent Smith"

    async def test_main_menu_renders_phase_categories(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            from smith.widgets.phase_list import PhaseList
            phase_list = app.screen.query_one(PhaseList)
            assert phase_list is not None
            assert phase_list.option_count > 0

    async def test_all_attacks_visible(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            from smith.registry import ATTACKS
            from smith.widgets.phase_list import PhaseList
            phase_list = app.screen.query_one(PhaseList)
            option_ids = [
                opt.id for opt in phase_list._options
                if opt.id is not None
            ]
            for attack in ATTACKS:
                assert attack.id in option_ids, f"Attack '{attack.id}' not in option list"

    async def test_down_arrow_moves_selection(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            from smith.widgets.phase_list import PhaseList
            phase_list = app.screen.query_one(PhaseList)
            phase_list.focus()
            await pilot.press("down")
            await pilot.pause()

    async def test_q_triggers_quit(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("q")

    async def test_question_mark_shows_help(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("question_mark")

    async def test_preview_panel_exists(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            from smith.screens.main_menu import AttackPreview
            preview = app.screen.query_one(AttackPreview)
            assert preview is not None
