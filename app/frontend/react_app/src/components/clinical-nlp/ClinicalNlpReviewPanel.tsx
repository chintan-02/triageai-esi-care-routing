import { AlertTriangle, CheckCircle2, ClipboardCheck, ShieldAlert } from 'lucide-react';
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

  return (
    <div className="space-y-3 rounded-[1.25rem] border border-blue-100 bg-blue-50/70 p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
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

      <div className="grid gap-2 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-3">
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-500">
            Extracted demographics
          </p>
          <div className="mt-2 grid gap-1.5 text-sm text-slate-700">
            <p><span className="font-bold">Age:</span> {extraction.age ?? 'Not extracted'}</p>
            <p><span className="font-bold">Gender:</span> {extraction.gender ?? 'Not extracted'}</p>
            <p><span className="font-bold">Chief complaint:</span> {extraction.chief_complaint ?? 'Not extracted'}</p>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-3">
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-500">
            Extracted vitals
          </p>
          <div className="mt-2 grid grid-cols-2 gap-1.5 text-sm text-slate-700">
            <p><span className="font-bold">HR:</span> {extraction.vitals.hr ?? '—'}</p>
            <p><span className="font-bold">BP:</span> {extraction.vitals.sbp ?? '—'}/{extraction.vitals.dbp ?? '—'}</p>
            <p><span className="font-bold">RR:</span> {extraction.vitals.rr ?? '—'}</p>
            <p><span className="font-bold">O₂:</span> {extraction.vitals.o2 ?? '—'}</p>
            <p><span className="font-bold">Temp:</span> {extraction.vitals.temp ?? '—'}</p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-3">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-500">
          Symptoms
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          {extraction.symptoms.length ? (
            extraction.symptoms.map((symptom) => (
              <Badge key={symptom} className="border-slate-200 bg-slate-50 text-slate-700">
                {symptom}
              </Badge>
            ))
          ) : (
            <span className="text-sm font-semibold text-slate-500">No symptoms extracted</span>
          )}
        </div>
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

      <div className="rounded-2xl border border-slate-200 bg-white p-3">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-500">
          Evidence snippets
        </p>
        <div className="mt-2 grid gap-2 md:grid-cols-2">
          {extraction.evidence.map((item, index) => (
            <div key={`${item.field}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 p-2">
              <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                {readableFieldName(item.field)}
              </p>
              <p className="mt-1 text-sm font-bold text-slate-900">{readableValue(item.value)}</p>
              <p className="mt-1 text-xs leading-5 text-slate-600">“{item.text}”</p>
            </div>
          ))}
        </div>
      </div>

      <label className="flex cursor-pointer items-start gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-900">
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
