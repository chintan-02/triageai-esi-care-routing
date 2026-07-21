import { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, BrainCircuit, ChevronDown, FileSearch, FileText, ShieldAlert, UserCheck } from 'lucide-react';
import { getAssessmentAudit, listAssessments } from '@/api/assessments';
import type { AssessmentAuditEvent, AssessmentListItem } from '@/types/api';
import type { EsiLevel } from '@/types/clinical';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { SkeletonTableRows } from '@/components/ui/Skeleton';
import { ClinicalNlpAuditEvidenceCard } from '@/components/clinical-nlp/ClinicalNlpAuditEvidenceCard';
import { formatDateTime, formatPercent } from '@/lib/formatters';

type AuditSeverity = 'info' | 'warning' | 'critical';
type AuditCategory = 'prediction' | 'nlp' | 'clinician' | 'safety' | 'report' | 'other';
type AuditMetadata = { label: string; value: string };

type ExtendedEvent = {
  id: string;
  assessmentId: string;
  patient: string;
  mrn: string;
  actor: string;
  action: string;
  details: string;
  timestamp: string;
  severity: AuditSeverity;
  category: AuditCategory;
  categories: AuditCategory[];
  eventType: string;
  status: string;
  summaryMetadata: AuditMetadata[];
  detailMetadata: AuditMetadata[];
  rawEvent?: AssessmentAuditEvent;
};

const RECENT_AUDIT_ASSESSMENT_LIMIT = 25;

const severityFilters: Array<{ value: AuditSeverity | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'info', label: 'Info' },
  { value: 'warning', label: 'Warning' },
  { value: 'critical', label: 'Critical' }
];

const categoryFilters: Array<{ value: AuditCategory | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'prediction', label: 'Prediction' },
  { value: 'nlp', label: 'NLP Review' },
  { value: 'clinician', label: 'Clinician Review' },
  { value: 'safety', label: 'Safety' },
  { value: 'report', label: 'Report' }
];

const severityTone: Record<AuditSeverity, string> = {
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  critical: 'border-red-200 bg-red-50 text-red-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800'
};

const eventTypeTone: Record<AuditCategory, string> = {
  prediction: 'border-violet-200 bg-violet-50 text-violet-800',
  nlp: 'border-cyan-200 bg-cyan-50 text-cyan-800',
  clinician: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  safety: 'border-rose-200 bg-rose-50 text-rose-800',
  report: 'border-indigo-200 bg-indigo-50 text-indigo-800',
  other: 'border-slate-200 bg-slate-50 text-slate-700'
};

function textOrFallback(value: unknown, fallback: string): string {
  return typeof value === 'string' && value.trim() ? value : fallback;
}

function isEsiLevel(value: unknown): value is EsiLevel {
  return typeof value === 'number' && [1, 2, 3, 4, 5].includes(value);
}

function shortAssessmentId(id: string): string {
  if (id.length <= 12) return id;
  const firstSegment = id.split('-')[0];
  return firstSegment.length >= 6 ? firstSegment : `${id.slice(0, 12)}…`;
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

function numericAuditValue(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() && Number.isFinite(Number(value))) return Number(value);
  return null;
}

function arrayCount(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

function extractedFieldCount(value: unknown): number {
  if (!isPlainRecord(value)) return 0;
  return Object.values(value).reduce<number>((count, item) => {
    if (isPlainRecord(item)) return count + extractedFieldCount(item);
    if (Array.isArray(item)) return count + (item.length ? 1 : 0);
    return count + (readableAuditValue(item) ? 1 : 0);
  }, 0);
}

function shortVisibleText(value: unknown, maxLength = 120): string | null {
  const text = readableAuditValue(value);
  return text && text.length <= maxLength ? text : null;
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

function auditActionTitle(action: string): string {
  if (action === 'assessment_created') return 'Assessment created';
  if (action === 'prediction_generated') return 'Prediction generated';
  if (action === 'nlp_extraction_reviewed') return 'Clinical NLP review completed';
  if (action === 'clinician_review_accept') return 'Clinician review accepted';
  if (action === 'clinician_review_override') return 'Clinician review overridden';
  if (action === 'clinician_review_needs_review') return 'Clinician marked needs review';
  if (action.toLowerCase().includes('report') || action.toLowerCase().includes('pdf')) return 'PDF report generated';
  return action.replace(/_/g, ' ');
}

function auditMessage(action: string, details: unknown, message?: string | null): string {
  const payload = auditPayload(details);
  if (action === 'assessment_created') return 'Assessment created and queued for clinician review.';
  if (action === 'nlp_extraction_reviewed') return 'Clinical NLP reviewed before prediction.';
  if (action === 'prediction_generated') {
    const predicted = readableAuditValue(payload.predicted_esi);
    const final = readableAuditValue(payload.final_esi ?? payload.model_final_esi);
    if (predicted && final) return `Model prediction generated. Predicted ESI ${predicted}, final ESI ${final}.`;
    return 'Model prediction generated.';
  }
  if (action === 'clinician_review_accept') return 'Clinician accepted final routing decision.';
  if (action === 'clinician_review_override') return 'Clinician overrode final routing decision.';
  if (action === 'clinician_review_needs_review') return 'Clinician marked assessment for additional clinician review.';
  if (action.toLowerCase().includes('report') || action.toLowerCase().includes('pdf')) return 'PDF decision-support report generated.';
  if (message?.trim()) return message;
  return 'Audit event recorded.';
}

function detailAuditMetadata(item: AssessmentListItem, event?: AssessmentAuditEvent): AuditMetadata[] {
  const payload = auditPayload(event?.details);
  const items: Array<AuditMetadata | null> = [
    auditMetadataItem(payload, ['latency_ms'], 'Latency (ms)'),
    auditMetadataItem(payload, ['final_source'], 'Final source'),
    auditMetadataItem(payload, ['threshold_profile'], 'Threshold profile'),
    auditMetadataItem(payload, ['model_version'], 'Model version'),
    auditMetadataItem(payload, ['report_status'], 'Report status'),
    auditMetadataItem(payload, ['include_audit'], 'Includes audit trail'),
    auditMetadataItem(payload, ['download_url'], 'Download path'),
    auditMetadataItem(payload, ['override_reason'], 'Override reason'),
    auditMetadataItem(payload, ['review_note', 'notes'], 'Review note')
  ];

  return items.filter((metadata): metadata is AuditMetadata => Boolean(metadata));
}

function auditCategories(action: string, payload: Record<string, unknown>): AuditCategory[] {
  const normalized = action.toLowerCase();
  const categories = new Set<AuditCategory>();
  if (normalized.includes('prediction')) categories.add('prediction');
  if (normalized.includes('nlp')) categories.add('nlp');
  if (normalized.includes('clinician_review')) categories.add('clinician');
  if (normalized.includes('report') || normalized.includes('pdf')) categories.add('report');

  const predicted = numericAuditValue(payload.predicted_esi);
  const final = numericAuditValue(payload.final_esi ?? payload.model_final_esi);
  const finalSource = readableAuditValue(payload.final_source)?.toLowerCase();
  if (
    normalized.includes('safety') ||
    normalized.includes('escalation') ||
    payload.safety_escalated === true ||
    finalSource?.includes('safety') ||
    (predicted !== null && final !== null && predicted !== final)
  ) {
    categories.add('safety');
  }

  if (categories.size === 0) categories.add('other');
  return [...categories];
}

function severityForEvent(action: string, categories: AuditCategory[]): AuditSeverity {
  const normalized = action.toLowerCase();
  if (normalized.includes('critical')) return 'critical';
  if (normalized.includes('override') || normalized.includes('escalation') || categories.includes('safety')) return 'warning';
  return 'info';
}

function eventTypeLabel(category: AuditCategory): string {
  if (category === 'nlp') return 'NLP Review';
  if (category === 'clinician') return 'Clinician Review';
  if (category === 'other') return 'Assessment';
  return category.charAt(0).toUpperCase() + category.slice(1);
}

function statusForEvent(action: string, categories: AuditCategory[]): string {
  if (action === 'nlp_extraction_reviewed') return 'Reviewed before prediction';
  if (action === 'clinician_review_accept') return 'Accepted';
  if (action === 'clinician_review_override') return 'Overridden';
  if (action === 'clinician_review_needs_review') return 'Needs review';
  if (action.includes('report') || action.includes('pdf')) return action.includes('regenerated') ? 'Regenerated' : 'Generated';
  if (action === 'prediction_generated') return categories.includes('safety') ? 'Safety escalated' : 'Model supported';
  return 'Recorded';
}

function summaryAuditMetadata(item: AssessmentListItem, event: AssessmentAuditEvent): AuditMetadata[] {
  const payload = auditPayload(event.details);

  if (event.action === 'nlp_extraction_reviewed') {
    return [
      { label: 'Safety cues', value: String(arrayCount(payload.safety_cues)) },
      { label: 'Missing fields', value: String(arrayCount(payload.missing_fields)) },
      { label: 'Extracted fields', value: String(extractedFieldCount(payload.extracted_fields)) },
      { label: 'Evidence snippets', value: String(arrayCount(payload.evidence)) }
    ];
  }

  if (event.action === 'prediction_generated') {
    const predicted = readableAuditValue(payload.predicted_esi) ?? (isEsiLevel(item.model_predicted_esi) ? String(item.model_predicted_esi) : '—');
    const final = readableAuditValue(payload.final_esi ?? payload.model_final_esi) ?? (isEsiLevel(item.final_esi) ? String(item.final_esi) : '—');
    const confidence = numericAuditValue(payload.confidence ?? payload.confidence_score ?? item.confidence_score);
    const categories = auditCategories(event.action, payload);
    return [
      { label: 'Model predicted', value: `ESI ${predicted}` },
      { label: 'Final routing', value: `ESI ${final}` },
      { label: 'Safety escalation', value: categories.includes('safety') ? 'Yes' : 'No' },
      ...(confidence === null ? [] : [{ label: 'Confidence', value: formatPercent(confidence) }])
    ];
  }

  if (event.action.startsWith('clinician_review_')) {
    const reviewer = readableAuditValue(payload.clinician_id ?? payload.reviewer);
    const final = readableAuditValue(payload.clinician_final_esi ?? payload.final_esi);
    const overrideReason = shortVisibleText(payload.override_reason);
    return [
      ...(reviewer ? [{ label: 'Reviewer', value: reviewer }] : []),
      ...(final ? [{ label: 'Final clinician ESI', value: `ESI ${final}` }] : []),
      ...(overrideReason ? [{ label: 'Override reason', value: overrideReason }] : [])
    ];
  }

  if (event.action.includes('report') || event.action.includes('pdf')) {
    const reportId = readableAuditValue(payload.report_id);
    const reportStatus = readableAuditValue(payload.report_status);
    return [
      ...(reportId ? [{ label: 'Report ID', value: reportId }] : []),
      ...(reportStatus ? [{ label: 'Status', value: reportStatus }] : [])
    ];
  }

  return [];
}

function mapBackendAuditEvent(item: AssessmentListItem, event: AssessmentAuditEvent): ExtendedEvent {
  const payload = auditPayload(event.details);
  const categories = auditCategories(event.action, payload);
  const category = categories[0];
  return {
    id: event.audit_id,
    assessmentId: item.assessment_id,
    patient: textOrFallback(item.patient_name, '—'),
    mrn: textOrFallback(item.mrn, '—'),
    actor: textOrFallback(event.actor ?? event.actor_id, 'Backend API'),
    action: auditActionTitle(event.action),
    details: auditMessage(event.action, event.details, event.message),
    timestamp: textOrFallback(event.timestamp ?? event.created_at, item.created_at ?? item.updated_at ?? new Date().toISOString()),
    severity: severityForEvent(event.action, categories),
    category,
    categories,
    eventType: eventTypeLabel(category),
    status: statusForEvent(event.action, categories),
    summaryMetadata: summaryAuditMetadata(item, event),
    detailMetadata: detailAuditMetadata(item, event),
    rawEvent: event,
  };
}

function hasReportAuditEvent(events: AssessmentAuditEvent[]): boolean {
  return events.some((event) => {
    const action = event.action.toLowerCase();
    return action.includes('report') || action.includes('pdf');
  });
}

function buildReportGeneratedEvent(item: AssessmentListItem): ExtendedEvent | null {
  if (!Array.isArray(item.report_ids) || item.report_ids.length === 0) return null;
  const reportId = item.report_ids[item.report_ids.length - 1];
  return {
    id: `${item.assessment_id}-report-generated`,
    assessmentId: item.assessment_id,
    patient: textOrFallback(item.patient_name, '—'),
    mrn: textOrFallback(item.mrn, '—'),
    actor: 'Backend API',
    action: 'PDF report generated',
    details: 'PDF decision-support report generated.',
    timestamp: item.updated_at ?? item.created_at ?? new Date().toISOString(),
    severity: 'info',
    category: 'report',
    categories: ['report'],
    eventType: 'Report',
    status: 'Generated',
    summaryMetadata: [{ label: 'Report ID', value: reportId }],
    detailMetadata: [],
  };
}

function recentAssessments(items: AssessmentListItem[]): AssessmentListItem[] {
  return [...items]
    .sort((a, b) => +new Date(b.created_at ?? b.updated_at ?? 0) - +new Date(a.created_at ?? a.updated_at ?? 0))
    .slice(0, RECENT_AUDIT_ASSESSMENT_LIMIT);
}

function EventIcon({ category }: { category: AuditCategory }) {
  if (category === 'prediction') return <BrainCircuit size={19} />;
  if (category === 'nlp') return <FileSearch size={19} />;
  if (category === 'clinician') return <UserCheck size={19} />;
  if (category === 'safety') return <ShieldAlert size={19} />;
  if (category === 'report') return <FileText size={19} />;
  return <Activity size={19} />;
}

function AuditTimelineEvent({ event }: { event: ExtendedEvent }) {
  const [isOpen, setIsOpen] = useState(false);
  const isNlpReview = event.rawEvent?.action === 'nlp_extraction_reviewed';
  const hasDetails = isNlpReview || event.detailMetadata.length > 0;
  const detailsId = `audit-details-${event.assessmentId}-${event.id}`.replace(/[^a-zA-Z0-9_-]/g, '-');

  return (
    <article className="relative rounded-3xl border border-slate-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-card sm:p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 gap-3.5">
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border ${eventTypeTone[event.category]}`}>
            <EventIcon category={event.category} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-display text-base font-black text-slate-950">{event.action}</h3>
              <Badge className={eventTypeTone[event.category]}>{event.eventType}</Badge>
              <Badge className={severityTone[event.severity]}>{event.severity}</Badge>
              <Badge className="border-slate-200 bg-slate-50 text-slate-700">{event.status}</Badge>
            </div>
            <p className="mt-1.5 text-sm leading-6 text-slate-600">{event.details}</p>
            <p className="font-data mt-2 text-xs font-semibold text-slate-500">
              {event.patient} <span aria-hidden="true">•</span> MRN {event.mrn} <span aria-hidden="true">•</span>{' '}
              <span title={event.assessmentId}>Assessment {shortAssessmentId(event.assessmentId)}</span>
            </p>
          </div>
        </div>

        <div className="shrink-0 border-t border-slate-100 pt-3 text-left lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0 lg:text-right">
          <p className="text-xs font-bold text-slate-600">{formatDateTime(event.timestamp)}</p>
          <p className="mt-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">Source</p>
          <p className="max-w-[240px] truncate text-xs font-semibold text-slate-500" title={event.actor}>{event.actor}</p>
        </div>
      </div>

      {event.summaryMetadata.length ? (
        <dl className="mt-4 grid gap-2 border-t border-slate-100 pt-4 sm:grid-cols-2 lg:grid-cols-4">
          {event.summaryMetadata.map((item) => (
            <div key={`${event.id}-summary-${item.label}`} className="min-w-0 rounded-2xl bg-slate-50 px-3 py-2.5">
              <dt className="text-[10px] font-black uppercase tracking-wide text-slate-400">{item.label}</dt>
              <dd className="mt-1 text-sm font-bold text-slate-800 [overflow-wrap:anywhere]">{item.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}

      {isNlpReview ? (
        <p className="mt-3 text-xs font-semibold leading-5 text-slate-500">
          Decision-support audit context only. Clinician review remains required.
        </p>
      ) : null}

      {hasDetails ? (
        <div className="mt-4 border-t border-slate-100 pt-3">
          <button
            type="button"
            aria-controls={detailsId}
            aria-expanded={isOpen}
            className="focus-ring inline-flex items-center gap-2 rounded-xl px-2 py-1.5 text-sm font-black text-clinical-blue hover:bg-blue-50"
            onClick={() => setIsOpen((open) => !open)}
          >
            {isOpen ? 'Hide details' : 'View details'}
            <ChevronDown className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} size={16} />
          </button>
          {isOpen ? (
            <div id={detailsId} className="mt-3 space-y-3">
              {event.detailMetadata.length ? (
                <dl className="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50/70 p-3 sm:grid-cols-2 lg:grid-cols-3">
                  {event.detailMetadata.map((item) => (
                    <div key={`${event.id}-detail-${item.label}`} className="min-w-0 rounded-xl bg-white px-3 py-2.5">
                      <dt className="text-[10px] font-black uppercase tracking-wide text-slate-400">{item.label}</dt>
                      <dd className="mt-1 text-xs font-semibold leading-5 text-slate-700 [overflow-wrap:anywhere]">{item.value}</dd>
                    </div>
                  ))}
                </dl>
              ) : null}
              {isNlpReview && event.rawEvent ? <ClinicalNlpAuditEvidenceCard event={event.rawEvent} /> : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

export function AuditPage() {
  const [category, setCategory] = useState<AuditCategory | 'all'>('all');
  const [severity, setSeverity] = useState<AuditSeverity | 'all'>('all');
  const [auditEvents, setAuditEvents] = useState<ExtendedEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const assessments = recentAssessments(await listAssessments());
      const auditResponses = await Promise.all(
        assessments.map(async (assessment) => {
          const response = await getAssessmentAudit(assessment.assessment_id);
          return { assessment, events: response.events };
        }),
      );

      const loadedEvents = auditResponses.flatMap(({ assessment, events }) => {
        const mapped = events.map((event) => mapBackendAuditEvent(assessment, event));
        const reportGenerated = hasReportAuditEvent(events) ? null : buildReportGeneratedEvent(assessment);
        return reportGenerated ? [...mapped, reportGenerated] : mapped;
      });

      setAuditEvents(loadedEvents);
    } catch {
      setAuditEvents([]);
      setLoadError('Audit events could not be loaded right now. Please retry.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const events = useMemo<ExtendedEvent[]>(
    () =>
      auditEvents
        .filter((event) => category === 'all' || event.categories.includes(category))
        .filter((event) => severity === 'all' || event.severity === severity)
        .sort((a, b) => +new Date(b.timestamp) - +new Date(a.timestamp)),
    [auditEvents, category, severity]
  );

  return (
    <div>
      <PageHeader
        eyebrow="Audit and governance"
        title="Decision Traceability"
        description="Backend audit trail for decision-support predictions, ESI care routing, clinician review actions, and report generation readiness. Decision support only; not a substitute for clinician judgment."
      />

      <Card>
        <CardHeader title="Audit events" description="Scan the complete decision-support history, then expand supporting evidence only when needed." />
        <div className="space-y-3 border-b border-slate-100 px-5 py-4">
          <div aria-label="Event type filters" className="flex flex-wrap items-center gap-2" role="group">
            <span className="mr-1 text-xs font-black uppercase tracking-wide text-slate-500">Event type</span>
            {categoryFilters.map((filter) => (
              <button
                key={filter.value}
                type="button"
                aria-pressed={category === filter.value}
                onClick={() => setCategory(filter.value)}
                className={`rounded-full border px-3 py-1.5 text-xs font-bold transition ${
                  category === filter.value ? 'border-clinical-navy bg-clinical-navy text-white' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
          <div aria-label="Severity filters" className="flex flex-wrap items-center gap-2" role="group">
            <span className="mr-1 text-xs font-black uppercase tracking-wide text-slate-500">Severity</span>
            {severityFilters.map((filter) => (
              <button
                key={filter.value}
                type="button"
                aria-pressed={severity === filter.value}
                onClick={() => setSeverity(filter.value)}
                className={`rounded-full border px-3 py-1.5 text-xs font-bold transition ${
                  severity === filter.value ? 'border-slate-700 bg-slate-700 text-white' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
        {loadError ? (
          <div className="border-b border-red-100 bg-red-50 px-5 py-4 text-sm text-red-800">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <span><strong>Could not load audit events.</strong> {loadError}</span>
              <Button variant="danger" onClick={() => void refresh()} className="px-3 py-2">Retry</Button>
            </div>
          </div>
        ) : null}
        <CardBody>
          {isLoading ? (
            <SkeletonTableRows rows={6} cols={4} />
          ) : loadError ? (
            <p className="p-2 text-sm font-semibold text-slate-500">The audit timeline is temporarily unavailable.</p>
          ) : events.length === 0 ? (
            <p className="p-2 text-sm text-slate-500">No audit events match this filter.</p>
          ) : (
            <div className="relative space-y-3 before:absolute before:bottom-5 before:left-5 before:top-5 before:w-px before:bg-slate-200 sm:before:left-6">
              {events.map((event) => <AuditTimelineEvent key={`${event.assessmentId}-${event.id}`} event={event} />)}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
