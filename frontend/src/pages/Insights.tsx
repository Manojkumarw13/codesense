import Card from '../components/ui/Card';

export default function Insights() {
  return (
    <div>
      <h2>Insights</h2>
      <p className="muted">Detected → Active → Reviewed → Resolved → Archived — Phase 18.</p>
      <Card title="Placeholder">
        <p className="muted">Connects to GET /api/v1/insights.</p>
      </Card>
    </div>
  );
}
