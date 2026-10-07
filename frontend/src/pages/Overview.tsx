import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';
import Evidence from '../components/Evidence';
import EmptyArt from '../components/EmptyArt';
import { DashboardSkeleton } from '../components/ui/Skeleton';
import { DimensionBarsChart, MiniSpark, ScoreArea } from '../components/charts/ScoreCharts';

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function Overview() {
  const { teamId, timeRange } = useApp();
  const scores = useApi(() => apiClient.listHealthScores({ limit: 30 }));
  const insights = useApi(() => apiClient.listInsights({ limit: 5 }));
  const anomalies = useApi(() => apiClient.listAnomalies({ limit: 100 }));
  const bottlenecks = useApi(() => apiClient.listBottlenecks({ limit: 100 }));

  const loading = scores.loading || insights.loading || anomalies.loading || bottlenecks.loading;
  const error = scores.error ?? insights.error ?? anomalies.error ?? bottlenecks.error;

  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorState message={`API unreachable: ${error}`} />;

  const history = [...(scores.data ?? [])].reverse();
  const latest = (scores.data ?? [])[0];
  const activeBottlenecks = bottlenecks.data ?? [];
  const activeAnomalies = anomalies.data ?? [];
  const latestInsights = insights.data ?? [];

  return (
    <div>
      <h1>Overview</h1>
      <p className="muted">
        Team <strong>{teamId}</strong> · Range <strong>{timeRange}</strong>
      </p>
      {!latest ? (
        <Card title="No data yet">
          <EmptyArt />
          <EmptyState message="No health scores found. Run the simulator to generate engineering events." />
        </Card>
      ) : (
        <>
          <div className="grid">
            <Card title="Engineering Health Score">
              <div className="score-hero">{latest.score.toFixed(1)}</div>
              <p className="muted">
                Period ending {shortDate(latest.period_end)} · {history.length} scored periods
              </p>
              {latest.score_change != null && (
                <p>
                  <Badge tone={latest.score_change >= 0 ? 'ok' : 'bad'}>
                    {latest.score_change >= 0 ? '+' : ''}
                    {latest.score_change.toFixed(1)} vs previous
                  </Badge>{' '}
                  <span className={`delta ${latest.score_change >= 0 ? 'delta-up' : 'delta-down'}`}>
                    {latest.score_change >= 0 ? '▲' : '▼'} trending
                  </span>
                </p>
              )}
              <MiniSpark data={history.map((s) => s.score)} />
              <Evidence data={latest.component_metrics} />
            </Card>
            <Card title="Dimensions">
              <DimensionBarsChart dims={latest.component_metrics} />
            </Card>
          </div>
          <Card title="Score trajectory">
            <ScoreArea
              data={history.map((s) => ({ label: shortDate(s.period_end), score: s.score }))}
              height={200}
            />
          </Card>
          <div className="grid">
            <Card title={`Bottlenecks (${activeBottlenecks.length})`}>
              {activeBottlenecks.length === 0 ? (
                <EmptyState message="Flow looks uncongested." />
              ) : (
                <ul className="list">
                  {activeBottlenecks.slice(0, 3).map((b) => (
                    <li key={b.id}>
                      <strong>{b.title}</strong>{' '}
                      <Badge tone={b.severity.toLowerCase()}>{b.severity}</Badge>
                    </li>
                  ))}
                </ul>
              )}
              <Link to="/bottlenecks">Open bottlenecks →</Link>
            </Card>
            <Card title={`Anomalies (${activeAnomalies.length})`}>
              {activeAnomalies.length === 0 ? (
                <EmptyState message="No unusual movement flagged." />
              ) : (
                <ul className="list">
                  {activeAnomalies.slice(0, 3).map((a) => (
                    <li key={a.id}>
                      observed <strong>{a.observed_value}</strong> vs baseline{' '}
                      {a.baseline_value ?? '—'}{' '}
                      <Badge tone={a.severity.toLowerCase()}>{a.severity}</Badge>
                    </li>
                  ))}
                </ul>
              )}
              <Link to="/anomalies">Open anomalies →</Link>
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
