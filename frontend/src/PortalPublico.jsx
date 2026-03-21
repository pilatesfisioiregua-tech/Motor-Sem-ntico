import { useState, useRef, useEffect } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

const SHORTCUTS = [
  "¿Qué es el Pilates auténtico?",
  "Tengo una lesión, ¿me puede ayudar?",
  "¿En qué se diferencia de un gimnasio?",
  "Quiero probar una clase",
];

export default function PortalPublico() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historial, setHistorial] = useState([]);
  const chatRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, loading]);

  async function send(texto) {
    const msg = texto || input.trim();
    if (!msg || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/pilates/publico/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: msg, historial }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.respuesta || 'Sin respuesta' }]);
      if (data.historial) setHistorial(data.historial);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Vaya, ha habido un error. Inténtalo de nuevo.' }]);
    }
    setLoading(false);
  }

  const styles = {
    container: {
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      padding: '20px 16px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    },
    header: {
      textAlign: 'center', color: '#fff', marginBottom: 16, maxWidth: 500,
    },
    logo: { fontSize: 28, fontWeight: 700, letterSpacing: '-0.5px' },
    subtitle: { fontSize: 14, opacity: 0.85, marginTop: 4 },
    chatBox: {
      background: '#fff', borderRadius: 20, width: '100%', maxWidth: 500,
      flex: 1, display: 'flex', flexDirection: 'column',
      boxShadow: '0 20px 60px rgba(0,0,0,0.2)', overflow: 'hidden',
      maxHeight: 'calc(100vh - 160px)',
    },
    messages: {
      flex: 1, overflowY: 'auto', padding: '20px 16px',
      display: 'flex', flexDirection: 'column', gap: 12,
    },
    welcome: {
      textAlign: 'center', color: '#666', fontSize: 14, padding: '20px 0',
      lineHeight: 1.6,
    },
    msgUser: {
      alignSelf: 'flex-end', background: '#6366f1', color: '#fff',
      padding: '10px 14px', borderRadius: '16px 16px 4px 16px',
      maxWidth: '80%', fontSize: 14, lineHeight: 1.5,
    },
    msgBot: {
      alignSelf: 'flex-start', background: '#f3f4f6', color: '#1a1a2e',
      padding: '10px 14px', borderRadius: '16px 16px 16px 4px',
      maxWidth: '80%', fontSize: 14, lineHeight: 1.5, whiteSpace: 'pre-wrap',
    },
    shortcuts: {
      display: 'flex', flexWrap: 'wrap', gap: 6, padding: '0 16px 12px',
      justifyContent: 'center',
    },
    chip: {
      background: '#f3f4f6', border: 'none', borderRadius: 20,
      padding: '6px 12px', fontSize: 12, color: '#555',
      cursor: 'pointer', transition: 'background 0.2s',
    },
    inputRow: {
      display: 'flex', gap: 8, padding: '12px 16px',
      borderTop: '1px solid #e5e7eb',
    },
    input: {
      flex: 1, border: '1px solid #e5e7eb', borderRadius: 12,
      padding: '10px 14px', fontSize: 14, outline: 'none',
    },
    sendBtn: {
      background: '#6366f1', color: '#fff', border: 'none',
      borderRadius: 12, padding: '10px 18px', fontSize: 14,
      fontWeight: 600, cursor: 'pointer',
    },
    dots: {
      alignSelf: 'flex-start', background: '#f3f4f6',
      padding: '10px 18px', borderRadius: '16px 16px 16px 4px',
      fontSize: 14, color: '#999',
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.logo}>Authentic Pilates</div>
        <div style={styles.subtitle}>Albelda de Iregua · Pilates de verdad</div>
      </div>

      <div style={styles.chatBox}>
        <div ref={chatRef} style={styles.messages}>
          {messages.length === 0 && (
            <div style={styles.welcome}>
              Hola! Soy el asistente de Authentic Pilates.<br />
              Pregúntame lo que quieras sobre el estudio.
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={m.role === 'user' ? styles.msgUser : styles.msgBot}>
              {m.content}
            </div>
          ))}
          {loading && <div style={styles.dots}>...</div>}
        </div>

        {messages.length === 0 && (
          <div style={styles.shortcuts}>
            {SHORTCUTS.map(s => (
              <button key={s} style={styles.chip} onClick={() => send(s)}>{s}</button>
            ))}
          </div>
        )}

        <div style={styles.inputRow}>
          <input
            style={styles.input}
            placeholder="Escribe tu pregunta..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            disabled={loading}
          />
          <button style={styles.sendBtn} onClick={() => send()} disabled={loading}>
            Enviar
          </button>
        </div>
      </div>
    </div>
  );
}
