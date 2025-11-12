# Lines Game - Complete System Overview

This document explains how the Lines slot game works in Stake Engine, from creation to player interaction.

---

## 🎰 System Architecture

### The Big Picture: Two-Part System

```
┌─────────────────────────────────────────────────────────────┐
│                    STAKE ENGINE SYSTEM                       │
├──────────────────────────┬──────────────────────────────────┤
│     MATH SDK (Python)    │      WEB SDK (JavaScript)        │
│    "The Game Brain"      │    "The Game Visuals"            │
├──────────────────────────┼──────────────────────────────────┤
│ • Defines rules          │ • Renders UI                     │
│ • Simulates outcomes     │ • Handles animations             │
│ • Generates books        │ • Responds to events             │
│ • Calculates RTP         │ • Manages state                  │
│ • Creates lookup tables  │ • Player interaction             │
└──────────────────────────┴──────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │      RGS       │
                    │ (Remote Game   │
                    │    Server)     │
                    └────────────────┘
```

---

## PART 1: MATH SDK - The Game Brain 🧠

### 1.1 Configuration Phase (`game_config.py`)

Define the game rules:

```python
# Game Structure
num_reels = 5          # 5 vertical reels
num_rows = [3,3,3,3,3] # 3 symbols per reel = 5×3 grid

# Paytable (kind, symbol) → payout multiplier
paytable = {
    (5, "H1"): 50,    # 5 H1 symbols = 50× bet
    (4, "H1"): 20,    # 4 H1 symbols = 20× bet
    (3, "H1"): 10,    # 3 H1 symbols = 10× bet
    # ... more symbols
}

# Paylines - paths across the 5×3 grid
paylines = {
    1: [0,0,0,0,0],   # Top row
    2: [1,1,1,1,1],   # Middle row
    3: [2,2,2,2,2],   # Bottom row
    4: [0,1,2,1,0],   # V shape
    5: [2,1,0,1,2],   # ^ shape
    # ... up to 20 paylines
}

# Game characteristics
rtp = 0.97            # 97% Return to Player
wincap = 5000         # Max win 5000× bet
```

**Visual Grid Layout**:
```
[0,0] [0,1] [0,2] [0,3] [0,4]  ← Row 0 (payline 1)
[1,0] [1,1] [1,2] [1,3] [1,4]  ← Row 1 (payline 2)
[2,0] [2,1] [2,2] [2,3] [2,4]  ← Row 2 (payline 3)
  ↑     ↑     ↑     ↑     ↑
Reel0 Reel1 Reel2 Reel3 Reel4
```

**Payline Example** (payline 4: [0,1,2,1,0]):
```
  X     ·     ·     ·     X    ← Checks positions [0,0], [1,1], [2,2], [1,3], [0,4]
  ·     X     ·     X     ·
  ·     ·     X     ·     ·
```

---

### 1.2 Reel Definition (`reels/BR0.csv`, `reels/FR0.csv`)

Each reel is a vertical strip of symbols that spins:

```
Reel 0:  L1, H1, H3, L1, L5, L4, L1, L2, H3, S, ...
Reel 1:  H3, H3, H1, H1, L2, L4, L5, L2, H4, S, ...
Reel 2:  L5, H4, L4, L5, H2, L2, L5, L4, L3, S, ...
Reel 3:  L4, L2, L1, L2, H4, L1, L5, L4, H2, S, ...
Reel 4:  L3, L5, H4, L1, L5, H2, L4, L5, L1, S, ...
```

**Symbol Types**:
- `H1-H4`: High value symbols (higher payouts)
- `L1-L5`: Low value symbols (lower payouts)
- `S`: Scatter symbol (triggers free spins)
- `W`: Wild symbol (substitutes for other symbols, has multipliers in bonus)

**Reel Files**:
- `BR0.csv`: Base game reel (regular symbols)
- `FR0.csv`: Free game reel (more wilds, higher multipliers)
- `FRWCAP.csv`: Free game wincap reel

---

### 1.3 Game Logic (`gamestate.py`)

The core simulation loop:

```python
def run_spin(self, sim):
    """Simulates one complete game round"""
    self.reset_book()           # Start new game round
    self.draw_board()           # Pick random symbols from reels

    # Evaluate all paylines for winning combinations
    self.evaluate_lines_board()

    # Check for scatter symbols (3+ triggers bonus)
    if self.check_fs_condition():
        self.run_freespin_from_base()  # Trigger bonus mode

    self.evaluate_finalwin()    # Calculate total win
```

**What happens during a spin**:

1. **Random Selection**: Use simulation seed to pick a position on each reel
2. **Symbol Extraction**: Extract 3 consecutive symbols from each reel
3. **Payline Evaluation**: Check all 20 paylines for matching symbols
4. **Win Calculation**: Calculate wins based on paytable
5. **Scatter Check**: Count scatter symbols for bonus trigger
6. **BookEvent Generation**: Create JSON events describing what happened

**Example Flow**:
```
Reel 0 at position 5 → [L4, L1, L2]
Reel 1 at position 12 → [L5, L2, H4]
Reel 2 at position 8 → [L5, L4, L3]
Reel 3 at position 16 → [L5, L4, H2]
Reel 4 at position 3 → [L1, L5, H2]

Board becomes:
[L4] [L5] [L5] [L5] [L1]  ← Row 0
[L1] [L2] [L4] [L4] [L5]  ← Row 1
[L2] [H4] [L3] [H2] [H2]  ← Row 2

Check payline 2 (middle row): L1-L2-L4-L4-L5 → No match
Check payline 1 (top row): L4-L5-L5-L5-L1 → 4×L5 = win!
... check all 20 paylines
```

---

### 1.4 Simulation & Output (`run.py`)

```python
# Simulation configuration
num_sim_args = {
    "base": 10000,    # Simulate 10k base games
    "bonus": 10000    # Simulate 10k bonus games
}

# Run simulation with:
# - 10 parallel threads
# - Compression enabled
# - Optimization enabled
```

**Generated Files**:

```
library/
├── publish_files/              # ← Upload these to RGS
│   ├── index.json              # Game mode configuration (364 B)
│   ├── books_base.jsonl.zst   # 10k base game outcomes (1.7 MB compressed)
│   ├── books_bonus.jsonl.zst  # 10k bonus game outcomes (9.5 MB compressed)
│   ├── lookUpTable_base_0.csv # Base game probability weights (197 KB)
│   └── lookUpTable_bonus_0.csv# Bonus game probability weights (215 KB)
│
├── configs/                    # Game metadata
│   ├── config.json            # Main game configuration
│   ├── config_fe_*.json       # Frontend configuration
│   ├── event_config_*.json    # Event configurations
│   └── math_config.json       # Math configuration
│
├── forces/                     # Forced outcomes for testing
│   ├── force.json
│   ├── force_record_base.json
│   └── force_record_bonus.json
│
├── lookup_tables/              # Lookup tables (non-segmented)
│   ├── lookUpTable_base.csv
│   └── lookUpTable_bonus.csv
│
├── optimization_files/         # Optimization results
│   └── base_0_*.csv, bonus_0_*.csv
│
└── statistics/                 # Analytics
    ├── 0_0_lines_full_statistics.xlsx
    ├── statistics_summary.json
    └── stats_summary.json
```

---

## PART 2: HOW RTP IS MAINTAINED 🎯

### The Question

Since we define:
- A fixed **RTP target** (0.97 = 97%)
- A fixed **paytable** (symbol combinations → payouts)
- Fixed **reels** (symbol strips)
- Fixed **paylines** (paths to check)

**How does the system ensure we achieve exactly 97% RTP?**

### The Three-Phase Solution

```
Phase 1: SIMULATION          Phase 2: OPTIMIZATION       Phase 3: VERIFICATION
  (Generate outcomes)          (Adjust weights)            (Confirm RTP)
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ Run 10k spins    │        │ Calculate stats  │        │ Check final RTP  │
│ Random reels     │   →    │ Adjust weights   │   →    │ Generate reports │
│ Apply rules      │        │ Target 97% RTP   │        │ Verify numbers   │
│ Record outcomes  │        │ Iterate until OK │        │ ✓ RTP = 0.97     │
└──────────────────┘        └──────────────────┘        └──────────────────┘
```

---

### Phase 1: Simulation - Generate Raw Outcomes

`run.py` simulates 10,000 base games and 10,000 bonus games:

```python
num_sim_args = {
    "base": 10000,    # 10k random base games
    "bonus": 10000    # 10k random bonus games
}
```

**What happens**:
- Each spin uses random reel positions
- Game rules are applied (paytable, paylines, scatters)
- Outcomes are recorded (wins, losses, bonus triggers)
- Books are generated (JSON representations)
- **Initial weights are all equal** (e.g., 100 for each book)

**At this point**: RTP is approximately 97%, but not exact. Could be 96.8% or 97.3%.

---

### Phase 2: Optimization - Adjust Probability Weights

`game_optimization.py` defines the target RTP breakdown:

```python
"conditions": {
    "basegame": ConstructConditions(hr=3.5, rtp=0.59),  # 59% from base wins
    "freegame": ConstructConditions(rtp=0.37, hr=200),  # 37% from bonus
    "wincap": ConstructConditions(rtp=0.01, ...),       # 1% from jackpots
}
# Total: 59% + 37% + 1% = 97% ✓
```

**The optimization algorithm**:

1. **Analyzes** all simulated outcomes
2. **Groups** books by win type:
   - No win books
   - Small win books (2-10×)
   - Medium win books (10-50×)
   - Big win books (50-500×)
   - Bonus trigger books
   - Jackpot books

3. **Adjusts probability weights** in the lookup table:
   ```csv
   simulation_id,probability_weight,payout_multiplier
   1,199895486317,0        ← High weight = very common (no win)
   2,15835407289,20        ← Medium weight = common (small win)
   3,17289740,140          ← Low weight = rare (bonus trigger)
   4,15835407289,20        ← Medium weight = common (small win)
   5,1155732498,300        ← Very low weight = very rare (big win)
   ```

4. **Iteratively refines** weights until:
   - Base game RTP = 0.59 (59%)
   - Bonus game RTP = 0.37 (37%)
   - Total RTP = 0.97 (97%) ✓

**Key Insight**: The same 10,000 books are used, but their **selection probability** changes. Losing books get higher weights (more frequent), winning books get lower weights (less frequent).

**Analogy**: Think of a weighted die:
- Side 1 (no win): 70% chance
- Side 2 (small win): 20% chance
- Side 3 (medium win): 8% chance
- Side 4 (big win): 1.9% chance
- Side 5 (bonus): 0.1% chance

The die has 5 sides (like 10k books), but they're weighted to produce exactly 97% RTP.

---

### Phase 3: Verification - Confirm Exact RTP

`utils/rgs_verification.py` validates the final configuration:

**Verification checks**:

```python
# Calculate weighted RTP
total_weight = sum(all_weights)  # e.g., 1,125,899,906,836,394
expected_return = sum(payout × weight) / total_weight

# Verify RTP
assert expected_return == 0.9700  # Exact 97%
```

**stats_summary.json** confirms:

```json
{
    "base": {
        "rtp": 0.97,              // ✓ Exact target achieved
        "average_win": 0.97,      // ✓ 97 cents per $1 bet
        "non_zero_hr": 3.44,      // 3.44% hit rate for wins
        "prob_nil": 0.709,        // 70.9% of spins = no win
        "weight_range": 1125899906836394.0  // Total weight
    }
}
```

**The math**:
```
RTP = Σ(payout_multiplier × probability_weight) / total_weight
    = (0×199895486317 + 20×15835407289 + 140×17289740 + ...) / 1125899906836394
    = 0.9700000000
    = 97.00%
```

---

### Why This Works

**Fixed elements** (never change):
- Paytable values (3×H1 = 10, 4×H1 = 20, etc.)
- Reel strips (L1, H3, L5, ...)
- Payline patterns ([0,0,0,0,0], [1,1,1,1,1], ...)
- Game rules (3 scatters = bonus, wilds substitute, etc.)

**Variable element** (adjusted during optimization):
- **Probability weights** in lookup tables

The weights control how often each book is selected, which directly controls RTP without changing any game rules or payouts.

---

### Lookup Table Weight Breakdown

**File**: `library/publish_files/lookUpTable_base_0.csv` (10,000 rows)

**Weight distribution**:
```
Books with 0 payout:     weight ≈ 200 billion each  (70.9% total probability)
Books with 20 payout:    weight ≈ 15 billion each   (20% total probability)
Books with 140 payout:   weight ≈ 17 million each   (5% total probability)
Books with 300+ payout:  weight ≈ 1 million each    (4% total probability)
Books with 5000 payout:  weight ≈ 100 each          (0.01% total probability)
```

**Total weight**: 1,125,899,906,836,394 (≈ 1.1 quadrillion)

**Selection probability** for any book:
```
P(book_i) = book_i_weight / total_weight
```

**Example**:
```
Book #1 (no win, weight=199895486317):
  P = 199895486317 / 1125899906836394
    = 0.1776
    = 17.76% chance

Book #5433 (big win, weight=1155732498):
  P = 1155732498 / 1125899906836394
    = 0.00000103
    = 0.000103% chance
```

---

### The Complete Flow

```
1. Game Designer defines:
   ├─ RTP target: 97%
   ├─ Paytable: (3,H1)→10, (4,H1)→20, ...
   ├─ Reels: L1,H3,L5,...
   └─ Paylines: 20 lines

2. Simulation runs:
   ├─ 10k random base games
   ├─ 10k random bonus games
   ├─ Books generated
   └─ Initial RTP ≈ 96.8% (not exact)

3. Optimization adjusts:
   ├─ Increase weight for losing books
   ├─ Decrease weight for winning books
   ├─ Iterate until RTP = exactly 97%
   └─ Lookup tables updated

4. Verification confirms:
   ├─ Calculate weighted RTP
   ├─ Check: RTP = 0.9700 ✓
   └─ Generate statistics report

5. Upload to RGS:
   ├─ Books (outcomes)
   ├─ Lookup tables (weights)
   └─ Frontend (visuals)

6. Player spins:
   ├─ RGS picks random book (weighted by CSV)
   ├─ Returns book to browser
   ├─ Frontend animates
   └─ Over infinite spins: 97% RTP guaranteed
```

---

### Key Takeaways

1. **RTP is controlled by probability weights**, not by changing game rules
2. **Simulation** generates diverse outcomes
3. **Optimization** adjusts selection frequency
4. **Verification** ensures mathematical exactness
5. **Same books** are used, just with different probabilities
6. **Over millions of spins**, players will receive exactly 97% back
7. **Short-term variance** is expected (you can win or lose in a session)
8. **Long-term convergence** to 97% is mathematically guaranteed

---

## PART 3: THE BOOK FORMAT 📖

### What is a Book?

A **book** is a JSON object representing one complete game round. It describes everything that happens from spin to win.

**Example Base Game Book** (no win):

```json
{
  "id": 1,
  "payoutMultiplier": 0,
  "events": [
    {
      "index": 0,
      "type": "reveal",           // ← BookEvent type
      "board": [                   // 5 reels × 3 rows
        [{"name": "L2"}, {"name": "L1"}, {"name": "L4"}, {"name": "H2"}, {"name": "L1"}],
        [{"name": "H1"}, {"name": "L5"}, {"name": "L2"}, {"name": "H3"}, {"name": "L4"}],
        [{"name": "L3"}, {"name": "L5"}, {"name": "L3"}, {"name": "H4"}, {"name": "L4"}],
        [{"name": "H4"}, {"name": "H3"}, {"name": "L4"}, {"name": "L5"}, {"name": "L1"}],
        [{"name": "H3"}, {"name": "L3"}, {"name": "L3"}, {"name": "H1"}, {"name": "H1"}]
      ],
      "paddingPositions": [216, 205, 195, 16, 65],  // Where reels stop
      "gameType": "basegame",
      "anticipation": [0, 0, 0, 0, 0]  // Anticipation effects per reel
    },
    {
      "index": 1,
      "type": "setTotalWin",      // Set the win amount
      "amount": 0
    },
    {
      "index": 2,
      "type": "finalWin",         // Display final win
      "amount": 0
    }
  ],
  "criteria": "0",                // Win classification
  "baseGameWins": 0.0,
  "freeGameWins": 0.0
}
```

**Example Book with Win**:

```json
{
  "id": 42,
  "payoutMultiplier": 5.2,
  "events": [
    {
      "type": "reveal",
      "board": [...],
      "gameType": "basegame"
    },
    {
      "type": "winInfo",          // ← Winning combinations
      "wins": [
        {
          "positions": [[0,0], [0,1], [0,2], [0,3]],  // 4 symbols on top row
          "multiplier": 5.0,
          "payline": 1
        }
      ]
    },
    {
      "type": "setTotalWin",
      "amount": 5.2
    },
    {
      "type": "finalWin",
      "amount": 5.2
    }
  ]
}
```

**Example Book with Free Spins Trigger**:

```json
{
  "id": 123,
  "events": [
    {"type": "reveal", "board": [...]},
    {
      "type": "freeSpinTrigger",  // ← Scatter symbols found!
      "positions": [[1,0], [1,2], [1,4]],  // 3 scatters
      "totalFs": 10                         // Award 10 free spins
    },
    {"type": "updateFreeSpin", "amount": 10, "total": 10},
    // ... free spin reveals ...
    {"type": "updateFreeSpin", "amount": 9, "total": 10},
    {"type": "reveal", "board": [...]},
    // ... continues for all 10 spins
  ]
}
```

### BookEvent Types

Common bookEvent types in the Lines game:

| Type | Purpose | Example Data |
|------|---------|--------------|
| `reveal` | Show spin result | `board`, `paddingPositions`, `anticipation` |
| `winInfo` | Winning combinations | `wins[]` with positions and multipliers |
| `setTotalWin` | Set win amount | `amount` |
| `finalWin` | Display final win | `amount` |
| `freeSpinTrigger` | Start free spins | `positions`, `totalFs` |
| `updateFreeSpin` | Update spin counter | `amount`, `total` |
| `freeSpinEnd` | End free spins | - |

---

## PART 3: WEB SDK - The Game Visuals 🎨

### 3.1 Game Flow Architecture

```
Player clicks "Spin"
       ↓
RGS returns a book (JSON)
       ↓
playBookEvents() ← Process events sequentially
       ↓
For each bookEvent in book.events[]:
       ↓
bookEventHandlerMap[event.type]() ← Find & execute handler
       ↓
Handler broadcasts emitterEvents
       ↓
Components subscribe & react (animations, UI updates)
       ↓
Next bookEvent...
       ↓
All events complete → Game round finished
```

**Key Files** (in `web-sdk/apps/lines/src/`):

- `game/bookEventHandlerMap.ts` - Maps bookEvent types to handler functions
- `game/eventEmitter.ts` - Event broadcaster/subscriber
- `game/stateGame.svelte.ts` - Game state management
- `components/Board.svelte` - Main game board component
- `components/Reel.svelte` - Individual reel component
- `components/Symbol.svelte` - Individual symbol component

---

### 3.2 The Three-Layer Event System

```
┌─────────────────────────────────────────────────┐
│         LAYER 1: BookEvents (from RGS)          │
│  - Data from backend describing what happens    │
│  - Example: {type: 'reveal', board: [...]}     │
│  - Processed by bookEventHandlers               │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│    LAYER 2: BookEventHandlers (game logic)      │
│  - Process bookEvents                           │
│  - Update game state                            │
│  - Broadcast emitterEvents to components        │
│  - Example: reveal handler → reelSpin events    │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│      LAYER 3: EmitterEvents (UI actions)        │
│  - Tell components what to do                   │
│  - Example: {type: 'reelSpin', reel: 0}        │
│  - Components subscribe and animate             │
└─────────────────────────────────────────────────┘
```

**Example Flow**:

```typescript
// LAYER 1: BookEvent arrives from RGS
const bookEvent = {
  type: 'reveal',
  board: [[...], [...], ...],
  gameType: 'basegame'
}

// LAYER 2: BookEventHandler processes it
bookEventHandlerMap.reveal = async (bookEvent) => {
  stateGame.gameType = bookEvent.gameType;

  // Broadcasts LAYER 3 emitterEvents:
  await enhancedBoard.spin({
    revealEvent: bookEvent,
    paddingBoard: config.paddingReels[bookEvent.gameType]
  });
}

// Inside enhancedBoard.spin():
eventEmitter.broadcast({ type: 'boardHide' });
eventEmitter.broadcast({ type: 'reelSpin', reel: 0 });
eventEmitter.broadcast({ type: 'reelSpin', reel: 1 });
// ... spin all reels
await eventEmitter.broadcastAsync({ type: 'reelStop', reel: 0 });
await eventEmitter.broadcastAsync({ type: 'reelStop', reel: 1 });
// ... stop all reels
eventEmitter.broadcast({ type: 'boardSettle', board: finalBoard });

// LAYER 3: Components react
// Board.svelte subscribes to these events:
eventEmitter.subscribeOnMount({
  boardHide: () => { visible = false },
  boardShow: () => { visible = true },
  boardSettle: (event) => { currentBoard = event.board }
});

// Reel.svelte subscribes:
eventEmitter.subscribeOnMount({
  reelSpin: (event) => { if (event.reel === myReelIndex) startSpin() },
  reelStop: async (event) => { if (event.reel === myReelIndex) await stopSpin() }
});
```

---

### 3.3 Key Components

**Board Component** (`components/Board.svelte`):
- Manages 5×3 grid of symbols
- Subscribes to board-related emitterEvents
- Coordinates reel animations

**Reel Component** (`components/Reel.svelte`):
- One vertical strip of symbols
- Handles spin/stop animations
- Uses padding positions for realistic stops

**Symbol Component** (`components/Symbol.svelte`):
- Individual symbol display
- Handles win animations
- State changes (idle, spinning, winning)

**Enhanced Board** (`game/stateGame.svelte.ts`):
- Orchestrates spin sequence
- Manages anticipation effects
- Coordinates timing between reels

---

## PART 4: THE COMPLETE LIFECYCLE 🔄

### Development → Deployment → Play

```
┌──────────────────────────────────────────────┐
│ 1. DEVELOPMENT (Your Computer)               │
├──────────────────────────────────────────────┤
│ ✓ Define game config (paytable, reels, RTP) │
│ ✓ Define game logic (gamestate.py)          │
│ ✓ Define reel strips (reels/*.csv)          │
│ ✓ Run simulations (10k+ games)              │
│ ✓ Generate books & lookup tables            │
│ ✓ Verify RTP and statistics                 │
│ ✓ Build frontend (HTML/JS/CSS)              │
│ ✓ Test in Storybook                         │
└─────────────────┬────────────────────────────┘
                  ↓ Upload to RGS
┌──────────────────────────────────────────────┐
│ 2. RGS (Remote Game Server)                  │
├──────────────────────────────────────────────┤
│ • Stores all books & lookup tables           │
│ • Stores frontend files                      │
│ • Validates game integrity                   │
│ • Manages player sessions & wallets          │
│ • Handles authentication                     │
└─────────────────┬────────────────────────────┘
                  ↓ Player connects
┌──────────────────────────────────────────────┐
│ 3. RUNTIME (Player's Browser)                │
├──────────────────────────────────────────────┤
│ Player clicks "Spin"                         │
│   → Frontend calls /new-round API            │
│   → RGS picks random book (weighted by CSV)  │
│   → Returns book JSON to browser             │
│   → playBookEvents() processes events        │
│   → Animations play sequentially             │
│   → Win displayed                            │
│   → Player wallet updated                    │
│   → /end-round API called                    │
└──────────────────────────────────────────────┘
```

---

## PART 5: HOW RGS SELECTS BOOKS 🎲

### The Lookup Table System

**lookUpTable_base_0.csv** structure:

```csv
simulation_id,probability_weight,payout_multiplier
1,100,0.0
2,100,0.0
3,100,0.0
...
5432,50,5.2      ← Lower weight = rarer
5433,25,50.0     ← Very rare, big win
...
10000,100,0.0
```

**Selection Algorithm**:

1. RGS loads lookup table for current mode (base/bonus)
2. Sums all probability weights: `total_weight = Σ weights`
3. Generates random number: `random_value = random(0, total_weight)`
4. Walks through table, subtracting weights until `random_value <= 0`
5. Selected row's `simulation_id` → fetch that book from `books_*.jsonl.zst`
6. Return book to player

**Example**:
```
Books 1-100: weight=100 each (common, no win)
Book 101: weight=50 (less common, small win)
Book 102: weight=10 (rare, big win)

Total weight = 100×100 + 50 + 10 = 10,060

Random(0, 10060):
  0-9999    → Books 1-100 (99.4% chance)
  10000-10049 → Book 101 (0.5% chance)
  10050-10059 → Book 102 (0.1% chance)
```

This ensures:
- Correct RTP (97%)
- Proper win distribution
- Regulated randomness
- Reproducible results

---

## PART 6: KEY CONCEPTS SUMMARY 💡

### Terminology Reference

| Concept | Description | Location/Example |
|---------|-------------|------------------|
| **Book** | One complete game round (JSON) | Generated by Math SDK, stored in `books_*.jsonl.zst` |
| **BookEvent** | One event within a game round | `{type: 'reveal', board: [...]}` |
| **BookEventHandler** | Function that processes a bookEvent | `bookEventHandlerMap.ts` |
| **EmitterEvent** | UI instruction to components | `{type: 'reelSpin', reel: 0}` |
| **EmitterEventHandler** | Component reaction to emitterEvent | Defined in Svelte components |
| **Lookup Table** | Probability distribution for book selection | `lookUpTable_*.csv` |
| **Reel Strip** | Vertical sequence of symbols | `reels/BR0.csv`, `reels/FR0.csv` |
| **Payline** | Path across grid to check for wins | Defined in `game_config.py` |
| **Paytable** | Symbol combinations → payout multipliers | Defined in `game_config.py` |
| **RTP** | Return to Player percentage | 97% for this game |
| **Wincap** | Maximum win multiplier | 5000× for this game |
| **Anticipation** | Reel slowdown effect before stop | Calculated per reel in reveal event |
| **Padding Position** | Reel stop position (index in reel strip) | Array in reveal event |

### File Locations Quick Reference

**Math SDK** (`/Users/arshak.mkhoyan/Desktop/Pet/math-sdk/games/0_0_lines/`):
- `game_config.py` - Game configuration
- `gamestate.py` - Game logic
- `game_calculations.py` - Win calculation methods
- `game_optimization.py` - Optimization settings
- `reels/*.csv` - Reel strips
- `library/publish_files/` - Files to upload to RGS

**Web SDK** (`/Users/arshak.mkhoyan/Desktop/Pet/web-sdk/apps/lines/`):
- `src/game/bookEventHandlerMap.ts` - BookEvent handlers
- `src/game/eventEmitter.ts` - Event system
- `src/game/stateGame.svelte.ts` - Game state
- `src/components/Board.svelte` - Main board
- `src/components/Reel.svelte` - Reel component
- `src/components/Symbol.svelte` - Symbol component
- `src/stories/data/base_books.ts` - Sample books for Storybook
- `build/` - Production build for RGS upload

---

## PART 7: TESTING & DEBUGGING 🔍

### Testing in Storybook

**URL**: http://localhost:6001/

**Key Stories**:

1. **MODE_BASE/book/random**
   - Tests random base game books
   - Click "Action" to play a round
   - See complete flow from reveal to win

2. **MODE_BASE/bookEvent/reveal**
   - Tests just the reveal event
   - See how reels spin and stop
   - Isolated testing

3. **MODE_BONUS/book/random**
   - Tests bonus mode books
   - See free spin mechanics
   - Wild multipliers in action

4. **COMPONENTS/Symbol/symbols**
   - View all symbols and states
   - Test symbol animations
   - Check visual assets

### Understanding a Book in Storybook

When you click "Action" in `MODE_BASE/book/random`:

1. Storybook loads a random book from `src/stories/data/base_books.ts`
2. Calls `playBookEvents(book.events)`
3. Each event processed sequentially
4. Console shows bookEvent details
5. Animations play in real-time
6. "Action is resolved ✅" appears when complete

### Debugging Tips

**Check BookEvents**:
```typescript
// In bookEventHandlerMap.ts, add logging:
reveal: async (bookEvent, context) => {
  console.log('📖 Reveal Event:', bookEvent);
  console.log('Board:', bookEvent.board);
  console.log('Padding:', bookEvent.paddingPositions);
  // ... rest of handler
}
```

**Check EmitterEvents**:
```typescript
// In a component, add logging:
eventEmitter.subscribeOnMount({
  reelSpin: (event) => {
    console.log('🎰 Reel Spin:', event.reel);
    startSpin();
  }
});
```

**Check State**:
```typescript
// Access game state:
import { stateGame } from './game/stateGame.svelte';
console.log('Game Type:', stateGame.gameType);
console.log('Current Board:', stateGame.board);
```

---

## PART 8: COMMON MODIFICATIONS 🔧

### Adding a New Symbol

**Math SDK**:
```python
# game_config.py
self.paytable = {
    (5, "NEW"): 100,  # Add new symbol payout
    (4, "NEW"): 40,
    (3, "NEW"): 15,
}
```

**Reel Files**:
```csv
# reels/BR0.csv
# Add "NEW" to reel strips
L1,H3,NEW,L4,L3
```

**Web SDK**:
```typescript
// src/game/stateGame.ts
// Add symbol configuration
symbols = {
  NEW: { texture: 'new_symbol.png', ... }
}
```

### Adding a New BookEvent

**Math SDK**:
```python
# gamestate.py
def some_game_logic(self):
    # Create new event
    self.transmit_event({
        'type': 'customEvent',
        'customData': value
    })
```

**Web SDK**:
```typescript
// src/game/typesBookEvent.ts
type BookEventCustom = {
  type: 'customEvent';
  customData: number;
};

export type BookEvent =
  | BookEventReveal
  | BookEventCustom  // Add here
  | ...;

// src/game/bookEventHandlerMap.ts
export const bookEventHandlerMap = {
  customEvent: async (bookEvent: BookEventOfType<'customEvent'>) => {
    console.log('Custom data:', bookEvent.customData);
    eventEmitter.broadcast({ type: 'customAnimation' });
  }
};
```

### Changing Paylines

```python
# game_config.py
self.paylines = {
    1: [0,0,0,0,0],     # Top row
    2: [1,1,1,1,1],     # Middle
    3: [2,2,2,2,2],     # Bottom
    21: [1,0,1,2,1],    # NEW: Zig-zag pattern
    22: [0,2,0,2,0],    # NEW: Up-down pattern
}
```

---

## PART 9: DEPLOYMENT CHECKLIST ✅

### Before Uploading to RGS

- [ ] Math SDK simulation completed successfully
- [ ] RTP verified in statistics (should be ~97%)
- [ ] All books generated (check `library/publish_files/`)
- [ ] Lookup tables created
- [ ] Frontend built (`pnpm run build --filter=lines`)
- [ ] Tested in Storybook
- [ ] No console errors in browser
- [ ] Win animations working
- [ ] Sound effects playing correctly

### Files to Upload

**Math Files** (from `games/0_0_lines/library/publish_files/`):
- [ ] `index.json`
- [ ] `books_base.jsonl.zst`
- [ ] `books_bonus.jsonl.zst`
- [ ] `lookUpTable_base_0.csv`
- [ ] `lookUpTable_bonus_0.csv`

**Frontend Files** (from `web-sdk/apps/lines/build/`):
- [ ] Entire `build/` folder contents
- [ ] `index.html`
- [ ] `_app/` directory
- [ ] `assets/` directory
- [ ] Asset files (loaders, favicon, etc.)

### Upload Steps

1. Login to https://engine.stake.com/
2. Navigate to game's "Files" page
3. Upload math files → Click "Publish Game" → Select "Backend/Math"
4. Upload frontend files → Click "Publish Game" → Select "Front End"
5. Go to "Developer" page
6. Click "Start game session"
7. Click "Launch in New Tab"
8. Test thoroughly!

---

## PART 10: RESOURCES 📚

### Documentation Links

- **Stake Engine Math SDK**: https://stakeengine.github.io/math-sdk/
- **Stake Engine Portal**: https://engine.stake.com/
- **Web SDK README**: `../web-sdk/README.md`

### Support Files

- **This Overview**: `games/0_0_lines/GAME_OVERVIEW.md`
- **Game README**: `games/0_0_lines/readme.txt`
- **Statistics**: `library/0_0_lines_full_statistics.xlsx`

### Key Concepts to Study

1. **Finite State Machines** (XState) - For bet flow
2. **Event-Driven Architecture** - For component communication
3. **Svelte 5 Reactivity** - For state management
4. **PixiJS** - For game rendering
5. **Probability & Statistics** - For understanding RTP

---

## Need Help? 🆘

Common issues and solutions:

**Issue**: Files generated in `venv3.12/src/stakeengine/...`
**Solution**: Copy to `games/0_0_lines/library/` or fix requirements.txt

**Issue**: Storybook won't start
**Solution**: Build dependencies: `pnpm run build --filter=pixi-svelte`

**Issue**: RTP doesn't match target
**Solution**: Run optimization in `run.py`, adjust reel strips

**Issue**: Animation timing issues
**Solution**: Check `await` in bookEventHandlers, ensure sequential execution

---

*Document created: 2025-11-12*
*Game: 0_0_lines (Lines Slot Game)*
*Stake Engine Version: Latest*