"""Optimization inputs for boringjob."""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructConditions,
    ConstructFenceBias,
    verify_optimization_input,
)


class OptimizationSetup:
    """Define optimization ranges for boringjob."""

    def __init__(self, game_config):
        common_parameters = ConstructParameters(
            num_show=4000,
            num_per_fence=9000,
            min_m2m=4,
            max_m2m=8,
            pmb_rtp=1.0,
            sim_trials=4000,
            test_spins=[25, 50, 100],
            test_weights=[0.4, 0.4, 0.2],
            score_type="rtp",
        ).return_dict()

        aggressive_parameters = ConstructParameters(
            num_show=5000,
            num_per_fence=12000,
            min_m2m=3,
            max_m2m=8,
            pmb_rtp=1.0,
            sim_trials=5000,
            test_spins=[10, 25, 50],
            test_weights=[0.5, 0.3, 0.2],
            score_type="rtp",
        ).return_dict()

        def scaling_for(criteria):
            return ConstructScaling(
                [
                    {"criteria": criteria, "scale_factor": 1.2, "win_range": (1, 25), "probability": 1.0},
                    {"criteria": criteria, "scale_factor": 0.9, "win_range": (25, 100), "probability": 1.0},
                    {"criteria": criteria, "scale_factor": 1.3, "win_range": (500, 1000), "probability": 1.0},
                ]
            ).return_dict()

        high_scale = ConstructScaling(
            [
                {"criteria": "freegame", "scale_factor": 1.1, "win_range": (10, 150), "probability": 1.0},
                {"criteria": "freegame", "scale_factor": 1.3, "win_range": (400, 1200), "probability": 1.0},
                {"criteria": "wincap", "scale_factor": 0.9, "win_range": (4000, 5000), "probability": 1.0},
            ]
        ).return_dict()

        self.game_config = game_config
        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.02, av_win=self.game_config.wincap, search_conditions=4800).return_dict(),
                    "freegame": ConstructConditions(rtp=0.35, hr=120, search_conditions={"symbol": "S"}).return_dict(),
                    "0": ConstructConditions(rtp=0.0, av_win=0.0, search_conditions=0).return_dict(),
                    "basegame": ConstructConditions(rtp=0.595, hr=4.5).return_dict(),
                },
                "scaling": scaling_for("basegame"),
                "parameters": common_parameters,
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["freegame"],
                    bias_ranges=[(50.0, 150.0)],
                    bias_weights=[0.4],
                ).return_dict(),
            },
            "bonus": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.03, av_win=self.game_config.wincap, search_conditions=4800).return_dict(),
                    "freegame": ConstructConditions(rtp=0.935, hr="x").return_dict(),
                },
                "scaling": high_scale,
                "parameters": aggressive_parameters,
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["freegame"],
                    bias_ranges=[(500.0, 1500.0)],
                    bias_weights=[0.5],
                ).return_dict(),
            },
            "doubleboost": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.02, av_win=self.game_config.wincap, search_conditions=4700).return_dict(),
                    "freegame": ConstructConditions(rtp=0.4, hr=100, search_conditions={"symbol": "S"}).return_dict(),
                    "0": ConstructConditions(rtp=0.0, av_win=0.0, search_conditions=0).return_dict(),
                    "basegame": ConstructConditions(rtp=0.545, hr=5.0).return_dict(),
                },
                "scaling": scaling_for("freegame"),
                "parameters": aggressive_parameters,
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["freegame"],
                    bias_ranges=[(40.0, 120.0)],
                    bias_weights=[0.4],
                ).return_dict(),
            },
            "no_small_bomb": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.03, av_win=self.game_config.wincap, search_conditions=4800).return_dict(),
                    "freegame": ConstructConditions(rtp=0.935, hr="x").return_dict(),
                },
                "scaling": high_scale,
                "parameters": aggressive_parameters,
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["freegame"],
                    bias_ranges=[(400.0, 1400.0)],
                    bias_weights=[0.45],
                ).return_dict(),
            },
            "min_one_x10": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.025, av_win=self.game_config.wincap, search_conditions=4600).return_dict(),
                    "freegame": ConstructConditions(rtp=0.37, hr=90, search_conditions={"symbol": "S"}).return_dict(),
                    "0": ConstructConditions(rtp=0.0, av_win=0.0, search_conditions=0).return_dict(),
                    "basegame": ConstructConditions(rtp=0.57, hr=5.5).return_dict(),
                },
                "scaling": scaling_for("basegame"),
                "parameters": common_parameters,
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["basegame"],
                    bias_ranges=[(20.0, 80.0)],
                    bias_weights=[0.35],
                ).return_dict(),
            },
            "min_one_x100": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.03, av_win=self.game_config.wincap, search_conditions=4700).return_dict(),
                    "freegame": ConstructConditions(rtp=0.38, hr=80, search_conditions={"symbol": "S"}).return_dict(),
                    "0": ConstructConditions(rtp=0.0, av_win=0.0, search_conditions=0).return_dict(),
                    "basegame": ConstructConditions(rtp=0.555, hr=5.0).return_dict(),
                },
                "scaling": scaling_for("freegame"),
                "parameters": aggressive_parameters,
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["wincap"],
                    bias_ranges=[(3200.0, 4800.0)],
                    bias_weights=[0.3],
                ).return_dict(),
            },
            "min_one_x1000": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.04, av_win=self.game_config.wincap, search_conditions=4900).return_dict(),
                    "freegame": ConstructConditions(rtp=0.36, hr=75, search_conditions={"symbol": "S"}).return_dict(),
                    "0": ConstructConditions(rtp=0.0, av_win=0.0, search_conditions=0).return_dict(),
                    "basegame": ConstructConditions(rtp=0.565, hr=4.8).return_dict(),
                },
                "scaling": scaling_for("freegame"),
                "parameters": aggressive_parameters,
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["wincap"],
                    bias_ranges=[(3600.0, 5000.0)],
                    bias_weights=[0.35],
                ).return_dict(),
            },
        }

        verify_optimization_input(self.game_config, self.game_config.opt_params)
