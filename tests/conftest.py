"""Shared fixtures for smith tests."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from smith.config import SmithConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "attacks"


@pytest.fixture()
def default_config() -> SmithConfig:
    return SmithConfig(
        agent_ns="agent-namespace",
        bind_port=4444,
        neo_ui_svc="neo-ui.agent-namespace.svc:3458",
        attacker_ns="attacker",
        scripts_dir=str(SCRIPTS_DIR),
        local_dev=True,
    )


@pytest.fixture()
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove smith-related env vars for a clean test."""
    for key in ("AGENT_NS", "BIND_PORT", "NEO_UI_SVC", "ATTACKER_NS"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def scripts_dir() -> Path:
    """Path to the real scripts/attacks/ directory."""
    return SCRIPTS_DIR
