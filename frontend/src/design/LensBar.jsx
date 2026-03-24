const lensConfig = [
  { key: 'S', label: 'Salud', color: 'emerald' },
  { key: 'Se', label: 'Sentido', color: 'violet' },
  { key: 'C', label: 'Continuidad', color: 'cyan' },
];

const barColors = {
  emerald: 'bg-emerald-400',
  violet: 'bg-violet-400',
  cyan: 'bg-cyan-400',
};

const textColors = {
  emerald: 'text-emerald-400',
  violet: 'text-violet-400',
  cyan: 'text-cyan-400',
};

export default function LensBar({ salud = 0, sentido = 0, continuidad = 0, showLabels = true }) {
  const safe = (v) => (typeof v === 'number' && !isNaN(v)) ? v : 0.5;
  const values = { S: safe(salud), Se: safe(sentido), C: safe(continuidad) };

  return (
    <div className="flex gap-3">
      {lensConfig.map(l => (
        <div key={l.key} className="flex-1">
          {showLabels && (
            <div className="flex justify-between items-baseline mb-1.5">
              <span className="text-[10px] font-medium tracking-wider uppercase text-[var(--text-tertiary)]">
                {l.label}
              </span>
              <span className={`text-sm font-bold ${textColors[l.color]}`}
                    style={{ fontFamily: 'var(--font-mono)' }}>
                {(values[l.key] * 100).toFixed(0)}
              </span>
            </div>
          )}
          <div className="h-1.5 rounded-full bg-[var(--bg-void)] overflow-hidden">
            <div
              className={`h-full rounded-full ${barColors[l.color]} lens-bar-fill`}
              style={{ width: `${values[l.key] * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
