import { beforeEach, describe, expect, it, vi } from 'vitest';
import { authApi } from './authApi';
import { apiBlobRequest, apiRequest } from './client';
import { sessionHeaders, storeSession } from './session';

const user = { id: 'visitor', name: 'Demo visitor', role: 'Doctor', initials: 'DV' };

function jsonResponse(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } });
}

describe('real backend sessions', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('starts a demo through the backend and sends the returned credential on API calls', async () => {
    const fetch = vi.spyOn(window, 'fetch');
    fetch.mockResolvedValueOnce(jsonResponse({ access_token: 'opaque-token', expires_at: new Date(Date.now() + 60000).toISOString(), user }));
    expect(await authApi.demo()).toEqual(user);
    expect(fetch.mock.calls[0][0]).toContain('/api/v1/auth/demo');
    fetch.mockResolvedValueOnce(jsonResponse([]));
    await apiRequest('/assessments');
    const options = fetch.mock.calls[1][1];
    expect(new Headers(options?.headers).get('Authorization')).toBe('Bearer opaque-token');
  });

  it('authenticates PDF downloads and expires the UI session on a 401', async () => {
    storeSession('opaque-token', new Date(Date.now() + 60000).toISOString());
    const fetch = vi.spyOn(window, 'fetch').mockResolvedValueOnce(new Response('%PDF example'));
    await apiBlobRequest('/reports/example/download');
    expect(new Headers(fetch.mock.calls[0][1]?.headers).get('Authorization')).toBe('Bearer opaque-token');
    const expired = vi.fn();
    window.addEventListener('triageai:session-expired', expired);
    fetch.mockResolvedValueOnce(jsonResponse({ detail: 'Session missing or expired' }, 401));
    await expect(apiRequest('/assessments')).rejects.toThrow('Session missing or expired');
    expect(expired).toHaveBeenCalledOnce();
    expect(sessionHeaders()).toEqual({});
    window.removeEventListener('triageai:session-expired', expired);
  });

  it('discards expired credentials and does not trust a local profile', async () => {
    storeSession('expired', new Date(Date.now() - 1000).toISOString());
    const fetch = vi.spyOn(window, 'fetch');
    expect(await authApi.me()).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
    expect(sessionHeaders()).toEqual({});
  });

  it('revokes logout server-side and clears local credentials even on failure', async () => {
    storeSession('opaque-token', new Date(Date.now() + 60000).toISOString());
    const fetch = vi.spyOn(window, 'fetch').mockRejectedValueOnce(new Error('Network unavailable'));
    await expect(authApi.logout()).rejects.toThrow('Network unavailable');
    expect(fetch.mock.calls[0][0]).toContain('/api/v1/auth/logout');
    expect(sessionHeaders()).toEqual({});
  });
});
