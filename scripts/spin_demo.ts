import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spin } from '../src/js/engine/engine.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const configPath = resolve(__dirname, '..', '..', 'config.json'); // root/config.json
const config = JSON.parse(readFileSync(configPath, 'utf-8'));

const seed = Date.now();
const res = spin(config as any, 1, { seed });

const wins = (res.events || []).filter((e: any) => e.type === 'win');
console.log(JSON.stringify({
  seed,
  totalWinX: res.totalWinX,
  wins: wins.map((w: any) => ({
    size: w.payload?.size,
    tier: w.payload?.symbol?.tier,
    mult: w.payload?.multiplier,
    winAmount: w.payload?.winAmount
  })),
  eventTypes: (res.events || []).map((e: any) => e.type)
}, null, 2));
