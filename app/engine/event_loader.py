"""Load and validate event data from JSON files."""

import json
from pathlib import Path
from typing import Any
from app.models.character_state import RELATIONSHIP_LABELS
#from app.engine.condition_engine import COMPARISON_OPERATORS
from app.models.game_state import STAT_LABELS
from app.models.faction_state import FACTION_STAT_LABELS
from app.models.information_report import (
    TRUTH_STATUSES,
)
from app.engine.condition_engine import (
    COMPARISON_OPERATORS,
    CONDITION_TYPES,
    get_condition_type,
)

EVENTS_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "content"
    / "events"
)


class EventDataError(ValueError):
    """Raised when event content is missing or invalid."""


def load_events(
    events_directory: Path = EVENTS_DIRECTORY,
    known_character_ids: set[str] | None = None,
    known_faction_ids: set[str] | None = None,
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

    _validate_condition_references(events)
    _validate_report_ids(events)

    if known_character_ids is not None:
        _validate_character_references(
            events=events,
            known_character_ids=known_character_ids,
        )

    events.sort(
        key=lambda event: (
            event["order"],
            event["id"],
        )
    )
    if known_faction_ids is not None:
        _validate_faction_references(
            events=events,
            known_faction_ids=known_faction_ids,
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

    _validate_reports(
        reports=event.get("reports", []),
        context=f"Event '{event['id']}'",
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
                "must be an object."
            )

        try:
            condition_type = get_condition_type(
                condition
            )
        except ValueError as error:
            raise EventDataError(
                f"{condition_context}: {error}"
            ) from error

        if condition_type not in CONDITION_TYPES:
            raise EventDataError(
                f"{condition_context} uses unsupported "
                f"condition type '{condition_type}'."
            )

        if condition_type == "stat":
            _validate_stat_condition(
                condition=condition,
                context=condition_context,
            )

        elif condition_type == "event_completed":
            _validate_event_completed_condition(
                condition=condition,
                context=condition_context,
            )

        elif condition_type == "faction_stat":
            _validate_faction_stat_condition(
                condition=condition,
                context=condition_context,
            )

        elif condition_type == "choice_made":
            _validate_choice_made_condition(
                condition=condition,
                context=condition_context,
            )

        elif condition_type == "character_relationship":
            _validate_character_relationship_condition(
                condition=condition,
                context=condition_context,
            )

def _validate_stat_condition(
    condition: dict[str, Any],
    context: str,
) -> None:
    """Validate a city-statistic condition."""
    _require_fields(
        data=condition,
        required_fields={
            "stat",
            "operator",
            "value",
        },
        context=context,
    )

    stat_name = condition["stat"]

    if stat_name not in STAT_LABELS:
        raise EventDataError(
            f"{context} uses unknown statistic "
            f"'{stat_name}'."
        )

    _validate_comparison_fields(
        condition=condition,
        context=context,
    )


def _validate_event_completed_condition(
    condition: dict[str, Any],
    context: str,
) -> None:
    """Validate an event-completed condition."""
    _require_fields(
        data=condition,
        required_fields={
            "type",
            "event_id",
        },
        context=context,
    )

    _validate_non_empty_string(
        value=condition["event_id"],
        field_name="event_id",
        context=context,
    )


def _validate_choice_made_condition(
    condition: dict[str, Any],
    context: str,
) -> None:
    """Validate a specific-choice condition."""
    _require_fields(
        data=condition,
        required_fields={
            "type",
            "event_id",
            "choice_id",
        },
        context=context,
    )

    _validate_non_empty_string(
        value=condition["event_id"],
        field_name="event_id",
        context=context,
    )

    _validate_non_empty_string(
        value=condition["choice_id"],
        field_name="choice_id",
        context=context,
    )


def _validate_character_relationship_condition(
    condition: dict[str, Any],
    context: str,
) -> None:
    """Validate a character-relationship condition."""
    _require_fields(
        data=condition,
        required_fields={
            "type",
            "character_id",
            "relationship",
            "operator",
            "value",
        },
        context=context,
    )

    _validate_non_empty_string(
        value=condition["character_id"],
        field_name="character_id",
        context=context,
    )

    relationship_name = condition[
        "relationship"
    ]

    if relationship_name not in RELATIONSHIP_LABELS:
        raise EventDataError(
            f"{context} uses unknown relationship "
            f"'{relationship_name}'."
        )

    _validate_comparison_fields(
        condition=condition,
        context=context,
    )


def _validate_comparison_fields(
    condition: dict[str, Any],
    context: str,
) -> None:
    """Validate a comparison operator and integer value."""
    operator_symbol = condition["operator"]
    expected_value = condition["value"]

    if operator_symbol not in COMPARISON_OPERATORS:
        raise EventDataError(
            f"{context} uses unsupported operator "
            f"'{operator_symbol}'."
        )

    if type(expected_value) is not int:
        raise EventDataError(
            f"{context} field 'value' "
            "must be an integer."
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

        faction_effects = choice.get(
            "faction_effects",
            {},
        )

        _validate_faction_effects(
            faction_effects=faction_effects,
            context=choice_context,
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


def _validate_condition_references(
    events: list[dict[str, Any]],
) -> None:
    """Validate referenced event and choice IDs."""
    events_by_id = {
        event["id"]: event
        for event in events
    }

    for source_event in events:
        for condition_number, condition in enumerate(
            source_event.get("conditions", []),
            start=1,
        ):
            condition_type = get_condition_type(
                condition
            )

            if condition_type not in {
                "event_completed",
                "choice_made",
            }:
                continue

            referenced_event_id = condition[
                "event_id"
            ]

            referenced_event = events_by_id.get(
                referenced_event_id
            )

            if referenced_event is None:
                raise EventDataError(
                    f"Event '{source_event['id']}', "
                    f"condition {condition_number}, "
                    "references unknown event ID "
                    f"'{referenced_event_id}'."
                )

            if condition_type != "choice_made":
                continue

            referenced_choice_id = condition[
                "choice_id"
            ]

            valid_choice_ids = {
                choice["id"]
                for choice
                in referenced_event["choices"]
            }

            if referenced_choice_id not in valid_choice_ids:
                raise EventDataError(
                    f"Event '{source_event['id']}', "
                    f"condition {condition_number}, "
                    f"references unknown choice ID "
                    f"'{referenced_choice_id}' in event "
                    f"'{referenced_event_id}'."
                )


def _validate_character_references(
    events: list[dict[str, Any]],
    known_character_ids: set[str],
) -> None:
    """Validate all character IDs used by events."""
    for event in events:
        for condition_number, condition in enumerate(
            event.get("conditions", []),
            start=1,
        ):
            if (
                get_condition_type(condition)
                != "character_relationship"
            ):
                continue

            character_id = condition[
                "character_id"
            ]

            if character_id not in known_character_ids:
                raise EventDataError(
                    f"Event '{event['id']}', "
                    f"condition {condition_number}, "
                    "references unknown character ID "
                    f"'{character_id}'."
                )

        for choice_number, choice in enumerate(
            event["choices"],
            start=1,
        ):
            character_effects = choice.get(
                "character_effects",
                {},
            )

            for character_id in character_effects:
                if character_id not in known_character_ids:
                    raise EventDataError(
                        f"Event '{event['id']}', "
                        f"choice {choice_number}, "
                        "references unknown character ID "
                        f"'{character_id}'."
                    )
        for report_number, report in enumerate(
                event.get("reports", []),
                start=1,
        ):
            character_id = report[
                "source_character_id"
            ]

            if character_id not in known_character_ids:
                raise EventDataError(
                    f"Event '{event['id']}', "
                    f"report {report_number}, "
                    "references unknown character ID "
                    f"'{character_id}'."
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

def _validate_faction_stat_condition(
    condition: dict[str, Any],
    context: str,
) -> None:
    """Validate a faction-stat condition."""
    _require_fields(
        data=condition,
        required_fields={
            "type",
            "faction_id",
            "faction_stat",
            "operator",
            "value",
        },
        context=context,
    )

    _validate_non_empty_string(
        value=condition["faction_id"],
        field_name="faction_id",
        context=context,
    )

    stat_name = condition["faction_stat"]

    if stat_name not in FACTION_STAT_LABELS:
        raise EventDataError(
            f"{context} uses unknown faction "
            f"statistic '{stat_name}'."
        )

    _validate_comparison_fields(
        condition=condition,
        context=context,
    )

def _validate_faction_effects(
    faction_effects: Any,
    context: str,
) -> None:
    """Validate optional faction effects."""
    if not isinstance(faction_effects, dict):
        raise EventDataError(
            f"{context} field 'faction_effects' "
            "must be an object."
        )

    for faction_id, effects in faction_effects.items():
        if (
            not isinstance(faction_id, str)
            or not faction_id.strip()
        ):
            raise EventDataError(
                f"{context} contains an invalid "
                "faction ID."
            )

        if not isinstance(effects, dict):
            raise EventDataError(
                f"{context} effects for faction "
                f"'{faction_id}' must be an object."
            )

        for stat_name, amount in effects.items():
            if stat_name not in FACTION_STAT_LABELS:
                raise EventDataError(
                    f"{context} uses unknown faction "
                    f"statistic '{stat_name}'."
                )

            if type(amount) is not int:
                raise EventDataError(
                    f"{context} faction statistic "
                    f"'{stat_name}' for '{faction_id}' "
                    "must be an integer."
                )

def _validate_faction_references(
    events: list[dict[str, Any]],
    known_faction_ids: set[str],
) -> None:
    """Validate all faction IDs used by events."""
    for event in events:
        for condition_number, condition in enumerate(
            event.get("conditions", []),
            start=1,
        ):
            if (
                get_condition_type(condition)
                != "faction_stat"
            ):
                continue

            faction_id = condition["faction_id"]

            if faction_id not in known_faction_ids:
                raise EventDataError(
                    f"Event '{event['id']}', "
                    f"condition {condition_number}, "
                    "references unknown faction ID "
                    f"'{faction_id}'."
                )

        for choice_number, choice in enumerate(
            event["choices"],
            start=1,
        ):
            faction_effects = choice.get(
                "faction_effects",
                {},
            )

            for faction_id in faction_effects:
                if faction_id not in known_faction_ids:
                    raise EventDataError(
                        f"Event '{event['id']}', "
                        f"choice {choice_number}, "
                        "references unknown faction ID "
                        f"'{faction_id}'."
                    )

def _validate_reports(
    reports: Any,
    context: str,
) -> None:
    """Validate optional unreliable-information reports."""
    if not isinstance(reports, list):
        raise EventDataError(
            f"{context} field 'reports' "
            "must be a list."
        )

    local_report_ids: set[str] = set()

    for report_number, report in enumerate(
        reports,
        start=1,
    ):
        report_context = (
            f"{context}, report {report_number}"
        )

        if not isinstance(report, dict):
            raise EventDataError(
                f"{report_context} must be an object."
            )

        _require_fields(
            data=report,
            required_fields={
                "id",
                "source_character_id",
                "statement",
                "reliability",
                "truth",
                "reveal_after_turns",
                "revelation",
            },
            context=report_context,
        )

        for field_name in (
            "id",
            "source_character_id",
            "statement",
        ):
            _validate_non_empty_string(
                value=report[field_name],
                field_name=field_name,
                context=report_context,
            )

        report_id = report["id"]

        if report_id in local_report_ids:
            raise EventDataError(
                f"{report_context} uses duplicate "
                f"report ID '{report_id}'."
            )

        local_report_ids.add(report_id)

        reliability = report["reliability"]

        if (
            type(reliability) is not int
            or not 0 <= reliability <= 100
        ):
            raise EventDataError(
                f"{report_context} field "
                "'reliability' must be an integer "
                "between 0 and 100."
            )

        truth = report["truth"]

        if truth not in TRUTH_STATUSES:
            raise EventDataError(
                f"{report_context} uses unknown "
                f"truth status '{truth}'."
            )

        reveal_after_turns = report[
            "reveal_after_turns"
        ]

        if (
            type(reveal_after_turns) is not int
            or reveal_after_turns < 1
        ):
            raise EventDataError(
                f"{report_context} field "
                "'reveal_after_turns' must be "
                "a positive integer."
            )

        revelation = report["revelation"]

        if not isinstance(revelation, dict):
            raise EventDataError(
                f"{report_context} field "
                "'revelation' must be an object."
            )

        _require_fields(
            data=revelation,
            required_fields={
                "title",
                "text",
            },
            context=(
                f"{report_context} revelation"
            ),
        )

        for field_name in (
            "title",
            "text",
        ):
            _validate_non_empty_string(
                value=revelation[field_name],
                field_name=field_name,
                context=(
                    f"{report_context} revelation"
                ),
            )

def _validate_report_ids(
    events: list[dict[str, Any]],
) -> None:
    """Require report IDs to be unique across all events."""
    report_locations: dict[str, str] = {}

    for event in events:
        for report in event.get("reports", []):
            report_id = report["id"]

            existing_event_id = report_locations.get(
                report_id
            )

            if existing_event_id is not None:
                raise EventDataError(
                    f"Report ID '{report_id}' appears "
                    f"in both event "
                    f"'{existing_event_id}' and "
                    f"event '{event['id']}'."
                )

            report_locations[report_id] = (
                event["id"]
            )