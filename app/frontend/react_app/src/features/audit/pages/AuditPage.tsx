import { useMemo, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { useAssessmentsStore } from '@/context/AssessmentsContext';
import type { AuditEvent } from '@/types/clinical';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SkeletonTableRows } from '@/components/ui/Skeleton';
import { formatDateTime } from '@/lib/formatters';

type ExtendedEvent = AuditEvent & { assessmentId: string; patient: string };

const severityFilters: Array<{ value: AuditEvent['severity'] | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'info', label: 'Info' },
  { value: 'warning', label: 'Warning' },
  { value: 'critical', label: 'Critical' }
];

const severityTone: Record<AuditEvent['severity'], string> = {
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  critical: 'border-red-200 bg-red-50 text-red-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800'
};

export function AuditPage() {
  const { records, isLoading } = useAssessmentsStore();
  const [severity, setSeverity] = useState<AuditEvent['severity'] | 'all'>('all');

  const events = useMemo<ExtendedEvent[]>(
    () =>
      records
        .flatMap((record) => record.auditTrail.map((event) => ({ ...event, assessmentId: record.id, patient: record.intake.patient.name })))
        .filter((event) => severity === 'all' || event.severity === severity)
        .sort((a, b) => +new Date(b.timestamp) - +new Date(a.timestamp)),
    [records, severity]
  );

  return (
    <div>
      <PageHeader
        eyebrow="Audit and governance"
        title="Decision Traceability"
        description="Audit trail for predictions, safety-rule escalations, clinician accept/override actions, and report generation readiness."
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
                        <p className="font-data mt-1 text-xs font-semibold text-slate-500">
                          {event.patient} • {event.assessmentId}
                        </p>
                      </div>
                    </div>
                    <div className="text-left lg:text-right">
                      <Badge className={severityTone[event.severity]}>{event.severity}</Badge>
                      <p className="mt-2 text-xs font-semibold text-slate-500">{formatDateTime(event.timestamp)}</p>
                      <p className="text-xs text-slate-400">{event.actor}</p>
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
