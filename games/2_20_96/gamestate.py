"""Handles the state and output for a single simulation round"""

from game_override import GameStateOverride
from src.calculations.lines import Lines
from src.events.events import update_freespin_event, reveal_event, set_total_event, set_win_event
from game_events import new_expanding_wild_event, update_expanding_wild_event, reveal_board_event
from src.calculations.statistics import get_random_outcome


class GameState(GameStateOverride):
    """Handle all game-logic and event updates for a given simulation number."""

    def run_spin(self, sim):
        """Entry point for all game-modes."""
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board(emit_event=True)

            self.reveal_multipliers()
            self.expand_rabbits()

            self.win_data = Lines.get_lines(self.board, self.config, global_multiplier=self.global_multiplier)
            Lines.record_lines_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
            Lines.emit_linewin_events(self)

            self.win_manager.update_gametype_wins(self.gametype)
            if self.check_fs_condition() and self.check_freespin_entry():
                if len(self.special_syms_on_board["scatter"]) in [3]:
                    self.regular_bonus = True
                elif len(self.special_syms_on_board["scatter"]) == 5:
                    self.super_bonus = True
                else:
                    self.repeat = True  # should only trigger on 3 or 5 scatters

                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        """Handles free spin rounds including sticky expanding wilds in bonus2."""
        self.reset_fs_spin()
        self.expanding_wilds = []
        self.avaliable_reels = [i for i in range(self.config.num_reels)]

        # Set flags for different bonus behavior
        self.bonus1 = self.betmode == "bonus1" or self.regular_bonus
        self.bonus2 = self.betmode == "bonus2" or self.super_bonus
        self.feature_spin = self.betmode == "feature_spin"

        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.draw_board(emit_event=False)

            wild_on_reveal = get_random_outcome(self.get_current_distribution_conditions()["landing_wilds"])

            if self.bonus2:
                self.update_with_sticky_rabbits()
            else:
                self.expanding_wilds = []

            self.reveal_multipliers()
            self.expand_rabbits()

            reveal_board_event(self)

            self.win_data = Lines.get_lines(self.board, self.config, global_multiplier=self.global_multiplier)

            Lines.record_lines_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
            Lines.emit_linewin_events(self)
            self.win_manager.update_gametype_wins(self.gametype)

        self.end_freespin()
