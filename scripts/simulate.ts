import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spin } from '../src/js/engine/engine.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const configPath = resolve(__dirname, '..', '..', 'config.json');
const config = JSON.parse(readFileSync(configPath, 'utf-8'));

const args = new Map<string, string>();
process.argv.slice(2).forEach((a) => {
  const [k, v] = a.startsWith('--') ? a.slice(2).split('=') : [a, 'true'];
  args.set(k, v ?? 'true');
});
const spins = Number(args.get('spins') ?? 10000);

let total = 0;
let hits = 0;
for (let i = 0; i < spins; i++) {
  const res = spin(config, 1, { seed: (123456789 + i) >>> 0 });
  total += res.totalWinX;
  if (res.totalWinX > 0) hits++;
}
const rtp = total / spins;
const hitRate = hits / spins;

console.log(JSON.stringify({ spins, rtp, hitRate }, null, 2));