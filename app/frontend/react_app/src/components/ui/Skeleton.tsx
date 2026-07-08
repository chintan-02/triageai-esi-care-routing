export function SkeletonBlock({ className = '' }: { className?: string }) {
  return <div className={`skeleton animate-shimmer rounded-2xl ${className}`} />;
}

export function SkeletonStatRow({ count = 4 }: { count?: number }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="rounded-3xl border border-clinical-border bg-white p-5 shadow-card">
          <SkeletonBlock className="h-4 w-24" />
          <SkeletonBlock className="mt-3 h-8 w-16" />
          <SkeletonBlock className="mt-4 h-3 w-32" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonTableRows({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="divide-y divide-slate-100">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex items-center gap-6 px-5 py-4">
          {Array.from({ length: cols }).map((_, colIndex) => (
            <SkeletonBlock key={colIndex} className={`h-4 ${colIndex === 0 ? 'w-32' : 'w-20'}`} />
          ))}
        </div>
      ))}
    </div>
  );
}
