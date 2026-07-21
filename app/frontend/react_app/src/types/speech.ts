export interface SpeechTranscriptionResponse {
  transcript_text: string;
  transcript?: string;
  confidence: number | null;
  language: string;
  source: string;
  requires_clinician_review: boolean;
  is_placeholder: boolean;
  message: string;
  disclaimer: string;
}
