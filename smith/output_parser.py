"""Parse structured @MARKER lines from attack script stdout."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class MarkerKind(Enum):
    PHASE = "PHASE"
    TARGET = "TARGET"
    FINDING = "FINDING"
    LOOT = "LOOT"
    RESULT = "RESULT"


class FindingSeverity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PhaseEvent:
    kind: MarkerKind = MarkerKind.PHASE
    name: str = ""


@dataclass
class TargetEvent:
    kind: MarkerKind = MarkerKind.TARGET
    ip: str = ""
    pod_name: str = ""


@dataclass
class FindingEvent:
    kind: MarkerKind = MarkerKind.FINDING
    severity: FindingSeverity = FindingSeverity.INFO
    message: str = ""


@dataclass
class LootEvent:
    kind: MarkerKind = MarkerKind.LOOT
    loot_type: str = ""
    data: str = ""


@dataclass
class ResultEvent:
    kind: MarkerKind = MarkerKind.RESULT
    status: str = ""
    summary: str = ""


ScriptEvent = PhaseEvent | TargetEvent | FindingEvent | LootEvent | ResultEvent

_MARKER_RE = re.compile(r"^@(PHASE|TARGET|FINDING|LOOT|RESULT)\s+(.*)$")

_SEVERITY_MAP = {s.value: s for s in FindingSeverity}


def parse_line(line: str) -> ScriptEvent | None:
    """Parse a single output line. Returns a typed event or None for plain text."""
    stripped = line.strip()
    match = _MARKER_RE.match(stripped)
    if not match:
        return None

    kind_str = match.group(1)
    payload = match.group(2).strip()

    if kind_str == "PHASE":
        return PhaseEvent(name=payload)

    if kind_str == "TARGET":
        parts = payload.split(maxsplit=1)
        return TargetEvent(
            ip=parts[0] if parts else "",
            pod_name=parts[1] if len(parts) > 1 else "",
        )

    if kind_str == "FINDING":
        parts = payload.split(maxsplit=1)
        severity_str = parts[0].lower() if parts else "info"
        severity = _SEVERITY_MAP.get(severity_str, FindingSeverity.INFO)
        message = parts[1] if len(parts) > 1 else payload
        if severity_str not in _SEVERITY_MAP:
            message = payload
        return FindingEvent(severity=severity, message=message)

    if kind_str == "LOOT":
        parts = payload.split(maxsplit=1)
        return LootEvent(
            loot_type=parts[0] if parts else "",
            data=parts[1] if len(parts) > 1 else "",
        )

    if kind_str == "RESULT":
        parts = payload.split(maxsplit=1)
        return ResultEvent(
            status=parts[0] if parts else "",
            summary=parts[1] if len(parts) > 1 else "",
        )

    return None


def parse_output(text: str) -> list[ScriptEvent]:
    """Parse all marker lines from multi-line output, ignoring plain text."""
    events: list[ScriptEvent] = []
    for line in text.splitlines():
        event = parse_line(line)
        if event is not None:
            events.append(event)
    return events
