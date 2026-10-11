interface EmptyStateProps {
  title: string;
  hint?: string;
}

export default function EmptyState({
  title,
  hint = 'Run the simulator to generate data.',
}: EmptyStateProps) {
  return (
    <div className="state-block">
      <p className="state-title">{title}</p>
      <p className="state-hint">{hint}</p>
    </div>
  );
}
