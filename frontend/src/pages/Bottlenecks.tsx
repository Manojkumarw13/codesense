import { useMemo, useState } from 'react';
import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Loading from '../components/ui/Loading';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';
import Evidence from '../components/Evidence';
import EmptyArt from '../components/EmptyArt';

export default function Bottlenecks() {
  const { teamId } = useApp();
  const bottlenecks = useApi(() => apiClient.listBottlenecks({ limit: 100 }));
  const [severity, setSeverity] = useState('');
  const [category, setCategory] = useState('');

  const severities = useMemo(
    () => [...new Set((bottlenecks.data ?? []).map((b) => b.severity).filter(Boolean))],
    [bottlenecks.data],
  );
  const categories = useMemo(
    () => [...new Set((bottlenecks.data ?? []).map((b) => b.category).filter(Boolean))],
    [bottlenecks.data],
  );
  const filtered = (bottlenecks.data ?? []).filter(
    (b) =>
      (!severity || b.severity === severity) && (!category || b.category === category),
  );

  if (bottlenecks.loading) return <Loading />;
  if (bottlenecks.error) return <ErrorState message={bottlenecks.error} />;

  return (
    <div>
      <h2>Bottlenecks</h2>
      <p className="muted">
        Team <strong>{teamId}</strong> · Review / CI / Deployment / Workflow / Incident
      </p>
      <div className="filters">
        <label className="selector">
          Severity
          <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="">All</option>
            {severities.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>
        <label className="selector">
          Category
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>
      {filtered.length === 0 ? (
        <Card title="No bottlenecks">
          <EmptyArt />
          <EmptyState message="No bottlenecks detected. Review/CI/deployment simulator scenarios produce detections." />
        </Card>
      ) : (
        <ul className="list cards">
          {filtered.map((b) => (
            <li key={b.id}>
              <Card title={b.title}>
                {b.description && <p>{b.description}</p>}
                <p className="muted">
                  <Badge tone={b.severity.toLowerCase()}>{b.severity}</Badge>{' '}
                  <Badge tone="info">{b.category}</Badge>{' '}
                  <span>{new Date(b.detected_at).toLocaleString()}</span>
                </p>
                <Evidence data={b.evidence} />
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
