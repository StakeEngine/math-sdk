"""Template game configuration file, detailing required user-specified inputs."""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Template configuration class."""

    def __init__(self):
        super().__init__()
        self.game_id = "0_0_expwilds"
        self.provider_numer = 0
        self.working_name = "Expanding Wilds"
        self.wincap = 5000
        self.win_type = "lines"
        self.rtp = 0.97
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 5
        self.num_rows = [5] * self.num_reels  # Optionally include variable number of rows per reel
        # Board and Symbol Properties
        self.paytable = {
            (5, "W"): 20,
            (4, "W"): 10,
            (3, "W"): 5,
            (5, "H1"): 20,
            (4, "H1"): 10,
            (3, "H1"): 5,
            (5, "H2"): 15,
            (4, "H2"): 5,
            (3, "H2"): 3,
            (5, "H3"): 10,
            (4, "H3"): 3,
            (3, "H3"): 2,
            (5, "H4"): 8,
            (4, "H4"): 2,
            (3, "H4"): 1,
            (5, "L1"): 5,
            (4, "L1"): 1,
            (3, "L1"): 0.5,
            (5, "L2"): 3,
            (4, "L2"): 0.7,
            (3, "L2"): 0.3,
            (5, "L3"): 3,
            (4, "L3"): 0.7,
            (3, "L3"): 0.3,
            (5, "L4"): 2,
            (4, "L4"): 0.5,
            (3, "L4"): 0.2,
            (5, "L5"): 2,
            (4, "L5"): 0.5,
            (3, "L5"): 0.2,
            (99, "X"): 0,  # only included for symbol register
        }
        self.paylines = {
            # horizontal lines
            1: [0, 0, 0, 0, 0],
            2: [1, 1, 1, 1, 1],
            3: [2, 2, 2, 2, 2],
            4: [3, 3, 3, 3, 3],
            5: [4, 4, 4, 4, 4],
            # W and M shaped lines
            6: [0, 1, 0, 1, 0],
            7: [1, 2, 1, 2, 1],
            8: [2, 3, 2, 3, 2],
            9: [3, 4, 3, 4, 3],
            10: [1, 0, 1, 0, 1],
            11: [2, 1, 2, 1, 2],
            12: [3, 2, 3, 2, 3],
            13: [4, 3, 4, 3, 4],
            # diagonal lines
            14: [0, 1, 2, 3, 4],
            15: [4, 3, 2, 1, 0],
        }
        self.include_padding = True
        self.special_symbols = {
            "wild": ["W"],
            "scatter": ["S"],
            "multiplier": ["W"],
            "prize": ["P"],
        }

        self.freespin_triggers = {self.basegame_type: {3: 8, 4: 12, 5: 15}}  # No retriggers in freegame
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
        }
        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "SSR": "SSR.csv", "SSWCAP": "SSWCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        self.padding_reels = {
            "basegame": self.reels["BR0"],
            "freegame": self.reels["FR0"],
            "superspin": self.reels["SSR"],
        }
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
                                self.freegame_type: {"FR0": 1},
                            },
                            "mult_values": {
                                self.freegame_type: {2: 200, 3: 80, 4: 40, 5: 30, 10: 10, 20: 5, 50: 1}
                            },
                            "landing_wilds": {0: 100, 1: 20, 2: 5, 3: 2},
                            "scatter_triggers": {4: 1, 5: 2},
                            "force_wincap": True,
                            "force_freegame": True,
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
                            "mult_values": {
                                self.freegame_type: {2: 300, 3: 100, 4: 30, 5: 20, 10: 5, 20: 5, 50: 1}
                            },
                            "landing_wilds": {0: 200, 1: 15, 2: 5, 3: 1},
                            "scatter_triggers": {4: 1, 5: 2},
                            "force_wincap": False,
                            "force_freegame": True,
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
                cost=200.0,
                rtp=self.rtp,
                max_win=mode_maxwins["bonus"],
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=mode_maxwins["bonus"],
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "mult_values": {
                                self.freegame_type: {2: 100, 3: 50, 4: 40, 5: 30, 10: 5, 20: 5, 50: 1}
                            },
                            "landing_wilds": {0: 100, 1: 15, 2: 10, 3: 2},
                            "scatter_triggers": {4: 1, 5: 2},
                            "force_wincap": True,
                            "force_freegame": True,
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
                            "mult_values": {
                                self.freegame_type: {2: 500, 3: 100, 4: 80, 5: 60, 10: 5, 20: 2, 50: 1}
                            },
                            "scatter_triggers": {4: 1, 5: 2},
                            "landing_wilds": {0: 200, 1: 20, 2: 5, 3: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
            BetMode(
                name="superspin",
                cost=50,
                rtp=self.rtp,
                max_win=mode_maxwins["superspin"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=mode_maxwins["superspin"],
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"SSR": 1, "SSWCAP": 5},
                            },
                            "prize_values": {
                                1: 10,
                                2: 20,
                                3: 50,
                                5: 50,
                                10: 50,
                                25: 80,
                                50: 30,
                                100: 20,
                                500: 5,
                                10000: 4,
                            },
                            "force_wincap": True,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.1,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"SSR": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                            "prize_values": {
                                1: 500,
                            },
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.9,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"SSR": 1},
                            },
                            "prize_values": {
                                1: 700,
                                2: 200,
                                3: 50,
                                5: 30,
                                10: 20,
                                25: 10,
                                50: 5,
                                100: 5,
                                500: 2,
                                1000: 1,
                            },
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
        ]
