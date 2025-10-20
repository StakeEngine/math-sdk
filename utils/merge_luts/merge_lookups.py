"""Given optimized bonus and base lookup tables, substitute bonus probabilities into basegame lookup"""

import numpy as np
from lookup_properties import (
    LookupProperties,
    calculate_new_freegame_probabilities,
    override_optimized_lookup,
    compare_payouts_array,
    plot_function_shapes,
)

if __name__ == "__main__":

    GAME_ID = "0_0_lines_feature_match"
    BASE_COST = 1.0
    FREEGAME_KEY = "freegame"

    base_table = LookupProperties(GAME_ID, "base")
    bonus_table = LookupProperties(GAME_ID, "bonus")

    # verify this substitution method is valid
    assert len(base_table.criteria_mapping[FREEGAME_KEY]) == len(
        bonus_table.criteria_mapping[FREEGAME_KEY]
    ), f"{FREEGAME_KEY} payout arrays do not match in length"
    assert compare_payouts_array(
        base_table.win_mapping[FREEGAME_KEY], bonus_table.win_mapping[FREEGAME_KEY]
    ), f"{FREEGAME_KEY} payout arrays must be identical"

    # find freegame contribtuion properties from base-game
    fg_wins = base_table.win_mapping[FREEGAME_KEY]
    fg_total = np.array(base_table.weight_mapping[FREEGAME_KEY]).sum()
    fg_index = base_table.criteria_mapping[FREEGAME_KEY]
    fg_contribution_in_base = base_table.calculate_criteria_av_win(FREEGAME_KEY) / BASE_COST
    Efg = bonus_table.calculate_criteria_av_win("freegame")

    H = fg_contribution_in_base / Efg  # freegame trigger probability required

    new_base_weights, fg_rtp_contribution, fg_act_hr, fg_weight_contribution = (
        calculate_new_freegame_probabilities(base_table, bonus_table, H, FREEGAME_KEY)
    )
    new_rtp = np.dot(base_table.payouts, new_base_weights) / sum(new_base_weights)
    new_fg_total = np.array(fg_weight_contribution).sum()

    # verify substitution method works
    print(f"Efg (avg per trigger): {Efg:.3f}x")
    print(f"Base FG contribution target: {fg_contribution_in_base:.3f}")
    print(f"Target hit-rate: {H:.6f} (1 in {1/H:.1f})")
    print(f"Derived hit-rate: {fg_act_hr:.6f} (1 in {1/fg_act_hr:.1f})")
    print(f"New total RTP: {new_rtp:.6f}")

    base_fg_norm = [x / fg_total for x in base_table.weight_mapping[FREEGAME_KEY]]
    new_fg_norm = [x / new_fg_total for x in fg_weight_contribution]
    bonus_norm = [
        x / np.array(bonus_table.weight_mapping[FREEGAME_KEY]).sum()
        for x in bonus_table.weight_mapping[FREEGAME_KEY]
    ]
    plot_function_shapes(fg_wins, base_fg_norm, new_fg_norm, bonus_norm)

    file_name = f"games/{GAME_ID}/library/publish_files/LookUpTable_base_0.csv"
    ans = input(f"Proceede with file override (y/n): {file_name}?")
    if str(ans).lower() == "y":
        override_optimized_lookup(file_name, base_table.payouts_ints, new_base_weights)
