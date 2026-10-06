import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div>
      <h2>Not found</h2>
      <p className="muted">
        <Link to="/">Back to Overview</Link>
      </p>
    </div>
  );
}
