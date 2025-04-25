import os.path
import random
from copy import deepcopy
from src.executables.executables import Executables
from src.calculations.statistics import get_random_outcome


class GameExecutables(Executables):
    """Game-specific executables for Ninja Rabbit."""

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        """Trigger the freespin function and update total fs amount."""
        self.record(
            {
                "kind": self.count_special_symbols(scatter_key),
                "symbol": scatter_key,
                "gametype": self.gametype,
            }
        )
        self.update_freespin_amount()
        self.run_freespin()

    def reveal_multipliers(self) -> None:
        """Assign multipliers to all WR and WC symbols on the board."""
        for reel, _ in enumerate(self.board):
            for row, _ in enumerate(self.board[reel]):

                if self.board[reel][row].name == "WR":
                    multiplier = get_random_outcome(self.get_current_distribution_conditions()["wr_mult_values"])
                    self.board[reel][row].assign_attribute({"multiplier": multiplier})

                elif self.board[reel][row].name == "WC":
                    multiplier = get_random_outcome(self.get_current_distribution_conditions()["wc_mult_values"])
                    self.board[reel][row].assign_attribute({"multiplier": multiplier})

    def expand_rabbits(self) -> None:
        """
        Expand all landed WR symbols upward, turning the reel into full WR.
        Collect and multiply any WC multipliers encountered on the way.
        """
        wr_positions = []
        for reel, _ in enumerate(self.board):
            for row, _ in enumerate(self.board[reel]):
                if self.board[reel][row].name == "WR":
                    base_mult = self.board[reel][row].get_attribute("multiplier")
                    total_mult = base_mult

                    # Expand upward from the WR position to the top of the column
                    for r in range(row - 1, -1, -1):

                        if self.board[reel][r].name == "WC":
                            wc_mult = self.board[reel][r].get_attribute("multiplier")
                            if wc_mult > 1:
                                total_mult *= wc_mult

                            # Replace symbol with WR and assign updated multiplier
                            self.board[reel][r] = self.create_symbol("WR")
                            self.board[reel][r].assign_attribute({"multiplier": total_mult})

                            # Update the multiplier of the original WR symbol as well
                            self.board[reel][row].assign_attribute({"multiplier": total_mult})

    def update_with_sticky_rabbits(self) -> None:
        """
        In Bonus 2: expand previously landed WRs upward again,
        collecting new WC multipliers and updating the WR's total multiplier.
        """
        updated_exp_wilds = []

        for rabbit in self.expanding_wilds:
            reel = rabbit["reel"]
            base_mult = rabbit["mult"]
            total_mult = base_mult

            # Expand whole reel from bottom to top
            for row in range(self.board.num_rows - 1, -1, -1):
                symbol = self.board[reel][row]

                if symbol.name == "WC":
                    new_mult = get_random_outcome(
                        self.get_current_distribution_conditions()["wc_mult_values"][self.gametype]
                    )
                    total_mult *= new_mult
                    symbol.assign_attribute({"multiplier": new_mult})

                self.board[reel][row] = self.create_symbol("WR")
                self.board[reel][row].assign_attribute({"multiplier": total_mult})

            updated_exp_wilds.append({"reel": reel, "row": 0, "mult": total_mult})

        self.expanding_wilds = updated_exp_wilds

    def assign_losing_weights(self):
        if self.modeName == "bonus1BattleOpposing":
            losingTable = os.path.join("games", self.gameName, "library", "lookUpTables", "lookUpTable_" + str(self.modeName) + "_0.csv")
            actualTable = os.path.join("games", self.gameName, "library", "lookUpTables", "lookUpTable_bonus1Battle_0.csv")
        elif self.modeName == "bonus2BattleOpposing":
            losingTable = os.path.join("games", self.gameName, "library", "lookUpTables", "lookUpTable_" + str(self.modeName) + "_0.csv")
            actualTable = os.path.join("games", self.gameName, "library", "lookUpTables", "lookUpTable_bonus2Battle_0.csv")

        lut1_weights = []
        lut1_pays = []
        lut_ids = []
        total_zero_weights = 0
        total_weight = 0
        with open(actualTable, "r") as f:
            for line in f:
                id1, w1, pay1 = line.strip().split(",")
                id1, w1, pay1 = int(id1), int(float(w1)), float(pay1)
                lut1_weights.append(w1)
                lut1_pays.append(pay1)
                lut_ids.append(id1)
                if pay1 == 0:
                    total_zero_weights += w1
                total_weight += w1

        first_rtp = 0.0
        for weight, pay in zip(lut1_weights, lut1_pays):
            first_rtp += (weight * pay) / total_weight / self.cost

        lut2_weights = []
        lut2_pays = []
        counter = 0
        total_losing_weights = 0
        with open(losingTable, "r") as f:
            for line in f:
                _, w2, pay2 = line.strip().split(",")
                w2, pay2 = int(w2), float(pay2)
                lut2_weights.append(w2)
                lut2_pays.append(pay2)
                if pay2 > 0:
                    total_losing_weights += w2 #contribution of weight from losing sims
                if lut2_pays[counter] > 0 and lut1_pays[counter] != 0:
                    raise RuntimeError("Pay Mismatch.")
                elif lut2_pays[counter] == 0 and lut1_pays[counter] == 0:
                    raise RuntimeError("Pay Mismatch")

                counter += 1

        new_total_weight = 0
        for idx, w in enumerate(lut1_weights):
            # Only alter non-paying values
            if lut1_pays[idx] == 0:
                lut1_weights[idx] = int(total_zero_weights * (lut2_weights[idx] / total_losing_weights))
            new_total_weight += w

        # Preform rtp check
        final_rtp = 0.0
        for weight, pay in zip(lut1_weights, lut1_pays):
            final_rtp += (weight * pay) / new_total_weight / self.cost

        if round(final_rtp, 2) != round(first_rtp, 2):
            raise RuntimeError("RTP Mismatch After Alteration.")
        # Swap weights
        with open(actualTable, "w") as f:
            for line in range(len(lut1_weights)):
                lne = str(lut_ids[line]) + "," + str(lut1_weights[line]) + "," + str(lut1_pays[line]) + "\n"
                f.write(lne)
