"""Set conditions/parameters for optimization program"""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructConditions,
    verify_optimization_input,
)


class OptimizationSetup:
    """Handle all game mode optimization parameters."""

    def __init__(self, game_config):
        self.game_config = game_config
        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.01, av_win=20000, search_conditions=20000).return_dict(),
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "superfreegame": ConstructConditions(
                        rtp=0.31, hr=900, search_conditions={"symbol": "scatter", "kind": 5}
                    ).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.31, hr=300, search_conditions={"symbol": "scatter"}
                    ).return_dict(),
                    "basegame": ConstructConditions(hr=3.5, rtp=0.3334).return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
            },
            "bonus1": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.01, av_win=20000, search_conditions=20000).return_dict(),
                    "freegame": ConstructConditions(rtp=0.6034, hr="x").return_dict(),
                    "superfreegame": ConstructConditions(rtp=0.35, hr="x").return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[10, 20, 50],
                    test_weights=[0.6, 0.2, 0.2],
                    score_type="rtp",
                ).return_dict(),
            },
            "bonus2": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.01, av_win=20000, search_conditions=20000).return_dict(),
                    "freegame": ConstructConditions(rtp=0.6034, hr="x").return_dict(),
                    "superfreegame": ConstructConditions(rtp=0.35, hr="x").return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[10, 20, 50],
                    test_weights=[0.6, 0.2, 0.2],
                    score_type="rtp",
                ).return_dict(),
            },
            "ante": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.01, av_win=20000, search_conditions=20000).return_dict(),
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "superfreegame": ConstructConditions(
                        rtp=0.31, hr=300, search_conditions={"symbol": "scatter", "kind": 5}
                    ).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.31, hr=100, search_conditions={"symbol": "scatter"}
                    ).return_dict(),
                    "basegame": ConstructConditions(hr=3.5, rtp=0.3334).return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
            },
            "feature_spin": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.01, av_win=20000, search_conditions=20000).return_dict(),
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "superfreegame": ConstructConditions(
                        rtp=0.31, hr=300, search_conditions={"symbol": "scatter", "kind": 5}
                    ).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.31, hr=100, search_conditions={"symbol": "scatter"}
                    ).return_dict(),
                    "basegame": ConstructConditions(hr=3.5, rtp=0.3334).return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
            },
        }

        verify_optimization_input(self.game_config, self.game_config.opt_params)
