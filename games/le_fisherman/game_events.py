from copy import deepcopy

# Event type constants
SUPER_CASCADE = "superCascade"
GOLDEN_SQUARE_UPDATE = "goldenSquareUpdate"
RAINBOW_ACTIVATION = "rainbowActivation"
BUCKET_COLLECTION = "bucketCollection"
CLOVER_MULTIPLIER = "cloverMultiplier"
BAR_UPDATE = "barUpdate"
BONUS_MODE_ENTER = "bonusModeEnter"
COIN_REVEAL = "coinReveal"


def super_cascade_event(gamestate, removed_symbol, removed_positions):
    """Emitted when Super Cascade removes all instances of a winning symbol type."""
    event = {
        "index": len(gamestate.book.events),
        "type": SUPER_CASCADE,
        "removedSymbol": removed_symbol,
        "removedPositions": [{"reel": p[0], "row": p[1]} for p in removed_positions],
        "removedCount": len(removed_positions),
    }
    gamestate.book.add_event(event)


def golden_square_update_event(gamestate):
    """Emitted when golden squares state changes."""
    event = {
        "index": len(gamestate.book.events),
        "type": GOLDEN_SQUARE_UPDATE,
        "goldenSquares": deepcopy(gamestate.golden_squares),
    }
    gamestate.book.add_event(event)


def rainbow_activation_event(gamestate, rainbow_type, revealed_items, total_coin_value):
    """Emitted when Rainbow/Epic Rainbow activates golden squares.

    Args:
        gamestate: Current game state.
        rainbow_type: "RB" or "ERB".
        revealed_items: List of {"reel": int, "row": int, "symbol": str, "value": float}.
        total_coin_value: Sum of all revealed coin values.
    """
    event = {
        "index": len(gamestate.book.events),
        "type": RAINBOW_ACTIVATION,
        "rainbowType": rainbow_type,
        "revealedItems": revealed_items,
        "totalCoinValue": total_coin_value,
    }
    gamestate.book.add_event(event)


def bucket_collection_event(gamestate, bucket_pos, bucket_type, collected_items, total_value):
    """Emitted when a bucket collects coin values.

    Args:
        gamestate: Current game state.
        bucket_pos: Tuple of (reel, row).
        bucket_type: "BK" (standard 3x3) or "GBK" (global).
        collected_items: List of {"reel", "row", "value"}.
        total_value: Sum of collected values.
    """
    event = {
        "index": len(gamestate.book.events),
        "type": BUCKET_COLLECTION,
        "bucketPosition": {"reel": bucket_pos[0], "row": bucket_pos[1]},
        "bucketType": bucket_type,
        "collectedItems": collected_items,
        "totalValue": total_value,
    }
    gamestate.book.add_event(event)


def clover_multiplier_event(gamestate, clover_pos, clover_type, multiplier_value, affected_items, boosted_value):
    """Emitted when a clover multiplier is applied.

    Args:
        gamestate: Current game state.
        clover_pos: Tuple of (reel, row).
        clover_type: "CLG" (gold) or "CLD" (diamond).
        multiplier_value: The multiplier applied.
        affected_items: Items affected by the multiplier.
        boosted_value: Total value after boost.
    """
    event = {
        "index": len(gamestate.book.events),
        "type": CLOVER_MULTIPLIER,
        "cloverPosition": {"reel": clover_pos[0], "row": clover_pos[1]},
        "cloverType": clover_type,
        "multiplierValue": multiplier_value,
        "affectedItems": affected_items,
        "boostedValue": boosted_value,
    }
    gamestate.book.add_event(event)


def bar_update_event(gamestate):
    """Emitted when Big Catch Bar state changes."""
    event = {
        "index": len(gamestate.book.events),
        "type": BAR_UPDATE,
        "barCount": gamestate.bar_count,
        "barLevel": gamestate.bar_level,
        "extraSpinsAwarded": getattr(gamestate, "extra_spins_awarded", 0),
    }
    gamestate.book.add_event(event)


def bonus_mode_enter_event(gamestate):
    """Emitted when entering a specific bonus mode."""
    event = {
        "index": len(gamestate.book.events),
        "type": BONUS_MODE_ENTER,
        "modeName": gamestate.bonus_mode_name,
        "barLevel": gamestate.bar_level,
        "persistentGolden": gamestate.persistent_golden,
    }
    gamestate.book.add_event(event)


def coin_reveal_event(gamestate, position, coin_type, value):
    """Emitted for individual coin value reveals during rainbow activation.

    Args:
        gamestate: Current game state.
        position: Tuple of (reel, row).
        coin_type: Type of coin revealed.
        value: Coin value.
    """
    event = {
        "index": len(gamestate.book.events),
        "type": COIN_REVEAL,
        "position": {"reel": position[0], "row": position[1]},
        "coinType": coin_type,
        "value": value,
    }
    gamestate.book.add_event(event)
