import { useState, useEffect, useCallback } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import * as api from './api';
import { fetchApi } from './context/AppContext';
import Calendario from './Calendario';
import PanelWA from './PanelWA';
import Card from './design/Card';
import Metric from './design/Metric';
import LensBar from './design/LensBar';
import AgentBadge from './design/AgentBadge';
import SignalFlow from './design/SignalFlow';
import ConflictLine from './design/ConflictLine';
import Pulse from './design/Pulse';
import VoicePanel, { speak } from './shared/VoicePanel';
import ChatOperativo from './shared/ChatOperativo';
import { CAPAS as CAPAS_DEFAULT } from './design/theme';

// ============================================================
// UTILITY
// ============================================================
function timeAgo(ts) {
  if (!ts) return '';
  const diff = (Date.now() - new Date(ts).getTime()) / 60000;
  if (diff < 60) return `${Math.round(diff)}m`;
  if (diff < 1440) return `${Math.round(diff / 60)}h`;
  return `${Math.round(diff / 1440)}d`;
}

// ============================================================
// QUICK BRIEF — iOS-native summary cards
// ============================================================
function QuickBrief() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getSesionesHoy().catch(() => ({ sesiones: [] })),
      api.getCargos({ estado: 'pendiente' }).catch(() => []),
      api.getAlertas().catch(() => ({ alertas: [] })),
      api.getResumen().catch(() => ({})),
      fetchApi('/pilates/wa/recientes').catch(() => ({ mensajes: [] })),
      fetchApi('/pilates/engagement').catch(() => ({})),
    ]).then(([sesiones, cargos, alertas, resumen, wa, engagement]) => {
      const cargosList = Array.isArray(cargos) ? cargos : [];
      const ahora = new Date();
      const horaActual = ahora.getHours() * 60 + ahora.getMinutes();
      const sesionesHoy = sesiones.sesiones || [];
      const siguiente = sesionesHoy.find(s => {
        if (!s.hora_inicio) return false;
        const [h, m] = s.hora_inicio.split(':').map(Number);
        return h * 60 + m > horaActual;
      });

      setData({
        siguiente,
        totalSesiones: sesionesHoy.length,
        sesiones: sesionesHoy,
        cargos: cargosList.slice(0, 5),
        totalDeuda: cargosList.reduce((s, c) => s + parseFloat(c.total || 0), 0),
        alertas: (alertas.alertas || []).filter(a => a.severidad === 'alta').slice(0, 3),
        wa: (wa.mensajes || []).slice(0, 4),
        resumen,
        enRiesgo: engagement.en_riesgo || [],
        topRachas: engagement.top_rachas || [],
      });
      setLoading(false);
    });
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center py-16">
      <Pulse color="blue" size={8} />
    </div>
  );
  if (!data) return null;

  const minutosSiguiente = data.siguiente?.hora_inicio
    ? (() => {
        const [h, m] = data.siguiente.hora_inicio.split(':').map(Number);
        const ahora = new Date();
        return (h * 60 + m) - (ahora.getHours() * 60 + ahora.getMinutes());
      })()
    : null;

  return (
    <div className="space-y-4 pb-4 anim-fade-in">
      {/* NEXT CLASS — Hero card */}
      {data.siguiente && (
        <div className="ios-card anim-slide-up" style={{ background: 'linear-gradient(135deg, rgba(10, 132, 255, 0.15) 0%, rgba(94, 92, 230, 0.1) 100%)' }}>
          <div className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="ios-caption font-semibold uppercase tracking-wider" style={{ color: 'var(--accent-blue)' }}>Siguiente clase</span>
              {minutosSiguiente !== null && (
                <span className="ios-pill" style={{ background: 'rgba(255, 214, 10, 0.15)', color: 'var(--accent-amber)' }}>
                  en {minutosSiguiente} min
                </span>
              )}
            </div>
            <div className="ios-large-title" style={{ fontSize: 28 }}>
              {data.siguiente.hora_inicio?.slice(0, 5)}
            </div>
            <div className="ios-body mt-1" style={{ color: 'var(--text-secondary)' }}>
              {data.siguiente.grupo_nombre || 'Individual'} \u00B7 {data.siguiente.asistentes_count || 0} alumnos
            </div>
          </div>
        </div>
      )}

      {/* KPI RING — iOS Health style */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { val: data.totalSesiones, label: 'Sesiones', color: 'var(--accent-blue)' },
          { val: data.resumen?.clientes_activos || 0, label: 'Clientes', color: 'var(--accent-green)' },
          { val: data.totalDeuda > 0 ? `${data.totalDeuda.toFixed(0)}\u20AC` : '\u2713', label: 'Deuda', color: data.totalDeuda > 0 ? 'var(--accent-red)' : 'var(--accent-green)' },
          { val: data.resumen?.ingresos ? `${(data.resumen.ingresos / 1000).toFixed(1)}k` : '0', label: 'Mes', color: 'var(--accent-violet)' },
        ].map((kpi, i) => (
          <div key={i} className={`ios-card p-3 text-center anim-fade-in anim-stagger-${i + 1}`}>
            <div className="text-[22px] font-bold tabular-nums" style={{ color: kpi.color }}>{kpi.val}</div>
            <div className="text-[10px] font-medium mt-1" style={{ color: 'var(--text-tertiary)' }}>{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* TODAY'S AGENDA */}
      {data.sesiones.length > 0 && (
        <div className="ios-card anim-fade-in anim-stagger-3">
          <div className="px-4 pt-4 pb-2">
            <span className="ios-headline" style={{ color: 'var(--text-primary)' }}>Agenda de hoy</span>
          </div>
          <div>
            {data.sesiones.map((s, i) => (
              <div key={s.id || i} className="ios-row">
                <div className="w-12 text-right">
                  <span className="text-[15px] font-semibold tabular-nums" style={{ color: 'var(--text-primary)' }}>
                    {s.hora_inicio?.slice(0, 5)}
                  </span>
                </div>
                <div className="flex-1">
                  <span className="text-[14px]" style={{ color: 'var(--text-primary)' }}>{s.grupo_nombre || 'Individual'}</span>
                </div>
                <span className="ios-pill" style={{ background: 'rgba(118, 118, 128, 0.24)', color: 'var(--text-secondary)', fontSize: 11 }}>
                  {s.asistentes_count || 0} al.
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ALERTS */}
      {data.alertas.length > 0 && (
        <div className="space-y-2 anim-fade-in anim-stagger-4">
          {data.alertas.map((a, i) => (
            <div key={i} className="ios-card" style={{ borderLeft: '3px solid var(--accent-red)' }}>
              <div className="p-4">
                <div className="text-[13px] font-semibold" style={{ color: 'var(--accent-red)' }}>{a.nombre}</div>
                <div className="text-[12px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{a.detalle}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* WA unread */}
      {data.wa.length > 0 && (
        <div className="ios-card anim-fade-in anim-stagger-5">
          <div className="px-4 pt-4 pb-2 flex items-center justify-between">
            <span className="ios-headline" style={{ color: 'var(--text-primary)' }}>WhatsApp</span>
            <span className="ios-pill" style={{ background: 'var(--accent-green)', color: '#fff', fontSize: 11 }}>{data.wa.length}</span>
          </div>
          <div>
            {data.wa.map((m, i) => (
              <div key={i} className="ios-row">
                <div className="w-2 h-2 rounded-full shrink-0" style={{ background: 'var(--accent-green)' }} />
                <span className="text-[14px] font-medium" style={{ color: 'var(--text-primary)' }}>{m.nombre || m.telefono_remitente}</span>
                <span className="flex-1 text-[13px] truncate" style={{ color: 'var(--text-tertiary)' }}>{m.contenido?.slice(0, 40)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ENGAGEMENT */}
      {(data.enRiesgo.length > 0 || data.topRachas.length > 0) && (
        <div className="ios-card anim-fade-in anim-stagger-6">
          <div className="px-4 pt-4 pb-2">
            <span className="ios-headline" style={{ color: 'var(--text-primary)' }}>Engagement</span>
          </div>
          <div>
            {data.enRiesgo.length > 0 && (
              <>
                <div className="px-4 py-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--accent-red)' }}>En riesgo</span>
                </div>
                {data.enRiesgo.slice(0, 3).map(r => (
                  <div key={r.cliente_id} className="ios-row">
                    <span className="flex-1 text-[14px]" style={{ color: 'var(--text-primary)' }}>{r.nombre} {r.apellidos}</span>
                    <span className="text-[13px] font-semibold tabular-nums" style={{ color: 'var(--accent-red)' }}>{r.engagement_score}pts</span>
                  </div>
                ))}
              </>
            )}
            {data.topRachas.length > 0 && (
              <>
                <div className="px-4 py-1 mt-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--accent-green)' }}>Top rachas</span>
                </div>
                {data.topRachas.slice(0, 3).map(r => (
                  <div key={r.cliente_id} className="ios-row">
                    <span className="flex-1 text-[14px]" style={{ color: 'var(--text-primary)' }}>{r.nombre}</span>
                    <span className="text-[13px] font-semibold tabular-nums" style={{ color: 'var(--accent-green)' }}>{r.racha_actual} sem</span>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      )}

      {/* COBROS PENDIENTES */}
      {data.cargos.length > 0 && (
        <div className="ios-card anim-fade-in">
          <div className="px-4 pt-4 pb-2 flex items-center justify-between">
            <span className="ios-headline" style={{ color: 'var(--text-primary)' }}>Cobros pendientes</span>
            <span className="text-[14px] font-bold tabular-nums" style={{ color: 'var(--accent-red)' }}>{data.totalDeuda.toFixed(0)}{'\u20AC'}</span>
          </div>
          <div>
            {data.cargos.map((c, i) => (
              <div key={i} className="ios-row">
                <span className="flex-1 text-[14px]" style={{ color: 'var(--text-primary)' }}>{c.cliente_nombre || c.descripcion}</span>
                <span className="text-[14px] font-semibold tabular-nums" style={{ color: 'var(--accent-red)' }}>{parseFloat(c.total).toFixed(0)}{'\u20AC'}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// MODULE COMPONENTS (iOS-styled)
// ============================================================

function AgendaHoy() {
  const [sesiones, setSesiones] = useState([]);
  useEffect(() => { api.getSesionesHoy().then(r => setSesiones(r.sesiones || [])).catch(() => {}); }, []);
  return (
    <div>
      {sesiones.length === 0 && <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>No hay sesiones hoy</p>}
      {sesiones.map(s => (
        <div key={s.id} className="ios-row">
          <span className="text-[15px] font-semibold tabular-nums w-14 text-right">{s.hora_inicio?.slice(0, 5)}</span>
          <span className="flex-1 text-[14px]" style={{ color: 'var(--text-secondary)' }}>{s.grupo_nombre || 'Individual'}</span>
          <span className="ios-pill" style={{ background: 'rgba(118,118,128,0.24)', color: 'var(--text-secondary)', fontSize: 11 }}>{s.asistentes_count || 0} al.</span>
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
      {cargos.length === 0 && <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Todo al d\u00EDa</p>}
      {cargos.slice(0, 10).map(c => (
        <div key={c.id} className="ios-row">
          <span className="flex-1 text-[14px]">{c.cliente_nombre || c.descripcion || c.tipo}</span>
          <span className="text-[14px] font-semibold tabular-nums" style={{ color: 'var(--accent-red)' }}>{parseFloat(c.total).toFixed(0)}{'\u20AC'}</span>
        </div>
      ))}
      {total > 0 && (
        <div className="flex justify-between px-4 py-3 font-semibold text-[14px]" style={{ borderTop: '0.5px solid var(--separator)' }}>
          <span>Total</span>
          <span style={{ color: 'var(--accent-red)' }}>{total.toFixed(0)}{'\u20AC'}</span>
        </div>
      )}
    </div>
  );
}

function ResumenMes() {
  const [r, setR] = useState(null);
  useEffect(() => { api.getResumen().then(setR).catch(() => {}); }, []);
  if (!r) return <div className="flex justify-center py-6"><Pulse color="blue" size={6} /></div>;
  return (
    <div className="grid grid-cols-2 gap-0">
      <Metric label="Ingresos" value={`${r.ingresos?.toFixed(0) || 0}\u20AC`} color="var(--accent-green)" />
      <Metric label="Deuda" value={`${r.deuda_pendiente_total?.toFixed(0) || 0}\u20AC`} color="var(--accent-red)" />
      <Metric label="Clientes" value={r.clientes_activos || 0} color="var(--accent-blue)" />
      <Metric label="Sesiones" value={r.sesiones_mes || 0} color="var(--accent-violet)" />
    </div>
  );
}

function AlertasPanel() {
  const [alertas, setAlertas] = useState([]);
  useEffect(() => { api.getAlertas().then(r => setAlertas(r.alertas || [])).catch(() => {}); }, []);
  return (
    <div>
      {alertas.length === 0 && <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin alertas activas</p>}
      {alertas.map((a, i) => (
        <div key={i} className="ios-row" style={a.severidad === 'alta' ? { background: 'rgba(255,69,58,0.06)' } : {}}>
          <div className="flex-1">
            <div className="text-[14px] font-medium">{a.nombre}</div>
            <div className="text-[12px]" style={{ color: 'var(--text-tertiary)' }}>{a.detalle}</div>
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
      <div className="px-1 pb-3">
        <div className="ios-search">
          <svg width="16" height="16" fill="none" stroke="rgba(235,235,245,0.3)" strokeWidth="1.5">
            <circle cx="7" cy="7" r="5.5" /><path d="m11 11 3.5 3.5" />
          </svg>
          <input placeholder="Nombre, tel\u00E9fono..." value={q} onChange={e => setQ(e.target.value)} autoFocus />
        </div>
      </div>
      {results.map(r => (
        <div key={r.id} className="ios-row">
          <span className="flex-1 text-[14px]">{r.nombre} {r.apellidos}</span>
          <span className="text-[12px]" style={{ color: 'var(--text-tertiary)' }}>{r.telefono}</span>
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
        <div key={g.id} className="ios-row">
          <span className="flex-1 text-[14px]">{g.nombre}</span>
          <span className="text-[13px] tabular-nums" style={{ color: 'var(--text-secondary)' }}>{g.inscritos || 0}/{g.capacidad_max || '?'}</span>
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
      {props.length === 0 && <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin propuestas pendientes</p>}
      {props.slice(0, 5).map(p => (
        <div key={p.id} className="ios-row">
          <div className="flex-1">
            <div className="text-[14px] font-medium">{p.titulo || p.tipo}</div>
            <div className="text-[12px]" style={{ color: 'var(--text-tertiary)' }}>{p.resumen?.slice(0, 80)}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function EngagementPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchApi('/pilates/engagement').then(setData).catch(() => {}); }, []);
  if (!data) return <div className="flex justify-center py-6"><Pulse color="blue" size={6} /></div>;
  return (
    <div>
      {data.en_riesgo?.length > 0 && (
        <>
          <div className="px-4 py-1"><span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--accent-red)' }}>En riesgo</span></div>
          {data.en_riesgo.map(r => (
            <div key={r.cliente_id} className="ios-row">
              <span className="flex-1 text-[14px]">{r.nombre} {r.apellidos}</span>
              <span className="text-[13px] font-semibold tabular-nums" style={{ color: 'var(--accent-red)' }}>{r.engagement_score}pts</span>
            </div>
          ))}
        </>
      )}
      {data.top_rachas?.length > 0 && (
        <>
          <div className="px-4 py-1 mt-2"><span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--accent-green)' }}>Top rachas</span></div>
          {data.top_rachas.map(r => (
            <div key={r.cliente_id} className="ios-row">
              <span className="flex-1 text-[14px]">{r.nombre}</span>
              <span className="text-[13px] font-semibold tabular-nums" style={{ color: 'var(--accent-green)' }}>{r.racha_actual} sem</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function FeedInline() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.getFeed({limit: 10}).then(r => setItems(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  return (
    <div>
      {items.map(f => (
        <div key={f.id} className="ios-row">
          <span className="text-base emoji-icon shrink-0">{f.icono}</span>
          <div className="flex-1 min-w-0">
            <div className="text-[14px]">{f.titulo}</div>
            {f.detalle && <div className="text-[12px] truncate" style={{ color: 'var(--text-tertiary)' }}>{f.detalle}</div>}
          </div>
          <span className="text-[11px]" style={{ color: 'var(--text-ghost)' }}>{timeAgo(f.created_at)}</span>
        </div>
      ))}
    </div>
  );
}

function PizarraPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getOrganismoPizarra().then(setData).catch(() => {}); }, []);
  if (!data) return <div className="flex justify-center py-6"><Pulse color="violet" size={6} /></div>;
  const entradas = data.entradas || [];
  const porCapa = {};
  for (const e of entradas) { const capa = e.capa || 'otro'; if (!porCapa[capa]) porCapa[capa] = []; porCapa[capa].push(e); }
  const conflictos = entradas.filter(e => e.conflicto_con);
  return (
    <div className="space-y-3 p-1">
      {Object.entries(porCapa).map(([capa, agentes]) => (
        <div key={capa}>
          <div className="text-[11px] font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--text-tertiary)' }}>{capa}</div>
          <div className="flex flex-wrap gap-1.5">
            {agentes.map(a => <AgentBadge key={a.agente} agent={a.agente} status={a.estado} confidence={a.confianza} />)}
          </div>
        </div>
      ))}
      {conflictos.length > 0 && (
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--accent-red)' }}>Conflictos</div>
          {conflictos.map((c, i) => <ConflictLine key={i} from={c.agente} to={c.conflicto_con} description={c.detectando} />)}
        </div>
      )}
    </div>
  );
}

function EstrategiaPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getOrganismoDirector().then(setData).catch(() => {}); }, []);
  if (!data || !data.estrategia_global) return <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin estrategia activa</p>;
  return (
    <div className="space-y-3 p-1">
      {data.estado_sistema && <div className="text-[14px]" style={{ color: 'var(--text-secondary)' }}>{data.estado_sistema}</div>}
      <div className="text-[14px] font-medium">{data.estrategia_global}</div>
      {data.configs?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {data.configs.map((c, i) => (
            <span key={i} className="ios-pill" style={{ background: 'rgba(94,92,230,0.15)', color: 'var(--accent-indigo)' }}>{c.agente || c}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function EvaluacionPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getOrganismoEvaluacion().then(setData).catch(() => {}); }, []);
  if (!data || !data.evaluacion_global) return <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin evaluaci\u00F3n</p>;
  return (
    <div className="space-y-3 p-1">
      {data.delta_lentes && <LensBar salud={data.delta_lentes?.salud || 0.5} sentido={data.delta_lentes?.sentido || 0.5} continuidad={data.delta_lentes?.continuidad || 0.5} />}
      <div className="text-[14px]">{data.evaluacion_global?.conclusion || data.evaluacion_global}</div>
    </div>
  );
}

function VozProactivaPanel() {
  const [props, setProps] = useState([]);
  useEffect(() => { api.getPropuestasVoz({estado:'pendiente'}).then(r => setProps(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  const channelColor = { instagram: 'var(--accent-red)', web: 'var(--accent-cyan)', whatsapp: 'var(--accent-green)', email: 'var(--accent-amber)' };
  return (
    <div>
      {props.length === 0 && <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin propuestas</p>}
      {props.slice(0, 5).map(p => (
        <div key={p.id} className="ios-row">
          <span className="ios-pill text-[10px]" style={{ background: `${channelColor[p.canal] || 'var(--accent-blue)'}22`, color: channelColor[p.canal] || 'var(--accent-blue)' }}>{p.canal}</span>
          <div className="flex-1 min-w-0">
            <div className="text-[14px] font-medium">{p.titulo || p.tipo}</div>
            <div className="text-[12px] truncate" style={{ color: 'var(--text-tertiary)' }}>{p.resumen?.slice(0, 80)}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function FeedCognitivo() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.getFeed({categoria: 'organismo', limit: 10}).then(r => setItems(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  return (
    <div>
      {items.length === 0 && <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin eventos cognitivos</p>}
      {items.map(f => (
        <div key={f.id} className="ios-row">
          <span className="text-base emoji-icon shrink-0">{f.icono}</span>
          <div className="flex-1 min-w-0">
            <div className="text-[14px]">{f.titulo}</div>
            {f.detalle && <div className="text-[12px] truncate" style={{ color: 'var(--text-tertiary)' }}>{f.detalle}</div>}
          </div>
          <span className="text-[11px]" style={{ color: 'var(--text-ghost)' }}>{timeAgo(f.created_at)}</span>
        </div>
      ))}
    </div>
  );
}

function MotorPanel() {
  const [motor, setMotor] = useState(null);
  useEffect(() => { api.getMotorResumen().then(setMotor).catch(() => {}); }, []);
  if (!motor) return <div className="flex justify-center py-6"><Pulse color="blue" size={6} /></div>;
  const pctUsed = motor.presupuesto_restante > 0 ? ((5 - motor.presupuesto_restante) / 5 * 100).toFixed(0) : 100;
  return (
    <div className="p-1 space-y-3">
      <div className="flex justify-between text-[13px]">
        <span style={{ color: 'var(--text-secondary)' }}>Presupuesto semanal</span>
        <span className="font-semibold tabular-nums">${motor.gastado_ciclo?.toFixed(2)} / $5.00</span>
      </div>
      <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: 'rgba(118,118,128,0.24)' }}>
        <div className="h-full rounded-full transition-all duration-500" style={{
          width: `${Math.min(100, pctUsed)}%`,
          background: pctUsed > 80 ? 'var(--accent-red)' : pctUsed > 50 ? 'var(--accent-amber)' : 'var(--accent-green)'
        }} />
      </div>
    </div>
  );
}

function BusPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getOrganismoBus().then(setData).catch(() => {}); }, []);
  if (!data) return <div className="flex justify-center py-6"><Pulse color="blue" size={6} /></div>;
  const raw = Array.isArray(data) ? data : (data.recientes || data.se\u00F1ales || []);
  const signals = raw.slice(0, 15);
  if (signals.length === 0) return <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin se\u00F1ales</p>;
  return <SignalFlow signals={signals} />;
}

function CalendarioSemanal() { return <Calendario onSelectSesion={() => {}} sesionSeleccionadaId={null} />; }

function IdentidadPresenciaPanel() {
  const [identidad, setIdentidad] = useState(null);
  useEffect(() => { api.getIdentidad().then(setIdentidad).catch(() => {}); }, []);
  if (!identidad || !identidad.esencia) return <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin identidad</p>;
  return (
    <div className="space-y-2 p-1">
      <div className="text-[14px] font-semibold">{identidad.esencia}</div>
      <div className="flex flex-wrap gap-1">
        {identidad.valores?.map(v => <span key={v} className="ios-pill" style={{ background: 'rgba(48,209,88,0.15)', color: 'var(--accent-green)', fontSize: 11 }}>{v}</span>)}
      </div>
    </div>
  );
}

function ContenidoPresenciaPanel() {
  const [contenido, setContenido] = useState([]);
  useEffect(() => { api.getContenido({limit: 5}).then(r => setContenido(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  return (
    <div>
      {contenido.length === 0 && <p className="text-[14px] py-4 text-center" style={{ color: 'var(--text-tertiary)' }}>Sin contenido</p>}
      {contenido.map(c => (
        <div key={c.id} className="ios-row">
          <div className="flex-1 min-w-0">
            <div className="text-[14px] font-medium">{c.titulo || 'Sin t\u00EDtulo'}</div>
            <div className="text-[12px] truncate" style={{ color: 'var(--text-tertiary)' }}>{c.cuerpo?.slice(0, 60)}</div>
          </div>
          <span className="ios-pill text-[10px]" style={{ background: 'rgba(118,118,128,0.24)', color: 'var(--text-secondary)' }}>{c.estado}</span>
        </div>
      ))}
    </div>
  );
}

function AutonomiaDashPanel() {
  const [d, setD] = useState(null);
  useEffect(() => { api.getAutonomiaDashboard().then(setD).catch(() => {}); }, []);
  if (!d) return <div className="flex justify-center py-6"><Pulse color="blue" size={6} /></div>;
  return (
    <div>
      {[
        { label: 'Auto (7d)', val: d.auto_7d, color: 'var(--accent-green)' },
        { label: 'Notificaciones', val: d.notificaciones?.length || 0, color: 'var(--accent-cyan)' },
        { label: 'CR1 pendientes', val: d.cr1_pendientes?.length || 0, color: d.cr1_pendientes?.length > 0 ? 'var(--accent-amber)' : 'var(--accent-green)' },
      ].map(item => (
        <div key={item.label} className="ios-row">
          <span className="flex-1 text-[14px]" style={{ color: 'var(--text-secondary)' }}>{item.label}</span>
          <span className="text-[15px] font-semibold tabular-nums" style={{ color: item.color }}>{item.val}</span>
        </div>
      ))}
    </div>
  );
}

function Placeholder({ nombre }) {
  return <p className="text-[14px] py-6 text-center" style={{ color: 'var(--text-tertiary)' }}>M\u00F3dulo \u201C{nombre}\u201D disponible pr\u00F3ximamente</p>;
}

// ============================================================
// MODULE MAP
// ============================================================
const MODULO_COMPONENTS = {
  agenda: AgendaHoy, calendario: CalendarioSemanal, feed: FeedInline,
  pagos_pendientes: PagosPendientes, resumen_mes: ResumenMes, alertas: AlertasPanel,
  buscar: BuscadorCliente, grupos: GruposPanel, voz: VozPanel,
  engagement: EngagementPanel, wa: PanelWA, pizarra: PizarraPanel,
  estrategia: EstrategiaPanel, evaluacion: EvaluacionPanel, feed_cognitivo: FeedCognitivo,
  bus: BusPanel, voz_proactiva: VozProactivaPanel, motor: MotorPanel,
  contenido: ContenidoPresenciaPanel, presencia: IdentidadPresenciaPanel,
  autonomia: AutonomiaDashPanel, quick_brief: QuickBrief,
};

const MODULE_ICONS = {
  agenda: '\u{1F4C5}', calendario: '\u{1F5D3}', feed: '\u{1F514}',
  pagos_pendientes: '\u{1F4B0}', resumen_mes: '\u{1F4CA}', alertas: '\u{26A0}',
  buscar: '\u{1F50D}', grupos: '\u{1F465}', voz: '\u{1F4E2}',
  engagement: '\u{2764}', wa: '\u{1F4AC}', pizarra: '\u{1F4CB}',
  estrategia: '\u{1F3BC}', evaluacion: '\u{1F4CA}', feed_cognitivo: '\u{1F9E0}',
  bus: '\u{1F4E1}', voz_proactiva: '\u{1F4E2}', motor: '\u{2699}',
  contenido: '\u{1F4F1}', presencia: '\u{1F9EC}', autonomia: '\u{1F916}',
};

const MODULE_COLORS = {
  agenda: 'bg-blue-500', calendario: 'bg-indigo-500', feed: 'bg-orange-500',
  pagos_pendientes: 'bg-red-500', resumen_mes: 'bg-green-500', alertas: 'bg-amber-500',
  buscar: 'bg-gray-500', grupos: 'bg-cyan-500', voz: 'bg-violet-500',
  engagement: 'bg-pink-500', wa: 'bg-emerald-500', pizarra: 'bg-violet-600',
  estrategia: 'bg-indigo-600', evaluacion: 'bg-teal-500', feed_cognitivo: 'bg-purple-500',
  bus: 'bg-sky-500', voz_proactiva: 'bg-fuchsia-500', motor: 'bg-slate-500',
  contenido: 'bg-rose-500', presencia: 'bg-lime-600', autonomia: 'bg-zinc-600',
};

// ============================================================
// iOS TAB BAR
// ============================================================
const TAB_CONFIG = [
  { id: 'home', icon: '\u{1F3E0}', label: 'Inicio' },
  { id: 'operativo', icon: '\u{26A1}', label: 'Operativo' },
  { id: 'financiero', icon: '\u{1F4B0}', label: 'Finanzas' },
  { id: 'cognitivo', icon: '\u{1F9E0}', label: 'Cognitivo' },
  { id: 'mas', icon: '\u{2699}', label: 'M\u00E1s' },
];

// ============================================================
// MAIN COCKPIT
// ============================================================
export default function EstudioCockpit() {
  const [contexto, setContexto] = useState(null);
  const [modulosActivos, setModulosActivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lentes, setLentes] = useState(null);
  const [capas, setCapas] = useState(CAPAS_DEFAULT);
  const [activeTab, setActiveTab] = useState('home');
  const [showModulePicker, setShowModulePicker] = useState(false);

  useEffect(() => {
    fetchApi('/pilates/cockpit').then(data => {
      setContexto(data);
      const sugeridos = (data.modulos_sugeridos || []).map(m => ({ id: m.id, rol: m.rol || 'secundario' }));
      setModulosActivos(sugeridos.length > 0 ? sugeridos : []);
      setLoading(false);
    }).catch(() => setLoading(false));

    fetchApi('/pilates/organismo/evaluacion').then(data => {
      if (data.delta_lentes) setLentes(data.delta_lentes);
    }).catch(() => {});

    fetchApi('/pilates/pizarra/interfaz').then(data => {
      if (data.capas) {
        const merged = { ...CAPAS_DEFAULT };
        for (const [key, serverCapa] of Object.entries(data.capas)) {
          if (merged[key]) merged[key] = { ...merged[key], modulos: serverCapa.modulos || merged[key].modulos };
        }
        setCapas(merged);
      }
    }).catch(() => {});
  }, []);

  const saveConfig = useCallback((modulos) => {
    fetchApi('/pilates/cockpit/config', { method: 'POST', body: JSON.stringify({modulos}) }).catch(() => {});
  }, []);

  const toggleModulo = useCallback((id) => {
    setModulosActivos(prev => {
      const existing = prev.find(m => m.id === id);
      let next;
      if (existing) { next = prev.filter(m => m.id !== id); }
      else {
        const hasPrincipal = prev.some(m => m.rol === 'principal');
        next = [...prev, {id, rol: hasPrincipal ? 'secundario' : 'principal'}];
      }
      saveConfig(next);
      return next;
    });
    setActiveTab('home');
  }, [saveConfig]);

  const handleChatAcciones = useCallback((acciones) => {
    if (!acciones) return;
    setModulosActivos(prev => {
      let next = [...prev];
      if (acciones.desmontar_todos) next = [];
      if (acciones.desmontar?.length) next = next.filter(m => !acciones.desmontar.includes(m.id));
      if (acciones.montar?.length) {
        for (const nuevo of acciones.montar) {
          const nid = nuevo.id || nuevo;
          const rol = nuevo.rol || 'secundario';
          if (rol === 'principal') next = next.map(m => m.rol === 'principal' ? {...m, rol: 'secundario'} : m);
          next = next.filter(m => m.id !== nid);
          next.push({id: nid, rol});
        }
      }
      saveConfig(next);
      return next;
    });
  }, [saveConfig]);

  // Loading
  if (loading) return (
    <div className="min-h-screen min-h-[100dvh] flex items-center justify-center" style={{ background: 'var(--bg-void)' }}>
      <div className="flex flex-col items-center gap-4 anim-fade-in">
        <div className="w-14 h-14 rounded-2xl flex items-center justify-center pulse-ring" style={{ background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-indigo))' }}>
          <span className="text-white text-xl font-bold">O</span>
        </div>
        <span className="text-[14px]" style={{ color: 'var(--text-tertiary)' }}>Preparando tu estudio...</span>
      </div>
    </div>
  );

  const allModulos = contexto?.modulos_disponibles || [];
  const activosIds = new Set(modulosActivos.map(m => m.id));
  const principal = modulosActivos.find(m => m.rol === 'principal');
  const secundarios = modulosActivos.filter(m => m.rol === 'secundario');

  // Filter modules by active tab
  const getTabModulos = () => {
    if (activeTab === 'home') return [];
    if (activeTab === 'mas') return [...(capas.voz?.modulos || []), ...(capas.motor?.modulos || []), ...(capas.identidad?.modulos || []), ...(capas.autonomia?.modulos || [])];
    return capas[activeTab]?.modulos || [];
  };

  const tabModulos = getTabModulos();

  return (
    <div className="min-h-screen min-h-[100dvh] flex flex-col" style={{ background: 'var(--bg-void)' }}>
      <Toaster position="top-center" toastOptions={{
        style: { background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '0.5px solid var(--separator)', borderRadius: 14, fontSize: 14 }
      }} />

      {/* iOS NAVBAR */}
      <div className="ios-navbar">
        <div className="flex items-center justify-between px-4 py-2">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-indigo))' }}>
              <span className="text-white text-sm font-bold">O</span>
            </div>
            <div>
              <h1 className="ios-title">{contexto?.saludo || 'Buenos d\u00EDas'}</h1>
              <p className="text-[11px] font-medium" style={{ color: 'var(--text-tertiary)' }}>Authentic Pilates</p>
            </div>
          </div>
          {lentes && <LensBar salud={lentes.salud || 0.5} sentido={lentes.sentido || 0.5} continuidad={lentes.continuidad || 0.5} compact />}
        </div>

        {/* Chat Operativo */}
        <ChatOperativo modulosActivos={modulosActivos} onAcciones={handleChatAcciones} onSaveConfig={saveConfig} compact />
      </div>

      {/* CONTENT */}
      <div className="flex-1 overflow-y-auto" style={{ paddingBottom: 'calc(60px + max(env(safe-area-inset-bottom), 8px))' }}>
        <div className="px-4 pt-4">

          {/* HOME TAB — QuickBrief + active modules */}
          {activeTab === 'home' && (
            <div className="anim-fade-in">
              {modulosActivos.length === 0 && <QuickBrief />}

              {/* Principal module */}
              {principal && (() => {
                const info = allModulos.find(m => m.id === principal.id);
                const Comp = MODULO_COMPONENTS[principal.id];
                return (
                  <div className="mb-4 anim-scale-in">
                    <Card
                      header={info?.nombre || principal.id}
                      icon={MODULE_ICONS[principal.id]}
                      iconBg={MODULE_COLORS[principal.id] || 'bg-blue-500'}
                      headerRight={<span className="ios-pill" style={{ background: 'var(--accent-blue)', color: '#fff', fontSize: 10 }}>FOCO</span>}
                    >
                      <div className="min-h-[120px]">
                        {Comp ? <Comp /> : <Placeholder nombre={info?.nombre || principal.id} />}
                      </div>
                    </Card>
                  </div>
                );
              })()}

              {/* Secondary modules */}
              {secundarios.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 pb-4">
                  {secundarios.map((mod, idx) => {
                    const info = allModulos.find(m => m.id === mod.id);
                    if (!info) return null;
                    const Comp = MODULO_COMPONENTS[mod.id];
                    return (
                      <div key={mod.id} className={`anim-fade-in anim-stagger-${Math.min(idx + 1, 6)}`}>
                        <Card
                          header={info.nombre}
                          icon={MODULE_ICONS[mod.id]}
                          iconBg={MODULE_COLORS[mod.id] || 'bg-blue-500'}
                          headerRight={
                            <button
                              onClick={() => toggleModulo(mod.id)}
                              className="text-[13px] font-medium bg-transparent border-none cursor-pointer"
                              style={{ color: 'var(--accent-blue)' }}
                            >Cerrar</button>
                          }
                        >
                          <div className="max-h-[300px] overflow-y-auto">
                            {Comp ? <Comp /> : <Placeholder nombre={info.nombre} />}
                          </div>
                        </Card>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* CATEGORY TABS — show module picker */}
          {activeTab !== 'home' && (
            <div className="anim-fade-in">
              <div className="mb-4">
                <h2 className="ios-large-title" style={{ fontSize: 28 }}>
                  {capas[activeTab]?.label || TAB_CONFIG.find(t => t.id === activeTab)?.label || activeTab}
                </h2>
              </div>

              <div className="space-y-3 pb-4">
                {tabModulos.map(id => {
                  const info = allModulos.find(m => m.id === id);
                  const isActive = activosIds.has(id);
                  const Comp = MODULO_COMPONENTS[id];

                  if (isActive && Comp) {
                    return (
                      <div key={id} className="anim-fade-in">
                        <Card
                          header={info?.nombre || id}
                          icon={MODULE_ICONS[id]}
                          iconBg={MODULE_COLORS[id] || 'bg-blue-500'}
                          headerRight={
                            <button
                              onClick={() => toggleModulo(id)}
                              className="text-[13px] font-medium bg-transparent border-none cursor-pointer"
                              style={{ color: 'var(--accent-red)' }}
                            >Quitar</button>
                          }
                        >
                          <div className="max-h-[300px] overflow-y-auto">
                            <Comp />
                          </div>
                        </Card>
                      </div>
                    );
                  }

                  return (
                    <button
                      key={id}
                      onClick={() => toggleModulo(id)}
                      className="w-full ios-card ios-card-interactive"
                      style={{ textAlign: 'left', border: 'none', cursor: 'pointer' }}
                    >
                      <div className="ios-row">
                        <div className={`ios-icon ${MODULE_COLORS[id] || 'bg-blue-500'} text-white`}>
                          <span className="emoji-icon">{MODULE_ICONS[id] || '\u{2699}'}</span>
                        </div>
                        <span className="flex-1 text-[15px] font-medium" style={{ color: 'var(--text-primary)' }}>
                          {info?.nombre || id}
                        </span>
                        <svg width="8" height="14" fill="none" stroke="rgba(235,235,245,0.3)" strokeWidth="2" strokeLinecap="round">
                          <path d="M1 1l6 6-6 6" />
                        </svg>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* iOS TAB BAR */}
      <div className="ios-tabbar">
        {TAB_CONFIG.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`ios-tabbar-item ${activeTab === tab.id ? 'active' : ''}`}
          >
            <span className="tab-icon emoji-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
