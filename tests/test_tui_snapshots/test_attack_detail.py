"""Snapshot tests for the attack detail screen."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from smith.app import SmithApp
from smith.registry import get_attack
from smith.screens.attack_detail import AttackDetailScreen


@pytest.fixture(autouse=True)
def mock_k8s():
    with (
        patch("smith.app.resolve_agent_ip", return_value=None),
        patch("smith.app.check_bind_shell", return_value=False),
    ):
        yield


class TestAttackDetail:
    async def test_detail_screen_renders(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            app.push_screen(AttackDetailScreen(attack))
            await pilot.pause()
            assert app.screen.__class__.__name__ == "AttackDetailScreen"

    async def test_detail_shows_attack_info(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            app.push_screen(AttackDetailScreen(attack))
            await pilot.pause()

    async def test_escape_returns_to_previous(self) -> None:
        app = SmithApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            attack = get_attack("recon")
            app.push_screen(AttackDetailScreen(attack))
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "MainMenuScreen"
