"""Load and validate faction content from JSON files."""

import json
from pathlib import Path
from typing import Any

from app.models.faction_state import FactionState


FACTIONS_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "content"
    / "factions"
)


class FactionDataError(ValueError):
    """Raised when faction content is missing or invalid."""


def load_factions(
    factions_directory: Path = FACTIONS_DIRECTORY,
) -> dict[str, FactionState]:
    """Load and return all faction definitions."""
    if not factions_directory.exists():
        raise FactionDataError(
            "Factions directory does not exist: "
            f"{factions_directory}"
        )

    faction_files = sorted(
        factions_directory.glob("*.json")
    )

    if not faction_files:
        raise FactionDataError(
            "No JSON faction files found in: "
            f"{factions_directory}"
        )

    factions: dict[str, FactionState] = {}

    for file_path in faction_files:
        faction_data = _load_faction_file(file_path)

        faction = _validate_and_create_faction(
            faction_data=faction_data,
            file_path=file_path,
        )

        if faction.id in factions:
            raise FactionDataError(
                f"Duplicate faction ID "
                f"'{faction.id}' in {file_path.name}."
            )

        factions[faction.id] = faction

    return factions


def _load_faction_file(
    file_path: Path,
) -> dict[str, Any]:
    """Read one faction JSON file."""
    try:
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as faction_file:
            data = json.load(faction_file)

    except json.JSONDecodeError as error:
        raise FactionDataError(
            f"Invalid JSON in {file_path.name} "
            f"at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error

    except OSError as error:
        raise FactionDataError(
            f"Could not read faction file "
            f"{file_path.name}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise FactionDataError(
            f"{file_path.name} must contain "
            "one JSON object."
        )

    return data


def _validate_and_create_faction(
    faction_data: dict[str, Any],
    file_path: Path,
) -> FactionState:
    """Validate JSON data and create a FactionState."""
    required_fields = {
        "id",
        "name",
        "description",
        "support",
        "influence",
        "hostility",
    }

    missing_fields = required_fields - faction_data.keys()

    if missing_fields:
        formatted_fields = ", ".join(
            sorted(missing_fields)
        )

        raise FactionDataError(
            f"Faction file {file_path.name} "
            f"is missing field(s): {formatted_fields}."
        )

    for field_name in (
        "id",
        "name",
        "description",
    ):
        value = faction_data[field_name]

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise FactionDataError(
                f"Faction file {file_path.name} "
                f"field '{field_name}' must be "
                "a non-empty string."
            )

    for field_name in (
        "support",
        "influence",
        "hostility",
    ):
        value = faction_data[field_name]

        if (
            type(value) is not int
            or not 0 <= value <= 100
        ):
            raise FactionDataError(
                f"Faction file {file_path.name} "
                f"field '{field_name}' must be "
                "an integer between 0 and 100."
            )

    return FactionState(
        id=faction_data["id"],
        name=faction_data["name"],
        description=faction_data["description"],
        support=faction_data["support"],
        influence=faction_data["influence"],
        hostility=faction_data["hostility"],
    )