"""
Game logic and event emission for golf_tumble_ways.

Structure copied directly from the CONFIRMED real games/0_0_ways/gamestate.py,
extended with the tumble mechanic from games/0_0_scatter/gamestate.py
(the tumble-inside-freespin while-loop pattern), combined with the ways-pays
evaluation instead of scatter-pays. This combination is not a stock sample
game — it's our own composition of two confirmed real patterns — so treat
it as needing real testing, not a guaranteed-correct copy.
"""
from game_override import GameStateOverride


class GameState(GameStateOverride):
    """Handle basegame and freegame logic."""

    def run_spin(self, sim: int, simulation_seed=None) -> None:
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board(emit_event=True)

            self.evaluate_ways_board()  # base game: no tumble multiplier applied
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()
        self.imprint_wins()

    def run_freespin(self) -> None:
        self.reset_fs_spin()
        while self.fs < self.tot_fs:
            self.update_freespin()
            self.draw_board(emit_event=True)

            self.evaluate_ways_board()  # first evaluation, global_multiplier == 1

            # Tumble loop: modeled on 0_0_scatter's pattern, using ways
            # evaluation instead of scatter evaluation.
            #
            # Safety limit added after a REAL observed hang: our reelstrips
            # are randomly generated (independent per-cell draws, see
            # reels/BR0.csv, FR0.csv), not curated like a real production
            # reelset, so hit-frequency is uncontrolled and can chain far
            # more tumbles than intended before a natural "no win" board
            # occurs. A single sim thread hung for minutes at 400x+ RTP.
            # This cap forces termination regardless of luck — treat this
            # as a scaffold safety valve, not a real design decision; once
            # reelstrips are properly curated for a sane hit-frequency,
            # this should rarely or never actually trigger.
            tumble_steps = 0
            max_tumble_steps = 20  # cut from 200 — 200 was being hit on
            # nearly every bonus sim (see the suspiciously uniform ~50.0x
            # results and the save-stage hang after bonus sims completed),
            # both signs our randomly-generated reelstrips have a much
            # higher win hit-frequency than intended. 20 is still a
            # scaffold safety valve, not a fix for the real cause — see
            # README bug #7/#8.
            while self.win_data["totalWin"] > 0 and not self.wincap_triggered:
                if tumble_steps >= max_tumble_steps:
                    break
                self.tumble_game_board()
                self.update_global_mult()  # +1 per tumble step (Birdie/Eagle/Albatross display labels), capped in game_override.py
                self.evaluate_ways_board()
                tumble_steps += 1

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

            self.win_manager.update_gametype_wins(self.gametype)
        self.end_freespin()
