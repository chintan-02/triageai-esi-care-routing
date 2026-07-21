import { apiBlobRequest } from './client';
import { downloadAssessmentPdf } from './assessments';

export { downloadAssessmentPdf };

export function downloadReportPdf(reportId: string): Promise<Blob> {
  return apiBlobRequest(`/reports/${encodeURIComponent(reportId)}/download`);
}
