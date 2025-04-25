import random
from copy import deepcopy
from src.executables.executables import Executables
from src.calculations.statistics import get_random_outcome
from game_events import wild_expand_start_event, wild_multiplier_update_event


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
                    multiplier = get_random_outcome(
                        self.get_current_distribution_conditions()["wr_mult_values"]
                    )
                    self.board[reel][row].assign_attribute({"multiplier": multiplier})

                elif self.board[reel][row].name == "WC":
                    multiplier = get_random_outcome(
                        self.get_current_distribution_conditions()["wc_mult_values"]
                    )
                    self.board[reel][row].assign_attribute({"multiplier": multiplier})

    def expand_rabbits(self) -> None:
        """
        Expand all landed WR symbols upward, turning the reel into full WR.
        Collect and multiply any WC multipliers encountered on the way.
        """
        for reel, _ in enumerate(self.board):
            for row, _ in enumerate(self.board[reel]):
                if self.board[reel][row].name == "WR":
                    base_mult = self.board[reel][row].get_attribute("multiplier")
                    total_mult = base_mult

                    wild_expand_start_event(self, reel, row)
                    # Expand upward from the WR position to the top of the column
                    for r in range(row - 1, -1, -1):

                        if self.board[reel][r].name == "WC":
                            wc_mult = self.board[reel][r].get_attribute("multiplier")
                            if wc_mult > 1:
                                total_mult *= wc_mult

                                wild_multiplier_update_event(self, reel, r, total_mult)

                            # Replace symbol with WR and assign updated multiplier
                            self.board[reel][r] = self.create_symbol("WR")
                            self.board[reel][r].assign_attribute(
                                {"multiplier": total_mult}
                            )

                            # Update the multiplier of the original WR symbol as well
                            self.board[reel][row].assign_attribute(
                                {"multiplier": total_mult}
                            )

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
                        self.get_current_distribution_conditions()["wc_mult_values"][
                            self.gametype
                        ]
                    )
                    total_mult *= new_mult
                    symbol.assign_attribute({"multiplier": new_mult})

                self.board[reel][row] = self.create_symbol("WR")
                self.board[reel][row].assign_attribute({"multiplier": total_mult})

            updated_exp_wilds.append({"reel": reel, "row": 0, "mult": total_mult})

        self.expanding_wilds = updated_exp_wilds
