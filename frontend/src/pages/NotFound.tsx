import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div>
      <h1>Not found</h1>
      <p className="muted">
        <Link to="/">Back to Overview</Link>
      </p>
    </div>
  );
}
