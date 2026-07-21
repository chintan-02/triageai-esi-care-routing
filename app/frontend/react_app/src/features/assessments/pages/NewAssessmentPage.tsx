import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, CheckCircle2, ChevronDown, ClipboardCheck, FileText, Loader2, Mic, Sparkles, Square, Trash2, UserRound } from 'lucide-react';
import { createPrediction } from '@/api/predictions';
import { useToast } from '@/context/ToastContext';
import { comorbidityOptions, riskFlagOptions } from '@/data/mockData';
import type { PatientProfile, Vitals } from '@/types/clinical';
import type { NlpExtractionAuditPayload, PatientIntakePayload } from '@/types/api';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { VitalsGrid } from '@/components/clinical/VitalsGrid';
import { VitalSliderPanel } from '@/components/clinical/VitalSliderPanel';
import { vitalFlag } from '@/lib/vitals';
import { getMissingIntakeFields } from '@/lib/intakeValidation';
import { extractClinicalIntake } from '@/api/clinicalNlp';
import { transcribeRecording } from '@/api/speech';
import { ClinicalNlpReviewPanel } from '@/components/clinical-nlp/ClinicalNlpReviewPanel';
import type { ClinicalIntakeExtractionResponse } from '@/types/clinicalNlp';
import type { SpeechTranscriptionResponse } from '@/types/speech';

function createDefaultPatient(): PatientProfile {
  const entropy = `${Date.now().toString().slice(-5)}${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`;
  return {
    id: `PAT-${entropy}`,
    mrn: `MRN-${entropy}`,
    name: '',
    age: 32,
    sex: 'Unknown',
    arrivalMode: 'Walk-in'
  };
}

const defaultVitals: Vitals = {
  heartRate: 86,
  respiratoryRate: 16,
  systolicBp: 122,
  diastolicBp: 78,
  temperatureC: 36.9,
  spo2: 98,
  painScore: 3
};

const CLINICAL_NLP_DEMO_NOTE =
  '62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2. Patient looks pale and dizzy.';

function createDefaultVitals(): Vitals {
  return { ...defaultVitals };
}

const steps = [
  { id: 'patient', label: 'Patient' },
  { id: 'complaint', label: 'Complaint' },
  { id: 'vitals', label: 'Vitals' },
  { id: 'risks', label: 'Selected Risk Flags' },
  { id: 'review', label: 'Review & Predict' }
] as const;

type StepId = (typeof steps)[number]['id'];
type RecordingState = 'idle' | 'requesting' | 'recording' | 'stopping';

const stepCardClass = 'flex flex-col rounded-[1.2rem] border border-slate-200 bg-white p-3 shadow-[0_10px_30px_-24px_rgba(15,23,42,0.35)]';
const fieldClass = 'space-y-1.5 text-sm font-semibold text-slate-700';

function displayValue(value: string, fallback = 'Not entered') {
  return value.trim() || fallback;
}

function toNullableText(value: string) {
  const trimmed = value.trim();
  return trimmed || null;
}

function microphoneErrorMessage(error: unknown) {
  const errorName = error instanceof DOMException
    ? error.name
    : typeof error === 'object' && error && 'name' in error
      ? String(error.name)
      : '';

  if (errorName === 'NotAllowedError' || errorName === 'SecurityError') {
    return 'Microphone permission was denied. Allow microphone access in your browser and try again.';
  }

  if (errorName === 'NotFoundError' || errorName === 'DevicesNotFoundError') {
    return 'No microphone is available. Connect a microphone and try again.';
  }

  if (['NotReadableError', 'TrackStartError', 'AbortError'].includes(errorName)) {
    return 'The microphone is unavailable or already in use. Close other audio apps and try again.';
  }

  return 'The microphone could not be started. Check browser permissions and try again.';
}

function stopMediaStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop());
}

function buildPredictionPayload(
  patient: PatientProfile,
  chiefComplaint: string,
  symptomText: string,
  duration: string,
  vitals: Vitals,
  nlpExtractionAudit?: NlpExtractionAuditPayload
): PatientIntakePayload {
  return {
    patient_name: toNullableText(patient.name),
    mrn: toNullableText(patient.mrn),
    patient_age: patient.age,
    sex: patient.sex === 'Unknown' ? null : patient.sex.toLowerCase(),
    chief_complaint: chiefComplaint.trim(),
    symptom_duration: toNullableText(duration),
    pain_score: vitals.painScore,
    temperature_c: vitals.temperatureC,
    heart_rate: vitals.heartRate,
    respiratory_rate: vitals.respiratoryRate,
    systolic_bp: vitals.systolicBp,
    diastolic_bp: vitals.diastolicBp,
    oxygen_saturation: vitals.spo2,
    arrival_mode: patient.arrivalMode,
    additional_context: toNullableText(symptomText),
    ...(nlpExtractionAudit ? { nlp_extraction_audit: nlpExtractionAudit } : {})
  };
}

function buildNlpExtractionAudit(
  extraction: ClinicalIntakeExtractionResponse
): NlpExtractionAuditPayload {
  return {
    reviewed: true,
    source: 'clinical_intake_nlp',
    extracted_fields: {
      age: extraction.age,
      gender: extraction.gender,
      chief_complaint: extraction.chief_complaint,
      symptoms: extraction.symptoms,
      vitals: extraction.vitals
    },
    safety_cues: extraction.safety_cues,
    missing_fields: extraction.missing_fields,
    evidence: extraction.evidence,
    disclaimer: extraction.disclaimer
  };
}

export function NewAssessmentPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [patient, setPatient] = useState<PatientProfile>(() => createDefaultPatient());
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [symptomText, setSymptomText] = useState('');
  const [duration, setDuration] = useState('');
  const [clinicalNote, setClinicalNote] = useState('');
  const [transcriptText, setTranscriptText] = useState('');
  const [isSpeechExpanded, setIsSpeechExpanded] = useState(false);
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null);
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<SpeechTranscriptionResponse | null>(null);
  const [transcriptionError, setTranscriptionError] = useState<string | null>(null);
  const [nlpExtraction, setNlpExtraction] = useState<ClinicalIntakeExtractionResponse | null>(null);
  const [isExtractingNlp, setIsExtractingNlp] = useState(false);
  const [nlpError, setNlpError] = useState<string | null>(null);
  const [isNlpReviewed, setIsNlpReviewed] = useState(false);
  const [vitals, setVitals] = useState<Vitals>(() => createDefaultVitals());
  const [riskFlags, setRiskFlags] = useState<string[]>([]);
  const [comorbidities, setComorbidities] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingUrlRef = useRef<string | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
      const recorder = mediaRecorderRef.current;

      if (recorder && recorder.state !== 'inactive') {
        recorder.ondataavailable = null;
        recorder.onstop = null;
        recorder.onerror = null;
        recorder.stop();
      }

      stopMediaStream(mediaStreamRef.current);
      mediaRecorderRef.current = null;
      mediaStreamRef.current = null;

      if (recordingUrlRef.current) {
        URL.revokeObjectURL(recordingUrlRef.current);
        recordingUrlRef.current = null;
      }
    };
  }, []);

  const missingFields = useMemo(
    () => getMissingIntakeFields({ patient, chiefComplaint, symptomText, duration }),
    [patient, chiefComplaint, symptomText, duration]
  );

  const needsNlpReview = Boolean(nlpExtraction && !isNlpReviewed);
  const stepErrors = useMemo<Record<StepId, string[]>>(
    () => ({
      patient: patient.name.trim() ? [] : ['Patient name is required'],
      complaint: [
        !chiefComplaint.trim() ? 'Chief complaint is required' : '',
        !symptomText.trim() ? 'Symptom narrative is required' : '',
        !duration.trim() ? 'Duration is required' : ''
      ].filter(Boolean),
      vitals: [],
      risks: [],
      review: [
      ...missingFields,
      ...(needsNlpReview ? ['Review NLP extracted fields before prediction'] : [])
    ]
    }),
    [chiefComplaint, duration, missingFields, needsNlpReview, patient.name, symptomText]
  );

  const abnormalVitalCount = useMemo(
    () =>
      (Object.keys(vitals) as Array<keyof Vitals>).filter((key) => vitalFlag(key, vitals[key], patient.age) !== 'normal').length,
    [patient.age, vitals]
  );

  const activeStep = steps[currentStep];
  const canGoNext = stepErrors[activeStep.id].length === 0;
  const progress = ((currentStep + 1) / steps.length) * 100;

  const toggle = (value: string, list: string[], setter: (next: string[]) => void) => {
    setter(list.includes(value) ? list.filter((item) => item !== value) : [...list, value]);
  };

  const toggleComorbidity = (value: string) => {
    if (value === 'None reported') {
      setComorbidities((current) => (current.includes('None reported') ? [] : ['None reported']));
      return;
    }

    setComorbidities((current) => {
      const withoutNone = current.filter((item) => item !== 'None reported');
      return withoutNone.includes(value) ? withoutNone.filter((item) => item !== value) : [...withoutNone, value];
    });
  };

  const goNext = () => {
    if (!canGoNext) return;
    setCurrentStep((step) => Math.min(step + 1, steps.length - 1));
  };

  const preventImplicitSubmit = (event: FormEvent) => {
    event.preventDefault();
  };

  const handleUseDemoNote = () => {
    setClinicalNote(CLINICAL_NLP_DEMO_NOTE);
    setNlpExtraction(null);
    setIsNlpReviewed(false);
    setNlpError(null);
  };

  const handleUseTranscript = () => {
    setClinicalNote(transcriptText);
    setNlpExtraction(null);
    setIsNlpReviewed(false);
    setNlpError(null);
  };

  const handleStartRecording = async () => {
    setRecordingError(null);

    if (
      typeof MediaRecorder === 'undefined'
      || !navigator.mediaDevices?.getUserMedia
    ) {
      setRecordingError(
        'Microphone recording is not supported in this browser. You can still enter transcript text manually.'
      );
      return;
    }

    setRecordingState('requesting');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      if (!isMountedRef.current) {
        stopMediaStream(stream);
        return;
      }

      mediaStreamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        stopMediaStream(mediaStreamRef.current);
        mediaStreamRef.current = null;
        mediaRecorderRef.current = null;

        if (!isMountedRef.current) return;

        const chunks = audioChunksRef.current;
        audioChunksRef.current = [];

        if (chunks.length > 0) {
          const recording = new Blob(chunks, {
            type: recorder.mimeType || chunks[0].type || 'audio/webm'
          });

          if (recordingUrlRef.current) {
            URL.revokeObjectURL(recordingUrlRef.current);
          }

          const nextUrl = URL.createObjectURL(recording);
          recordingUrlRef.current = nextUrl;
          setRecordingBlob(recording);
          setRecordingUrl(nextUrl);
          setTranscriptionResult(null);
          setTranscriptionError(null);
        } else {
          setRecordingError('No audio was captured. Please try recording again.');
        }

        setRecordingState('idle');
      };

      recorder.onerror = () => {
        if (isMountedRef.current) {
          setRecordingError('Audio recording stopped unexpectedly. Please try again.');
          setRecordingState('idle');
        }
        stopMediaStream(mediaStreamRef.current);
        mediaStreamRef.current = null;
        mediaRecorderRef.current = null;
      };

      recorder.start();
      setRecordingState('recording');
    } catch (error) {
      stopMediaStream(mediaStreamRef.current);
      mediaStreamRef.current = null;
      mediaRecorderRef.current = null;

      if (isMountedRef.current) {
        setRecordingState('idle');
        setRecordingError(microphoneErrorMessage(error));
      }
    }
  };

  const handleStopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === 'inactive') return;

    setRecordingState('stopping');
    recorder.stop();
    stopMediaStream(mediaStreamRef.current);
    mediaStreamRef.current = null;
  };

  const handleClearRecording = () => {
    if (recordingUrlRef.current) {
      URL.revokeObjectURL(recordingUrlRef.current);
      recordingUrlRef.current = null;
    }
    setRecordingBlob(null);
    setRecordingUrl(null);
    setRecordingError(null);
    setTranscriptionResult(null);
    setTranscriptionError(null);
  };

  const handleTranscribeRecording = async () => {
    if (!recordingBlob || isTranscribing) return;

    setIsTranscribing(true);
    setTranscriptionResult(null);
    setTranscriptionError(null);

    try {
      const result = await transcribeRecording(recordingBlob);
      if (!isMountedRef.current) return;

      const returnedTranscript = (result.transcript_text || result.transcript || '').trim();
      if (returnedTranscript) {
        setTranscriptText(returnedTranscript);
      }
      setTranscriptionResult(result);
    } catch {
      if (!isMountedRef.current) return;
      setTranscriptionError(
        'Recording could not be transcribed. You can enter transcript text manually or try again.'
      );
    } finally {
      if (isMountedRef.current) {
        setIsTranscribing(false);
      }
    }
  };
  
  const handleExtractClinicalNote = async () => {
  const note = clinicalNote.trim();

  if (!note || isExtractingNlp) return;

  setIsExtractingNlp(true);
  setNlpError(null);
  setIsNlpReviewed(false);

  try {
    const extraction = await extractClinicalIntake(note);
    setNlpExtraction(extraction);

    setPatient((current) => ({
      ...current,
      age: extraction.age ?? current.age,
      sex: extraction.gender
        ? (extraction.gender as PatientProfile['sex'])
        : current.sex
    }));

    if (extraction.chief_complaint) {
      setChiefComplaint(extraction.chief_complaint);
    }

    if (extraction.symptoms.length) {
      setSymptomText(note);
    }

    setVitals((current) => ({
      ...current,
      heartRate: extraction.vitals.hr ?? current.heartRate,
      respiratoryRate: extraction.vitals.rr ?? current.respiratoryRate,
      systolicBp: extraction.vitals.sbp ?? current.systolicBp,
      diastolicBp: extraction.vitals.dbp ?? current.diastolicBp,
      temperatureC: extraction.vitals.temp ?? current.temperatureC,
      spo2: extraction.vitals.o2 ?? current.spo2
    }));

    showToast({
      tone: 'success',
      title: 'Intake fields extracted',
      description: 'Review and edit the extracted fields before running ESI decision support.'
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Could not extract clinical intake fields.';
    setNlpError(message);
    showToast({
      tone: 'error',
      title: 'Clinical NLP extraction failed',
      description: message
    });
  } finally {
    setIsExtractingNlp(false);
  }
};
  

  const handleRunDecisionSupport = async () => {
    if (missingFields.length || needsNlpReview || isSubmitting) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const nlpExtractionAudit =
        nlpExtraction && isNlpReviewed
          ? buildNlpExtractionAudit(nlpExtraction)
          : undefined;
      const payload = buildPredictionPayload(
        patient,
        chiefComplaint,
        symptomText,
        duration,
        vitals,
        nlpExtractionAudit
      );
      const prediction = await createPrediction(payload);
      if (!prediction.assessment_id) {
        throw new Error('Prediction completed, but the backend did not return an assessment ID.');
      }
      showToast({
        tone: 'success',
        title: 'Assessment created',
        description: `${prediction.assessment_id} routed to ESI ${prediction.final_esi ?? 'pending clinician review'}.`
      });
      navigate(`/assessments/${prediction.assessment_id}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Please try again or confirm the FastAPI backend is available.';
      setSubmitError(message);
      showToast({ tone: 'error', title: 'Could not run ESI decision support', description: message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-x-hidden overflow-y-auto pb-5">
      <div className="mb-4 flex shrink-0 flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-[0.22em] text-clinical-blue">New clinical intake</p>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-slate-950">Structured ESI intake workspace</h1>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">
            Structured intake, vitals, safety-rule escalation, and clinician review in one compact workspace.
          </p>
        </div>
        <div className="rounded-2xl border border-blue-100 bg-blue-50 px-3.5 py-2.5 text-xs font-semibold leading-5 text-blue-900">
          Model predicts <span className="font-black">ESI 3/4/5</span>; safety rules and clinician review can escalate final routing.
        </div>
      </div>

      <form onSubmit={preventImplicitSubmit} className="grid items-start gap-4 2xl:grid-cols-[minmax(0,1fr)_300px] 2xl:gap-5">
        <section className="flex flex-col self-start overflow-hidden rounded-[1.45rem] border border-slate-200 bg-white/95 shadow-soft backdrop-blur">
          <div className="shrink-0 border-b border-slate-100 px-3.5 py-2.5 sm:px-4">
            <div className="hide-scrollbar flex gap-2 overflow-x-auto pb-1">
              {steps.map((step, index) => {
                const isActive = index === currentStep;
                const isDone = index < currentStep;
                const hasError = stepErrors[step.id].length > 0;
                const isAttention = !isActive && !isDone && index === currentStep - 1 && hasError;
                return (
                  <button
                    key={step.id}
                    type="button"
                    onClick={() => setCurrentStep(index)}
                    className={`shrink-0 rounded-full border px-3 py-1.5 text-[11px] font-black uppercase tracking-wide transition ${
                      isActive
                        ? 'border-clinical-navy bg-clinical-navy text-white shadow-soft'
                        : isDone
                          ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                          : isAttention
                            ? 'border-amber-200 bg-amber-50 text-amber-800'
                            : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {index + 1}. {step.label}
                  </button>
                );
              })}
            </div>
            <div className="mt-2.5 h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-clinical-blue transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>

          <div className="p-3">
            {activeStep.id === 'patient' ? (
              <div className={`${stepCardClass} gap-3`}>
                <div className="shrink-0">
                  <h2 className="text-lg font-black text-slate-950">1. Patient information</h2>
                  <p className="mt-1 text-sm text-slate-600">Core identifiers and arrival context for the structured intake record.</p>
                </div>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                  <label className={fieldClass}>
                    Patient name
                    <input value={patient.name} onChange={(event) => setPatient({ ...patient, name: event.target.value })} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5" placeholder="Example: Alex Morgan" />
                  </label>
                  <label className={fieldClass}>
                    MRN
                    <input value={patient.mrn} onChange={(event) => setPatient({ ...patient, mrn: event.target.value })} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5 font-data" />
                  </label>
                  <label className={fieldClass}>
                    Age
                    <input type="number" min={0} value={patient.age} onChange={(event) => setPatient({ ...patient, age: Number(event.target.value) })} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5" />
                  </label>
                  <label className={fieldClass}>
                    Sex
                    <select value={patient.sex} onChange={(event) => setPatient({ ...patient, sex: event.target.value as PatientProfile['sex'] })} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5">
                      <option>Unknown</option>
                      <option>Female</option>
                      <option>Male</option>
                      <option>Other</option>
                    </select>
                  </label>
                  <label className={`${fieldClass} md:col-span-2 xl:col-span-1`}>
                    Arrival mode
                    <select value={patient.arrivalMode} onChange={(event) => setPatient({ ...patient, arrivalMode: event.target.value as PatientProfile['arrivalMode'] })} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5">
                      <option>Walk-in</option>
                      <option>Ambulance</option>
                      <option>Referral</option>
                      <option>Other</option>
                    </select>
                  </label>
                </div>
              </div>
            ) : null}

            {activeStep.id === 'complaint' ? (
              <div className={`${stepCardClass} gap-3`}>
                <div className="shrink-0">
                  <h2 className="text-lg font-black text-slate-950">2. Complaint and symptom narrative</h2>
                  <p className="mt-1 text-sm text-slate-600">Capture the chief complaint and symptom narrative concisely.</p>
                </div>
                <div className="grid gap-3">
                <div className="rounded-[1.2rem] border border-blue-100 bg-blue-50/70 p-3">
  <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
    <div>
      <div className="flex items-center gap-2 text-sm font-black text-blue-950">
        <FileText size={18} />
        Clinical note extraction
      </div>
      <p className="mt-1 text-sm leading-6 text-blue-900">
        Paste a clinician note or transcript to extract structured intake fields for review. This is not diagnosis and does not auto-run prediction.
      </p>
    </div>
    <Badge className="border-blue-200 bg-white text-blue-800">
      Optional assistant
    </Badge>
  </div>

  <label className="flex flex-col gap-1.5 text-sm font-semibold text-slate-700">
    Clinical note / transcript
    <textarea
      value={clinicalNote}
      onChange={(event) => setClinicalNote(event.target.value)}
      className="focus-ring min-h-[112px] resize-y rounded-2xl border border-blue-100 bg-white px-3.5 py-2.5"
      placeholder="Example: 62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2."
    />
  </label>

  <div className="mt-3 rounded-2xl border border-blue-100 bg-white/80 p-3">
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-2.5">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
          <Mic size={16} />
        </div>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-black text-blue-950">Speech / transcript</p>
            {recordingBlob ? (
              <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">Recording ready</Badge>
            ) : null}
          </div>
          <p className="mt-0.5 text-xs font-semibold text-slate-600">Optional voice or transcript input</p>
        </div>
      </div>
      <Button
        type="button"
        variant="secondary"
        className="shrink-0 px-3 py-2 text-xs"
        aria-controls="speech-transcript-controls"
        aria-expanded={isSpeechExpanded}
        disabled={recordingState !== 'idle' || isTranscribing}
        onClick={() => setIsSpeechExpanded((expanded) => !expanded)}
      >
        {isSpeechExpanded ? 'Hide voice / transcript input' : 'Use voice / transcript input'}
        <ChevronDown className={`transition-transform ${isSpeechExpanded ? 'rotate-180' : ''}`} size={16} />
      </Button>
    </div>
    <p className="mt-2 text-xs font-semibold leading-5 text-blue-900">
      Transcript text must be reviewed before extraction or prediction.
    </p>

    {isSpeechExpanded ? (
      <div id="speech-transcript-controls" className="mt-3 border-t border-blue-100 pt-3">
    <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          className="px-3 py-2 text-xs"
          disabled={recordingState !== 'idle' || isTranscribing}
          onClick={handleStartRecording}
        >
          {recordingState === 'requesting' ? <Loader2 className="animate-spin" size={16} /> : <Mic size={16} />}
          {recordingState === 'requesting' ? 'Requesting microphone' : 'Start recording'}
        </Button>
        <Button
          type="button"
          variant="danger"
          className="px-3 py-2 text-xs"
          disabled={recordingState !== 'recording'}
          onClick={handleStopRecording}
        >
          <Square size={14} />
          Stop recording
        </Button>
        <Button
          type="button"
          variant="ghost"
          className="px-3 py-2 text-xs"
          disabled={!recordingUrl || recordingState !== 'idle' || isTranscribing}
          onClick={handleClearRecording}
        >
          <Trash2 size={16} />
          Clear recording
        </Button>
        <Button
          type="button"
          variant="secondary"
          className="px-3 py-2 text-xs"
          disabled={!recordingBlob || recordingState !== 'idle' || isTranscribing}
          onClick={handleTranscribeRecording}
        >
          {isTranscribing ? <Loader2 className="animate-spin" size={16} /> : <FileText size={16} />}
          {isTranscribing ? 'Transcribing recording' : 'Transcribe recording'}
        </Button>
        {recordingState === 'recording' ? (
          <span className="inline-flex items-center gap-2 text-xs font-bold text-red-700" role="status">
            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-red-600" />
            Recording locally
          </span>
        ) : null}
        {recordingState === 'stopping' ? (
          <span className="text-xs font-semibold text-slate-600" role="status">Preparing playback…</span>
        ) : null}
      </div>

      {recordingUrl ? (
        <audio
          aria-label="Recorded audio playback"
          className="mt-3 h-10 w-full"
          controls
          preload="metadata"
          src={recordingUrl}
        />
      ) : null}

      {recordingError ? (
        <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold leading-5 text-amber-900" role="alert">
          {recordingError}
        </div>
      ) : null}

      {transcriptionResult ? (
        <div
          className={`mt-3 rounded-xl border px-3 py-2 text-xs font-semibold leading-5 ${
            transcriptionResult.is_placeholder
              ? 'border-amber-200 bg-amber-50 text-amber-900'
              : 'border-emerald-200 bg-emerald-50 text-emerald-900'
          }`}
          role="status"
        >
          <p>{transcriptionResult.message}</p>
          <p className="mt-1 font-medium">{transcriptionResult.disclaimer}</p>
        </div>
      ) : null}

      {transcriptionError ? (
        <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold leading-5 text-red-800" role="alert">
          {transcriptionError}
        </div>
      ) : null}

      <p className="mt-2 text-xs font-semibold leading-5 text-slate-600">
        Audio recording is for local clinician review only.
      </p>
    </div>
    <label className="mt-2 flex flex-col gap-1.5 text-sm font-semibold text-slate-700">
      Transcript text
      <textarea
        value={transcriptText}
        onChange={(event) => setTranscriptText(event.target.value)}
        className="focus-ring min-h-[88px] resize-y rounded-2xl border border-blue-100 bg-white px-3.5 py-2.5"
        placeholder="Paste or enter transcript text for clinician review."
      />
    </label>
    <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs font-semibold leading-5 text-blue-900">
        Review and edit the transcript before copying it into the clinical note.
      </p>
      <Button
        type="button"
        variant="secondary"
        disabled={!transcriptText.trim() || isExtractingNlp}
        onClick={handleUseTranscript}
      >
        Use transcript as clinical note
      </Button>
    </div>
      </div>
    ) : null}
  </div>

  <div className="mt-2 w-fit">
    <Button
      type="button"
      variant="secondary"
      className="px-3 py-2 text-xs"
      disabled={isExtractingNlp}
      onClick={handleUseDemoNote}
    >
      Use demo note
    </Button>
    <p className="mt-1 text-[11px] font-semibold text-blue-800">
      Demo note is for workflow testing only.
    </p>
  </div>

  <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
    <p className="text-xs font-semibold leading-5 text-blue-900">
      Extracted values are copied into editable fields below. Clinician review is required before prediction.
    </p>
    <Button
      type="button"
      variant="secondary"
      disabled={!clinicalNote.trim() || isExtractingNlp}
      onClick={handleExtractClinicalNote}
    >
      {isExtractingNlp ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
      Extract Intake Fields
    </Button>
  </div>

  {nlpError ? (
    <div className="mt-2 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-800">
      {nlpError}
    </div>
  ) : null}

  {nlpExtraction ? (
    <div className="mt-3">
      <ClinicalNlpReviewPanel
        extraction={nlpExtraction}
        isReviewed={isNlpReviewed}
        onReviewedChange={setIsNlpReviewed}
      />
      <p className="mt-2 rounded-2xl border border-blue-100 bg-white px-3 py-2 text-xs font-semibold leading-5 text-blue-900">
        Extracted values were copied into the editable structured fields below. Confirm or edit them before continuing.
      </p>
    </div>
  ) : null}
</div>
                  <div className="flex flex-col gap-1 border-b border-slate-100 pb-2 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-sm font-black text-slate-900">Editable structured intake</p>
                      <p className="mt-0.5 text-xs font-semibold text-slate-500">These fields are used for decision support after clinician confirmation.</p>
                    </div>
                    {nlpExtraction ? (
                      <Badge className="border-blue-200 bg-blue-50 text-blue-800">Updated from extraction</Badge>
                    ) : null}
                  </div>
                  <label className={fieldClass}>
                    Chief complaint
                    <input value={chiefComplaint} onChange={(event) => setChiefComplaint(event.target.value)} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5" placeholder="Example: chest pain and shortness of breath" />
                  </label>
                  <label className="flex flex-col gap-1.5 text-sm font-semibold text-slate-700">
                    Symptom narrative
                    <textarea value={symptomText} onChange={(event) => setSymptomText(event.target.value)} className="focus-ring min-h-[128px] resize-y rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5" placeholder="Brief but clinically useful description..." />
                  </label>
                  <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_220px] md:items-end">
                    <p className="rounded-2xl border border-blue-100 bg-blue-50 px-3.5 py-2.5 text-sm font-semibold leading-6 text-blue-900">
                      Keep the narrative concise, clinically relevant, and ready for clinician review.
                    </p>
                    <label className={fieldClass}>
                      Duration
                      <input value={duration} onChange={(event) => setDuration(event.target.value)} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5" placeholder="Example: 2 hours" />
                    </label>
                  </div>
                </div>
              </div>
            ) : null}

            {activeStep.id === 'vitals' ? (
              <div className={`${stepCardClass} min-h-0 overflow-hidden`}>
                <div className="mb-2.5 shrink-0">
                  <h2 className="text-lg font-black text-slate-950">3. Vitals</h2>
                  <p className="mt-1 text-sm text-slate-600">Responsive vitals cards with fixed reference bands and independent current-value markers.</p>
                </div>
                <VitalSliderPanel vitals={vitals} age={patient.age} onChange={setVitals} />
              </div>
            ) : null}

            {activeStep.id === 'risks' ? (
              <div className={`${stepCardClass} gap-3`}>
                <div className="shrink-0">
                  <h2 className="text-lg font-black text-slate-950">4. Selected risk flags and comorbidities</h2>
                  <p className="mt-1 text-sm text-slate-600">Selected risk flags are intake context. Measured vital abnormalities are shown separately in the vitals summary.</p>
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="mb-2 text-sm font-bold text-slate-700">Selected risk flags</p>
                    <div className="flex flex-wrap gap-2">
                      {riskFlagOptions.map((flag) => (
                        <button type="button" key={flag} onClick={() => toggle(flag, riskFlags, setRiskFlags)} className={`rounded-full border px-3 py-2 text-sm font-semibold transition ${riskFlags.includes(flag) ? 'border-red-200 bg-red-50 text-red-800' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'}`}>
                          {flag}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="mb-2 text-sm font-bold text-slate-700">Comorbidities</p>
                    <div className="flex flex-wrap gap-2">
                      {comorbidityOptions.map((item) => (
                        <button type="button" key={item} onClick={() => toggleComorbidity(item)} className={`rounded-full border px-3 py-2 text-sm font-semibold transition ${comorbidities.includes(item) ? 'border-blue-200 bg-blue-50 text-blue-800' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'}`}>
                          {item}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            {activeStep.id === 'review' ? (
              <div className={`${stepCardClass} gap-3`}>
                <div className="shrink-0">
                  <h2 className="text-lg font-black text-slate-950">5. Review & Predict</h2>
                  <p className="mt-1 text-sm text-slate-600">Confirm the structured intake before running ESI decision support.</p>
                </div>
                {missingFields.length ? (
                  <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                    <div className="flex items-center gap-2 font-black">
                      <AlertTriangle size={18} />
                      Step needs attention
                    </div>
                    <p className="mt-1 text-amber-800">Complete the required fields before running ESI decision support.</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {missingFields.map((field) => (
                        <Badge key={field} className="border-amber-200 bg-white text-amber-800">
                          {field}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
                    <div className="flex items-center gap-2 font-black">
                      <CheckCircle2 size={18} />
                      Ready for prediction
                    </div>
                    <p className="mt-1 text-emerald-800">Required intake fields are complete for backend ESI decision support.</p>
                  </div>
                )}
                <div className="grid gap-2.5 xl:grid-cols-2">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Patient context</p>
                    <p className="mt-2 font-bold text-slate-950">{displayValue(patient.name)}</p>
                    <p className="mt-1 text-sm text-slate-600">MRN {displayValue(patient.mrn)} • Age {patient.age} • {patient.sex} • {patient.arrivalMode}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Chief complaint and symptom narrative</p>
                    <p className="mt-2 font-bold text-slate-950">{displayValue(chiefComplaint)}</p>
                    <p className="mt-1 line-clamp-3 text-sm leading-6 text-slate-600">{displayValue(symptomText)}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Duration</p>
                    <p className="mt-2 font-bold text-slate-950">{displayValue(duration)}</p>
                    <p className="mt-1 text-sm text-slate-600">Captured as reported in the structured intake.</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Selected risk flags</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {riskFlags.length ? riskFlags.map((flag) => <Badge key={flag} className="border-red-200 bg-red-50 text-red-800">{flag}</Badge>) : <span className="text-sm font-semibold text-slate-500">None selected</span>}
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Comorbidities</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {comorbidities.length ? comorbidities.map((item) => <Badge key={item} className="border-blue-200 bg-blue-50 text-blue-800">{item}</Badge>) : <span className="text-sm font-semibold text-slate-500">None selected</span>}
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Safety gate preview</p>
                    <p className="mt-2 font-bold text-slate-950">{missingFields.length ? 'Step needs attention' : 'Ready for prediction'}</p>
                    <p className="mt-1 text-sm text-slate-600">{abnormalVitalCount} watch vitals. Safety rules and clinician review can escalate final routing before sign-off.</p>
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-2.5 sm:p-3">
                  <p className="mb-2 text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Vitals summary</p>
                  <VitalsGrid vitals={vitals} age={patient.age} />
                </div>
                <div className="shrink-0 rounded-2xl border border-slate-200 bg-slate-950 p-3 text-sm leading-6 text-slate-200">
                  <div className="mb-2 flex items-center gap-2 font-bold text-white"><ClipboardCheck size={18} /> Decision-support summary</div>
                  The model predicts ESI 3/4/5. Safety rules and clinician review can escalate the final routing decision to ESI 1/2 when high-risk criteria are present.
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Badge className="border-white/15 bg-white/10 text-white">Structured intake</Badge>
                    <Badge className="border-white/15 bg-white/10 text-white">Safety rules</Badge>
                    <Badge className="border-white/15 bg-white/10 text-white">Clinician review</Badge>
                  </div>
                </div>
                {submitError ? (
                  <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-800">
                    {submitError}
                  </div>
                ) : null}

                {needsNlpReview ? (
              <div className="rounded-2xl border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                <div className="flex items-center gap-2 font-black">
                  <ClipboardCheck size={18} />
                  NLP extraction review required
                </div>
                <p className="mt-1 text-blue-800">
                  Review the extracted fields in the complaint step before running ESI decision support.
                </p>
              </div>
            ) : null}
              </div>
            ) : null}
          </div>

          <div className="flex shrink-0 flex-col gap-2 border-t border-slate-100 px-3.5 py-3 sm:flex-row sm:justify-between sm:px-4">
            <Button type="button" variant="secondary" disabled={currentStep === 0} onClick={() => setCurrentStep((step) => Math.max(step - 1, 0))}>
              Back
            </Button>
            {currentStep < steps.length - 1 ? (
              <Button type="button" disabled={!canGoNext} onClick={goNext}>
                Next
              </Button>
            ) : (
              <Button type="button" disabled={isSubmitting || missingFields.length > 0 || needsNlpReview} onClick={handleRunDecisionSupport}>
                {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : null}
                Run ESI Decision Support
              </Button>
            )}
          </div>
        </section>

        <aside className="flex min-h-[240px] flex-col overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white/95 shadow-soft backdrop-blur 2xl:sticky 2xl:top-6 2xl:self-start">
          <div className="shrink-0 border-b border-slate-100 p-3">
            <h2 className="text-lg font-black text-slate-950">Live intake summary</h2>
            <p className="mt-1 text-sm text-slate-600">Patient context, vitals, and workflow status.</p>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-2.5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                <UserRound size={18} />
              </div>
              <div className="min-w-0">
                <p className="truncate font-bold text-slate-950">{displayValue(patient.name)}</p>
                <p className="truncate text-sm text-slate-500">Age {patient.age} • {patient.sex} • {patient.arrivalMode}</p>
              </div>
            </div>
            <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 p-2.5">
              <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Complaint</p>
              <p className="mt-2 text-sm font-semibold text-slate-800">{displayValue(chiefComplaint)}</p>
              <p className="mt-1 text-xs font-semibold text-slate-500">Duration: {displayValue(duration)}</p>
            </div>
            <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 p-2.5">
              <p className="mb-2 text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Vitals summary</p>
              <VitalsGrid vitals={vitals} age={patient.age} compact />
            </div>
            <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 p-2.5">
              <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Workflow status</p>
              <p className="mt-2 text-sm font-semibold text-slate-800">
                {needsNlpReview ? 'NLP review required' : missingFields.length ? 'Step needs attention' : 'Ready for prediction'}
              </p>
              <p className="mt-1 text-sm text-slate-600">Decision support only. Clinician review remains required.</p>
            </div>
            {missingFields.length ? (
              <div className="mt-2 rounded-2xl border border-amber-200 bg-amber-50 p-2.5 text-sm text-amber-800">
                <div className="flex gap-2 font-bold"><AlertTriangle size={18} /> Step needs attention</div>
                <p className="mt-1">{missingFields.join(', ')}</p>
              </div>
            ) : (
              <div className="mt-2 rounded-2xl border border-emerald-200 bg-emerald-50 p-2.5 text-sm text-emerald-800">
                <div className="flex gap-2 font-bold"><CheckCircle2 size={18} /> Ready for prediction</div>
                <p className="mt-1">The backend will return model output, latency, safety gate, and audit metadata.</p>
              </div>
            )}
          </div>
        </aside>
      </form>
    </div>
  );
}
