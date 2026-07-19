"""Shared pytest fixtures for The Last Mandate tests."""

import pytest

from app.models.game_state import GameState


@pytest.fixture
def fresh_state() -> GameState:
    """Return a new game state for each test."""
    return GameState(player_name="Test Governor")


@pytest.fixture
def sample_event() -> dict:
    """Return a small valid event for testing."""
    return {
        "id": "test_crisis",
        "order": 10,
        "title": "TEST CRISIS",
        "description": "A crisis created for automated testing.",
        "conditions": [],
        "choices": [
            {
                "id": "test_choice",
                "text": "Take the test action.",
                "outcome": "The test action is completed.",
                "effects": {
                    "treasury": -5,
                    "public_trust": 3,
                },
            }
        ],
    }