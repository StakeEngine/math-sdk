"""Events specific to new and updating expanding wild symbols."""

from copy import deepcopy
from src.events.event_constants import EventConstants
from src.events.events import json_ready_sym

NEW_EXP_WILDS = "newExpandingWilds"
UPDATE_EXP_WILDS = "updateExpandingWilds"
WIN_DATA = "winInfo"


def new_expanding_wild_event(gamestate) -> None:
    """Triggered after new wild rabbit expands."""
    new_exp_wilds = gamestate.new_exp_wilds
    if gamestate.config.include_padding:
        for ew in new_exp_wilds:
            ew["row"] += 1

    event = {"index": len(gamestate.book.events), "type": NEW_EXP_WILDS, "newWilds": new_exp_wilds}
    gamestate.book.add_event(event)


def update_expanding_wild_event(gamestate) -> None:
    """Triggered when an existing WR symbol expands again (e.g. in sticky bonus)."""
    existing_wild_details = deepcopy(gamestate.expanding_wilds)
    wild_event = []
    if gamestate.config.include_padding:
        for ew in existing_wild_details:
            if ew:
                ew["row"] += 1
                wild_event.append(ew)

    event = {"index": len(gamestate.book.events), "type": UPDATE_EXP_WILDS, "existingWilds": wild_event}
    gamestate.book.add_event(event)


def reveal_board_event(gamestate):
    """Display the current board to the client."""
    board_client = []
    special_attributes = list(gamestate.config.special_symbols.keys())
    for reel in range(len(gamestate.board)):
        board_client.append([])
        for row in range(len(gamestate.board[reel])):
            board_client[reel].append(json_ready_sym(gamestate.board[reel][row], special_attributes))

    if gamestate.config.include_padding:
        for reel in range(len(board_client)):
            board_client[reel] = [json_ready_sym(gamestate.top_symbols[reel], special_attributes)] + board_client[reel]
            board_client[reel].append(json_ready_sym(gamestate.bottom_symbols[reel], special_attributes))

    event = {
        "index": len(gamestate.book.events),
        "type": EventConstants.REVEAL.value,
        "board": board_client,
        "paddingPositions": gamestate.reel_positions,
        "gameType": gamestate.gametype,
        "anticipation": gamestate.anticipation,
    }
    gamestate.book.add_event(event)

