import Card from '../components/ui/Card';

export default function Trends() {
  return (
    <div>
      <h2>Trends</h2>
      <p className="muted">Historical baselines and % change — Phase 18.</p>
      <Card title="Placeholder">
        <p className="muted">Connects to GET /api/v1/metrics/*values.</p>
      </Card>
    </div>
  );
}
