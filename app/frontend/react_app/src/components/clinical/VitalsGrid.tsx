import { AlertTriangle } from 'lucide-react';
import type { Vitals } from '@/types/clinical';
import { ageBand, vitalFlag, vitalFlagTone, vitalStatusLabel, type VitalKey } from '@/lib/vitals';

function entered(value: number | undefined) {
  return typeof value === 'number' && Number.isFinite(value);
}

function formatBp(vitals: Vitals) {
  if (!entered(vitals.systolicBp) || !entered(vitals.diastolicBp)) return 'Not entered';
  return `${vitals.systolicBp}/${vitals.diastolicBp}`;
}

const rows: Array<{ key: VitalKey; label: string; compactLabel: string; format: (v: Vitals) => string }> = [
  { key: 'heartRate', label: 'Heart rate', compactLabel: 'HR', format: (v) => `${v.heartRate} bpm` },
  { key: 'respiratoryRate', label: 'Respiratory rate', compactLabel: 'RR', format: (v) => `${v.respiratoryRate} /min` },
  { key: 'systolicBp', label: 'Blood pressure', compactLabel: 'BP', format: formatBp },
  { key: 'temperatureC', label: 'Temperature', compactLabel: 'Temp', format: (v) => `${v.temperatureC.toFixed(1)}°C` },
  { key: 'spo2', label: 'SpO₂', compactLabel: 'SpO₂', format: (v) => `${v.spo2}%` },
  { key: 'painScore', label: 'Pain score', compactLabel: 'Pain', format: (v) => `${v.painScore}/10` }
];

export function VitalsGrid({ vitals, age, compact = false }: { vitals: Vitals; age?: number; compact?: boolean }) {
  return (
    <div className={compact ? 'space-y-2' : 'space-y-3'}>
      {!compact ? <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Age-aware display range: {ageBand(age)}</p> : null}
      <div className={compact ? 'grid grid-cols-2 gap-2' : 'grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3'}>
        {rows.map((row) => {
          const flag = vitalFlag(row.key, vitals[row.key], age);
          return (
            <div key={row.key} className={`flex h-full flex-col rounded-2xl border ${compact ? 'p-2' : 'p-3'} ${vitalFlagTone(flag)}`}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{compact ? row.compactLabel : row.label}</p>
                {flag !== 'normal' ? <AlertTriangle size={13} className={flag === 'critical' ? 'text-red-600' : 'text-amber-600'} /> : null}
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
