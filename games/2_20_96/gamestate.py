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
        
    def run_feature_spin(self):
        # This needs to be updated to guarantee a feature, currently just copied run_spin logic over
        """Entry point for feature spins"""
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

    def run_bonus_battle(self, sim):
        self.resetSeed(sim)
        self.repeat = True
        while self.repeat:
            self.finalSetWin = False
            self.sim = sim  # Make sure to set this before resetBook, overwise every other id/sim number will be +1e6
            self.resetBook()
            self.reset_battle_book(sim)
            b1, b2 = {}, {}
            self.createBoardFromReelStrips()
            initWin = self.testClusterWins()  # ensure there are no winning boards when drawing battle symbols
            while (len(self.specialSymbolsOnBoard["battle"]) != self.config.numReels) or (initWin > 0):
                self.createBoardFromReelStrips()
                initWin = self.testClusterWins()

            # Reveal the board with 1 battle symbol on each reel
            reveal_board_event(self)

            self.run_battle_feature_from_base_game        ()
            bookStartCopy = self.book
            boardCopy = self.board
            preTriggerEvents = copy(self.book["events"])

            for i in range(2):
                if i == 0:
                    self.setup_new_battle_board(bookStartCopy, boardCopy)
                    self.gameType = "baseGame"
                    self.runSpin(
                        self.sim
                    )  # calls the main run-spin function in the gamestate as you normally would for a normal game-mode
                    b1["events"] = self.book["events"]
                    self.finalSetWin = True
                    setBaseWinEvent(self)
                    self.assign_final_win_amounts()
                    self.evaluateFinalWin()

                    if self.repeat:
                        raise RuntimeError("should not repeat after function exit")
                    if self.winCapTriggered:
                        self.battleWinCap[0] = True
                    b1["sim"] = sim + 1
                    b1["payout"] = self.finalWin
                    self.freeWins += b1["payout"]
                    assert self.triggeredFreeSpins == True
                elif i == 1:
                    self.setup_new_battle_board(bookStartCopy, boardCopy)
                    self.triggeredFreeSpins = False
                    self.winCapTriggered = False
                    self.fs = 0
                    self.gameType = "baseGame"
                    self.runSpin(deepcopy(self.sim + int(1e6)))
                    b2["events"] = deepcopy(self.book["events"])
                    self.finalSetWin = True
                    setBaseWinEvent(self)
                    self.assign_final_win_amounts()
                    self.evaluateFinalWin()

                    if self.repeat:
                        raise RuntimeError("should not repeat after function exit")
                    if self.winCapTriggered:
                        self.battleWinCap[1] = True
                    b2["sim"] = self.sim + int(1e6)
                    b2["payout"] = self.finalWin
                    self.freeWins += b2["payout"]
                    if not (self.repeat):
                        assert self.triggeredFreeSpins == True

            self.repeat = False
            self.book["events"] = deepcopy(preTriggerEvents)
            # Boards which tie should always result in the player winning, so are excluded from 0-criteria
            if self.inFence("0") and (b1["payout"] == b2["payout"]):
                self.repeat = True
            totalWin = 0

            if not (self.repeat):
                playerWon, totalWin, playersIndex, _, casinoWin = self.assign_battle_mode_wins(b1, b2)

                if b1["payout"] == b2["payout"]:
                    assert playerWon == True, "Payout mismatch error."

                self.opossingBattleResult = round(float(casinoWin), 1)
                self.battleResult = round(totalWin, 1)
                self.finalWin = round(totalWin, 1)
                self.runningBetWin = round(totalWin, 1)
                if totalWin != 0:
                    self.record(
                        {"kind": 1, "symbol": "battleWin", "hasWild": False, "mult": 1, "gameType": self.gameType}
                    )

                if totalWin < 2 * self.config.winCap and b1["payout"] == b2["payout"]:
                    self.record(
                        {"kind": 1, "symbol": "equalPayout", "hasWild": False, "mult": 1, "gameType": self.gameType}
                    )

                if self.inFence("0"):
                    assert self.finalWin == 0, "Non-Zero win awarded in 0 fence."

                # Enforce player result to always be the first response
                if playersIndex == 0:
                    self.book1Outcomes = b2
                    self.book2Outcomes = b1
                elif playersIndex == 1:
                    self.book1Outcomes = b1
                    self.book2Outcomes = b2

                dualBookEvent(self)
                displayBattleOutcomes(self)
                setBattleBaseWinEvent(self)

            self.checkBattleRepeat()

            if not (self.repeat) and playerWon and (self.book1Outcomes["payout"] > self.book2Outcomes["payout"]):
                raise RuntimeError("Player won. But book set 1 (bot) has larger payout")
            elif (
                not (self.repeat) and not (playerWon) and (self.book1Outcomes["payout"] < self.book2Outcomes["payout"])
            ):
                raise RuntimeError("Player lost. But book set 2 has larger payout")


    def run_battle_feature_from_base_game(self, startingWildNum=0):
        self.bonusType = "battleBonus"
        self.record(
        {
            "kind": self.getScatterAmount(),
            "symbol": "battleScatter",
            "hasWild": False,
            "mult": 1,
            "gameType": self.gameType,
        }
        )
        assert int(self.getScatterAmount()) == self.config.numReels, "Ensure one battle-symbol on every reel"
        self.updateTotalFreeSpinAmount()
        freeSpinTriggerEvent(self)
        if self.betMode == "bonus1Battle":
            self.bonusType = "bonus1"
        elif self.betMode == "bonus2Battle":
            self.bonusType = "bonus2"
        else:
            raise TypeError("Bonus Type Not Set")
        enterBonusEvent(self)
        self.gameType = "freeSpins"


    def assign_battle_mode_wins(self, book1, book2):
        bothWins = [book1["payout"], book2["payout"]]
        totalWin = 0
        playerWon = False
        # Assing player win if both books are equal
        if bothWins[0] == bothWins[1]:
            if self.inFence("0"):
                self.repeat = True
            else:
                totalWin = round(sum(bothWins), 1)
                playersIndex = random.choice([0, 1])
                self.book2Outcomes = book2
                self.book1Outcomes = book1
                playerWon = True
                playerWin = totalWin
                casinoWin = 0
                self.record({"kind": 1, "symbol": "battleWin", "hasWild": False, "mult": 1, "gameType": self.gameType})
                self.record(
                {"kind": 1, "symbol": "equalPayout", "hasWild": False, "mult": 1, "gameType": self.gameType}
                )
        else:
            if self.inFence("0"):
                playerWin, totalWin = 0, 0
                casinoWin = sum(bothWins)
                self.oppossingBattleResult = casinoWin
            else:
                playerWin, totalWin = sum(bothWins), sum(bothWins)
                casinoWin = 0

            if playerWin == 0:
                playerWon = False
                if min(bothWins) == bothWins[0]:
                    playersIndex = 0
                else:
                    playersIndex = 1
            elif playerWin > 0:
                playerWon = True
                if max(bothWins) == bothWins[1]:
                    playersIndex = 1
                else:
                    playersIndex = 0

        return playerWon, totalWin, playersIndex, playerWin, casinoWin


    def setup_new_battle_board(self, bookStartCopy, boardCopy):
        self.spinWin = 0
        self.runningBetWin = 0
        self.winCapTriggered = False
        self.board = deepcopy(boardCopy)
        self.book = deepcopy(bookStartCopy)
        self.book["events"] = []


    def assign_final_win_amounts(self):
        bookCopy = deepcopy(self.book)
        for e in range(len(bookCopy["events"]) - 1, -1, -1):
            if bookCopy["events"][e]["type"] == "reveal":
                bookCopy["events"][e]["accumulatedWinAmount"] = deepcopy(int(round(self.runningBetWin * 100, 0)))
                bookCopy["events"][e]["winAmount"] = deepcopy(int(round(self.setSpinWin * 100, 0)))
                break
        self.book = deepcopy(bookCopy)


    def reset_battle_book(self, sim):
        self.startSim = sim
        self.baseWin = 0
        self.setSpinWin = 0
        self.inBattleBonus = True
        self.battleWinCap = [False, False]
        self.initWildPositions = [[], []]
        self.gameType = "battleSetup"
