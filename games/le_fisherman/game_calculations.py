from src.executables.executables import Executables
from src.calculations.cluster import Cluster
from src.calculations.board import Board
from src.calculations.statistics import get_random_outcome
from src.config.config import Config


class GameCalculations(Executables):
    """Core math calculations for Le Fisherman - a 6x5 cluster-pay slot with
    Super Cascades, Golden Squares, Rainbow activation, Bucket collection,
    and Clover multipliers."""

    def evaluate_super_cascade_clusters(self, config, board, clusters, golden_squares,
                                        global_multiplier=1, return_data=None):
        """
        Evaluate cluster wins with Super Cascade behavior.
        For each winning cluster:
        1. Calculate payout based on cluster size
        2. Mark ALL board positions with that symbol as explode=True (Super Cascade)
        3. Track positions behind winning symbols as golden squares
        """
        if return_data is None:
            return_data = {"totalWin": 0, "wins": []}

        exploding_symbols = []
        total_win = 0
        winning_symbol_types = set()

        for sym in clusters:
            for cluster in clusters[sym]:
                syms_in_cluster = len(cluster)
                if (syms_in_cluster, sym) in config.paytable:
                    sym_win = config.paytable[(syms_in_cluster, sym)] * global_multiplier
                    total_win += sym_win
                    winning_symbol_types.add(sym)

                    json_positions = [{"reel": p[0], "row": p[1]} for p in cluster]
                    central_pos = Cluster.get_central_cluster_position(json_positions)

                    return_data["wins"].append({
                        "symbol": sym,
                        "clusterSize": syms_in_cluster,
                        "win": sym_win,
                        "positions": json_positions,
                        "meta": {
                            "globalMult": global_multiplier,
                            "overlay": {"reel": central_pos[0], "row": central_pos[1]},
                        },
                    })

                    # Mark cluster positions as golden squares
                    for pos in cluster:
                        golden_squares[pos[0]][pos[1]] = True

        # SUPER CASCADE: Remove ALL symbols of each winning type from entire board
        super_cascade_positions = {}
        for sym in winning_symbol_types:
            positions = []
            for reel in range(len(board)):
                for row in range(len(board[reel])):
                    if board[reel][row].name == sym:
                        board[reel][row].explode = True
                        positions.append((reel, row))
                        if {"reel": reel, "row": row} not in exploding_symbols:
                            exploding_symbols.append({"reel": reel, "row": row})
            super_cascade_positions[sym] = positions

        return_data["totalWin"] += total_win
        return_data["super_cascade"] = super_cascade_positions

        return board, return_data, golden_squares

    def update_golden_squares(self, win_data, golden_squares):
        """Mark positions behind winning symbols as golden."""
        if win_data.get("totalWin", 0) > 0:
            for win in win_data.get("wins", []):
                for pos in win["positions"]:
                    golden_squares[pos["reel"]][pos["row"]] = True
        return golden_squares

    def activate_rainbow(self, board, golden_squares, bar_level, config):
        """
        Activate golden squares when Rainbow lands.
        Each golden square reveals a random item based on bar_level.
        Returns: list of revealed items and total coin value.
        """
        revealed_items = []
        total_coin_value = 0.0

        reveal_weights = config.reveal_weights.get(bar_level, config.reveal_weights[0])

        for reel in range(len(golden_squares)):
            for row in range(len(golden_squares[reel])):
                if golden_squares[reel][row]:
                    # Determine what this golden square reveals
                    revealed_sym = get_random_outcome(reveal_weights)

                    # Assign value based on symbol type
                    value = 0.0
                    if revealed_sym in config.coin_values:
                        value = get_random_outcome(config.coin_values[revealed_sym])
                        total_coin_value += value

                    multiplier = 0
                    if revealed_sym in config.clover_values:
                        multiplier = get_random_outcome(config.clover_values[revealed_sym])

                    revealed_items.append({
                        "reel": reel,
                        "row": row,
                        "symbol": revealed_sym,
                        "value": value,
                        "multiplier": multiplier,
                    })

        return revealed_items, total_coin_value

    def evaluate_bucket_collection(self, revealed_items):
        """
        Process bucket collection from revealed items.
        Standard Bucket (BK): collects coins in 3x3 zone.
        Global Bucket (GBK): collects ALL coins on grid.
        Returns: list of collection events and total collected value.
        """
        # Separate items by type
        coins = [item for item in revealed_items if item["value"] > 0]
        buckets = [item for item in revealed_items if item["symbol"] == "BK"]
        global_buckets = [item for item in revealed_items if item["symbol"] == "GBK"]

        collections = []
        collected_positions = set()
        total_collected = 0.0

        # Process Global Buckets first (collect everything)
        for gbk in global_buckets:
            collected = []
            gbk_total = 0.0
            for coin in coins:
                key = (coin["reel"], coin["row"])
                if key not in collected_positions:
                    collected.append({"reel": coin["reel"], "row": coin["row"], "value": coin["value"]})
                    gbk_total += coin["value"]
                    collected_positions.add(key)
            collections.append({
                "bucket_pos": (gbk["reel"], gbk["row"]),
                "bucket_type": "GBK",
                "collected": collected,
                "total": gbk_total,
            })
            total_collected += gbk_total

        # Process Standard Buckets (3x3 zone)
        for bk in buckets:
            collected = []
            bk_total = 0.0
            for coin in coins:
                key = (coin["reel"], coin["row"])
                if key not in collected_positions:
                    # Check if coin is within 3x3 zone of bucket
                    if abs(coin["reel"] - bk["reel"]) <= 1 and abs(coin["row"] - bk["row"]) <= 1:
                        collected.append({"reel": coin["reel"], "row": coin["row"], "value": coin["value"]})
                        bk_total += coin["value"]
                        collected_positions.add(key)
            collections.append({
                "bucket_pos": (bk["reel"], bk["row"]),
                "bucket_type": "BK",
                "collected": collected,
                "total": bk_total,
            })
            total_collected += bk_total

        return collections, total_collected

    def apply_clover_multipliers(self, revealed_items, base_value):
        """
        Apply clover multipliers to the total coin/bucket value.
        Green Clover (CLG): multiplies adjacent items only (sum of adjacent coin values * mult).
        Gold Clover (CLD): multiplies ALL items globally.
        Returns: boosted total value, list of clover events.
        """
        clovers_green = [item for item in revealed_items if item["symbol"] == "CLG"]
        clovers_gold = [item for item in revealed_items if item["symbol"] == "CLD"]
        coins = [item for item in revealed_items if item["value"] > 0]

        clover_events = []
        total_value = base_value

        # Gold Clovers multiply everything
        for clover in clovers_gold:
            mult = clover["multiplier"]
            boosted = total_value * (mult - 1)  # Additional value from multiplier
            total_value += boosted
            clover_events.append({
                "pos": (clover["reel"], clover["row"]),
                "type": "CLD",
                "multiplier": mult,
                "affected": [{"reel": c["reel"], "row": c["row"]} for c in coins],
                "boosted_value": boosted,
            })

        # Green Clovers multiply adjacent items
        for clover in clovers_green:
            mult = clover["multiplier"]
            adjacent_value = 0.0
            affected = []
            for coin in coins:
                if abs(coin["reel"] - clover["reel"]) <= 1 and abs(coin["row"] - clover["row"]) <= 1:
                    adjacent_value += coin["value"]
                    affected.append({"reel": coin["reel"], "row": coin["row"]})
            boosted = adjacent_value * (mult - 1)
            total_value += boosted
            clover_events.append({
                "pos": (clover["reel"], clover["row"]),
                "type": "CLG",
                "multiplier": mult,
                "affected": affected,
                "boosted_value": boosted,
            })

        return total_value, clover_events
