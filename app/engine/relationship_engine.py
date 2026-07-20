"""Character relationship processing for The Last Mandate."""

from app.models.game_state import GameState


CharacterChanges = dict[
    str,
    dict[str, tuple[int, int]],
]


def apply_character_effects(
    state: GameState,
    character_effects: dict[str, dict[str, int]],
) -> CharacterChanges:
    """Apply relationship effects to major characters."""
    applied_changes: CharacterChanges = {}

    for character_id, effects in character_effects.items():
        character = state.characters.get(character_id)

        if character is None:
            raise ValueError(
                f"Unknown character ID: {character_id}"
            )

        changes = character.apply_effects(effects)

        if changes:
            applied_changes[character_id] = changes

    return applied_changes