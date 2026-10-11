import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { HealthScore } from '../types';

const PIPELINE = ['Collect', 'Normalize', 'Score', 'Visualize'] as const;

const DIMENSIONS: Array<{ name: string; detail: string }> = [
  { name: 'Delivery Flow', detail: 'Throughput and cycle time across the team backlog, rolled up weekly.' },
  { name: 'Development Flow', detail: 'Branch activity and review turnaround, aggregated per team.' },
  { name: 'Review Flow', detail: 'Pickup time, depth of review, and approval latency signals.' },
  { name: 'CI/CD Reliability', detail: 'Pipeline success rate, flaky-test load, and red-build recovery.' },
  { name: 'Deployment Health', detail: 'Release cadence, change-fail rate, and rollback frequency.' },
  { name: 'Operational Health', detail: 'Incident volume, detection speed, and recovery time trends.' },
];

const SCENARIOS = [
  'Sprint review: walk stakeholders through the score trend, not raw activity.',
  'Retrospective: open the lowest dimension and read its linked evidence.',
  'Planning: compare scenario forecasts before committing to scope.',
] as const;

export default function Landing() {
  const [preview, setPreview] = useState<HealthScore[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const scores = await apiClient.listHealthScores();
        if (!cancelled && Array.isArray(scores)) setPreview(scores.slice(0, 3));
      } catch {
        if (!cancelled) setPreview([]);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="public-main">
      <section aria-labelledby="landing-hero">
        <h1 id="landing-hero">CodeSense</h1>
        <p>
          Team-level engineering health, composed from six dimensions into one
          honest score: Delivery 30 + Development 20 + Review 15 + CI/CD 15 +
          Deployment 10 + Operations 10.
        </p>
        <p>
          <Link to="/app">Open dashboard</Link>
          {' · '}
          <Link to="/product">See how it works</Link>
        </p>
        {preview.length > 0 && (
          <ul aria-label="Latest score preview">
            {preview.map((s) => (
              <li key={s.id} className="tnum">
                Team score {s.score}
                {s.score_change != null ? ` (${s.score_change >= 0 ? '+' : ''}${s.score_change})` : ''}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-label="Pipeline">
        <h2>From raw signals to decisions</h2>
        <ol>
          {PIPELINE.map((stage, i) => (
            <li key={stage}>
              {stage}
              {i < PIPELINE.length - 1 ? ' →' : ''}
            </li>
          ))}
        </ol>
      </section>

      <section aria-label="Privacy boundary">
        <h2>Privacy boundary</h2>
        <p>
          CodeSense scores teams, never individuals. Raw events stay behind the
          API; the dashboard only receives aggregated team scores and linked
          evidence. No per-developer surveillance, no keystroke tracking.
        </p>
      </section>

      <section aria-label="Health dimensions">
        <h2>Six dimensions, one score</h2>
        <dl>
          {DIMENSIONS.map((d) => (
            <div key={d.name}>
              <dt>{d.name}</dt>
              <dd>{d.detail}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-label="Scenarios">
        <h2>Built for team rituals</h2>
        <ul>
          {SCENARIOS.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
