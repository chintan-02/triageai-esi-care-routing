// Synthetic fixtures for tests and explicit mock-mode UI development only.
// Real assessments, dashboard summaries, audit trails, and official reports
// come from the backend/database in normal app runtime.
import type {
  AssessmentRecord,
  AuditEvent,
  ClinicianReview,
  DashboardSummary,
  EsiLevel,
  ModelStatusResponse,
  IntakePayload,
  PatientProfile,
  PredictionResponse,
  RuleHit,
  Vitals
} from '@/types/clinical';

const now = new Date('2026-07-06T16:45:00-06:00');
const isoMinutesAgo = (minutes: number) => new Date(now.getTime() - minutes * 60_000).toISOString();

export const finalModelMetrics = {
  accuracy: 0.7832,
  macroF1: 0.7037,
  weightedF1: 0.7888,
  esi5F1: 0.547,
  unsafeDowngradeRate: 0.0068,
  calibrationNote:
    'Safety-tuned final notebook selected raw LightGBM probabilities. Calibration is not deployed because guardrails must preserve Macro F1, ESI 5 F1, and unsafe downgrade safety.'
};

export const activeModelStatus: ModelStatusResponse = {
  apiContractVersion: 'triageai.frontend.v2.1',
  backendAdapterRequired: true,
  activeModel: {
    modelVersion: 'lightgbm_v2_weight_threshold_esi345_safety_tuned',
    modelDisplayName: 'LightGBM V2 Weight + Threshold',
    modelFamily: 'LightGBM',
    deploymentStage: 'production-ready-baseline',
    sourceNotebook: 'ESI_345_FINAL_DEPLOYMENT_LIGHTGBM_V2_SAFETY_TUNED_FINAL_VERDICT_CHECKED.ipynb',
    trainedRuntime: 'Python 3.11.15 • LightGBM 4.6.0 • macOS arm64',
    featureCount: 273,
    selectedThreshold: 0.6,
    deploymentThreshold: 0.6,
    esi5WeightMultiplier: 0.75,
    thresholdProfile: 'safety_tuned_threshold_0_60_esi5_weight_0_75_raw_probabilities',
    calibrationMethod: 'raw_lightgbm_probability',
    deployCalibratedProbabilities: false,
    safetyGateEnabled: true,
    classScope: 'ESI_3_4_5_MODEL_WITH_RULE_ESCALATION',
    metrics: finalModelMetrics,
    artifactCheck: {
      status: 'passed',
      checkedAtLabel: 'Final notebook artifact check passed after run-all validation',
      requiredArtifacts: [
        'esi_345_lightgbm_v2_model.txt',
        'esi_345_lightgbm_v2_preprocessing_artifacts.joblib',
        'esi_345_lightgbm_v2_threshold_config.json',
        'esi_345_label_mapping.json',
        'metrics_test.json',
        'calibration_deployment_decision.json'
      ]
    },
    notes: [
      'The model predicts ESI 3/4/5 only.',
      'ESI 1/2 routing comes from safety gate escalation and clinician review, not from the model classifier.',
      'Calibration challengers are evaluated but raw LightGBM probabilities remain the deployment default.',
      'Safety-first selection reduced the final unsafe ESI 3 → ESI 5 downgrade rate to 0.68%.'
    ]
  }
};

export const riskFlagOptions = [
  'Chest pain',
  'Shortness of breath',
  'Altered mental status',
  'Severe pain',
  'Pregnancy concern',
  'Abnormal vital signs',
  'Immunocompromised',
  'Recent trauma'
];

export const comorbidityOptions = ['Diabetes', 'Hypertension', 'COPD/Asthma', 'Cardiac disease', 'Kidney disease', 'Cancer history', 'None reported'];

/** Core prediction simulator shared by the live intake flow and the seeded demo records. */
export function simulatePrediction(payload: IntakePayload, latencyMsOverride?: number): PredictionResponse {
  const start = performance.now();
  const riskText = `${payload.chiefComplaint} ${payload.symptomText} ${payload.riskFlags.join(' ')}`.toLowerCase();
  const riskFlags = payload.riskFlags.map((flag) => flag.toLowerCase());
  const unstableVitals =
    payload.vitals.spo2 < 92 || payload.vitals.systolicBp < 95 || payload.vitals.respiratoryRate >= 24 || payload.vitals.heartRate >= 115;
  const abnormalVitals =
    unstableVitals || payload.vitals.spo2 < 95 || payload.vitals.systolicBp < 100 || payload.vitals.respiratoryRate >= 22 || payload.vitals.heartRate >= 110;
  const highRiskComplaint = ['chest', 'breath', 'altered', 'severe', 'pregnancy'].some((term) => riskText.includes(term));

  let predictedEsi: EsiLevel = 4;
  let probabilities: Record<string, number> = { 'ESI 3': 0.25, 'ESI 4': 0.56, 'ESI 5': 0.19 };

  if (highRiskComplaint || unstableVitals || payload.vitals.painScore >= 7) {
    predictedEsi = 3;
    probabilities = { 'ESI 3': 0.64, 'ESI 4': 0.24, 'ESI 5': 0.12 };
  } else if (payload.vitals.painScore <= 2 && payload.riskFlags.length === 0) {
    predictedEsi = 5;
    probabilities = { 'ESI 3': 0.16, 'ESI 4': 0.22, 'ESI 5': 0.62 };
  }

  const ruleHits: RuleHit[] = [];
  if (payload.vitals.spo2 < 92) {
    ruleHits.push({
      id: 'rule_spo2_low',
      label: 'Low oxygen saturation safety rule',
      description: 'SpO₂ is below threshold. Final routing escalates for immediate clinician review.',
      severity: 'high',
      escalatesTo: 2
    });
  }
  if (payload.vitals.respiratoryRate >= 30) {
    ruleHits.push({
      id: 'rule_critical_respiratory_rate',
      label: 'Critical respiratory rate safety rule',
      description: 'Respiratory rate is in a critical range. Final routing escalates for immediate clinician review.',
      severity: 'high',
      escalatesTo: 2
    });
  }
  if (payload.vitals.systolicBp < 95) {
    ruleHits.push({
      id: 'rule_hypotension',
      label: 'Low blood pressure safety rule',
      description: 'Systolic blood pressure is below the safety threshold.',
      severity: 'high',
      escalatesTo: 2
    });
  }
  if (riskText.includes('altered')) {
    ruleHits.push({
      id: 'rule_altered_mental_status',
      label: 'Altered mental status rule',
      description: 'Altered mental status is treated as a high-risk safety signal.',
      severity: 'critical',
      escalatesTo: 2
    });
  }
  if ((riskFlags.includes('chest pain') || riskText.includes('chest')) && abnormalVitals) {
    ruleHits.push({
      id: 'rule_chest_pain_abnormal_vitals',
      label: 'Chest pain with abnormal vitals safety rule',
      description: 'Chest pain with abnormal vital signs requires higher-acuity safety routing for clinician review.',
      severity: 'high',
      escalatesTo: 2
    });
  }
  if ((riskFlags.includes('shortness of breath') || riskText.includes('shortness of breath') || riskText.includes('breath')) && abnormalVitals) {
    ruleHits.push({
      id: 'rule_breathing_abnormal_vitals',
      label: 'Respiratory concern with abnormal vitals safety rule',
      description: 'Shortness of breath or respiratory concern with abnormal vitals triggers safety-rule escalation.',
      severity: 'high',
      escalatesTo: 2
    });
  }
  if ((riskFlags.includes('severe pain') || payload.vitals.painScore >= 8) && abnormalVitals) {
    ruleHits.push({
      id: 'rule_severe_pain_abnormal_vitals',
      label: 'Severe pain with abnormal vitals safety rule',
      description: 'Severe pain with abnormal vital signs is routed for urgent clinician review.',
      severity: 'moderate',
      escalatesTo: 3
    });
  }
  if (riskFlags.includes('recent trauma') && abnormalVitals) {
    ruleHits.push({
      id: 'rule_trauma_abnormal_vitals',
      label: 'Recent trauma with abnormal vitals safety rule',
      description: 'Recent trauma with abnormal vital signs triggers higher-acuity safety routing.',
      severity: 'high',
      escalatesTo: 2
    });
  }
  if (riskFlags.includes('abnormal vital signs') && unstableVitals) {
    ruleHits.push({
      id: 'rule_flagged_abnormal_vitals',
      label: 'Abnormal vital signs flag safety rule',
      description: 'The abnormal vital signs flag is supported by unstable vitals in the structured intake.',
      severity: 'moderate',
      escalatesTo: 3
    });
  }

  const escalatedLevels = ruleHits.map((rule) => rule.escalatesTo).filter((level): level is EsiLevel => level !== undefined);
  const finalEsi = escalatedLevels.length ? (Math.min(predictedEsi, ...escalatedLevels) as EsiLevel) : predictedEsi;
  const latencyMs = latencyMsOverride ?? Math.max(72, Math.round(performance.now() - start + 96 + Math.random() * 50));

  return {
    requestId: `req_${Math.random().toString(16).slice(2, 8)}`,
    modelVersion: activeModelStatus.activeModel.modelVersion,
    modelFamily: activeModelStatus.activeModel.modelFamily,
    predictedEsi,
    finalEsi,
    confidence: Math.max(...Object.values(probabilities)),
    latencyMs,
    probabilities,
    thresholdProfile: activeModelStatus.activeModel.thresholdProfile,
    metrics: activeModelStatus.activeModel.metrics,
    ruleHits,
    explanation:
      finalEsi < predictedEsi
        ? `The model predicted ESI ${predictedEsi}, but safety rules escalated the final decision to ESI ${finalEsi}.`
        : ruleHits.length
          ? `The model predicted ESI ${predictedEsi}. Safety rules confirmed the final routing decision for clinician review.`
          : `The model predicted ESI ${predictedEsi}. No safety-rule escalation triggered.`,
    recommendation:
      finalEsi <= 2
        ? 'Immediate clinician assessment recommended. Confirm final acuity before care routing.'
        : finalEsi === 3
          ? 'Urgent review recommended. Validate resource need and risk indicators.'
          : 'Lower-acuity or fast-track pathway may be appropriate after clinician review.',
    createdAt: new Date().toISOString()
  };
}

interface ScenarioSeed {
  id: string;
  minutesAgo: number;
  patient: PatientProfile;
  chiefComplaint: string;
  symptomText: string;
  duration: string;
  vitals: Vitals;
  riskFlags: string[];
  comorbidities: string[];
  latencyMs: number;
  review: { status: ClinicianReview['status']; reviewer: string; role: ClinicianReview['role']; note: string; reviewMinutesAgo?: number };
}

const scenarioSeeds: ScenarioSeed[] = [
  {
    id: 'ASM-2026-0706-001',
    minutesAgo: 14,
    patient: { id: 'PAT-1001', mrn: 'MRN-582104', name: 'Maya Johnson', age: 64, sex: 'Female', arrivalMode: 'Ambulance' },
    chiefComplaint: 'Shortness of breath and chest discomfort',
    symptomText: 'Patient reports worsening shortness of breath, chest pressure, fatigue and dizziness over the last two hours.',
    duration: '2 hours',
    vitals: { heartRate: 118, respiratoryRate: 26, systolicBp: 92, diastolicBp: 58, temperatureC: 37.8, spo2: 89, painScore: 7 },
    riskFlags: ['Shortness of breath', 'Chest pain', 'Abnormal vital signs'],
    comorbidities: ['Cardiac disease', 'Hypertension'],
    latencyMs: 142,
    review: { status: 'pending', reviewer: 'Unassigned', role: 'Demo Clinician', note: 'Awaiting clinician review.' }
  },
  {
    id: 'ASM-2026-0706-002',
    minutesAgo: 42,
    patient: { id: 'PAT-1002', mrn: 'MRN-883210', name: 'Ethan Brooks', age: 29, sex: 'Male', arrivalMode: 'Walk-in' },
    chiefComplaint: 'Ankle injury after sports',
    symptomText: 'Twisted ankle during soccer. Pain and swelling. Able to speak normally and no major trauma symptoms reported.',
    duration: '4 hours',
    vitals: { heartRate: 86, respiratoryRate: 16, systolicBp: 124, diastolicBp: 78, temperatureC: 36.9, spo2: 98, painScore: 5 },
    riskFlags: ['Recent trauma'],
    comorbidities: ['None reported'],
    latencyMs: 96,
    review: { status: 'accepted', reviewer: 'Priya Nair', role: 'Nurse', note: 'Accepted model-assisted routing after physical assessment.', reviewMinutesAgo: 37 }
  },
  {
    id: 'ASM-2026-0706-003',
    minutesAgo: 76,
    patient: { id: 'PAT-1003', mrn: 'MRN-119842', name: 'Noah Singh', age: 7, sex: 'Male', arrivalMode: 'Walk-in' },
    chiefComplaint: 'Fever and sore throat',
    symptomText: 'Fever, sore throat and reduced appetite. Alert, no respiratory distress, tolerating fluids.',
    duration: '1 day',
    vitals: { heartRate: 104, respiratoryRate: 20, systolicBp: 102, diastolicBp: 64, temperatureC: 38.4, spo2: 99, painScore: 3 },
    riskFlags: [],
    comorbidities: ['None reported'],
    latencyMs: 104,
    review: { status: 'overridden', reviewer: 'Dr. Alan Reyes', role: 'Doctor', note: 'Overridden to ESI 4 due to pediatric age and clinician judgment.', reviewMinutesAgo: 66 }
  },
  {
    id: 'ASM-2026-0705-014',
    minutesAgo: 21 * 60,
    patient: { id: 'PAT-1004', mrn: 'MRN-220981', name: 'Grace Okafor', age: 41, sex: 'Female', arrivalMode: 'Walk-in' },
    chiefComplaint: 'Severe abdominal pain',
    symptomText: 'Sudden onset right lower quadrant pain, worsening over 6 hours, nausea, unable to find a comfortable position.',
    duration: '6 hours',
    vitals: { heartRate: 108, respiratoryRate: 20, systolicBp: 118, diastolicBp: 76, temperatureC: 37.9, spo2: 97, painScore: 8 },
    riskFlags: ['Severe pain'],
    comorbidities: ['None reported'],
    latencyMs: 611,
    review: { status: 'accepted', reviewer: 'Priya Nair', role: 'Nurse', note: 'Accepted. Escalated for imaging.', reviewMinutesAgo: 21 * 60 - 12 }
  },
  {
    id: 'ASM-2026-0705-013',
    minutesAgo: 24 * 60,
    patient: { id: 'PAT-1005', mrn: 'MRN-774102', name: 'Liam Chen', age: 52, sex: 'Male', arrivalMode: 'Referral' },
    chiefComplaint: 'Follow-up for hypertension medication review',
    symptomText: 'Routine follow-up, mild headache, no acute distress, requesting medication adjustment.',
    duration: '3 days',
    vitals: { heartRate: 76, respiratoryRate: 14, systolicBp: 138, diastolicBp: 88, temperatureC: 36.7, spo2: 98, painScore: 1 },
    riskFlags: [],
    comorbidities: ['Hypertension'],
    latencyMs: 88,
    review: { status: 'accepted', reviewer: 'Priya Nair', role: 'Nurse', note: 'Routed to fast-track as expected.', reviewMinutesAgo: 24 * 60 - 40 }
  },
  {
    id: 'ASM-2026-0705-012',
    minutesAgo: 27 * 60,
    patient: { id: 'PAT-1006', mrn: 'MRN-330198', name: 'Amara Diallo', age: 34, sex: 'Female', arrivalMode: 'Walk-in' },
    chiefComplaint: 'Altered mental status after fall',
    symptomText: 'Found confused after a fall at home, intermittently drowsy, slurred speech reported by family.',
    duration: '45 minutes',
    vitals: { heartRate: 122, respiratoryRate: 24, systolicBp: 88, diastolicBp: 54, temperatureC: 36.2, spo2: 91, painScore: 6 },
    riskFlags: ['Altered mental status', 'Recent trauma', 'Abnormal vital signs'],
    comorbidities: ['Diabetes'],
    latencyMs: 168,
    review: { status: 'accepted', reviewer: 'Dr. Alan Reyes', role: 'Doctor', note: 'Confirmed ESI 2, trauma bay activated.', reviewMinutesAgo: 27 * 60 - 6 }
  },
  {
    id: 'ASM-2026-0705-011',
    minutesAgo: 30 * 60,
    patient: { id: 'PAT-1007', mrn: 'MRN-118820', name: 'Oliver Kim', age: 19, sex: 'Male', arrivalMode: 'Walk-in' },
    chiefComplaint: 'Minor laceration to forearm',
    symptomText: 'Clean laceration from kitchen knife, bleeding controlled with pressure, tetanus status unknown.',
    duration: '30 minutes',
    vitals: { heartRate: 82, respiratoryRate: 15, systolicBp: 120, diastolicBp: 74, temperatureC: 36.8, spo2: 99, painScore: 4 },
    riskFlags: [],
    comorbidities: ['None reported'],
    latencyMs: 79,
    review: { status: 'pending', reviewer: 'Unassigned', role: 'Demo Clinician', note: 'Awaiting clinician review.' }
  },
  {
    id: 'ASM-2026-0704-009',
    minutesAgo: 46 * 60,
    patient: { id: 'PAT-1008', mrn: 'MRN-556213', name: 'Sofia Martinez', age: 71, sex: 'Female', arrivalMode: 'Ambulance' },
    chiefComplaint: 'Chest pain radiating to left arm',
    symptomText: 'Crushing chest pain radiating to left arm and jaw, diaphoretic, history of prior MI.',
    duration: '35 minutes',
    vitals: { heartRate: 128, respiratoryRate: 24, systolicBp: 94, diastolicBp: 60, temperatureC: 37.1, spo2: 93, painScore: 9 },
    riskFlags: ['Chest pain', 'Abnormal vital signs'],
    comorbidities: ['Cardiac disease', 'Hypertension', 'Diabetes'],
    latencyMs: 231,
    review: { status: 'accepted', reviewer: 'Dr. Alan Reyes', role: 'Doctor', note: 'Cath lab activated, ESI 1 confirmed.', reviewMinutesAgo: 46 * 60 - 4 }
  },
  {
    id: 'ASM-2026-0704-008',
    minutesAgo: 50 * 60,
    patient: { id: 'PAT-1009', mrn: 'MRN-902341', name: 'Ravi Patel', age: 45, sex: 'Male', arrivalMode: 'Walk-in' },
    chiefComplaint: 'Persistent cough and mild fever',
    symptomText: 'Productive cough for 4 days, low-grade fever, mild fatigue, no shortness of breath at rest.',
    duration: '4 days',
    vitals: { heartRate: 92, respiratoryRate: 18, systolicBp: 122, diastolicBp: 80, temperatureC: 37.6, spo2: 96, painScore: 2 },
    riskFlags: [],
    comorbidities: ['COPD/Asthma'],
    latencyMs: 402,
    review: { status: 'overridden', reviewer: 'Priya Nair', role: 'Nurse', note: 'Overridden to ESI 3 given COPD history.', reviewMinutesAgo: 50 * 60 - 18 }
  },
  {
    id: 'ASM-2026-0704-007',
    minutesAgo: 55 * 60,
    patient: { id: 'PAT-1010', mrn: 'MRN-664821', name: 'Isabella Rossi', age: 26, sex: 'Female', arrivalMode: 'Walk-in' },
    chiefComplaint: 'Migraine with photophobia',
    symptomText: 'Known migraine history, similar pattern to prior episodes, photophobia, nausea, no focal neuro deficit reported.',
    duration: '5 hours',
    vitals: { heartRate: 88, respiratoryRate: 16, systolicBp: 116, diastolicBp: 74, temperatureC: 36.9, spo2: 99, painScore: 6 },
    riskFlags: ['Severe pain'],
    comorbidities: ['None reported'],
    latencyMs: 121,
    review: { status: 'pending', reviewer: 'Unassigned', role: 'Demo Clinician', note: 'Awaiting clinician review.' }
  },
  {
    id: 'ASM-2026-0703-005',
    minutesAgo: 72 * 60,
    patient: { id: 'PAT-1011', mrn: 'MRN-441098', name: 'Benjamin Okoye', age: 58, sex: 'Male', arrivalMode: 'Referral' },
    chiefComplaint: 'Uncontrolled type 2 diabetes, referred for evaluation',
    symptomText: 'Referred by clinic for elevated glucose readings over the past week, mild fatigue, no acute distress.',
    duration: '1 week',
    vitals: { heartRate: 84, respiratoryRate: 16, systolicBp: 128, diastolicBp: 82, temperatureC: 36.8, spo2: 98, painScore: 1 },
    riskFlags: [],
    comorbidities: ['Diabetes', 'Hypertension'],
    latencyMs: 94,
    review: { status: 'accepted', reviewer: 'Priya Nair', role: 'Nurse', note: 'Routine review, routed to internal medicine.', reviewMinutesAgo: 72 * 60 - 30 }
  },
  {
    id: 'ASM-2026-0703-004',
    minutesAgo: 80 * 60,
    patient: { id: 'PAT-1012', mrn: 'MRN-207765', name: 'Chloe Anderson', age: 3, sex: 'Female', arrivalMode: 'Walk-in' },
    chiefComplaint: 'High fever and low oxygen saturation',
    symptomText: 'Fever for 2 days, increased work of breathing noted by parent, decreased oral intake, lethargic at times.',
    duration: '2 days',
    vitals: { heartRate: 138, respiratoryRate: 32, systolicBp: 96, diastolicBp: 60, temperatureC: 39.4, spo2: 91, painScore: 5 },
    riskFlags: ['Abnormal vital signs', 'Shortness of breath'],
    comorbidities: ['None reported'],
    latencyMs: 157,
    review: { status: 'accepted', reviewer: 'Dr. Alan Reyes', role: 'Doctor', note: 'Confirmed ESI 2, pediatric respiratory workup.', reviewMinutesAgo: 80 * 60 - 9 }
  }
];

function buildAuditTrail(seed: ScenarioSeed, prediction: PredictionResponse, review: ClinicianReview): AuditEvent[] {
  const trail: AuditEvent[] = [
    {
      id: `AUD-${seed.id}-created`,
      timestamp: prediction.createdAt,
      actor: 'System',
      action: 'Prediction created',
      details: 'Model output, latency and rule summary stored.',
      severity: 'info'
    }
  ];
  if (prediction.ruleHits.length) {
    trail.push({
      id: `AUD-${seed.id}-rules`,
      timestamp: prediction.createdAt,
      actor: 'Rules Engine',
      action: 'Safety escalation',
      details: `Safety rules changed or confirmed final acuity as ESI ${prediction.finalEsi}.`,
      severity: 'warning'
    });
  }
  if (review.status !== 'pending' && review.reviewedAt) {
    trail.push({
      id: `AUD-${seed.id}-review`,
      timestamp: review.reviewedAt,
      actor: review.reviewer,
      action: review.status === 'overridden' ? 'Decision overridden' : 'Decision accepted',
      details: review.note,
      severity: review.status === 'overridden' ? 'warning' : 'info'
    });
  }
  return trail;
}

function buildAssessmentFromSeed(seed: ScenarioSeed): AssessmentRecord {
  const intake: IntakePayload = {
    patient: seed.patient,
    chiefComplaint: seed.chiefComplaint,
    symptomText: seed.symptomText,
    duration: seed.duration,
    vitals: seed.vitals,
    riskFlags: seed.riskFlags,
    comorbidities: seed.comorbidities
  };

  const prediction: PredictionResponse = {
    ...simulatePrediction(intake, seed.latencyMs),
    requestId: `req_${seed.id.slice(-6).toLowerCase()}`,
    createdAt: isoMinutesAgo(seed.minutesAgo)
  };

  const review: ClinicianReview = {
    status: seed.review.status,
    reviewer: seed.review.reviewer,
    role: seed.review.role,
    finalDecision: prediction.finalEsi,
    note: seed.review.note,
    reviewedAt: seed.review.reviewMinutesAgo !== undefined ? isoMinutesAgo(seed.review.reviewMinutesAgo) : undefined
  };

  return {
    id: seed.id,
    intake,
    prediction,
    review,
    auditTrail: buildAuditTrail(seed, prediction, review)
  };
}

export const mockAssessments: AssessmentRecord[] = scenarioSeeds
  .map(buildAssessmentFromSeed)
  .sort((a, b) => +new Date(b.prediction.createdAt) - +new Date(a.prediction.createdAt));

export function buildDashboardSummary(records: AssessmentRecord[]): DashboardSummary {
  const total = records.length;
  const pendingReviews = records.filter((record) => record.review.status === 'pending').length;
  const highRiskEscalations = records.filter((record) => record.prediction.finalEsi < record.prediction.predictedEsi).length;
  const capturedLatencies = records
    .map((record) => record.prediction.latencyMs)
    .filter((value): value is number => typeof value === 'number');
  const avgLatencyMs = capturedLatencies.length
    ? Math.round(capturedLatencies.reduce((sum, value) => sum + value, 0) / capturedLatencies.length)
    : 0;
  const avgConfidence = records.reduce((sum, record) => sum + record.prediction.confidence, 0) / Math.max(total, 1);
  const overrideRate = records.filter((record) => record.review.status === 'overridden').length / Math.max(total, 1);
  const esiDistribution = records.reduce<Record<string, number>>((acc, record) => {
    const key = `ESI ${record.prediction.finalEsi}`;
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
  return { totalAssessments: total, pendingReviews, highRiskEscalations, avgLatencyMs, avgConfidence, overrideRate, esiDistribution };
}
