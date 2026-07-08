import { Minus, Plus } from 'lucide-react';
import type { Vitals } from '@/types/clinical';
import { ageBand, vitalFlag, vitalFlagTone, vitalRange, vitalStatusLabel, type VitalKey } from '@/lib/vitals';

interface VitalControl {
  key: VitalKey;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  format?: (value: number) => string;
}

const controls: VitalControl[] = [
  { key: 'spo2', label: 'Oxygen saturation', unit: '%', min: 70, max: 100, step: 1 },
  { key: 'heartRate', label: 'Heart rate', unit: 'bpm', min: 30, max: 220, step: 1 },
  { key: 'respiratoryRate', label: 'Respiratory rate', unit: '/min', min: 6, max: 60, step: 1 },
  { key: 'systolicBp', label: 'Systolic BP', unit: 'mmHg', min: 60, max: 220, step: 1 },
  { key: 'diastolicBp', label: 'Diastolic BP', unit: 'mmHg', min: 30, max: 130, step: 1 },
  { key: 'temperatureC', label: 'Temperature', unit: '°C', min: 34, max: 42, step: 0.1, format: (value) => value.toFixed(1) },
  { key: 'painScore', label: 'Pain score', unit: '/10', min: 0, max: 10, step: 1 }
];

function clampPercent(value: number, min: number, max: number) {
  return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
}

function formatStableValue(value: number, control: VitalControl) {
  return control.format ? control.format(value) : String(value);
}

function normalBand(control: VitalControl, age: number) {
  const range = vitalRange(control.key, age);
  const normalLow = range.low ?? control.min;
  const normalHigh = range.high ?? control.max;
  const left = clampPercent(normalLow, control.min, control.max);
  const right = clampPercent(normalHigh, control.min, control.max);
  return {
    normalLow,
    normalHigh,
    left,
    width: Math.max(2, right - left)
  };
}

function referenceText(control: VitalControl, age: number) {
  const range = vitalRange(control.key, age);
  const low = range.low;
  const high = range.high;
  if (low !== undefined && high !== undefined) return `Normal ${formatStableValue(low, control)}–${formatStableValue(high, control)} ${control.unit}`;
  if (low !== undefined) return `Normal ≥ ${formatStableValue(low, control)} ${control.unit}`;
  if (high !== undefined) return `Normal ≤ ${formatStableValue(high, control)} ${control.unit}`;
  return 'Reference range unavailable';
}

export function VitalSliderPanel({ vitals, age, onChange }: { vitals: Vitals; age: number; onChange: (next: Vitals) => void }) {
  const update = (key: VitalKey, nextValue: number) => {
    onChange({ ...vitals, [key]: Number(nextValue.toFixed(key === 'temperatureC' ? 1 : 0)) });
  };

  return (
    <div className="flex flex-col overflow-x-hidden">
      <div className="mb-2.5 flex shrink-0 flex-col gap-2 rounded-2xl border border-blue-100 bg-blue-50 px-3 py-2 text-sm text-blue-900 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-bold">Slider-based vitals entry</p>
          <p className="mt-1 text-xs leading-5 text-blue-800/80">
            Each vitals card stays in the normal page flow with fixed reference bands for {ageBand(age)} patients.
          </p>
        </div>
        <p className="font-data rounded-full bg-white px-3 py-1 text-xs font-black uppercase tracking-wide text-blue-700">Age {age || '—'}</p>
      </div>

      <div className="grid grid-cols-1 gap-2.5 md:grid-cols-2 xl:grid-cols-3">
        {controls.map((control) => {
          const value = vitals[control.key];
          const flag = vitalFlag(control.key, value, age);
          const display = formatStableValue(value, control);
          const band = normalBand(control, age);
          const thumbPosition = clampPercent(value, control.min, control.max);
          return (
            <section key={control.key} className={`flex h-full flex-col rounded-[1.2rem] border bg-white p-2.5 shadow-sm ${vitalFlagTone(flag)}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">{control.label}</p>
                  <div className="mt-1.5 flex items-end gap-2">
                    <span className="font-data text-2xl font-black text-slate-950">{display}</span>
                    <span className="pb-1 text-sm font-bold text-slate-500">{control.unit}</span>
                  </div>
                </div>
                <span className="rounded-full border bg-white px-2.5 py-1 text-[11px] font-black uppercase tracking-wide">{vitalStatusLabel(flag)}</span>
              </div>

              <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 px-2.5 py-1.5">
                <p className="text-[11px] font-black uppercase tracking-wide text-emerald-700">Stable reference</p>
                <p className="font-data mt-1 text-xs font-bold text-slate-700">{referenceText(control, age)}</p>
              </div>

              <div className="relative mt-3 h-8">
                <div className="absolute left-0 right-0 top-3 h-2 rounded-full bg-slate-200">
                  <div
                    className="absolute top-0 h-2 rounded-full bg-emerald-300/80"
                    style={{ left: `${band.left}%`, width: `${band.width}%` }}
                    aria-hidden="true"
                  />
                  <div
                    className="absolute top-1/2 h-4 w-1 -translate-y-1/2 rounded-full bg-clinical-blue shadow"
                    style={{ left: `calc(${thumbPosition}% - 2px)` }}
                    aria-hidden="true"
                  />
                </div>
                <input
                  type="range"
                  min={control.min}
                  max={control.max}
                  step={control.step}
                  value={value}
                  onChange={(event) => update(control.key, Number(event.target.value))}
                  className="vital-range-input absolute inset-0 h-8 w-full cursor-pointer opacity-0"
                  aria-label={control.label}
                />
              </div>

              <div className="font-data mt-1 flex items-center justify-between text-[11px] font-bold text-slate-400">
                <span>{formatStableValue(control.min, control)}</span>
                <span>{formatStableValue(control.max, control)}</span>
              </div>

              <div className="mt-2.5 grid grid-cols-[36px_1fr_36px] items-center gap-2">
                <button
                  type="button"
                  onClick={() => update(control.key, Math.max(control.min, value - control.step))}
                  className="focus-ring flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  aria-label={`Decrease ${control.label}`}
                >
                  <Minus size={16} />
                </button>
                <input
                  type="number"
                  min={control.min}
                  max={control.max}
                  step={control.step}
                  value={value}
                  onChange={(event) => update(control.key, Number(event.target.value))}
                  className="focus-ring w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-center font-data font-bold text-slate-950"
                />
                <button
                  type="button"
                  onClick={() => update(control.key, Math.min(control.max, value + control.step))}
                  className="focus-ring flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  aria-label={`Increase ${control.label}`}
                >
                  <Plus size={16} />
                </button>
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
