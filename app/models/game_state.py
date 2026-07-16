"""Game state model for The Last Mandate."""

from dataclasses import dataclass, field

from app.models.decision_record import DecisionRecord
from app.models.scheduled_consequence import ScheduledConsequence


STAT_LABELS = {
    "treasury": "Treasury Reserves",
    "public_trust": "Public Trust",
    "unrest": "Public Unrest",
    "infrastructure": "Infrastructure",
    "authority": "Government Authority",
    "business_confidence": "Business Confidence",
}


@dataclass
class GameState:
    """Store the current condition and history of the city."""

    player_name: str
    current_turn: int = 0

    treasury: int = 65
    public_trust: int = 50
    unrest: int = 25
    infrastructure: int = 45
    authority: int = 50
    business_confidence: int = 50

    completed_event_ids: set[str] = field(
        default_factory=set
    )
    decision_history: list[DecisionRecord] = field(
        default_factory=list
    )
    scheduled_consequences: list[ScheduledConsequence] = field(
        default_factory=list
    )
    resolved_consequence_ids: set[str] = field(
        default_factory=set
    )

    def apply_effects(
        self,
        effects: dict[str, int],
    ) -> dict[str, tuple[int, int]]:
        """
        Apply effects to the city statistics.

        Returns the previous and updated value for every
        statistic affected.
        """
        applied_changes: dict[str, tuple[int, int]] = {}

        for stat_name, amount in effects.items():
            if stat_name not in STAT_LABELS:
                raise ValueError(
                    f"Unknown city statistic: {stat_name}"
                )

            previous_value = getattr(
                self,
                stat_name,
            )

            updated_value = previous_value + amount
            updated_value = max(
                0,
                min(100, updated_value),
            )

            setattr(
                self,
                stat_name,
                updated_value,
            )

            applied_changes[stat_name] = (
                previous_value,
                updated_value,
            )

        return applied_changes

    def record_decision(
        self,
        turn_number: int,
        event: dict,
        choice: dict,
        stat_changes: dict[str, tuple[int, int]],
    ) -> DecisionRecord:
        """Record a completed event and selected choice."""
        event_id = event["id"]

        if self.has_completed_event(event_id):
            raise ValueError(
                f"Event '{event_id}' has already been completed."
            )

        decision_record = DecisionRecord(
            turn_number=turn_number,
            event_id=event_id,
            event_title=event["title"],
            choice_id=choice["id"],
            choice_text=choice["text"],
            effects=dict(choice["effects"]),
            stat_changes=dict(stat_changes),
        )

        self.decision_history.append(decision_record)
        self.completed_event_ids.add(event_id)

        return decision_record

    def has_completed_event(
        self,
        event_id: str,
    ) -> bool:
        """Return whether an event has been completed."""
        return event_id in self.completed_event_ids

    def has_made_choice(
        self,
        event_id: str,
        choice_id: str,
    ) -> bool:
        """Return whether the player made a specific choice."""
        return any(
            record.event_id == event_id
            and record.choice_id == choice_id
            for record in self.decision_history
        )