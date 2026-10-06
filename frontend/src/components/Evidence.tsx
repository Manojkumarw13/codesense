/** Explainability drill-down: Score → Dimension → Metric → Evidence. */
export default function Evidence({ data }: { data: unknown }) {
  if (data == null) return null;
  const empty =
    typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length === 0;
  if (empty) return <p className="muted">No evidence recorded.</p>;
  return (
    <details className="evidence">
      <summary>Evidence</summary>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </details>
  );
}
