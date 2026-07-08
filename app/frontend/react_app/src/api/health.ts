import { apiRequest } from './client';
import type { HealthResponse, ReadyResponse } from '@/types/api';

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/health');
}

export function getReady(): Promise<ReadyResponse> {
  return apiRequest<ReadyResponse>('/ready');
}
