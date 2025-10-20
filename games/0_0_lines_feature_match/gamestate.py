from game_override import GameStateOverride
from src.calculations.lines import Lines
from copy import deepcopy
import json


class GameState(GameStateOverride):
    """Handles game logic and events for a single simulation number/game-round."""

    def run_spin(self, sim, thread_index):
        if self.bonus_pays is None:
            self.bonus_pays = []
            with open("games/0_0_lines/library/lookup_tables/LookUpTable_bonus.csv", "r") as f:
                for line in f:
                    _, _, p = line.strip().split(",")
                    self.bonus_pays.append(int(p))
            with open("games/0_0_lines/library/lookup_tables/LookUpTableSegmented_bonus.csv", "r") as f:
                for line in f:
                    _, c, _, _ = line.strip().split(",")
                    self.bonus_criteria.append(c)

        sim_override = None
        if self.get_current_distribution_conditions()["force_wincap"]:
            sim_override = (thread_index + 1) * self.wincap_offset + self.wincap_index
            self.wincap_index += 1
        elif self.get_current_distribution_conditions()["force_freegame"]:
            sim_override = (thread_index + 1) * self.freegame_offset + self.freegame_index
            self.freegame_index += 1

        self.reset_seed(sim, sim_override)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board()

            # Evaluate wins, update wallet, transmit events
            self.evaluate_lines_board()

            self.win_manager.update_gametype_wins(self.gametype)
            if self.check_fs_condition():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()
        while self.fs < self.tot_fs:
            self.update_freespin()
            self.draw_board()

            self.evaluate_lines_board()

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

            self.win_manager.update_gametype_wins(self.gametype)

        self.end_freespin()
