import type { AssessmentRecord, ClinicianReview, DashboardSummary, IntakePayload, ModelStatusResponse } from '@/types/clinical';
import { API_BASE_URL, USE_MOCK_API, getRuntimeWarnings } from '@/lib/env';
import { mockApi } from './mockApi';

function legacyClientDisabled(): never {
  throw new Error(
    'Legacy mock apiClient is disabled in backend-connected mode. Use the current backend API modules in src/api/*.ts.',
  );
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
    return Promise.reject(legacyClientDisabled());
  },

  getModelStatus(): Promise<ModelStatusResponse> {
    if (USE_MOCK_API) return mockApi.getModelStatus();
    return Promise.reject(legacyClientDisabled());
  },

  listAssessments(): Promise<AssessmentRecord[]> {
    if (USE_MOCK_API) return mockApi.listAssessments();
    return Promise.reject(legacyClientDisabled());
  },

  getAssessment(id: string): Promise<AssessmentRecord | undefined> {
    if (USE_MOCK_API) return mockApi.getAssessment(id);
    void id;
    return Promise.reject(legacyClientDisabled());
  },

  createAssessment(payload: IntakePayload): Promise<AssessmentRecord> {
    if (USE_MOCK_API) return mockApi.createAssessment(payload);
    void payload;
    return Promise.reject(legacyClientDisabled());
  },

  saveReview(id: string, review: ClinicianReview): Promise<AssessmentRecord | undefined> {
    if (USE_MOCK_API) return mockApi.saveReview(id, review);
    void id;
    void review;
    return Promise.reject(legacyClientDisabled());
  }
};
