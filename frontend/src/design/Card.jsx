const variants = {
  default: 'bg-[var(--bg-surface)] border border-[var(--border)] card-interactive',
  elevated: 'glass border border-[var(--glass-border)] shadow-[var(--shadow-elevated)] card-interactive',
  organism: 'glass border border-violet-500/15 shadow-[0_0_32px_rgba(167,139,250,0.06)] card-interactive',
  alert: 'bg-[var(--bg-surface)] border-l-2 border-l-amber-400/80 border border-[var(--border)] card-interactive',
  danger: 'bg-[var(--bg-surface)] border-l-2 border-l-red-400/80 border border-[var(--border)] card-interactive',
  success: 'bg-[var(--bg-surface)] border-l-2 border-l-emerald-400/80 border border-[var(--border)] card-interactive',
  glass: 'glass card-interactive',
};

export default function Card({ children, variant = 'default', glow = false, className = '' }) {
  return (
    <div className={`rounded-[var(--radius-lg)] p-5
      ${variants[variant] || variants.default}
      ${glow ? 'shadow-[var(--shadow-glow)]' : ''} ${className}`}>
      {children}
    </div>
  );
}
