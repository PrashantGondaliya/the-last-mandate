"""Decision history model for The Last Mandate."""

from dataclasses import dataclass
from dataclasses import dataclass, field

CharacterChanges = dict[
    str,
    dict[str, tuple[int, int]],
]

FactionChanges = dict[
    str,
    dict[str, tuple[int, int]],
]



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
    character_changes: CharacterChanges
    faction_changes: FactionChanges
    information_reports: list[
        dict[str, str]
    ] = field(default_factory=list)