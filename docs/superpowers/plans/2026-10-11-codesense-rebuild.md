# CodeSense Rebuild (Dashboard + Landing) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild deleted `frontend/` as a premium Vite + shadcn/ui app with public landing (3 routes) plus full dashboard parity (14 pages + 3 detail routes), wired to real `/api/v1` and `:8001` simulator.

**Architecture:** Vite SPA with public layout (`/`, `/product`, `/docs`) and app shell (`/app/*`); single typed `apiClient` seam over list endpoints with `{items}` unwrap and UUID-gated filters; separate `simulatorClient` base; `AppContext` display state; lazy pages; Recharts in one lazy chunk; nginx `dist` + `dashboard` compose service.

**Tech Stack:** Vite 5 + React 18 + TypeScript strict + Tailwind + shadcn/ui + Recharts (named imports) + react-router-dom v6 + Vitest + Testing Library + Node budget/probe scripts.

**Spec:** `docs/superpowers/specs/2026-10-11-codesense-rebuild-design.md` (this plan argues from it; executors read both) + `PLAN.md` §§1–11 + `specs/phase-17-frontend-foundation.md` + `specs/phase-18-dashboards.md` + `specs/stripe-phase-01-tokens.md` through `specs/stripe-phase-09-final.md` + `docs/superpowers/plans/2026-10-07-codesense-frontend-rebuild.md` (dashboard tasks reused, landing added) + `docs/CodeSense — Application Flow.md` + live backend `backend/app/main.py:29-63` endpoint truth.

## Global Constraints

- React + TypeScript only; no Streamlit, no framework swap.
- Team-level only: never render identity; never send names/emails/usernames/IDs to LLM; 422 privacy-block renders fallback, never retries.
- Placeholder teams (`team-alpha`, `team-beta`) are display-only; never send non-UUID `team_id`/`organization_id`/`project_id` params (backend 422).
- Never fetch `GET /api/v1/metrics` as JSON (Prometheus text).
- Simulator is external (`:8001` start/stop/status/scenario); never write DB directly.
- Indigo `#533afd` family for CTA/link/focus only; ink scale for body; severity pairs for status.
- All motion honors `prefers-reduced-motion` (instant fallback); content visible by default.
- Gzip budgets: chart chunk ≤130KB, entry ≤60KB; `tsc --noEmit` clean every task.
- One task = one commit, independently testable; no next task until gate passes.

## Review Focus

- Placeholder team sent as UUID filter → 422: expect no filter sent until real UUIDs exist. Pinned in Task 1 (UUID gate test).
- `GET /metrics` parsed as JSON crashes client: expect no such method. Pinned in Task 1 (grep gate).
- Simulator down crashes page: expect offline card + fix hint. Pinned in Task 7.
- Empty DB looks broken: expect "run the simulator" guidance. Pinned in Tasks 4–6.
- AI unconfigured looks like error: expect calm fallback notice with core intact. Pinned in Task 7.

---

## File Structure

All under new `frontend/` (nothing on disk; plan creates): `package.json` (dev/build/typecheck/budgets/preview/test), `vite.config.ts` (`/api` proxy, chart chunk naming), `index.html` (Inter, title), `src/main.tsx`, `src/App.tsx` (public layout + app shell, lazy routes: `/`, `/product`, `/docs`, `/app/*` 14 pages + 3 details, `*` NotFound), `src/types.ts` (HealthScore, Insight, Anomaly, Bottleneck, MlModel, ExplainResponse, AiStatus, Paginated, TimeRange, DIMENSIONS), `src/api/client.ts` (apiClient + simulatorClient, ApiError, unwrap, UUID gate), `src/hooks/useApi.ts`, `src/context/AppContext.tsx`, `src/components/layout/` (PublicLayout, Layout, Sidebar, Header, TeamSelector, TimeRangeSelector, UserMenu), `src/components/ui/` (Button, Badge, Card, Input, Select, Table, Skeleton, Loading, EmptyState, ErrorState, Toast), `src/components/` (ScoreHero, DimensionBars, ScoreTrend, Evidence, SignalList, FilterBar, EmptyArt), `src/pages/` (Landing, Product, DocsEntry, Overview, Health, Delivery, Development, CICD, Reliability, Insights, InsightDetail, Anomalies, AnomalyDetail, Bottlenecks, BottleneckDetail, Trends, Integrations, Simulator, AIAnalysis, Settings, NotFound), `src/styles/tokens.css` + `index.css`, `scripts/check-budgets.mjs`, `scripts/probe-responsive.mjs`, `Dockerfile`; modify `docker-compose.yml` (add `dashboard`).

### Task 0: Readiness probe

**Files:**
- Create: `docs/superpowers/plans/readiness-2026-10-11.md`

**Interfaces:**
- Consumes: live `localhost:8000/api/v1/openapi.json`, `localhost:8001/simulator/status`.
- Produces: LIVE/DOWN verdict Tasks 1–7 use for live-vs-mock wiring.

- [ ] **Step 1: Probe backend and simulator**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/openapi.json; curl -s http://localhost:8001/simulator/status || echo SIMULATOR_DOWN
```

- [ ] **Step 2: Run and record verdict**

Run: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/openapi.json`
Expected: `200` = LIVE; else DOWN (continue, do not block).

- [ ] **Step 3: Write verdict file**

```markdown
BACKEND=LIVE|DOWN
SIMULATOR=LIVE|DOWN
ENDPOINTS: /health, /health-score, /insights, /anomalies, /bottlenecks, /ai/explain, /ai/status
WIRING: live where reachable, typed fallbacks otherwise; Simulator/AI pages always handle DOWN.
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/readiness-2026-10-11.md
git commit -m "docs: record backend/simulator readiness for dashboard+landing rebuild"
```

### Task 1: Scaffold, typed API seam, route table

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/types.ts`, `frontend/src/api/client.ts`, `frontend/src/api/client.test.ts`

**Interfaces:**
- Consumes: Task 0 base URLs.
- Produces: `apiClient` (ApiError, unwrap, UUID gate, no metrics-JSON) + public/app route table used by all later tasks.

- [ ] **Step 1: Write the failing client test**

```ts
import { describe, expect, it, vi } from 'vitest';
import { apiClient } from './client';
describe('apiClient', () => {
  it('unwraps {items} and never sends placeholder teams as UUID filters', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({ total: 1, skip: 0, limit: 100, items: [{ id: 'x' }] }) }));
    vi.stubGlobal('fetch', fetchMock);
    const rows = await apiClient.listAnomalies({ team_id: 'team-alpha' });
    expect(rows).toEqual([{ id: 'x' }]);
    expect(String(fetchMock.mock.calls[0][0])).not.toContain('team-alpha');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --prefix frontend -- src/api/client.test.ts`
Expected: FAIL (no client yet).

- [ ] **Step 3: Write scaffold + types + client**

`package.json` scripts: `dev` (vite), `build` (`tsc --noEmit && vite build`), `typecheck`, `budgets`, `preview`, `test` (vitest run). Deps: react, react-dom, react-router-dom, recharts; devDeps: typescript, vite, vitest, @testing-library/react. `vite.config.ts` with `/api` proxy to `http://localhost:8000`. `types.ts`: HealthScore, Insight, Anomaly, Bottleneck, Paginated, TimeRange, DIMENSIONS (6 health dimensions). `api/client.ts`:

```ts
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';
export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
async function get<T>(path: string, params: Record<string, string | undefined> = {}): Promise<T> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (!v) continue;
    if ((k === 'team_id' || k === 'organization_id' || k === 'project_id') && !UUID_RE.test(v)) continue;
    qs.set(k, v);
  }
  const res = await fetch(`${BASE_URL}${path}${qs.size ? `?${qs}` : ''}`);
  if (!res.ok) throw new ApiError(res.status, `${res.status} ${path}`);
  const body = await res.json();
  return (body && Array.isArray(body.items) ? body.items : body) as T;
}
```

Methods: `getHealth`, `getDetailedHealth`, `listHealthScores`, `getHealthScore`, `listInsights`, `getInsight`, `listAnomalies`, `getAnomaly`, `listBottlenecks`, `getBottleneck`, `getTeamRisk`, `listMlModels`, `getMlFeatures`, `getMlPredictions`, `getAiStatus`, `postAiExplain`, `listEvents`; `simulatorClient` on `SIM_BASE` with `getSimulatorStatus/startSimulator/stopSimulator/setSimulatorScenario`. `App.tsx`: public routes `/`, `/product`, `/docs` under `<PublicLayout/>`; `/app/*` 14 pages + 3 details under `<Layout/>` (stub passthrough `<Outlet/>` this task).

- [ ] **Step 4: Run tests and typecheck**

Run: `npm run test --prefix frontend -- src/api/client.test.ts && npm run typecheck --prefix frontend && grep -rn "metrics" frontend/src/api/client.ts | grep -iv prometheus || echo NO_METRICS_JSON`
Expected: PASS + `NO_METRICS_JSON`.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/index.html frontend/src/main.tsx frontend/src/App.tsx frontend/src/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts
git commit -m "feat(frontend): scaffold app with typed apiClient and route table"
```

### Task 2: Tokens, primitives, shell, state

**Files:**
- Create: `frontend/src/styles/tokens.css`, `frontend/src/styles/index.css`, `frontend/src/context/AppContext.tsx`, `frontend/src/hooks/useApi.ts`, `frontend/src/components/layout/PublicLayout.tsx`, `frontend/src/components/layout/Layout.tsx`, `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/components/layout/Header.tsx`, `frontend/src/components/layout/TeamSelector.tsx`, `frontend/src/components/layout/TimeRangeSelector.tsx`, `frontend/src/components/layout/UserMenu.tsx`, `frontend/src/components/ui/Button.tsx`, `frontend/src/components/ui/Badge.tsx`, `frontend/src/components/ui/Card.tsx`, `frontend/src/components/ui/Input.tsx`, `frontend/src/components/ui/Select.tsx`, `frontend/src/components/ui/Table.tsx`, `frontend/src/components/ui/Skeleton.tsx`, `frontend/src/components/ui/Loading.tsx`, `frontend/src/components/ui/EmptyState.tsx`, `frontend/src/components/ui/ErrorState.tsx`, `frontend/src/components/ui/Toast.tsx`

**Interfaces:**
- Consumes: Task 1 routes.
- Produces: themed shell + primitives every page uses.

- [ ] **Step 1: Write the failing shell test**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from './Layout';
describe('Layout', () => {
  it('exposes skip link, main landmark, aria-current nav', () => {
    render(<MemoryRouter initialEntries={['/app/health']}><Layout /></MemoryRouter>);
    expect(screen.getByText(/skip to content/i)).toBeTruthy();
    expect(document.querySelector('main#main-content')).toBeTruthy();
    expect(document.querySelector('[aria-current="page"]')).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --prefix frontend -- src/components/layout/Layout.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Write tokens, context, hook, shell, primitives**

`tokens.css`: `--bg #f6f9fc`, `--panel #fff`, `--ink #0d253d`, `--ink-2 #273951`, `--muted #5b6b83`, `--line #e3e8ee`, `--accent #533afd`, `--accent-deep #4434d4`, `--sidebar #1c1e54`, severity pairs, radius/spacing/shadow scales, `.tnum`, `.eyebrow`, `.skip-link`, `.scrim`, `.table-wrap`. `AppContext`: `{teamId='team-alpha', timeRange='30d'}` display-only. `useApi`: mount-safe `{data,loading,error}`. `Sidebar` groups Analyze/Flows/Signals/System via NavLink. `Layout`: skip link, eyebrow from route group, drawer + scrim + Escape under 768px. `Button`: pill, 40px min, press scale. `Badge`: soft-pill severity. `Card`: hairline + L1, hover L2.

- [ ] **Step 4: Run tests, typecheck, build**

Run: `npm run test --prefix frontend -- src/components/layout/Layout.test.tsx && npm run typecheck --prefix frontend && npm run build --prefix frontend`
Expected: PASS + `dist/`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/styles frontend/src/context frontend/src/hooks frontend/src/components/layout frontend/src/components/ui
git commit -m "feat(frontend): themed shell, primitives, and global state"
```

### Task 3: Landing (public routes)

**Files:**
- Create: `frontend/src/pages/Landing.tsx`, `frontend/src/pages/Product.tsx`, `frontend/src/pages/DocsEntry.tsx`

**Interfaces:**
- Consumes: Task 2 shell/primitives (no API dependency; static + optional score preview via `listHealthScores` with graceful empty).
- Produces: public site sharing tokens with dashboard.

- [ ] **Step 1: Write the failing landing test**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Landing from './Landing';
describe('Landing', () => {
  it('presents pipeline, privacy boundary, and app CTA', () => {
    render(<MemoryRouter><Landing /></MemoryRouter>);
    expect(screen.getByRole('heading', { name: /codesense/i })).toBeTruthy();
    expect(screen.getByText(/team-level/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: /open dashboard/i })).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --prefix frontend -- src/pages/Landing.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Write minimal pages**

`Landing`: hero (one h1, score-composition motif, CTA to `/app`), pipeline strip COLLECT→VISUALIZE, privacy boundary panel, dimensions overview (varied rows, not identical cards), scenario strip, footer. `Product`: flows + Score→Evidence chain. `DocsEntry`: links into `docs/` topics. Shared `PublicLayout` header/footer; no eyebrow-per-section; links indigo.

- [ ] **Step 4: Run tests and typecheck**

Run: `npm run test --prefix frontend -- src/pages/Landing.test.tsx && npm run typecheck --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Landing.tsx frontend/src/pages/Product.tsx frontend/src/pages/DocsEntry.tsx frontend/src/pages/Landing.test.tsx frontend/src/components/layout/PublicLayout.tsx
git commit -m "feat(frontend): public landing, product, and docs entry"
```

### Task 4: Overview + Health + Trends

**Files:**
- Create: `frontend/src/components/ScoreHero.tsx`, `frontend/src/components/DimensionBars.tsx`, `frontend/src/components/ScoreTrend.tsx`, `frontend/src/components/Evidence.tsx`, `frontend/src/pages/Overview.tsx`, `frontend/src/pages/Health.tsx`, `frontend/src/pages/Trends.tsx`, `frontend/src/pages/Overview.test.tsx`

**Interfaces:**
- Consumes: `listHealthScores`/`getHealthScore`, `useApi`, AppContext display team.
- Produces: score→dimensions→evidence pattern reused by Tasks 5–6.

- [ ] **Step 1: Write the failing empty-state test**

```tsx
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Overview from './Overview';
vi.mock('../api/client', () => ({ apiClient: { listHealthScores: async () => [], listInsights: async () => [], listAnomalies: async () => [], listBottlenecks: async () => [] } }));
describe('Overview', () => {
  it('guides fresh DBs to the simulator', async () => {
    render(<Overview />);
    expect(await screen.findByText(/run the simulator/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --prefix frontend -- src/pages/Overview.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Write pages and charts**

Overview: score card (score + period + delta + sparkline), signal counts as links. Health: DimensionBars from `component_metrics`, history table in `.table-wrap`, Evidence per row. Trends: full `ScoreTrend` (`role="img"`, aria-label) + table. Recharts named imports only. Each page: group eyebrow + one `h1`; Loading/Error/Empty states.

- [ ] **Step 4: Run tests and typecheck**

Run: `npm run test --prefix frontend -- src/pages/Overview.test.tsx && npm run typecheck --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ScoreHero.tsx frontend/src/components/DimensionBars.tsx frontend/src/components/ScoreTrend.tsx frontend/src/components/Evidence.tsx frontend/src/pages/Overview.tsx frontend/src/pages/Health.tsx frontend/src/pages/Trends.tsx frontend/src/pages/Overview.test.tsx
git commit -m "feat(frontend): overview, health, and trends score chain"
```

### Task 5: Flow pages + shared signal list

**Files:**
- Create: `frontend/src/pages/Delivery.tsx`, `frontend/src/pages/Development.tsx`, `frontend/src/pages/CICD.tsx`, `frontend/src/pages/Reliability.tsx`, `frontend/src/components/FilterBar.tsx`, `frontend/src/components/SignalList.tsx`, `frontend/src/components/SignalList.test.tsx`

**Interfaces:**
- Consumes: Task 4 pattern + filtered `listInsights/listAnomalies/listBottlenecks`.
- Produces: `SignalList`/`FilterBar` reused by Task 6.

- [ ] **Step 1: Write the failing list test**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SignalList from './SignalList';
describe('SignalList', () => {
  it('renders Open links and empty hint', () => {
    const { rerender } = render(<MemoryRouter><SignalList items={[{ id: '1', title: 'Review backlog rising', severity: 'HIGH' }]} basePath="/app/insights" /></MemoryRouter>);
    expect(screen.getByText(/review backlog rising/i)).toBeTruthy();
    rerender(<MemoryRouter><SignalList items={[]} basePath="/app/insights" emptyHint="run the simulator" /></MemoryRouter>);
    expect(screen.getByText(/run the simulator/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --prefix frontend -- src/components/SignalList.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Write pages**

Each flow page: dimension slice + related signals with `Open →` links; `FilterBar` severity/category selects (44px targets mobile).

- [ ] **Step 4: Run tests and typecheck**

Run: `npm run test --prefix frontend -- src/components/SignalList.test.tsx && npm run typecheck --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Delivery.tsx frontend/src/pages/Development.tsx frontend/src/pages/CICD.tsx frontend/src/pages/Reliability.tsx frontend/src/components/FilterBar.tsx frontend/src/components/SignalList.tsx frontend/src/components/SignalList.test.tsx
git commit -m "feat(frontend): flow pages with shared signal list and filters"
```

### Task 6: Signals + detail routes

**Files:**
- Create: `frontend/src/pages/Insights.tsx`, `frontend/src/pages/InsightDetail.tsx`, `frontend/src/pages/Anomalies.tsx`, `frontend/src/pages/AnomalyDetail.tsx`, `frontend/src/pages/Bottlenecks.tsx`, `frontend/src/pages/BottleneckDetail.tsx`, `frontend/src/pages/InsightDetail.test.tsx`

**Interfaces:**
- Consumes: Task 5 list/filter + `getInsight/getAnomaly/getBottleneck` + Evidence.
- Produces: full drill-down.

- [ ] **Step 1: Write the failing detail test**

```tsx
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import InsightDetail from './InsightDetail';
vi.mock('../api/client', () => ({ apiClient: { getInsight: async () => ({ id: '1', title: 'CI failure spike', severity: 'HIGH', category: 'CI', confidence: 0.82, evidence: { failed: 7 }, generated_by: 'ML_ENGINE', status: 'Active' }) } }));
describe('InsightDetail', () => {
  it('shows title, badges, evidence, back link', async () => {
    render(<MemoryRouter initialEntries={['/app/insights/1']}><Routes><Route path="/app/insights/:id" element={<InsightDetail />} /></Routes></MemoryRouter>);
    expect(await screen.findByText(/ci failure spike/i)).toBeTruthy();
    expect(screen.getByText(/back to insights/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --prefix frontend -- src/pages/InsightDetail.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Write lists + details**

Lists with filters; details with badges, meta table, Evidence, related metrics, back link; 404 → ErrorState.

- [ ] **Step 4: Run tests and typecheck**

Run: `npm run test --prefix frontend -- src/pages/InsightDetail.test.tsx && npm run typecheck --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Insights.tsx frontend/src/pages/InsightDetail.tsx frontend/src/pages/Anomalies.tsx frontend/src/pages/AnomalyDetail.tsx frontend/src/pages/Bottlenecks.tsx frontend/src/pages/BottleneckDetail.tsx frontend/src/pages/InsightDetail.test.tsx
git commit -m "feat(frontend): signal lists with evidence drill-down"
```

### Task 7: Simulator, AI, system pages

**Files:**
- Create: `frontend/src/pages/Simulator.tsx`, `frontend/src/pages/Simulator.test.tsx`, `frontend/src/pages/AIAnalysis.tsx`, `frontend/src/pages/Integrations.tsx`, `frontend/src/pages/Settings.tsx`, `frontend/src/pages/NotFound.tsx`

**Interfaces:**
- Consumes: `simulatorClient`, `getAiStatus/postAiExplain`, primitives.
- Produces: operable demo loop + honest AI fallback.

- [ ] **Step 1: Write the failing offline test**

```tsx
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Simulator from './Simulator';
vi.mock('../api/client', () => ({ simulatorClient: { getSimulatorStatus: async () => { throw new Error('down'); } } }));
describe('Simulator', () => {
  it('explains the fix when unreachable', async () => {
    render(<Simulator />);
    expect(await screen.findByText(/simulator unavailable/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --prefix frontend -- src/pages/Simulator.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Write pages**

Simulator: status card, start/stop, scenario select, offline EmptyState, toasts. AIAnalysis: status-gated fallback notice + on-demand explain with loading/error/fallback (422 → fallback content). Integrations/Settings: Phase 21/22 boundary placeholders. NotFound → `/`.

- [ ] **Step 4: Run tests and typecheck**

Run: `npm run test --prefix frontend -- src/pages/Simulator.test.tsx && npm run typecheck --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Simulator.tsx frontend/src/pages/Simulator.test.tsx frontend/src/pages/AIAnalysis.tsx frontend/src/pages/Integrations.tsx frontend/src/pages/Settings.tsx frontend/src/pages/NotFound.tsx
git commit -m "feat(frontend): simulator controls, AI fallback, system pages"
```

### Task 8: Responsive, motion, a11y

**Files:**
- Modify: `frontend/src/styles/index.css`, `frontend/src/components/layout/Layout.tsx`
- Create: `frontend/scripts/probe-responsive.mjs`

**Interfaces:**
- Consumes: Tasks 3–7 pages (CSS/shell only, no logic changes).
- Produces: 375/768/1024/1440 readiness with gated motion.

- [ ] **Step 1: Write the failing probe**

```js
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
const src = readFileSync(new URL('../src/styles/index.css', import.meta.url), 'utf8');
assert.match(src, /max-width:\s*1024px/, 'missing 1024px tier');
assert.match(src, /max-width:\s*768px/, 'missing drawer tier');
assert.match(src, /table-wrap[\s\S]*overflow-x:\s*auto/, 'missing table scroll');
assert.match(src, /prefers-reduced-motion/, 'missing reduced-motion guard');
console.log('responsive probe: PASS');
```

- [ ] **Step 2: Run probe to verify it fails**

Run: `node frontend/scripts/probe-responsive.mjs`
Expected: FAIL.

- [ ] **Step 3: Implement tiers, scrim, motion, semantics**

1024px content/grid tier; 768px drawer tier with scrim button + Escape; `.table-wrap` scroll; 44px targets; 150ms expo micro-motion; reduced-motion → 0.01ms; focus-visible indigo; h1 per page; chart `role="img"` labels.

- [ ] **Step 4: Run probe, tests, build**

Run: `node frontend/scripts/probe-responsive.mjs && npm run test --prefix frontend && npm run build --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/styles/index.css frontend/src/components/layout/Layout.tsx frontend/scripts/probe-responsive.mjs
git commit -m "feat(frontend): responsive tiers, gated motion, a11y pass"
```

### Task 9: Budgets + Docker

**Files:**
- Create: `frontend/scripts/check-budgets.mjs`, `frontend/Dockerfile`
- Modify: `docker-compose.yml`

**Interfaces:**
- Consumes: Task 8 `dist/`.
- Produces: enforced budgets + deployable dashboard.

- [ ] **Step 1: Write budget script and run**

```js
import { readdirSync, readFileSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { join } from 'node:path';
const dir = new URL('../dist/assets/', import.meta.url);
const rows = [];
for (const f of readdirSync(dir)) {
  if (!f.endsWith('.js')) continue;
  rows.push({ file: f, gzipKB: gzipSync(readFileSync(join(dir.pathname, f))).length / 1024 });
}
const chart = rows.filter(r => /ScoreCharts|ScoreTrend/.test(r.file)).reduce((a, r) => a + r.gzipKB, 0);
const entry = rows.filter(r => /^index-/.test(r.file)).reduce((a, r) => a + r.gzipKB, 0);
console.table(rows.map(r => ({ ...r, gzipKB: +r.gzipKB.toFixed(1) })));
let fail = false;
if (chart > 130) { console.error(`chart ${chart.toFixed(1)}KB > 130KB`); fail = true; }
if (entry > 60) { console.error(`entry ${entry.toFixed(1)}KB > 60KB`); fail = true; }
process.exit(fail ? 1 : 0);
```

Run: `npm run build --prefix frontend && npm run budgets --prefix frontend`
Expected: PASS (narrow to named Recharts imports if FAIL).

- [ ] **Step 2: Verify treeshake**

Run: `grep -rn "from 'recharts'" frontend/src | grep -v ScoreTrend | grep -v DimensionBars || echo TREESHAKE_OK`
Expected: `TREESHAKE_OK`.

- [ ] **Step 3: Add Dockerfile + compose service**

Dockerfile: node build → nginx serve `dist`. Compose: `dashboard` (port `3000:80`, depends on backend healthy, same network).

- [ ] **Step 4: Re-run gate**

Run: `npm run typecheck --prefix frontend && npm run build --prefix frontend && npm run budgets --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/scripts/check-budgets.mjs frontend/Dockerfile docker-compose.yml
git commit -m "feat(frontend): performance budgets and dashboard service"
```

### Task 10: Final validation + visual audit

**Files:**
- Modify: implicated `frontend/src/**` only (polish, no features).

**Interfaces:**
- Consumes: Tasks 0–9 + `docs/screenshots/` reference.
- Produces: shippable `frontend/`.

- [ ] **Step 1: Backend contract gate**

Run: `python -m pytest tests/ -x -q -k "not e2e" 2>&1 | tail -n 5`
Expected: PASS.

- [ ] **Step 2: Full frontend gate**

Run: `npm run typecheck --prefix frontend && npm run test --prefix frontend && npm run build --prefix frontend && npm run budgets --prefix frontend && node frontend/scripts/probe-responsive.mjs`
Expected: PASS all five; fix inline, re-run from start.

- [ ] **Step 3: Privacy + contrast audit**

Run: `grep -rni "developer.*productivity\|developer.*performance\|developer_rank\|user_name\|user_email" frontend/src || echo PRIVACY_OK`
Expected: `PRIVACY_OK`; verify ink/panel, muted/panel, badge pairs ≥4.5:1; record forced-colors verdict in commit body.

- [ ] **Step 4: Screenshot-compare landing + 14 app pages at 1440px/375px; fix inconsistencies inline; re-run Step 2.**

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(frontend): final validation and visual audit"
```
