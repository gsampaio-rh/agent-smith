"""Tests for the structured output parser."""

from __future__ import annotations

import pytest

from smith.output_parser import (
    FindingEvent,
    FindingSeverity,
    LootEvent,
    PhaseEvent,
    ResultEvent,
    TargetEvent,
    parse_line,
    parse_output,
)


class TestParseLine:
    def test_plain_text_returns_none(self) -> None:
        assert parse_line("just a normal line") is None
        assert parse_line("") is None
        assert parse_line("  indented text") is None

    def test_phase_event(self) -> None:
        event = parse_line("@PHASE Reconnaissance")
        assert isinstance(event, PhaseEvent)
        assert event.name == "Reconnaissance"

    def test_phase_event_with_hyphens(self) -> None:
        event = parse_line("@PHASE DNS-Service-Discovery")
        assert isinstance(event, PhaseEvent)
        assert event.name == "DNS-Service-Discovery"

    def test_target_event(self) -> None:
        event = parse_line("@TARGET 10.0.0.42 neo-agent")
        assert isinstance(event, TargetEvent)
        assert event.ip == "10.0.0.42"
        assert event.pod_name == "neo-agent"

    def test_target_event_ip_only(self) -> None:
        event = parse_line("@TARGET 10.0.0.42")
        assert isinstance(event, TargetEvent)
        assert event.ip == "10.0.0.42"
        assert event.pod_name == ""

    def test_finding_info(self) -> None:
        event = parse_line("@FINDING info 3 RBAC rules discovered")
        assert isinstance(event, FindingEvent)
        assert event.severity == FindingSeverity.INFO
        assert event.message == "3 RBAC rules discovered"

    def test_finding_critical(self) -> None:
        event = parse_line("@FINDING critical CLAUDE.md override injected")
        assert isinstance(event, FindingEvent)
        assert event.severity == FindingSeverity.CRITICAL
        assert event.message == "CLAUDE.md override injected"

    def test_finding_unknown_severity_treated_as_full_message(self) -> None:
        event = parse_line("@FINDING Some message without severity")
        assert isinstance(event, FindingEvent)
        assert event.severity == FindingSeverity.INFO
        assert "Some message without severity" in event.message

    def test_loot_event(self) -> None:
        event = parse_line("@LOOT secrets target-apps/db-password")
        assert isinstance(event, LootEvent)
        assert event.loot_type == "secrets"
        assert event.data == "target-apps/db-password"

    def test_loot_event_no_data(self) -> None:
        event = parse_line("@LOOT shell-access")
        assert isinstance(event, LootEvent)
        assert event.loot_type == "shell-access"
        assert event.data == ""

    def test_result_success(self) -> None:
        event = parse_line("@RESULT success Recon complete")
        assert isinstance(event, ResultEvent)
        assert event.status == "success"
        assert event.summary == "Recon complete"

    def test_result_failure(self) -> None:
        event = parse_line("@RESULT failure Bind shell not detected")
        assert isinstance(event, ResultEvent)
        assert event.status == "failure"
        assert event.summary == "Bind shell not detected"

    def test_whitespace_handling(self) -> None:
        event = parse_line("  @PHASE  Recon  ")
        assert isinstance(event, PhaseEvent)
        assert event.name == "Recon"

    def test_marker_must_be_at_line_start(self) -> None:
        assert parse_line("echo @PHASE something") is None


class TestParseOutput:
    def test_empty_output(self) -> None:
        assert parse_output("") == []

    def test_mixed_output(self) -> None:
        text = (
            "Some banner text\n"
            "@PHASE Recon\n"
            "  Running recon...\n"
            "@FINDING high 5 secrets found\n"
            "@LOOT secrets db-password\n"
            "More output\n"
            "@RESULT success Done\n"
        )
        events = parse_output(text)
        assert len(events) == 4
        assert isinstance(events[0], PhaseEvent)
        assert isinstance(events[1], FindingEvent)
        assert isinstance(events[2], LootEvent)
        assert isinstance(events[3], ResultEvent)

    def test_multiple_phases(self) -> None:
        text = "@PHASE A\n@PHASE B\n@PHASE C\n"
        events = parse_output(text)
        assert len(events) == 3
        assert [e.name for e in events] == ["A", "B", "C"]
