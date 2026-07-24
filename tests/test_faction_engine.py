"""Tests for faction state and faction effects."""

import pytest

from app.engine.faction_engine import (
    apply_faction_effects,
)
from app.models.faction_state import FactionState
from app.models.game_state import GameState


def build_state_with_faction() -> GameState:
    """Create a state containing one faction."""
    faction = FactionState(
        id="test_faction",
        name="Test Faction",
        description="A faction used by tests.",
        support=50,
        influence=60,
        hostility=20,
    )

    return GameState(
        player_name="Test Governor",
        factions={
            faction.id: faction,
        },
    )


def test_faction_effects_update_values() -> None:
    """Faction effects should update political values."""
    state = build_state_with_faction()

    changes = apply_faction_effects(
        state=state,
        faction_effects={
            "test_faction": {
                "support": 8,
                "hostility": -5,
            }
        },
    )

    faction = state.factions["test_faction"]

    assert faction.support == 58
    assert faction.hostility == 15

    assert changes == {
        "test_faction": {
            "support": (50, 58),
            "hostility": (20, 15),
        }
    }


def test_faction_values_are_clamped() -> None:
    """Faction values must remain between 0 and 100."""
    state = build_state_with_faction()

    apply_faction_effects(
        state=state,
        faction_effects={
            "test_faction": {
                "support": 100,
                "hostility": -100,
            }
        },
    )

    faction = state.factions["test_faction"]

    assert faction.support == 100
    assert faction.hostility == 0


def test_unknown_faction_is_rejected() -> None:
    """Unknown faction IDs should fail clearly."""
    state = build_state_with_faction()

    with pytest.raises(
        ValueError,
        match="Unknown faction ID",
    ):
        apply_faction_effects(
            state=state,
            faction_effects={
                "missing_faction": {
                    "support": 5,
                }
            },
        )