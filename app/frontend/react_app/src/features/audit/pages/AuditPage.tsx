import { useCallback, useEffect, useMemo, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { getAssessmentAudit, listAssessments } from '@/api/assessments';
import type { AssessmentAuditEvent, AssessmentListItem } from '@/types/api';
import type { EsiLevel } from '@/types/clinical';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { SkeletonTableRows } from '@/components/ui/Skeleton';
import { formatDateTime } from '@/lib/formatters';

type AuditSeverity = 'info' | 'warning' | 'critical';

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
  metadata: Array<{ label: string; value: string }>;
};

const RECENT_AUDIT_ASSESSMENT_LIMIT = 25;

const severityFilters: Array<{ value: AuditSeverity | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'info', label: 'Info' },
  { value: 'warning', label: 'Warning' },
  { value: 'critical', label: 'Critical' }
];

const severityTone: Record<AuditSeverity, string> = {
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  critical: 'border-red-200 bg-red-50 text-red-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800'
};

function textOrFallback(value: unknown, fallback: string): string {
  return typeof value === 'string' && value.trim() ? value : fallback;
}

function isEsiLevel(value: unknown): value is EsiLevel {
  return typeof value === 'number' && [1, 2, 3, 4, 5].includes(value);
}

function shortAssessmentId(id: string): string {
  return id.split('-')[0] || id.slice(0, 8);
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

function auditActionTitle(action: string): string {
  if (action === 'assessment_created') return 'Assessment created';
  if (action === 'prediction_generated') return 'Prediction generated';
  if (action === 'clinician_review_accept') return 'Clinician review accepted';
  if (action === 'clinician_review_override') return 'Clinician review overridden';
  if (action === 'clinician_review_needs_review') return 'Clinician marked needs review';
  if (action.toLowerCase().includes('report') || action.toLowerCase().includes('pdf')) return 'PDF report generated';
  return action.replace(/_/g, ' ');
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
  if (action === 'clinician_review_needs_review') return 'Clinician marked assessment for additional clinician review.';
  if (action.toLowerCase().includes('report') || action.toLowerCase().includes('pdf')) return 'PDF report generated.';
  if (message?.trim()) return message;
  return 'Audit event recorded.';
}

function compactAuditMetadata(item: AssessmentListItem, event?: AssessmentAuditEvent): Array<{ label: string; value: string }> {
  const payload = auditPayload(event?.details);
  const items: Array<{ label: string; value: string } | null> = [
    { label: 'Assessment', value: shortAssessmentId(item.assessment_id) },
    { label: 'MRN', value: textOrFallback(item.mrn, 'N/A') },
  ];

  const predictedEsi = auditMetadataItem(payload, ['predicted_esi'], 'Predicted ESI');
  const finalEsi = auditMetadataItem(payload, ['final_esi', 'model_final_esi', 'clinician_final_esi'], 'Final ESI');
  items.push(
    predictedEsi ?? (isEsiLevel(item.model_predicted_esi) ? { label: 'Predicted ESI', value: String(item.model_predicted_esi) } : null),
    finalEsi ?? (isEsiLevel(item.final_esi) ? { label: 'Final ESI', value: String(item.final_esi) } : null),
  );

  if (event?.action.startsWith('clinician_review_')) {
    items.push(
      auditMetadataItem(payload, ['clinician_id', 'reviewer'], 'Reviewer'),
      auditMetadataItem(payload, ['override_reason'], 'Override reason'),
      auditMetadataItem(payload, ['review_note', 'notes'], 'Review note'),
    );
  }

  return items.filter((metadata): metadata is { label: string; value: string } => Boolean(metadata));
}

function severityForAction(action: string): AuditSeverity {
  const normalized = action.toLowerCase();
  if (normalized.includes('critical')) return 'critical';
  if (normalized.includes('override') || normalized.includes('escalation')) return 'warning';
  return 'info';
}

function mapBackendAuditEvent(item: AssessmentListItem, event: AssessmentAuditEvent): ExtendedEvent {
  return {
    id: event.audit_id,
    assessmentId: item.assessment_id,
    patient: textOrFallback(item.patient_name, 'Unknown patient'),
    mrn: textOrFallback(item.mrn, 'N/A'),
    actor: textOrFallback(event.actor ?? event.actor_id, 'Backend API'),
    action: auditActionTitle(event.action),
    details: auditMessage(event.action, event.details, event.message),
    timestamp: textOrFallback(event.timestamp ?? event.created_at, item.created_at ?? item.updated_at ?? new Date().toISOString()),
    severity: severityForAction(event.action),
    metadata: compactAuditMetadata(item, event),
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
  return {
    id: `${item.assessment_id}-report-generated`,
    assessmentId: item.assessment_id,
    patient: textOrFallback(item.patient_name, 'Unknown patient'),
    mrn: textOrFallback(item.mrn, 'N/A'),
    actor: 'Backend API',
    action: 'PDF report generated',
    details: 'PDF report generated.',
    timestamp: item.updated_at ?? item.created_at ?? new Date().toISOString(),
    severity: 'info',
    metadata: compactAuditMetadata(item),
  };
}

function recentAssessments(items: AssessmentListItem[]): AssessmentListItem[] {
  return [...items]
    .sort((a, b) => +new Date(b.created_at ?? b.updated_at ?? 0) - +new Date(a.created_at ?? a.updated_at ?? 0))
    .slice(0, RECENT_AUDIT_ASSESSMENT_LIMIT);
}

export function AuditPage() {
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
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Backend request failed.';
      setAuditEvents([]);
      setLoadError(`Unable to load real backend audit data from GET /assessments and GET /assessments/{assessment_id}/audit. ${message}`);
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
        .filter((event) => severity === 'all' || event.severity === severity)
        .sort((a, b) => +new Date(b.timestamp) - +new Date(a.timestamp)),
    [auditEvents, severity]
  );

  return (
    <div>
      <PageHeader
        eyebrow="Audit and governance"
        title="Decision Traceability"
        description="Backend audit trail for decision-support predictions, ESI care routing, clinician review actions, and report generation readiness. This is not diagnosis and does not replace clinician judgment."
      />

      <Card>
        <CardHeader title="Audit events" description="Every prediction, escalation, and clinician action is recorded here." />
        <div className="flex flex-wrap gap-2 border-b border-slate-100 px-5 py-4">
          {severityFilters.map((filter) => (
            <button
              key={filter.value}
              onClick={() => setSeverity(filter.value)}
              className={`rounded-full border px-3 py-1.5 text-xs font-bold transition ${
                severity === filter.value ? 'border-clinical-navy bg-clinical-navy text-white' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
              }`}
            >
              {filter.label}
            </button>
          ))}
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
          ) : events.length === 0 ? (
            <p className="p-2 text-sm text-slate-500">No audit events match this filter.</p>
          ) : (
            <div className="space-y-3">
              {events.map((event) => (
                <div key={`${event.assessmentId}-${event.id}`} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div className="flex gap-3">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                        <ShieldCheck size={20} />
                      </div>
                      <div>
                        <p className="font-bold text-slate-950">{event.action}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-600">{event.details}</p>
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
                        <p className="font-data mt-1 text-xs font-semibold text-slate-500">
                          {event.patient} • MRN {event.mrn} • <span title={event.assessmentId}>{shortAssessmentId(event.assessmentId)}</span>
                        </p>
                      </div>
                    </div>
                    <div className="text-left lg:text-right">
                      <Badge className={severityTone[event.severity]}>{event.severity}</Badge>
                      <p className="mt-2 text-xs font-semibold text-slate-500">{formatDateTime(event.timestamp)}</p>
                      <p className="max-w-[220px] truncate text-xs text-slate-400" title={event.actor}>{event.actor}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
