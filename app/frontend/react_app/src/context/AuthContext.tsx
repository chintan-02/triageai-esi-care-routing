// This file exports both the provider component and its `useX` hook, which is
// the standard React context pattern. react-refresh's export-purity rule flags
// that combination; disabled here rather than splitting one small file in two.
/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { AuthUser, ClinicianRole, RegisterAccountInput } from '@/types/auth';
import { authApi } from '@/api/authApi';

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (nameOrEmail: string, role: ClinicianRole, password: string) => Promise<void>;
  register: (input: RegisterAccountInput) => Promise<void>;
  logout: () => Promise<void>;
  startDemo: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    // Retire plaintext mock accounts and unverified local profiles from older builds.
    window.localStorage.removeItem('triageai.auth.localAccounts');
    window.localStorage.removeItem('triageai.auth.user');

    async function loadSession() {
      try {
        const currentUser = await authApi.me();
        if (mounted) setUser(currentUser);
      } catch {
        if (mounted) setUser(null);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    const expireSession = () => setUser(null);
    window.addEventListener("triageai:session-expired", expireSession);
    void loadSession();
    return () => {
      mounted = false;
      window.removeEventListener("triageai:session-expired", expireSession);
    };
  }, []);

  const login = async (nameOrEmail: string, role: ClinicianRole, password: string) => {
    const authedUser = await authApi.login(nameOrEmail, role, password);
    setUser(authedUser);
  };

  const register = async (input: RegisterAccountInput) => {
    const authedUser = await authApi.register(input);
    setUser(authedUser);
  };

  const logout = async () => {
    try { await authApi.logout(); } finally { setUser(null); }
  };

  const startDemo = async () => { setUser(await authApi.demo()); };

  const value = useMemo(() => ({ user, isLoading, login, register, logout, startDemo }), [user, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
