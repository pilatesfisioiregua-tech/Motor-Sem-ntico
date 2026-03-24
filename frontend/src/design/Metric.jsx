const sizes = {
  sm: { value: 'text-xl', label: 'text-[10px]' },
  md: { value: 'text-3xl', label: 'text-[11px]' },
  lg: { value: 'text-5xl', label: 'text-xs' },
};

export default function Metric({ label, value, unit = '', delta = null, size = 'md' }) {
  const s = sizes[size] || sizes.md;
  const deltaColor = delta > 0 ? 'text-emerald-400' : delta < 0 ? 'text-red-400' : 'text-[var(--text-tertiary)]';
  const deltaArrow = delta > 0 ? '\u2191' : delta < 0 ? '\u2193' : '';
  const deltaBg = delta > 0 ? 'bg-emerald-400/10' : delta < 0 ? 'bg-red-400/10' : 'bg-white/5';

  return (
    <div className="flex flex-col gap-1.5">
      <span className={`${s.label} font-semibold tracking-[0.06em] uppercase text-[var(--text-ghost)]`}>
        {label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className={`${s.value} font-bold tracking-tighter text-[var(--text-primary)] metric-value`}
              style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.03em' }}>
          {value}
          {unit && <span className="text-[0.45em] text-[var(--text-tertiary)] ml-0.5 font-medium">{unit}</span>}
        </span>
        {delta !== null && delta !== 0 && (
          <span className={`text-[10px] font-semibold ${deltaColor} ${deltaBg} px-1.5 py-0.5 rounded-md`}
                style={{ fontFamily: 'var(--font-mono)' }}>
            {deltaArrow}{Math.abs(delta)}%
          </span>
        )}
      </div>
    </div>
  );
}
