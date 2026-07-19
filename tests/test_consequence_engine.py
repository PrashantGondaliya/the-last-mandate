"""Tests for scheduled and delayed consequences."""

from app.engine.consequence_engine import (
    get_next_scheduled_turn,
    resolve_due_consequences,
    schedule_choice_consequences,
)
from app.models.game_state import GameState


def build_delayed_choice() -> dict:
    """Create a choice with one delayed consequence."""
    return {
        "id": "delay_choice",
        "text": "Create a future problem.",
        "outcome": "The immediate situation appears stable.",
        "effects": {},
        "delayed_consequences": [
            {
                "id": "future_unrest",
                "delay_turns": 2,
                "title": "FUTURE UNREST",
                "description": "The decision causes unrest later.",
                "effects": {
                    "unrest": 10,
                    "public_trust": -5,
                },
            }
        ],
    }


def test_choice_schedules_future_consequence(
    fresh_state: GameState,
) -> None:
    """A delayed consequence should receive the correct due turn."""
    fresh_state.current_turn = 3

    event = {
        "id": "source_event",
    }
    choice = build_delayed_choice()

    scheduled = schedule_choice_consequences(
        state=fresh_state,
        event=event,
        choice=choice,
    )

    assert len(scheduled) == 1
    assert scheduled[0].due_turn == 5
    assert len(
        fresh_state.scheduled_consequences
    ) == 1
    assert get_next_scheduled_turn(fresh_state) == 5


def test_consequence_does_not_resolve_early(
    fresh_state: GameState,
) -> None:
    """A consequence should remain pending before its due turn."""
    fresh_state.current_turn = 3

    schedule_choice_consequences(
        state=fresh_state,
        event={"id": "source_event"},
        choice=build_delayed_choice(),
    )

    fresh_state.current_turn = 4

    resolved = resolve_due_consequences(
        fresh_state
    )

    assert resolved == []
    assert fresh_state.unrest == 25
    assert len(
        fresh_state.scheduled_consequences
    ) == 1


def test_due_consequence_updates_state(
    fresh_state: GameState,
) -> None:
    """A due consequence should apply and then be removed."""
    fresh_state.current_turn = 3

    scheduled = schedule_choice_consequences(
        state=fresh_state,
        event={"id": "source_event"},
        choice=build_delayed_choice(),
    )

    consequence_id = scheduled[0].id

    fresh_state.current_turn = 5

    resolved = resolve_due_consequences(
        fresh_state
    )

    assert len(resolved) == 1
    assert fresh_state.unrest == 35
    assert fresh_state.public_trust == 45
    assert fresh_state.scheduled_consequences == []
    assert consequence_id in (
        fresh_state.resolved_consequence_ids
    )