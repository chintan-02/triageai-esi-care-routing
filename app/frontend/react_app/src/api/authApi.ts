import type { AuthUser, ClinicianRole, RegisterAccountInput } from '@/types/auth';
import { getInitials } from '@/lib/formatters';
import { API_BASE_URL, USE_MOCK_AUTH, USE_MOCK_API } from '@/lib/env';

const wait = (ms = 420) => new Promise((resolve) => window.setTimeout(resolve, ms));

// Local-only credential gate for standalone development. In live API mode this
// should be replaced by FastAPI JWT or secure httpOnly session auth.
const LOCAL_DEV_PASSWORD = 'triage2026';
const LOCAL_ACCOUNTS_KEY = 'triageai.auth.localAccounts';

interface LocalAccount extends AuthUser {
  email: string;
  password: string;
  createdAt: string;
}

function readLocalAccounts(): LocalAccount[] {
  try {
    const raw = window.localStorage.getItem(LOCAL_ACCOUNTS_KEY);
    return raw ? (JSON.parse(raw) as LocalAccount[]) : [];
  } catch {
    return [];
  }
}

function writeLocalAccounts(accounts: LocalAccount[]) {
  window.localStorage.setItem(LOCAL_ACCOUNTS_KEY, JSON.stringify(accounts));
}

async function authRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {})
    },
    credentials: 'include',
    ...options
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Auth request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function buildUser(name: string, role: ClinicianRole, email?: string, organization?: string, unit?: string): AuthUser {
  const safeName = name.trim() || 'Clinical User';
  return {
    name: safeName,
    role,
    initials: getInitials(safeName),
    email,
    organization,
    unit
  };
}

export const authApi = {
  async login(nameOrEmail: string, role: ClinicianRole, password: string): Promise<AuthUser> {
    if (USE_MOCK_API || USE_MOCK_AUTH) {
      await wait();
      const identifier = nameOrEmail.trim();
      if (!identifier) throw new Error('Enter your name or work email.');

      const matched = readLocalAccounts().find(
        (account) => account.email.toLowerCase() === identifier.toLowerCase() || account.name.toLowerCase() === identifier.toLowerCase()
      );

      if (matched) {
        if (matched.password !== password) throw new Error('Incorrect password for this local account.');
        return {
          name: matched.name,
          role: matched.role,
          initials: matched.initials,
          email: matched.email,
          organization: matched.organization,
          unit: matched.unit
        };
      }

      if (password !== LOCAL_DEV_PASSWORD) {
        throw new Error('Incorrect local development password.');
      }
      return buildUser(identifier, role);
    }

    return authRequest<AuthUser>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ identifier: nameOrEmail, role, password })
    });
  },

  async register(input: RegisterAccountInput): Promise<AuthUser> {
    if (USE_MOCK_API || USE_MOCK_AUTH) {
      await wait(520);
      const email = input.email.trim().toLowerCase();
      if (!input.name.trim()) throw new Error('Full name is required.');
      if (!email.includes('@')) throw new Error('Enter a valid work email.');
      if (!input.organization.trim()) throw new Error('Organization or hospital name is required.');
      if (input.password !== LOCAL_DEV_PASSWORD) throw new Error('Use the local access code for standalone testing.');

      const accounts = readLocalAccounts();
      if (accounts.some((account) => account.email.toLowerCase() === email)) {
        throw new Error('A local account already exists for this email. Use sign in instead.');
      }

      const user = buildUser(input.name, input.role, email, input.organization.trim(), input.unit.trim() || 'Emergency Department');
      const localAccount: LocalAccount = {
        ...user,
        email,
        password: input.password,
        createdAt: new Date().toISOString()
      };
      writeLocalAccounts([...accounts, localAccount]);
      return user;
    }

    return authRequest<AuthUser>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(input)
    });
  },

  async me(): Promise<AuthUser | null> {
    if (USE_MOCK_API || USE_MOCK_AUTH) return null;
    return authRequest<AuthUser>('/api/v1/users/me');
  },

  async logout(): Promise<void> {
    if (USE_MOCK_API || USE_MOCK_AUTH) return;
    await authRequest('/api/v1/auth/logout', { method: 'POST' });
  }
};

export { LOCAL_DEV_PASSWORD };
