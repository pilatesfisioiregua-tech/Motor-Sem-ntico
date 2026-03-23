import { useState, useEffect, useRef } from 'react';
import VoiceButton from '../design/VoiceButton';

export function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'es-ES';
  utterance.rate = 1.0;
  const voices = speechSynthesis.getVoices();
  const spanishVoice = voices.find(v => v.lang.startsWith('es'));
  if (spanishVoice) utterance.voice = spanishVoice;
  speechSynthesis.speak(utterance);
}

export default function VoicePanel({ onTranscript }) {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      const result = event.results[event.results.length - 1];
      const text = result[0].transcript;
      setTranscript(text);
      if (result.isFinal) {
        setListening(false);
        onTranscript(text);
      }
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
  }, [onTranscript]);

  const toggle = () => {
    if (listening) { recognitionRef.current?.stop(); }
    else { setTranscript(''); recognitionRef.current?.start(); setListening(true); }
  };

  return (
    <div className="flex items-center gap-2">
      <VoiceButton listening={listening} onClick={toggle} />
      {transcript && <span className="text-xs text-[var(--text-tertiary)]">{transcript}</span>}
    </div>
  );
}
