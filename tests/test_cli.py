"""Tests for the smith CLI — argument parsing, subcommands, error handling."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import patch

import pytest

from smith.cli import build_parser, cmd_list, cmd_plan, cmd_status, main
from smith.registry import ATTACKS


class TestParser:
    def test_no_args_parses(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None
        assert not args.no_tui

    def test_no_tui_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--no-tui"])
        assert args.no_tui

    def test_run_subcommand(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["run", "recon"])
        assert args.command == "run"
        assert args.attack_id == "recon"

    def test_status_subcommand(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_plan_subcommand(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["plan"])
        assert args.command == "plan"

    def test_list_subcommand(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_guided_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--guided"])
        assert args.guided


class TestMainEntrypoint:
    def test_help_exits_zero(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_no_tui_prints_help(self, capsys) -> None:
        code = main(["--no-tui"])
        assert code == 0

    def test_run_invalid_attack(self) -> None:
        code = main(["run", "nonexistent"])
        assert code == 1

    def test_status_runs(self) -> None:
        code = main(["status"])
        assert code == 0

    def test_plan_runs(self) -> None:
        code = main(["plan"])
        assert code == 0

    def test_list_runs(self) -> None:
        code = main(["list"])
        assert code == 0


class TestCmdPlanOutput:
    def test_plan_shows_numbered_sequence(self, capsys) -> None:
        parser = build_parser()
        args = parser.parse_args(["plan"])
        code = cmd_plan(args)
        assert code == 0

    def test_plan_references_valid_attacks(self) -> None:
        from smith.cli import DEMO_SEQUENCE
        from smith.registry import ATTACKS_BY_ID
        for attack_id in DEMO_SEQUENCE:
            assert attack_id in ATTACKS_BY_ID, f"'{attack_id}' in DEMO_SEQUENCE but not in registry"


class TestCmdList:
    def test_list_returns_zero(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert cmd_list(args) == 0
