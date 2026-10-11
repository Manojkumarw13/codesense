interface SkeletonProps {
  lines?: number;
}

export default function Skeleton({ lines = 3 }: SkeletonProps) {
  return (
    <div aria-hidden="true" className="skeleton-stack">
      {Array.from({ length: lines }, (_, index) => (
        <div key={index} className="skeleton" />
      ))}
    </div>
  );
}
