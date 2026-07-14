"""Dynamic event selection for The Last Mandate."""

from typing import Any

from app.engine.condition_engine import event_is_available
from app.models.game_state import GameState


def find_available_events(
    state: GameState,
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return all uncompleted events whose conditions are satisfied.
    """
    available_events: list[dict[str, Any]] = []

    for event in events:
        event_id = event["id"]

        if state.has_completed_event(event_id):
            continue

        if not event_is_available(
            state=state,
            event=event,
        ):
            continue

        available_events.append(event)

    return available_events


def select_next_event(
    available_events: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Select the highest-priority event.

    A lower order number means a higher priority.
    Event ID is used as a predictable tie-breaker.
    """
    if not available_events:
        return None

    return min(
        available_events,
        key=lambda event: (
            event["order"],
            event["id"],
        ),
    )


def get_next_event(
    state: GameState,
    events: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Find and select the next playable event."""
    available_events = find_available_events(
        state=state,
        events=events,
    )

    return select_next_event(available_events)