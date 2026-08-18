"""
Game-specific executable functions.

evaluate_ways_board() here is DELIBERATELY DIFFERENT from the real
games/0_0_ways/game_executables.py version — that version calls
Ways.get_ways_data(self.config, self.board) with no multiplier args, which
means it never applies self.global_multiplier.

We override it to pass global_multiplier=self.global_multiplier and
multiplier_strategy="global", both of which are CONFIRMED real parameters
on src/calculations/ways.py's get_ways_data() (verified directly from
source — see README). This is what actually wires our tumble multiplier
into the ways win calculation instead of it silently doing nothing.
"""
from game_calculations import GameCalculations
from src.calculations.ways import Ways


class GameExecutables(GameCalculations):
    """Events specific to 'ways' wins, extended with global tumble multiplier."""

    def evaluate_ways_board(self):
        """Populate win-data, record wins, transmit events."""
        self.win_data = Ways.get_ways_data(
            self.config,
            self.board,
            global_multiplier=self.global_multiplier,
            multiplier_strategy="global",
        )
        if self.win_data["totalWin"] > 0:
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
        Ways.emit_wayswin_events(self)
