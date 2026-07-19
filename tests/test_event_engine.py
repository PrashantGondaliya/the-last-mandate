"""Tests for dynamic event selection."""

from app.engine.event_engine import (
    find_available_events,
    get_next_event,
)
from app.models.game_state import GameState


def build_event(
    event_id: str,
    order: int,
    conditions: list[dict] | None = None,
) -> dict:
    """Create a minimal event for an engine test."""
    return {
        "id": event_id,
        "order": order,
        "title": event_id.upper(),
        "description": "Test event.",
        "conditions": conditions or [],
        "choices": [],
    }


def test_selects_available_event_with_lowest_order(
    fresh_state: GameState,
) -> None:
    """Lower order should receive higher priority."""
    events = [
        build_event(
            event_id="second_event",
            order=20,
        ),
        build_event(
            event_id="first_event",
            order=10,
        ),
    ]

    selected = get_next_event(
        state=fresh_state,
        events=events,
    )

    assert selected is not None
    assert selected["id"] == "first_event"


def test_unmet_conditional_event_is_skipped(
    fresh_state: GameState,
) -> None:
    """An unavailable event must not be selected."""
    events = [
        build_event(
            event_id="financial_crisis",
            order=10,
            conditions=[
                {
                    "stat": "treasury",
                    "operator": "<=",
                    "value": 40,
                }
            ],
        ),
        build_event(
            event_id="ordinary_crisis",
            order=20,
        ),
    ]

    selected = get_next_event(
        state=fresh_state,
        events=events,
    )

    assert selected is not None
    assert selected["id"] == "ordinary_crisis"


def test_conditional_event_becomes_available(
    fresh_state: GameState,
) -> None:
    """Changing state should unlock a conditional event."""
    events = [
        build_event(
            event_id="financial_crisis",
            order=10,
            conditions=[
                {
                    "stat": "treasury",
                    "operator": "<=",
                    "value": 40,
                }
            ],
        )
    ]

    assert get_next_event(
        state=fresh_state,
        events=events,
    ) is None

    fresh_state.treasury = 35

    selected = get_next_event(
        state=fresh_state,
        events=events,
    )

    assert selected is not None
    assert selected["id"] == "financial_crisis"


def test_completed_events_are_excluded(
    fresh_state: GameState,
) -> None:
    """Completed events must not be offered again."""
    events = [
        build_event(
            event_id="completed_event",
            order=10,
        ),
        build_event(
            event_id="remaining_event",
            order=20,
        ),
    ]

    fresh_state.completed_event_ids.add(
        "completed_event"
    )

    available = find_available_events(
        state=fresh_state,
        events=events,
    )

    assert [
        event["id"]
        for event in available
    ] == ["remaining_event"]