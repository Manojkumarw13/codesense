export default function OfflineNotice({
  mode,
  aiAvailable,
}: {
  mode: 'normal' | 'offline';
  aiAvailable: boolean;
}) {
  // Fully available — nothing to surface.
  if (mode === 'normal' && aiAvailable === true) {
    return null;
  }

  const isOffline = mode === 'offline';
  const headline = isOffline
    ? 'Working offline'
    : 'AI unavailable';
  const body = isOffline
    ? "Core analytics keep working. Cloud AI is unavailable until you're back online."
    : 'Core analytics keep working. Cloud AI isn\'t configured for this team.';

  return (
    <div role="status" className="offline-notice">
      <span className="offline-notice__icon" aria-hidden="true">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx={12} cy={12} r={10} />
          <path d="M12 16v-4" />
          <path d="M12 8h.01" />
        </svg>
      </span>
      <div className="offline-notice__text">
        <div className="offline-notice__headline">{headline}</div>
        <p className="offline-notice__body">{body}</p>
      </div>
    </div>
  );
}
