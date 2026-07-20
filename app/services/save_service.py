"""Save and load game sessions using JSON files."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any
from app.models.character_state import CharacterState
from app.models.decision_record import DecisionRecord
from app.models.game_state import GameState, STAT_LABELS
from app.models.scheduled_consequence import (
    ScheduledConsequence,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAVES_DIRECTORY = PROJECT_ROOT / "saves"
AUTOSAVE_PATH = SAVES_DIRECTORY / "autosave.json"

SAVE_VERSION = 2


class SaveDataError(ValueError):
    """Raised when game save data cannot be used."""


def autosave_exists(
    file_path: Path = AUTOSAVE_PATH,
) -> bool:
    """Return whether an autosave file exists."""
    return file_path.is_file()


def save_game(
    state: GameState,
    file_path: Path = AUTOSAVE_PATH,
) -> None:
    """Serialize and save a complete game state."""
    save_data = {
        "save_version": SAVE_VERSION,
        "game_state": {
            "player_name": state.player_name,
            "current_turn": state.current_turn,
            "treasury": state.treasury,
            "public_trust": state.public_trust,
            "unrest": state.unrest,
            "infrastructure": state.infrastructure,
            "authority": state.authority,
            "business_confidence": (
                state.business_confidence
            ),
            "characters": {
                character_id: asdict(character)
                for character_id, character
                in sorted(state.characters.items())
            },
            "completed_event_ids": sorted(
                state.completed_event_ids
            ),
            "decision_history": [
                asdict(record)
                for record in state.decision_history
            ],
            "scheduled_consequences": [
                asdict(consequence)
                for consequence
                in state.scheduled_consequences
            ],
            "resolved_consequence_ids": sorted(
                state.resolved_consequence_ids
            ),
        },
    }

    temporary_path = file_path.with_suffix(".tmp")

    try:
        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with temporary_path.open(
            mode="w",
            encoding="utf-8",
        ) as save_file:
            json.dump(
                save_data,
                save_file,
                indent=2,
                ensure_ascii=False,
            )

        temporary_path.replace(file_path)

    except OSError as error:
        raise SaveDataError(
            f"Could not save the game: {error}"
        ) from error


def load_game(
    file_path: Path = AUTOSAVE_PATH,
) -> GameState:
    """Load and reconstruct a complete game state."""
    if not file_path.is_file():
        raise SaveDataError(
            f"Save file does not exist: {file_path}"
        )

    try:
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as save_file:
            save_data = json.load(save_file)

    except json.JSONDecodeError as error:
        raise SaveDataError(
            f"Invalid JSON in save file at "
            f"line {error.lineno}, "
            f"column {error.colno}: "
            f"{error.msg}"
        ) from error

    except OSError as error:
        raise SaveDataError(
            f"Could not read the save file: {error}"
        ) from error

    if not isinstance(save_data, dict):
        raise SaveDataError(
            "The save file must contain a JSON object."
        )

    save_version = save_data.get("save_version")

    if save_version != SAVE_VERSION:
        raise SaveDataError(
            f"Unsupported save version: {save_version}. "
            f"Expected version {SAVE_VERSION}."
        )

    state_data = save_data.get("game_state")

    if not isinstance(state_data, dict):
        raise SaveDataError(
            "The save file is missing valid game state data."
        )

    _validate_state_fields(state_data)

    try:
        decision_history = [
            _deserialize_decision_record(record_data)
            for record_data
            in state_data["decision_history"]
        ]

        scheduled_consequences = [
            _deserialize_scheduled_consequence(
                consequence_data
            )
            for consequence_data
            in state_data["scheduled_consequences"]
        ]

        characters = {
            character_id: _deserialize_character_state(
                character_data
            )
            for character_id, character_data
            in state_data["characters"].items()
        }

        for character_id, character in characters.items():
            if character.id != character_id:
                raise SaveDataError(
                    "Saved character dictionary key "
                    f"'{character_id}' does not match "
                    f"character ID '{character.id}'."
                )

        state = GameState(
            player_name=state_data["player_name"],
            current_turn=state_data["current_turn"],
            treasury=state_data["treasury"],
            public_trust=state_data["public_trust"],
            unrest=state_data["unrest"],
            infrastructure=state_data["infrastructure"],
            authority=state_data["authority"],
            business_confidence=(
                state_data["business_confidence"]
            ),
            completed_event_ids=set(
                state_data["completed_event_ids"]
            ),
            characters=characters,
            decision_history=decision_history,
            scheduled_consequences=(
                scheduled_consequences
            ),
            resolved_consequence_ids=set(
                state_data["resolved_consequence_ids"]
            ),
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise SaveDataError(
            f"Could not reconstruct game state: {error}"
        ) from error

    _validate_loaded_state(state)

    return state


def _validate_state_fields(
    state_data: dict[str, Any],
) -> None:
    """Validate the main fields in serialized game state."""
    required_fields = {
        "player_name",
        "current_turn",
        "treasury",
        "characters",
        "public_trust",
        "unrest",
        "infrastructure",
        "authority",
        "business_confidence",
        "completed_event_ids",
        "decision_history",
        "scheduled_consequences",
        "resolved_consequence_ids",
    }

    missing_fields = required_fields - state_data.keys()

    if missing_fields:
        formatted_fields = ", ".join(
            sorted(missing_fields)
        )

        raise SaveDataError(
            "Save data is missing required field(s): "
            f"{formatted_fields}."
        )

    list_fields = {
        "completed_event_ids",
        "decision_history",
        "scheduled_consequences",
        "resolved_consequence_ids",
    }

    for field_name in list_fields:
        if not isinstance(
            state_data[field_name],
            list,
        ):
            raise SaveDataError(
                f"Save field '{field_name}' "
                f"must be a list."
            )
    if not isinstance(
        state_data["characters"],
        dict,
    ):
        raise SaveDataError(
            "Save field 'characters' must be an object."
        )


def _deserialize_character_state(
    character_data: Any,
) -> CharacterState:
    """Convert serialized data into CharacterState."""
    if not isinstance(character_data, dict):
        raise SaveDataError(
            "Every saved character must be an object."
        )

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

        raise SaveDataError(
            "A saved character is missing field(s): "
            f"{formatted_fields}."
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

def _deserialize_decision_record(
    record_data: Any,
) -> DecisionRecord:
    """Convert serialized data into a DecisionRecord."""
    if not isinstance(record_data, dict):
        raise SaveDataError(
            "Every decision record must be an object."
        )

    required_fields = {
        "turn_number",
        "event_id",
        "event_title",
        "choice_id",
        "choice_text",
        "effects",
        "stat_changes",
    }

    missing_fields = required_fields - record_data.keys()

    if missing_fields:
        formatted_fields = ", ".join(
            sorted(missing_fields)
        )

        raise SaveDataError(
            "A decision record is missing field(s): "
            f"{formatted_fields}."
        )

    stat_changes_data = record_data["stat_changes"]

    if not isinstance(stat_changes_data, dict):
        raise SaveDataError(
            "Decision stat changes must be an object."
        )

    stat_changes: dict[str, tuple[int, int]] = {}

    for stat_name, values in stat_changes_data.items():
        if (
            not isinstance(values, list)
            or len(values) != 2
            or type(values[0]) is not int
            or type(values[1]) is not int
        ):
            raise SaveDataError(
                f"Invalid saved stat change "
                f"for '{stat_name}'."
            )

        stat_changes[stat_name] = (
            values[0],
            values[1],
        )

    character_changes = (
        _deserialize_character_changes(
            record_data["character_changes"]
        )
    )

    return DecisionRecord(
        turn_number=record_data["turn_number"],
        event_id=record_data["event_id"],
        event_title=record_data["event_title"],
        choice_id=record_data["choice_id"],
        choice_text=record_data["choice_text"],
        effects=dict(record_data["effects"]),
        stat_changes=stat_changes,
        character_changes=character_changes,
    )

def _deserialize_character_changes(
    changes_data: Any,
) -> dict[str, dict[str, tuple[int, int]]]:
    """Restore nested character relationship changes."""
    if not isinstance(changes_data, dict):
        raise SaveDataError(
            "Decision character changes must be an object."
        )

    character_changes: dict[
        str,
        dict[str, tuple[int, int]],
    ] = {}

    for character_id, relationship_data in changes_data.items():
        if not isinstance(relationship_data, dict):
            raise SaveDataError(
                "Saved relationship changes for "
                f"'{character_id}' must be an object."
            )

        character_changes[character_id] = {}

        for relationship_name, values in relationship_data.items():
            if (
                not isinstance(values, list)
                or len(values) != 2
                or type(values[0]) is not int
                or type(values[1]) is not int
            ):
                raise SaveDataError(
                    "Invalid saved relationship change "
                    f"for '{character_id}."
                    f"{relationship_name}'."
                )

            character_changes[character_id][
                relationship_name
            ] = (
                values[0],
                values[1],
            )

    return character_changes

def _deserialize_scheduled_consequence(
    consequence_data: Any,
) -> ScheduledConsequence:
    """Convert serialized data into a scheduled consequence."""
    if not isinstance(consequence_data, dict):
        raise SaveDataError(
            "Every scheduled consequence "
            "must be an object."
        )

    required_fields = {
        "id",
        "source_event_id",
        "source_choice_id",
        "due_turn",
        "title",
        "description",
        "effects",
    }

    missing_fields = (
        required_fields - consequence_data.keys()
    )

    if missing_fields:
        formatted_fields = ", ".join(
            sorted(missing_fields)
        )

        raise SaveDataError(
            "A scheduled consequence is missing "
            f"field(s): {formatted_fields}."
        )

    return ScheduledConsequence(
        id=consequence_data["id"],
        source_event_id=(
            consequence_data["source_event_id"]
        ),
        source_choice_id=(
            consequence_data["source_choice_id"]
        ),
        due_turn=consequence_data["due_turn"],
        title=consequence_data["title"],
        description=consequence_data["description"],
        effects=dict(consequence_data["effects"]),
    )


def _validate_loaded_state(
    state: GameState,
) -> None:
    """Validate the reconstructed GameState object."""
    if (
        not isinstance(state.player_name, str)
        or not state.player_name.strip()
    ):
        raise SaveDataError(
            "Saved player name must be a "
            "non-empty string."
        )

    if (
        type(state.current_turn) is not int
        or state.current_turn < 0
    ):
        raise SaveDataError(
            "Saved current turn must be "
            "a non-negative integer."
        )

    for stat_name in STAT_LABELS:
        value = getattr(state, stat_name)

        if (
            type(value) is not int
            or not 0 <= value <= 100
        ):
            raise SaveDataError(
                f"Saved statistic '{stat_name}' "
                f"must be an integer between 0 and 100."
            )

    if not all(
        isinstance(event_id, str)
        for event_id in state.completed_event_ids
    ):
        raise SaveDataError(
            "Completed event IDs must be strings."
        )

    if not all(
        isinstance(consequence_id, str)
        for consequence_id
        in state.resolved_consequence_ids
    ):
        raise SaveDataError(
            "Resolved consequence IDs "
            "must be strings."
        )

    for character_id, character in state.characters.items():
        if character.id != character_id:
            raise SaveDataError(
                f"Character key '{character_id}' does "
                "not match its internal ID."
            )

        for relationship_name in (
            "trust",
            "fear",
            "loyalty",
        ):
            value = getattr(
                character,
                relationship_name,
            )

            if (
                type(value) is not int
                or not 0 <= value <= 100
            ):
                raise SaveDataError(
                    f"Character '{character_id}' "
                    f"relationship '{relationship_name}' "
                    "must be between 0 and 100."
                )