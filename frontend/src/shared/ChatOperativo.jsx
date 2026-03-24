/**
 * ChatOperativo — Chat Operativo Universal con confirmación de acciones.
 *
 * Flujo:
 * 1. Jesús escribe/habla → POST /cockpit/chat
 * 2. Si respuesta tiene action_plan → mostrar plan con botones Ejecutar/Cancelar
 * 3. Si Jesús confirma → POST /cockpit/confirm → feedback paso a paso
 * 4. Historial visible con burbujas
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import * as api from '../api';
import { fetchApi } from '../context/AppContext';
import Pulse from '../design/Pulse';
import VoicePanel, { speak } from './VoicePanel';

// Iconos por tipo de acción
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

function ActionPlan({ plan, onConfirm, onCancel, executing, results }) {
  return (
    <div className="glass rounded-2xl p-4 border border-[var(--accent-amber)]/30 space-y-3 fade-in">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-bold tracking-widest uppercase text-[var(--accent-amber)]">
          Plan de acciones
        </span>
        {!executing && !results && (
          <span className="text-[10px] text-[var(--text-ghost)] ml-auto">Requiere confirmaci\u00F3n</span>
        )}
      </div>

      <p className="text-sm text-[var(--text-primary)] font-medium">{plan.resumen}</p>

      <div className="space-y-2">
        {plan.pasos.map((paso, i) => {
          const icon = ACTION_ICONS[paso.accion] || '\u{2699}\u{FE0F}';
          const result = results?.[i];
          const statusClass = result
            ? result.estado === 'ok'
              ? 'border-l-green-500 bg-green-500/5'
              : 'border-l-red-500 bg-red-500/5'
            : executing && i < (results?.length || 0)
            ? 'border-l-[var(--accent-indigo)] bg-[var(--accent-indigo)]/5'
            : 'border-l-[var(--border)]';

          return (
            <div key={i} className={`flex items-start gap-3 p-3 rounded-xl border-l-2 ${statusClass} transition-all duration-300`}>
              <span className="text-lg shrink-0">{icon}</span>
              <div className="flex-1 min-w-0">
                <span className="text-sm text-[var(--text-primary)]">{paso.descripcion}</span>
                {result?.estado === 'ok' && (
                  <span className="text-[10px] text-green-400 ml-2">{String.fromCodePoint(0x2705)}</span>
                )}
                {result?.estado === 'error' && (
                  <div className="text-[11px] text-red-400 mt-1">
                    {String.fromCodePoint(0x274C)} {result.error || result.resultado?.error || 'Error'}
                  </div>
                )}
              </div>
              {executing && !result && i === (results?.length || 0) && (
                <Pulse color="amber" size={5} />
              )}
            </div>
          );
        })}
      </div>

      {!executing && !results && (
        <div className="flex gap-2 pt-2">
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold bg-[var(--accent-indigo)] text-white hover:brightness-110 transition-all cursor-pointer border-none active:scale-[0.98]"
          >
            {String.fromCodePoint(0x2705)} Ejecutar
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2.5 rounded-xl text-sm font-medium bg-white/5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/10 transition-all cursor-pointer border border-[var(--border)] active:scale-[0.98]"
          >
            Cancelar
          </button>
        </div>
      )}

      {results && (
        <div className={`text-xs font-semibold pt-1 ${results.every(r => r.estado === 'ok') ? 'text-green-400' : 'text-red-400'}`}>
          {results.every(r => r.estado === 'ok')
            ? `${String.fromCodePoint(0x2705)} ${results.length} ${results.length === 1 ? 'acci\u00F3n ejecutada' : 'acciones ejecutadas'}`
            : `${results.filter(r => r.estado === 'ok').length}/${results.length} completadas`
          }
        </div>
      )}
    </div>
  );
}


function ChatBubble({ role, content, timestamp }) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} fade-in`}>
      <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed
        ${isUser
          ? 'bg-[var(--accent-indigo)]/15 text-[var(--text-primary)] rounded-br-md'
          : 'bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border)] rounded-bl-md'
        }`}
      >
        {content}
        {timestamp && (
          <div className="text-[9px] text-[var(--text-ghost)] mt-1 text-right">{timestamp}</div>
        )}
      </div>
    </div>
  );
}


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
        body: JSON.stringify({
          mensaje: msg,
          modulos_activos: modulosActivos,
          historial,
        }),
      });

      // Aplicar acciones de interfaz
      if (data.acciones && onAcciones) {
        onAcciones(data.acciones);
      }

      // Si hay plan de acciones → mostrar para confirmar
      if (data.action_plan) {
        setPendingPlan(data.action_plan);
        if (data.respuesta) addMessage('assistant', data.respuesta);
      } else if (data.respuesta) {
        addMessage('assistant', data.respuesta);
        speak(data.respuesta);
      }

      if (data.historial) setHistorial(data.historial);
    } catch {
      addMessage('assistant', 'Error de conexi\u00F3n. Prueba otra vez.');
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
        addMessage('assistant', `Hecho. ${data.ejecutados} ${data.ejecutados === 1 ? 'acci\u00F3n completada' : 'acciones completadas'}.`);
        speak('Hecho.');
      } else {
        const ok = data.resultados?.filter(r => r.estado === 'ok').length || 0;
        addMessage('assistant', `${ok} de ${data.total} acciones completadas. Revisa los errores.`);
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
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  // Modo compacto: solo barra de búsqueda
  if (compact && !expanded) {
    return (
      <div className="relative group">
        <input
          ref={inputRef}
          className="w-full glass rounded-2xl px-5 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-ghost)] focus:outline-none focus:border-[var(--border-active)] focus:shadow-[var(--shadow-glow)] transition-all duration-200"
          placeholder="Pregunta lo que necesites..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setExpanded(true)}
          disabled={loading}
        />
        {loading && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <Pulse color="indigo" size={6} />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${compact ? 'fixed inset-x-0 bottom-0 z-50 max-h-[70vh] bg-[var(--bg)] border-t border-[var(--border)] rounded-t-3xl shadow-2xl' : ''}`}>
      {/* Header si es expandido desde compacto */}
      {compact && expanded && (
        <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--border)]">
          <span className="text-xs font-bold tracking-widest uppercase text-[var(--accent-indigo)]">Chat operativo</span>
          <button
            onClick={() => { setExpanded(false); }}
            className="text-[var(--text-ghost)] hover:text-[var(--text-secondary)] text-lg cursor-pointer bg-transparent border-none"
          >
            {String.fromCodePoint(0x2715)}
          </button>
        </div>
      )}

      {/* Mensajes */}
      <div className={`flex-1 overflow-y-auto px-4 py-3 space-y-3 ${compact ? 'max-h-[50vh]' : 'max-h-[400px]'}`}>
        {messages.length === 0 && (
          <div className="text-center py-8 text-[var(--text-ghost)] text-sm">
            Pregunta lo que necesites: cobrar, cancelar, buscar clientes, enviar facturas...
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatBubble key={i} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
        ))}

        {/* Plan de acciones pendiente */}
        {pendingPlan && (
          <ActionPlan
            plan={pendingPlan}
            onConfirm={handleConfirm}
            onCancel={handleCancel}
            executing={executing}
            results={planResults}
          />
        )}

        {loading && !pendingPlan && (
          <div className="flex justify-start fade-in">
            <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-2xl rounded-bl-md px-4 py-3">
              <Pulse color="indigo" size={6} />
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 pb-4 pt-2">
        <div className="flex items-center gap-2">
          <div className="relative flex-1 group">
            <div className="absolute inset-0 rounded-2xl bg-[var(--accent-indigo)] opacity-0 group-focus-within:opacity-[0.06] blur-xl transition-opacity duration-300" />
            <input
              ref={inputRef}
              className="relative w-full glass rounded-2xl px-5 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-ghost)] focus:outline-none focus:border-[var(--border-active)] focus:shadow-[var(--shadow-glow)] transition-all duration-200"
              placeholder="Pregunta lo que necesites..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading || executing}
            />
            {loading && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                <Pulse color="indigo" size={6} />
              </div>
            )}
          </div>
          <VoicePanel onTranscript={handleVoice} />
        </div>
      </div>
    </div>
  );
}
