import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Loading from '../components/ui/Loading';
import ErrorState from '../components/ui/ErrorState';

export default function Overview() {
  const { teamId, timeRange } = useApp();
  const [backend, setBackend] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .getHealth()
      .then((h) => setBackend(h.status))
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div>
      <h2>Overview</h2>
      <p className="muted">
        Team <strong>{teamId}</strong> · Range <strong>{timeRange}</strong> · Full
        dashboard arrives in Phase 18.
      </p>
      <div className="grid">
        <Card title="Backend">
          {error ? (
            <ErrorState message={`API unreachable: ${error}`} />
          ) : backend ? (
            <Badge tone="ok">{backend}</Badge>
          ) : (
            <Loading label="Checking API…" />
          )}
        </Card>
        <Card title="Health Score">
          <p className="muted">Score, change and dimensions wire up in Phase 18.</p>
        </Card>
        <Card title="Active Signals">
          <p className="muted">Bottlenecks, anomalies and insights wire up in Phase 18.</p>
        </Card>
      </div>
    </div>
  );
}
