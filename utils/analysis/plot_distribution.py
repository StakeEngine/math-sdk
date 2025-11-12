"""Visual inspections for optimization program output"""

import os
import argparse
import matplotlib.pyplot as plt
from utils.analysis.distribution_functions import make_win_distribution_from_optimizer


def make_win_dist(game_id: str, mode: str, optimization_number: int):
    """Load sorted win distribution"""
    fname = os.path.join("games", game_id, "library", "optimization_files", f"{mode}_0_{optimization_number}.csv")

    return make_win_distribution_from_optimizer(fname, normalize=True)


def plot_win_dist(win_dist: list):
    """Overlay win distributions"""
    plt.style.use("seaborn-v0_8-darkgrid")
    colors = plt.get_cmap("tab10", len(win_dist))
    xmax = max(list(win_dist[0].keys()))
    xmax = 1.05 * xmax
    xmin = min(list(win_dist[0].keys()))

    for idx, wd in enumerate(win_dist):
        wins = list(wd.keys())
        weights = list(wd.values())
        plt.scatter(
            wins,
            weights,
            label=f"Distribution {idx+1}",
            color=colors(idx),
            linewidth=0.7,
            alpha=1 / len(win_dist),
            marker="x",
            s=8,
        )
        plt.fill_between(wins, weights, color=colors(idx), alpha=0.05)
    plt.grid(True)
    plt.xlim([xmin, xmax])
    plt.show()


def run(game_id: str, mode: str, optimization_tests: list):
    """Compare distributions"""
    win_dists = []
    for o in optimization_tests:
        win_dists.append(make_win_dist(game_id, mode, o))
    plot_win_dist(win_dists)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", dest="gameid")
    parser.add_argument("-m", dest="mode")
    parser.add_argument("-o", dest="optimized", nargs="+")
    args = parser.parse_args()

    # run("0_0_scatter", "bonus", [1, 2])
    run(args.gameid, args.mode, args.optimized)
