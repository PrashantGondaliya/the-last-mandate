"""Game state model for The Last Mandate."""

from dataclasses import dataclass


STAT_LABELS = {
    "treasury": "Treasury Reserves",
    "public_trust": "Public Trust",
    "unrest": "Public Unrest",
    "infrastructure": "Infrastructure",
    "authority": "Government Authority",
    "business_confidence": "Business Confidence",
}


@dataclass
class GameState:
    """Store the current condition of the city."""

    player_name: str
    treasury: int = 65
    public_trust: int = 50
    unrest: int = 25
    infrastructure: int = 45
    authority: int = 50
    business_confidence: int = 50

    def apply_effects(
        self,
        effects: dict[str, int],
    ) -> dict[str, tuple[int, int]]:
        """
        Apply decision effects to the city statistics.

        Returns a dictionary containing the previous and updated value
        for every statistic that changed.
        """
        applied_changes: dict[str, tuple[int, int]] = {}

        for stat_name, amount in effects.items():
            if stat_name not in STAT_LABELS:
                raise ValueError(f"Unknown city statistic: {stat_name}")

            previous_value = getattr(self, stat_name)
            updated_value = previous_value + amount

            updated_value = max(0, min(100, updated_value))

            setattr(self, stat_name, updated_value)

            applied_changes[stat_name] = (
                previous_value,
                updated_value,
            )

        return applied_changes