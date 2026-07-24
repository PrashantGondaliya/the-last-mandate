"""Faction state model for The Last Mandate."""

from dataclasses import dataclass


FACTION_STAT_LABELS = {
    "support": "Support",
    "influence": "Influence",
    "hostility": "Hostility",
}


@dataclass
class FactionState:
    """Store the political state of one city faction."""

    id: str
    name: str
    description: str
    support: int = 50
    influence: int = 50
    hostility: int = 10

    def apply_effects(
        self,
        effects: dict[str, int],
    ) -> dict[str, tuple[int, int]]:
        """Apply and return changes to faction statistics."""
        applied_changes: dict[str, tuple[int, int]] = {}

        for stat_name, amount in effects.items():
            if stat_name not in FACTION_STAT_LABELS:
                raise ValueError(
                    f"Unknown faction statistic: {stat_name}"
                )

            previous_value = getattr(
                self,
                stat_name,
            )

            updated_value = previous_value + amount
            updated_value = max(
                0,
                min(100, updated_value),
            )

            setattr(
                self,
                stat_name,
                updated_value,
            )

            applied_changes[stat_name] = (
                previous_value,
                updated_value,
            )

        return applied_changes