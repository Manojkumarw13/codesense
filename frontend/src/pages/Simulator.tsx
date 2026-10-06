import Card from '../components/ui/Card';

export default function Simulator() {
  return (
    <div>
      <h2>Simulator</h2>
      <p className="muted">Controls: START / STOP / PAUSE / RESUME / STATUS / SCENARIO.</p>
      <Card title="Placeholder">
        <p className="muted">Simulator service runs on :8001; controls wire up in Phase 18.</p>
      </Card>
    </div>
  );
}
