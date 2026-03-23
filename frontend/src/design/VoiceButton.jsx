export default function VoiceButton({ listening = false, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`relative w-11 h-11 rounded-full flex items-center justify-center
                  transition-all duration-300 cursor-pointer
                  ${listening
                    ? 'bg-red-500 shadow-[0_0_24px_rgba(248,113,113,0.4)]'
                    : 'bg-[var(--accent-indigo)] hover:shadow-[var(--shadow-glow)]'
                  }`}
    >
      {listening && (
        <>
          <span className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-30" />
          <span className="absolute inset-[-4px] rounded-full border-2 border-red-400/30 animate-pulse" />
        </>
      )}
      <span className="relative text-white text-lg">
        {listening ? '\u23F9' : '\uD83C\uDFA4'}
      </span>
    </button>
  );
}
