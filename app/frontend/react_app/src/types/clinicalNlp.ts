export type ClinicalIntakeVitals = {
  hr: number | null;
  sbp: number | null;
  dbp: number | null;
  rr: number | null;
  o2: number | null;
  temp: number | null;
};

export type ClinicalIntakeEvidence = {
  field: string;
  value: number | string | string[] | null;
  text: string;
};

export type ClinicalIntakeExtractionResponse = {
  age: number | null;
  gender: string | null;
  chief_complaint: string | null;
  symptoms: string[];
  vitals: ClinicalIntakeVitals;
  safety_cues: string[];
  missing_fields: string[];
  evidence: ClinicalIntakeEvidence[];
  requires_clinician_review: boolean;
  disclaimer: string;
};

export type ClinicalIntakeExtractionRequest = {
  note_text: string;
};
