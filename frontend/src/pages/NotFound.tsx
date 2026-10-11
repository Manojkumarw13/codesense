import { Link } from 'react-router-dom';

/** NotFound: unknown routes guide back home. */
export default function NotFound() {
  return (
    <main>
      <h1>Page not found</h1>
      <p className="state-hint">The page you are looking for does not exist.</p>
      <Link to="/">Back home</Link>
    </main>
  );
}
