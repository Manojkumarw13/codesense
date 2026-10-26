import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface RequireAuthProps {
  children: React.ReactNode;
}

/**
 * Renders `children` when authenticated; otherwise redirects to `/login`.
 * Renders nothing while the auth state is still hydrating from localStorage.
 */
export default function RequireAuth({ children }: RequireAuthProps) {
  const { token, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (loading) return;
    if (!token) navigate('/login', { replace: true });
  }, [token, loading, navigate]);

  if (loading || !token) return null;
  return <>{children}</>;
}
