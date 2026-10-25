import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import './Login.css';

interface LoginProps {
  /** Called after a successful login; the route supplies navigation to /app. */
  onLogin?: () => void;
}

/** Email/password login form. Stores the token via AuthContext on success. */
export default function Login({ onLogin }: LoginProps = {}) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      onLogin?.();
    } catch {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login">
      <form className="login-form" onSubmit={handleSubmit}>
        <h1 className="login-title">Sign in</h1>
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        {error && <p className="login-error" role="alert">{error}</p>}
        <Button type="submit" variant="primary" disabled={loading} className="login-submit">
          Sign in
        </Button>
      </form>
    </div>
  );
}
