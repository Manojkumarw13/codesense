import Card from '../components/ui/Card';

export default function CICD() {
  return (
    <div>
      <h2>CI/CD</h2>
      <p className="muted">Build success, pipeline duration, deployment health — Phase 18.</p>
      <Card title="Placeholder">
        <p className="muted">Connects to GET /api/v1/metrics/*values.</p>
      </Card>
    </div>
  );
}
