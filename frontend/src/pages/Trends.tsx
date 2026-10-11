import { useState } from 'react';
import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import type { HealthScore } from '../types';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';
import Loading from '../components/ui/Loading';
import Table from '../components/ui/Table';
import ScoreTrend from '../components/ScoreTrend';

function formatPeriod(score: HealthScore): string {
  const fmt = (raw: string | null | undefined) => {
    if (!raw) return null;
    const time = new Date(raw).getTime();
    return Number.isNaN(time) ? null : new Date(time).toLocaleDateString();
  };
  const start = fmt(score.period_start);
  const end = fmt(score.period_end);
  if (start && end) return `${start} – ${end}`;
  return fmt(score.calculated_at) ?? fmt(score.computed_at) ?? '—';
}

function formatChange(score: HealthScore): string {
  const delta =
    score.score_change ?? (score.previous_score != null ? score.score - score.previous_score : null);
  if (delta === null || delta === undefined) return '—';
  const rounded = Math.round(delta * 10) / 10;
  return `${rounded > 0 ? '+' : ''}${rounded}`;
}

/** Trends: full score-trend chart plus the underlying score table. */
export default function Trends() {
  const { teamId } = useApp();
  const [attempt, setAttempt] = useState(0);
  const scores = useApi(() => apiClient.listHealthScores(), [attempt]);

  if (scores.loading) {
    return (
      <div>
        <h1>Trends</h1>
        <Loading />
      </div>
    );
  }

  if (scores.error) {
    return (
      <div>
        <h1>Trends</h1>
        <ErrorState message={scores.error.message} onRetry={() => setAttempt((n) => n + 1)} />
      </div>
    );
  }

  const history = scores.data ?? [];
  if (history.length === 0) {
    return (
      <div>
        <h1>Trends</h1>
        <EmptyState title="No health scores yet" />
      </div>
    );
  }

  return (
    <div>
      <h1>Trends</h1>
      <p className="page-sub">Team {teamId}</p>
      <Card title="Score trend">
        <ScoreTrend scores={history} />
      </Card>
      <Card title="Scores">
        <Table<HealthScore>
          caption="Health scores by period"
          columns={[
            { key: 'period', header: 'Period', render: (row) => formatPeriod(row) },
            { key: 'score', header: 'Score', render: (row) => row.score.toFixed(1) },
            { key: 'change', header: 'Change', render: (row) => formatChange(row) },
          ]}
          rows={history}
          getRowKey={(row) => row.id}
        />
      </Card>
    </div>
  );
}
