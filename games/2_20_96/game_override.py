from game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome


class GameStateOverride(GameExecutables):
    """
    This class is is used to override or extend universal state.py functions.
    e.g: A specific game may have custom book properties to reset
    """

    def reset_book(self):
        """Reset game specific properties"""
        super().reset_book()
        self.expanding_wilds = []
        self.avaliable_reels = [i for i in range(self.config.num_reels)]

    def assign_special_sym_function(self):
        self.special_symbol_functions = {"W": [self.assign_mult_property], "P": [self.assign_prize_value]}

    def assign_mult_property(self, symbol):
        """Only assign multiplier values in freegame"""
        if self.gametype != self.config.basegame_type:
            multiplier_value = get_random_outcome(
                self.get_current_distribution_conditions()["mult_values"][self.gametype]
            )
            symbol.assign_attribute({"multiplier": multiplier_value})

    def assign_prize_value(self, symbol):
        """Only assign multiplier values in freegame"""
        # if self.gametype != self.config.basegame_type:
        multiplier_value = get_random_outcome(self.get_current_distribution_conditions()["prize_values"])
        symbol.assign_attribute({"prize": multiplier_value})

    def check_repeat(self) -> None:
        """Checks if the spin failed a criteria constraint at any point."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

            if self.get_current_distribution_conditions()["force_freegame"] and not (self.triggered_freegame):
                self.repeat = True

            if self.win_manager.running_bet_win == 0.0 and self.criteria != "0":
                self.repeat = True

    def reset_superspin(self):
        self.tot_fs = 3
        self.fs = 0
        self.sticky_symbols = []
        self.existing_sticky_symbols = []
