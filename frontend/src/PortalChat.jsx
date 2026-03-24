import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';

const SHORTCUTS = [
  { emoji: '📅', text: '¿Cuándo es mi próxima clase?', label: 'Próxima clase' },
  { emoji: '❌', text: 'Quiero cancelar una clase', label: 'Cancelar' },
  { emoji: '🔄', text: '¿Hay hueco para recuperar?', label: 'Recuperar' },
  { emoji: '💰', text: '¿Cuánto debo?', label: 'Mi cuenta' },
  { emoji: '📄', text: 'Mis facturas', label: 'Facturas' },
  { emoji: '📊', text: '¿Cómo voy este mes?', label: 'Mi progreso' },
];

export default function PortalChat() {
  const { token } = useParams();
  const [nombre, setNombre] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historial, setHistorial] = useState([]);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fetch(`/portal/${token}/data`)
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
      const r = await fetch(`/portal/${token}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: userMsg, historial }),
      });
      if (!r.ok) throw new Error('Error de conexión');
      const data = await r.json();
      setMessages(prev => [...prev, {
        role: 'assistant', text: data.respuesta, datos: data.datos,
      }]);
      setHistorial(data.historial || []);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant', text: 'Perdona, ha habido un error. Inténtalo de nuevo.',
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  if (error) return (
    <div style={s.page}>
      <div style={s.errorCard}>
        <div style={s.errorIcon}>!</div>
        <p style={s.errorText}>{error}</p>
      </div>
    </div>
  );

  return (
    <div style={s.page}>
      <div style={s.card}>
        {/* Apple-style header */}
        <header style={s.header}>
          <div style={s.headerInner}>
            <div style={s.logoMark}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
            </div>
            <div>
              <div style={s.brandName}>Authentic Pilates</div>
              <div style={s.brandSub}>Albelda de Iregua</div>
            </div>
          </div>
          {nombre && <div style={s.avatar}>{nombre[0]}</div>}
        </header>

        {/* Chat area */}
        <div style={s.chat}>
          {messages.length === 0 && (
            <div style={s.welcome}>
              <div style={s.welcomeEmoji}>✨</div>
              <h2 style={s.welcomeTitle}>
                {nombre ? `Hola, ${nombre}` : 'Bienvenido'}
              </h2>
              <p style={s.welcomeSub}>¿En qué puedo ayudarte hoy?</p>
              <div style={s.grid}>
                {SHORTCUTS.map((sc, i) => (
                  <button key={i} style={s.gridBtn} onClick={() => send(sc.text)}
                    onMouseEnter={e => { e.currentTarget.style.background = '#f3f4f6'; e.currentTarget.style.transform = 'scale(1.02)'; }}
                    onMouseLeave={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.transform = 'scale(1)'; }}>
                    <span style={s.gridEmoji}>{sc.emoji}</span>
                    <span style={s.gridLabel}>{sc.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} style={msg.role === 'user' ? s.rowUser : s.rowBot}>
              {msg.role !== 'user' && <div style={s.botDot}/>}
              <div style={msg.role === 'user' ? s.bubbleUser : s.bubbleBot}>
                {msg.text.split('\n').map((line, j) => (
                  <span key={j}>{line}{j < msg.text.split('\n').length - 1 && <br/>}</span>
                ))}
              </div>
              {msg.datos && Object.keys(msg.datos).length > 0 && (
                <div style={s.dataCards}>{renderDataCards(msg.datos)}</div>
              )}
            </div>
          ))}

          {loading && (
            <div style={s.rowBot}>
              <div style={s.botDot}/>
              <div style={{...s.bubbleBot, ...s.typing}}>
                <div style={s.typingDots}>
                  <span style={{...s.dot, animationDelay: '0s'}}/>
                  <span style={{...s.dot, animationDelay: '0.15s'}}/>
                  <span style={{...s.dot, animationDelay: '0.3s'}}/>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input area — Apple iMessage style */}
        <div style={s.inputArea}>
          {messages.length > 0 && (
            <div style={s.quickRow}>
              {SHORTCUTS.slice(0, 4).map((sc, i) => (
                <button key={i} style={s.quickBtn} onClick={() => send(sc.text)}>
                  {sc.emoji}
                </button>
              ))}
            </div>
          )}
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
            <button
              style={{...s.sendBtn, ...(input.trim() && !loading ? s.sendActive : {})}}
              onClick={() => send(input)}
              disabled={loading || !input.trim()}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes typing {
          0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
          30% { opacity: 1; transform: scale(1); }
        }
        @media (max-width: 480px) {
          .portal-card { margin: 0 !important; border-radius: 0 !important; min-height: 100vh !important; max-height: 100vh !important; }
        }
      `}</style>
    </div>
  );
}

function renderDataCards(datos) {
  const cards = [];
  if (datos.buscar_huecos_recuperacion?.huecos?.length > 0) {
    datos.buscar_huecos_recuperacion.huecos.slice(0, 5).forEach((h, i) => {
      cards.push(
        <div key={`hueco-${i}`} style={s.dataCard}>
          <div style={s.cardRow}>
            <span style={s.cardIcon}>🗓</span>
            <div>
              <div style={s.cardTitle}>{h.dia} {h.fecha}</div>
              <div style={s.cardSub}>{h.hora} · {h.grupo}</div>
            </div>
          </div>
          <div style={s.cardBadge}>{h.plazas_libres} plazas</div>
        </div>
      );
    });
  }
  if (datos.ver_facturas?.facturas?.length > 0) {
    datos.ver_facturas.facturas.forEach((f, i) => {
      cards.push(
        <div key={`fact-${i}`} style={s.dataCard}>
          <div style={s.cardRow}>
            <span style={s.cardIcon}>📄</span>
            <div>
              <div style={s.cardTitle}>{f.numero}</div>
              <div style={s.cardSub}>{f.fecha} · {f.total.toFixed(2)}€</div>
            </div>
          </div>
          <a href={f.pdf_url} target="_blank" rel="noopener" style={s.cardLink}>PDF</a>
        </div>
      );
    });
  }
  if (datos.ver_proximas_clases?.clases?.length > 0) {
    datos.ver_proximas_clases.clases.slice(0, 5).forEach((c, i) => {
      cards.push(
        <div key={`clase-${i}`} style={s.dataCard}>
          <div style={s.cardRow}>
            <span style={s.cardIcon}>🧘‍♀️</span>
            <div>
              <div style={s.cardTitle}>{c.dia} {c.fecha}</div>
              <div style={s.cardSub}>{c.hora} · {c.grupo}</div>
            </div>
          </div>
          <div style={{...s.cardBadge, background: c.estado === 'confirmada' ? '#dcfce7' : '#f3f4f6',
            color: c.estado === 'confirmada' ? '#16a34a' : '#6b7280'}}>{c.estado}</div>
        </div>
      );
    });
  }
  return cards;
}

const s = {
  // Page
  page: {
    minHeight: '100vh', display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
    background: 'linear-gradient(180deg, #f5f5f7 0%, #e8e8ed 100%)',
    padding: '12px 8px',
    fontFamily: "-apple-system, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', sans-serif",
    WebkitFontSmoothing: 'antialiased',
  },
  card: {
    background: '#fff', borderRadius: 24, maxWidth: 440, width: '100%',
    boxShadow: '0 2px 20px rgba(0,0,0,0.06), 0 0 0 0.5px rgba(0,0,0,0.04)',
    marginTop: 8,
    display: 'flex', flexDirection: 'column',
    minHeight: 'calc(100vh - 40px)', maxHeight: 'calc(100vh - 40px)',
    overflow: 'hidden',
  },

  // Header
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '14px 20px',
    background: 'rgba(255,255,255,0.8)',
    backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
    borderBottom: '0.5px solid rgba(0,0,0,0.06)',
    position: 'sticky', top: 0, zIndex: 10,
  },
  headerInner: { display: 'flex', gap: 12, alignItems: 'center' },
  logoMark: {
    width: 36, height: 36, borderRadius: 10,
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  brandName: { fontSize: 15, fontWeight: 600, color: '#1d1d1f', letterSpacing: '-0.01em' },
  brandSub: { fontSize: 11, color: '#86868b', fontWeight: 400 },
  avatar: {
    width: 32, height: 32, borderRadius: 16,
    background: '#f5f5f7', color: '#1d1d1f',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 13, fontWeight: 600,
  },

  // Chat
  chat: {
    flex: 1, overflowY: 'auto', padding: '16px 16px 8px',
    display: 'flex', flexDirection: 'column', gap: 6,
  },

  // Welcome
  welcome: { textAlign: 'center', padding: '48px 16px 24px' },
  welcomeEmoji: { fontSize: 40, marginBottom: 12 },
  welcomeTitle: { fontSize: 22, fontWeight: 600, color: '#1d1d1f', letterSpacing: '-0.02em', marginBottom: 4 },
  welcomeSub: { fontSize: 15, color: '#86868b', marginBottom: 28 },
  grid: {
    display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8,
    maxWidth: 320, margin: '0 auto',
  },
  gridBtn: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
    padding: '14px 8px', background: '#fff', border: '0.5px solid rgba(0,0,0,0.08)',
    borderRadius: 14, cursor: 'pointer', transition: 'all 0.2s cubic-bezier(0.4,0,0.2,1)',
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
  },
  gridEmoji: { fontSize: 22 },
  gridLabel: { fontSize: 11, color: '#1d1d1f', fontWeight: 500, lineHeight: 1.2 },

  // Messages
  rowUser: { display: 'flex', justifyContent: 'flex-end', padding: '2px 0' },
  rowBot: { display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 4, padding: '2px 0' },
  botDot: {
    width: 6, height: 6, borderRadius: 3, background: '#6366f1',
    marginLeft: 4, marginBottom: 2, opacity: 0.4,
  },
  bubbleUser: {
    background: '#007AFF', color: '#fff', padding: '10px 14px',
    borderRadius: '18px 18px 4px 18px', maxWidth: '78%',
    fontSize: 15, lineHeight: 1.45, fontWeight: 400,
  },
  bubbleBot: {
    background: '#f0f0f0', color: '#1d1d1f', padding: '10px 14px',
    borderRadius: '18px 18px 18px 4px', maxWidth: '82%',
    fontSize: 15, lineHeight: 1.45, fontWeight: 400,
  },

  // Typing indicator
  typing: { padding: '12px 18px' },
  typingDots: { display: 'flex', gap: 4, alignItems: 'center' },
  dot: {
    width: 7, height: 7, borderRadius: '50%', background: '#86868b',
    animation: 'typing 1s infinite ease-in-out',
  },

  // Data cards
  dataCards: { display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4, width: '82%' },
  dataCard: {
    background: '#fff', border: '0.5px solid rgba(0,0,0,0.08)',
    borderRadius: 12, padding: '10px 14px',
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
  },
  cardRow: { display: 'flex', gap: 10, alignItems: 'center' },
  cardIcon: { fontSize: 18 },
  cardTitle: { fontSize: 13, fontWeight: 600, color: '#1d1d1f' },
  cardSub: { fontSize: 12, color: '#86868b' },
  cardBadge: {
    fontSize: 11, fontWeight: 500, padding: '3px 8px', borderRadius: 6,
    background: '#dcfce7', color: '#16a34a',
  },
  cardLink: {
    fontSize: 12, fontWeight: 500, color: '#007AFF', textDecoration: 'none',
  },

  // Input
  inputArea: {
    borderTop: '0.5px solid rgba(0,0,0,0.06)',
    background: 'rgba(255,255,255,0.9)',
    backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
  },
  quickRow: {
    display: 'flex', justifyContent: 'center', gap: 10, padding: '10px 16px 4px',
  },
  quickBtn: {
    width: 34, height: 34, borderRadius: 17, border: '0.5px solid rgba(0,0,0,0.08)',
    background: '#f5f5f7', fontSize: 15, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'transform 0.15s',
  },
  inputRow: {
    display: 'flex', gap: 8, padding: '8px 12px 12px', alignItems: 'center',
  },
  input: {
    flex: 1, padding: '10px 16px', border: '0.5px solid rgba(0,0,0,0.1)',
    borderRadius: 20, fontSize: 15, outline: 'none', background: '#f5f5f7',
    color: '#1d1d1f', transition: 'border-color 0.2s',
  },
  sendBtn: {
    width: 36, height: 36, borderRadius: 18, border: 'none',
    background: '#e5e5ea', color: '#86868b', fontSize: 14, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'all 0.2s',
  },
  sendActive: {
    background: '#007AFF', color: '#fff',
  },

  // Error
  errorCard: {
    background: '#fff', borderRadius: 20, padding: 40, maxWidth: 360, width: '100%',
    textAlign: 'center', boxShadow: '0 2px 20px rgba(0,0,0,0.06)',
  },
  errorIcon: {
    width: 48, height: 48, borderRadius: 24, background: '#fee2e2', color: '#dc2626',
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 20, fontWeight: 700, marginBottom: 16,
  },
  errorText: { fontSize: 15, color: '#1d1d1f' },
};
