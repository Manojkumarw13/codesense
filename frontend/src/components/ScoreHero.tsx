import type { HealthScore } from '../types';
import ScoreTrend from './ScoreTrend';

function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return null;
  return new Date(time).toLocaleDateString();
}

function periodText(score: HealthScore): string {
  const start = formatDate(score.period_start);
  const end = formatDate(score.period_end);
  if (start && end) return `${start} – ${end}`;
  const at = formatDate(score.calculated_at) ?? formatDate(score.computed_at);
  return at ? `Calculated ${at}` : 'Latest score';
}

function formatDelta(delta: number | null): string {
  if (delta === null) return 'No change data yet';
  const rounded = Math.round(delta * 10) / 10;
  const sign = rounded > 0 ? '+' : '';
  return `${sign}${rounded} points vs previous period`;
}

interface ScoreHeroProps {
  score: HealthScore;
  history?: HealthScore[];
}

/** Score card: headline score + period + delta + sparkline. */
export default function ScoreHero({ score, history = [] }: ScoreHeroProps) {
  const delta =
    score.score_change ?? (score.previous_score != null ? score.score - score.previous_score : null);
  const sparkline = history.length > 1 ? history : [score];
  return (
    <div className="score-hero">
      <p className="score-value tnum" aria-label={`Health score ${score.score.toFixed(1)}`}>
        {score.score.toFixed(1)}
      </p>
      <p className="score-period">{periodText(score)}</p>
      <p className="score-delta tnum">{formatDelta(delta)}</p>
      {sparkline.length > 1 && <ScoreTrend scores={sparkline} height={96} label="Recent health score trend" />}
    </div>
  );
}
