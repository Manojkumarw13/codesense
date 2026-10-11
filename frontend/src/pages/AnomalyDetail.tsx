import { Link, useParams } from 'react-router-dom';
import { ApiError, apiClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import ErrorState from '../components/ui/ErrorState';
import Evidence from '../components/Evidence';
import Loading from '../components/ui/Loading';

type Loose = Record<string, unknown>;

function str(value: unknown): string | null {
  return typeof value === 'string' && value ? value : null;
}

function formatConfidence(value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  return value <= 1 ? `${Math.round(value * 100)}%` : String(value);
}

function formatNumber(value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  return String(Math.round(value * 100) / 100);
}

function formatDate(value: unknown): string {
  const raw = str(value);
  if (!raw) return '—';
  const time = new Date(raw).getTime();
  return Number.isNaN(time) ? raw : new Date(time).toLocaleString();
}

/** Anomaly detail: badges, meta table, related metrics, evidence, back link. */
export default function AnomalyDetail() {
  const { id = '' } = useParams();
  const anomaly = useApi(() => apiClient.getAnomaly(id), [id]);

  if (anomaly.loading) {
    return (
      <div>
        <h1>Anomaly</h1>
        <Loading />
      </div>
    );
  }

  // 404 and backend-DOWN both land here with a way back to the list.
  if (anomaly.error || !anomaly.data) {
    const message =
      anomaly.error instanceof ApiError && anomaly.error.status === 404
        ? 'Anomaly not found'
        : (anomaly.error?.message ?? 'Anomaly not found');
    return (
      <div>
        <h1>Anomaly</h1>
        <ErrorState message={message} />
        <p>
          <Link to="/app/anomalies">← Back to anomalies</Link>
        </p>
      </div>
    );
  }

  const item = anomaly.data;
  const extra = item as unknown as Loose;

  return (
    <div>
      <h1>{item.title || 'Untitled anomaly'}</h1>
      <p>
        {item.severity && <Badge severity={item.severity}>{item.severity}</Badge>}{' '}
        {str(extra.anomaly_type) && <span className="badge">{str(extra.anomaly_type)}</span>}
      </p>
      {item.description && <p className="page-sub">{item.description}</p>}
      <Card title="Details">
        <table className="meta-table">
          <tbody>
            <tr>
              <th scope="row">Detected</th>
              <td>{formatDate(extra.detected_at ?? extra.created_at)}</td>
            </tr>
            <tr>
              <th scope="row">Confidence</th>
              <td>{formatConfidence(item.confidence)}</td>
            </tr>
            <tr>
              <th scope="row">Baseline</th>
              <td className="tnum">{formatNumber(extra.baseline_value)}</td>
            </tr>
            <tr>
              <th scope="row">Observed</th>
              <td className="tnum">{formatNumber(extra.observed_value)}</td>
            </tr>
          </tbody>
        </table>
      </Card>
      <Card title="Related metrics">
        <table className="meta-table">
          <tbody>
            <tr>
              <th scope="row">Change</th>
              <td className="tnum">
                {typeof extra.change_percent === 'number' && Number.isFinite(extra.change_percent)
                  ? `${Math.round(extra.change_percent * 100) / 100}%`
                  : '—'}
              </td>
            </tr>
            <tr>
              <th scope="row">Metric</th>
              <td>{str(extra.metric_id) ?? str(extra.metric_name) ?? '—'}</td>
            </tr>
          </tbody>
        </table>
      </Card>
      <Card title="Evidence">
        <Evidence evidence={item.evidence} />
      </Card>
      <p>
        <Link to="/app/anomalies">← Back to anomalies</Link>
      </p>
    </div>
  );
}
