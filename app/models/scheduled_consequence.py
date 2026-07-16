"""Scheduled consequence model for The Last Mandate."""

from dataclasses import dataclass


@dataclass
class ScheduledConsequence:
    """Store one consequence waiting to happen."""

    id: str
    source_event_id: str
    source_choice_id: str
    due_turn: int
    title: str
    description: str
    effects: dict[str, int]