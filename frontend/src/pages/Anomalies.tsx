import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
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

export default function Anomalies() {
  const { teamId } = useApp();
  const anomalies = useApi(() => apiClient.listAnomalies({ limit: 100 }));
  const [severity, setSeverity] = useState('');

  const severities = useMemo(
    () => [...new Set((anomalies.data ?? []).map((a) => a.severity).filter(Boolean))],
    [anomalies.data],
  );
  const filtered = (anomalies.data ?? []).filter((a) => !severity || a.severity === severity);

  if (anomalies.loading) return <Loading />;
  if (anomalies.error) return <ErrorState message={anomalies.error} />;

  return (
    <div>
      <h1>Anomalies</h1>
      <p className="muted">
        Team <strong>{teamId}</strong> · Rules + Stats + ML fused detections
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
      </div>
      {filtered.length === 0 ? (
        <Card title="No anomalies">
          <EmptyArt />
          <EmptyState message="No anomalies detected. Bottleneck simulator scenarios produce detections." />
        </Card>
      ) : (
        <div className="table-wrap">
            <table className="table">
          <thead>
            <tr>
              <th>Detected</th>
              <th>Observed</th>
              <th>Baseline</th>
              <th>Change</th>
              <th>Severity</th>
              <th>Confidence</th>
              <th>Evidence</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.detected_at).toLocaleString()}</td>
                <td>{a.observed_value}</td>
                <td>{a.baseline_value ?? '—'}</td>
                <td>{a.change_percent != null ? `${a.change_percent.toFixed(1)}%` : '—'}</td>
                <td><Badge tone={a.severity.toLowerCase()}>{a.severity}</Badge></td>
                <td>{a.confidence != null ? a.confidence.toFixed(2) : '—'}</td>
                <td><Evidence data={a.evidence} /><br /><Link to={`/anomalies/${a.id}`}>Open →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
            </div>
      )}
    </div>
  );
}
