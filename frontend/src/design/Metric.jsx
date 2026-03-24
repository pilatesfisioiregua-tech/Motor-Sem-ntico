/** iOS-native metric display */
export default function Metric({ label, value, unit = '', delta = null, color = 'var(--accent-blue)' }) {
  const deltaColor = delta > 0 ? 'var(--accent-green)' : delta < 0 ? 'var(--accent-red)' : 'var(--text-tertiary)';
  const deltaArrow = delta > 0 ? '\u2191' : delta < 0 ? '\u2193' : '';

  return (
    <div className="flex flex-col items-center gap-1 p-3">
      <span className="text-[28px] font-bold tracking-tight tabular-nums" style={{ color, fontFamily: 'var(--font-system)' }}>
        {value}
        {unit && <span className="text-[14px] font-medium ml-0.5" style={{ color: 'var(--text-tertiary)' }}>{unit}</span>}
      </span>
      {delta !== null && delta !== 0 && (
        <span className="text-[11px] font-semibold tabular-nums" style={{ color: deltaColor }}>
          {deltaArrow}{Math.abs(delta)}%
        </span>
      )}
      <span className="text-[11px] font-medium" style={{ color: 'var(--text-secondary)' }}>{label}</span>
    </div>
  );
}
