"""Tests for the GameState model."""

import pytest

from app.models.game_state import GameState


def test_apply_effects_updates_multiple_statistics(
    fresh_state: GameState,
) -> None:
    """Effects should update state and return actual changes."""
    changes = fresh_state.apply_effects(
        {
            "treasury": -10,
            "public_trust": 5,
            "unrest": 3,
        }
    )

    assert fresh_state.treasury == 55
    assert fresh_state.public_trust == 55
    assert fresh_state.unrest == 28

    assert changes == {
        "treasury": (65, 55),
        "public_trust": (50, 55),
        "unrest": (25, 28),
    }


def test_apply_effects_clamps_statistics(
    fresh_state: GameState,
) -> None:
    """Statistics should never fall below 0 or exceed 100."""
    fresh_state.public_trust = 98
    fresh_state.unrest = 2

    changes = fresh_state.apply_effects(
        {
            "public_trust": 20,
            "unrest": -20,
        }
    )

    assert fresh_state.public_trust == 100
    assert fresh_state.unrest == 0

    assert changes["public_trust"] == (98, 100)
    assert changes["unrest"] == (2, 0)


def test_apply_effects_rejects_unknown_statistic(
    fresh_state: GameState,
) -> None:
    """Unknown statistic names should produce a useful error."""
    with pytest.raises(
        ValueError,
        match="Unknown city statistic",
    ):
        fresh_state.apply_effects(
            {
                "political_power": 10,
            }
        )


def test_record_decision_updates_history(
    fresh_state: GameState,
    sample_event: dict,
) -> None:
    """A completed decision should be stored in the state."""
    choice = sample_event["choices"][0]

    changes = fresh_state.apply_effects(
        choice["effects"]
    )

    record = fresh_state.record_decision(
        turn_number=1,
        event=sample_event,
        choice=choice,
        stat_changes=changes,
    )

    assert len(fresh_state.decision_history) == 1
    assert record.event_id == "test_crisis"
    assert record.choice_id == "test_choice"
    assert record.turn_number == 1

    assert fresh_state.has_completed_event(
        "test_crisis"
    )
    assert fresh_state.has_made_choice(
        event_id="test_crisis",
        choice_id="test_choice",
    )


def test_same_event_cannot_be_recorded_twice(
    fresh_state: GameState,
    sample_event: dict,
) -> None:
    """The same event should not be completed twice."""
    choice = sample_event["choices"][0]

    fresh_state.record_decision(
        turn_number=1,
        event=sample_event,
        choice=choice,
        stat_changes={},
    )

    with pytest.raises(
        ValueError,
        match="already been completed",
    ):
        fresh_state.record_decision(
            turn_number=2,
            event=sample_event,
            choice=choice,
            stat_changes={},
        )