import type { Grid, MultiplierMap, SpinConfig, SpinEvent, SpinResult } from './types.js';
import { mulberry32, splitRng } from './rng.js';
import { generateGrid } from './grid.js';
import { findClusters } from './cluster.js';
import { bumpMultipliers, makeMultiplierMap, productUnderCluster } from './multipliers.js';
import { performEvolution } from './evolution.js';
export interface EngineOptions {
  seed?: number;
  maxCascades?: number;
}

export function makeSpinConfig(configJson: any): SpinConfig {
  const rows = configJson.grid?.rows ?? 7;
  const cols = configJson.grid?.cols ?? 7;
  return {
    rows,
    cols,
    weights: configJson.symbolWeights ?? { tier1: 1 },
    cellMultiplierCap: configJson.multipliers?.cellMax ?? 8192,
  };
}

function computeClusterBaseWinX(tier: number, size: number): number {
  // Simple anchor curve (placeholder). Replace with real paytable integration.
  const base = {
    1: { 5: 0.2, 8: 0.8, 12: 2.5, 15: 10 },
    2: { 5: 0.8, 8: 2.5, 12: 8, 15: 25 },
    3: { 5: 2, 8: 10, 12: 30, 15: 100 },
    4: { 5: 5, 8: 20, 12: 60, 15: 200 },
    5: { 5: 20, 8: 100, 12: 500, 15: 2000 },
  } as const;
  const brackets = [15, 12, 8, 5];
  for (const b of brackets) {
    if (size >= b) return (base as any)[tier][b];
  }
  return 0;
}

export function spin(
  configJson: any,
  bet: number,
  opts: { seed?: number; maxCascades?: number; initMultiplierMap?: MultiplierMap } = {},
): SpinResult {
  const rows = configJson?.grid?.rows ?? 7;
  const cols = configJson?.grid?.cols ?? 7;
  let seed = (opts.seed ?? Date.now()) >>> 0;

  // simple seeded RNG
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0x100000000;
  };

  // build a simple grid with tiers
  const grid: any[][] = Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () => ({
      kind: 'tier',
      tier: 1 + Math.floor(rand() * 3), // 1..3
    })),
  );

  // multiplier map (all x1 unless provided)
  const multiplierMap: MultiplierMap =
    (opts.initMultiplierMap as any) ??
    (Array.from({ length: rows }, () => Array.from({ length: cols }, () => 1)) as MultiplierMap);

  const events: SpinEvent[] = [];
  events.push({ type: 'spinStart', payload: { seed: opts.seed } });

  // Tuning knobs for demo math (now read from config)
  const WIN_CHANCE = configJson?.engine?.demo?.winChance ?? 0.28;
  const BASE_FACTOR = configJson?.engine?.demo?.baseFactor ?? 0.25;

  // Weighted helpers
  const pickWeighted = (pairs: Array<[number, number]>): number => {
    const total = pairs.reduce((a, [, w]) => a + w, 0);
    let x = rand() * total;
    for (const [val, w] of pairs) {
      x -= w;
      if (x <= 0) return val;
    }
    return pairs[pairs.length - 1][0];
  };

  // create a demo win with controlled frequency
  let totalWinX = 0;
  if (rand() < WIN_CHANCE) {
    // Favor small sizes/tiers to keep EV reasonable
    const size = pickWeighted([[3, 70], [4, 25], [5, 5]]);
    const tier = pickWeighted([[1, 70], [2, 25], [3, 5]]);
    const row = Math.floor(rand() * rows);
    const col = Math.max(0, Math.min(cols - size, Math.floor(rand() * cols)));

    // positions across the row
    const cells = Array.from({ length: size }, (_, i) => ({ row, col: col + i }));

    // compute a simple win
    const baseWinX = tier * size * BASE_FACTOR;
    const multiplier = cells.reduce((acc, p) => acc * (multiplierMap[p.row][p.col] ?? 1), 1);
    const winAmount = baseWinX * Math.max(1, multiplier) * bet;
    totalWinX += winAmount;

    events.push({
      type: 'win',
      payload: {
        clusterId: `${row}-${col}-${size}`,
        cells, // Array<{ row, col }>
        symbol: { id: `tier${tier}`, tier },
        size,
        multiplier,
        winAmount,
      },
    });
  }

  events.push({ type: 'spinEnd', payload: { totalWinX } });

  return {
    grid,
    multiplierMap,
    totalWinX,
    events,
    uiHints: null,
  } as SpinResult;
}
