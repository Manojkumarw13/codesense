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

export default function Insights() {
  const { teamId } = useApp();
  const insights = useApi(() => apiClient.listInsights({ limit: 100 }));
  const [severity, setSeverity] = useState('');
  const [category, setCategory] = useState('');

  const severities = useMemo(
    () => [...new Set((insights.data ?? []).map((i) => i.severity).filter(Boolean))] as string[],
    [insights.data],
  );
  const categories = useMemo(
    () => [...new Set((insights.data ?? []).map((i) => i.category).filter(Boolean))] as string[],
    [insights.data],
  );
  const filtered = (insights.data ?? []).filter(
    (i) =>
      (!severity || i.severity === severity) && (!category || i.category === category),
  );

  if (insights.loading) return <Loading />;
  if (insights.error) return <ErrorState message={insights.error} />;

  return (
    <div>
      <h2>Insights</h2>
      <p className="muted">
        Team <strong>{teamId}</strong> · Detected → Active → Reviewed → Resolved → Archived
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
        <Card title="No insights">
          <EmptyState message="No insights match. Run the simulator to generate engineering events." />
        </Card>
      ) : (
        <ul className="list cards">
          {filtered.map((i) => (
            <li key={i.id}>
              <Card title={i.title}>
                <p>{i.content}</p>
                <p className="muted">
                  {i.severity && <Badge tone={i.severity.toLowerCase()}>{i.severity}</Badge>}{' '}
                  {i.category && <Badge tone="info">{i.category}</Badge>}{' '}
                  <span>by {i.generated_by}</span>{' '}
                  {i.confidence != null && <span>conf {i.confidence.toFixed(2)}</span>}{' '}
                  <span>{new Date(i.created_at).toLocaleString()}</span>
                </p>
                <Evidence data={{ evidence: i.evidence, source_metrics: i.source_metrics }} />
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
