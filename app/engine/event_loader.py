"""Load and validate event data from JSON files."""

import json
from pathlib import Path
from typing import Any
from app.models.character_state import RELATIONSHIP_LABELS
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
            f"Events directory does not exist: "
            f"{events_directory}"
        )

    event_files = sorted(
        events_directory.glob("*.json")
    )

    if not event_files:
        raise EventDataError(
            f"No JSON event files found in: "
            f"{events_directory}"
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

    events.sort(
        key=lambda event: (
            event["order"],
            event["id"],
        )
    )

    return events


def _load_event_file(
    file_path: Path,
) -> dict[str, Any]:
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
            f"column {error.colno}: "
            f"{error.msg}"
        ) from error

    except OSError as error:
        raise EventDataError(
            f"Could not read event file "
            f"{file_path.name}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise EventDataError(
            f"{file_path.name} must contain "
            f"one JSON object."
        )

    return data


def _validate_event(
    event: dict[str, Any],
    file_path: Path,
    existing_event_ids: set[str],
) -> None:
    """Validate one event and its nested content."""
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
            f"{context} field 'order' "
            f"must be an integer."
        )

    if not isinstance(event["conditions"], list):
        raise EventDataError(
            f"{context} field 'conditions' "
            f"must be a list."
        )

    if not isinstance(event["choices"], list):
        raise EventDataError(
            f"{context} field 'choices' "
            f"must be a list."
        )

    if not event["choices"]:
        raise EventDataError(
            f"{context} must contain "
            f"at least one choice."
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
            f"{context}, "
            f"condition {condition_number}"
        )

        if not isinstance(condition, dict):
            raise EventDataError(
                f"{condition_context} "
                f"must be an object."
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
                f"{condition_context} uses "
                f"unknown statistic '{stat_name}'."
            )

        if operator_symbol not in COMPARISON_OPERATORS:
            raise EventDataError(
                f"{condition_context} uses "
                f"unsupported operator "
                f"'{operator_symbol}'."
            )

        if type(expected_value) is not int:
            raise EventDataError(
                f"{condition_context} field "
                f"'value' must be an integer."
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
            f"{context}, "
            f"choice {choice_number}"
        )

        if not isinstance(choice, dict):
            raise EventDataError(
                f"{choice_context} "
                f"must be an object."
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

        for field_name in (
            "id",
            "text",
            "outcome",
        ):
            _validate_non_empty_string(
                value=choice[field_name],
                field_name=field_name,
                context=choice_context,
            )

        choice_id = choice["id"]

        if choice_id in choice_ids:
            raise EventDataError(
                f"{choice_context} uses "
                f"duplicate choice ID "
                f"'{choice_id}'."
            )

        choice_ids.add(choice_id)

        _validate_effects(
            effects=choice["effects"],
            context=choice_context,
        )

        delayed_consequences = choice.get(
            "delayed_consequences",
            [],
        )

        if not isinstance(
            delayed_consequences,
            list,
        ):
            raise EventDataError(
                f"{choice_context} field "
                f"'delayed_consequences' "
                f"must be a list."
            )

        _validate_delayed_consequences(
            delayed_consequences=delayed_consequences,
            context=choice_context,
        )

        character_effects = choice.get(
            "character_effects",
            {},
        )

        _validate_character_effects(
            character_effects=character_effects,
            context=choice_context,
        )


def _validate_delayed_consequences(
    delayed_consequences: list[Any],
    context: str,
) -> None:
    """Validate delayed consequences belonging to a choice."""
    consequence_ids: set[str] = set()

    for consequence_number, consequence in enumerate(
        delayed_consequences,
        start=1,
    ):
        consequence_context = (
            f"{context}, delayed consequence "
            f"{consequence_number}"
        )

        if not isinstance(consequence, dict):
            raise EventDataError(
                f"{consequence_context} "
                f"must be an object."
            )

        _require_fields(
            data=consequence,
            required_fields={
                "id",
                "delay_turns",
                "title",
                "description",
                "effects",
            },
            context=consequence_context,
        )

        for field_name in (
            "id",
            "title",
            "description",
        ):
            _validate_non_empty_string(
                value=consequence[field_name],
                field_name=field_name,
                context=consequence_context,
            )

        consequence_id = consequence["id"]

        if consequence_id in consequence_ids:
            raise EventDataError(
                f"{consequence_context} uses "
                f"duplicate consequence ID "
                f"'{consequence_id}'."
            )

        consequence_ids.add(consequence_id)

        delay_turns = consequence["delay_turns"]

        if (
            type(delay_turns) is not int
            or delay_turns < 1
        ):
            raise EventDataError(
                f"{consequence_context} field "
                f"'delay_turns' must be a "
                f"positive integer."
            )

        _validate_effects(
            effects=consequence["effects"],
            context=consequence_context,
        )

def _validate_character_effects(
    character_effects: Any,
    context: str,
) -> None:
    """Validate optional character relationship effects."""
    if not isinstance(character_effects, dict):
        raise EventDataError(
            f"{context} field 'character_effects' "
            "must be an object."
        )

    for character_id, effects in character_effects.items():
        if (
            not isinstance(character_id, str)
            or not character_id.strip()
        ):
            raise EventDataError(
                f"{context} contains an invalid "
                "character ID."
            )

        if not isinstance(effects, dict):
            raise EventDataError(
                f"{context} effects for character "
                f"'{character_id}' must be an object."
            )

        for relationship_name, amount in effects.items():
            if relationship_name not in RELATIONSHIP_LABELS:
                raise EventDataError(
                    f"{context} uses unknown relationship "
                    f"'{relationship_name}'."
                )

            if type(amount) is not int:
                raise EventDataError(
                    f"{context} relationship "
                    f"'{relationship_name}' for "
                    f"'{character_id}' must be an integer."
                )

def _validate_effects(
    effects: Any,
    context: str,
) -> None:
    """Validate an effects dictionary."""
    if not isinstance(effects, dict):
        raise EventDataError(
            f"{context} field 'effects' "
            f"must be an object."
        )

    for stat_name, amount in effects.items():
        if stat_name not in STAT_LABELS:
            raise EventDataError(
                f"{context} uses unknown "
                f"effect statistic '{stat_name}'."
            )

        if type(amount) is not int:
            raise EventDataError(
                f"{context} effect '{stat_name}' "
                f"must be an integer."
            )


def _require_fields(
    data: dict[str, Any],
    required_fields: set[str],
    context: str,
) -> None:
    """Ensure a dictionary contains required fields."""
    missing_fields = required_fields - data.keys()

    if missing_fields:
        formatted_fields = ", ".join(
            sorted(missing_fields)
        )

        raise EventDataError(
            f"{context} is missing required "
            f"field(s): {formatted_fields}."
        )


def _validate_non_empty_string(
    value: Any,
    field_name: str,
    context: str,
) -> None:
    """Ensure a value is a non-empty string."""
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise EventDataError(
            f"{context} field '{field_name}' "
            f"must be a non-empty string."
        )