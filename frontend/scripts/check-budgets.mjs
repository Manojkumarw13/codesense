import { readdirSync, readFileSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { join } from 'node:path';
const dir = new URL('../dist/assets/', import.meta.url);
const rows = [];
for (const f of readdirSync(dir)) {
  if (!f.endsWith('.js')) continue;
  rows.push({ file: f, gzipKB: gzipSync(readFileSync(join(dir.pathname, f))).length / 1024 });
}
// Chart chunks: ScoreTrend/DimensionBars component chunks plus the Recharts
// vendor chunk. Vite/Rollup names the shared Recharts chunk after its largest
// internal module (generateCategoricalChart); update this pattern if a Recharts
// upgrade changes the emitted chunk name (run build and check dist/assets).
const chart = rows.filter(r => /ScoreCharts|ScoreTrend|DimensionBars|generateCategoricalChart/.test(r.file)).reduce((a, r) => a + r.gzipKB, 0);
const entry = rows.filter(r => /^index-/.test(r.file)).reduce((a, r) => a + r.gzipKB, 0);
console.table(rows.map(r => ({ ...r, gzipKB: +r.gzipKB.toFixed(1) })));
let fail = false;
if (chart > 130) { console.error(`chart ${chart.toFixed(1)}KB > 130KB`); fail = true; }
if (entry > 60) { console.error(`entry ${entry.toFixed(1)}KB > 60KB`); fail = true; }
process.exit(fail ? 1 : 0);
