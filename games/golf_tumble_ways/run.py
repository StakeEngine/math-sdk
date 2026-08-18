"""Main file for generating results for golf_tumble_ways.

Structure copied directly from the CONFIRMED real games/0_0_ways/run.py.
Only the bet-mode names ("base"/"bonus" — matching our game_config.py's
bet_modes) and sim counts differ.
"""
from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":

    num_threads = 10
    rust_threads = 20
    batching_size = 50000
    compression = True
    profiling = False

    # Small sim counts for the FIRST test run — bump these up once this
    # actually completes without errors. Real tuning needs far more.
    # Cut further to 10 after a real hang was observed at 1e3 — confirm
    # this completes quickly before scaling back up.
    num_sim_args = {
        "base": 10,
        "bonus": 10,
    }

    run_conditions = {
        "run_sims": True,
        "run_optimization": False,  # OFF for first smoke test — needs Rust/Cargo, test that separately
        "run_analysis": False,  # TEMP OFF — isolating a real observed hang, see README bug #7
        "run_format_checks": False,  # TEMP OFF — isolating a real observed hang, see README bug #7
    }
    target_modes = ["base", "bonus"]

    config = GameConfig()
    gamestate = GameState(config)
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
