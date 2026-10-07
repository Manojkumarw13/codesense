// Gzip budget gate: fails the build if key chunks grow past their budgets.
// Usage: npm run build && npm run budgets
import { readdirSync, readFileSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { join } from 'node:path';

const DIST = new URL('../dist/assets/', import.meta.url).pathname;
const BUDGETS = [
  { pattern: /^ScoreCharts-.*\.js$/, maxGzipKb: 130, label: 'chart chunk (Recharts)' },
  { pattern: /^index-.*\.js$/, maxGzipKb: 60, label: 'initial route chunk' },
];

const files = readdirSync(DIST).filter((f) => f.endsWith('.js'));
let failed = false;
for (const { pattern, maxGzipKb, label } of BUDGETS) {
  const match = files.find((f) => pattern.test(f));
  if (!match) {
    console.error(`BUDGET MISSING: no file matching ${pattern}`);
    failed = true;
    continue;
  }
  const kb = gzipSync(readFileSync(join(DIST, match))).length / 1024;
  const ok = kb <= maxGzipKb;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${label}: ${match} = ${kb.toFixed(1)}KB gzip (budget ${maxGzipKb}KB)`);
  if (!ok) failed = true;
}
process.exit(failed ? 1 : 0);
