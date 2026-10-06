/** Jhey-selective delight: static geometric SVG art for empty/placeholder states.
    No loops, no vestibular triggers — pure shape craft in brand tokens. */
export default function EmptyArt() {
  return (
    <svg className="empty-art" width="180" height="96" viewBox="0 0 180 96" role="img" aria-hidden="true">
      <rect x="8" y="8" width="164" height="80" rx="12" fill="#eef1f6" />
      <polyline
        points="20,64 44,64 54,40 66,72 78,52 92,52 100,30 110,60 124,60 132,44 160,44"
        fill="none"
        stroke="#2563eb"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.85"
      />
      <circle cx="100" cy="30" r="5" fill="#2563eb" />
      <circle cx="54" cy="40" r="3.5" fill="#8b5cf6" />
      <circle cx="132" cy="44" r="3.5" fill="#0ea5e9" />
    </svg>
  );
}
