import { Link } from 'react-router-dom';
import { useState } from 'react';
import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';
import Loading from '../components/ui/Loading';
import ScoreHero from '../components/ScoreHero';

/** Team overview: current score card + signal counts as links. */
export default function Overview() {
  const { teamId } = useApp();
  const [attempt, setAttempt] = useState(0);
  const retry = () => setAttempt((n) => n + 1);
  const scores = useApi(() => apiClient.listHealthScores(), [attempt]);
  const insights = useApi(() => apiClient.listInsights(), [attempt]);
  const anomalies = useApi(() => apiClient.listAnomalies(), [attempt]);
  const bottlenecks = useApi(() => apiClient.listBottlenecks(), [attempt]);

  if (scores.loading || insights.loading || anomalies.loading || bottlenecks.loading) {
    return (
      <div>
        <h1>Overview</h1>
        <Loading />
      </div>
    );
  }

  if (scores.error) {
    return (
      <div>
        <h1>Overview</h1>
        <ErrorState message={scores.error.message} onRetry={retry} />
      </div>
    );
  }

  const history = scores.data ?? [];
  if (history.length === 0) {
    return (
      <div>
        <h1>Overview</h1>
        <EmptyState title="No health scores yet" />
      </div>
    );
  }

  const latest = history[0];
  return (
    <div>
      <h1>Overview</h1>
      <p className="page-sub">Team {teamId}</p>
      <Card title="Current health score">
        <ScoreHero score={latest} history={history.slice(0, 12)} />
      </Card>
      <section aria-labelledby="overview-signals">
        <h2 id="overview-signals">Signals</h2>
        <ul className="signal-counts">
          <li>
            <Link to="/app/insights">{(insights.data ?? []).length} insights</Link>
          </li>
          <li>
            <Link to="/app/anomalies">{(anomalies.data ?? []).length} anomalies</Link>
          </li>
          <li>
            <Link to="/app/bottlenecks">{(bottlenecks.data ?? []).length} bottlenecks</Link>
          </li>
        </ul>
      </section>
    </div>
  );
}
