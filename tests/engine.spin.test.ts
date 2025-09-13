import { readFileSync } from 'node:fs';import { resolve } from 'node:path';import { describe, it, expect } from 'vitest';import { spin } from '../src/js/engine/engine.js';const config = JSON.parse(readFileSync(resolve(process.cwd(), 'config.json'), 'utf-8'));describe('spin() contract', () => {  it('emits spinStart and spinEnd, totalWinX equals sum of win events', () => {    const seed = 4242;    const res = spin(config, 1, { seed });    expect(res.events[0].type).toBe('spinStart');    expect(res.events.at(-1)?.type).toBe('spinEnd');    const wins = res.events.filter(e => e.type === 'win');
    const sum = wins.reduce((a, w) => a + (w.payload?.winAmount ?? 0), 0);
    expect(res.totalWinX).toBeCloseTo(sum, 8);
  });

  it('is deterministic for a given seed', () => {
    const seed = 1337;
    const a = spin(config, 1, { seed });
    const b = spin(config, 1, { seed });
    expect(a.totalWinX).toBeCloseTo(b.totalWinX, 8);
    expect(a.events.map(e => e.type)).toEqual(b.events.map(e => e.type));
  });
});