import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import * as api from './api';

export default function PanelWA() {
  const [mensajes, setMensajes] = useState([]);
  const [seleccionado, setSeleccionado] = useState(null);
  const [respuesta, setRespuesta] = useState('');
  const [sugerencia, setSugerencia] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMensajes();
    // Poll cada 30s
    const interval = setInterval(loadMensajes, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadMensajes() {
    try {
      const msgs = await api.getMensajesWA({ direccion: 'entrante', limit: 20 });
      setMensajes(msgs);
    } catch (e) { /* silencioso en poll */ }
  }

  async function seleccionar(msg) {
    setSeleccionado(msg);
    if (!msg.leido) {
      await api.marcarLeidoWA(msg.id).catch(() => {});
    }
    // Obtener respuesta sugerida
    if (msg.intencion && msg.intencion !== 'otro') {
      try {
        const sug = await api.getRespuestaSugerida({
          intencion: msg.intencion,
          cliente_id: msg.cliente_id,
          contenido_original: msg.contenido,
        });
        setSugerencia(sug);
        setRespuesta(sug.mensaje || '');
      } catch (e) {
        setSugerencia(null);
        setRespuesta('');
      }
    } else {
      setSugerencia(null);
      setRespuesta('');
    }
  }

  async function enviar() {
    if (!respuesta || !seleccionado) return;
    setLoading(true);
    try {
      await api.enviarMensajeWA({
        telefono: seleccionado.remitente,
        mensaje: respuesta,
        cliente_id: seleccionado.cliente_id,
      });

      // Ejecutar acción si hay
      if (sugerencia?.accion === 'cancelar_sesion' && sugerencia?.accion_datos) {
        toast.success('Respuesta enviada + cancelación procesada');
      } else if (sugerencia?.accion === 'enviar_onboarding') {
        await api.responderLead({
          telefono: seleccionado.remitente,
          nombre: '',
        });
        toast.success('Respuesta + enlace onboarding enviados');
      } else {
        toast.success('Respuesta enviada');
      }

      setSeleccionado(null);
      setRespuesta('');
      setSugerencia(null);
      loadMensajes();
    } catch (e) {
      toast.error(e.message);
    }
    setLoading(false);
  }

  const noLeidos = mensajes.filter(m => !m.leido).length;

  return (
    <div>
      <h3>WhatsApp {noLeidos > 0 && <span style={{
        background: 'var(--red)', color: '#fff', borderRadius: '50%',
        padding: '1px 6px', fontSize: 11, marginLeft: 4
      }}>{noLeidos}</span>}</h3>

      {/* Lista mensajes */}
      <div style={{ maxHeight: 200, overflowY: 'auto', marginBottom: 8 }}>
        {mensajes.slice(0, 10).map(m => (
          <div key={m.id}
            onClick={() => seleccionar(m)}
            style={{
              padding: '6px 8px', borderRadius: 6, cursor: 'pointer', marginBottom: 2,
              background: seleccionado?.id === m.id ? 'var(--surface-hover)' : 'transparent',
              borderLeft: !m.leido ? '3px solid var(--accent)' : '3px solid transparent',
            }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
              <span style={{ fontWeight: m.leido ? 400 : 600 }}>
                {m.nombre ? `${m.nombre} ${m.apellidos || ''}` : m.remitente?.slice(-9)}
              </span>
              <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                {m.intencion && m.intencion !== 'otro' && (
                  <span style={{
                    background: 'var(--surface)', padding: '1px 4px', borderRadius: 3,
                    marginRight: 4,
                  }}>{m.intencion}</span>
                )}
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {m.contenido?.slice(0, 60)}
            </div>
          </div>
        ))}
        {mensajes.length === 0 && (
          <div className="empty" style={{ fontSize: 12, padding: 8 }}>Sin mensajes recientes</div>
        )}
      </div>

      {/* Responder */}
      {seleccionado && (
        <div style={{
          background: 'var(--bg)', borderRadius: 8, padding: 8, marginTop: 4,
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4 }}>
            Respondiendo a {seleccionado.nombre || seleccionado.remitente}
            {sugerencia?.accion && (
              <span style={{ color: 'var(--accent)', marginLeft: 4 }}>
                + {sugerencia.accion}
              </span>
            )}
          </div>
          <textarea
            className="input"
            style={{ minHeight: 50, resize: 'vertical', fontSize: 12 }}
            value={respuesta}
            onChange={e => setRespuesta(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) enviar(); }}
            placeholder="Escribe respuesta... (Ctrl+Enter para enviar)"
          />
          <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
            <button className="btn btn-primary btn-sm" style={{ flex: 1 }}
              onClick={enviar} disabled={loading || !respuesta}>
              {loading ? '...' : 'Enviar'}
            </button>
            <button className="btn btn-secondary btn-sm"
              onClick={() => { setSeleccionado(null); setRespuesta(''); setSugerencia(null); }}>
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Confirmaciones mañana */}
      <button className="btn btn-secondary btn-sm" style={{ width: '100%', marginTop: 8 }}
        onClick={async () => {
          try {
            const r = await api.confirmarManana();
            toast.success(`${r.enviados} confirmaciones enviadas`);
          } catch (e) { toast.error(e.message); }
        }}>
        Enviar confirmaciones mañana
      </button>
    </div>
  );
}
