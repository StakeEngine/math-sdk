"""
Standalone RTP tuning simulator for golf_tumble_ways.

*** THIS IS NOT THE STAKE MATH SDK. ***
It's a simplified stand-in I'm using to get real simulated numbers instead
of guessing paytable values blind. It models the same rules (ways pays,
wild substitution, tumble multiplier tiers, scatter pays, free spins) but
takes shortcuts vs the real engine (e.g. refills are resampled from weight
tables rather than pulled from contiguous positions on an actual reelstrip
tape). Treat output RTP as a directional estimate to get the paytable into
a sane ballpark — the real math-sdk simulation (and its optimizer) is what
Stake will actually run and what determines final approval numbers.
"""

import random

random.seed(42)

SYMBOLS_HIGH = ["H1", "H2", "H3", "H4"]
SYMBOLS_LOW = ["L1", "L2", "L3", "L4"]
WILD = "W"
SCATTER = "S"
ALL_PAYING = SYMBOLS_HIGH + SYMBOLS_LOW

NUM_REELS = 5
NUM_ROWS = 4

# --- Symbol weights (relative frequency per reel cell) ---
BASE_WEIGHTS = {
    "H1": 2, "H2": 3, "H3": 4, "H4": 5,
    "L1": 10, "L2": 11, "L3": 12, "L4": 13,
    "W": 1, "S": 1,
}
FREE_WEIGHTS = {
    "H1": 2, "H2": 3, "H3": 4, "H4": 5,
    "L1": 9, "L2": 10, "L3": 11, "L4": 12,
    "W": 2, "S": 2,
}

# Ways-pay payouts must be much smaller than lines-pay, since win = payout x
# (product of symbol-or-wild counts per matched reel), which compounds fast.
PAYTABLE = {
    (5, "H1"): 0.60, (4, "H1"): 0.25, (3, "H1"): 0.08,
    (5, "H2"): 0.40, (4, "H2"): 0.16, (3, "H2"): 0.05,
    (5, "H3"): 0.28, (4, "H3"): 0.11, (3, "H3"): 0.035,
    (5, "H4"): 0.20, (4, "H4"): 0.08, (3, "H4"): 0.025,
    (5, "L1"): 0.12, (4, "L1"): 0.045, (3, "L1"): 0.015,
    (5, "L2"): 0.10, (4, "L2"): 0.035, (3, "L2"): 0.012,
    (5, "L3"): 0.08, (4, "L3"): 0.028, (3, "L3"): 0.010,
    (5, "L4"): 0.06, (4, "L4"): 0.022, (3, "L4"): 0.008,
    (5, "W"): 0.80, (4, "W"): 0.32, (3, "W"): 0.10,
    (5, "S"): 3.00, (4, "S"): 1.20, (3, "S"): 0.50,
}

TUMBLE_TIERS_BASE = {1: 1, 2: 2, 3: 4, 4: 8}
TUMBLE_TIERS_FREE = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
MAX_MULT = 100

FS_TRIGGERS_BASE = {3: 8, 4: 12, 5: 20}
FS_TRIGGERS_FREE = {3: 5, 4: 8, 5: 12}


def weighted_symbol(weights):
    pop = list(weights.keys())
    wts = list(weights.values())
    return random.choices(pop, weights=wts, k=1)[0]


def draw_board(weights):
    return [[weighted_symbol(weights) for _ in range(NUM_ROWS)] for _ in range(NUM_REELS)]


def refill(board, weights):
    for c in range(NUM_REELS):
        for r in range(NUM_ROWS):
            if board[c][r] is None:
                board[c][r] = weighted_symbol(weights)
    return board


def evaluate_ways(board):
    """Returns (win_multiplier_of_bet, set_of_winning_cells)."""
    total = 0.0
    winning_cells = set()
    for sym in ALL_PAYING:
        # find max consecutive reels from reel0 where sym or WILD present
        matched_reels = 0
        for c in range(NUM_REELS):
            col_syms = board[c]
            if sym in col_syms or WILD in col_syms:
                matched_reels += 1
            else:
                break
        if matched_reels >= 3:
            ways = 1
            for c in range(matched_reels):
                cnt = sum(1 for x in board[c] if x == sym or x == WILD)
                ways *= cnt
            payout = PAYTABLE.get((matched_reels, sym), 0)
            total += payout * ways
            for c in range(matched_reels):
                for r in range(NUM_ROWS):
                    if board[c][r] == sym or board[c][r] == WILD:
                        winning_cells.add((c, r))
    return total, winning_cells


def evaluate_scatter(board):
    count = sum(1 for c in range(NUM_REELS) for r in range(NUM_ROWS) if board[c][r] == SCATTER)
    for kind in (5, 4, 3):
        if count >= kind:
            return PAYTABLE.get((kind, SCATTER), 0), count
    return 0, count


def tumble_sequence(weights, tier_table, carry_in_mult=1):
    board = draw_board(weights)
    total_win = 0.0
    step = 0
    current_mult = carry_in_mult
    scatter_count_total = 0

    while True:
        step += 1
        ways_win, winning_cells = evaluate_ways(board)
        # Scatter pays once per spin sequence (step 1 only) — scatter symbols
        # aren't removed by tumbles, so re-evaluating every step would pay
        # repeatedly for the same unchanged scatters (and could loop forever
        # if ways_win is 0 but scatter count stays >=3).
        if step == 1:
            scat_win, scat_count = evaluate_scatter(board)
            scatter_count_total = scat_count
        else:
            scat_win = 0

        step_win = (ways_win + scat_win) * current_mult
        total_win += step_win

        if ways_win == 0:
            break

        # remove winning cells (ways contributors); scatter symbols stay unless part of a win
        for (c, r) in winning_cells:
            board[c][r] = None
        board = refill(board, weights)

        next_tier = tier_table.get(step + 1, list(tier_table.values())[-1])
        current_mult = min(next_tier, MAX_MULT)

    return total_win, current_mult, scatter_count_total


def run_freespins(num_spins):
    total = 0.0
    persistent_mult = 1
    spins_left = num_spins
    while spins_left > 0:
        step_win, final_mult, scat_count = tumble_sequence(
            FREE_WEIGHTS, TUMBLE_TIERS_FREE, carry_in_mult=persistent_mult
        )
        persistent_mult = min(final_mult, MAX_MULT)
        total += step_win
        if scat_count in FS_TRIGGERS_FREE:
            spins_left += FS_TRIGGERS_FREE[scat_count]
        spins_left -= 1
    return total


def run_base_spin():
    win, _, scat_count = tumble_sequence(BASE_WEIGHTS, TUMBLE_TIERS_BASE)
    if scat_count in FS_TRIGGERS_BASE:
        win += run_freespins(FS_TRIGGERS_BASE[scat_count])
    return win


def simulate(n):
    total_win = 0.0
    max_win_seen = 0.0
    for _ in range(n):
        w = run_base_spin()
        total_win += w
        max_win_seen = max(max_win_seen, w)
    rtp = total_win / n
    return rtp, max_win_seen


if __name__ == "__main__":
    N = 200_000
    rtp, max_win = simulate(N)
    print(f"Simulated spins: {N}")
    print(f"Estimated RTP: {rtp*100:.2f}%")
    print(f"Max single-spin win seen: {max_win:.1f}x bet")
