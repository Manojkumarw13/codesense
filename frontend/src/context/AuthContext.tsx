import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { AuthUser } from '../types';
import { apiClient } from '../api/client';

/** localStorage key holding the access token after login. */
const TOKEN_KEY = 'codesense_token';

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  loading: boolean;
}

export const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  login: async () => {},
  logout: () => {},
  refresh: async () => {},
  loading: false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Hydrate the stored token on mount so a page refresh stays authenticated.
  useEffect(() => {
    setToken(localStorage.getItem(TOKEN_KEY));
    setLoading(false);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        const { access_token, user: loggedInUser } = await apiClient.login(email, password);
        localStorage.setItem(TOKEN_KEY, access_token);
        setToken(access_token);
        setUser(loggedInUser);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const refresh = useCallback(
    async () => {
      if (!token) return;
      setLoading(true);
      try {
        const { access_token } = await apiClient.refresh(token);
        localStorage.setItem(TOKEN_KEY, access_token);
        setToken(access_token);
        setUser(await apiClient.me());
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    },
    [token, logout],
  );

  const value = useMemo(
    () => ({ user, token, login, logout, refresh, loading }),
    [user, token, login, logout, refresh, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
