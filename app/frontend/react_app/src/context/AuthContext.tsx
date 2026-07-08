// This file exports both the provider component and its `useX` hook, which is
// the standard React context pattern. react-refresh's export-purity rule flags
// that combination; disabled here rather than splitting one small file in two.
/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { AuthUser, ClinicianRole, RegisterAccountInput } from '@/types/auth';
import { authApi } from '@/api/authApi';
import { USE_MOCK_AUTH, USE_MOCK_API } from '@/lib/env';

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (nameOrEmail: string, role: ClinicianRole, password: string) => Promise<void>;
  register: (input: RegisterAccountInput) => Promise<void>;
  logout: () => Promise<void>;
}

const STORAGE_KEY = 'triageai.auth.user';
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function loadSession() {
      try {
        if (USE_MOCK_API || USE_MOCK_AUTH) {
          const raw = window.localStorage.getItem(STORAGE_KEY);
          if (raw && mounted) setUser(JSON.parse(raw) as AuthUser);
          return;
        }
        const currentUser = await authApi.me();
        if (mounted) setUser(currentUser);
      } catch {
        if (mounted) setUser(null);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    void loadSession();
    return () => {
      mounted = false;
    };
  }, []);

  const login = async (nameOrEmail: string, role: ClinicianRole, password: string) => {
    const authedUser = await authApi.login(nameOrEmail, role, password);
    setUser(authedUser);
    if (USE_MOCK_API || USE_MOCK_AUTH) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(authedUser));
    }
  };

  const register = async (input: RegisterAccountInput) => {
    const authedUser = await authApi.register(input);
    setUser(authedUser);
    if (USE_MOCK_API || USE_MOCK_AUTH) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(authedUser));
    }
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
    window.localStorage.removeItem(STORAGE_KEY);
  };

  const value = useMemo(() => ({ user, isLoading, login, register, logout }), [user, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
