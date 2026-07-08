import { useMemo, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, CheckCircle2, ClipboardCheck, Loader2, UserRound } from 'lucide-react';
import { createPrediction } from '@/api/predictions';
import { useToast } from '@/context/ToastContext';
import { comorbidityOptions, riskFlagOptions } from '@/data/mockData';
import type { PatientProfile, Vitals } from '@/types/clinical';
import type { PatientIntakePayload } from '@/types/api';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { VitalsGrid } from '@/components/clinical/VitalsGrid';
import { VitalSliderPanel } from '@/components/clinical/VitalSliderPanel';
import { vitalFlag } from '@/lib/vitals';
import { getMissingIntakeFields } from '@/lib/intakeValidation';

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

const stepCardClass = 'flex flex-col rounded-[1.2rem] border border-slate-200 bg-white p-3 shadow-[0_10px_30px_-24px_rgba(15,23,42,0.35)]';
const fieldClass = 'space-y-1.5 text-sm font-semibold text-slate-700';

function displayValue(value: string, fallback = 'Not entered') {
  return value.trim() || fallback;
}

function toNullableText(value: string) {
  const trimmed = value.trim();
  return trimmed || null;
}

function buildPredictionPayload(
  patient: PatientProfile,
  chiefComplaint: string,
  symptomText: string,
  duration: string,
  vitals: Vitals
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
    additional_context: toNullableText(symptomText)
  };
}

export function NewAssessmentPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [patient, setPatient] = useState<PatientProfile>(() => createDefaultPatient());
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [symptomText, setSymptomText] = useState('');
  const [duration, setDuration] = useState('');
  const [vitals, setVitals] = useState<Vitals>(() => createDefaultVitals());
  const [riskFlags, setRiskFlags] = useState<string[]>([]);
  const [comorbidities, setComorbidities] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  const missingFields = useMemo(
    () => getMissingIntakeFields({ patient, chiefComplaint, symptomText, duration }),
    [patient, chiefComplaint, symptomText, duration]
  );

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
      review: missingFields
    }),
    [chiefComplaint, duration, missingFields, patient.name, symptomText]
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

  const handleRunDecisionSupport = async () => {
    if (missingFields.length || isSubmitting) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const payload = buildPredictionPayload(patient, chiefComplaint, symptomText, duration, vitals);
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

      <form onSubmit={preventImplicitSubmit} className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_300px]">
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
              <Button type="button" disabled={isSubmitting || missingFields.length > 0} onClick={handleRunDecisionSupport}>
                {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : null}
                Run ESI Decision Support
              </Button>
            )}
          </div>
        </section>

        <aside className="flex min-h-[240px] flex-col overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white/95 shadow-soft backdrop-blur xl:sticky xl:top-6 xl:self-start">
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
              <p className="mb-2 text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Selected risk flags</p>
              <div className="flex flex-wrap gap-2">
                {riskFlags.length ? riskFlags.map((flag) => <Badge key={flag} className="border-red-200 bg-red-50 text-red-800">{flag}</Badge>) : <span className="text-sm text-slate-500">None selected</span>}
              </div>
            </div>
            <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 p-2.5">
              <p className="mb-2 text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Comorbidities</p>
              <div className="flex flex-wrap gap-2">
                {comorbidities.length ? comorbidities.map((item) => <Badge key={item} className="border-blue-200 bg-blue-50 text-blue-800">{item}</Badge>) : <span className="text-sm text-slate-500">None selected</span>}
              </div>
            </div>
            <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 p-2.5">
              <p className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Workflow status</p>
              <p className="mt-2 text-sm font-semibold text-slate-800">{missingFields.length ? 'Step needs attention' : 'Ready for prediction'}</p>
              <p className="mt-1 text-sm text-slate-600">ESI decision-support workflow.</p>
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
