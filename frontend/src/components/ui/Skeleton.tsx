/** Static-shape loading placeholders. Shimmer is finite-load feedback only;
    fully static under prefers-reduced-motion (see styles.css). */
export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="card skeleton-card" aria-hidden="true">
      <div className="skeleton skeleton-title" />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="skeleton skeleton-line" style={{ width: `${92 - i * 13}%` }} />
      ))}
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div role="status" aria-label="Loading dashboards">
      <span className="sr-only">Loading dashboards…</span>
      <div className="grid">
        <SkeletonCard />
        <SkeletonCard lines={4} />
        <SkeletonCard lines={2} />
      </div>
    </div>
  );
}
