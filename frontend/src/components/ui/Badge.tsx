export default function Badge({ tone = 'info', children }: { tone?: string; children: string }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
