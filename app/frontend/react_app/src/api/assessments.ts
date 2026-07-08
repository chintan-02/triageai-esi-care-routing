import { apiBlobRequest, apiRequest } from './client';
import type {
  AssessmentAuditTrailResponse,
  AssessmentDetail,
  AssessmentListItem,
} from '@/types/api';

export function listAssessments(): Promise<AssessmentListItem[]> {
  return apiRequest<AssessmentListItem[]>('/assessments');
}

export function getAssessment(assessmentId: string): Promise<AssessmentDetail> {
  return apiRequest<AssessmentDetail>(`/assessments/${encodeURIComponent(assessmentId)}`);
}

export function getAssessmentAudit(
  assessmentId: string,
): Promise<AssessmentAuditTrailResponse> {
  return apiRequest<AssessmentAuditTrailResponse>(
    `/assessments/${encodeURIComponent(assessmentId)}/audit`,
  );
}

export function downloadAssessmentPdf(assessmentId: string): Promise<Blob> {
  return apiBlobRequest(`/assessments/${encodeURIComponent(assessmentId)}/report/pdf`);
}
