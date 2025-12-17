"""Boringjob game calculations."""

from copy import deepcopy
from src.executables.executables import Executables
from src.calculations.scatter import Scatter


class GameCalculations(Executables):
    """Game specific calculations for boringjob."""

    def evaluate_symbol_wins(self):
        """Evaluate scatter-style symbol wins."""
        symbol_wins = Scatter.get_scatterpay_wins(
            self.config, self.board, global_multiplier=self.global_multiplier
        )
        return symbol_wins

    def record_symbol_wins(self, wins):
        """Record symbol wins for force files."""
        for win in wins:
            self.record(
                {
                    "kind": len(win["positions"]),
                    "symbol": win["symbol"],
                    "gametype": self.gametype,
                }
            )

    def get_bomb_wins(self):
        """Collect bomb payouts."""
        bomb_positions = []
        total = 0.0
        prize_value = self.get_current_distribution_conditions().get(
            "bomb_prize", {}
        ).get(self.gametype, self.config.default_bomb_prize)
        for reel, _ in enumerate(self.board):
            for row, _ in enumerate(self.board[reel]):
                if self.board[reel][row].check_attribute("bomb_value"):
                    bomb_value = self.board[reel][row].get_attribute("bomb_value")
                    total += bomb_value * prize_value * self.global_multiplier
                    bomb_positions.append(
                        {
                            "reel": reel,
                            "row": row,
                            "value": bomb_value,
                            "payout": bomb_value * prize_value * self.global_multiplier,
                        }
                    )
        wins = []
        if bomb_positions:
            wins.append(
                {
                    "symbol": "B",
                    "kind": len(bomb_positions),
                    "win": total,
                    "positions": bomb_positions,
                    "meta": {
                        "bombPrize": prize_value,
                        "globalMult": self.global_multiplier,
                        "winWithoutMult": sum(p["value"] * prize_value for p in bomb_positions),
                    },
                }
            )
        return {"wins": wins, "totalWin": total}

    def record_bomb_wins(self, wins):
        """Force record for bombs."""
        for win in wins:
            self.record(
                {
                    "bombs": len(win["positions"]),
                    "minValue": min(p["value"] for p in win["positions"]),
                    "maxValue": max(p["value"] for p in win["positions"]),
                    "gametype": self.gametype,
                }
            )

    def combine_win_data(self):
        """Combine scatter and bomb wins into a single response."""
        symbol_wins = self.evaluate_symbol_wins()
        bomb_wins = self.get_bomb_wins()

        combined = {
            "totalWin": symbol_wins["totalWin"] + bomb_wins["totalWin"],
            "wins": deepcopy(symbol_wins["wins"]) + deepcopy(bomb_wins["wins"]),
        }

        self.record_symbol_wins(symbol_wins["wins"])
        if bomb_wins["wins"]:
            self.record_bomb_wins(bomb_wins["wins"])

        return combined
