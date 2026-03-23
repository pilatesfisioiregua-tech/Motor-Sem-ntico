const variants = {
  default: 'bg-[var(--bg-surface)] border border-[var(--border)]',
  elevated: 'bg-[var(--bg-elevated)] border border-[var(--border-active)] shadow-[var(--shadow-elevated)]',
  organism: 'bg-[var(--bg-surface)] border border-violet-500/20 shadow-[0_0_24px_rgba(167,139,250,0.08)]',
  alert: 'bg-[var(--bg-surface)] border-l-2 border-l-amber-400 border border-[var(--border)]',
  danger: 'bg-[var(--bg-surface)] border-l-2 border-l-red-400 border border-[var(--border)]',
  success: 'bg-[var(--bg-surface)] border-l-2 border-l-emerald-400 border border-[var(--border)]',
};

export default function Card({ children, variant = 'default', glow = false, className = '' }) {
  return (
    <div className={`rounded-[var(--radius-lg)] p-5 transition-all duration-[var(--duration-normal)]
      ${variants[variant] || variants.default} ${glow ? 'shadow-[var(--shadow-glow)]' : ''} ${className}`}>
      {children}
    </div>
  );
}
