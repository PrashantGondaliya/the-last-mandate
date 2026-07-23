"""Tests for loading and validating JSON event files."""

import json
from pathlib import Path

import pytest

from app.engine.event_loader import (
    EventDataError,
    load_events,
)


def build_valid_event(
    event_id: str,
    order: int,
) -> dict:
    """Create valid JSON-compatible event data."""
    return {
        "id": event_id,
        "order": order,
        "title": event_id.upper(),
        "description": "A valid test event.",
        "conditions": [],
        "choices": [
            {
                "id": "test_choice",
                "text": "Choose this option.",
                "outcome": "The choice is complete.",
                "effects": {
                    "treasury": -5,
                },
            }
        ],
    }


def write_event(
    directory: Path,
    filename: str,
    event_data: dict,
) -> None:
    """Write an event dictionary as JSON."""
    file_path = directory / filename

    file_path.write_text(
        json.dumps(
            event_data,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_load_events_discovers_and_sorts_files(
    tmp_path: Path,
) -> None:
    """Events should be loaded and sorted by order."""
    write_event(
        directory=tmp_path,
        filename="later.json",
        event_data=build_valid_event(
            event_id="later_event",
            order=20,
        ),
    )

    write_event(
        directory=tmp_path,
        filename="earlier.json",
        event_data=build_valid_event(
            event_id="earlier_event",
            order=10,
        ),
    )

    events = load_events(
        events_directory=tmp_path
    )

    assert [
        event["id"]
        for event in events
    ] == [
        "earlier_event",
        "later_event",
    ]


def test_invalid_json_produces_readable_error(
    tmp_path: Path,
) -> None:
    """Malformed JSON should raise EventDataError."""
    invalid_file = tmp_path / "broken.json"

    invalid_file.write_text(
        '{"id": "broken_event",',
        encoding="utf-8",
    )

    with pytest.raises(
        EventDataError,
        match="Invalid JSON",
    ):
        load_events(
            events_directory=tmp_path
        )


def test_missing_event_field_is_rejected(
    tmp_path: Path,
) -> None:
    """Missing required fields should be reported."""
    event_data = build_valid_event(
        event_id="missing_title",
        order=10,
    )

    del event_data["title"]

    write_event(
        directory=tmp_path,
        filename="missing_title.json",
        event_data=event_data,
    )

    with pytest.raises(
        EventDataError,
        match="title",
    ):
        load_events(
            events_directory=tmp_path
        )


def test_unknown_effect_statistic_is_rejected(
    tmp_path: Path,
) -> None:
    """Event effects may only use known city statistics."""
    event_data = build_valid_event(
        event_id="bad_effect",
        order=10,
    )

    event_data["choices"][0]["effects"] = {
        "unknown_stat": 5,
    }

    write_event(
        directory=tmp_path,
        filename="bad_effect.json",
        event_data=event_data,
    )

    with pytest.raises(
        EventDataError,
        match="unknown effect statistic",
    ):
        load_events(
            events_directory=tmp_path
        )

def test_unknown_condition_type_is_rejected(
    tmp_path: Path,
) -> None:
    """Unsupported narrative conditions should fail validation."""
    event_data = build_valid_event(
        event_id="bad_condition",
        order=10,
    )

    event_data["conditions"] = [
        {
            "type": "unknown_condition",
        }
    ]

    write_event(
        directory=tmp_path,
        filename="bad_condition.json",
        event_data=event_data,
    )

    with pytest.raises(
        EventDataError,
        match="unsupported condition type",
    ):
        load_events(
            events_directory=tmp_path
        )

def test_unknown_event_condition_reference_is_rejected(
    tmp_path: Path,
) -> None:
    """History conditions must reference existing events."""
    event_data = build_valid_event(
        event_id="branch_event",
        order=10,
    )

    event_data["conditions"] = [
        {
            "type": "event_completed",
            "event_id": "missing_event",
        }
    ]

    write_event(
        directory=tmp_path,
        filename="branch_event.json",
        event_data=event_data,
    )

    with pytest.raises(
        EventDataError,
        match="unknown event ID",
    ):
        load_events(
            events_directory=tmp_path
        )

def test_unknown_character_condition_reference_is_rejected(
    tmp_path: Path,
) -> None:
    """Relationship conditions must reference known characters."""
    event_data = build_valid_event(
        event_id="character_branch",
        order=10,
    )

    event_data["conditions"] = [
        {
            "type": "character_relationship",
            "character_id": "unknown_character",
            "relationship": "trust",
            "operator": "<=",
            "value": 30,
        }
    ]

    write_event(
        directory=tmp_path,
        filename="character_branch.json",
        event_data=event_data,
    )

    with pytest.raises(
        EventDataError,
        match="unknown character ID",
    ):
        load_events(
            events_directory=tmp_path,
            known_character_ids={
                "elena_voss",
            },
        )