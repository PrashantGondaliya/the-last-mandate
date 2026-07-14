"""Decision history model for The Last Mandate."""

from dataclasses import dataclass


@dataclass
class DecisionRecord:
    """Store one decision made by the player."""

    turn_number: int
    event_id: str
    event_title: str
    choice_id: str
    choice_text: str
    effects: dict[str, int]
    stat_changes: dict[str, tuple[int, int]]