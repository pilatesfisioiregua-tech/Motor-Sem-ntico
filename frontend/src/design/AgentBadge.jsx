const statusConfig = {
  activo:     { color: 'text-emerald-400', icon: '\u25CF' },
  esperando:  { color: 'text-amber-400',   icon: '\u25D0' },
  bloqueado:  { color: 'text-red-400',     icon: '\u25A0' },
  completado: { color: 'text-indigo-400',  icon: '\u2713' },
};

export default function AgentBadge({ agent, status = 'activo', confidence }) {
  const cfg = statusConfig[status] || statusConfig.activo;

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                    bg-[var(--bg-elevated)] border border-[var(--border)]
                    text-xs font-medium transition-all hover:border-[var(--border-active)]">
      <span className={cfg.color}>{cfg.icon}</span>
      <span className="text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-mono)' }}>{agent}</span>
      {confidence != null && (
        <span className="text-[var(--text-tertiary)] text-[10px]" style={{ fontFamily: 'var(--font-mono)' }}>
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}
