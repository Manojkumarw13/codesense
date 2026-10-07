import { Link, useParams } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Loading from '../components/ui/Loading';
import ErrorState from '../components/ui/ErrorState';
import Evidence from '../components/Evidence';

export default function BottleneckDetail() {
  const { id = '' } = useParams();
  const bottleneck = useApi(() => apiClient.getBottleneck(id), [id]);

  if (bottleneck.loading) return <Loading />;
  if (bottleneck.error) return <ErrorState message={bottleneck.error} />;
  const item = bottleneck.data;
  if (!item) return <ErrorState message="Bottleneck not found." />;

  return (
    <div>
      <p className="muted">
        <Link to="/bottlenecks">← All bottlenecks</Link>
      </p>
      <h2>{item.title}</h2>
      <p className="muted">
        <Badge tone={item.severity.toLowerCase()}>{item.severity}</Badge>{' '}
        <Badge tone="info">{item.category}</Badge>{' '}
        <span>{new Date(item.detected_at).toLocaleString()}</span>
      </p>
      {item.description && (
        <Card title="Summary">
          <p>{item.description}</p>
        </Card>
      )}
      <Card title="Evidence">
        <Evidence data={item.evidence} />
      </Card>
    </div>
  );
}
