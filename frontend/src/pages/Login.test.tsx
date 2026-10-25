import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { cleanup, render, screen, fireEvent } from '@testing-library/react';
import Login from './Login';

afterEach(() => cleanup());

vi.mock('../hooks/useAuth', () => {
  const login = vi.fn().mockResolvedValue(undefined);
  return {
    useAuth: vi.fn(() => ({
      login,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: null,
      token: null,
      loading: false,
    })),
  };
});

import { useAuth } from '../hooks/useAuth';

const mockLogin = useAuth().login as unknown as ReturnType<typeof vi.fn>;

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockResolvedValue(undefined);
  });

  it('renders email/password form and submit button', () => {
    render(<Login />);
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeTruthy();
  });

  it('calls login with credentials and invokes onLogin on success', async () => {
    const onLogin = vi.fn();
    render(<Login onLogin={onLogin} />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.c' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'secret' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    await vi.waitFor(() => expect(mockLogin).toHaveBeenCalledWith('a@b.c', 'secret'));
    await vi.waitFor(() => expect(onLogin).toHaveBeenCalledTimes(1));
  });

  it('shows a generic error and does not call onLogin when login rejects', async () => {
    mockLogin.mockRejectedValue(new Error('bad credentials'));
    const onLogin = vi.fn();
    render(<Login onLogin={onLogin} />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.c' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'secret' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    await vi.waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Invalid credentials'));
    expect(onLogin).not.toHaveBeenCalled();
  });
});
