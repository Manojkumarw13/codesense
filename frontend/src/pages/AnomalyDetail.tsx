import { Link, useParams } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Loading from '../components/ui/Loading';
import ErrorState from '../components/ui/ErrorState';
import Evidence from '../components/Evidence';

export default function AnomalyDetail() {
  const { id = '' } = useParams();
  const anomaly = useApi(() => apiClient.getAnomaly(id), [id]);

  if (anomaly.loading) return <Loading />;
  if (anomaly.error) return <ErrorState message={anomaly.error} />;
  const item = anomaly.data;
  if (!item) return <ErrorState message="Anomaly not found." />;

  return (
    <div>
      <p className="muted">
        <Link to="/anomalies">← All anomalies</Link>
      </p>
      <h1>
        Anomaly <Badge tone={item.severity.toLowerCase()}>{item.severity}</Badge>
      </h1>
      <p className="muted">Detected {new Date(item.detected_at).toLocaleString()}</p>
      <Card title="Observed vs baseline">
        <div className="table-wrap">
            <table className="table">
          <tbody>
            <tr>
              <td>Observed</td>
              <td>{item.observed_value}</td>
            </tr>
            <tr>
              <td>Baseline</td>
              <td>{item.baseline_value ?? '—'}</td>
            </tr>
            <tr>
              <td>Change</td>
              <td>{item.change_percent != null ? `${item.change_percent.toFixed(1)}%` : '—'}</td>
            </tr>
            <tr>
              <td>Confidence</td>
              <td>{item.confidence != null ? item.confidence.toFixed(2) : '—'}</td>
            </tr>
          </tbody>
        </table>
            </div>
      </Card>
      <Card title="Evidence">
        <Evidence data={item.evidence} />
      </Card>
    </div>
  );
}
