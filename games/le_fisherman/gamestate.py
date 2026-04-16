from game_override import GameStateOverride
from game_events import golden_square_update_event, bonus_mode_enter_event


class GameState(GameStateOverride):

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board()

            # Evaluate clusters with Super Cascade
            self.get_clusters_update_wins_super()
            self.emit_tumble_win_events()

            # Super Cascade tumble loop
            while self.win_data["totalWin"] > 0 and not self.wincap_triggered:
                self.tumble_game_board()
                self.get_clusters_update_wins_super()
                self.emit_tumble_win_events()

            # Process Rainbow AFTER tumble chain ends
            self.process_rainbow_on_board()
            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            # Check for bonus trigger
            if self.check_fs_condition() and self.check_freespin_entry():
                scatter_count = self.count_special_symbols("scatter")
                self.determine_bonus_mode(scatter_count)
                bonus_mode_enter_event(self)
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()

        while self.fs < self.tot_fs:
            self.update_freespin()
            self.draw_board()
            golden_square_update_event(self)

            # Evaluate clusters with Super Cascade
            self.get_clusters_update_wins_super()
            self.emit_tumble_win_events()

            # Super Cascade tumble loop with golden square tracking
            while self.win_data["totalWin"] > 0 and not self.wincap_triggered:
                self.tumble_game_board()
                self.get_clusters_update_wins_super()
                self.emit_tumble_win_events()

            # Process Rainbow AFTER tumble chain ends
            self.process_rainbow_on_board()
            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            # Update Big Catch Bar with scatters
            self.update_bar_on_scatter()

            # Check retrigger
            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

        self.end_freespin()
