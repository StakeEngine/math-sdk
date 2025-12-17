"""Configuration for boringjob."""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """boringjob configuration class."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "boringjob"
        self.game_name = "boringjob"
        self.provider_number = 0
        self.working_name = "boringjob"
        self.wincap = 5000.0
        self.win_type = "scatter"
        self.rtp = 0.965
        self.construct_paths()

        # Board setup
        self.num_reels = 6
        self.num_rows = [5] * self.num_reels

        # Paytable
        t1, t2, t3, t4 = (6, 6), (7, 8), (9, 11), (12, 15)
        pay_group = {
            (t1, "H1"): 4.0,
            (t2, "H1"): 10.0,
            (t3, "H1"): 22.0,
            (t4, "H1"): 70.0,
            (t1, "H2"): 3.0,
            (t2, "H2"): 8.0,
            (t3, "H2"): 18.0,
            (t4, "H2"): 60.0,
            (t1, "H3"): 2.0,
            (t2, "H3"): 6.0,
            (t3, "H3"): 15.0,
            (t4, "H3"): 45.0,
            (t1, "H4"): 1.5,
            (t2, "H4"): 5.0,
            (t3, "H4"): 12.0,
            (t4, "H4"): 30.0,
            (t1, "L1"): 1.0,
            (t2, "L1"): 2.5,
            (t3, "L1"): 6.0,
            (t4, "L1"): 18.0,
            (t1, "L2"): 0.8,
            (t2, "L2"): 2.0,
            (t3, "L2"): 5.0,
            (t4, "L2"): 14.0,
            (t1, "L3"): 0.5,
            (t2, "L3"): 1.5,
            (t3, "L3"): 4.0,
            (t4, "L3"): 12.0,
        }
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        self.special_symbols = {"wild": [], "scatter": ["S"], "bomb": ["B"], "multiplier": ["B"]}

        self.freespin_triggers = {
            self.basegame_type: {3: 8, 4: 12, 5: 16, 6: 20},
            self.freegame_type: {3: 5, 4: 8, 5: 10, 6: 12},
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
        }

        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "BW0": "BW0.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FR0"]

        # Bomb defaults
        self.default_bomb_prize = 0.4
        self.mode_minimum_bombs = {
            "min_one_x10": 10,
            "min_one_x100": 100,
            "min_one_x1000": 1000,
        }

        base_bomb_values = {
            self.basegame_type: {2: 30, 5: 25, 10: 20, 25: 10, 50: 8, 100: 5, 250: 2},
            self.freegame_type: {5: 25, 10: 20, 25: 15, 50: 10, 100: 6, 250: 3, 500: 2, 1000: 1},
        }
        boosted_bomb_values = {
            self.basegame_type: {5: 25, 10: 20, 25: 15, 50: 10, 100: 8, 250: 4},
            self.freegame_type: {10: 25, 25: 18, 50: 12, 100: 8, 250: 4, 500: 3, 1000: 2},
        }
        no_small_bomb_values = {
            self.basegame_type: {10: 25, 25: 18, 50: 12, 100: 8, 250: 5, 500: 2},
            self.freegame_type: {25: 24, 50: 18, 100: 12, 250: 8, 500: 4, 1000: 2},
        }
        min_ten_values = {
            self.basegame_type: {10: 30, 25: 18, 50: 12, 100: 8, 250: 5},
            self.freegame_type: {10: 28, 25: 18, 50: 12, 100: 10, 250: 6, 500: 3},
        }
        min_hundred_values = {
            self.basegame_type: {100: 28, 250: 16, 500: 10, 750: 6, 1000: 4},
            self.freegame_type: {100: 24, 250: 18, 500: 12, 750: 8, 1000: 6, 1500: 2},
        }
        min_thousand_values = {
            self.basegame_type: {1000: 24, 1500: 12, 2000: 6, 2500: 4},
            self.freegame_type: {1000: 20, 1500: 12, 2000: 8, 2500: 6, 3000: 4},
        }
        wincap_bomb_values = {
            self.basegame_type: {750: 12, 1000: 10, 1500: 8, 2000: 6, 3000: 4, 4000: 2, 7000: 1},
            self.freegame_type: {1000: 12, 1500: 10, 2000: 8, 3000: 6, 4000: 4, 5000: 2, 7000: 1},
        }

        base_bomb_prize = {self.basegame_type: 0.35, self.freegame_type: 0.55}
        boosted_bomb_prize = {self.basegame_type: 0.4, self.freegame_type: 0.6}
        high_bomb_prize = {self.basegame_type: 0.45, self.freegame_type: 0.65}
        extreme_bomb_prize = {self.basegame_type: 0.5, self.freegame_type: 0.75}

        common_scatter = {3: 1, 4: 2, 5: 2, 6: 1}

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
                    Distribution(
                        criteria="wincap",
                        quota=0.01,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1, "BW0": 2},
                                self.freegame_type: {"FR0": 1, "BW0": 3},
                            },
                            "scatter_triggers": common_scatter,
                            "bomb_values": wincap_bomb_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.1,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                            "scatter_triggers": common_scatter,
                            "bomb_values": base_bomb_values,
                            "bomb_prize": base_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.3,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": base_bomb_values,
                            "bomb_prize": base_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.59,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": base_bomb_values,
                            "bomb_prize": base_bomb_prize,
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
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.01,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BW0": 1},
                                self.freegame_type: {"BW0": 1, "FR0": 1},
                            },
                            "scatter_triggers": common_scatter,
                            "bomb_values": wincap_bomb_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.99,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                            "scatter_triggers": common_scatter,
                            "bomb_values": boosted_bomb_values,
                            "bomb_prize": boosted_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
            BetMode(
                name="doubleboost",
                cost=1.3,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.015,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1, "BW0": 2},
                                self.freegame_type: {"FR0": 1, "BW0": 3},
                            },
                            "scatter_triggers": common_scatter,
                            "bomb_values": wincap_bomb_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.2,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1, "BW0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "scatter_triggers": common_scatter,
                            "bomb_values": boosted_bomb_values,
                            "bomb_prize": boosted_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.3,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": boosted_bomb_values,
                            "bomb_prize": boosted_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.485,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1, "BW0": 1}},
                            "bomb_values": boosted_bomb_values,
                            "bomb_prize": boosted_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            BetMode(
                name="no_small_bomb",
                cost=500.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.02,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BW0": 1},
                                self.freegame_type: {"BW0": 1, "FR0": 1},
                            },
                            "scatter_triggers": common_scatter,
                            "bomb_values": wincap_bomb_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.98,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                            "scatter_triggers": common_scatter,
                            "bomb_values": no_small_bomb_values,
                            "bomb_prize": high_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
            BetMode(
                name="min_one_x10",
                cost=5.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.015,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1, "BW0": 2},
                                self.freegame_type: {"FR0": 1, "BW0": 3},
                            },
                            "scatter_triggers": common_scatter,
                            "bomb_values": wincap_bomb_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.2,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                            "scatter_triggers": common_scatter,
                            "bomb_values": min_ten_values,
                            "bomb_prize": high_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.25,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": min_ten_values,
                            "bomb_prize": high_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.535,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": min_ten_values,
                            "bomb_prize": high_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            BetMode(
                name="min_one_x100",
                cost=250.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.02,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BW0": 1, "BR0": 1},
                                self.freegame_type: {"BW0": 2, "FR0": 1},
                            },
                            "scatter_triggers": common_scatter,
                            "bomb_values": wincap_bomb_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.25,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                            "scatter_triggers": common_scatter,
                            "bomb_values": min_hundred_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.2,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": min_hundred_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.53,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": min_hundred_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            BetMode(
                name="min_one_x1000",
                cost=1000.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.03,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BW0": 2, "BR0": 1},
                                self.freegame_type: {"BW0": 3, "FR0": 1},
                            },
                            "scatter_triggers": common_scatter,
                            "bomb_values": wincap_bomb_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.27,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                            "scatter_triggers": common_scatter,
                            "bomb_values": min_thousand_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.15,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": min_thousand_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.55,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "bomb_values": min_thousand_values,
                            "bomb_prize": extreme_bomb_prize,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
        ]
