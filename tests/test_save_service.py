"""Tests for game save and load operations."""

from pathlib import Path
from pathlib import Path

from app.models.character_state import CharacterState
from app.models.game_state import GameState
from app.services.save_service import load_game, save_game
import pytest
from app.models.character_state import CharacterState
from app.engine.consequence_engine import (
    schedule_choice_consequences,
)
from app.models.game_state import GameState
from app.services.save_service import (
    SaveDataError,
    autosave_exists,
    load_game,
    save_game,
)


def test_save_and_load_complete_game_state(
    tmp_path: Path,
    fresh_state: GameState,
    sample_event: dict,
) -> None:
    """A saved state should be reconstructed accurately."""
    save_path = tmp_path / "test_save.json"

    fresh_state.current_turn = 3
    choice = sample_event["choices"][0]

    changes = fresh_state.apply_effects(
        choice["effects"]
    )

    fresh_state.record_decision(
        turn_number=3,
        event=sample_event,
        choice=choice,
        stat_changes=changes,
    )

    delayed_choice = {
        "id": "delayed_choice",
        "delayed_consequences": [
            {
                "id": "future_problem",
                "delay_turns": 2,
                "title": "FUTURE PROBLEM",
                "description": "A pending consequence.",
                "effects": {
                    "unrest": 10,
                },
            }
        ],
    }

    schedule_choice_consequences(
        state=fresh_state,
        event={"id": "delayed_event"},
        choice=delayed_choice,
    )

    save_game(
        state=fresh_state,
        file_path=save_path,
    )

    loaded_state = load_game(
        file_path=save_path
    )

    assert autosave_exists(save_path)
    assert loaded_state.player_name == "Test Governor"
    assert loaded_state.current_turn == 3
    assert loaded_state.treasury == 60
    assert loaded_state.public_trust == 53

    assert loaded_state.completed_event_ids == {
        "test_crisis"
    }

    assert len(
        loaded_state.decision_history
    ) == 1

    loaded_record = (
        loaded_state.decision_history[0]
    )

    assert loaded_record.event_id == "test_crisis"
    assert loaded_record.choice_id == "test_choice"
    assert loaded_record.stat_changes == {
        "treasury": (65, 60),
        "public_trust": (50, 53),
    }

    assert len(
        loaded_state.scheduled_consequences
    ) == 1

    loaded_consequence = (
        loaded_state.scheduled_consequences[0]
    )

    assert loaded_consequence.due_turn == 5
    assert loaded_consequence.effects == {
        "unrest": 10
    }


def test_loading_missing_save_raises_error(
    tmp_path: Path,
) -> None:
    """Loading a nonexistent save should fail cleanly."""
    missing_path = tmp_path / "missing.json"

    with pytest.raises(
        SaveDataError,
        match="does not exist",
    ):
        load_game(
            file_path=missing_path
        )


def test_loading_invalid_json_raises_error(
    tmp_path: Path,
) -> None:
    """A corrupted save should produce a readable error."""
    save_path = tmp_path / "broken_save.json"

    save_path.write_text(
        '{"save_version": 1,',
        encoding="utf-8",
    )

    with pytest.raises(
        SaveDataError,
        match="Invalid JSON",
    ):
        load_game(
            file_path=save_path
        )

def test_character_relationships_survive_save_and_load(
    tmp_path: Path,
) -> None:
    """Character relationships should survive serialization."""
    save_path = tmp_path / "character_save.json"

    character = CharacterState(
        id="elena_voss",
        name="Elena Voss",
        role="Journalist",
        description="A test description.",
        trust=72,
        fear=14,
        loyalty=38,
    )

    state = GameState(
        player_name="Test Governor",
        characters={
            character.id: character,
        },
    )

    save_game(
        state=state,
        file_path=save_path,
    )

    loaded_state = load_game(
        file_path=save_path,
    )

    loaded_character = (
        loaded_state.characters["elena_voss"]
    )

    assert loaded_character.name == "Elena Voss"
    assert loaded_character.trust == 72
    assert loaded_character.fear == 14
    assert loaded_character.loyalty == 38

def test_decision_character_changes_survive_save_and_load(
            tmp_path: Path,
    ) -> None:
        """Character reactions in decision history should survive loading."""
        save_path = tmp_path / "decision_character_changes.json"

        character = CharacterState(
            id="elena_voss",
            name="Elena Voss",
            role="Journalist",
            description="A test character.",
            trust=45,
            fear=8,
            loyalty=25,
        )

        state = GameState(
            player_name="Test Governor",
            characters={
                character.id: character,
            },
        )

        event = {
            "id": "missing_report",
            "title": "THE MISSING REPORT",
        }

        choice = {
            "id": "defend_minister",
            "text": "Defend the minister.",
            "effects": {
                "public_trust": -8,
            },
        }

        stat_changes = state.apply_effects(
            choice["effects"]
        )

        character_changes = {
            "elena_voss": {
                "trust": (45, 30),
                "fear": (8, 13),
            }
        }

        state.record_decision(
            turn_number=3,
            event=event,
            choice=choice,
            stat_changes=stat_changes,
            character_changes=character_changes,
        )

        save_game(
            state=state,
            file_path=save_path,
        )

        loaded_state = load_game(
            file_path=save_path,
        )

        loaded_record = loaded_state.decision_history[0]

        assert loaded_record.character_changes == {
            "elena_voss": {
                "trust": (45, 30),
                "fear": (8, 13),
            }
        }