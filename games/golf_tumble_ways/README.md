# "Hole-In-One" — Golf-themed slot (working title)

Ways Pays + Tumble/Cascade with a global tumble multiplier, golf terminology
bonus features.

## Status: rewritten against real, confirmed SDK source (2nd pass)

This scaffold was originally written against documented conventions only
(guesses). It has now been **rewritten against real source code you pulled
directly from a working local clone** — every structural decision below is
confirmed, not guessed, unless explicitly flagged otherwise.

**Still not done:** this has not actually been run yet (`python run.py`).
That's the next step — see "Next steps" at the bottom.

## Confirmed design decisions (resolved from open questions)

**1. Scatter pays are NOT used — scatter is trigger-only.**
Confirmed by reading the real `games/0_0_ways/gamestate.py`: the entire
win evaluation is just `self.evaluate_ways_board()`, no separate
scatter-pay pass. Scatter symbols only feed `check_fs_condition()`. We
followed this pattern exactly — the "S" (Hole-In-One) symbol has no
paytable entry, it only triggers free spins.

**2. The tumble multiplier is a simple +1-per-tumble-step counter, not a
tier table.** Confirmed by reading `src/executables/executables.py`:
```python
def update_global_mult(self) -> None:
    self.global_multiplier += 1
    update_global_mult_event(self)
```
So the original "Birdie=2x, Eagle=4x, Albatross=8x" *tier table* idea was
wrong — the real mechanic just increments by 1 each tumble (1, 2, 3, 4...).
Golf terms should be applied as **display labels** over whatever the
current value is (e.g. show "Birdie!" the first time it hits 2, "Eagle!"
at 3, etc.), not a different underlying mechanic.

**3. The core `ways` calculation natively supports a global multiplier.**
Confirmed by reading `src/calculations/ways.py`:
`Ways.get_ways_data(config, board, global_multiplier=..., multiplier_strategy="global")`
is a first-class, supported call shape. The real `0_0_ways` sample doesn't
use this (it calls `get_ways_data()` with no multiplier args), so we
**override `evaluate_ways_board()`** in our own `game_executables.py` to
pass these through — see that file's docstring for why.

## Files (rewritten to match real file names/structure)

- `game_config.py` — GameConfig class; confirmed real shape (BetMode,
  Distribution, `construct_paths()`, named reelset loading via
  `read_reels_csv`)
- `gamestate.py` — **note: no underscore**, matching the real SDK's
  filename (we had this wrong originally as `game_state.py`, which is why
  early `type` commands failed)
- `game_override.py` — reset_book/reset_fs_spin overrides; sets
  `global_multiplier = 1` in both (base game needs it too, since
  `evaluate_ways_board()` always reads it now)
- `game_executables.py` — **the key file**: overrides `evaluate_ways_board()`
  to actually wire `global_multiplier` into the ways win calculation
- `game_calculations.py` — minimal pass-through, matching confirmed
  `0_0_ways` shape (we don't need the "M" multiplier-symbol logic from
  `0_0_scatter`, since we're using the tumble-count mechanic instead)
- `run.py` — still a placeholder, not yet matched against real
  `0_0_ways/run.py` (see Next steps)
- `tune_rtp_sim.py` — standalone Monte Carlo tuning simulator (NOT the
  real SDK), used to get the paytable numbers below
- `config/` — placeholder reelstrip CSVs, still need real rebuild

## What's NOT yet confirmed / still guessed

- **`tumble_game_board()`** — used in our `gamestate.py` tumble loop
  (copied from the confirmed real `0_0_scatter/gamestate.py` pattern),
  but we've never actually seen its definition. It's presumably a core
  method inherited via `Executables` → should just work, but hasn't been
  verified.
- **`reset_book`/`reset_fs_spin` overrides** — borrowed from
  `0_0_scatter/game_override.py` since `0_0_ways` doesn't define these at
  all in what we've seen. Reasonable, but not independently confirmed for
  a ways-type game.
- **`run.py`** — never actually diffed against the real
  `games/0_0_ways/run.py`. Do this before your first real run.
- **Distribution quotas/conditions** in `game_config.py`'s `bet_modes` —
  structurally correct (confirmed shape) but the actual quota numbers are
  still placeholders modeled on `0_0_ways`, not tuned for our game.

## 🟡 Paytable — tuned once via standalone simulator, not final

`game_config.py` paytable values went through one tuning pass — see
`tune_rtp_sim.py`, a **standalone stand-in simulator** (NOT the real
Stake math-sdk) modeling the same ways/tumble/free-spin rules. At ~150k
simulated spins it landed around **~94% RTP**.

**Important caveats, don't lose these:**
- Estimated RTP was **highly volatile across runs** — smaller sample
  sizes (20k) swung anywhere from ~88% to ~99% at the original 256x
  multiplier cap. Lowering the cap to **100x** (current setting)
  tightened that to roughly ~91-94% across repeated runs — a meaningful
  volatility reduction for a small RTP cost.
- The paytable values assume the symbol weights in
  `game_config.py -> relative_symbol_weights`, **not** the tiny
  placeholder reelstrip CSVs in `config/`. Those need to be rebuilt as
  much longer, properly weighted strips before real tuning is meaningful.
- Once running against the real SDK, re-tune again at real scale using
  its own simulation/optimizer, and check the ±0.5% RTP spread across
  bet modes that Stake's approval checklist requires.

## Theme / feature mapping

| Golf term | Mechanic |
|---|---|
| Hole-In-One (golf ball + hole scatter) | Scatter symbol, triggers free spins only (no direct pay) |
| Birdie / Eagle / Albatross | Display labels for the global_multiplier value as it climbs +1 per tumble |
| The 19th Hole | Free spins bonus round name |

## Next steps (in order)

1. ✅ `run.py` now matches the real confirmed structure (was rewritten
   against `games/0_0_ways/run.py`). Two new required files added:
   `game_events.py` (simple `from src.events.events import *`) and
   `game_optimization.py` (opt_params for the Rust optimizer, structure
   copied from the real sample — **rtp/av_win/hr numbers inside are
   still placeholders copied from 0_0_ways, not tuned for our game**).
2. `run_optimization` is set to `False` for the first test run —
   optimization uses the Rust-based optimizer (`rust_threads`), which
   needs Cargo installed. Get a plain sim run working first, then test
   optimization separately once that's confirmed (this is also where the
   earlier Cargo/Build Tools install may actually matter, unlike the
   Python-version issue that caused the first false alarm).
3. ✅ Real reelstrips generated: `reels\BR0.csv` and `reels\FR0.csv`, 60
   rows each, no header row, one symbol per reel per row (format
   confirmed directly against the real `games/0_0_ways/reels/BR0.csv`).
   Built from the `relative_symbol_weights` in `game_config.py` via
   independent per-cell random draws — not hand-tuned reel-by-reel like a
   real production reelset eventually should be, but structurally valid
   and enough to actually run. The old `config/` folder and its
   `reelstrips_basegame.csv`/`reelstrips_freegame.csv` files are gone —
   wrong location and wrong filenames from the original guess-based
   scaffold; real files live in `reels\BR0.csv` / `reels\FR0.csv`.
4. Copy every file in this folder (including the new `reels\` subfolder)
   over your existing `math-sdk/games/golf_tumble_ways/`, then run
   `python run.py` from inside that folder

## ⚠️ Known filename gotcha

Downloaded files from chat can get renamed on save (we hit this twice:
`game_config.py` → `GameConfig.py`, `gamestate.py` → `game_state.py`).
Python imports are exact-name-sensitive. **Before running, `dir` the
folder and confirm every filename matches exactly** what's listed above
— rename anything that doesn't match, don't assume the save preserved
the name.

## Fixed bugs (chronological, keep for reference)

1. Filenames renamed on download (`game_config.py`→`GameConfig.py`,
   `gamestate.py`→`game_state.py`) — fixed by manual rename, not a code bug.
2. `run.py` was still the guessed placeholder — rewritten against real
   `games/0_0_ways/run.py`; added missing `game_events.py`/`game_optimization.py`.
3. Reelstrip files were wrong name/location (`config/reelstrips_*.csv`
   instead of `reels/BR0.csv`+`reels/FR0.csv`) — regenerated in the
   correct location/format, confirmed against real
   `games/0_0_ways/reels/BR0.csv`.
4. `TypeError: Can't instantiate abstract class GameState without an
   implementation for 'assign_special_sym_function'` — this method is
   abstract/required on the base class. Fixed in `game_override.py` with
   a deliberate no-op (`self.special_symbol_functions = {}`), since our
   global-counter multiplier doesn't need per-symbol special functions
   the way the real `0_0_ways` sample's Wild-multiplier mechanic does.
5. `AssertionError: Optimization RTP does not match betmode RTP` — the
   optimizer requires each bet mode's condition RTPs (wincap + 0 +
   freegame + basegame for base; wincap + freegame for bonus) to sum
   EXACTLY to that mode's `rtp` (0.94). Base mode was off by 0.001
   (0.941 vs 0.94) from the copied sample values — fixed by adjusting
   `game_optimization.py`'s base "freegame" condition rtp from 0.35 to
   0.349. Both modes now sum to exactly 0.94.
6. Sim hung for minutes, single thread reported 400x+ RTP — root cause
   was TWO real bugs at once: (a) `max_tumble_multiplier` cap was
   defined in an earlier draft but got dropped during the real-source
   rewrite — `update_global_mult()` was calling the base class's
   uncapped `+= 1` version forever. Fixed with an override in
   `game_override.py` that stops incrementing once
   `config.max_tumble_multiplier` (100) is reached.
   (b) Our reelstrips are randomly generated (independent per-cell
   draws), not curated, so hit-frequency is uncontrolled — a single spin
   could chain far more tumbles than intended by bad luck alone. Added a
   hard `max_tumble_steps = 200` safety valve in `gamestate.py`'s tumble
   loop as a scaffold-only defensive measure. Also cut `run.py`'s test
   sim counts from 1000 to 10 per mode to get a fast first signal before
   scaling back up.
7. Run hung again after sims+generate_configs completed successfully
   (confirmed via library file timestamps not updating for 12+ minutes,
   ~5% CPU — genuinely stuck, not slow). Root cause not yet identified —
   temporarily set `run_analysis` and `run_format_checks` to False in
   run.py to isolate which stage is hanging (leading theory: create_stat_sheet
   or execute_all_tests choking on the runaway win data we saw — 5000x
   wincap hits, suspiciously uniform 50.0x results across most bonus
   sims — rather than a raw infinite loop). Re-enable one at a time once
   sims-only run is confirmed fast and clean.
