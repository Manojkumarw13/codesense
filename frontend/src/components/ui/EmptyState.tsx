export default function EmptyState({ message = 'No data yet.' }: { message?: string }) {
  return <div className="state">{message}</div>;
}
