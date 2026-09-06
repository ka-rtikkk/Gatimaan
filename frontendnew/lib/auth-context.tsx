/**
 * Auth Context - manages login state across the app
 */
'use client';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { auth, User, setToken, clearToken, getToken } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null, loading: true,
  login: async () => {}, logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('gatimaan_user');
    if (stored && getToken()) {
      try { setUser(JSON.parse(stored)); } catch {}
    } else if (!getToken()) {
      clearToken();
    }
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    const res = await auth.login(username, password);
    setToken(res.access_token);
    localStorage.setItem('gatimaan_user', JSON.stringify(res.user));
    setUser(res.user);
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
