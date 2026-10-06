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
import ScoreTrend from '../components/charts/ScoreTrend';
import DimensionBars from '../components/charts/DimensionBars';

export default function Overview() {
  const { teamId, timeRange } = useApp();
  const scores = useApi(() => apiClient.listHealthScores({ limit: 30 }));
  const insights = useApi(() => apiClient.listInsights({ limit: 5 }));
  const anomalies = useApi(() => apiClient.listAnomalies({ limit: 100 }));
  const bottlenecks = useApi(() => apiClient.listBottlenecks({ limit: 100 }));

  const loading = scores.loading || insights.loading || anomalies.loading || bottlenecks.loading;
  const error = scores.error ?? insights.error ?? anomalies.error ?? bottlenecks.error;

  if (loading) return <Loading label="Loading dashboards…" />;
  if (error) return <ErrorState message={`API unreachable: ${error}`} />;

  const history = [...(scores.data ?? [])].reverse();
  const latest = (scores.data ?? [])[0];
  const activeBottlenecks = (bottlenecks.data ?? []).length;
  const activeAnomalies = (anomalies.data ?? []).length;
  const latestInsights = insights.data ?? [];

  return (
    <div>
      <h2>Overview</h2>
      <p className="muted">
        Team <strong>{teamId}</strong> · Range <strong>{timeRange}</strong>
      </p>
      {!latest ? (
        <Card title="No data yet">
          <EmptyState message="No health scores found. Run the simulator to generate engineering events." />
        </Card>
      ) : (
        <>
          <div className="grid">
            <Card title="Engineering Health Score">
              <div className="score-hero">{latest.score.toFixed(1)}</div>
              {latest.score_change != null && (
                <Badge tone={latest.score_change >= 0 ? 'ok' : 'bad'}>
                  {latest.score_change >= 0 ? '+' : ''}
                  {latest.score_change.toFixed(1)} vs previous
                </Badge>
              )}
              <Evidence data={latest.component_metrics} />
            </Card>
            <Card title="Dimensions">
              <DimensionBars dims={latest.component_metrics} />
            </Card>
          </div>
          <div className="grid">
            <Card title={`Bottlenecks (${activeBottlenecks})`}>
              <Link to="/bottlenecks">Open bottlenecks →</Link>
            </Card>
            <Card title={`Anomalies (${activeAnomalies})`}>
              <Link to="/anomalies">Open anomalies →</Link>
            </Card>
            <Card title="Trend">
              <ScoreTrend scores={history.map((s) => s.score)} />
              <Link to="/trends">Open trends →</Link>
            </Card>
          </div>
          <Card title="Latest insights">
            {latestInsights.length === 0 ? (
              <EmptyState message="No insights yet." />
            ) : (
              <ul className="list">
                {latestInsights.map((i) => (
                  <li key={i.id}>
                    <strong>{i.title}</strong>{' '}
                    {i.severity && <Badge tone={i.severity.toLowerCase()}>{i.severity}</Badge>}{' '}
                    {i.confidence != null && (
                      <span className="muted">conf {i.confidence.toFixed(2)}</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
            <Link to="/insights">All insights →</Link>
          </Card>
        </>
      )}
    </div>
  );
}
