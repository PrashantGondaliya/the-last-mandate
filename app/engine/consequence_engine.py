"""Delayed consequence processing for The Last Mandate."""

from app.models.game_state import GameState
from app.models.scheduled_consequence import (
    ScheduledConsequence,
)


def schedule_choice_consequences(
    state: GameState,
    event: dict,
    choice: dict,
) -> list[ScheduledConsequence]:
    """Schedule every delayed consequence created by a choice."""
    consequence_data_list = choice.get(
        "delayed_consequences",
        [],
    )

    scheduled: list[ScheduledConsequence] = []

    for consequence_data in consequence_data_list:
        consequence_id = (
            f"{event['id']}:"
            f"{choice['id']}:"
            f"{consequence_data['id']}"
        )

        if consequence_id in state.resolved_consequence_ids:
            raise ValueError(
                f"Consequence '{consequence_id}' "
                f"has already been resolved."
            )

        if any(
            existing.id == consequence_id
            for existing in state.scheduled_consequences
        ):
            raise ValueError(
                f"Consequence '{consequence_id}' "
                f"has already been scheduled."
            )

        consequence = ScheduledConsequence(
            id=consequence_id,
            source_event_id=event["id"],
            source_choice_id=choice["id"],
            due_turn=(
                state.current_turn
                + consequence_data["delay_turns"]
            ),
            title=consequence_data["title"],
            description=consequence_data["description"],
            effects=dict(consequence_data["effects"]),
        )

        state.scheduled_consequences.append(
            consequence
        )
        scheduled.append(consequence)

    return scheduled


def get_due_consequences(
    state: GameState,
) -> list[ScheduledConsequence]:
    """Return consequences due on or before the current turn."""
    due_consequences = [
        consequence
        for consequence in state.scheduled_consequences
        if consequence.due_turn <= state.current_turn
    ]

    return sorted(
        due_consequences,
        key=lambda consequence: (
            consequence.due_turn,
            consequence.id,
        ),
    )


def resolve_due_consequences(
    state: GameState,
) -> list[
    tuple[
        ScheduledConsequence,
        dict[str, tuple[int, int]],
    ]
]:
    """Apply and remove all consequences currently due."""
    due_consequences = get_due_consequences(state)

    if not due_consequences:
        return []

    due_ids = {
        consequence.id
        for consequence in due_consequences
    }

    state.scheduled_consequences = [
        consequence
        for consequence in state.scheduled_consequences
        if consequence.id not in due_ids
    ]

    resolved_results: list[
        tuple[
            ScheduledConsequence,
            dict[str, tuple[int, int]],
        ]
    ] = []

    for consequence in due_consequences:
        if consequence.id in state.resolved_consequence_ids:
            continue

        stat_changes = state.apply_effects(
            consequence.effects
        )

        state.resolved_consequence_ids.add(
            consequence.id
        )

        resolved_results.append(
            (
                consequence,
                stat_changes,
            )
        )

    return resolved_results


def get_next_scheduled_turn(
    state: GameState,
) -> int | None:
    """Return the next turn containing a consequence."""
    future_turns = [
        consequence.due_turn
        for consequence in state.scheduled_consequences
        if consequence.due_turn > state.current_turn
    ]

    if not future_turns:
        return None

    return min(future_turns)