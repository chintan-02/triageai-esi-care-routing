import type { EsiLevel } from '@/types/clinical';
import { esiDescriptor } from '@/lib/formatters';

const SEGMENT_COLORS: Record<EsiLevel, string> = {
  1: '#7F1D1D',
  2: '#DC2626',
  3: '#D97706',
  4: '#2563EB',
  5: '#16A34A'
};

const CX = 120;
const CY = 132;
const R_OUTER = 108;
const R_INNER = 78;

// theta: -90 = left (ESI 1), 0 = top (ESI 3), 90 = right (ESI 5)
function pointAt(radius: number, thetaDeg: number) {
  const rad = (thetaDeg * Math.PI) / 180;
  return { x: CX + radius * Math.sin(rad), y: CY - radius * Math.cos(rad) };
}

function segmentPath(startDeg: number, endDeg: number) {
  const outerStart = pointAt(R_OUTER, startDeg);
  const outerEnd = pointAt(R_OUTER, endDeg);
  const innerEnd = pointAt(R_INNER, endDeg);
  const innerStart = pointAt(R_INNER, startDeg);
  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${R_OUTER} ${R_OUTER} 0 0 1 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerEnd.x} ${innerEnd.y}`,
    `A ${R_INNER} ${R_INNER} 0 0 0 ${innerStart.x} ${innerStart.y}`,
    'Z'
  ].join(' ');
}

const SEGMENTS: Array<{ level: EsiLevel; start: number; end: number; center: number }> = [1, 2, 3, 4, 5].map((level) => {
  const start = -90 + (level - 1) * 36;
  const end = start + 36;
  return { level: level as EsiLevel, start, end, center: start + 18 };
});

function Needle({ level, ghost = false }: { level: EsiLevel; ghost?: boolean }) {
  const angle = SEGMENTS[level - 1].center;
  const tip = pointAt(R_INNER - 8, angle);
  return (
    <g opacity={ghost ? 0.45 : 1}>
      <line x1={CX} y1={CY} x2={tip.x} y2={tip.y} stroke={ghost ? '#94A3B8' : '#0B1220'} strokeWidth={ghost ? 2 : 3} strokeLinecap="round" strokeDasharray={ghost ? '4 3' : undefined} />
      <circle cx={tip.x} cy={tip.y} r={ghost ? 3 : 4} fill={ghost ? '#94A3B8' : '#0B1220'} />
    </g>
  );
}

export function AcuityGauge({ finalEsi, predictedEsi }: { finalEsi: EsiLevel; predictedEsi: EsiLevel }) {
  const escalated = finalEsi !== predictedEsi;

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 240 160" className="w-full max-w-[280px]" role="img" aria-label={`Acuity gauge showing final ESI ${finalEsi}`}>
        {SEGMENTS.map((segment) => (
          <path
            key={segment.level}
            d={segmentPath(segment.start, segment.end)}
            fill={SEGMENT_COLORS[segment.level]}
            opacity={segment.level === finalEsi ? 1 : 0.28}
            stroke="#ffffff"
            strokeWidth={2}
          />
        ))}
        {escalated ? <Needle level={predictedEsi} ghost /> : null}
        <Needle level={finalEsi} />
        <circle cx={CX} cy={CY} r={10} fill="#0B1220" />
        <circle cx={CX} cy={CY} r={4} fill="#ffffff" />
      </svg>
      <div className="-mt-2 text-center">
        <p className="font-display text-4xl font-extrabold text-slate-950">ESI {finalEsi}</p>
        <p className="text-sm font-semibold text-slate-600">{esiDescriptor(finalEsi)}</p>
        {escalated ? (
          <p className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-bold text-amber-800">
            Escalated from model prediction ESI {predictedEsi}
          </p>
        ) : (
          <p className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-bold text-slate-600">
            Matches model prediction
          </p>
        )}
      </div>
    </div>
  );
}
