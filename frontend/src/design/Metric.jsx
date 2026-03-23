const sizes = {
  sm: { value: 'text-lg', label: 'text-[10px]' },
  md: { value: 'text-3xl', label: 'text-xs' },
  lg: { value: 'text-5xl', label: 'text-sm' },
};

export default function Metric({ label, value, unit = '', delta = null, size = 'md' }) {
  const s = sizes[size] || sizes.md;
  const deltaColor = delta > 0 ? 'text-emerald-400' : delta < 0 ? 'text-red-400' : 'text-[var(--text-tertiary)]';
  const deltaArrow = delta > 0 ? '\u2191' : delta < 0 ? '\u2193' : '\u2192';

  return (
    <div className="flex flex-col gap-1">
      <span className={`${s.label} font-medium tracking-wider uppercase text-[var(--text-tertiary)]`}>
        {label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className={`${s.value} font-bold tracking-tight text-[var(--text-primary)]`}
              style={{ fontFamily: 'var(--font-display)' }}>
          {value}
          {unit && <span className="text-[0.5em] text-[var(--text-secondary)] ml-0.5">{unit}</span>}
        </span>
        {delta !== null && (
          <span className={`text-xs font-medium ${deltaColor}`}
                style={{ fontFamily: 'var(--font-mono)' }}>
            {deltaArrow} {Math.abs(delta)}%
          </span>
        )}
      </div>
    </div>
  );
}
