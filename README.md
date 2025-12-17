# Stake Engine Math SDK

Welcome to [Stake Engine Math SDK](https://engine.stake.com/)!

The Math SDK is a Python-based engine for defining game rules, simulating outcomes, and optimizing win distributions. It generates all necessary backend and configuration files, lookup tables, and simulation results.
   

For technical details [view the docs](https://stakeengine.github.io/math-sdk/)


# Installation
 
This repository requires Python3 (version >= 3.12), along with the PIP package installer.
If the included optimization algorithm is being used, Rust/Cargo will also need to be installed.

It is recommended to use [Make](https://www.gnu.org/software/make/) and setup the engine by running:
```sh
make setup
```

Alternatively, visit our [Setup and Installation page](https://stakeengine.github.io/math-sdk/math_docs/general_overview/) for more details.

## Boringjob game

The `games/boringjob/` package wires a new bomb-based scatter game with seven bet modes:

- `base` (cost 1.0, target RTP 0.965)
- `bonus` (cost 100.0, buybonus, direct bonus entry)
- `doubleboost` (cost 1.3, boosted free-game allocation to double the trigger chance)
- `no_small_bomb` (cost 500.0, buybonus, bomb table trims the smallest tier)
- `min_one_x10` (cost 5.0, guarantees at least one 10x+ bomb per spin)
- `min_one_x100` (cost 250.0, guarantees at least one 100x+ bomb per spin)
- `min_one_x1000` (cost 1000.0, guarantees at least one 1000x+ bomb per spin)

Bombs are represented by the special `B` multiplier symbol. Mode constraints are enforced during board generation (not filtered post-hoc) by injecting or selecting `B` symbols that meet the required multiplier floor; the `no_small_bomb` mode removes sub-10x tiers from its bomb tables, and the `doubleboost` mode increases the quota of forced free-game spins to double the bonus-entry likelihood.

Use repo-standard commands to run the full pipeline or target a specific stage:

- Generate books for all boringjob modes (default also runs optimization/analysis):  
  ```sh
  make run GAME=boringjob
  ```
- Generate books only:  
  ```sh
  BORINGJOB_MODE=books python3 games/boringjob/run.py
  ```
- Re-run optimization using existing books:  
  ```sh
  BORINGJOB_MODE=opt python3 games/boringjob/run.py
  ```
