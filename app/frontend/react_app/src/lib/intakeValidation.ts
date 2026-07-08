import type { IntakePayload, PatientProfile } from '@/types/clinical';

interface DraftIntakeFields {
  patient: Pick<PatientProfile, 'name'> & Partial<Pick<PatientProfile, 'age' | 'sex' | 'arrivalMode'>>;
  chiefComplaint: string;
  symptomText: string;
  duration: string;
}

export function getMissingIntakeFields(fields: DraftIntakeFields | IntakePayload) {
  const missing: string[] = [];
  if (!fields.patient.name.trim()) missing.push('Patient name');
  if ('age' in fields.patient && !Number.isFinite(fields.patient.age)) missing.push('Age');
  if ('sex' in fields.patient && !fields.patient.sex) missing.push('Sex');
  if ('arrivalMode' in fields.patient && !fields.patient.arrivalMode) missing.push('Arrival mode');
  if (!fields.chiefComplaint.trim()) missing.push('Chief complaint');
  if (!fields.symptomText.trim()) missing.push('Symptom narrative');
  if (!fields.duration.trim()) missing.push('Duration');
  return missing;
}
