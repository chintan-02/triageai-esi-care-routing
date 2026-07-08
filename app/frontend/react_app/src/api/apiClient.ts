import type { AssessmentRecord, ClinicianReview, DashboardSummary, IntakePayload, ModelStatusResponse } from '@/types/clinical';
import { API_BASE_URL, USE_MOCK_API, getRuntimeWarnings } from '@/lib/env';
import { mockApi } from './mockApi';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
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
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get mode() {
    return USE_MOCK_API ? 'mock' : 'api';
  },

  get baseUrl() {
    return API_BASE_URL;
  },

  get runtimeWarnings() {
    return getRuntimeWarnings();
  },

  getDashboardSummary(): Promise<DashboardSummary> {
    if (USE_MOCK_API) return mockApi.getDashboardSummary();
    return request<DashboardSummary>('/api/v1/dashboard/summary');
  },

  getModelStatus(): Promise<ModelStatusResponse> {
    if (USE_MOCK_API) return mockApi.getModelStatus();
    return request<ModelStatusResponse>('/api/v1/model/status');
  },

  listAssessments(): Promise<AssessmentRecord[]> {
    if (USE_MOCK_API) return mockApi.listAssessments();
    return request<AssessmentRecord[]>('/api/v1/assessments');
  },

  getAssessment(id: string): Promise<AssessmentRecord | undefined> {
    if (USE_MOCK_API) return mockApi.getAssessment(id);
    return request<AssessmentRecord>(`/api/v1/assessments/${id}`);
  },

  createAssessment(payload: IntakePayload): Promise<AssessmentRecord> {
    if (USE_MOCK_API) return mockApi.createAssessment(payload);
    return request<AssessmentRecord>('/api/v1/assessments', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  saveReview(id: string, review: ClinicianReview): Promise<AssessmentRecord | undefined> {
    if (USE_MOCK_API) return mockApi.saveReview(id, review);
    return request<AssessmentRecord>(`/api/v1/assessments/${id}/review`, {
      method: 'POST',
      body: JSON.stringify(review)
    });
  }
};
