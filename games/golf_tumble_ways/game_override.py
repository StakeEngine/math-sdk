"""
Game-specific overrides/extensions of universal state.py functions.

reset_book/reset_fs_spin pattern based on the CONFIRMED real
games/0_0_scatter/game_override.py.

assign_special_sym_function() below is now CONFIRMED required — real
games/0_0_ways/game_override.py showed it's an abstract method on the
base class, so every game must implement it or GameState can't even be
instantiated (this caused a real crash: "Can't instantiate abstract
class GameState without an implementation for..."). The real 0_0_ways
version uses it to attach a random multiplier VALUE onto the Wild symbol
itself (multiplier_strategy="symbol", pulling from mult_values in the
distribution config) — that's a DIFFERENT mechanic than ours. We're
using a global tumble counter instead (multiplier_strategy="global",
incremented via update_global_mult() in gamestate.py), so our symbols
don't need any special per-symbol function — this override is a
deliberate no-op, not a placeholder we forgot to fill in.
"""
from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """
    Used to override or extend universal state.py functions —
    e.g. game-specific book properties to reset each spin.
    """

    def assign_special_sym_function(self):
        """
        Required abstract override. This game's tumble multiplier is a
        global counter (see gamestate.py's update_global_mult() calls),
        not a per-symbol attribute, so no special symbol functions are
        needed here.
        """
        self.special_symbol_functions = {}

    def update_global_mult(self) -> None:
        """
        Override the base class's uncapped +1-per-tumble version.
        Confirmed real bug: without a cap, a single sim thread hung for
        minutes with RTP readings over 400x — runaway tumble chains
        before wincap_triggered caught it. Once global_multiplier hits
        config.max_tumble_multiplier, stop incrementing further (still
        lets the tumble loop continue/exit normally via win totals and
        wincap_triggered — this only stops the multiplier from growing
        without bound).
        """
        if self.global_multiplier < self.config.max_tumble_multiplier:
            super().update_global_mult()

    def reset_book(self):
        super().reset_book()
        self.tumble_win = 0
        # evaluate_ways_board() now always reads self.global_multiplier
        # (see game_executables.py), including in the base game where
        # reset_fs_spin() never runs — so it must exist here too, not
        # just in reset_fs_spin(). Base game always evaluates at 1x.
        self.global_multiplier = 1

    def reset_fs_spin(self):
        super().reset_fs_spin()
        self.global_multiplier = 1

    def check_game_repeat(self):
        """Verify final win matches required betmode conditions."""
        if self.repeat == False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
