import type { MultiplierMap } from '../engine/types.js';
import { spin } from '../engine/engine.js';

// Minimal Free Spins feature with persistent multipliers and deterministic steps

export interface FreeSpinsState {
  seed: number;
  spinsTotal: number;
  spinsLeft: number;
  stepIndex: number;
  totalWinX: number;
  multiplierMap: MultiplierMap;
  ended: boolean;
  lastSpin?: { winX: number; events: any[]; grid: any[][] };
}

export interface FreeSpinsConfig {
  spinsByScatters: Record<string, number>; // e.g. { "4":10, "5":12, "6":15, "7":20 }
  retriggerScatterCount?: number;          // default 3
  retriggerSpins?: number;                 // default 5
}

function spinsForScatters(cfg: FreeSpinsConfig, scatters: number) {
  const keys = Object.keys(cfg.spinsByScatters).map(Number).sort((a, b) => a - b);
  let out = 0;
  for (const k of keys) if (scatters >= k) out = cfg.spinsByScatters[String(k)];
  return out;
}

function makeOnesMap(rows: number, cols: number): MultiplierMap {
  return Array.from({ length: rows }, () => Array.from({ length: cols }, () => 1));
}

function bumpAllByOne(map: MultiplierMap) {
  for (let r = 0; r < map.length; r++) for (let c = 0; c < map[0].length; c++) map[r][c] += 1;
}

function countPikachuScatters(grid: any[][]) {
  let k = 0;
  for (let r = 0; r < grid.length; r++) for (let c = 0; c < grid[0].length; c++) {
    if (String(grid[r][c]?.kind) === 'scatter_pikachu') k++;
  }
  return k;
}

// Simple seed mixer to derive deterministic child seeds per step
function mixSeed(base: number, step: number) {
  let x = (base ^ (step * 0x9e3779b1)) >>> 0;
  x ^= x << 13; x >>>= 0;
  x ^= x >> 17; x >>>= 0;
  x ^= x << 5;  x >>>= 0;
  return x >>> 0;
}

export function enterFreeSpins(configJson: any, pikachuScatterCount: number, seed: number, rows?: number, cols?: number): FreeSpinsState {
  const r = rows ?? (configJson?.grid?.rows ?? 7);
  const c = cols ?? (configJson?.grid?.cols ?? 7);
  const cfg: FreeSpinsConfig = configJson?.features?.freespins ?? {
    spinsByScatters: { '4': 10, '5': 12, '6': 15, '7': 20 },
    retriggerScatterCount: 3,
    retriggerSpins: 5,
  };
  const total = spinsForScatters(cfg, pikachuScatterCount);
  return {
    seed,
    spinsTotal: total,
    spinsLeft: total,
    stepIndex: 0,
    totalWinX: 0,
    multiplierMap: makeOnesMap(r, c),
    ended: total <= 0,
  };
}

export function stepFreeSpins(state: FreeSpinsState, configJson: any): FreeSpinsState {
  if (state.ended || state.spinsLeft <= 0) return state;

  const cfg: FreeSpinsConfig = configJson?.features?.freespins ?? {
    spinsByScatters: { '4': 10, '5': 12, '6': 15, '7': 20 },
    retriggerScatterCount: 3,
    retriggerSpins: 5,
  };

  const childSeed = mixSeed(state.seed, state.stepIndex);

  const res = spin(configJson, 1, { seed: childSeed, initMultiplierMap: state.multiplierMap as any });

  let spinsLeft = state.spinsLeft - 1;
  let totalWinX = state.totalWinX + (res.totalWinX ?? 0);
  const newMap: MultiplierMap = res.multiplierMap as any;

  // Retrigger on 3+ Pikachu scatters (if your grid produces them)
  const pikachu = countPikachuScatters(res.grid as any[][]);
  if (pikachu >= (cfg.retriggerScatterCount ?? 3)) {
    spinsLeft += cfg.retriggerSpins ?? 5;
    bumpAllByOne(newMap);
  }

  return {
    ...state,
    stepIndex: state.stepIndex + 1,
    spinsLeft,
    totalWinX,
    multiplierMap: newMap,
    ended: spinsLeft <= 0,
    lastSpin: { winX: res.totalWinX, events: res.events, grid: res.grid },
  };
}