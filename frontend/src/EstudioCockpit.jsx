import { useState, useEffect, useCallback } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import * as api from './api';
import Calendario from './Calendario';
import PanelWA from './PanelWA';
import FeedEstudio from './FeedEstudio';

const BASE = import.meta.env.VITE_API_URL || '';
const PREFIX = `${BASE}/pilates`;

// ============================================================
// MÓDULOS INLINE
// ============================================================

function AgendaHoy() {
  const [sesiones, setSesiones] = useState([]);
  useEffect(() => { api.getSesionesHoy().then(r => setSesiones(r.sesiones || [])).catch(() => {}); }, []);
  return (
    <div>
      {sesiones.length === 0 && <div style={S.empty}>No hay sesiones hoy</div>}
      {sesiones.map(s => (
        <div key={s.id} style={S.row}>
          <span style={{fontWeight:600}}>{s.hora_inicio?.slice(0,5)}</span>
          <span style={{flex:1, marginLeft:8}}>{s.grupo_nombre || 'Individual'}</span>
          <span style={S.badge}>{s.asistentes_count || 0} alumnos</span>
        </div>
      ))}
    </div>
  );
}

function PagosPendientes() {
  const [cargos, setCargos] = useState([]);
  useEffect(() => { api.getCargos({estado:'pendiente'}).then(r => setCargos(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  const total = cargos.reduce((s, c) => s + parseFloat(c.total || 0), 0);
  return (
    <div>
      {cargos.length === 0 && <div style={S.empty}>Todo al día</div>}
      {cargos.slice(0, 10).map(c => (
        <div key={c.id} style={S.row}>
          <span style={{flex:1}}>{c.cliente_nombre || c.descripcion || c.tipo}</span>
          <span style={{fontWeight:600, color:'var(--red)'}}>{parseFloat(c.total).toFixed(0)}€</span>
        </div>
      ))}
      {total > 0 && <div style={{...S.row, fontWeight:700, borderTop:'1px solid var(--border)', paddingTop:8, marginTop:4}}>
        <span>Total</span><span style={{color:'var(--red)'}}>{total.toFixed(0)}€</span>
      </div>}
    </div>
  );
}

function ResumenMes() {
  const [r, setR] = useState(null);
  useEffect(() => { api.getResumen().then(setR).catch(() => {}); }, []);
  if (!r) return <div style={S.empty}>Cargando...</div>;
  return (
    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:8}}>
      <div style={S.stat}><div style={S.statLabel}>Ingresos</div><div style={{...S.statVal, color:'var(--green)'}}>{r.ingresos?.toFixed(0) || 0}€</div></div>
      <div style={S.stat}><div style={S.statLabel}>Deuda</div><div style={{...S.statVal, color: r.deuda_pendiente_total > 0 ? 'var(--red)':'var(--text)'}}>{r.deuda_pendiente_total?.toFixed(0) || 0}€</div></div>
      <div style={S.stat}><div style={S.statLabel}>Clientes</div><div style={S.statVal}>{r.clientes_activos || 0}</div></div>
      <div style={S.stat}><div style={S.statLabel}>Sesiones mes</div><div style={S.statVal}>{r.sesiones_mes || 0}</div></div>
    </div>
  );
}

function AlertasPanel() {
  const [alertas, setAlertas] = useState([]);
  useEffect(() => { api.getAlertas().then(r => setAlertas(r.alertas || [])).catch(() => {}); }, []);
  return (
    <div>
      {alertas.length === 0 && <div style={S.empty}>Sin alertas activas</div>}
      {alertas.map((a, i) => (
        <div key={i} style={{...S.row, background: a.severidad === 'alta' ? 'rgba(239,68,68,0.1)' : 'transparent'}}>
          <div>
            <div style={{fontWeight:500}}>{a.nombre}</div>
            <div style={{fontSize:11, color:'var(--text-dim)'}}>{a.detalle}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function BuscadorCliente() {
  const [q, setQ] = useState('');
  const [results, setResults] = useState([]);
  useEffect(() => {
    if (q.length < 2) { setResults([]); return; }
    const t = setTimeout(() => { api.buscar(q).then(setResults).catch(() => {}); }, 250);
    return () => clearTimeout(t);
  }, [q]);
  return (
    <div>
      <input style={S.input} placeholder="Nombre, teléfono..." value={q} onChange={e => setQ(e.target.value)} autoFocus />
      {results.map(r => (
        <div key={r.id} style={S.row}>
          <span style={{flex:1}}>{r.nombre} {r.apellidos}</span>
          <span style={{fontSize:11, color:'var(--text-dim)'}}>{r.telefono}</span>
        </div>
      ))}
    </div>
  );
}

function GruposPanel() {
  const [grupos, setGrupos] = useState([]);
  useEffect(() => { api.getGrupos().then(r => setGrupos(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  return (
    <div>
      {grupos.map(g => (
        <div key={g.id} style={S.row}>
          <span style={{flex:1}}>{g.nombre}</span>
          <span style={{fontSize:12}}>{g.inscritos || 0}/{g.capacidad_max || '?'}</span>
        </div>
      ))}
    </div>
  );
}

function VozPanel() {
  const [props, setProps] = useState([]);
  useEffect(() => { api.getPropuestasVoz({estado:'pendiente'}).then(r => setProps(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  return (
    <div>
      {props.length === 0 && <div style={S.empty}>Sin propuestas pendientes</div>}
      {props.slice(0, 5).map(p => (
        <div key={p.id} style={S.row}>
          <div style={{flex:1}}>
            <div style={{fontWeight:500, fontSize:13}}>{p.titulo || p.tipo}</div>
            <div style={{fontSize:11, color:'var(--text-dim)'}}>{p.resumen?.slice(0, 80)}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function EngagementPanel() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(`${PREFIX}/engagement`).then(r => r.json()).then(setData).catch(() => {});
  }, []);
  if (!data) return <div style={S.empty}>Cargando...</div>;
  return (
    <div>
      {data.en_riesgo?.length > 0 && <div style={{fontSize:11, color:'var(--red)', fontWeight:600, marginBottom:4}}>EN RIESGO</div>}
      {data.en_riesgo?.map(r => (
        <div key={r.cliente_id} style={S.row}>
          <span style={{flex:1}}>{r.nombre} {r.apellidos}</span>
          <span style={{fontSize:12, color:'var(--red)'}}>{r.engagement_score}pts</span>
        </div>
      ))}
      {data.top_rachas?.length > 0 && <div style={{fontSize:11, color:'var(--green)', fontWeight:600, marginBottom:4, marginTop:8}}>TOP RACHAS</div>}
      {data.top_rachas?.map(r => (
        <div key={r.cliente_id} style={S.row}>
          <span style={{flex:1}}>{r.nombre}</span>
          <span style={{fontSize:12, color:'var(--green)'}}>{r.racha_actual} sem</span>
        </div>
      ))}
    </div>
  );
}

function FeedInline() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.getFeed({limit: 10}).then(r => setItems(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  const severityColor = { danger:'#ef4444', warning:'#f59e0b', success:'#22c55e', info:'#6366f1' };
  return (
    <div>
      {items.map(f => (
        <div key={f.id} style={{...S.row, borderLeft: `3px solid ${severityColor[f.severidad] || '#6366f1'}`, paddingLeft:8}}>
          <div style={{flex:1}}>
            <div style={{fontSize:13}}>{f.icono} {f.titulo}</div>
            {f.detalle && <div style={{fontSize:11, color:'var(--text-dim)'}}>{f.detalle}</div>}
          </div>
          <span style={{fontSize:10, color:'var(--text-dim)'}}>{timeAgo(f.created_at)}</span>
        </div>
      ))}
    </div>
  );
}

function timeAgo(ts) {
  const diff = (Date.now() - new Date(ts).getTime()) / 60000;
  if (diff < 60) return `${Math.round(diff)}m`;
  if (diff < 1440) return `${Math.round(diff / 60)}h`;
  return `${Math.round(diff / 1440)}d`;
}

function CalendarioSemanal({ onSelectSesion }) {
  return <Calendario onSelectSesion={onSelectSesion || (() => {})} sesionSeleccionadaId={null} />;
}

function Placeholder({ nombre }) {
  return <div style={S.empty}>Módulo "{nombre}" disponible próximamente</div>;
}

const MODULO_COMPONENTS = {
  agenda: AgendaHoy,
  calendario: CalendarioSemanal,
  feed: FeedInline,
  pagos_pendientes: PagosPendientes,
  resumen_mes: ResumenMes,
  alertas: AlertasPanel,
  buscar: BuscadorCliente,
  grupos: GruposPanel,
  voz: VozPanel,
  engagement: EngagementPanel,
  wa: PanelWA,
};

// ============================================================
// COCKPIT PRINCIPAL — con jerarquía visual
// ============================================================

export default function EstudioCockpit() {
  // modulosActivos: [{id: "agenda", rol: "principal"}, {id: "feed", rol: "secundario"}, ...]
  const [contexto, setContexto] = useState(null);
  const [modulosActivos, setModulosActivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chatInput, setChatInput] = useState('');
  const [chatResp, setChatResp] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatHistorial, setChatHistorial] = useState([]);

  useEffect(() => {
    fetch(`${PREFIX}/cockpit`).then(r => r.json()).then(data => {
      setContexto(data);
      // Sugeridos ya vienen con rol
      const sugeridos = (data.modulos_sugeridos || []).map(m => ({
        id: m.id,
        rol: m.rol || 'secundario'
      }));
      setModulosActivos(sugeridos.length > 0 ? sugeridos : [{id: 'agenda', rol: 'principal'}]);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  // Guardar config en backend
  const saveConfig = useCallback((modulos) => {
    fetch(`${PREFIX}/cockpit/config`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({modulos}),
    }).catch(() => {});
  }, []);

  // Toggle módulo desde chips
  const toggleModulo = useCallback((id) => {
    setModulosActivos(prev => {
      const existing = prev.find(m => m.id === id);
      let next;
      if (existing) {
        next = prev.filter(m => m.id !== id);
      } else {
        // Si no hay principal, el nuevo es principal. Si ya hay, es secundario.
        const hasPrincipal = prev.some(m => m.rol === 'principal');
        next = [...prev, {id, rol: hasPrincipal ? 'secundario' : 'principal'}];
      }
      saveConfig(next);
      return next;
    });
  }, [saveConfig]);

  // Promover módulo a principal (click en la estrella)
  const promoverPrincipal = useCallback((id) => {
    setModulosActivos(prev => {
      const next = prev.map(m => ({
        ...m,
        rol: m.id === id ? 'principal' : (m.rol === 'principal' ? 'secundario' : m.rol)
      }));
      saveConfig(next);
      return next;
    });
  }, [saveConfig]);

  const removeModulo = useCallback((id) => {
    setModulosActivos(prev => {
      const next = prev.filter(m => m.id !== id);
      saveConfig(next);
      return next;
    });
  }, [saveConfig]);

  // Chat conversacional
  const enviarChat = useCallback(async () => {
    const msg = chatInput.trim();
    if (!msg || chatLoading) return;
    setChatLoading(true);
    setChatInput('');
    setChatResp('');
    try {
      const resp = await fetch(`${PREFIX}/cockpit/chat`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          mensaje: msg,
          modulos_activos: modulosActivos,
          historial: chatHistorial,
        }),
      });
      const data = await resp.json();

      if (data.acciones) {
        setModulosActivos(prev => {
          let next = [...prev];

          // Desmontar todos
          if (data.acciones.desmontar_todos) next = [];

          // Desmontar específicos
          if (data.acciones.desmontar?.length) {
            next = next.filter(m => !data.acciones.desmontar.includes(m.id));
          }

          // Montar nuevos con sus roles
          if (data.acciones.montar?.length) {
            for (const nuevo of data.acciones.montar) {
              const id = nuevo.id || nuevo;
              const rol = nuevo.rol || 'secundario';
              // Si viene un nuevo principal, degradar el anterior
              if (rol === 'principal') {
                next = next.map(m => m.rol === 'principal' ? {...m, rol: 'secundario'} : m);
              }
              // Quitar si ya existía (para actualizar rol)
              next = next.filter(m => m.id !== id);
              next.push({id, rol});
            }
          }

          saveConfig(next);
          return next;
        });
      }
      if (data.respuesta) setChatResp(data.respuesta);
      if (data.historial) setChatHistorial(data.historial);
    } catch (e) {
      setChatResp('Error de conexión.');
    }
    setChatLoading(false);
  }, [chatInput, chatLoading, modulosActivos, chatHistorial, saveConfig]);

  if (loading) return <div style={{...S.container, justifyContent:'center', alignItems:'center'}}>
    <div style={{color:'var(--text-dim)'}}>Cargando cockpit...</div>
  </div>;

  const allModulos = contexto?.modulos_disponibles || [];
  const activosIds = new Set(modulosActivos.map(m => m.id));
  const sugeridosIds = new Set((contexto?.modulos_sugeridos || []).map(m => m.id));

  // Separar por rol para renderizar en orden
  const principal = modulosActivos.find(m => m.rol === 'principal');
  const secundarios = modulosActivos.filter(m => m.rol === 'secundario');
  const compactos = modulosActivos.filter(m => m.rol === 'compacto');

  return (
    <div style={S.container}>
      <Toaster position="top-right" toastOptions={{
        style: { background:'#1a1d27', color:'#e4e4e7', border:'1px solid #2a2e3a' }
      }} />

      {/* HEADER */}
      <div style={S.header}>
        <div style={S.saludo}>{contexto?.saludo || 'Buenos días.'}</div>
        <div style={S.chatBox}>
          <input
            style={S.chatInput}
            placeholder="¿Qué necesitas hoy?"
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && enviarChat()}
            disabled={chatLoading}
          />
          <button style={S.chatBtn} onClick={enviarChat} disabled={chatLoading}>
            {chatLoading ? '...' : '→'}
          </button>
        </div>
        {chatResp && <div style={S.chatResp}>{chatResp}</div>}
      </div>

      {/* CHIPS */}
      <div style={S.chips}>
        {allModulos.map(m => {
          const activo = activosIds.has(m.id);
          const sugerido = sugeridosIds.has(m.id);
          return (
            <button key={m.id}
              style={{...S.chip, ...(activo ? S.chipActivo : {}), ...(sugerido && !activo ? S.chipSugerido : {})}}
              onClick={() => toggleModulo(m.id)}>
              {m.icono} {m.nombre}
            </button>
          );
        })}
      </div>

      {/* LAYOUT JERÁRQUICO */}
      <div style={S.layoutContainer}>

        {/* PRINCIPAL — Grande, ancho completo */}
        {principal && (
          <div style={S.moduloPrincipal}>
            <div style={S.moduloHeaderPrincipal}>
              <span style={{fontSize:15}}>
                {allModulos.find(m => m.id === principal.id)?.icono} {allModulos.find(m => m.id === principal.id)?.nombre}
              </span>
              <div style={{display:'flex', gap:8, alignItems:'center'}}>
                <span style={S.rolBadgePrincipal}>FOCO</span>
                <button style={S.closeBtn} onClick={() => removeModulo(principal.id)}>×</button>
              </div>
            </div>
            <div style={S.moduloBodyPrincipal}>
              {MODULO_COMPONENTS[principal.id]
                ? (() => { const C = MODULO_COMPONENTS[principal.id]; return <C />; })()
                : <Placeholder nombre={allModulos.find(m => m.id === principal.id)?.nombre || principal.id} />
              }
            </div>
          </div>
        )}

        {/* SECUNDARIOS + COMPACTOS — Grid debajo */}
        {(secundarios.length > 0 || compactos.length > 0) && (
          <div style={S.gridSecundario}>
            {/* Secundarios — tamaño normal */}
            {secundarios.map(mod => {
              const info = allModulos.find(m => m.id === mod.id);
              if (!info) return null;
              const Comp = MODULO_COMPONENTS[mod.id];
              return (
                <div key={mod.id} style={S.moduloSecundario}>
                  <div style={S.moduloHeader}>
                    <span>{info.icono} {info.nombre}</span>
                    <div style={{display:'flex', gap:4, alignItems:'center'}}>
                      <button style={S.promoteBtn} onClick={() => promoverPrincipal(mod.id)}
                        title="Poner como foco principal">
                        ↑
                      </button>
                      <button style={S.closeBtn} onClick={() => removeModulo(mod.id)}>×</button>
                    </div>
                  </div>
                  <div style={S.moduloBody}>
                    {Comp ? <Comp /> : <Placeholder nombre={info.nombre} />}
                  </div>
                </div>
              );
            })}

            {/* Compactos — más estrechos, info mínima */}
            {compactos.map(mod => {
              const info = allModulos.find(m => m.id === mod.id);
              if (!info) return null;
              const Comp = MODULO_COMPONENTS[mod.id];
              return (
                <div key={mod.id} style={S.moduloCompacto}>
                  <div style={S.moduloHeaderCompacto}>
                    <span style={{fontSize:12}}>{info.icono} {info.nombre}</span>
                    <button style={S.closeBtn} onClick={() => removeModulo(mod.id)}>×</button>
                  </div>
                  <div style={S.moduloBodyCompacto}>
                    {Comp ? <Comp /> : <Placeholder nombre={info.nombre} />}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {modulosActivos.length === 0 && (
        <div style={{textAlign:'center', padding:40, color:'var(--text-dim)'}}>
          Pulsa un módulo arriba o escribe lo que necesitas
        </div>
      )}
    </div>
  );
}

// ============================================================
// ESTILOS
// ============================================================

const S = {
  container: {
    minHeight: '100vh', background: 'var(--bg, #0f1117)',
    color: 'var(--text, #e4e4e7)', padding: 20,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  header: { marginBottom: 16 },
  saludo: { fontSize: 16, color: 'var(--text, #e4e4e7)', lineHeight: 1.5, marginBottom: 12 },
  chatBox: { display: 'flex', gap: 8, marginBottom: 8 },
  chatInput: {
    flex: 1, background: 'var(--surface, #1a1d27)', border: '1px solid var(--border, #2a2e3a)',
    borderRadius: 10, padding: '10px 14px', color: 'var(--text, #e4e4e7)',
    fontSize: 14, outline: 'none',
  },
  chatBtn: {
    background: 'var(--indigo, #6366f1)', border: 'none', borderRadius: 10,
    padding: '10px 16px', color: '#fff', fontSize: 16, cursor: 'pointer', fontWeight: 700,
  },
  chatResp: {
    fontSize: 13, color: 'var(--text, #e4e4e7)', background: 'var(--surface, #1a1d27)',
    borderRadius: 8, padding: '8px 12px', marginBottom: 4,
    borderLeft: '3px solid var(--indigo, #6366f1)',
  },
  chips: {
    display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 20,
    paddingBottom: 16, borderBottom: '1px solid var(--border, #2a2e3a)',
  },
  chip: {
    background: 'var(--surface, #1a1d27)', border: '1px solid var(--border, #2a2e3a)',
    borderRadius: 20, padding: '5px 12px', fontSize: 12,
    color: 'var(--text-dim, #71717a)', cursor: 'pointer', transition: 'all 0.15s',
  },
  chipActivo: {
    background: 'var(--indigo, #6366f1)', color: '#fff',
    borderColor: 'var(--indigo, #6366f1)',
  },
  chipSugerido: {
    borderColor: 'var(--indigo, #6366f1)', color: 'var(--indigo, #6366f1)',
  },

  // === LAYOUT JERÁRQUICO ===
  layoutContainer: {
    display: 'flex', flexDirection: 'column', gap: 16,
  },

  // PRINCIPAL — Ancho completo, destacado
  moduloPrincipal: {
    background: 'var(--surface, #1a1d27)', borderRadius: 14,
    border: '2px solid var(--indigo, #6366f1)',
    overflow: 'hidden',
    boxShadow: '0 4px 24px rgba(99, 102, 241, 0.15)',
  },
  moduloHeaderPrincipal: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 18px',
    background: 'rgba(99, 102, 241, 0.08)',
    borderBottom: '1px solid var(--border, #2a2e3a)',
    fontWeight: 700,
  },
  moduloBodyPrincipal: {
    padding: 16, minHeight: 200,
  },
  rolBadgePrincipal: {
    fontSize: 9, fontWeight: 700, letterSpacing: '0.08em',
    background: 'var(--indigo, #6366f1)', color: '#fff',
    padding: '2px 8px', borderRadius: 6,
  },

  // SECUNDARIO + COMPACTO — Grid debajo del principal
  gridSecundario: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: 14,
  },

  // SECUNDARIO — Tamaño normal
  moduloSecundario: {
    background: 'var(--surface, #1a1d27)', borderRadius: 12,
    border: '1px solid var(--border, #2a2e3a)', overflow: 'hidden',
  },
  moduloHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '10px 14px', borderBottom: '1px solid var(--border, #2a2e3a)',
    fontSize: 13, fontWeight: 600,
  },
  moduloBody: { padding: 12, maxHeight: 350, overflowY: 'auto' },

  // COMPACTO — Más pequeño, info mínima
  moduloCompacto: {
    background: 'var(--surface, #1a1d27)', borderRadius: 10,
    border: '1px solid var(--border, #2a2e3a)', overflow: 'hidden',
    opacity: 0.9,
  },
  moduloHeaderCompacto: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '6px 10px', borderBottom: '1px solid var(--border, #2a2e3a)',
    fontSize: 11, fontWeight: 600, color: 'var(--text-dim, #71717a)',
  },
  moduloBodyCompacto: { padding: 8, maxHeight: 180, overflowY: 'auto', fontSize: 12 },

  // Botones
  closeBtn: {
    background: 'none', border: 'none', color: 'var(--text-dim, #71717a)',
    fontSize: 18, cursor: 'pointer', padding: '0 4px', lineHeight: 1,
  },
  promoteBtn: {
    background: 'none', border: '1px solid var(--border, #2a2e3a)',
    color: 'var(--text-dim, #71717a)', fontSize: 12, cursor: 'pointer',
    padding: '1px 6px', borderRadius: 4, lineHeight: 1,
  },

  // Shared
  row: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '6px 0', borderBottom: '1px solid var(--border, #2a2e3a)', fontSize: 13,
  },
  badge: {
    fontSize: 11, background: 'var(--bg, #0f1117)', padding: '2px 8px',
    borderRadius: 10, color: 'var(--text-dim, #71717a)',
  },
  stat: { background: 'var(--bg, #0f1117)', borderRadius: 8, padding: 12, textAlign: 'center' },
  statLabel: { fontSize: 11, color: 'var(--text-dim, #71717a)', marginBottom: 4 },
  statVal: { fontSize: 20, fontWeight: 700 },
  empty: { color: 'var(--text-dim, #71717a)', fontSize: 13, padding: '12px 0', textAlign: 'center' },
  input: {
    width: '100%', background: 'var(--bg, #0f1117)', border: '1px solid var(--border, #2a2e3a)',
    borderRadius: 8, padding: '8px 12px', color: 'var(--text, #e4e4e7)',
    fontSize: 13, outline: 'none', marginBottom: 8,
  },
};
