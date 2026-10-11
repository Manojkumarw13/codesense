import { Line, LineChart, ResponsiveContainer } from 'recharts';
import type { HealthScore } from '../types';

function pointTime(score: HealthScore): number {
  for (const raw of [score.period_end, score.calculated_at, score.computed_at, score.period_start]) {
    if (!raw) continue;
    const time = new Date(raw).getTime();
    if (!Number.isNaN(time)) return time;
  }
  return 0;
}

interface ScoreTrendProps {
  scores: HealthScore[];
  height?: number;
  label?: string;
}

/** Full score-history line chart. Wrapper carries `role="img"` + aria-label. */
export default function ScoreTrend({
  scores,
  height = 280,
  label = 'Health score trend over time',
}: ScoreTrendProps) {
  const points = [...scores]
    .sort((a, b) => pointTime(a) - pointTime(b))
    .map((score) => ({ score: Number(score.score) || 0 }));
  return (
    <div role="img" aria-label={label} className="score-trend" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
          <Line type="monotone" dataKey="score" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
