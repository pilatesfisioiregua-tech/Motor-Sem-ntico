const colorMap = {
  indigo: 'bg-indigo-400',
  emerald: 'bg-emerald-400',
  amber: 'bg-amber-400',
  red: 'bg-red-400',
  violet: 'bg-violet-400',
  cyan: 'bg-cyan-400',
  rose: 'bg-rose-400',
};

export default function Pulse({ color = 'indigo', size = 8 }) {
  const bg = colorMap[color] || colorMap.indigo;
  return (
    <span className="relative inline-flex">
      <span className={`absolute inline-flex h-full w-full rounded-full ${bg} opacity-75 animate-ping`}
            style={{ width: size, height: size }} />
      <span className={`relative inline-flex rounded-full ${bg}`}
            style={{ width: size, height: size }} />
    </span>
  );
}
