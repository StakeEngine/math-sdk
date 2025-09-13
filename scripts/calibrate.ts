import { readFileSync, writeFileSync } from 'node:fs';
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
const spins = Number(args.get('spins') ?? 100000);
const targetRTP = Number(args.get('targetRTP') ?? 0.95);
const write = args.get('write') === 'true' || args.get('write') === '1';

const currentFactor = config.engine?.demo?.baseFactor ?? 0.25;

let total = 0;
for (let i = 0; i < spins; i++) {
  const res = spin(config, 1, { seed: (123456789 + i) >>> 0 });
  total += res.totalWinX;
}
const rtp = total / spins;
const recommended = currentFactor * (targetRTP / (rtp || 1e-9));

const out = { spins, rtp, targetRTP, currentFactor, recommendedFactor: recommended };
console.log(JSON.stringify(out, null, 2));

if (write) {
  config.engine = config.engine ?? {};
  config.engine.demo = config.engine.demo ?? {};
  config.engine.demo.baseFactor = recommended;
  writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log(`Wrote baseFactor=${recommended.toFixed(6)} to config.json`);
}