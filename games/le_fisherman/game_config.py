"""Le Fisherman game configuration file/setup"""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Singleton Le Fisherman game configuration class."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "le_fisherman"
        self.working_name = "Le Fisherman"
        self.wincap = 15000.0
        self.win_type = "cluster"
        self.rtp = 0.9633
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 6
        self.num_rows = [5] * 6

        # Board and Symbol Properties
        t1, t2, t3, t4 = (5, 7), (8, 11), (12, 17), (18, 30)
        pay_group = {
            (t1, "FISH"): 2.0,
            (t2, "FISH"): 5.0,
            (t3, "FISH"): 15.0,
            (t4, "FISH"): 50.0,
            (t1, "ANCHOR"): 1.5,
            (t2, "ANCHOR"): 4.0,
            (t3, "ANCHOR"): 10.0,
            (t4, "ANCHOR"): 40.0,
            (t1, "HOOK"): 1.2,
            (t2, "HOOK"): 3.0,
            (t3, "HOOK"): 8.0,
            (t4, "HOOK"): 30.0,
            (t1, "FLOAT"): 1.0,
            (t2, "FLOAT"): 2.5,
            (t3, "FLOAT"): 6.0,
            (t4, "FLOAT"): 25.0,
            (t1, "HAT"): 0.8,
            (t2, "HAT"): 2.0,
            (t3, "HAT"): 5.0,
            (t4, "HAT"): 20.0,
            (t1, "A"): 0.5,
            (t2, "A"): 1.5,
            (t3, "A"): 3.0,
            (t4, "A"): 10.0,
            (t1, "K"): 0.4,
            (t2, "K"): 1.2,
            (t3, "K"): 2.5,
            (t4, "K"): 8.0,
            (t1, "Q"): 0.3,
            (t2, "Q"): 1.0,
            (t3, "Q"): 2.0,
            (t4, "Q"): 6.0,
            (t1, "J"): 0.2,
            (t2, "J"): 0.8,
            (t3, "J"): 1.5,
            (t4, "J"): 5.0,
            (t1, "TEN"): 0.15,
            (t2, "TEN"): 0.6,
            (t3, "TEN"): 1.2,
            (t4, "TEN"): 4.0,
        }
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["SC"], "rainbow": ["RB"], "epic_rainbow": ["ERB"]}

        # Coin value distributions (weighted random)
        self.coin_values = {
            "CB": {0.2: 30, 0.5: 25, 1.0: 20, 2.0: 15, 4.0: 10},
            "CS": {5.0: 30, 8.0: 25, 10.0: 20, 15.0: 15, 20.0: 10},
            "CG": {25.0: 25, 40.0: 25, 50.0: 20, 75.0: 15, 100.0: 15},
            "CD": {150.0: 25, 200.0: 25, 300.0: 20, 400.0: 15, 500.0: 15},
        }

        # Clover multiplier distributions
        self.clover_values = {
            "CLG": {2: 30, 3: 25, 5: 20, 10: 15, 15: 7, 20: 3},
            "CLD": {2: 30, 3: 25, 5: 20, 10: 15, 15: 7, 20: 3},
        }

        # Freespin triggers
        self.freespin_triggers = {
            self.basegame_type: {3: 10, 4: 10, 5: 10},
            self.freegame_type: {3: 5, 4: 5, 5: 5},
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
        }

        # Bonus mode configuration
        self.bonus_modes = {
            3: {"name": "on_thin_ice", "bar_level": 0, "persistent_golden": False},
            4: {"name": "slippery_when_wet", "bar_level": 0, "persistent_golden": True},
            5: {"name": "smokey_under_water", "bar_level": 4, "persistent_golden": False},
        }

        # Big Catch Bar
        self.bar_levels = {
            0: {"reveal_pool": ["CB"]},
            1: {"reveal_pool": ["CB", "CLG"]},
            2: {"reveal_pool": ["CB", "CS", "CLG"]},
            3: {"reveal_pool": ["CB", "CS", "CG", "CLG", "CLD"]},
            4: {"reveal_pool": ["CB", "CS", "CG", "CD", "CLG", "CLD", "BK", "GBK"]},
        }
        self.bar_threshold = 5

        # Golden square reveal weights by bar level
        self.reveal_weights = {
            0: {"CB": 100},
            1: {"CB": 80, "CLG": 20},
            2: {"CB": 50, "CS": 30, "CLG": 20},
            3: {"CB": 30, "CS": 25, "CG": 15, "CLG": 15, "CLD": 15},
            4: {"CB": 20, "CS": 15, "CG": 12, "CD": 8, "CLG": 12, "CLD": 10, "BK": 15, "GBK": 8},
        }

        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "WCAP": "WCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))
        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FR0"]

        mode_maxwins = {"base": 15000, "bonus_hunt": 15000, "rainbow_trout": 15000, "rainbow_epic": 15000}

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
                                self.freegame_type: {"FR0": 1, "WCAP": 5},
                            },
                            "scatter_triggers": {3: 10, 4: 3, 5: 1},
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.08,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "scatter_triggers": {3: 10, 4: 3, 5: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.35,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.569,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            BetMode(
                name="bonus_hunt",
                cost=3.0,
                rtp=self.rtp,
                max_win=mode_maxwins["bonus_hunt"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=mode_maxwins["bonus_hunt"],
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "WCAP": 5},
                            },
                            "scatter_triggers": {3: 10, 4: 3, 5: 1},
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.999,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "scatter_triggers": {3: 10, 4: 3, 5: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
            BetMode(
                name="rainbow_trout",
                cost=50.0,
                rtp=self.rtp,
                max_win=mode_maxwins["rainbow_trout"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.002,
                        win_criteria=mode_maxwins["rainbow_trout"],
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "WCAP": 5},
                            },
                            "scatter_triggers": {4: 5, 5: 1},
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.998,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "scatter_triggers": {4: 5, 5: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
            BetMode(
                name="rainbow_epic",
                cost=500.0,
                rtp=self.rtp,
                max_win=mode_maxwins["rainbow_epic"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.005,
                        win_criteria=mode_maxwins["rainbow_epic"],
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "WCAP": 5},
                            },
                            "scatter_triggers": {5: 1},
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.995,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "scatter_triggers": {5: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
        ]
