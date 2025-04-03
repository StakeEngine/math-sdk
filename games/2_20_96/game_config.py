from src.config.config import Config
from src.config.distributions import Distribution
from src.config.config import BetMode
from src.write_data.force import *


class GameConfig(Config):
    """Ninja Rabbit configuration class."""

    def __init__(self):
        super().__init__()
        self.game_id = "2_20_96"
        self.provider_number = 0
        self.working_name = "Ninja Rabbit"
        self.wincap = 10000
        self.win_type = "lines"
        self.rtp = 0.97
        self.construct_paths(self.game_id)

        # Game Dimensions
        self.num_reels = 5
        self.num_rows = [5] * self.num_reels  # 5 rows for Ninja Rabbit

        # Paylines - horizontal, diagonal, and custom patterns
        self.paylines = {
            1: [0, 0, 0, 0, 0],  # horizontal
            2: [1, 1, 1, 1, 1],
            3: [2, 2, 2, 2, 2],
            4: [3, 3, 3, 3, 3],
            5: [4, 4, 4, 4, 4],
            6: [0, 1, 0, 1, 0],  # W and M shaped
            7: [1, 2, 1, 2, 1],
            8: [2, 3, 2, 3, 2],
            9: [3, 4, 3, 4, 3],
            10: [1, 0, 1, 0, 1],  # Other diagonal and V shapes
            11: [2, 1, 2, 1, 2],
            12: [3, 2, 3, 2, 3],
            13: [4, 3, 4, 3, 4],
            14: [0, 1, 2, 3, 4],  # Diagonal
            15: [4, 3, 2, 1, 0],
        }

        # Board and Symbol Properties
        self.paytable = {
            (5, "WR"): 25,
            (4, "WR"): 15,
            (3, "WR"): 5,
            (5, "WC"): 25,
            (4, "WC"): 15,
            (3, "WC"): 5,
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

        # Adjust for Wild Rabbit and Wild Carrot Payouts
        self.symbols = ["L1", "L2", "L3", "L4", "L5", "H1", "H2", "H3", "H4", "WC", "S", "WR"]

        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(str.join("/", [self.reels_path, f]))

        self.padding_reels = {
            "basegame": self.reels["BR0"],
            "freegame": self.reels["FR0"],
        }

        # Feature and betmode settings
        self.include_padding = True
        self.special_symbols = {
            "wild": ["WR", "WC"],
            "scatter": ["S"],
            "multiplier": ["WR", "WC"],
        }

        # Updated freespin triggers for bonus1 and bonus2
        self.freespin_triggers = {
            self.basegame_type: {3: 10, 4: 10, 5: 10},  # Both bonus1 and bonus2 give 10 free spins
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
        }

        # Updated bet_modes section with bonus1, bonus2, ante, and feature_spin
        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    # Distribution(
                    #    criteria="wincap",
                    #    quota=0.001,
                    #    win_criteria=self.wincap,
                    #    conditions={
                    #        "reel_weights": {
                    #            self.basegame_type: {"BR0": 1},
                    #            self.freegame_type: {"FR0": 1},
                    #        },
                    #        "wr_mult_values": {
                    #            2: 100, 3: 80, 4: 40, 5: 30, 10: 10
                    #        },
                    #        "wc_mult_values": {
                    #            2: 100, 3: 50, 4: 30, 5: 20, 10: 5, 15: 5, 20: 1
                    #        },
                    #        "landing_wilds": {0: 100, 1: 20, 2: 5, 3: 2},
                    #        "scatter_triggers": {3: 10, 5: 1},
                    #        "force_wincap": True,
                    #        "force_freegame": True,
                    #    },
                    # ),
                    Distribution(
                        criteria="freegame",
                        quota=0.1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "wr_mult_values": {2: 200, 3: 100, 4: 50, 5: 30, 10: 10},
                            "wc_mult_values": {2: 150, 3: 75, 4: 35, 5: 25, 10: 10, 20: 5},
                            "landing_wilds": {0: 200, 1: 15, 2: 5, 3: 1},
                            "scatter_triggers": {3: 10, 5: 1},
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
                            "wr_mult_values": {2: 200, 3: 100, 4: 50, 5: 30, 10: 10},
                            "wc_mult_values": {2: 150, 3: 75, 4: 35, 5: 25, 10: 10, 20: 5},
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.5,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                            "wr_mult_values": {2: 200, 3: 100, 4: 50, 5: 30, 10: 10},
                            "wc_mult_values": {2: 150, 3: 75, 4: 35, 5: 25, 10: 10, 20: 5},
                        },
                    ),
                ],
            ),
            BetMode(
                name="bonus1",  # Renamed to bonus1
                cost=100.0,  # Correct cost for bonus1
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    # Distribution(
                    #    criteria="wincap",
                    #    quota=0.001,
                    #    win_criteria=self.wincap,
                    #    conditions={
                    #        "reel_weights": {
                    #            self.basegame_type: {"BR0": 1},
                    #            self.freegame_type: {"FR0": 1},
                    #        },
                    #        "wr_mult_values": {
                    #            2: 100, 3: 50, 4: 40, 5: 30, 10: 5
                    #        },
                    #        "wc_mult_values": {
                    #            2: 50, 3: 30, 4: 20, 5: 15, 10: 4, 20: 5
                    #        },
                    #        "landing_wilds": {0: 100, 1: 15, 2: 10, 3: 2},
                    #        "scatter_triggers": {3: 10, 5: 1},
                    #        "force_wincap": True,
                    #        "force_freegame": True,
                    #    },
                    # ),
                    Distribution(
                        criteria="freegame",
                        quota=0.1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "wr_mult_values": {2: 500, 3: 100, 4: 80, 5: 60, 10: 500},
                            "wc_mult_values": {2: 250, 3: 125, 4: 55, 5: 45, 10: 10, 20: 500},
                            "scatter_triggers": {3: 10, 5: 1},
                            "landing_wilds": {0: 200, 1: 20, 2: 5, 3: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
            BetMode(
                name="bonus2",  # Added bonus2
                cost=300.0,  # Correct cost for bonus2
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    # Distribution(
                    #    criteria="wincap",
                    #    quota=0.001,
                    #    win_criteria=self.wincap,
                    #    conditions={
                    #        "reel_weights": {
                    #            self.basegame_type: {"BR0": 1},
                    #            self.freegame_type: {"FR0": 1},
                    #        },
                    #        "wr_mult_values": {
                    #            2: 100, 3: 50, 4: 40, 5: 30, 10: 5
                    #        },
                    #        "wc_mult_values": {
                    #            2: 50, 3: 30, 4: 20, 5: 15, 10: 4, 20: 5
                    #        },
                    #        "landing_wilds": {0: 100, 1: 15, 2: 10, 3: 2},
                    #        "scatter_triggers": {3: 10, 5: 1},
                    #        "force_wincap": True,
                    #        "force_freegame": True,
                    #    },
                    # ),
                    Distribution(
                        criteria="freegame",
                        quota=0.1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "wr_mult_values": {2: 500, 3: 100, 4: 80, 5: 60, 10: 5000},
                            "wc_mult_values": {2: 250, 3: 125, 4: 55, 5: 45, 10: 10, 20: 5000},
                            "scatter_triggers": {3: 10, 5: 1},
                            "landing_wilds": {0: 200, 1: 20, 2: 5, 3: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
            BetMode(
                name="feature_spin",  # Added feature_spin
                cost=10.0,  # Adjusted cost for feature_spin
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="feature_spin",
                        quota=0.05,  # 5% chance for feature spins
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "landing_wilds": {0: 0, 1: 2, 2: 1},  # 2 WR symbols guaranteed in feature spin
                            "force_wincap": False,
                            "force_freegame": False,
                            "wr_mult_values": {2: 200, 3: 100, 4: 50, 5: 30, 10: 10},
                            "wc_mult_values": {2: 150, 3: 75, 4: 35, 5: 25, 10: 10, 20: 5},
                        },
                    ),
                ],
            ),
        ]
