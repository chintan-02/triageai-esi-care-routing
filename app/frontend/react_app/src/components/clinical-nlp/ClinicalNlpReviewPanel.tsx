import { useState } from 'react';
import { AlertTriangle, CheckCircle2, ChevronDown, ClipboardCheck, ShieldAlert } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import type { ClinicalIntakeExtractionResponse } from '@/types/clinicalNlp';

type ClinicalNlpReviewPanelProps = {
  extraction: ClinicalIntakeExtractionResponse;
  isReviewed: boolean;
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

export function ClinicalNlpReviewPanel({
  extraction,
  isReviewed,
  onReviewedChange
}: ClinicalNlpReviewPanelProps) {
  const hasSafetyCues = extraction.safety_cues.length > 0;
  const hasMissingFields = extraction.missing_fields.length > 0;
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);

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
    <div className="space-y-4 rounded-[1.5rem] border border-blue-100 bg-blue-50/70 p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm font-black text-blue-950">
            <ClipboardCheck size={18} />
            Clinical Intake NLP Safety Layer
          </div>
          <p className="mt-1 text-sm leading-6 text-blue-900">
            Extracted fields are decision-support only and require clinician review before prediction.
          </p>
        </div>
        <Badge className="border-blue-200 bg-white text-blue-800">
          Review required
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-200/40 sm:p-5">
          <h3 className="text-sm font-black text-slate-900">Extracted demographics</h3>
          <div className="mt-4 grid grid-cols-2 gap-4">
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

        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-200/40 sm:p-5">
          <h3 className="text-sm font-black text-slate-900">Complaint</h3>
          <p className="mt-4 text-xs font-black uppercase tracking-[0.16em] text-slate-500">Chief complaint</p>
          <p className="mt-1.5 text-base font-bold leading-6 text-slate-900">
            {extraction.chief_complaint ?? 'Not extracted'}
          </p>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-200/40 sm:p-5">
          <h3 className="text-sm font-black text-slate-900">Key vitals</h3>
          <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-3">
            {vitalItems.map((vital) => (
              <div key={vital.label}>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{vital.label}</p>
                <p className="mt-1.5 text-base font-bold text-slate-900">{vital.value ?? '—'}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-200/40 sm:p-5">
          <h3 className="text-sm font-black text-slate-900">Symptoms ({extraction.symptoms.length})</h3>
          <div className="mt-4 flex flex-wrap gap-2">
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
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-900">
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
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900">
          <div className="flex items-center gap-2 text-sm font-black">
            <AlertTriangle size={18} />
            Missing critical fields
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
          <span>{isEvidenceOpen ? 'Hide extraction evidence' : 'View extraction evidence'}</span>
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

      <label className="flex cursor-pointer items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-900">
        <input
          type="checkbox"
          checked={isReviewed}
          onChange={(event) => onReviewedChange(event.target.checked)}
          className="mt-1 h-4 w-4 rounded border-emerald-300"
        />
        <span>
          <span className="flex items-center gap-2 font-black">
            <CheckCircle2 size={17} />
            I reviewed the extracted fields before prediction
          </span>
          <span className="mt-1 block text-emerald-800">
            The clinician remains responsible for confirming or editing structured intake values.
          </span>
        </span>
      </label>

      <p className="text-xs font-semibold leading-5 text-blue-900">
        {extraction.disclaimer}
      </p>
    </div>
  );
}
