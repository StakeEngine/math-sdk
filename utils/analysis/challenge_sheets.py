import importlib
import xlsxwriter
import argparse
from utils.analysis.distribution_functions import make_win_distribution


def load_game_config(game_id: str):
    """Load game config class"""
    module_path = f"games.{game_id}.game_config"
    module = importlib.import_module(module_path)
    config = getattr(module, "GameConfig")

    return config()


def get_mode_dict(game_config: object):
    """Extract mode names and cost from config class"""
    mode_info = {}
    for bm in game_config.bet_modes:
        mode_info[bm.get_name()] = bm.get_cost()

    return mode_info


def get_def_lut_names(game_config: object):
    """Create lookup table filepaths"""
    lut_path = game_config.publish_path
    f = []
    for bm in game_config.bet_modes:
        f.append(str.join("/", [lut_path, f"lookUpTable_{bm.get_name()}_0.csv"]))

    return f


def get_all_mode_values(
    distributions: list[dict],
    mode_costs: list[float],
    all_target_mults,
    rtp_contribution,
    bet_size,
    base_rtp=0.97,
):
    """Compute params for worst-case win scenarios with multiple modes."""
    mode_outcomes = {}
    mode_max_prize = {}
    mode_expected_hit_rates = {}
    expected_profit = {}
    dists = []
    for dist in distributions:
        items = sorted(dist.items())
        wins = [w for w, _ in items]
        weights = [p for _, p in items]
        dists.append((wins, weights))

    for target_mult in all_target_mults:
        candidates = []

        for (wins, weights), mode_cost in zip(dists, mode_costs):
            if wins[-1] < mode_cost * target_mult:
                continue

            cumulative = 0.0
            for w, p in zip(reversed(wins), reversed(weights)):
                if w >= target_mult * mode_cost:
                    cumulative += p
                else:
                    break

            if cumulative > 0:
                candidates.append((cumulative, mode_cost))

        worst_p, worst_cost = max(candidates, key=lambda x: x[0] / x[1])
        mode_outcomes[target_mult] = worst_p

        mode_max_prize[target_mult] = round(rtp_contribution * (1.0 / worst_p) * (worst_cost) * (bet_size), 1)
        mode_expected_hit_rates[target_mult] = round(1 / worst_p, 1)

        expected_profit[target_mult] = round(
            bet_size * worst_cost * (1 - (base_rtp + rtp_contribution)) / worst_p, 2
        )

    return mode_outcomes, mode_max_prize, mode_expected_hit_rates, expected_profit


def write_xlsx(
    file_name: str,
    game_name: str,
    game_id: str,
    bet_size: float,
    bet_size_array: list,
    game_rtp: float,
    additional_rtp: float,
    challange_multipliers: list,
    challange_probs: dict,
    challange_expected_hits: dict,
    challange_max_payouts: dict,
    challange_profits: dict,
):
    """Write payouts, and expected profit/hit-rates."""
    workbook = xlsxwriter.Workbook(f"games/{game_id}/library/" + file_name + ".xlsx")
    bold = workbook.add_format({"bold": True})

    maxtrix_worksheet = workbook.add_worksheet("Challenge Index")
    maxtrix_worksheet.set_column("A:A", 20, bold)
    maxtrix_worksheet.write(0, 0, "Bet Size (->)")
    maxtrix_worksheet.write(1, 0, "Challenge Multiplier")
    for idx, chal in enumerate(challange_multipliers):
        maxtrix_worksheet.write(2 + idx, 0, str(chal) + "x")
        for idy, bet in enumerate(bet_size_array):
            maxtrix_worksheet.write(0, 1 + idy, bet)
            maxtrix_worksheet.write(2 + idx, idy + 1, challange_max_payouts[chal] * bet)

    worksheet = workbook.add_worksheet(game_id)
    worksheet.set_column("A:F", 20, bold)
    worksheet.write_row(
        "A1",
        [
            game_name,
            f"Base Game RTP: {game_rtp*100}%",
            f"Challange RTP: {additional_rtp*100}%",
            f"Bet Size: {bet_size}",
        ],
    )
    worksheet.write_row(
        "A3",
        ["Challange Multiplier", "Max Award", "", "Expected Hit Rate", "Actual Probability", "Expected Profit"],
    )

    # Write results
    probabilities = list(challange_probs.values())
    expected_hits = list(challange_expected_hits.values())
    expected_profit = list(challange_profits.values())
    max_payouts = list(challange_max_payouts.values())
    row_start_index = 3
    for idx, _ in enumerate(challange_multipliers):
        worksheet.write(row_start_index + idx, 0, str(challange_multipliers[idx]))
        worksheet.write(row_start_index + idx, 1, str(max_payouts[idx]))

        worksheet.write(row_start_index + idx, 3, str(expected_hits[idx]))
        prob_format = "{:.3e}".format(probabilities[idx])
        worksheet.write(row_start_index + idx, 4, str(prob_format))
        worksheet.write(row_start_index + idx, 5, str(expected_profit[idx]))

    workbook.close()


def run(
    game_id: str,
    rtp_allocation: float = 0.01,
    bet_sizes: list = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
    mult_step: int = 500,
):
    """Generate payout probabilities and write Excel file"""
    game_config = load_game_config(game_id)
    mode_info = get_mode_dict(game_config)
    files = get_def_lut_names(game_config)
    costs = list(mode_info.values())

    promotion_mult = [100, 150, 200, 250, 300, 350, 400, 450, 500, 750, 1000, 1200, 1500, 1800]
    max_mult = game_config.wincap
    for i in range(int(2000), int(max_mult) + mult_step, mult_step):
        promotion_mult.append(i)

    dists = []
    for f in files:
        dists.append(make_win_distribution(f))

    mode_outcomes, mode_max_prize, mode_expected_hit_rates, expected_profit = get_all_mode_values(
        dists, costs, promotion_mult, rtp_allocation, 1.0, game_config.rtp
    )

    write_xlsx(
        "challenge_amounts",
        game_config.working_name,
        game_id,
        1.0,
        bet_sizes,
        game_config.rtp,
        rtp_allocation,
        promotion_mult,
        mode_outcomes,
        mode_expected_hit_rates,
        mode_max_prize,
        expected_profit,
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", dest="game_id", default="0_0_lines", help="enter game_id, folder name within games/")
    parser.add_argument("-ms", dest="step", default=int(500))
    parser.add_argument("-ra", dest="allocation", default=0.01)
    args = parser.parse_args()

    run(args.game_id, rtp_allocation=args.allocation, mult_step=args.step)
