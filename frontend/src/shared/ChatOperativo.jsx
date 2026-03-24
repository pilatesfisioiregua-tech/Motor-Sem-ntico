/**
 * ChatOperativo — iMessage-style Chat with action confirmation.
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { fetchApi } from '../context/AppContext';
import Pulse from '../design/Pulse';
import VoicePanel, { speak } from './VoicePanel';

const ACTION_ICONS = {
  registrar_pago: '\u{1F4B0}',
  cancelar_sesiones_cliente: '\u{274C}',
  generar_facturas: '\u{1F4C4}',
  enviar_whatsapp: '\u{1F4AC}',
  inscribir_en_grupo: '\u{1F465}',
  agendar_sesiones_recurrentes: '\u{1F4C5}',
  buscar_cliente: '\u{1F50D}',
  ver_cliente: '\u{1F464}',
  ver_grupos: '\u{1F465}',
  ver_pagos_cliente: '\u{1F4B3}',
  voz_estrategia: '\u{1F4E2}',
  voz_senales: '\u{1F4E1}',
};

/* ---- Action Plan Card ---- */
function ActionPlan({ plan, onConfirm, onCancel, executing, results }) {
  return (
    <div className="mx-4 my-2 rounded-2xl overflow-hidden anim-scale-in" style={{ background: 'rgba(255, 214, 10, 0.08)', border: '1px solid rgba(255, 214, 10, 0.2)' }}>
      <div className="px-4 pt-3 pb-2">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-bold tracking-wider uppercase" style={{ color: 'var(--accent-amber)' }}>
            Plan de acciones
          </span>
          {!executing && !results && (
            <span className="ios-pill ml-auto" style={{ background: 'rgba(255, 214, 10, 0.15)', color: 'var(--accent-amber)', fontSize: 10 }}>
              Confirmar
            </span>
          )}
        </div>
        <p className="text-[14px] mt-2 font-medium" style={{ color: 'var(--text-primary)' }}>{plan.resumen}</p>
      </div>

      <div className="px-3 pb-2 space-y-1">
        {plan.pasos.map((paso, i) => {
          const icon = ACTION_ICONS[paso.accion] || '\u{2699}\u{FE0F}';
          const result = results?.[i];
          const bg = result
            ? result.estado === 'ok' ? 'rgba(48, 209, 88, 0.08)' : 'rgba(255, 69, 58, 0.08)'
            : 'transparent';
          const border = result
            ? result.estado === 'ok' ? 'rgba(48, 209, 88, 0.25)' : 'rgba(255, 69, 58, 0.25)'
            : 'var(--separator)';

          return (
            <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all" style={{ background: bg, borderLeft: `2px solid ${border}` }}>
              <span className="text-base shrink-0 emoji-icon">{icon}</span>
              <span className="flex-1 text-[13px]" style={{ color: 'var(--text-primary)' }}>{paso.descripcion}</span>
              {result?.estado === 'ok' && <span className="text-[var(--accent-green)] text-sm">{String.fromCodePoint(0x2705)}</span>}
              {result?.estado === 'error' && <span className="text-[var(--accent-red)] text-[11px]">{String.fromCodePoint(0x274C)}</span>}
              {executing && !result && i === (results?.length || 0) && <Pulse color="amber" size={5} />}
            </div>
          );
        })}
      </div>

      {!executing && !results && (
        <div className="flex gap-2 px-4 pb-4 pt-2">
          <button onClick={onConfirm} className="ios-btn ios-btn-primary flex-1 text-[14px] py-2.5">
            Ejecutar
          </button>
          <button onClick={onCancel} className="ios-btn ios-btn-secondary py-2.5 text-[14px]">
            Cancelar
          </button>
        </div>
      )}

      {results && (
        <div className="px-4 pb-3">
          <span className="text-[12px] font-semibold" style={{ color: results.every(r => r.estado === 'ok') ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {results.every(r => r.estado === 'ok')
              ? `${String.fromCodePoint(0x2705)} ${results.length} completada${results.length > 1 ? 's' : ''}`
              : `${results.filter(r => r.estado === 'ok').length}/${results.length} completadas`
            }
          </span>
        </div>
      )}
    </div>
  );
}

/* ---- iMessage Bubble ---- */
function ChatBubble({ role, content, timestamp }) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4 anim-fade-in`}>
      <div
        className="max-w-[82%] px-3.5 py-2 text-[15px] leading-[1.35]"
        style={{
          background: isUser ? 'var(--accent-blue)' : 'var(--bg-elevated)',
          color: isUser ? '#fff' : 'var(--text-primary)',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
        }}
      >
        {content}
        {timestamp && (
          <div className="text-[10px] mt-1 text-right" style={{ opacity: 0.5 }}>{timestamp}</div>
        )}
      </div>
    </div>
  );
}

/* ---- Main Chat Component ---- */
export default function ChatOperativo({ modulosActivos, onAcciones, onSaveConfig, compact = false }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historial, setHistorial] = useState([]);
  const [pendingPlan, setPendingPlan] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [planResults, setPlanResults] = useState(null);
  const [expanded, setExpanded] = useState(!compact);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pendingPlan, planResults]);

  const addMessage = useCallback((role, content) => {
    const ts = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role, content, timestamp: ts }]);
  }, []);

  const handleSend = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    setLoading(true);
    setInput('');
    setPendingPlan(null);
    setPlanResults(null);
    addMessage('user', msg);

    try {
      const data = await fetchApi('/pilates/cockpit/chat', {
        method: 'POST',
        body: JSON.stringify({ mensaje: msg, modulos_activos: modulosActivos, historial }),
      });

      if (data.acciones && onAcciones) onAcciones(data.acciones);

      if (data.action_plan) {
        setPendingPlan(data.action_plan);
        if (data.respuesta) addMessage('assistant', data.respuesta);
      } else if (data.respuesta) {
        addMessage('assistant', data.respuesta);
        speak(data.respuesta);
      }

      if (data.historial) setHistorial(data.historial);
    } catch {
      addMessage('assistant', 'Error de conexi\u00F3n.');
    }
    setLoading(false);
  }, [input, loading, modulosActivos, historial, addMessage, onAcciones]);

  const handleConfirm = useCallback(async () => {
    if (!pendingPlan || executing) return;
    setExecuting(true);
    setPlanResults([]);

    try {
      const data = await fetchApi('/pilates/cockpit/confirm', {
        method: 'POST',
        body: JSON.stringify({ pasos: pendingPlan.pasos }),
      });

      setPlanResults(data.resultados || []);
      if (data.todos_ok) {
        addMessage('assistant', `Hecho. ${data.ejecutados} acci\u00F3n${data.ejecutados > 1 ? 'es' : ''} completada${data.ejecutados > 1 ? 's' : ''}.`);
        speak('Hecho.');
      } else {
        const ok = data.resultados?.filter(r => r.estado === 'ok').length || 0;
        addMessage('assistant', `${ok} de ${data.total} completadas.`);
      }
    } catch {
      addMessage('assistant', 'Error ejecutando el plan.');
    }
    setExecuting(false);
  }, [pendingPlan, executing, addMessage]);

  const handleCancel = useCallback(() => {
    setPendingPlan(null);
    setPlanResults(null);
    addMessage('assistant', 'Plan cancelado.');
  }, [addMessage]);

  const handleVoice = useCallback((text) => {
    setInput(text);
    setTimeout(() => handleSend(text), 100);
  }, [handleSend]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }, [handleSend]);

  const showChat = expanded || messages.length > 0 || loading || pendingPlan;

  return (
    <div className="flex flex-col">
      {/* iOS-style search/input bar */}
      <div className="px-4 pb-2">
        <div className="flex items-center gap-2">
          <div className="ios-search flex-1">
            <svg width="16" height="16" fill="none" stroke="rgba(235,235,245,0.3)" strokeWidth="1.5">
              <circle cx="7" cy="7" r="5.5" /><path d="m11 11 3.5 3.5" />
            </svg>
            <input
              ref={inputRef}
              placeholder="Pregunta lo que necesites..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading || executing}
              onFocus={() => setExpanded(true)}
            />
            {loading && <Pulse color="blue" size={5} />}
          </div>
          <VoicePanel onTranscript={handleVoice} />
        </div>
      </div>

      {/* Chat sheet — slides up from below input */}
      {showChat && (
        <div className="mx-4 rounded-2xl overflow-hidden anim-fade-in" style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--separator)' }}>
          {/* Handle + close */}
          <div className="flex items-center justify-between px-4 py-2" style={{ borderBottom: '0.5px solid var(--separator)' }}>
            <span className="text-[11px] font-bold tracking-wider uppercase" style={{ color: 'var(--accent-blue)' }}>Chat</span>
            {messages.length > 0 && !loading && !pendingPlan && (
              <button
                onClick={() => { setExpanded(false); setMessages([]); setPendingPlan(null); setPlanResults(null); }}
                className="text-[13px] font-medium bg-transparent border-none cursor-pointer"
                style={{ color: 'var(--accent-blue)' }}
              >
                Cerrar
              </button>
            )}
          </div>

          {/* Messages */}
          <div className="overflow-y-auto py-3 space-y-2" style={{ maxHeight: 320 }}>
            {messages.map((msg, i) => (
              <ChatBubble key={i} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
            ))}

            {pendingPlan && (
              <ActionPlan plan={pendingPlan} onConfirm={handleConfirm} onCancel={handleCancel} executing={executing} results={planResults} />
            )}

            {loading && !pendingPlan && (
              <div className="flex justify-start px-4 anim-fade-in">
                <div className="px-4 py-3 rounded-2xl" style={{ background: 'var(--bg-elevated)' }}>
                  <Pulse color="blue" size={6} />
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}
