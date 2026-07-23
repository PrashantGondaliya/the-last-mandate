"""Condition evaluation for state-driven events."""

from operator import eq, ge, gt, le, lt, ne
from typing import Any

from app.models.character_state import RELATIONSHIP_LABELS
from app.models.game_state import GameState, STAT_LABELS


COMPARISON_OPERATORS = {
    "<": lt,
    "<=": le,
    "==": eq,
    "!=": ne,
    ">=": ge,
    ">": gt,
}

CONDITION_TYPES = {
    "stat",
    "event_completed",
    "choice_made",
    "character_relationship",
}


def get_condition_type(
    condition: dict[str, Any],
) -> str:
    """
    Return the condition type.

    Legacy statistic conditions without a 'type' field
    are treated as statistic conditions.
    """
    explicit_type = condition.get("type")

    if explicit_type is not None:
        return explicit_type

    if "stat" in condition:
        return "stat"

    raise ValueError(
        "Condition must contain either a valid "
        "'type' field or a legacy 'stat' field."
    )


def condition_is_met(
    state: GameState,
    condition: dict[str, Any],
) -> bool:
    """Return whether one event condition is satisfied."""
    condition_type = get_condition_type(condition)

    if condition_type == "stat":
        return _stat_condition_is_met(
            state=state,
            condition=condition,
        )

    if condition_type == "event_completed":
        return _event_completed_condition_is_met(
            state=state,
            condition=condition,
        )

    if condition_type == "choice_made":
        return _choice_made_condition_is_met(
            state=state,
            condition=condition,
        )

    if condition_type == "character_relationship":
        return _character_relationship_condition_is_met(
            state=state,
            condition=condition,
        )

    raise ValueError(
        f"Unsupported condition type: {condition_type}"
    )


def event_is_available(
    state: GameState,
    event: dict[str, Any],
) -> bool:
    """Return whether every condition for an event is satisfied."""
    conditions = event.get("conditions", [])

    return all(
        condition_is_met(
            state=state,
            condition=condition,
        )
        for condition in conditions
    )


def _stat_condition_is_met(
    state: GameState,
    condition: dict[str, Any],
) -> bool:
    """Evaluate a city-statistic condition."""
    stat_name = condition.get("stat")

    if stat_name not in STAT_LABELS:
        raise ValueError(
            f"Unknown condition statistic: {stat_name}"
        )

    actual_value = getattr(
        state,
        stat_name,
    )

    return _compare_values(
        actual_value=actual_value,
        operator_symbol=condition.get("operator"),
        expected_value=condition.get("value"),
    )


def _event_completed_condition_is_met(
    state: GameState,
    condition: dict[str, Any],
) -> bool:
    """Evaluate whether an event was completed."""
    event_id = condition.get("event_id")

    if (
        not isinstance(event_id, str)
        or not event_id.strip()
    ):
        raise ValueError(
            "Event-completed condition requires "
            "a non-empty event ID."
        )

    return state.has_completed_event(event_id)


def _choice_made_condition_is_met(
    state: GameState,
    condition: dict[str, Any],
) -> bool:
    """Evaluate whether a specific choice was made."""
    event_id = condition.get("event_id")
    choice_id = condition.get("choice_id")

    if (
        not isinstance(event_id, str)
        or not event_id.strip()
    ):
        raise ValueError(
            "Choice-made condition requires "
            "a non-empty event ID."
        )

    if (
        not isinstance(choice_id, str)
        or not choice_id.strip()
    ):
        raise ValueError(
            "Choice-made condition requires "
            "a non-empty choice ID."
        )

    return state.has_made_choice(
        event_id=event_id,
        choice_id=choice_id,
    )


def _character_relationship_condition_is_met(
    state: GameState,
    condition: dict[str, Any],
) -> bool:
    """Evaluate a major character's relationship value."""
    character_id = condition.get("character_id")
    relationship_name = condition.get(
        "relationship"
    )

    if (
        not isinstance(character_id, str)
        or not character_id.strip()
    ):
        raise ValueError(
            "Character relationship condition requires "
            "a non-empty character ID."
        )

    if relationship_name not in RELATIONSHIP_LABELS:
        raise ValueError(
            "Unknown character relationship: "
            f"{relationship_name}"
        )

    character = state.get_character(character_id)

    actual_value = getattr(
        character,
        relationship_name,
    )

    return _compare_values(
        actual_value=actual_value,
        operator_symbol=condition.get("operator"),
        expected_value=condition.get("value"),
    )


def _compare_values(
    actual_value: int,
    operator_symbol: Any,
    expected_value: Any,
) -> bool:
    """Compare two integer values using a supported operator."""
    if operator_symbol not in COMPARISON_OPERATORS:
        raise ValueError(
            "Unsupported condition operator: "
            f"{operator_symbol}"
        )

    if type(expected_value) is not int:
        raise ValueError(
            "Condition value must be an integer."
        )

    comparison_function = COMPARISON_OPERATORS[
        operator_symbol
    ]

    return comparison_function(
        actual_value,
        expected_value,
    )