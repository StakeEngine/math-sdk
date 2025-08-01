"""
Verify lookup-tale and book result format
Output statistics tested via RGS
"""

import json
import os
import importlib
from io import TextIOWrapper
import numpy as np
import zstandard as zst
import hashlib
import pickle
from utils.analysis.distribution_functions import (
    make_win_distribution,
    get_distribution_moments,
    get_distribution_average,
    non_zero_hitrate,
    prob_less_than_bet,
    get_prob_no_win,
    get_maxwin_hitrate,
    get_distribution_median,
    min_dist_difference,
    calculate_rtp,
)


class WinStatistics:
    """Statistics tested upon RGS upload"""

    def __init__(
        self,
        win_distribution=None,
        num_events=None,
        weight_range=None,
        min_win=None,
        max_win=None,
        min_diff=None,
        unique_wins=None,
        average_wins=None,
        rtp=None,
        std=None,
        var=None,
        m2m=None,
        hr_max=None,
        non_zero_hr=None,
        prob_nil=None,
        prob_less_bet=None,
        num_non_zero_payouts=None,
        skew=None,
        excess_kurtosis=None,
    ):
        self.win_distribution = win_distribution
        self.num_events = num_events
        self.weight_range = weight_range
        self.min_win = min_win
        self.max_win = max_win
        self.min_diff = min_diff
        self.unique_wins = unique_wins
        self.average_win = average_wins
        self.rtp = rtp
        self.std = std
        self.var = var
        self.m2m = m2m
        self.hr_max = hr_max
        self.non_zero_hr = non_zero_hr
        self.prob_nil = prob_nil
        self.num_non_zero_payouts = num_non_zero_payouts
        self.prob_less_bet = prob_less_bet
        self.skew = skew
        self.excess_kurtosis = excess_kurtosis

    def to_dict(self):
        map_object = {}
        for item in self.__dict__.keys():
            if item is not None:
                map_object[item] = getattr(self, item)
        return map_object


def verify_lookup_format(filename: str) -> list:
    "Duplicate RGS verification before upload."
    integer_payouts = []
    running_weight_total = 0
    min_win, max_win = None, None
    win_distribution = make_win_distribution(filename)

    with open(filename, "r", encoding="UTF-8") as f:
        for line in f:
            _, weight, payout = line.strip().split(",")
            weight = float(weight)
            payout = float(payout)

            # Payout checks
            assert payout.is_integer() and payout >= 0, "Payout mult be uint64 format:"
            if payout > 0:
                assert payout >= 10, "Minimum non-zero payout is 10 (RGS accepts 'cents' increments)."
            assert payout % 10 == 0, "Payout values must be in increments of 10."
            integer_payouts.append(int(payout))

            if (min_win is None) or (payout < min_win):
                min_win = payout
            if (max_win is None) or (payout > max_win):
                max_win = payout
            # Weight checks
            assert weight.is_integer() and weight >= 0, "Weight must be uint64 format."
            running_weight_total += weight

    assert running_weight_total <= np.iinfo(np.uint64).max, "Sum of weights must be <= MAX(uint64)"

    return win_distribution, integer_payouts, running_weight_total, min_win, max_win


# payout mult value match to lut + length match
def verify_books_and_payout_mults(books_filename: str) -> list:
    """Ensure the values written to the books match those in the lookup table exactly."""
    assert str(books_filename).endswith(".jsonl.zstd") or str(books_filename).endswith(
        "jsonl.zst"
    ), "Verification is only run for compressed book files of format .jsonl.zst."

    book_payout_ints = []
    total_num_events = 0
    with open(books_filename, "rb") as f:
        decompressor = zst.ZstdDecompressor()
        with decompressor.stream_reader(f) as reader:
            txt_stream = TextIOWrapper(reader, encoding="UTF-8")
            for line in txt_stream:
                line = line.strip()
                if not line:
                    continue

                try:
                    blob = json.loads(line)
                except json.JSONDecodeError:
                    raise RuntimeError("Invalid JSON format.")

                for key in ["payoutMultiplier", "id", "events"]:
                    if key not in blob:
                        raise RuntimeError(f"Missing required key: {key}")

                total_num_events += len(blob["events"])
                book_payout_ints.append(blob["payoutMultiplier"])

    return book_payout_ints, total_num_events


def compare_payout_values(book_int_payouts, lut_int_payouts) -> None:
    """Ensure payout multiplier values match between books and lookup tables."""
    book_ints = pickle.dumps(book_int_payouts)
    lut_ints = pickle.dumps(lut_int_payouts)
    assert hashlib.md5(book_ints).hexdigest() == hashlib.md5(lut_ints).hexdigest(), "Mismatch in payout array."


def get_num_non_zero_payouts(book_int_payouts) -> None:
    """Count non-zero payouts"""
    return len([p for p in book_int_payouts if p > 0])


def get_lut_statistics(
    win_distribution, bet_cost, unique_payouts, weight_range, min_win, max_win, num_events
) -> object:
    """Run RGS statistic tests for upload verification."""

    var, std, skew, kurtosis = get_distribution_moments(win_distribution)
    MathStats = WinStatistics(
        win_distribution=win_distribution,
        num_events=num_events,
        weight_range=weight_range,
        min_win=min_win,
        max_win=max_win,
        min_diff=min_dist_difference(win_distribution),
        unique_wins=unique_payouts,
        average_wins=float(get_distribution_average(win_distribution)),
        rtp=calculate_rtp(win_distribution, bet_cost, weight_range),
        std=std,
        var=var,
        hr_max=get_maxwin_hitrate(win_distribution, weight_range),
        non_zero_hr=non_zero_hitrate(win_distribution, weight_range),
        prob_nil=get_prob_no_win(win_distribution, weight_range),
        prob_less_bet=prob_less_than_bet(win_distribution, bet_cost, weight_range),
        num_non_zero_payouts=get_num_non_zero_payouts(unique_payouts),
        skew=skew,
        excess_kurtosis=kurtosis,
    )
    median = get_distribution_median(win_distribution, weight_range)
    if median > 0:
        m2m = MathStats.average_win / median
        MathStats.m2m = m2m
    else:
        MathStats.m2m = 0
    return MathStats


def execute_all_tests(config, excluded_modes=[]):
    """Run all tests for a given game"""
    mode_stats = []
    for bet_mode in config.bet_modes:
        name = bet_mode.get_name()
        cost = bet_mode.get_cost()
        if name not in excluded_modes:
            book_name = f"books_{name}.jsonl.zst"
            lookup_name = f"lookUpTable_{name}_0.csv"
            book_file = os.path.join(config.publish_path, book_name)
            lut_file = os.path.join(config.publish_path, lookup_name)

            if not (os.path.exists(book_file)) or not (os.path.exists(lut_file)):
                raise RuntimeError("Books/Lookup file does not exist.")

            win_dist, lut_payouts, weights_range, min_win, max_win = verify_lookup_format(lut_file)
            book_payouts, num_events = verify_books_and_payout_mults(book_file)

            compare_payout_values(book_payouts, lut_payouts)

            StatsObject = get_lut_statistics(
                win_dist, cost, lut_payouts, weights_range, min_win, max_win, num_events
            )
            setattr(StatsObject, "name", name)
            mode_stats.append(StatsObject)

    fname = f"games/{config.game_id}/library/stats_summary.json"
    write_all_stats(mode_stats, fname)


def write_all_stats(StatsList: object, filename: str) -> None:
    """Write all stats to JSON file."""
    all_stats = {}
    for Stats in StatsList:
        all_stats[Stats.name] = Stats.to_dict()
        # Don't print unique wins/distribution for brevity.
        del all_stats[Stats.name]["win_distribution"]
        del all_stats[Stats.name]["unique_wins"]

    with open(filename, "w", encoding="UTF-8") as f:
        f.write(json.dumps(all_stats, indent=4))


def load_game_config(game_id: str):
    """Load game config class"""
    module_path = f"games.{game_id}.game_config"
    module = importlib.import_module(module_path)
    config = getattr(module, "GameConfig")

    return config()


if __name__ == "__main__":

    game_id = "0_0_lines"
    GameConfig = load_game_config(game_id)
    execute_all_tests(GameConfig)
