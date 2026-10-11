import { Link } from 'react-router-dom';

const FLOWS = [
  {
    name: 'Team health tracking',
    detail: 'Connect a repo once; nightly scoring rolls delivery, review, CI/CD, deployment, and operations signals into a team-level trend.',
  },
  {
    name: 'Evidence-backed retros',
    detail: 'Every score links down to the dimensions, insights, and anomalies behind it, so the conversation starts from facts.',
  },
  {
    name: 'What-if simulation',
    detail: 'Run scenarios against the current baseline to forecast how staffing or scope changes move the score before you commit.',
  },
] as const;

const CHAIN = [
  { level: 'Score', detail: 'One team-level number per scoring run, with change since the previous run.' },
  { level: 'Dimensions', detail: 'Six weighted dimensions explain where the score moved.' },
  { level: 'Insights', detail: 'Generated findings narrate the movement in plain language.' },
  { level: 'Evidence', detail: 'Anomalies and bottlenecks link each insight to concrete signals.' },
] as const;

export default function Product() {
  return (
    <main className="public-main">
      <h1>Product</h1>
      <p>
        CodeSense turns engineering signals into team-level health you can act
        on. <Link to="/app">Open dashboard</Link> to explore live data, or read
        the <Link to="/docs">docs</Link> for background.
      </p>

      <section aria-label="Flows">
        <h2>Flows</h2>
        <ul>
          {FLOWS.map((f) => (
            <li key={f.name}>
              <h3>{f.name}</h3>
              <p>{f.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-label="Score to evidence chain">
        <h2>Score → Evidence chain</h2>
        <ol>
          {CHAIN.map((c) => (
            <li key={c.level}>
              <h3>{c.level}</h3>
              <p>{c.detail}</p>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
