"""Load and validate character data from JSON files."""

import json
from pathlib import Path
from typing import Any

from app.models.character_state import CharacterState


CHARACTERS_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "content"
    / "characters"
)


class CharacterDataError(ValueError):
    """Raised when character content is missing or invalid."""


def load_characters(
    characters_directory: Path = CHARACTERS_DIRECTORY,
) -> dict[str, CharacterState]:
    """Load and return all character definitions."""
    if not characters_directory.exists():
        raise CharacterDataError(
            "Characters directory does not exist: "
            f"{characters_directory}"
        )

    character_files = sorted(
        characters_directory.glob("*.json")
    )

    if not character_files:
        raise CharacterDataError(
            "No JSON character files found in: "
            f"{characters_directory}"
        )

    characters: dict[str, CharacterState] = {}

    for file_path in character_files:
        character_data = _load_character_file(
            file_path
        )

        character = _validate_and_create_character(
            character_data=character_data,
            file_path=file_path,
        )

        if character.id in characters:
            raise CharacterDataError(
                f"Duplicate character ID "
                f"'{character.id}' in "
                f"{file_path.name}."
            )

        characters[character.id] = character

    return characters


def _load_character_file(
    file_path: Path,
) -> dict[str, Any]:
    """Read one character JSON file."""
    try:
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as character_file:
            data = json.load(character_file)

    except json.JSONDecodeError as error:
        raise CharacterDataError(
            f"Invalid JSON in {file_path.name} "
            f"at line {error.lineno}, "
            f"column {error.colno}: "
            f"{error.msg}"
        ) from error

    except OSError as error:
        raise CharacterDataError(
            f"Could not read character file "
            f"{file_path.name}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise CharacterDataError(
            f"{file_path.name} must contain "
            "one JSON object."
        )

    return data


def _validate_and_create_character(
    character_data: dict[str, Any],
    file_path: Path,
) -> CharacterState:
    """Validate JSON data and create a CharacterState."""
    required_fields = {
        "id",
        "name",
        "role",
        "description",
        "trust",
        "fear",
        "loyalty",
    }

    missing_fields = (
        required_fields - character_data.keys()
    )

    if missing_fields:
        formatted_fields = ", ".join(
            sorted(missing_fields)
        )

        raise CharacterDataError(
            f"Character file {file_path.name} "
            f"is missing field(s): "
            f"{formatted_fields}."
        )

    for field_name in (
        "id",
        "name",
        "role",
        "description",
    ):
        value = character_data[field_name]

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise CharacterDataError(
                f"Character file {file_path.name} "
                f"field '{field_name}' must be "
                "a non-empty string."
            )

    for field_name in (
        "trust",
        "fear",
        "loyalty",
    ):
        value = character_data[field_name]

        if (
            type(value) is not int
            or not 0 <= value <= 100
        ):
            raise CharacterDataError(
                f"Character file {file_path.name} "
                f"field '{field_name}' must be "
                "an integer between 0 and 100."
            )

    return CharacterState(
        id=character_data["id"],
        name=character_data["name"],
        role=character_data["role"],
        description=character_data["description"],
        trust=character_data["trust"],
        fear=character_data["fear"],
        loyalty=character_data["loyalty"],
    )