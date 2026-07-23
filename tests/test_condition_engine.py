"""Tests for narrative event conditions."""

from app.engine.condition_engine import (
    condition_is_met,
    event_is_available,
)
from app.models.character_state import CharacterState
from app.models.game_state import GameState


def test_legacy_stat_condition_is_supported(
    fresh_state: GameState,
) -> None:
    """Old statistic conditions should remain valid."""
    condition = {
        "stat": "treasury",
        "operator": "<=",
        "value": 65,
    }

    assert condition_is_met(
        state=fresh_state,
        condition=condition,
    )


def test_explicit_stat_condition_is_supported(
    fresh_state: GameState,
) -> None:
    """Statistic conditions may use an explicit type."""
    condition = {
        "type": "stat",
        "stat": "public_trust",
        "operator": ">=",
        "value": 50,
    }

    assert condition_is_met(
        state=fresh_state,
        condition=condition,
    )


def test_event_completed_condition(
    fresh_state: GameState,
) -> None:
    """Completed-event conditions should use event history."""
    condition = {
        "type": "event_completed",
        "event_id": "hospital_blackout",
    }

    assert not condition_is_met(
        state=fresh_state,
        condition=condition,
    )

    fresh_state.completed_event_ids.add(
        "hospital_blackout"
    )

    assert condition_is_met(
        state=fresh_state,
        condition=condition,
    )


def test_choice_made_condition(
    fresh_state: GameState,
) -> None:
    """Specific decisions should unlock conditions."""
    event = {
        "id": "missing_report",
        "title": "THE MISSING REPORT",
    }

    choice = {
        "id": "defend_minister",
        "text": "Defend the minister.",
        "effects": {},
    }

    fresh_state.record_decision(
        turn_number=3,
        event=event,
        choice=choice,
        stat_changes={},
    )

    condition = {
        "type": "choice_made",
        "event_id": "missing_report",
        "choice_id": "defend_minister",
    }

    assert condition_is_met(
        state=fresh_state,
        condition=condition,
    )


def test_character_relationship_condition() -> None:
    """Character conditions should use current relationships."""
    elena = CharacterState(
        id="elena_voss",
        name="Elena Voss",
        role="Journalist",
        description="A test character.",
        trust=30,
        fear=10,
        loyalty=25,
    )

    state = GameState(
        player_name="Test Governor",
        characters={
            elena.id: elena,
        },
    )

    condition = {
        "type": "character_relationship",
        "character_id": "elena_voss",
        "relationship": "trust",
        "operator": "<=",
        "value": 30,
    }

    assert condition_is_met(
        state=state,
        condition=condition,
    )


def test_every_event_condition_must_be_met() -> None:
    """Multiple conditions should use AND behaviour."""
    elena = CharacterState(
        id="elena_voss",
        name="Elena Voss",
        role="Journalist",
        description="A test character.",
        trust=25,
        fear=10,
        loyalty=25,
    )

    state = GameState(
        player_name="Test Governor",
        characters={
            elena.id: elena,
        },
    )

    event = {
        "id": "branching_event",
        "conditions": [
            {
                "type": "event_completed",
                "event_id": "missing_report",
            },
            {
                "type": "character_relationship",
                "character_id": "elena_voss",
                "relationship": "trust",
                "operator": "<=",
                "value": 30,
            },
        ],
    }

    assert not event_is_available(
        state=state,
        event=event,
    )

    state.completed_event_ids.add(
        "missing_report"
    )

    assert event_is_available(
        state=state,
        event=event,
    )