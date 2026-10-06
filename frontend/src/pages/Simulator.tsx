import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import EmptyArt from '../components/EmptyArt';

const SCENARIOS = [
  'NORMAL',
  'HIGH_LOAD',
  'REVIEW_BOTTLENECK',
  'CI_BOTTLENECK',
  'DEPLOYMENT_FAILURE',
  'INCIDENT_SPIKE',
  'RECOVERY',
];

export default function Simulator() {
  return (
    <div>
      <h2>Simulator</h2>
      <p className="muted">
        The external data source — service on <code>:8001</code>, live controls arrive next.
      </p>
      <Card title="Scenarios">
        <EmptyArt />
        <ul className="list">
          {SCENARIOS.map((s, i) => (
            <li key={s}>
              <strong>{s}</strong>{' '}
              <Badge tone={i === 0 ? 'ok' : 'low'}>{i === 0 ? 'STEADY' : 'ON DEMAND'}</Badge>
            </li>
          ))}
        </ul>
      </Card>
      <Card title="Controls">
        <p className="muted">START · STOP · PAUSE · RESUME · STATUS · SCENARIO</p>
      </Card>
    </div>
  );
}
