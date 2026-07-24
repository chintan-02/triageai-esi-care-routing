import { useState } from 'react';
import { AlertTriangle, CheckCircle2, ChevronDown, ClipboardCheck, ShieldAlert } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import type { ClinicalIntakeExtractionResponse } from '@/types/clinicalNlp';

type ClinicalNlpReviewPanelProps = {
  extraction: ClinicalIntakeExtractionResponse;
  isReviewed: boolean;
  isStale?: boolean;
  onReviewedChange: (reviewed: boolean) => void;
};

function readableFieldName(field: string) {
  return field
    .replace(/^triage_vital_/, 'vital ')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char: string) => char.toUpperCase());
}

function readableValue(value: ClinicalIntakeExtractionResponse['evidence'][number]['value']) {
  if (Array.isArray(value)) return value.join(', ');
  if (value === null || value === undefined || value === '') return 'Not extracted';
  return String(value);
}

function pluralized(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? '' : 's'}`;
}

function extractedFieldCount(extraction: ClinicalIntakeExtractionResponse) {
  return [
    extraction.age,
    extraction.gender,
    extraction.chief_complaint,
    extraction.symptoms.length ? extraction.symptoms : null,
    extraction.vitals.hr,
    extraction.vitals.sbp,
    extraction.vitals.dbp,
    extraction.vitals.rr,
    extraction.vitals.o2,
    extraction.vitals.temp
  ].filter((value) => value !== null && value !== undefined && value !== '').length;
}

export function ClinicalNlpReviewPanel({
  extraction,
  isReviewed,
  isStale = false,
  onReviewedChange
}: ClinicalNlpReviewPanelProps) {
  const hasSafetyCues = extraction.safety_cues.length > 0;
  const hasMissingFields = extraction.missing_fields.length > 0;
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);
  const fieldCount = extractedFieldCount(extraction);

  const vitalItems = [
    { label: 'HR', value: extraction.vitals.hr },
    {
      label: 'BP',
      value:
        extraction.vitals.sbp !== null || extraction.vitals.dbp !== null
          ? `${extraction.vitals.sbp ?? '—'}/${extraction.vitals.dbp ?? '—'}`
          : null
    },
    { label: 'O₂', value: extraction.vitals.o2 },
    { label: 'Temp', value: extraction.vitals.temp },
    { label: 'RR', value: extraction.vitals.rr }
  ];

  return (
    <div className="space-y-3 rounded-[1.5rem] border border-blue-100 bg-blue-50/70 p-3 sm:p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm font-black text-blue-950">
            <ClipboardCheck size={18} />
            Clinical Intake NLP Safety Layer
          </div>
          <p className="mt-1 text-sm font-bold text-blue-950">
            {pluralized(fieldCount, 'field')} extracted · {pluralized(extraction.safety_cues.length, 'safety cue')} · {pluralized(extraction.missing_fields.length, 'missing field')}
          </p>
          <p className="mt-1 text-xs font-semibold leading-5 text-blue-900">
            Review required before prediction
          </p>
        </div>
        <Badge className={isStale ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-blue-200 bg-white text-blue-800'}>
          {isStale ? 'Re-extraction required' : 'Review required'}
        </Badge>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm shadow-slate-200/40">
          <h3 className="text-sm font-black text-slate-900">Extracted demographics</h3>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Age</p>
              <p className="mt-1.5 text-base font-bold text-slate-900">{extraction.age ?? 'Not extracted'}</p>
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Gender</p>
              <p className="mt-1.5 text-base font-bold text-slate-900">{extraction.gender ?? 'Not extracted'}</p>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm shadow-slate-200/40">
          <h3 className="text-sm font-black text-slate-900">Complaint</h3>
          <p className="mt-3 text-xs font-black uppercase tracking-[0.16em] text-slate-500">Chief complaint</p>
          <p className="mt-1.5 text-base font-bold leading-6 text-slate-900">
            {extraction.chief_complaint ?? 'Not extracted'}
          </p>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm shadow-slate-200/40">
          <h3 className="text-sm font-black text-slate-900">Key vitals</h3>
          <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-3 sm:grid-cols-3">
            {vitalItems.map((vital) => (
              <div key={vital.label}>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{vital.label}</p>
                <p className="mt-1.5 text-base font-bold text-slate-900">{vital.value ?? 'Not extracted'}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm shadow-slate-200/40">
          <h3 className="text-sm font-black text-slate-900">Symptoms ({extraction.symptoms.length})</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {extraction.symptoms.length ? (
              extraction.symptoms.map((symptom) => (
                <Badge key={symptom} className="border-slate-200 bg-slate-50 px-3 py-1 text-slate-700">
                  {symptom}
                </Badge>
              ))
            ) : (
              <span className="text-sm font-semibold text-slate-500">None extracted</span>
            )}
          </div>
        </section>
      </div>

      {hasSafetyCues ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-red-900">
          <div className="flex items-center gap-2 text-sm font-black">
            <ShieldAlert size={18} />
            Safety cues detected
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {extraction.safety_cues.map((cue) => (
              <Badge key={cue} className="border-red-200 bg-white text-red-800">
                {cue}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {hasMissingFields ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-amber-900">
          <div className="flex items-center gap-2 text-sm font-black">
            <AlertTriangle size={18} />
            Missing intake information
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {extraction.missing_fields.map((field) => (
              <Badge key={field} className="border-amber-200 bg-white text-amber-800">
                {field}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <button
          type="button"
          aria-controls="clinical-nlp-evidence"
          aria-expanded={isEvidenceOpen}
          className="focus-ring flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-bold text-slate-800 hover:bg-slate-50"
          onClick={() => setIsEvidenceOpen((open) => !open)}
        >
          <span>{isEvidenceOpen ? `Hide extraction evidence (${extraction.evidence.length})` : `View extraction evidence (${extraction.evidence.length})`}</span>
          <ChevronDown className={`shrink-0 transition-transform ${isEvidenceOpen ? 'rotate-180' : ''}`} size={17} />
        </button>
        {isEvidenceOpen ? (
          <div id="clinical-nlp-evidence" className="grid gap-3 border-t border-slate-200 p-4 md:grid-cols-2">
            {extraction.evidence.map((item, index) => (
              <div key={`${item.field}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                  {readableFieldName(item.field)}
                </p>
                <p className="mt-1 text-sm font-bold text-slate-900">{readableValue(item.value)}</p>
                <p className="mt-1 text-xs leading-5 text-slate-600">“{item.text}”</p>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <label className={`focus-within:ring-2 focus-within:ring-clinical-blue/40 flex items-start gap-3 rounded-2xl border p-3 text-sm font-semibold ${
        isStale
          ? 'cursor-not-allowed border-amber-200 bg-amber-50 text-amber-900'
          : isReviewed
            ? 'cursor-pointer border-emerald-200 bg-emerald-50 text-emerald-900'
            : 'cursor-pointer border-blue-200 bg-white text-blue-950'
      }`}>
        <input
          type="checkbox"
          checked={isReviewed}
          disabled={isStale}
          onChange={(event) => onReviewedChange(event.target.checked)}
          className="mt-1 h-5 w-5 rounded border-slate-300"
        />
        <span>
          <span className="flex items-center gap-2 font-black">
            <CheckCircle2 size={17} />
            {isStale ? 'Run extraction again before confirming review' : 'I reviewed the extracted fields before prediction'}
          </span>
          <span className="mt-1 block opacity-90">
            {isStale
              ? 'The original note changed after this extraction.'
              : 'I confirm the structured intake reflects my review; clinician judgment remains required.'}
          </span>
        </span>
      </label>
    </div>
  );
}
