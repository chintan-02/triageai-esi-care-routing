import { apiRequest } from './client';
import type { DashboardSummaryResponse } from '@/types/api';

export function getDashboardSummary(): Promise<DashboardSummaryResponse> {
  return apiRequest<DashboardSummaryResponse>('/dashboard/summary');
}
