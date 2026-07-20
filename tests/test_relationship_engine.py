"""Tests for character relationship processing."""

import pytest

from app.engine.relationship_engine import (
    apply_character_effects,
)
from app.models.character_state import CharacterState
from app.models.game_state import GameState


def build_state_with_character() -> GameState:
    """Create a state containing one test character."""
    character = CharacterState(
        id="test_character",
        name="Test Character",
        role="Tester",
        description="A character used in tests.",
        trust=50,
        fear=10,
        loyalty=60,
    )

    return GameState(
        player_name="Test Governor",
        characters={
            character.id: character,
        },
    )


def test_character_relationships_are_updated() -> None:
    """Relationship effects should update the character."""
    state = build_state_with_character()

    changes = apply_character_effects(
        state=state,
        character_effects={
            "test_character": {
                "trust": 8,
                "fear": -4,
            }
        },
    )

    character = state.characters["test_character"]

    assert character.trust == 58
    assert character.fear == 6

    assert changes == {
        "test_character": {
            "trust": (50, 58),
            "fear": (10, 6),
        }
    }


def test_character_relationships_are_clamped() -> None:
    """Relationship values must remain between 0 and 100."""
    state = build_state_with_character()

    apply_character_effects(
        state=state,
        character_effects={
            "test_character": {
                "trust": 100,
                "fear": -100,
            }
        },
    )

    character = state.characters["test_character"]

    assert character.trust == 100
    assert character.fear == 0


def test_unknown_character_is_rejected() -> None:
    """Unknown IDs should produce a useful error."""
    state = build_state_with_character()

    with pytest.raises(
        ValueError,
        match="Unknown character ID",
    ):
        apply_character_effects(
            state=state,
            character_effects={
                "missing_character": {
                    "trust": 5,
                }
            },
        )