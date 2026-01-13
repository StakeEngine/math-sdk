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
        self.game_id = "0_0_ways"
        self.provider_number = 0
        self.working_name = "sample ways game"
        self.wincap = 5000
        self.win_type = "ways"
        self.rtp = 0.97
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 5
        self.num_rows = [3] * self.num_reels  # Optionally include variable number of rows per reel
        # Board and Symbol Properties
        self.paytable = {
            (5, "H1"): 10,
            (4, "H1"): 5,
            (3, "H1"): 3,
            (5, "H2"): 8,
            (4, "H2"): 4,
            (3, "H2"): 2,
            (5, "H3"): 5,
            (4, "H3"): 2,
            (3, "H3"): 1,
            (5, "H4"): 3,
            (4, "H4"): 1,
            (3, "H4"): 0.5,
            (5, "H5"): 2,
            (4, "H5"): 0.8,
            (3, "H5"): 0.4,
            (5, "L1"): 2,
            (4, "L1"): 0.8,
            (3, "L1"): 0.4,
            (5, "L2"): 1.5,
            (4, "L2"): 0.5,
            (3, "L2"): 0.2,
            (5, "L3"): 1.5,
            (4, "L3"): 0.5,
            (3, "L3"): 0.2,
            (5, "L4"): 1,
            (4, "L4"): 0.3,
            (3, "L4"): 0.1,
        }

        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["S"], "multiplier": []}

        self.freespin_triggers = {
            self.basegame_type: {3: 10, 4: 15, 5: 20},
            self.freegame_type: {2: 4, 3: 6, 4: 8, 5: 10},
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 1}
        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "FRWCAP": "FRWCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        mode_maxwins = {"base": 5000, "bonus": 5000, "superspin": 2000}

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
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_wincap": True,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 20, 5: 5},
                            "mult_values": {1: 20, 2: 50, 3: 80, 4: 100, 5: 20},
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
                            "mult_values": {1: 200, 2: 100, 3: 80, 4: 50, 5: 20},
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
                            "mult_values": {1: 1},
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.5,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                            "mult_values": {1: 1},
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
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_wincap": False,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 20, 5: 5},
                            "mult_values": {1: 20, 2: 100, 3: 80, 4: 90, 5: 80},
                        },
                    ),
                ],
            ),
        ]
