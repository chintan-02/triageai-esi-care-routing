const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === 'true';
export const USE_MOCK_AUTH = import.meta.env.VITE_USE_MOCK_AUTH !== 'false';
export const API_BASE_URL = rawApiBaseUrl?.trim() || 'http://localhost:8001';

export interface RuntimeWarning {
  id: string;
  title: string;
  detail: string;
  severity: 'info' | 'warning' | 'critical';
}

export function getRuntimeWarnings(): RuntimeWarning[] {
  const warnings: RuntimeWarning[] = [];

  if (!USE_MOCK_API && USE_MOCK_AUTH) {
    warnings.push({
      id: 'mock-auth-with-live-api',
      title: 'Live API is using local mock authentication',
      detail: 'Backend data remains the source of truth. For deployment, set VITE_USE_MOCK_AUTH=false and connect FastAPI JWT or secure session auth.',
      severity: 'warning'
    });
  }

  if (USE_MOCK_API) {
    warnings.push({
      id: 'mock-api-mode',
      title: 'Development mock API mode',
      detail: 'The frontend is running with local synthetic records. No patient data should be entered in this mode.',
      severity: 'info'
    });
  }

  return warnings;
}
