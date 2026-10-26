import { Link } from 'react-router-dom';

const TOPICS = [
  { id: 'product-requirements', file: 'CodeSense — Product Requirements Document (PRD).md', detail: 'What CodeSense measures and why: team-level health, privacy constraints, and scope.' },
  { id: 'system-architecture', file: 'CodeSense — System Architecture.md', detail: 'Backend, simulator, and frontend services and how they fit together.' },
  { id: 'api-specification', file: 'CodeSense — API Specification.md', detail: 'REST endpoints, envelopes, and error codes served under /api/v1.' },
  { id: 'data-flow', file: 'CodeSense — Data Flow.md', detail: 'How raw events become scores, insights, and dashboard views.' },
  { id: 'ai-data-boundary', file: 'CodeSense — AI Data Boundary.md', detail: 'What AI providers may receive and the team-level aggregation rule.' },
  { id: 'application-flow', file: 'CodeSense — Application Flow.md', detail: 'End-to-end user journeys across landing, dashboard, and simulator.' },
  { id: 'acceptance-tests', file: 'CodeSense — Acceptance Tests.md', detail: 'Acceptance criteria the rebuild is verified against.' },
] as const;

export default function DocsEntry() {
  return (
    <main className="public-main">
      <h1>Docs</h1>
      <p>
        Background reading lives in the in-repo <code>docs/</code> folder. Start
        with the topics below, or <Link to="/app">open the dashboard</Link> to
        see the concepts live.
      </p>
      <ul aria-label="Documentation topics">
        {TOPICS.map((t) => (
          <li key={t.id}>
            <a href={`#${t.id}`}>{t.file}</a>
          </li>
        ))}
      </ul>
      {TOPICS.map((t) => (
        <section key={t.id} id={t.id} aria-label={t.file}>
          <h2>{t.file}</h2>
          <p>{t.detail}</p>
        </section>
      ))}
    </main>
  );
}
