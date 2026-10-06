import Card from '../components/ui/Card';

export default function Health() {
  return (
    <div>
      <h2>Engineering Health</h2>
      <p className="muted">Score → Dimension → Metric → Evidence drill-down arrives in Phase 18.</p>
      <Card title="Placeholder">
        <p className="muted">Connects to GET /api/v1/health-score.</p>
      </Card>
    </div>
  );
}
