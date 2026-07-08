const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API !== 'false';
export const USE_MOCK_AUTH = import.meta.env.VITE_USE_MOCK_AUTH !== 'false';
export const API_BASE_URL = rawApiBaseUrl?.trim() || 'http://localhost:8000';

export interface RuntimeWarning {
  id: string;
  title: string;
  detail: string;
  severity: 'info' | 'warning' | 'critical';
}

export function getRuntimeWarnings(): RuntimeWarning[] {
  const warnings: RuntimeWarning[] = [];

  if (!USE_MOCK_API && !rawApiBaseUrl?.trim()) {
    warnings.push({
      id: 'missing-api-base-url',
      title: 'Live API mode needs VITE_API_BASE_URL',
      detail: 'Set VITE_API_BASE_URL to your FastAPI backend origin before disabling mock API mode.',
      severity: 'critical'
    });
  }

  if (!USE_MOCK_API && USE_MOCK_AUTH) {
    warnings.push({
      id: 'mock-auth-with-live-api',
      title: 'Live API is using local mock authentication',
      detail: 'For a real deployment, set VITE_USE_MOCK_AUTH=false and connect FastAPI JWT or secure session auth.',
      severity: 'warning'
    });
  }

  if (USE_MOCK_API) {
    warnings.push({
      id: 'mock-api-mode',
      title: 'Standalone mock API mode',
      detail: 'The frontend is running with local synthetic records. No patient data should be entered in this mode.',
      severity: 'info'
    });
  }

  return warnings;
}
