import { Link, useParams } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Loading from '../components/ui/Loading';
import ErrorState from '../components/ui/ErrorState';
import Evidence from '../components/Evidence';

export default function InsightDetail() {
  const { id = '' } = useParams();
  const insight = useApi(() => apiClient.getInsight(id), [id]);

  if (insight.loading) return <Loading />;
  if (insight.error) return <ErrorState message={insight.error} />;
  const item = insight.data;
  if (!item) return <ErrorState message="Insight not found." />;

  return (
    <div>
      <p className="muted">
        <Link to="/insights">← All insights</Link>
      </p>
      <h1>{item.title}</h1>
      <p className="muted">
        {item.severity && <Badge tone={item.severity.toLowerCase()}>{item.severity}</Badge>}{' '}
        {item.category && <Badge tone="info">{item.category}</Badge>}{' '}
        <span>
          by {item.generated_by} · {item.status} · {new Date(item.created_at).toLocaleString()}
        </span>{' '}
        {item.confidence != null && <span>conf {item.confidence.toFixed(2)}</span>}
      </p>
      <Card title="Summary">
        <p>{item.content}</p>
      </Card>
      <Card title="Evidence & related metrics">
        <Evidence data={{ evidence: item.evidence, source_metrics: item.source_metrics }} />
      </Card>
    </div>
  );
}
