import { apiRequest } from './client';
import type { PatientIntakePayload, PredictionResponse } from '@/types/api';

export function createPrediction(
  payload: PatientIntakePayload,
): Promise<PredictionResponse> {
  return apiRequest<PredictionResponse>('/predict', {
    method: 'POST',
    body: payload,
  });
}
