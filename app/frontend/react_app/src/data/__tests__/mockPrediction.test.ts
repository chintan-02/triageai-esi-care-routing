import { describe, expect, it } from 'vitest';
import { simulatePrediction } from '@/data/mockData';
import type { IntakePayload } from '@/types/clinical';

const basePayload: IntakePayload = {
  patient: { id: 'PAT-test', mrn: 'MRN-test', name: 'Test Patient', age: 40, sex: 'Unknown', arrivalMode: 'Walk-in' },
  chiefComplaint: 'cough',
  symptomText: 'mild cough, no distress',
  duration: '1 day',
  vitals: { heartRate: 86, respiratoryRate: 16, systolicBp: 122, diastolicBp: 78, temperatureC: 36.9, spo2: 98, painScore: 1 },
  riskFlags: [],
  comorbidities: []
};

describe('mock prediction safety gate', () => {
  it('escalates low SpO₂ to final ESI 2 even if the model predicts ESI 3/4/5', () => {
    const prediction = simulatePrediction({ ...basePayload, vitals: { ...basePayload.vitals, spo2: 89 } }, 100);
    expect(prediction.finalEsi).toBe(2);
    expect(prediction.ruleHits.some((rule) => rule.id === 'rule_spo2_low')).toBe(true);
  });

  it('escalates chest pain with abnormal vitals instead of reporting a clean safety gate', () => {
    const prediction = simulatePrediction(
      {
        ...basePayload,
        chiefComplaint: 'Chest pain',
        vitals: { ...basePayload.vitals, heartRate: 112 },
        riskFlags: ['Chest pain']
      },
      100
    );

    expect(prediction.ruleHits.some((rule) => rule.id === 'rule_chest_pain_abnormal_vitals')).toBe(true);
    expect(prediction.explanation).not.toMatch(/No safety-rule escalation triggered/i);
  });

  it('uses the clean safety gate message only when no high-risk rule applies', () => {
    const prediction = simulatePrediction(basePayload, 100);
    expect(prediction.ruleHits).toEqual([]);
    expect(prediction.explanation).toMatch(/No safety-rule escalation triggered/i);
  });
});
