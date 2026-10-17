import type { AuthUser, ClinicianRole, RegisterAccountInput } from '@/types/auth';
import { API_BASE_URL } from '@/lib/env';
import { clearSession, sessionHeaders, storeSession } from './session';

interface SessionResponse { access_token: string; expires_at: string; user: AuthUser }

async function authRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...sessionHeaders(), ...options.headers },
  });
  if (!response.ok) {
    if (response.status === 401) clearSession();
    const error = await response.json().catch(() => ({}));
    const detail = typeof error.detail === 'string' ? error.detail
      : Array.isArray(error.detail) ? error.detail.map((item: { loc?: string[]; msg?: string }) =>
          `${item.loc?.filter((part) => part !== 'body').join('.') || 'Field'}: ${item.msg || 'Invalid value'}`).join('; ')
      : 'Unable to authenticate. Check your details and try again.';
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function beginSession(path: string, body?: unknown): Promise<AuthUser> {
  const session = await authRequest<SessionResponse>(path, {
    method: 'POST', body: body === undefined ? undefined : JSON.stringify(body),
  });
  storeSession(session.access_token, session.expires_at);
  return session.user;
}

export const authApi = {
  login(identifier: string, _role: ClinicianRole, password: string): Promise<AuthUser> {
    return beginSession('/login', { identifier, password });
  },
  register(input: RegisterAccountInput): Promise<AuthUser> {
    return beginSession('/register', { name: input.name, email: input.email, password: input.password });
  },
  demo(): Promise<AuthUser> { return beginSession('/demo'); },
  async me(): Promise<AuthUser | null> {
    if (!sessionHeaders().Authorization) return null;
    return authRequest<AuthUser>('/me');
  },
  async logout(): Promise<void> {
    try { await authRequest('/logout', { method: 'POST' }); }
    finally { clearSession(); }
  },
};
