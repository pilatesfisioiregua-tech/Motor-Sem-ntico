const typeColors = {
  DIAGNOSTICO: { dot: 'bg-cyan-400/80', ring: 'ring-cyan-400/30', text: 'text-cyan-400' },
  PRESCRIPCION: { dot: 'bg-indigo-400/80', ring: 'ring-indigo-400/30', text: 'text-indigo-400' },
  ALERTA: { dot: 'bg-amber-400/80', ring: 'ring-amber-400/30', text: 'text-amber-400' },
  VETO: { dot: 'bg-red-400/80', ring: 'ring-red-400/30', text: 'text-red-400' },
  OPORTUNIDAD: { dot: 'bg-emerald-400/80', ring: 'ring-emerald-400/30', text: 'text-emerald-400' },
  ACCION: { dot: 'bg-violet-400/80', ring: 'ring-violet-400/30', text: 'text-violet-400' },
  DATO: { dot: 'bg-slate-400/80', ring: 'ring-slate-400/30', text: 'text-slate-400' },
};

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

export default function SignalFlow({ signals = [] }) {
  return (
    <div className="relative pl-4 border-l border-[var(--border)]">
      {signals.map((s, i) => {
        const c = typeColors[s.tipo] || typeColors.DATO;
        return (
          <div key={i} className="relative mb-3 group">
            <div className={`absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full
                            ${c.dot} ring-2 ring-[var(--bg-deep)]
                            group-hover:${c.ring} transition-all`} />
            <div className="flex items-start gap-3">
              <span className={`text-[10px] font-bold tracking-wider uppercase
                               ${c.text} min-w-[80px]`}
                    style={{ fontFamily: 'var(--font-mono)' }}>
                {s.tipo}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-[var(--text-primary)]">
                  {s.origen} &rarr; {s.destino || 'bus'}
                </div>
                <div className="text-[11px] text-[var(--text-tertiary)] truncate">
                  {s.resumen || ''}
                </div>
              </div>
              <span className="text-[10px] text-[var(--text-ghost)] whitespace-nowrap"
                    style={{ fontFamily: 'var(--font-mono)' }}>
                {timeAgo(s.created_at)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
