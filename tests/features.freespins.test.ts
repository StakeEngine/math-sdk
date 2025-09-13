import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, it, expect } from 'vitest';
import { enterFreeSpins, stepFreeSpins } from '../src/js/features/freespins.ts';

const config = JSON.parse(readFileSync(resolve(process.cwd(), 'config.json'), 'utf-8'));
describe('Free Spins', () => {
  it('is deterministic for a given seed and trigger count', () => {
    const seed = 4242;
    let a = enterFreeSpins(config, 4, seed);
    let b = enterFreeSpins(config, 4, seed);
    for (let i = 0; i < 3; i++) {
      a = stepFreeSpins(a, config);
      b = stepFreeSpins(b, config);
      expect(a.totalWinX).toBeCloseTo(b.totalWinX, 8);
      expect(a.spinsLeft).toBe(b.spinsLeft);
      expect(a.multiplierMap.length).toBe(b.multiplierMap.length);
      expect(a.multiplierMap[0].length).toBe(b.multiplierMap[0].length);
    }
  });

  it('multiplier map shape matches grid config', () => {
    const seed = 777;
    const rows = config.grid?.rows ?? 7;
    const cols = config.grid?.cols ?? 7;
    const s0 = enterFreeSpins(config, 4, seed, rows, cols);
    expect(s0.multiplierMap.length).toBe(rows);
    expect(s0.multiplierMap[0].length).toBe(cols);
  });
});