/** iOS-native voice button */
export default function VoiceButton({ listening = false, onClick }) {
  return (
    <button
      onClick={onClick}
      className="ios-btn relative"
      style={{
        width: 38,
        height: 38,
        borderRadius: '50%',
        padding: 0,
        background: listening ? 'var(--accent-red)' : 'rgba(118, 118, 128, 0.24)',
        transition: 'all 0.2s ease',
      }}
    >
      {listening && (
        <span className="absolute inset-[-3px] rounded-full" style={{ border: '2px solid rgba(255, 69, 58, 0.4)', animation: 'pulse-ring 1.5s ease infinite' }} />
      )}
      <span className="relative text-[16px] emoji-icon">
        {listening ? '\u23F9' : '\uD83C\uDFA4'}
      </span>
    </button>
  );
}
