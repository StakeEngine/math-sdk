import pytest

pytest.importorskip("zstandard")

from games.boringjob.game_config import GameConfig
from games.boringjob.gamestate import GameState
from games.boringjob.game_optimization import OptimizationSetup


EXPECTED_MODES = [
    "base",
    "bonus",
    "doubleboost",
    "no_small_bomb",
    "min_one_x10",
    "min_one_x100",
    "min_one_x1000",
]


def test_boringjob_modes_present():
    config = GameConfig()
    mode_names = [bm.get_name() for bm in config.bet_modes]
    assert mode_names == EXPECTED_MODES
    assert all(pytest.approx(bm.get_rtp(), rel=1e-5) == 0.965 for bm in config.bet_modes)
    costs = {bm.get_name(): bm.get_cost() for bm in config.bet_modes}
    assert costs["base"] == 1.0
    assert costs["bonus"] == 100.0
    assert costs["doubleboost"] == 1.3
    assert costs["no_small_bomb"] == 500.0
    assert costs["min_one_x10"] == 5.0
    assert costs["min_one_x100"] == 250.0
    assert costs["min_one_x1000"] == 1000.0


def test_boringjob_board_generation_and_bomb_guarantee():
    config = GameConfig()
    gamestate = GameState(config)
    for betmode in config.bet_modes:
        gamestate.betmode = betmode.get_name()
        for distribution in betmode.get_distributions():
            gamestate.criteria = distribution.get_criteria()
            gamestate.gametype = config.basegame_type
            gamestate.reset_book()
            gamestate.draw_board(emit_event=False)
            gamestate.enforce_bomb_guarantee()
            assert len(gamestate.board) == config.num_reels
            required = config.mode_minimum_bombs.get(gamestate.betmode)
            if required is not None:
                assert gamestate.get_highest_bomb_value() >= required


def test_boringjob_optimization_setup_matches_modes():
    config = GameConfig()
    OptimizationSetup(config)
    assert set(config.opt_params.keys()) == set(EXPECTED_MODES)
    for mode_name, opt_config in config.opt_params.items():
        distribution_keys = {dist.get_criteria() for dist in config.get_betmode(mode_name).get_distributions()}
        assert set(opt_config["conditions"].keys()) == distribution_keys
