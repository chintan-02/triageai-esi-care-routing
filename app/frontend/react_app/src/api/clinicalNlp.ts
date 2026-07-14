import { apiRequest } from '@/api/client';
import type {
  ClinicalIntakeExtractionRequest,
  ClinicalIntakeExtractionResponse
} from '@/types/clinicalNlp';

export function extractClinicalIntake(
  noteText: string
): Promise<ClinicalIntakeExtractionResponse> {
  const payload: ClinicalIntakeExtractionRequest = {
    note_text: noteText
  };

  return apiRequest<ClinicalIntakeExtractionResponse>('/nlp/extract-intake', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}
