from game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome


class GameStateOverride(GameExecutables):

    def reset_book(self):
        super().reset_book()
        self.tumble_win = 0
        self.reset_golden_squares()
        self.reset_bar()
        self.bonus_mode_name = ""
        self.persistent_golden = False

    def reset_fs_spin(self):
        super().reset_fs_spin()
        # Golden squares: reset unless persistent mode
        if not self.persistent_golden:
            self.reset_golden_squares()
        # BAR STATE NEVER RESETS during bonus session

    def assign_special_sym_function(self):
        """Register coin and clover value assignment functions."""
        self.special_symbol_functions = {}
        # Coins get random prize values when created
        for coin_sym in ["CB", "CS", "CG", "CD"]:
            self.special_symbol_functions[coin_sym] = [
                lambda sym, cs=coin_sym: sym.assign_attribute(
                    {"prize": get_random_outcome(self.config.coin_values[cs])}
                )
            ]
        # Clovers get random multiplier values when created
        for clover_sym in ["CLG", "CLD"]:
            self.special_symbol_functions[clover_sym] = [
                lambda sym, cl=clover_sym: sym.assign_attribute(
                    {"multiplier": get_random_outcome(self.config.clover_values[cl])}
                )
            ]

    def check_repeat(self):
        """Check if simulation meets distribution criteria."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
            if self.get_current_distribution_conditions()["force_freegame"] and not self.triggered_freegame:
                self.repeat = True
            if self.win_manager.running_bet_win == 0 and self.criteria != "0":
                self.repeat = True
