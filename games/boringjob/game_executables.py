"""Executables for boringjob."""

try:
    from game_calculations import GameCalculations
except ModuleNotFoundError:  # pragma: no cover - support package import
    from games.boringjob.game_calculations import GameCalculations
from src.events.events import win_info_event, set_win_event, set_total_event


class GameExecutables(GameCalculations):
    """Executable helpers for boringjob."""

    def evaluate_boringjob_board(self):
        """Compute wins for current board and emit core events."""
        self.win_data = self.combine_win_data()
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        if self.win_manager.spin_win > 0:
            win_info_event(self)
            self.evaluate_wincap()
            set_win_event(self)
        set_total_event(self)
