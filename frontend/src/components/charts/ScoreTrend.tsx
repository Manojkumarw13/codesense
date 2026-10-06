/** SVG sparkline of health-score history (no chart deps — lean + offline-safe). */
export default function ScoreTrend({
  scores,
  width = 560,
  height = 140,
}: {
  scores: number[];
  width?: number;
  height?: number;
}) {
  if (scores.length === 0) return <p className="muted">No score history yet.</p>;
  const min = Math.min(...scores, 0);
  const max = Math.max(...scores, 100);
  const span = max - min || 1;
  const pts = scores.map((s, i) => {
    const x = scores.length === 1 ? width / 2 : (i / (scores.length - 1)) * (width - 8) + 4;
    const y = height - 8 - ((s - min) / span) * (height - 24);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return (
    <svg
      className="chart"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Health score trend"
    >
      <polyline points={pts.join(' ')} fill="none" strokeWidth={2} className="trend-line" />
      {pts.map((p, i) => {
        const [cx, cy] = p.split(',');
        return <circle key={i} cx={cx} cy={cy} r={3} className="trend-dot" />;
      })}
    </svg>
  );
}
