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

function formatDate(value: unknown): string {
  const raw = str(value);
  if (!raw) return '—';
  const time = new Date(raw).getTime();
  return Number.isNaN(time) ? raw : new Date(time).toLocaleString();
}

function metricEntries(value: unknown): Array<[string, string]> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return [];
  return (Object.entries(value as Loose) as Array<[string, unknown]>)
    .filter(([, val]) => typeof val === 'number' || typeof val === 'string')
    .map(([key, val]) => [key, String(val)]);
}

/** Bottleneck detail: badges, meta table, related metrics, evidence, back link. */
export default function BottleneckDetail() {
  const { id = '' } = useParams();
  const bottleneck = useApi(() => apiClient.getBottleneck(id), [id]);

  if (bottleneck.loading) {
    return (
      <div>
        <h1>Bottleneck</h1>
        <Loading />
      </div>
    );
  }

  // 404 and backend-DOWN both land here with a way back to the list.
  if (bottleneck.error || !bottleneck.data) {
    const message =
      bottleneck.error instanceof ApiError && bottleneck.error.status === 404
        ? 'Bottleneck not found'
        : (bottleneck.error?.message ?? 'Bottleneck not found');
    return (
      <div>
        <h1>Bottleneck</h1>
        <ErrorState message={message} />
        <p>
          <Link to="/app/bottlenecks">← Back to bottlenecks</Link>
        </p>
      </div>
    );
  }

  const item = bottleneck.data;
  const extra = item as unknown as Loose;
  const metrics = metricEntries(item.evidence);

  return (
    <div>
      <h1>{item.title || 'Untitled bottleneck'}</h1>
      <p>
        {item.severity && <Badge severity={item.severity}>{item.severity}</Badge>}{' '}
        {item.category && <span className="badge">{item.category}</span>}
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
              <th scope="row">Category</th>
              <td>{item.category || '—'}</td>
            </tr>
            <tr>
              <th scope="row">Severity</th>
              <td>{item.severity || '—'}</td>
            </tr>
            <tr>
              <th scope="row">Status</th>
              <td>{str(extra.status) ?? '—'}</td>
            </tr>
          </tbody>
        </table>
      </Card>
      {metrics.length > 0 && (
        <Card title="Related metrics">
          <table className="meta-table">
            <tbody>
              {metrics.map(([key, value]) => (
                <tr key={key}>
                  <th scope="row">{key}</th>
                  <td className="tnum">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      <Card title="Evidence">
        <Evidence evidence={item.evidence} />
      </Card>
      <p>
        <Link to="/app/bottlenecks">← Back to bottlenecks</Link>
      </p>
    </div>
  );
}
