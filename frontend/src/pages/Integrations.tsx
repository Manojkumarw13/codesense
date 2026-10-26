import { Link } from 'react-router-dom';
import Card from '../components/ui/Card';

/** Integrations: honest Phase 21/22 boundary placeholder. */
export default function Integrations() {
  return (
    <div>
      <h1>Integrations</h1>
      <p className="page-sub">External providers land here in Phase 21.</p>
      <Card title="Planned providers">
        <ol className="provider-list">
          <li>GitHub</li>
          <li>GitLab</li>
          <li>Jira</li>
          <li>CI/CD</li>
        </ol>
        <p className="state-hint">
          Integrations are not connected yet. Provider setup arrives with the Phase 21 boundary.
        </p>
        <Link to="/app/simulator">Run the simulator meanwhile</Link>
      </Card>
    </div>
  );
}
