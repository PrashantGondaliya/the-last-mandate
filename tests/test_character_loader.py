"""Tests for loading character JSON content."""

import json
from pathlib import Path

import pytest

from app.engine.character_loader import (
    CharacterDataError,
    load_characters,
)


def build_character(
    character_id: str,
    name: str,
) -> dict:
    """Create valid character JSON data."""
    return {
        "id": character_id,
        "name": name,
        "role": "Test Role",
        "description": "A test character.",
        "trust": 50,
        "fear": 10,
        "loyalty": 60,
    }


def write_character(
    directory: Path,
    filename: str,
    character_data: dict,
) -> None:
    """Write character data to a JSON file."""
    (directory / filename).write_text(
        json.dumps(character_data),
        encoding="utf-8",
    )


def test_load_characters_returns_character_states(
    tmp_path: Path,
) -> None:
    """Valid files should become CharacterState objects."""
    write_character(
        directory=tmp_path,
        filename="elena.json",
        character_data=build_character(
            character_id="elena",
            name="Elena",
        ),
    )

    characters = load_characters(tmp_path)

    assert "elena" in characters
    assert characters["elena"].name == "Elena"
    assert characters["elena"].trust == 50


def test_invalid_relationship_value_is_rejected(
    tmp_path: Path,
) -> None:
    """Relationship values must remain between 0 and 100."""
    character_data = build_character(
        character_id="invalid",
        name="Invalid",
    )
    character_data["trust"] = 120

    write_character(
        directory=tmp_path,
        filename="invalid.json",
        character_data=character_data,
    )

    with pytest.raises(
        CharacterDataError,
        match="between 0 and 100",
    ):
        load_characters(tmp_path)


def test_duplicate_character_ids_are_rejected(
    tmp_path: Path,
) -> None:
    """Two files cannot define the same character ID."""
    character_data = build_character(
        character_id="duplicate",
        name="Duplicate",
    )

    write_character(
        tmp_path,
        "one.json",
        character_data,
    )
    write_character(
        tmp_path,
        "two.json",
        character_data,
    )

    with pytest.raises(
        CharacterDataError,
        match="Duplicate character ID",
    ):
        load_characters(tmp_path)