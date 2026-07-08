// Wire contract with the FastAPI backend (see BACKEND_CONTRACT.md).
// The frontend is model-agnostic: the active model can change as long as the
// backend returns the same decision-support fields.

export type EsiLevel = 1 | 2 | 3 | 4 | 5;
export type ReviewStatus = 'pending' | 'accepted' | 'overridden';
export type RiskSeverity = 'low' | 'moderate' | 'high' | 'critical';

export interface PatientProfile {
  id: string;
  mrn: string;
  name: string;
  age: number;
  sex: 'Female' | 'Male' | 'Other' | 'Unknown';
  arrivalMode: 'Walk-in' | 'Ambulance' | 'Referral' | 'Other';
}

export interface Vitals {
  heartRate: number;
  respiratoryRate: number;
  systolicBp: number;
  diastolicBp: number;
  temperatureC: number;
  spo2: number;
  painScore: number;
}

export interface IntakePayload {
  patient: PatientProfile;
  chiefComplaint: string;
  symptomText: string;
  duration: string;
  vitals: Vitals;
  riskFlags: string[];
  comorbidities: string[];
}

export interface ModelMetricSnapshot {
  accuracy?: number;
  macroF1?: number;
  weightedF1?: number;
  esi5Precision?: number;
  esi5Recall?: number;
  esi5F1?: number;
  unsafeDowngradeRate?: number;
  calibrationNote?: string;
}

export interface ActiveModelStatus {
  modelVersion: string;
  modelDisplayName: string;
  modelFamily: string;
  deploymentStage: 'development' | 'staging' | 'production-ready-baseline';
  sourceNotebook: string;
  trainedRuntime: string;
  featureCount: number;
  selectedThreshold: number;
  deploymentThreshold: number;
  esi5WeightMultiplier: number;
  thresholdProfile: string;
  calibrationMethod: string;
  deployCalibratedProbabilities: boolean;
  safetyGateEnabled: boolean;
  classScope: 'ESI_3_4_5_MODEL_WITH_RULE_ESCALATION';
  metrics: ModelMetricSnapshot;
  artifactCheck: {
    status: 'passed' | 'pending' | 'failed';
    checkedAtLabel: string;
    requiredArtifacts: string[];
  };
  notes: string[];
}

export interface ModelStatusResponse {
  activeModel: ActiveModelStatus;
  apiContractVersion: string;
  backendAdapterRequired: boolean;
}

export interface RuleHit {
  id: string;
  label: string;
  description: string;
  severity: RiskSeverity;
  escalatesTo?: EsiLevel;
}

export interface PredictionResponse {
  requestId: string;
  modelVersion: string;
  modelFamily: string;
  predictedEsi: EsiLevel;
  finalEsi: EsiLevel;
  confidence: number;
  latencyMs: number;
  probabilities: Record<string, number>;
  thresholdProfile: string;
  /** Deprecated compatibility field. Use GET /api/v1/model/status for model-level evaluation metrics. */
  metrics?: ModelMetricSnapshot;
  ruleHits: RuleHit[];
  explanation: string;
  recommendation: string;
  createdAt: string;
}

export interface ClinicianReview {
  status: ReviewStatus;
  reviewer: string;
  role: 'Nurse' | 'Doctor' | 'Admin' | 'Demo Clinician';
  finalDecision: EsiLevel;
  note: string;
  reviewedAt?: string;
}

export interface AssessmentRecord {
  id: string;
  intake: IntakePayload;
  prediction: PredictionResponse;
  review: ClinicianReview;
  auditTrail: AuditEvent[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  details: string;
  severity: 'info' | 'warning' | 'critical';
}

export interface DashboardSummary {
  totalAssessments: number;
  pendingReviews: number;
  highRiskEscalations: number;
  avgLatencyMs: number;
  avgConfidence: number;
  overrideRate: number;
  esiDistribution: Record<string, number>;
}
