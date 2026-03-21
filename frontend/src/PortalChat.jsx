import { useState, useEffect, useRef } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

// Sugerencias rápidas
const SHORTCUTS = [
  { emoji: '📅', text: '¿Cuándo es mi próxima clase?' },
  { emoji: '❌', text: 'Quiero cancelar una clase' },
  { emoji: '🔄', text: '¿Hay hueco para recuperar?' },
  { emoji: '💰', text: '¿Cuánto debo?' },
  { emoji: '📄', text: 'Mis facturas' },
  { emoji: '📊', text: '¿Cómo voy este mes?' },
];

export default function PortalChat({ token }) {
  const [nombre, setNombre] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historial, setHistorial] = useState([]);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Load client name
  useEffect(() => {
    fetch(`${BASE}/portal/${token}/data`)
      .then(r => { if (!r.ok) throw new Error('Portal no disponible'); return r.json(); })
      .then(d => setNombre(d.cliente.nombre))
      .catch(e => setError(e.message));
  }, [token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send(text) {
    if (!text.trim() || loading) return;
    const userMsg = text.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const r = await fetch(`${BASE}/portal/${token}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: userMsg, historial }),
      });
      if (!r.ok) throw new Error('Error de conexión');
      const data = await r.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        text: data.respuesta,
        datos: data.datos,
      }]);
      setHistorial(data.historial || []);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Perdona, ha habido un error. Inténtalo de nuevo.',
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  if (error) return (
    <div style={s.container}>
      <div style={s.card}>
        <p style={{ color: '#ef4444', textAlign: 'center', padding: 40 }}>{error}</p>
      </div>
    </div>
  );

  return (
    <div style={s.container}>
      <div style={s.card}>
        {/* Header */}
        <div style={s.header}>
          <div style={s.logo}>AP</div>
          <div>
            <div style={s.title}>Authentic Pilates</div>
            {nombre && <div style={s.greeting}>Hola, {nombre}</div>}
          </div>
        </div>

        {/* Messages */}
        <div style={s.chat}>
          {messages.length === 0 && (
            <div style={s.welcome}>
              <div style={s.welcomeText}>¿Qué necesitas?</div>
              <div style={s.shortcuts}>
                {SHORTCUTS.map((sc, i) => (
                  <button key={i} style={s.shortcut}
                    onClick={() => send(sc.text)}>
                    <span>{sc.emoji}</span> {sc.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} style={msg.role === 'user' ? s.msgUser : s.msgBot}>
              <div style={msg.role === 'user' ? s.bubbleUser : s.bubbleBot}>
                {msg.text.split('\n').map((line, j) => (
                  <span key={j}>{line}<br/></span>
                ))}
              </div>
              {/* Render data cards if present */}
              {msg.datos && Object.keys(msg.datos).length > 0 && (
                <div style={s.dataCards}>
                  {renderDataCards(msg.datos)}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={s.msgBot}>
              <div style={{ ...s.bubbleBot, opacity: 0.6 }}>
                <span style={s.dots}>
                  <span>.</span><span>.</span><span>.</span>
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={s.inputRow}>
          <input
            ref={inputRef}
            style={s.input}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send(input)}
            placeholder="Escribe lo que necesitas..."
            disabled={loading}
          />
          <button style={s.sendBtn} onClick={() => send(input)} disabled={loading || !input.trim()}>
            →
          </button>
        </div>

        {/* Quick shortcuts after conversation started */}
        {messages.length > 0 && (
          <div style={s.miniShortcuts}>
            {SHORTCUTS.slice(0, 4).map((sc, i) => (
              <button key={i} style={s.miniShortcut}
                onClick={() => send(sc.text)}>
                {sc.emoji}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function renderDataCards(datos) {
  const cards = [];
  // Render huecos de recuperación
  if (datos.buscar_huecos_recuperacion?.huecos?.length > 0) {
    datos.buscar_huecos_recuperacion.huecos.slice(0, 5).forEach((h, i) => {
      cards.push(
        <div key={`hueco-${i}`} style={s.dataCard}>
          <div style={{ fontWeight: 600 }}>{h.dia} {h.fecha}</div>
          <div style={{ fontSize: 13, color: '#6b7280' }}>{h.hora} · {h.grupo}</div>
          <div style={{ fontSize: 12, color: '#22c55e' }}>{h.plazas_libres} plazas</div>
        </div>
      );
    });
  }
  // Render facturas
  if (datos.ver_facturas?.facturas?.length > 0) {
    datos.ver_facturas.facturas.forEach((f, i) => {
      cards.push(
        <div key={`fact-${i}`} style={s.dataCard}>
          <div style={{ fontWeight: 600 }}>{f.numero}</div>
          <div style={{ fontSize: 13 }}>{f.fecha} · {f.total.toFixed(2)}€</div>
          <a href={`${BASE}${f.pdf_url}`} target="_blank"
            style={{ fontSize: 12, color: '#6366f1' }}>Descargar PDF</a>
        </div>
      );
    });
  }
  // Render próximas clases
  if (datos.ver_proximas_clases?.clases?.length > 0) {
    datos.ver_proximas_clases.clases.slice(0, 5).forEach((c, i) => {
      cards.push(
        <div key={`clase-${i}`} style={s.dataCard}>
          <div style={{ fontWeight: 600 }}>{c.dia} {c.fecha}</div>
          <div style={{ fontSize: 13, color: '#6b7280' }}>{c.hora} · {c.grupo}</div>
          <div style={{ fontSize: 12, color: c.estado === 'confirmada' ? '#22c55e' : '#9ca3af' }}>
            {c.estado}
          </div>
        </div>
      );
    });
  }
  return cards;
}

const s = {
  container: {
    minHeight: '100vh', display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
    background: '#f0f0f0', padding: '16px 8px', fontFamily: "'Inter', -apple-system, sans-serif",
  },
  card: {
    background: '#fff', borderRadius: 20, maxWidth: 440, width: '100%',
    boxShadow: '0 8px 40px rgba(0,0,0,0.08)', marginTop: 12,
    display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 56px)', maxHeight: 'calc(100vh - 56px)',
  },
  header: {
    display: 'flex', gap: 12, alignItems: 'center',
    padding: '16px 20px', borderBottom: '1px solid #f3f4f6',
  },
  logo: {
    width: 40, height: 40, borderRadius: 12, background: '#6366f1',
    color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontWeight: 700, fontSize: 14,
  },
  title: { fontSize: 16, fontWeight: 700, color: '#111' },
  greeting: { fontSize: 13, color: '#6b7280' },
  chat: {
    flex: 1, overflowY: 'auto', padding: '16px 16px 8px',
    display: 'flex', flexDirection: 'column', gap: 8,
  },
  welcome: { textAlign: 'center', paddingTop: 40 },
  welcomeText: { fontSize: 20, fontWeight: 600, marginBottom: 24, color: '#374151' },
  shortcuts: { display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 300, margin: '0 auto' },
  shortcut: {
    display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
    background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 12,
    fontSize: 13, color: '#374151', cursor: 'pointer', textAlign: 'left',
    transition: 'all 0.15s',
  },
  msgUser: { display: 'flex', justifyContent: 'flex-end' },
  msgBot: { display: 'flex', flexDirection: 'column', alignItems: 'flex-start' },
  bubbleUser: {
    background: '#6366f1', color: '#fff', padding: '10px 14px',
    borderRadius: '16px 16px 4px 16px', maxWidth: '80%', fontSize: 14, lineHeight: 1.5,
  },
  bubbleBot: {
    background: '#f3f4f6', color: '#111', padding: '10px 14px',
    borderRadius: '16px 16px 16px 4px', maxWidth: '85%', fontSize: 14, lineHeight: 1.5,
  },
  dataCards: { display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6, width: '85%' },
  dataCard: {
    background: '#fafafa', border: '1px solid #e5e7eb', borderRadius: 10,
    padding: '8px 12px', fontSize: 13,
  },
  inputRow: {
    display: 'flex', gap: 8, padding: '12px 16px',
    borderTop: '1px solid #f3f4f6',
  },
  input: {
    flex: 1, padding: '12px 16px', border: '1px solid #e5e7eb', borderRadius: 14,
    fontSize: 14, outline: 'none', background: '#f9fafb',
  },
  sendBtn: {
    width: 44, height: 44, borderRadius: 14, border: 'none',
    background: '#6366f1', color: '#fff', fontSize: 18, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  miniShortcuts: {
    display: 'flex', justifyContent: 'center', gap: 12, padding: '8px 16px 12px',
  },
  miniShortcut: {
    width: 36, height: 36, borderRadius: 10, border: '1px solid #e5e7eb',
    background: '#fff', fontSize: 16, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  dots: { display: 'inline-flex', gap: 2, animation: 'pulse 1s infinite' },
};
