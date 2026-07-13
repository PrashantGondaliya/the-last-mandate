"""Condition evaluation for state-driven events."""

from operator import eq, ge, gt, le, lt, ne

from app.models.game_state import GameState, STAT_LABELS


COMPARISON_OPERATORS = {
    "<": lt,
    "<=": le,
    "==": eq,
    "!=": ne,
    ">=": ge,
    ">": gt,
}


def condition_is_met(
    state: GameState,
    condition: dict,
) -> bool:
    """Return whether one event condition is satisfied."""
    stat_name = condition.get("stat")
    operator_symbol = condition.get("operator")
    expected_value = condition.get("value")

    if stat_name not in STAT_LABELS:
        raise ValueError(
            f"Unknown condition statistic: {stat_name}"
        )

    if operator_symbol not in COMPARISON_OPERATORS:
        raise ValueError(
            f"Unsupported condition operator: {operator_symbol}"
        )

    if not isinstance(expected_value, int):
        raise ValueError(
            "Condition value must be an integer."
        )

    actual_value = getattr(state, stat_name)
    comparison_function = COMPARISON_OPERATORS[
        operator_symbol
    ]

    return comparison_function(
        actual_value,
        expected_value,
    )


def event_is_available(
    state: GameState,
    event: dict,
) -> bool:
    """Return whether every condition for an event is satisfied."""
    conditions = event.get("conditions", [])

    return all(
        condition_is_met(state, condition)
        for condition in conditions
    )