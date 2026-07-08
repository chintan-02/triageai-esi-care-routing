import { describe, expect, it } from 'vitest';
import { getMissingIntakeFields } from '@/lib/intakeValidation';

describe('intake validation', () => {
  it('blocks submit when required intake fields are missing', () => {
    expect(getMissingIntakeFields({ patient: { name: '' }, chiefComplaint: '', symptomText: ' ', duration: '' })).toEqual([
      'Patient name',
      'Chief complaint',
      'Symptom narrative',
      'Duration'
    ]);
  });
});
