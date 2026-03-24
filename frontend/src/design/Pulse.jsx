/** iOS-native loading pulse */
export default function Pulse({ color = 'blue', size = 8 }) {
  const colors = {
    blue: 'var(--accent-blue)',
    green: 'var(--accent-green)',
    amber: 'var(--accent-amber)',
    red: 'var(--accent-red)',
    indigo: 'var(--accent-indigo)',
    violet: 'var(--accent-violet)',
  };
  const c = colors[color] || colors.blue;

  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2].map(i => (
        <div
          key={i}
          className="rounded-full"
          style={{
            width: size,
            height: size,
            background: c,
            animation: `breathe 1.4s ease-in-out ${i * 0.15}s infinite`,
          }}
        />
      ))}
    </div>
  );
}
