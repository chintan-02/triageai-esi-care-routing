// Development-only synthetic API used only when VITE_USE_MOCK_API=true.
// Production workflows use the backend modules in src/api/*.ts and the
// database-backed FastAPI service as the source of truth.
import type { AssessmentRecord, ClinicianReview, DashboardSummary, IntakePayload, ModelStatusResponse } from '@/types/clinical';
import { activeModelStatus, buildDashboardSummary, mockAssessments, simulatePrediction } from '@/data/mockData';

let records: AssessmentRecord[] = [...mockAssessments];

const wait = (ms = 240) => new Promise((resolve) => window.setTimeout(resolve, ms));

function sessionMrn() {
  return `MRN-${Date.now().toString().slice(-6)}${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`;
}

function uniqueMrn(candidate?: string) {
  const trimmed = candidate?.trim();
  if (trimmed) return trimmed;

  let next = sessionMrn();
  const used = new Set(records.map((record) => record.intake.patient.mrn));
  while (used.has(next)) next = sessionMrn();
  return next;
}

function numberOrFallback(value: unknown, fallback: number) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function normalizeCreatePayload(payload: IntakePayload): IntakePayload {
  const mrn = uniqueMrn(payload.patient.mrn);
  return {
    patient: {
      id: payload.patient.id?.trim() || `PAT-${mrn.replace(/\D/g, '').slice(-8) || Date.now().toString().slice(-6)}`,
      mrn,
      name: payload.patient.name.trim(),
      age: numberOrFallback(payload.patient.age, 0),
      sex: payload.patient.sex || 'Unknown',
      arrivalMode: payload.patient.arrivalMode || 'Walk-in'
    },
    chiefComplaint: payload.chiefComplaint.trim(),
    symptomText: payload.symptomText.trim(),
    duration: payload.duration.trim(),
    vitals: {
      heartRate: numberOrFallback(payload.vitals.heartRate, 86),
      respiratoryRate: numberOrFallback(payload.vitals.respiratoryRate, 16),
      systolicBp: numberOrFallback(payload.vitals.systolicBp, 122),
      diastolicBp: numberOrFallback(payload.vitals.diastolicBp, 78),
      temperatureC: numberOrFallback(payload.vitals.temperatureC, 36.9),
      spo2: numberOrFallback(payload.vitals.spo2, 98),
      painScore: numberOrFallback(payload.vitals.painScore, 3)
    },
    riskFlags: [...payload.riskFlags],
    comorbidities: payload.comorbidities.filter((item) => item !== 'None reported' || payload.comorbidities.length === 1)
  };
}

export const mockApi = {
  async getDashboardSummary(): Promise<DashboardSummary> {
    await wait();
    return buildDashboardSummary(records);
  },

  async getModelStatus(): Promise<ModelStatusResponse> {
    await wait(180);
    return activeModelStatus;
  },

  async listAssessments(): Promise<AssessmentRecord[]> {
    await wait();
    return [...records].sort((a, b) => +new Date(b.prediction.createdAt) - +new Date(a.prediction.createdAt));
  },

  async getAssessment(id: string): Promise<AssessmentRecord | undefined> {
    await wait();
    return records.find((record) => record.id === id);
  },

  async createAssessment(payload: IntakePayload): Promise<AssessmentRecord> {
    await wait(520);
    const normalizedPayload = normalizeCreatePayload(payload);
    const prediction = simulatePrediction(normalizedPayload);
    const record: AssessmentRecord = {
      id: `ASM-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${String(records.length + 1).padStart(3, '0')}`,
      intake: normalizedPayload,
      prediction,
      review: {
        status: 'pending',
        reviewer: 'Unassigned',
        role: 'Demo Clinician',
        finalDecision: prediction.finalEsi,
        note: 'Awaiting clinician review.'
      },
      auditTrail: [
        {
          id: `AUD-${Math.random().toString(16).slice(2, 7)}`,
          timestamp: prediction.createdAt,
          actor: 'System',
          action: 'Prediction created',
          details: 'Assessment, model output, latency and rule summary stored.',
          severity: 'info'
        },
        ...(prediction.ruleHits.length
          ? [
              {
                id: `AUD-${Math.random().toString(16).slice(2, 7)}`,
                timestamp: prediction.createdAt,
                actor: 'Rules Engine',
                action: 'Safety escalation',
                details: `Safety rules changed or confirmed final acuity as ESI ${prediction.finalEsi}.`,
                severity: 'warning' as const
              }
            ]
          : [])
      ]
    };
    records = [record, ...records];
    return record;
  },

  async saveReview(id: string, review: ClinicianReview): Promise<AssessmentRecord | undefined> {
    await wait(280);
    const index = records.findIndex((record) => record.id === id);
    if (index === -1) return undefined;
    const updated: AssessmentRecord = {
      ...records[index],
      review: {
        ...review,
        reviewedAt: new Date().toISOString()
      },
      auditTrail: [
        ...records[index].auditTrail.filter((event) => !/^Decision (accepted|overridden)$/i.test(event.action)),
        {
          id: `AUD-${Math.random().toString(16).slice(2, 7)}`,
          timestamp: new Date().toISOString(),
          actor: review.reviewer,
          action: review.status === 'overridden' ? 'Decision overridden' : 'Decision accepted',
          details: review.note || `Final decision saved as ESI ${review.finalDecision}.`,
          severity: review.status === 'overridden' ? 'warning' : 'info'
        }
      ]
    };
    records[index] = updated;
    return updated;
  }
};
