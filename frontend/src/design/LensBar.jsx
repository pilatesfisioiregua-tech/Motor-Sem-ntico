/** iOS-native Health-style lens bars */
const lensConfig = [
  { key: 'S', label: 'Salud', color: '#30d158', bg: 'rgba(48, 209, 88, 0.15)' },
  { key: 'Se', label: 'Sentido', color: '#bf5af2', bg: 'rgba(191, 90, 242, 0.15)' },
  { key: 'C', label: 'Continuidad', color: '#64d2ff', bg: 'rgba(100, 210, 255, 0.15)' },
];

export default function LensBar({ salud = 0, sentido = 0, continuidad = 0, compact = false }) {
  const safe = (v) => (typeof v === 'number' && !isNaN(v)) ? v : 0.5;
  const values = { S: safe(salud), Se: safe(sentido), C: safe(continuidad) };

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        {lensConfig.map(l => (
          <div key={l.key} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: l.color }} />
            <span className="text-[13px] font-semibold" style={{ color: l.color, fontVariantNumeric: 'tabular-nums' }}>
              {(values[l.key] * 100).toFixed(0)}
            </span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      {lensConfig.map(l => (
        <div key={l.key} className="flex-1 rounded-xl p-3" style={{ background: l.bg }}>
          <div className="flex items-baseline justify-between mb-2">
            <span className="text-[11px] font-medium" style={{ color: l.color }}>{l.label}</span>
            <span className="text-[20px] font-bold tabular-nums" style={{ color: l.color, fontFamily: 'var(--font-system)' }}>
              {(values[l.key] * 100).toFixed(0)}
            </span>
          </div>
          <div className="h-1 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{ width: `${values[l.key] * 100}%`, background: l.color }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
