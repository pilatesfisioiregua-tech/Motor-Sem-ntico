import AgentBadge from './AgentBadge';

export default function ConflictLine({ from, to, description }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg
                    bg-red-500/5 border border-red-500/10">
      <AgentBadge agent={from} status="activo" />
      <span className="text-red-400 text-sm">{'\u26A1'}</span>
      <AgentBadge agent={to} status="activo" />
      {description && (
        <span className="text-xs text-[var(--text-tertiary)] ml-2 truncate flex-1">
          {description}
        </span>
      )}
    </div>
  );
}
