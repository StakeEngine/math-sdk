"""Overrides for boringjob gamestate."""

import random

try:
    from game_executables import GameExecutables
except ModuleNotFoundError:  # pragma: no cover - support package import
    from games.boringjob.game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome


class GameStateOverride(GameExecutables):
    """Override shared gamestate behaviors."""

    def reset_book(self):
        super().reset_book()
        self.bonus_type = None

    def assign_special_sym_function(self):
        """Assign bomb value attributes."""
        self.special_symbol_functions = {"B": [self.assign_bomb_property]}

    def assign_bomb_property(self, symbol):
        """Assign bomb multiplier value and prize configuration."""
        bomb_values = self.get_current_distribution_conditions().get("bomb_values", {})
        bomb_prize = self.get_current_distribution_conditions().get(
            "bomb_prize", {}
        ).get(self.gametype, self.config.default_bomb_prize)
        if bomb_values and self.gametype in bomb_values:
            bomb_value = get_random_outcome(bomb_values[self.gametype])
        else:
            bomb_value = self.config.mode_minimum_bombs.get(self.betmode, 0) or 0
        symbol.assign_attribute({"bomb_value": bomb_value})
        symbol.assign_attribute({"bomb_prize": bomb_prize})
        symbol.assign_attribute({"multiplier": bomb_value})

    def get_highest_bomb_value(self) -> float:
        """Return the highest bomb value on the active board."""
        highest = 0.0
        for reel, _ in enumerate(self.board):
            for row, _ in enumerate(self.board[reel]):
                if self.board[reel][row].check_attribute("bomb_value"):
                    highest = max(highest, float(self.board[reel][row].get_attribute("bomb_value")))
        return highest

    def enforce_bomb_guarantee(self):
        """Ensure modes that require minimum bomb values meet the constraint."""
        required = self.config.mode_minimum_bombs.get(self.betmode)
        if required is None:
            return
        current_high = self.get_highest_bomb_value()
        if current_high >= required:
            return
        self.inject_bomb(required)
        self.get_special_symbols_on_board()

    def inject_bomb(self, target_value: float):
        """Replace a random symbol with a bomb carrying at least the target value."""
        reel_index = random.randrange(0, self.config.num_reels)
        row_index = random.randrange(0, self.config.num_rows[reel_index])
        bomb_symbol = self.create_symbol("B")
        bomb_symbol.assign_attribute({"bomb_value": target_value, "multiplier": target_value})
        bomb_symbol.assign_attribute(
            {
                "bomb_prize": self.get_current_distribution_conditions()
                .get("bomb_prize", {})
                .get(self.gametype, self.config.default_bomb_prize)
            }
        )
        self.board[reel_index][row_index] = bomb_symbol

    def check_repeat(self):
        super().check_repeat()
        if not self.repeat:
            required = self.config.mode_minimum_bombs.get(self.betmode)
            if required is not None and self.get_highest_bomb_value() < required:
                self.repeat = True
