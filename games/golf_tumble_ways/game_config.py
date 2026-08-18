"""
GameConfig for "Hole-In-One" (working title)
Ways Pays + Tumble/Cascade with a global tumble multiplier, golf theme.

Rewritten against CONFIRMED real source from:
- games/0_0_ways/game_config.py (BetMode/Distribution shape, construct_paths,
  named reelset loading via read_reels_csv)
- src/calculations/ways.py (get_ways_data signature: global_multiplier +
  multiplier_strategy params)

Design confirmed against real SDK behavior:
- Scatter pays are NOT supported alongside ways win_type in the standard
  pattern (0_0_ways evaluates only via evaluate_ways_board(), scatter is
  trigger-only). We follow that: scatter triggers free spins, no direct
  scatter payout. (See README for full reasoning.)
- The tumble multiplier is a simple +1-per-tumble-step global_multiplier
  (confirmed via src/executables/executables.py: update_global_mult just
  does self.global_multiplier += 1), NOT a lookup tier table like the
  original placeholder assumed. Golf terms (Birdie/Eagle/Albatross) are
  applied as display labels for whatever the current multiplier value is,
  not a different underlying mechanic.

*** Paytable values are the tuned numbers from tune_rtp_sim.py (~94% RTP
estimate, see README for volatility caveats) — still need re-validation
against the real SDK's own simulation output. ***
"""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Game specific configuration class."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "golf_tumble_ways"
        self.provider_number = 0
        self.working_name = "Hole-In-One"
        self.wincap = 5000
        self.win_type = "ways"
        self.rtp = 0.94  # per tune_rtp_sim.py Monte Carlo pass — re-verify against real sims
        self.construct_paths()

        # --- Game Dimensions ---
        self.num_reels = 5
        self.num_rows = [4] * self.num_reels

        # --- Paytable (tuned via tune_rtp_sim.py, factor 1.22 applied) ---
        self.paytable = {
            (5, "H1"): 0.732,  # Trophy
            (4, "H1"): 0.305,
            (3, "H1"): 0.098,
            (5, "H2"): 0.488,  # Golfer
            (4, "H2"): 0.195,
            (3, "H2"): 0.061,
            (5, "H3"): 0.342,  # Clubhouse
            (4, "H3"): 0.134,
            (3, "H3"): 0.043,
            (5, "H4"): 0.244,  # Golf Bag
            (4, "H4"): 0.098,
            (3, "H4"): 0.030,
            (5, "L1"): 0.146,  # Golf Ball
            (4, "L1"): 0.055,
            (3, "L1"): 0.018,
            (5, "L2"): 0.122,  # Tee
            (4, "L2"): 0.043,
            (3, "L2"): 0.015,
            (5, "L3"): 0.098,  # Glove
            (4, "L3"): 0.034,
            (3, "L3"): 0.012,
            (5, "L4"): 0.073,  # Cap
            (4, "L4"): 0.027,
            (3, "L4"): 0.010,
            (5, "W"): 0.976,   # Eagle Wild
            (4, "W"): 0.390,
            (3, "W"): 0.122,
        }
        # NOTE: dropped separate scatter (5,"S")/(4,"S")/(3,"S") payout
        # entries — confirmed scatter is trigger-only in the standard ways
        # pattern (0_0_ways), not directly paying. "S" is still a valid
        # symbol, just has no paytable entry, matching that pattern.

        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["S"], "multiplier": []}

        # Hard cap on the tumble multiplier. Real update_global_mult() in
        # the base SDK just does self.global_multiplier += 1 every tumble
        # step with NO cap — left uncapped, this caused a real observed
        # bug: a single sim thread hung for minutes at 400x+ RTP, almost
        # certainly runaway tumble chains where wins never fully clear
        # before wincap_triggered kicks in. See game_override.py for the
        # actual enforcement (this is just the config value).
        self.max_tumble_multiplier = 100

        # --- Freespin triggers: confirmed real dict shape from 0_0_ways ---
        self.freespin_triggers = {
            self.basegame_type: {3: 8, 4: 12, 5: 20},
            self.freegame_type: {3: 5, 4: 8, 5: 12},  # retrigger amounts
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 1}

        # --- Reelstrips: confirmed real loading pattern (named sets via CSV) ---
        # ⚠️ These CSV files are still tiny placeholders (see config/ folder)
        # — need to be rebuilt as long, properly weighted strips using the
        # relative weights below before real tuning is meaningful.
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        self.relative_symbol_weights = {
            "BR0": {
                "H1": 2, "H2": 3, "H3": 4, "H4": 5,
                "L1": 10, "L2": 11, "L3": 12, "L4": 13,
                "W": 1, "S": 1,
            },
            "FR0": {
                "H1": 2, "H2": 3, "H3": 4, "H4": 5,
                "L1": 9, "L2": 10, "L3": 11, "L4": 12,
                "W": 2, "S": 2,
            },
        }

        mode_maxwins = {"base": 5000, "bonus": 5000}

        # --- Bet modes: confirmed real BetMode/Distribution shape ---
        # ⚠️ Distribution quotas/conditions below are placeholders modeled
        # on 0_0_ways's shape, NOT tuned — real quotas need to come from
        # actual simulation + optimization against this game's math.
        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=mode_maxwins["base"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=mode_maxwins["base"],
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": True,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 20, 5: 5},
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": False,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 20, 5: 5},
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.4,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.5,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            BetMode(
                name="bonus",
                cost=100.0,
                rtp=self.rtp,
                max_win=mode_maxwins["bonus"],
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="freegame",
                        quota=1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": False,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 20, 5: 5},
                        },
                    ),
                ],
            ),
        ]
