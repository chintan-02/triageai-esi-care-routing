import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertTriangle, ArrowRight, CheckCircle2, Download, RotateCcw, ShieldAlert } from 'lucide-react';
import { downloadAssessmentPdf, getAssessment } from '@/api/assessments';
import { submitClinicianReview } from '@/api/reviews';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import type { AssessmentDetail } from '@/types/api';
import type { AssessmentRecord, AuditEvent, ClinicianReview, EsiLevel, PatientProfile, ReviewStatus, RiskSeverity, RuleHit, Vitals } from '@/types/clinical';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { AcuityGauge } from '@/components/clinical/AcuityGauge';
import { EsiBadge } from '@/components/clinical/EsiBadge';
import { LatencyBadge } from '@/components/clinical/LatencyBadge';
import { ProbabilityBars } from '@/components/clinical/ProbabilityBars';
import { ReviewStatusBadge } from '@/components/clinical/ReviewStatusBadge';
import { RiskRuleList } from '@/components/clinical/RiskRuleList';
import { VitalsGrid } from '@/components/clinical/VitalsGrid';
import { formatDateTime, formatPercent } from '@/lib/formatters';
import { hasPermission } from '@/lib/permissions';

function FinalDecisionBanner({ predicted, final, confidence, latency, status, rules }: { predicted: EsiLevel; final: EsiLevel; confidence: number; latency: number; status: ClinicianReview['status']; rules: RuleHit[] }) {
  const escalated = final < predicted;
  const ruleSummary = rules.map((rule) => rule.label).join(' + ');
  const safetyStatus = escalated ? 'Escalated by safety rules' : rules.length ? 'Safety rules confirmed routing' : 'No safety-rule escalation triggered';
  const decisionStatus = escalated ? 'Escalated by safety rules' : 'Model decision confirmed';

  return (
    <Card className={escalated ? 'border-red-200 bg-red-50' : 'border-emerald-200 bg-emerald-50'}>
      <CardBody className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Final routing decision</p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <EsiBadge level={final} prefix="Final" />
            <h2 className="font-display text-3xl font-black text-slate-950">ESI {final}</h2>
            <span className={`rounded-full border px-3 py-1 text-xs font-black uppercase tracking-wide ${escalated ? 'border-red-200 bg-white text-red-800' : 'border-emerald-200 bg-white text-emerald-800'}`}>
              {decisionStatus}
            </span>
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">
            Model predicted ESI {predicted}. {ruleSummary || safetyStatus}. Clinician review status: {status}.
          </p>
        </div>
        <div className="grid w-full gap-2 sm:grid-cols-2 lg:w-auto lg:min-w-[520px] lg:grid-cols-4">
          <div className="rounded-2xl border border-white/70 bg-white p-3 text-center">
            <p className="text-xs font-bold uppercase text-slate-500">Model</p>
            <p className="font-data mt-1 text-lg font-black text-slate-950">ESI {predicted}</p>
          </div>
          <div className="rounded-2xl border border-white/70 bg-white p-3 text-center">
            <p className="text-xs font-bold uppercase text-slate-500">Confidence</p>
            <p className="font-data mt-1 text-lg font-black text-slate-950">{formatPercent(confidence)}</p>
          </div>
          <div className="rounded-2xl border border-white/70 bg-white p-3 text-center">
            <p className="text-xs font-bold uppercase text-slate-500">Latency</p>
            <p className="font-data mt-1 text-lg font-black text-slate-950">{latency} ms</p>
          </div>
          <div className="rounded-2xl border border-white/70 bg-white p-3 text-center">
            <p className="text-xs font-bold uppercase text-slate-500">Review</p>
            <p className="mt-1 text-sm font-black capitalize text-slate-950">{status}</p>
          </div>
          <div className="rounded-2xl border border-white/70 bg-white p-3 text-center sm:col-span-2 lg:col-span-4">
            <p className="text-xs font-bold uppercase text-slate-500">Safety gate</p>
            <p className="mt-1 text-sm font-black text-slate-950">{safetyStatus}</p>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function DecisionComparison({ predicted, final, rules }: { predicted: EsiLevel; final: EsiLevel; rules: RuleHit[] }) {
  const ruleSummary = rules.length ? rules.map((rule) => rule.label).join(' + ') : 'No safety-rule escalation triggered';
  return (
    <Card>
      <CardHeader title="Why the final ESI changed" description="Safety-rule escalation is shown for routing transparency and clinician review." />
      <CardBody>
        <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr_auto_1fr] md:items-center">
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-black uppercase tracking-wide text-slate-500">Model prediction</p>
            <div className="mt-3"><EsiBadge level={predicted} prefix="Pred" /></div>
          </div>
          <ArrowRight className="hidden text-slate-300 md:block" />
          <div className={`rounded-3xl border p-4 ${rules.length ? 'border-red-200 bg-red-50' : 'border-slate-200 bg-white'}`}>
            <p className="text-xs font-black uppercase tracking-wide text-slate-500">Safety gate result</p>
            <p className="mt-3 text-sm font-bold leading-6 text-slate-800">{ruleSummary}</p>
          </div>
          <ArrowRight className="hidden text-slate-300 md:block" />
          <div className="rounded-3xl border border-slate-200 bg-slate-950 p-4 text-white">
            <p className="text-xs font-black uppercase tracking-wide text-slate-300">Final decision</p>
            <p className="font-data mt-3 text-2xl font-black">ESI {final}</p>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function pendingNote(note: string) {
  return note.trim().toLowerCase().startsWith('awaiting clinician review');
}

function shortAssessmentId(id: string): string {
  return id.split('-')[0] || id.slice(0, 8);
}

function isEsiLevel(value: unknown): value is EsiLevel {
  return typeof value === 'number' && [1, 2, 3, 4, 5].includes(value);
}

function esiLevelOrFallback(value: unknown, fallback: EsiLevel): EsiLevel {
  return isEsiLevel(value) ? value : fallback;
}

function numberOrZero(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function textOrFallback(value: unknown, fallback: string): string {
  return typeof value === 'string' && value.trim() ? value : fallback;
}

function normalizeSex(value: unknown): PatientProfile['sex'] {
  const normalized = typeof value === 'string' ? value.trim().toLowerCase() : '';
  if (normalized === 'female') return 'Female';
  if (normalized === 'male') return 'Male';
  if (normalized === 'other') return 'Other';
  return 'Unknown';
}

function normalizeArrivalMode(value: unknown): PatientProfile['arrivalMode'] {
  if (value === 'Walk-in' || value === 'Ambulance' || value === 'Referral' || value === 'Other') return value;
  return 'Other';
}

function normalizeReviewStatus(value: unknown): ReviewStatus {
  if (value === 'accepted' || value === 'overridden') return value;
  return 'pending';
}

function normalizeReviewerRole(value: unknown): ClinicianReview['role'] {
  if (value === 'Nurse' || value === 'Doctor' || value === 'Admin' || value === 'Demo Clinician') return value;
  return 'Nurse';
}

function normalizeProbabilities(probabilities: Record<string, number> | undefined): Record<string, number> {
  if (!probabilities) return {};
  return Object.fromEntries(
    Object.entries(probabilities).map(([key, value]) => [key.replace('_', ' '), value])
  );
}

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function auditPayload(details: unknown): Record<string, unknown> {
  if (!isPlainRecord(details)) return {};
  const payload = details.payload;
  return isPlainRecord(payload) ? { ...details, ...payload } : details;
}

function readableAuditValue(value: unknown): string | null {
  if (value === null || value === undefined || value === '') return null;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (typeof value === 'string') return value.replace(/_/g, ' ');
  return null;
}

function auditMetadataItem(
  details: Record<string, unknown>,
  keys: string[],
  label: string,
): { label: string; value: string } | null {
  for (const key of keys) {
    const value = readableAuditValue(details[key]);
    if (value) return { label, value };
  }
  return null;
}

function compactAuditMetadata(action: string, details: unknown): Array<{ label: string; value: string }> {
  const payload = auditPayload(details);
  const items: Array<{ label: string; value: string } | null> = [];

  if (action === 'prediction_generated') {
    items.push(
      auditMetadataItem(payload, ['predicted_esi'], 'Predicted ESI'),
      auditMetadataItem(payload, ['final_esi', 'model_final_esi'], 'Final ESI'),
    );
  }

  if (action.startsWith('clinician_review_')) {
    items.push(
      auditMetadataItem(payload, ['clinician_final_esi', 'final_esi'], 'Final ESI'),
      auditMetadataItem(payload, ['clinician_id', 'reviewer'], 'Reviewer'),
      auditMetadataItem(payload, ['override_reason'], 'Override reason'),
      auditMetadataItem(payload, ['review_note', 'notes'], 'Review note'),
    );
  }

  return items.filter((item): item is { label: string; value: string } => Boolean(item));
}

function auditActionTitle(action: string): string {
  switch (action) {
    case 'assessment_created':
      return 'Assessment created';
    case 'prediction_generated':
      return 'Prediction generated';
    case 'clinician_review_accept':
      return 'Clinician review accepted';
    case 'clinician_review_override':
      return 'Clinician review overridden';
    case 'clinician_review_needs_review':
      return 'Clinician marked needs review';
    default:
      return action.replace(/_/g, ' ');
  }
}

function auditMessage(action: string, details: unknown, message?: string | null): string {
  const payload = auditPayload(details);
  if (action === 'assessment_created') return 'Assessment created and queued for clinician review.';
  if (action === 'prediction_generated') {
    const predicted = readableAuditValue(payload.predicted_esi);
    const final = readableAuditValue(payload.final_esi ?? payload.model_final_esi);
    if (predicted && final) return `Model prediction generated. Predicted ESI ${predicted}, final ESI ${final}.`;
    return 'Model prediction generated.';
  }
  if (action === 'clinician_review_accept') return 'Clinician accepted final routing decision.';
  if (action === 'clinician_review_override') return 'Clinician overrode final routing decision.';
  if (action === 'clinician_review_needs_review') return 'Clinician marked assessment for additional review.';
  if (message?.trim()) return message;
  if (typeof details === 'string' && details.trim()) return details;
  return 'Audit event recorded.';
}

function severityFromRule(rule: Record<string, unknown>, safetyEscalated: boolean): RiskSeverity {
  const severity = rule.severity;
  if (severity === 'low' || severity === 'moderate' || severity === 'high' || severity === 'critical') return severity;
  return safetyEscalated ? 'high' : 'moderate';
}

function mapRuleHits(detail: AssessmentDetail): RuleHit[] {
  const rules = detail.latest_prediction?.safety_rules_triggered ?? [];
  return rules
    .filter((rule) => rule.triggered !== false)
    .map((rule, index) => {
      const ruleId = textOrFallback(rule.rule_id, `safety_rule_${index + 1}`);
      const message = textOrFallback(rule.message, 'Safety rule triggered by backend decision-support.');
      const escalatesTo = esiLevelOrFallback(rule.escalates_to, detail.final_esi ?? 3);
      return {
        id: ruleId,
        label: message,
        description: message,
        severity: severityFromRule(rule, detail.safety_escalated),
        escalatesTo: detail.safety_escalated ? escalatesTo : undefined
      };
    });
}

function mapAuditTrail(detail: AssessmentDetail): AuditEvent[] {
  return detail.audit_trail.map((event) => ({
    id: event.audit_id,
    timestamp: textOrFallback(event.timestamp ?? event.created_at, detail.created_at ?? new Date().toISOString()),
    actor: textOrFallback(event.actor ?? event.actor_id, 'Backend API'),
    action: auditActionTitle(event.action),
    details: auditMessage(event.action, event.details, event.message),
    metadata: compactAuditMetadata(event.action, event.details),
    severity: event.action.toLowerCase().includes('override') ? 'warning' : 'info'
  }));
}

function modelFamilyFromVersion(version: string): string {
  return version.toLowerCase().includes('lightgbm') ? 'LightGBM' : 'Backend model';
}

function mapBackendAssessment(detail: AssessmentDetail): AssessmentRecord {
  const latestPrediction = detail.latest_prediction;
  const latestReview = detail.latest_clinician_review;
  const predictedEsi = esiLevelOrFallback(latestPrediction?.predicted_esi ?? detail.model_predicted_esi, 3);
  const finalEsi = esiLevelOrFallback(latestPrediction?.final_esi ?? detail.final_esi, predictedEsi);
  const age = numberOrZero(detail.age ?? detail.intake?.patient_age);
  const modelVersion = textOrFallback(latestPrediction?.model_version ?? detail.model_version, 'Backend model version unavailable');

  return {
    id: detail.assessment_id,
    intake: {
      patient: {
        id: textOrFallback(detail.patient_id, detail.assessment_id),
        mrn: textOrFallback(detail.mrn, 'N/A'),
        name: textOrFallback(detail.patient_name, 'Unknown patient'),
        age,
        sex: normalizeSex(detail.sex ?? detail.intake?.sex),
        arrivalMode: normalizeArrivalMode(detail.arrival_mode ?? detail.intake?.arrival_mode)
      },
      chiefComplaint: textOrFallback(detail.chief_complaint ?? detail.intake?.chief_complaint, 'Chief complaint unavailable'),
      symptomText: textOrFallback(detail.symptom_narrative ?? detail.additional_context ?? detail.intake?.additional_context, 'No symptom narrative entered.'),
      duration: textOrFallback(detail.symptom_duration ?? detail.intake?.symptom_duration, 'Not entered'),
      vitals: {
        heartRate: numberOrZero(detail.heart_rate ?? detail.intake?.heart_rate),
        respiratoryRate: numberOrZero(detail.respiratory_rate ?? detail.intake?.respiratory_rate),
        systolicBp: numberOrZero(detail.systolic_bp ?? detail.intake?.systolic_bp),
        diastolicBp: numberOrZero(detail.diastolic_bp ?? detail.intake?.diastolic_bp),
        temperatureC: numberOrZero(detail.temperature_c ?? detail.intake?.temperature_c),
        spo2: numberOrZero(detail.oxygen_saturation ?? detail.intake?.oxygen_saturation),
        painScore: numberOrZero(detail.pain_score ?? detail.intake?.pain_score)
      } satisfies Vitals,
      riskFlags: detail.risk_flags,
      comorbidities: detail.comorbidities
    },
    prediction: {
      requestId: textOrFallback(detail.request_id_value ?? detail.request_id, detail.assessment_id),
      modelVersion,
      modelFamily: modelFamilyFromVersion(modelVersion),
      predictedEsi,
      finalEsi,
      confidence: numberOrZero(latestPrediction?.confidence_score ?? detail.confidence_score ?? detail.confidence),
      latencyMs: numberOrZero(detail.latency_ms),
      probabilities: normalizeProbabilities(latestPrediction?.probabilities ?? detail.probabilities),
      thresholdProfile: textOrFallback(latestPrediction?.final_source, 'Backend final decision'),
      ruleHits: mapRuleHits(detail),
      explanation: textOrFallback(latestPrediction?.explanation, detail.message),
      recommendation: textOrFallback(latestPrediction?.recommendation, 'Clinician review is required.'),
      createdAt: textOrFallback(latestPrediction?.created_at, detail.created_at ?? new Date().toISOString())
    },
    review: {
      status: normalizeReviewStatus(detail.review_status_normalized ?? detail.review_status ?? latestReview?.clinician_decision),
      reviewer: textOrFallback(detail.reviewer ?? latestReview?.clinician_id, 'Unassigned'),
      role: normalizeReviewerRole(detail.reviewer_role),
      finalDecision: esiLevelOrFallback(latestReview?.clinician_final_esi ?? detail.final_esi, finalEsi),
      note: textOrFallback(latestReview?.review_note ?? latestReview?.override_reason, 'Awaiting clinician review.'),
      reviewedAt: latestReview?.created_at ?? undefined
    },
    auditTrail: mapAuditTrail(detail)
  };
}

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function AssessmentDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const { showToast } = useToast();

  const [record, setRecord] = useState<AssessmentRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reviewNote, setReviewNote] = useState('');
  const [finalDecision, setFinalDecision] = useState<EsiLevel>(3);
  const [isSaving, setIsSaving] = useState(false);

  const canAccept = hasPermission(user?.role, 'review:accept');
  const canOverride = hasPermission(user?.role, 'review:override');
  const canDownloadReport = hasPermission(user?.role, 'report:generate');

  const loadAssessment = useCallback(async () => {
    if (!id) {
      setRecord(null);
      setLoadError('Missing assessment ID in the route.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      const detail = await getAssessment(id);
      setRecord(mapBackendAssessment(detail));
    } catch (error) {
      setRecord(null);
      setLoadError(error instanceof Error ? error.message : 'Unable to load this backend assessment.');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadAssessment();
  }, [loadAssessment]);

  useEffect(() => {
    if (!record) return;
    setReviewNote(record.review.note);
    setFinalDecision(record.review.finalDecision);
  }, [record]);

  const overrideLocked = useMemo(() => !canOverride, [canOverride]);

  if (isLoading) {
    return (
      <Card className="p-8 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
          <RotateCcw size={26} className="animate-spin" />
        </div>
        <h2 className="font-display mt-4 text-lg font-bold text-slate-950">Loading assessment</h2>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">Fetching the assessment from the FastAPI backend.</p>
      </Card>
    );
  }

  if (loadError) {
    return (
      <EmptyState
        title="Assessment unavailable"
        description={loadError}
        action={
          <div className="flex gap-3">
            <Button onClick={loadAssessment}>Try again</Button>
            <Link to="/assessments">
              <Button variant="secondary">Back to Assessments</Button>
            </Link>
          </div>
        }
      />
    );
  }

  if (!record) {
    return (
      <EmptyState
        title="Assessment not found"
        description="The selected assessment could not be loaded from the backend database."
        action={
          <Link to="/assessments">
            <Button>Back to Assessments</Button>
          </Link>
        }
      />
    );
  }

  const { intake, prediction, review } = record;
  const reviewerName = review.status === 'pending' && review.reviewer === 'Unassigned' ? 'Unassigned' : review.reviewer;
  const actingReviewer = user?.email ?? user?.name ?? 'Clinical User';
  const isNurseRole = user?.role === 'Nurse';
  const canEditFinalDecision = canOverride;
  const safetyFinalDecision = prediction.finalEsi;
  const currentDisplayedFinalDecision = review.status === 'overridden' && review.finalDecision !== safetyFinalDecision ? review.finalDecision : safetyFinalDecision;
  const displayedFinalDecision = canEditFinalDecision ? finalDecision : currentDisplayedFinalDecision;

  const saveReviewAction = async (status: ClinicianReview['status']) => {
    if (status === 'accepted' && !canAccept) {
      showToast({ tone: 'error', title: 'Permission required', description: 'Your role cannot accept clinical review decisions.' });
      return;
    }
    if (status === 'overridden' && !canOverride) {
      showToast({ tone: 'error', title: 'Doctor permission required', description: 'Only Doctor role can override the final ESI decision in this frontend policy.' });
      return;
    }

    setIsSaving(true);
    try {
      const requestedOverride = status === 'overridden';
      const selectedFinalDecision = requestedOverride ? finalDecision : safetyFinalDecision;
      const effectiveStatus: ClinicianReview['status'] = requestedOverride && selectedFinalDecision !== safetyFinalDecision ? 'overridden' : 'accepted';
      const overrideReason = reviewNote.trim();

      if (effectiveStatus === 'overridden' && (!overrideReason || pendingNote(overrideReason))) {
        showToast({ tone: 'error', title: 'Override reason required', description: 'Add a brief reason before changing the final ESI.' });
        return;
      }

      const savedFinalDecision = effectiveStatus === 'accepted' ? safetyFinalDecision : selectedFinalDecision;
      const note = effectiveStatus === 'accepted' ? 'Current final routing decision accepted.' : overrideReason;
      await submitClinicianReview({
        assessment_id: record.id,
        clinician_id: actingReviewer,
        action: effectiveStatus === 'overridden' ? 'override' : 'accept',
        final_esi: savedFinalDecision,
        override_reason: effectiveStatus === 'overridden' ? note : null,
        notes: note
      });
      await loadAssessment();
      showToast({
        tone: 'success',
        title: effectiveStatus === 'accepted' ? 'Decision accepted' : 'Decision overridden',
        description: `Final ESI ${savedFinalDecision} saved for ${record.id}.`
      });
    } catch {
      showToast({ tone: 'error', title: 'Could not save review', description: 'Please try again.' });
    } finally {
      setIsSaving(false);
    }
  };

  const downloadPdf = async () => {
    if (!canDownloadReport) {
      showToast({ tone: 'error', title: 'Permission required', description: 'Your role cannot generate clinical reports.' });
      return;
    }
    const blob = await downloadAssessmentPdf(record.id);
    saveBlob(blob, `${record.id}_triageai_report.pdf`);
    showToast({ tone: 'info', title: 'PDF generated', description: `${record.id}_triageai_report.pdf downloaded.` });
  };

  return (
    <div>
      <PageHeader
        eyebrow="Assessment detail"
        title={`${intake.patient.name} — ${shortAssessmentId(record.id)}`}
        description="Complete clinical decision-support view with patient intake, model probabilities, latency, safety-rule escalation, clinician review, audit trail, and PDF report generation."
        actions={
          <>
            <Button variant="secondary" onClick={downloadPdf} disabled={!canDownloadReport}>
              <Download size={17} /> Generate PDF
            </Button>
            <Link to="/assessments">
              <Button variant="ghost"><RotateCcw size={17} /> Back</Button>
            </Link>
          </>
        }
      />

      <div className="space-y-6">
        <FinalDecisionBanner predicted={prediction.predictedEsi} final={prediction.finalEsi} confidence={prediction.confidence} latency={prediction.latencyMs} status={review.status} rules={prediction.ruleHits} />
        {prediction.finalEsi !== prediction.predictedEsi ? <DecisionComparison predicted={prediction.predictedEsi} final={prediction.finalEsi} rules={prediction.ruleHits} /> : null}
      </div>

      <div className="mt-5 grid items-start gap-5 xl:grid-cols-[300px_minmax(0,1fr)_360px]">
        <Card className="self-start p-4">
          <p className="mb-2 text-center text-xs font-bold uppercase tracking-wide text-slate-500">Acuity routing</p>
          <AcuityGauge finalEsi={prediction.finalEsi} predictedEsi={prediction.predictedEsi} />
          <div className="mt-4 grid grid-cols-2 gap-2">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-2.5 text-center">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Confidence</p>
              <p className="font-data mt-1 text-xl font-bold text-slate-950">{formatPercent(prediction.confidence)}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-2.5 text-center">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Latency</p>
              <div className="mt-1.5 flex justify-center"><LatencyBadge ms={prediction.latencyMs} size="sm" /></div>
            </div>
          </div>
          <div className="mt-2 rounded-2xl border border-slate-200 bg-white p-2.5 text-center">
            <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Review status</p>
            <div className="mt-1.5 flex justify-center"><ReviewStatusBadge status={review.status} /></div>
          </div>
        </Card>

        <div className="min-w-0 space-y-5">
          <Card>
            <CardHeader title="Patient intake" description="Structured patient context used by the model and safety rules." />
            <CardBody className="space-y-4">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">MRN</p><p className="font-data mt-1 break-words font-bold text-slate-950">{intake.patient.mrn}</p></div>
                <div className="rounded-2xl bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Demographics</p><p className="mt-1 font-bold text-slate-950">{intake.patient.age} • {intake.patient.sex || 'Unknown'}</p></div>
                <div className="rounded-2xl bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Arrival</p><p className="mt-1 font-bold text-slate-950">{intake.patient.arrivalMode}</p></div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-3">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Chief complaint</p>
                <p className="mt-1.5 break-words font-bold text-slate-950">{intake.chiefComplaint}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{intake.symptomText}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-3">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Selected risk flags</p>
                <p className="mt-1.5 text-sm font-semibold leading-6 text-slate-700">{intake.riskFlags.length ? intake.riskFlags.join(', ') : 'None selected'}</p>
              </div>
              <VitalsGrid vitals={intake.vitals} age={intake.patient.age} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Model output" description="Notebook-aligned model output for review, audit, and routing transparency." />
            <CardBody className="grid min-w-0 gap-5 lg:grid-cols-2">
              <div><p className="mb-4 text-sm font-bold text-slate-700">Class probabilities</p><ProbabilityBars probabilities={prediction.probabilities} /></div>
              <div className="min-w-0 space-y-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Model family/version</p><p className="mt-1 font-bold text-slate-950">{prediction.modelFamily}</p><p className="font-data mt-1 text-sm text-slate-600 [overflow-wrap:anywhere]">{prediction.modelVersion}</p></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Threshold profile</p><p className="font-data mt-1 text-sm font-bold text-slate-950 [overflow-wrap:anywhere]">{prediction.thresholdProfile}</p></div>
                <div className="rounded-2xl border border-blue-100 bg-blue-50 p-3 text-sm font-semibold leading-6 text-blue-900">Raw model probabilities are shown for transparency; they are not calibrated probabilities.</div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Explanation</p><p className="mt-1 text-sm leading-6 text-slate-700">{prediction.explanation}</p></div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Audit trail" description="Traceability for prediction, escalation, and review events." />
            <CardBody className="pt-4">
              <div className="space-y-2.5">
                {record.auditTrail.map((event) => (
                  <div key={event.id} className="rounded-2xl border border-slate-200 bg-white p-3">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><p className="font-bold text-slate-950">{event.action}</p><p className="text-xs font-semibold text-slate-500">{formatDateTime(event.timestamp)}</p></div>
                    <p className="mt-1 text-sm text-slate-600">{event.details}</p>
                    {event.metadata?.length ? (
                      <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                        {event.metadata.map((item) => (
                          <div key={`${event.id}-${item.label}`} className="min-w-0 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
                            <dt className="text-[10px] font-black uppercase tracking-wide text-slate-400">{item.label}</dt>
                            <dd className="mt-0.5 text-xs font-semibold text-slate-700 [overflow-wrap:anywhere]">{item.value}</dd>
                          </div>
                        ))}
                      </dl>
                    ) : null}
                    <p className="mt-2 text-xs font-bold uppercase tracking-wide text-slate-400 [overflow-wrap:anywhere]">{event.actor}</p>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>

        <aside className="space-y-5 xl:sticky xl:top-28 xl:self-start">
          <Card><CardHeader title="Safety rules" description="Shows exactly why final ESI can differ from model output." /><CardBody><RiskRuleList rules={prediction.ruleHits} /></CardBody></Card>

          <Card>
            <CardHeader title="Clinician review" description="Human-in-the-loop accept or doctor override workflow." />
            <CardBody className="space-y-3.5">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Current reviewer</p>
                <p className="mt-1 font-bold text-slate-950">{reviewerName}</p>
                <p className="text-sm text-slate-500">{review.status === 'pending' ? 'Pending assignment' : review.role}</p>
                <p className="mt-2 text-xs font-semibold text-slate-500">Signed in: {actingReviewer} ({user?.role ?? 'Nurse'})</p>
              </div>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Final clinician decision
                <select value={displayedFinalDecision} onChange={(event) => setFinalDecision(Number(event.target.value) as EsiLevel)} disabled={!canEditFinalDecision} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 disabled:bg-slate-100 disabled:text-slate-500">
                  <option value={1}>ESI 1</option><option value={2}>ESI 2</option><option value={3}>ESI 3</option><option value={4}>ESI 4</option><option value={5}>ESI 5</option>
                </select>
                {isNurseRole ? <span className="block text-xs font-semibold leading-5 text-slate-500">Read-only for Nurse role. Accept confirms the current final routing decision.</span> : null}
              </label>
              {overrideLocked && isNurseRole ? <div className="rounded-2xl border border-amber-100 bg-amber-50/70 p-3 text-sm text-amber-800"><div className="font-bold">Override requires Doctor role</div><p className="mt-1">Nurse users can accept the current final routing decision. Doctor role is required to change the final ESI.</p></div> : null}
              <label className="space-y-2 text-sm font-semibold text-slate-700">Review note / override reason<textarea value={reviewNote} onChange={(event) => setReviewNote(event.target.value)} rows={4} className="focus-ring w-full rounded-2xl border border-slate-200 bg-white px-4 py-3" /></label>
              <div className="grid gap-3 sm:grid-cols-2">
                <Button type="button" disabled={isSaving || !canAccept} onClick={() => saveReviewAction('accepted')}><CheckCircle2 size={17} /> Accept</Button>
                <Button type="button" variant="secondary" disabled={isSaving || !canOverride} title={!canOverride ? 'Doctor role required to override final routing decision.' : undefined} onClick={() => saveReviewAction('overridden')}><ShieldAlert size={17} /> Override</Button>
              </div>
              {!canAccept && !canOverride ? <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600"><div className="flex gap-2 font-bold text-slate-800"><AlertTriangle size={16} /> Review unavailable</div><p className="mt-1">Your role can view this record but cannot save clinical review decisions.</p></div> : null}
              <Button type="button" variant="secondary" className="w-full" onClick={downloadPdf} disabled={!canDownloadReport}><Download size={17} /> Generate PDF Report</Button>
            </CardBody>
          </Card>
        </aside>
      </div>
    </div>
  );
}
