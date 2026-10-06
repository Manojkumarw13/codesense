export default function Loading({ label = 'Loading…' }: { label?: string }) {
  return <div className="state">{label}</div>;
}
