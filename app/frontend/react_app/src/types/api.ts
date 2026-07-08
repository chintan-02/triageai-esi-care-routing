export type EsiLevel = 1 | 2 | 3 | 4 | 5;
export type ReviewStatusNormalized = 'pending' | 'accepted' | 'overridden';
export type ClinicianReviewAction = 'accept' | 'override' | 'needs_review';
export type ModelSource = 'final_registry' | 'legacy_model_artifacts' | 'unavailable' | string;

export interface ApiErrorBody {
  detail?: unknown;
  message?: string;
  error?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface ReadyResponse {
  status: 'ready' | 'not_ready' | string;
  database_connected: boolean;
  database: 'connected' | 'not_connected' | string;
  model_loaded: boolean;
  model_version: string | null;
  model_name?: string | null;
  model_source?: ModelSource | null;
  selected_calibration_method?: string | null;
  threshold_config_loaded?: boolean;
  feature_count?: number | null;
  class_order?: string[] | null;
  model_error: string | null;
  is_placeholder: boolean;
  timestamp: string;
}

export interface PatientIntakePayload {
  patient_age: number;
  sex?: string | null;
  chief_complaint: string;
  symptom_duration?: string | null;
  pain_score?: number | null;
  temperature_c?: number | null;
  heart_rate?: number | null;
  respiratory_rate?: number | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  oxygen_saturation?: number | null;
  consciousness_level?: string | null;
  pregnancy?: boolean | null;
  arrival_mode?: string | null;
  additional_context?: string | null;
}

export interface SafetyRuleResult {
  rule_id: string;
  triggered: boolean;
  message: string;
  is_placeholder: boolean;
}

export interface PredictionResponse {
  request_id: string;
  assessment_id?: string | null;
  acuity_scale: 'ESI';
  model_version?: string | null;
  model_name?: string | null;
  selected_calibration_method?: string | null;
  model_loaded: boolean;
  predicted_esi?: EsiLevel | null;
  final_esi?: EsiLevel | null;
  confidence_score?: number | null;
  probabilities: Record<string, number>;
  safety_rules_triggered: SafetyRuleResult[];
  final_source: string;
  recommendation: string;
  explanation: string;
  clinician_summary: string;
  is_placeholder: boolean;
  disclaimer: string;
  probability_note?: string | null;
}

export interface AssessmentPredictionDetail {
  prediction_id: string;
  model_version?: string | null;
  model_loaded: boolean;
  predicted_esi?: EsiLevel | null;
  final_esi?: EsiLevel | null;
  confidence_score?: number | null;
  probabilities: Record<string, number>;
  safety_rules_triggered: Array<Record<string, unknown>>;
  final_source: string;
  recommendation: string;
  explanation: string;
  clinician_summary: string;
  is_placeholder: boolean;
  created_at?: string | null;
}

export interface AssessmentClinicianReviewDetail {
  review_id: string;
  clinician_id: string;
  clinician_decision: string;
  clinician_final_esi?: EsiLevel | null;
  override_reason?: string | null;
  review_note?: string | null;
  reviewed: boolean;
  created_at?: string | null;
}

export interface AssessmentAuditEvent {
  audit_id: string;
  actor_id?: string | null;
  action: string;
  details?: Record<string, unknown> | null;
  created_at?: string | null;
  event_type?: string | null;
  message?: string | null;
  actor?: string | null;
  timestamp?: string | null;
}

export interface AssessmentListItem {
  assessment_id: string;
  patient_id?: string | null;
  patient_name?: string | null;
  mrn?: string | null;
  age?: number | null;
  sex?: string | null;
  arrival_mode?: string | null;
  chief_complaint?: string | null;
  symptom_narrative?: string | null;
  final_esi?: EsiLevel | null;
  model_predicted_esi?: EsiLevel | null;
  confidence_score?: number | null;
  latency_ms?: number | null;
  safety_escalated: boolean;
  safety_gate_status?: string | null;
  status?: string | null;
  review_status?: ReviewStatusNormalized | string | null;
  review_status_normalized?: ReviewStatusNormalized | string | null;
  reviewer?: string | null;
  reviewer_role?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AssessmentDetail extends AssessmentListItem {
  request_id: string;
  status: string;
  symptom_duration?: string | null;
  pain_score?: number | null;
  temperature_c?: number | null;
  heart_rate?: number | null;
  respiratory_rate?: number | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  oxygen_saturation?: number | null;
  consciousness_level?: string | null;
  pregnancy?: boolean | null;
  additional_context?: string | null;
  vitals: Record<string, unknown>;
  risk_flags: string[];
  comorbidities: string[];
  probabilities: Record<string, number>;
  confidence?: number | null;
  model_version?: string | null;
  request_id_value?: string | null;
  intake?: PatientIntakePayload | null;
  latest_prediction?: AssessmentPredictionDetail | null;
  latest_clinician_review?: AssessmentClinicianReviewDetail | null;
  audit_trail: AssessmentAuditEvent[];
  report_ids: string[];
  message: string;
  is_placeholder: boolean;
}

export interface AssessmentAuditTrailResponse {
  assessment_id: string;
  events: AssessmentAuditEvent[];
}

export interface ClinicianReviewPayload {
  assessment_id: string;
  clinician_id?: string;
  action: ClinicianReviewAction;
  final_esi?: EsiLevel | null;
  override_reason?: string | null;
  notes?: string | null;
}

export interface ClinicianReviewResponse {
  review_id: string;
  assessment_id: string;
  clinician_decision: string;
  clinician_final_esi?: EsiLevel | null;
  final_esi?: EsiLevel | null;
  review_note?: string | null;
  status: string;
  review_status?: ReviewStatusNormalized | string | null;
  review_status_normalized?: ReviewStatusNormalized | string | null;
  review_status_raw?: string | null;
  reviewer?: string | null;
  reviewer_role?: string | null;
  reviewed: boolean;
  reviewed_at?: string | null;
  audit_event_created: boolean;
  message: string;
  is_placeholder: boolean;
  timestamp?: string | null;
}

export interface RecentAssessmentItem {
  assessment_id: string;
  patient_id: string;
  patient_age?: number | null;
  sex?: string | null;
  chief_complaint: string;
  status: string;
  created_at: string;
  predicted_esi?: EsiLevel | null;
  model_final_esi?: EsiLevel | null;
  final_esi?: EsiLevel | null;
  clinician_final_esi?: EsiLevel | null;
  clinician_decision?: string | null;
  final_source?: string | null;
  confidence_score?: number | null;
}

export interface DashboardSummaryResponse {
  total_assessments: number;
  model_predictions_generated: number;
  reviewed_assessments: number;
  pending_reviews: number;
  completed_reviews: number;
  override_count: number;
  most_common_final_esi?: EsiLevel | null;
  high_risk_flags: number;
  esi_distribution: Record<string, number>;
  recent_assessments: RecentAssessmentItem[];
  is_placeholder: boolean;
}
