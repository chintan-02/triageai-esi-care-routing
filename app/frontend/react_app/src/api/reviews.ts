import { apiRequest } from './client';
import type { ClinicianReviewPayload, ClinicianReviewResponse } from '@/types/api';

export function submitClinicianReview(
  payload: ClinicianReviewPayload,
): Promise<ClinicianReviewResponse> {
  return apiRequest<ClinicianReviewResponse>('/clinician-review', {
    method: 'POST',
    body: payload,
  });
}
