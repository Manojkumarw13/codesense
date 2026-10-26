interface EvidenceProps {
  evidence: unknown;
  title?: string;
}

/** `<details>` JSON drill-down for a row's evidence payload. */
export default function Evidence({ evidence, title = 'Evidence' }: EvidenceProps) {
  if (evidence === null || evidence === undefined) return null;
  return (
    <details className="evidence">
      <summary>{title}</summary>
      <pre className="tnum">{JSON.stringify(evidence, null, 2)}</pre>
    </details>
  );
}
