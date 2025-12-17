"""Gamestate orchestration for boringjob."""

try:
    from game_override import GameStateOverride
except ModuleNotFoundError:  # pragma: no cover - support package import
    from games.boringjob.game_override import GameStateOverride


class GameState(GameStateOverride):
    """Handles game logic and events per simulation."""

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim, simulation_seed)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board()
            self.enforce_bomb_guarantee()

            self.evaluate_boringjob_board()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()
        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()
        while self.fs < self.tot_fs:
            self.update_freespin()
            self.draw_board()
            self.enforce_bomb_guarantee()
            self.evaluate_boringjob_board()

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

            self.win_manager.update_gametype_wins(self.gametype)

        self.end_freespin()
