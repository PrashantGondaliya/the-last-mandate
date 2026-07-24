"""Faction effect processing for The Last Mandate."""

from app.models.game_state import GameState


FactionChanges = dict[
    str,
    dict[str, tuple[int, int]],
]


def apply_faction_effects(
    state: GameState,
    faction_effects: dict[str, dict[str, int]],
) -> FactionChanges:
    """Apply political effects to city factions."""
    applied_changes: FactionChanges = {}

    for faction_id, effects in faction_effects.items():
        faction = state.factions.get(faction_id)

        if faction is None:
            raise ValueError(
                f"Unknown faction ID: {faction_id}"
            )

        changes = faction.apply_effects(effects)

        if changes:
            applied_changes[faction_id] = changes

    return applied_changes