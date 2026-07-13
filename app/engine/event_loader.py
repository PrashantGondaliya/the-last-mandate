"""Load and validate event data from JSON files."""

import json
from pathlib import Path
from typing import Any

from app.engine.condition_engine import COMPARISON_OPERATORS
from app.models.game_state import STAT_LABELS


EVENTS_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "content"
    / "events"
)


class EventDataError(ValueError):
    """Raised when event content is missing or invalid."""


def load_events(
    events_directory: Path = EVENTS_DIRECTORY,
) -> list[dict[str, Any]]:
    """Load, validate, sort and return all JSON events."""
    if not events_directory.exists():
        raise EventDataError(
            f"Events directory does not exist: {events_directory}"
        )

    event_files = sorted(events_directory.glob("*.json"))

    if not event_files:
        raise EventDataError(
            f"No JSON event files found in: {events_directory}"
        )

    events: list[dict[str, Any]] = []
    event_ids: set[str] = set()

    for file_path in event_files:
        event = _load_event_file(file_path)

        _validate_event(
            event=event,
            file_path=file_path,
            existing_event_ids=event_ids,
        )

        event_ids.add(event["id"])
        events.append(event)

    events.sort(key=lambda event: event["order"])

    return events


def _load_event_file(file_path: Path) -> dict[str, Any]:
    """Read and decode one JSON event file."""
    try:
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as event_file:
            data = json.load(event_file)

    except json.JSONDecodeError as error:
        raise EventDataError(
            f"Invalid JSON in {file_path.name} "
            f"at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error

    except OSError as error:
        raise EventDataError(
            f"Could not read event file "
            f"{file_path.name}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise EventDataError(
            f"{file_path.name} must contain one JSON object."
        )

    return data


def _validate_event(
    event: dict[str, Any],
    file_path: Path,
    existing_event_ids: set[str],
) -> None:
    """Validate one event and all of its nested content."""
    context = f"Event file {file_path.name}"

    _require_fields(
        data=event,
        required_fields={
            "id",
            "order",
            "title",
            "description",
            "conditions",
            "choices",
        },
        context=context,
    )

    _validate_non_empty_string(
        value=event["id"],
        field_name="id",
        context=context,
    )
    _validate_non_empty_string(
        value=event["title"],
        field_name="title",
        context=context,
    )
    _validate_non_empty_string(
        value=event["description"],
        field_name="description",
        context=context,
    )

    if event["id"] in existing_event_ids:
        raise EventDataError(
            f"{context} uses duplicate event ID "
            f"'{event['id']}'."
        )

    if type(event["order"]) is not int:
        raise EventDataError(
            f"{context} field 'order' must be an integer."
        )

    if not isinstance(event["conditions"], list):
        raise EventDataError(
            f"{context} field 'conditions' must be a list."
        )

    if not isinstance(event["choices"], list):
        raise EventDataError(
            f"{context} field 'choices' must be a list."
        )

    if not event["choices"]:
        raise EventDataError(
            f"{context} must contain at least one choice."
        )

    _validate_conditions(
        conditions=event["conditions"],
        context=context,
    )

    _validate_choices(
        choices=event["choices"],
        context=context,
    )


def _validate_conditions(
    conditions: list[Any],
    context: str,
) -> None:
    """Validate every condition belonging to an event."""
    for condition_number, condition in enumerate(
        conditions,
        start=1,
    ):
        condition_context = (
            f"{context}, condition {condition_number}"
        )

        if not isinstance(condition, dict):
            raise EventDataError(
                f"{condition_context} must be an object."
            )

        _require_fields(
            data=condition,
            required_fields={
                "stat",
                "operator",
                "value",
            },
            context=condition_context,
        )

        stat_name = condition["stat"]
        operator_symbol = condition["operator"]
        expected_value = condition["value"]

        if stat_name not in STAT_LABELS:
            raise EventDataError(
                f"{condition_context} uses unknown statistic "
                f"'{stat_name}'."
            )

        if operator_symbol not in COMPARISON_OPERATORS:
            raise EventDataError(
                f"{condition_context} uses unsupported operator "
                f"'{operator_symbol}'."
            )

        if type(expected_value) is not int:
            raise EventDataError(
                f"{condition_context} field 'value' "
                f"must be an integer."
            )


def _validate_choices(
    choices: list[Any],
    context: str,
) -> None:
    """Validate every choice belonging to an event."""
    choice_ids: set[str] = set()

    for choice_number, choice in enumerate(
        choices,
        start=1,
    ):
        choice_context = (
            f"{context}, choice {choice_number}"
        )

        if not isinstance(choice, dict):
            raise EventDataError(
                f"{choice_context} must be an object."
            )

        _require_fields(
            data=choice,
            required_fields={
                "id",
                "text",
                "outcome",
                "effects",
            },
            context=choice_context,
        )

        for field_name in ("id", "text", "outcome"):
            _validate_non_empty_string(
                value=choice[field_name],
                field_name=field_name,
                context=choice_context,
            )

        choice_id = choice["id"]

        if choice_id in choice_ids:
            raise EventDataError(
                f"{choice_context} uses duplicate choice ID "
                f"'{choice_id}'."
            )

        choice_ids.add(choice_id)

        effects = choice["effects"]

        if not isinstance(effects, dict):
            raise EventDataError(
                f"{choice_context} field 'effects' "
                f"must be an object."
            )

        for stat_name, amount in effects.items():
            if stat_name not in STAT_LABELS:
                raise EventDataError(
                    f"{choice_context} uses unknown effect "
                    f"statistic '{stat_name}'."
                )

            if type(amount) is not int:
                raise EventDataError(
                    f"{choice_context} effect '{stat_name}' "
                    f"must be an integer."
                )


def _require_fields(
    data: dict[str, Any],
    required_fields: set[str],
    context: str,
) -> None:
    """Ensure that a dictionary contains required fields."""
    missing_fields = required_fields - data.keys()

    if missing_fields:
        formatted_fields = ", ".join(
            sorted(missing_fields)
        )

        raise EventDataError(
            f"{context} is missing required field(s): "
            f"{formatted_fields}."
        )


def _validate_non_empty_string(
    value: Any,
    field_name: str,
    context: str,
) -> None:
    """Ensure that a value is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise EventDataError(
            f"{context} field '{field_name}' "
            f"must be a non-empty string."
        )