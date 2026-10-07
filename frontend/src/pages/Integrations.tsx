import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import EmptyArt from '../components/EmptyArt';

const ROADMAP = [
  { name: 'GitHub', state: 'Next — Phase 21', tone: 'info' },
  { name: 'GitLab', state: 'Queued', tone: 'low' },
  { name: 'Jira', state: 'Queued', tone: 'low' },
  { name: 'CI/CD providers', state: 'Queued', tone: 'low' },
];

export default function Integrations() {
  return (
    <div>
      <h1>Integrations</h1>
      <p className="muted">Real providers land in Phase 21 — simulator data flows today.</p>
      <Card title="Provider roadmap">
        <EmptyArt />
        <ul className="list">
          {ROADMAP.map((p) => (
            <li key={p.name}>
              <strong>{p.name}</strong> <Badge tone={p.tone}>{p.state}</Badge>
            </li>
          ))}
        </ul>
      </Card>
      <Card title="Current source">
        <p className="muted">
          The standalone simulator posts through <code>/api/v1/events</code> — the same
          pipeline real providers will use, so analytics are provider-agnostic by construction.
        </p>
      </Card>
    </div>
  );
}
