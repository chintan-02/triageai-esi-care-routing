import { useState } from 'react';
import { AlertTriangle, CheckCircle2, ChevronDown, FileSearch, ShieldAlert } from 'lucide-react';
import type { AssessmentAuditEvent } from '@/types/api';
import { Badge } from '@/components/ui/Badge';

type ClinicalNlpAuditEvidenceCardProps = {
  event: AssessmentAuditEvent;
  collapseEvidence?: boolean;
};

const evidenceFields = new Set([
  'age',
  'gender',
  'chief_complaint',
  'symptom',
  'symptoms',
  'triage_vital_hr',
  'triage_vital_sbp',
  'triage_vital_dbp',
  'triage_vital_rr',
  'triage_vital_o2',
  'triage_vital_temp'
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function detailsFor(event: AssessmentAuditEvent): Record<string, unknown> {
  if (!isRecord(event.details)) return {};
  const payload = event.details.payload;
  return isRecord(payload) ? { ...event.details, ...payload } : event.details;
}

function nonEmptyText(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

function displayValue(value: unknown): string | null {
  if (typeof value === 'string') return value.trim() || null;
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (Array.isArray(value)) {
    const values = value.map(displayValue).filter((item): item is string => Boolean(item));
    return values.length ? values.join(', ') : null;
  }
  return null;
}

function textList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map(nonEmptyText)
    .filter((item): item is string => Boolean(item));
}

function readableField(field: string): string {
  return field
    .replace(/^triage_vital_/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function extractedFieldItems(extractedFields: Record<string, unknown>) {
  const items = [
    { label: 'Age', value: displayValue(extractedFields.age) },
    { label: 'Gender', value: displayValue(extractedFields.gender) },
    { label: 'Chief complaint', value: displayValue(extractedFields.chief_complaint) },
    { label: 'Symptoms', value: displayValue(extractedFields.symptoms) }
  ];
  return items.filter((item): item is { label: string; value: string } => Boolean(item.value));
}

function vitalItems(value: unknown): Array<{ label: string; value: string }> {
  if (!isRecord(value)) return [];

  const systolic = displayValue(value.sbp);
  const diastolic = displayValue(value.dbp);
  const bloodPressure = systolic || diastolic
    ? `${systolic ?? '—'}/${diastolic ?? '—'}`
    : null;

  return [
    { label: 'HR', value: displayValue(value.hr) },
    { label: 'BP', value: bloodPressure },
    { label: 'RR', value: displayValue(value.rr) },
    { label: 'O₂', value: displayValue(value.o2) },
    { label: 'Temp', value: displayValue(value.temp) }
  ].filter((item): item is { label: string; value: string } => Boolean(item.value));
}

function evidenceItems(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!isRecord(item)) return [];
    const field = nonEmptyText(item.field);
    const snippet = nonEmptyText(item.text);
    const renderedValue = displayValue(item.value);
    if (!field || !evidenceFields.has(field) || !snippet || !renderedValue) return [];
    return [{ field, snippet, value: renderedValue }];
  });
}

export function ClinicalNlpAuditEvidenceCard({
  event,
  collapseEvidence = false
}: ClinicalNlpAuditEvidenceCardProps) {
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);

  if (event.action !== 'nlp_extraction_reviewed') return null;

  const details = detailsFor(event);
  const extractedFields = isRecord(details.extracted_fields) ? details.extracted_fields : {};
  const fields = extractedFieldItems(extractedFields);
  const vitals = vitalItems(extractedFields.vitals);
  const safetyCues = textList(details.safety_cues);
  const missingFields = textList(details.missing_fields);
  const evidence = evidenceItems(details.evidence);
  const message = nonEmptyText(details.message);
  const disclaimer = nonEmptyText(details.disclaimer);

  return (
    <section className="overflow-hidden rounded-3xl border border-blue-200 bg-gradient-to-br from-white via-blue-50/60 to-cyan-50/60 shadow-[0_18px_50px_-34px_rgba(30,64,175,0.65)]">
      <div className="border-b border-blue-100 px-4 py-4 sm:px-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-700 text-white shadow-sm">
              <FileSearch size={21} />
            </div>
            <div>
              <h3 className="font-display text-lg font-black text-slate-950">
                Clinical NLP Review Evidence
              </h3>
              {message ? <p className="mt-1 text-sm leading-6 text-slate-600">{message}</p> : null}
            </div>
          </div>
          <Badge className="w-fit border-emerald-200 bg-emerald-50 text-emerald-800">
            <CheckCircle2 size={14} /> Reviewed before prediction
          </Badge>
        </div>
      </div>

      <div className="space-y-4 p-4 sm:p-5">
        {safetyCues.length || missingFields.length ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {safetyCues.length ? (
              <div className="rounded-2xl border border-rose-100 bg-white/90 p-3.5">
                <p className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.16em] text-rose-700">
                  <ShieldAlert size={15} /> Safety cues
                </p>
                <div className="mt-2.5 flex flex-wrap gap-2">
                  {safetyCues.map((cue) => (
                    <Badge key={cue} className="border-rose-200 bg-rose-50 text-rose-800">
                      {cue}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}

            {missingFields.length ? (
              <div className="rounded-2xl border border-amber-100 bg-white/90 p-3.5">
                <p className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.16em] text-amber-700">
                  <AlertTriangle size={15} /> Missing fields
                </p>
                <div className="mt-2.5 flex flex-wrap gap-2">
                  {missingFields.map((field) => (
                    <Badge key={field} className="border-amber-200 bg-amber-50 text-amber-800">
                      {field}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}

        {fields.length || vitals.length ? (
          <div className="rounded-2xl border border-slate-200 bg-white/90 p-3.5">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">
              Extracted fields
            </p>
            {fields.length ? (
              <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                {fields.map((field) => (
                  <div key={field.label} className="rounded-xl bg-slate-50 px-3 py-2.5">
                    <dt className="text-[10px] font-black uppercase tracking-wide text-slate-400">
                      {field.label}
                    </dt>
                    <dd className="mt-1 text-sm font-semibold text-slate-800 [overflow-wrap:anywhere]">
                      {field.value}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : null}
            {vitals.length ? (
              <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3">
                {vitals.map((vital) => (
                  <Badge key={vital.label} className="border-blue-100 bg-blue-50 text-blue-900">
                    <span className="font-black">{vital.label}</span> {vital.value}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        {evidence.length && collapseEvidence ? (
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white/90">
            <button
              type="button"
              aria-controls={`nlp-evidence-${event.audit_id}`}
              aria-expanded={isEvidenceOpen}
              className="focus-ring flex w-full items-center justify-between gap-3 px-3.5 py-3 text-left text-sm font-black text-slate-800 hover:bg-slate-50"
              onClick={() => setIsEvidenceOpen((open) => !open)}
            >
              <span>{isEvidenceOpen ? 'Hide evidence snippets' : `View evidence snippets (${evidence.length})`}</span>
              <ChevronDown className={`shrink-0 transition-transform ${isEvidenceOpen ? 'rotate-180' : ''}`} size={17} />
            </button>
            {isEvidenceOpen ? (
              <div id={`nlp-evidence-${event.audit_id}`} className="grid gap-2 border-t border-slate-200 p-3.5 lg:grid-cols-2">
                {evidence.map((item, index) => (
                  <div key={`${item.field}-${index}`} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                        {readableField(item.field)}
                      </p>
                      <Badge className="border-slate-200 bg-white text-slate-700">{item.value}</Badge>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-700">“{item.snippet}”</p>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        {evidence.length && !collapseEvidence ? (
          <div className="rounded-2xl border border-slate-200 bg-white/90 p-3.5">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">
              Evidence snippets
            </p>
            <div className="mt-3 grid gap-2 lg:grid-cols-2">
              {evidence.map((item, index) => (
                <div key={`${item.field}-${index}`} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                      {readableField(item.field)}
                    </p>
                    <Badge className="border-slate-200 bg-white text-slate-700">{item.value}</Badge>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-700">“{item.snippet}”</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {disclaimer ? (
          <p className="rounded-2xl border border-blue-100 bg-blue-50/80 px-3.5 py-3 text-xs font-semibold leading-5 text-blue-900">
            {disclaimer}
          </p>
        ) : null}
        <p className="text-xs font-semibold leading-5 text-slate-500">
          Decision-support audit context only. Clinician review remains required.
        </p>
      </div>
    </section>
  );
}
