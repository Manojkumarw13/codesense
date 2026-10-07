import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import EmptyArt from '../components/EmptyArt';
import { useApp } from '../context/AppContext';

const WEIGHTS = [
  ['Delivery Flow', '20%'],
  ['Development Flow', '20%'],
  ['Review Flow', '15%'],
  ['CI/CD Reliability', '15%'],
  ['Deployment Health', '15%'],
  ['Operational Health', '15%'],
];

export default function Settings() {
  const { teamId, timeRange } = useApp();
  return (
    <div>
      <h1>Settings</h1>
      <p className="muted">Workspace context and score configuration (read-only for now).</p>
      <Card title="Workspace">
        <p>
          Team <strong>{teamId}</strong> · Range <strong>{timeRange}</strong>{' '}
          <Badge tone="info">LOCAL PREVIEW</Badge>
        </p>
      </Card>
      <Card title="Health-score weights">
        <EmptyArt />
        <div className="table-wrap">
            <table className="table">
          <thead>
            <tr>
              <th>Dimension</th>
              <th>Weight</th>
            </tr>
          </thead>
          <tbody>
            {WEIGHTS.map(([dim, w]) => (
              <tr key={dim}>
                <td>{dim}</td>
                <td>{w}</td>
              </tr>
            ))}
          </tbody>
        </table>
            </div>
      </Card>
    </div>
  );
}
