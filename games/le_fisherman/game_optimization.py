from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructFenceBias,
    ConstructConditions,
    verify_optimization_input,
)


class OptimizationSetup:
    def __init__(self, game_config):
        self.game_config = game_config

        wincaps = {}
        for bm in game_config.bet_modes:
            wincaps[bm.get_name()] = bm.get_wincap()

        self.game_config.opt_params = {
            "base": {
                "conditions": ConstructConditions(
                    {
                        "wincap": {"rtp": 0.005, "av_win": 15000, "search_conditions": 15000},
                        "0": {"rtp": 0, "av_win": 0, "search_conditions": 0},
                        "freegame": {
                            "rtp": 0.32,
                            "hr": 600,
                            "search_conditions": {"symbol": "scatter"},
                        },
                        "basegame": {"hr": 2.4, "rtp": 0.6383},
                    }
                ).return_dict(),
                "scaling": ConstructScaling(
                    [
                        {"name": "basegame", "type": "reel_weight", "reelset": "base", "scaling_type": "all"},
                        {"name": "freegame", "type": "reel_weight", "reelset": "base", "scaling_type": "scatter"},
                    ]
                ).return_dict(),
                "parameters": ConstructParameters(
                    wincap=wincaps["base"],
                    betmode="base",
                    iterations=500,
                    tolerance=0.0005,
                    batch_size=50000,
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    [
                        {"name": "basegame", "fence_rtp": 0.6383, "bias": 1.0},
                        {"name": "freegame", "fence_rtp": 0.32, "bias": 1.0},
                        {"name": "wincap", "fence_rtp": 0.005, "bias": 1.0},
                    ]
                ).return_dict(),
            },
            "bonus_hunt": {
                "conditions": ConstructConditions(
                    {
                        "wincap": {"rtp": 0.01, "av_win": 15000, "search_conditions": 15000},
                        "freegame": {"rtp": 0.95, "hr": "x"},
                    }
                ).return_dict(),
                "scaling": ConstructScaling(
                    [
                        {"name": "freegame", "type": "reel_weight", "reelset": "bonus_hunt", "scaling_type": "all"},
                    ]
                ).return_dict(),
                "parameters": ConstructParameters(
                    wincap=wincaps["bonus_hunt"],
                    betmode="bonus_hunt",
                    iterations=500,
                    tolerance=0.0005,
                    batch_size=50000,
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    [
                        {"name": "freegame", "fence_rtp": 0.95, "bias": 1.0},
                        {"name": "wincap", "fence_rtp": 0.01, "bias": 1.0},
                    ]
                ).return_dict(),
            },
            "rainbow_trout": {
                "conditions": ConstructConditions(
                    {
                        "wincap": {"rtp": 0.01, "av_win": 15000, "search_conditions": 15000},
                        "freegame": {"rtp": 0.95, "hr": "x"},
                    }
                ).return_dict(),
                "scaling": ConstructScaling(
                    [
                        {"name": "freegame", "type": "reel_weight", "reelset": "rainbow_trout", "scaling_type": "all"},
                    ]
                ).return_dict(),
                "parameters": ConstructParameters(
                    wincap=wincaps["rainbow_trout"],
                    betmode="rainbow_trout",
                    iterations=500,
                    tolerance=0.0005,
                    batch_size=50000,
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    [
                        {"name": "freegame", "fence_rtp": 0.95, "bias": 1.0},
                        {"name": "wincap", "fence_rtp": 0.01, "bias": 1.0},
                    ]
                ).return_dict(),
            },
            "rainbow_epic": {
                "conditions": ConstructConditions(
                    {
                        "wincap": {"rtp": 0.01, "av_win": 15000, "search_conditions": 15000},
                        "freegame": {"rtp": 0.95, "hr": "x"},
                    }
                ).return_dict(),
                "scaling": ConstructScaling(
                    [
                        {"name": "freegame", "type": "reel_weight", "reelset": "rainbow_epic", "scaling_type": "all"},
                    ]
                ).return_dict(),
                "parameters": ConstructParameters(
                    wincap=wincaps["rainbow_epic"],
                    betmode="rainbow_epic",
                    iterations=500,
                    tolerance=0.0005,
                    batch_size=50000,
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    [
                        {"name": "freegame", "fence_rtp": 0.95, "bias": 1.0},
                        {"name": "wincap", "fence_rtp": 0.01, "bias": 1.0},
                    ]
                ).return_dict(),
            },
        }

        verify_optimization_input(self.game_config, self.game_config.opt_params)
