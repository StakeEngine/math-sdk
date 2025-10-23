"""Handles the state and output for a single simulation round"""

from game_override import GameStateOverride
from src.events.events import *


class GameState(GameStateOverride):
    """Handle all game-logic and event updates for a given simulation number."""

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()

            win_data = {"totalWin": 0}
            if sim % 2 == 0:
                win_data["totalWin"] = 2
            self.win_manager.update_spinwin(win_data["totalWin"])
            self.win_manager.update_gametype_wins(self.gametype)

            game_event = {
                "index": len(self.book.events),
                "type": EventConstants.WIN_DATA.value,
                "numberRolled": int(sim + 1),
                "totalWin": int(round(win_data["totalWin"] * 100, 0)),
            }
            self.book.add_event(game_event)

            self.evaluate_finalwin()

        self.imprint_wins()

    def run_freespin(self):
        pass
