import { AlertTriangle } from 'lucide-react';
import type { DraftVitals, Vitals } from '@/types/clinical';
import { ageBand, bloodPressureFlag, vitalFlag, vitalFlagTone, vitalStatusLabel, type VitalKey } from '@/lib/vitals';

type VitalValues = Vitals | DraftVitals;

function entered(value: number | null | undefined): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function formatBp(vitals: VitalValues) {
  if (!entered(vitals.systolicBp) && !entered(vitals.diastolicBp)) return 'Not entered';
  return `${entered(vitals.systolicBp) ? vitals.systolicBp : '—'}/${entered(vitals.diastolicBp) ? vitals.diastolicBp : '—'}`;
}

function formattedVital(value: number | null, suffix: string, decimals?: number) {
  if (!entered(value)) return 'Not entered';
  return `${decimals === undefined ? value : value.toFixed(decimals)}${suffix}`;
}

const rows: Array<{ key: VitalKey; label: string; compactLabel: string; format: (v: VitalValues) => string }> = [
  { key: 'heartRate', label: 'Heart rate', compactLabel: 'HR', format: (v) => formattedVital(v.heartRate, ' bpm') },
  { key: 'respiratoryRate', label: 'Respiratory rate', compactLabel: 'RR', format: (v) => formattedVital(v.respiratoryRate, ' /min') },
  { key: 'systolicBp', label: 'Blood pressure', compactLabel: 'BP', format: formatBp },
  { key: 'temperatureC', label: 'Temperature', compactLabel: 'Temp', format: (v) => formattedVital(v.temperatureC, '°C', 1) },
  { key: 'spo2', label: 'SpO₂', compactLabel: 'SpO₂', format: (v) => formattedVital(v.spo2, '%') },
  { key: 'painScore', label: 'Pain score', compactLabel: 'Pain', format: (v) => formattedVital(v.painScore, '/10') }
];

export function VitalsGrid({ vitals, age, compact = false }: { vitals: VitalValues; age?: number; compact?: boolean }) {
  return (
    <div className={compact ? 'space-y-2' : 'space-y-3'}>
      {!compact ? <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Age-aware display range: {ageBand(age)}</p> : null}
      <div className={compact ? 'grid grid-cols-2 gap-2' : 'grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3'}>
        {rows.map((row) => {
          const flag = row.key === 'systolicBp'
            ? bloodPressureFlag(vitals, age)
            : vitalFlag(row.key, vitals[row.key], age);
          return (
            <div key={row.key} className={`flex h-full flex-col rounded-2xl border ${compact ? 'p-2' : 'p-3'} ${vitalFlagTone(flag)}`}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{compact ? row.compactLabel : row.label}</p>
                {flag === 'abnormal' || flag === 'critical' ? <AlertTriangle size={13} className={flag === 'critical' ? 'text-red-600' : 'text-amber-600'} /> : null}
              </div>
              <p className={`font-data mt-1 font-bold ${compact ? 'text-base' : 'text-lg'}`}>{row.format(vitals)}</p>
              <p className="mt-1 text-[11px] font-bold uppercase tracking-wide opacity-70">{vitalStatusLabel(flag)}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
