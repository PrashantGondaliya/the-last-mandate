"""Information report model for uncertain narrative intelligence."""

from dataclasses import dataclass


TRUTH_STATUSES = {
    "accurate",
    "incomplete",
    "exaggerated",
    "misleading",
    "false",
}


@dataclass(frozen=True)
class InformationReport:
    """Represent one hidden-truth report attached to an event."""

    id: str
    source_event_id: str
    source_event_title: str
    source_character_id: str
    statement: str
    reliability: int
    truth: str
    reveal_after_turns: int
    revelation_title: str
    revelation_text: str