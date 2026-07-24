export type NlpWorkflowState = 'not-used' | 'review-required' | 'stale' | 'reviewed';
export type ClinicianReviewState = 'not-started' | 'required' | 'accepted';

export type WorkflowStatusCode =
  | 'required-intake-incomplete'
  | 'nlp-review-required'
  | 'nlp-extraction-stale'
  | 'ready-with-undocumented-information'
  | 'ready-for-prediction'
  | 'clinician-review-required'
  | 'clinician-review-accepted';

export interface WorkflowStatus {
  code: WorkflowStatusCode;
  label: string;
  predictionEnabled: boolean;
}

export function deriveWorkflowStatus({
  requiredIntakeComplete,
  nlpState,
  hasUndocumentedInformation,
  clinicianReviewState = 'not-started'
}: {
  requiredIntakeComplete: boolean;
  nlpState: NlpWorkflowState;
  hasUndocumentedInformation: boolean;
  clinicianReviewState?: ClinicianReviewState;
}): WorkflowStatus {
  if (clinicianReviewState === 'accepted') {
    return {
      code: 'clinician-review-accepted',
      label: 'Clinician review accepted',
      predictionEnabled: false
    };
  }
  if (clinicianReviewState === 'required') {
    return {
      code: 'clinician-review-required',
      label: 'Clinician review required',
      predictionEnabled: false
    };
  }
  if (!requiredIntakeComplete) {
    return {
      code: 'required-intake-incomplete',
      label: 'Required intake incomplete',
      predictionEnabled: false
    };
  }
  if (nlpState === 'stale') {
    return {
      code: 'nlp-extraction-stale',
      label: 'NLP extraction stale',
      predictionEnabled: false
    };
  }
  if (nlpState === 'review-required') {
    return {
      code: 'nlp-review-required',
      label: 'NLP review confirmation required',
      predictionEnabled: false
    };
  }
  if (hasUndocumentedInformation) {
    return {
      code: 'ready-with-undocumented-information',
      label: 'Ready with undocumented intake information',
      predictionEnabled: true
    };
  }
  return {
    code: 'ready-for-prediction',
    label: 'Ready for prediction',
    predictionEnabled: true
  };
}
