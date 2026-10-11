import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
const src = readFileSync(new URL('../src/styles/index.css', import.meta.url), 'utf8');
assert.match(src, /max-width:\s*1024px/, 'missing 1024px tier');
assert.match(src, /max-width:\s*768px/, 'missing drawer tier');
assert.match(src, /table-wrap[\s\S]*overflow-x:\s*auto/, 'missing table scroll');
assert.match(src, /prefers-reduced-motion/, 'missing reduced-motion guard');
console.log('responsive probe: PASS');
