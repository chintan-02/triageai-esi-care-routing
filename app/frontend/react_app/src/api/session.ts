// Tab-scoped bearer credentials avoid third-party cookie requirements between
// Netlify and the API. Never put these values in logs or persistent localStorage.
const SESSION_KEY = 'triageai.backend.session';
interface StoredSession { token: string; expiresAt: string }

export function storeSession(token: string, expiresAt: string) {
  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify({ token, expiresAt }));
}

export function clearSession() {
  window.sessionStorage.removeItem(SESSION_KEY);
}

export function sessionHeaders(): Record<string, string> {
  try {
    const raw = window.sessionStorage.getItem(SESSION_KEY);
    if (!raw) return {};
    const session = JSON.parse(raw) as StoredSession;
    if (!session.token || !Number.isFinite(Date.parse(session.expiresAt)) || Date.parse(session.expiresAt) <= Date.now()) {
      clearSession();
      return {};
    }
    return { Authorization: `Bearer ${session.token}` };
  } catch {
    clearSession();
    return {};
  }
}
