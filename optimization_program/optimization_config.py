"""Classes for setting up and verifying inputs for game optimization."""

from typing import List, Tuple, Union
from warnings import warn


class ConstructScaling:
    """Verify valid inputs for applying scaling conditions."""

    def __init__(self, all_scaling: List[Tuple]):
        for scaling in all_scaling:
            for cond in ["criteria", "scale_factor", "win_range", "probability"]:
                assert cond in scaling.keys()
                if cond == "criteria":
                    assert isinstance(scaling[cond], str), "Enter string type for criteria condition"
                elif cond in ["scale_factor", "probability"]:
                    assert isinstance(scaling[cond], Union[float, int]), "Enter float/int type for value."
                    if cond == "probability" and scaling[cond] > 1:
                        warn("probabilities > 1 will have no effect on selection.")
                elif cond == "win_range":
                    assert isinstance(scaling[cond], tuple), "Enter tuple for range: (min, max)."
                    assert scaling[cond][0] <= scaling[cond][1]
        self.scaling = all_scaling

    def return_dict(self):
        return self.scaling


class ConstructFenceBias:
    """Bias distribution mean generation"""

    def __init__(
        self,
        applied_criteria: list[str],
        bias_ranges: list[tuple[float, float]],
        bias_weights: list[float],
    ):
        assert len(applied_criteria) == len(bias_ranges)
        assert len(bias_ranges) == len(bias_weights)
        assert all([len(x) == 2 for x in bias_ranges])
        assert all([x[0] <= x[1] for x in bias_ranges])

        bias_dict = []
        for idx, c in enumerate(applied_criteria):
            bias_dict.append({"criteria": c, "range": bias_ranges[idx], "prob": bias_weights[idx]})

        self.bias = bias_dict

    def return_dict(self):
        """Return bias values"""
        return self.bias


class ConstructParameters:
    """Optimization run conditions."""

    def __init__(
        self,
        num_show: int,
        num_per_fence: int,
        min_m2m: float,
        max_m2m: float,
        pmb_rtp: float,
        sim_trials: int,
        test_spins: list,
        test_weights: list,
        score_type: str = "rtp",
        max_trial_dist: int = 15,
    ):

        self.parameters = {
            "num_show_pigs": num_show,
            "num_pigs_per_fence": num_per_fence,
            "min_mean_to_median": min_m2m,
            "max_mean_to_median": max_m2m,
            "pmb_rtp": pmb_rtp,
            "simulation_trials": sim_trials,
            "test_spins": test_spins,
            "test_spins_weights": test_weights,
            "score_type": score_type,
            "max_trial_dist": max_trial_dist,
        }

    def return_dict(self):
        return self.parameters


class ConstructConditions:
    """Construct optimization parameter class for each bet mode."""

    def __init__(
        self,
        rtp: float = None,
        av_win: float = None,
        hr: float = None,
        search_conditions=None,
    ):
        if rtp is None or rtp == "x":
            assert all(
                [av_win is not None, hr is not None]
            ), "if RTP is not specified, hit-rate (hr) and average win amount (av_win) must be given. "
            rtp = round(av_win / hr, 5)
        none_count = sum([1 for x in [rtp, av_win, hr] if x is None])
        assert none_count <= 1, "Criteria RTP is ill defined."

        search_range, force_search = (-1, -1), {}
        if isinstance(search_conditions, (float, int)):
            search_range = (search_conditions, search_conditions)
            force_search = {}
        elif isinstance(search_conditions, tuple):
            assert search_conditions[0] <= search_conditions[1], "Enter (min, max) payout format."
            assert all(
                [isinstance(search_conditions[0], (float, int)), isinstance(search_conditions[1], (float, int))]
            ), "Search condition (min,max) entries must be numbers."
            assert len(search_conditions) == 2, "Search condition length exceeded, enter (min, max) payout format."
            search_range = search_conditions
            force_search = {}
        elif isinstance(search_conditions, dict):
            search_range = (-1, -1)
            force_search = search_conditions

        self.rtp = rtp
        self.av_win = av_win
        self.hr = hr
        self.search_range = search_range
        self.force_search = force_search
        self.params = self.to_dict()

    def to_dict(self):
        """JSON readable"""
        data_struct = {
            "search_range": self.search_range,
            "force_search": self.force_search,
        }
        if self.rtp is not None:
            data_struct["rtp"] = self.rtp
        if self.av_win is not None:
            data_struct["av_win"] = self.av_win
        if self.hr is not None:
            data_struct["hr"] = self.hr
        return data_struct

    def return_dict(self):
        """Return dictionary format for parameters."""
        return self.params


def verify_optimization_input(game_config, opt_dict):
    """Check simulation setup is compatible with optimization inputs,"""
    optimization_mode_names = list(opt_dict.keys())
    for mode_name in optimization_mode_names:
        opt_keys = list(opt_dict[mode_name].keys())
        assert all(
            ["conditions" in opt_keys, "scaling" in opt_keys, "parameters" in opt_keys]
        ), "Required keys: {<mode>: 'conditions':{}, 'scaling':{}, 'parameters':{}}"

        criteria_list = opt_dict[mode_name]["conditions"].keys()
        bet = None
        for bm in game_config.bet_modes:
            if bm.get_name() == mode_name:
                bet = bm
                break
        assert bet is not None, "bet_mode name and optimization mode names do not match."

        dist_keys = []
        for dist in bm._distributions:
            dist_keys.append(dist._criteria)

        assert all(x in criteria_list for x in dist_keys), "Distribution criteria must match 'conditions' keys"

        # Verify optimization segmentation matches target RTP
        bm_rtp = bm.get_rtp()
        param_rtp = 0.0
        param_conditions = opt_dict[mode_name]["conditions"].values()
        for p in param_conditions:
            param_rtp += p["rtp"]

        assert round(bm_rtp, 5) == round(param_rtp, 5), "Optimization RTP does not match betmode RTP."

        # Verify bias criteria is valid
