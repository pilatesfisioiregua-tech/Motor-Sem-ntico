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
import { CAPAS as CAPAS_DEFAULT } from './design/theme';

// ============================================================
// MÓDULOS INLINE — migrados a Tailwind
// ============================================================

// ============================================================
// QUICK BRIEF — Vista optimizada para 10 min entre clases
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
    ]).then(([sesiones, cargos, alertas, resumen, wa]) => {
      const cargosList = Array.isArray(cargos) ? cargos : [];
      const ahora = new Date();
      const horaActual = ahora.getHours() * 60 + ahora.getMinutes();

      // Encontrar siguiente sesión
      const sesionesHoy = sesiones.sesiones || [];
      const siguiente = sesionesHoy.find(s => {
        if (!s.hora_inicio) return false;
        const [h, m] = s.hora_inicio.split(':').map(Number);
        return h * 60 + m > horaActual;
      });

      // Anterior (última que ya pasó)
      const anteriores = sesionesHoy.filter(s => {
        if (!s.hora_inicio) return false;
        const [h, m] = s.hora_inicio.split(':').map(Number);
        return h * 60 + m <= horaActual;
      });
      const anterior = anteriores[anteriores.length - 1];

      setData({
        siguiente,
        anterior,
        totalSesiones: sesionesHoy.length,
        cargos: cargosList.slice(0, 3),
        totalDeuda: cargosList.reduce((s, c) => s + parseFloat(c.total || 0), 0),
        alertas: (alertas.alertas || []).filter(a => a.severidad === 'alta').slice(0, 2),
        wa: (wa.mensajes || []).slice(0, 3),
        resumen,
      });
      setLoading(false);
    });
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center py-12">
      <Pulse color="indigo" size={8} />
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
    <div className="space-y-4 fade-in">
      {/* SIGUIENTE CLASE */}
      {data.siguiente && (
        <div className="glass rounded-2xl p-5 border border-[var(--accent-indigo)]/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold tracking-wider uppercase text-[var(--accent-indigo)]">Siguiente clase</span>
            {minutosSiguiente !== null && (
              <span className="text-xs font-bold text-[var(--accent-amber)] bg-amber-400/10 px-2 py-0.5 rounded-md">
                en {minutosSiguiente} min
              </span>
            )}
          </div>
          <div className="text-lg font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
            {data.siguiente.hora_inicio?.slice(0, 5)} — {data.siguiente.grupo_nombre || 'Individual'}
          </div>
          <div className="text-sm text-[var(--text-secondary)] mt-1">
            {data.siguiente.asistentes_count || 0} alumnos confirmados
          </div>
        </div>
      )}

      {/* URGENTE — alertas + WA sin contestar */}
      {(data.alertas.length > 0 || data.wa.length > 0) && (
        <div className="space-y-2">
          {data.alertas.map((a, i) => (
            <div key={i} className="glass rounded-xl p-4 border-l-3 border-l-[var(--accent-red)]">
              <div className="text-sm font-semibold text-[var(--accent-red)]">{a.nombre}</div>
              <div className="text-xs text-[var(--text-tertiary)] mt-0.5">{a.detalle}</div>
            </div>
          ))}
          {data.wa.length > 0 && (
            <div className="glass rounded-xl p-4">
              <div className="text-xs font-semibold tracking-wider uppercase text-[var(--text-ghost)] mb-2">
                WhatsApp sin leer
              </div>
              {data.wa.map((m, i) => (
                <div key={i} className="flex items-center gap-2 py-1.5 text-sm">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
                  <span className="text-[var(--text-primary)] font-medium">{m.nombre || m.telefono_remitente}</span>
                  <span className="text-[var(--text-tertiary)] truncate flex-1">{m.contenido?.slice(0, 40)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* RESUMEN RÁPIDO — 4 KPIs en fila */}
      <div className="grid grid-cols-4 gap-3">
        <div className="glass rounded-xl p-3 text-center">
          <div className="text-lg font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
            {data.totalSesiones}
          </div>
          <div className="text-[9px] text-[var(--text-ghost)] font-semibold tracking-wider uppercase">Sesiones</div>
        </div>
        <div className="glass rounded-xl p-3 text-center">
          <div className="text-lg font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
            {data.resumen?.clientes_activos || 0}
          </div>
          <div className="text-[9px] text-[var(--text-ghost)] font-semibold tracking-wider uppercase">Clientes</div>
        </div>
        <div className="glass rounded-xl p-3 text-center">
          <div className={`text-lg font-bold ${data.totalDeuda > 0 ? 'text-[var(--accent-red)]' : 'text-[var(--accent-green)]'}`}
               style={{ fontFamily: 'var(--font-display)' }}>
            {data.totalDeuda > 0 ? `${data.totalDeuda.toFixed(0)}\u20AC` : '\u2713'}
          </div>
          <div className="text-[9px] text-[var(--text-ghost)] font-semibold tracking-wider uppercase">Deuda</div>
        </div>
        <div className="glass rounded-xl p-3 text-center">
          <div className="text-lg font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
            {data.resumen?.ingresos ? `${(data.resumen.ingresos / 1000).toFixed(1)}k` : '0'}
          </div>
          <div className="text-[9px] text-[var(--text-ghost)] font-semibold tracking-wider uppercase">Mes</div>
        </div>
      </div>

      {/* CLASE ANTERIOR (si hubo) */}
      {data.anterior && (
        <div className="glass-subtle rounded-xl p-4">
          <div className="text-xs text-[var(--text-ghost)] font-semibold tracking-wider uppercase mb-1">Clase anterior</div>
          <div className="text-sm text-[var(--text-secondary)]">
            {data.anterior.hora_inicio?.slice(0, 5)} — {data.anterior.grupo_nombre || 'Individual'}
            <span className="ml-2 text-[var(--text-ghost)]">({data.anterior.asistentes_count || 0} alumnos)</span>
          </div>
        </div>
      )}

      {/* COBROS PENDIENTES (top 3) */}
      {data.cargos.length > 0 && (
        <div className="glass-subtle rounded-xl p-4">
          <div className="text-xs text-[var(--text-ghost)] font-semibold tracking-wider uppercase mb-2">Cobros pendientes</div>
          {data.cargos.map((c, i) => (
            <div key={i} className="flex justify-between py-1.5 text-sm border-b border-[var(--border)] last:border-0">
              <span className="text-[var(--text-secondary)]">{c.cliente_nombre || c.descripcion}</span>
              <span className="font-semibold text-[var(--accent-red)]">{parseFloat(c.total).toFixed(0)}\u20AC</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AgendaHoy() {
  const [sesiones, setSesiones] = useState([]);
  useEffect(() => { api.getSesionesHoy().then(r => setSesiones(r.sesiones || [])).catch(() => {}); }, []);
  return (
    <div>
      {sesiones.length === 0 && <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">No hay sesiones hoy</p>}
      {sesiones.map(s => (
        <div key={s.id} className="flex justify-between items-center py-1.5 border-b border-[var(--border)] text-sm">
          <span className="font-semibold">{s.hora_inicio?.slice(0,5)}</span>
          <span className="flex-1 ml-2 text-[var(--text-secondary)]">{s.grupo_nombre || 'Individual'}</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--bg-void)] text-[var(--text-tertiary)]">{s.asistentes_count || 0} alumnos</span>
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
      {cargos.length === 0 && <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Todo al dia</p>}
      {cargos.slice(0, 10).map(c => (
        <div key={c.id} className="flex justify-between items-center py-1.5 border-b border-[var(--border)] text-sm">
          <span className="flex-1">{c.cliente_nombre || c.descripcion || c.tipo}</span>
          <span className="font-semibold text-[var(--accent-red)]">{parseFloat(c.total).toFixed(0)}&euro;</span>
        </div>
      ))}
      {total > 0 && (
        <div className="flex justify-between items-center pt-2 mt-1 border-t border-[var(--border)] font-bold text-sm">
          <span>Total</span><span className="text-[var(--accent-red)]">{total.toFixed(0)}&euro;</span>
        </div>
      )}
    </div>
  );
}

function ResumenMes() {
  const [r, setR] = useState(null);
  useEffect(() => { api.getResumen().then(setR).catch(() => {}); }, []);
  if (!r) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Cargando...</p>;
  return (
    <div className="grid grid-cols-2 gap-3">
      <Metric label="Ingresos" value={`${r.ingresos?.toFixed(0) || 0}\u20AC`} size="sm" />
      <Metric label="Deuda" value={`${r.deuda_pendiente_total?.toFixed(0) || 0}\u20AC`} size="sm"
              delta={r.deuda_pendiente_total > 0 ? -1 : 0} />
      <Metric label="Clientes" value={r.clientes_activos || 0} size="sm" />
      <Metric label="Sesiones mes" value={r.sesiones_mes || 0} size="sm" />
    </div>
  );
}

function AlertasPanel() {
  const [alertas, setAlertas] = useState([]);
  useEffect(() => { api.getAlertas().then(r => setAlertas(r.alertas || [])).catch(() => {}); }, []);
  return (
    <div>
      {alertas.length === 0 && <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin alertas activas</p>}
      {alertas.map((a, i) => (
        <div key={i} className={`py-2 border-b border-[var(--border)] text-sm ${a.severidad === 'alta' ? 'bg-red-500/5' : ''}`}>
          <div className="font-medium">{a.nombre}</div>
          <div className="text-xs text-[var(--text-tertiary)]">{a.detalle}</div>
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
      <input className="w-full bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-ghost)] outline-none focus:border-[var(--border-active)] mb-2"
             placeholder="Nombre, telefono..." value={q} onChange={e => setQ(e.target.value)} autoFocus />
      {results.map(r => (
        <div key={r.id} className="flex justify-between items-center py-1.5 border-b border-[var(--border)] text-sm">
          <span className="flex-1">{r.nombre} {r.apellidos}</span>
          <span className="text-xs text-[var(--text-tertiary)]">{r.telefono}</span>
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
        <div key={g.id} className="flex justify-between items-center py-1.5 border-b border-[var(--border)] text-sm">
          <span className="flex-1">{g.nombre}</span>
          <span className="text-xs">{g.inscritos || 0}/{g.capacidad_max || '?'}</span>
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
      {props.length === 0 && <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin propuestas pendientes</p>}
      {props.slice(0, 5).map(p => (
        <div key={p.id} className="py-2 border-b border-[var(--border)]">
          <div className="font-medium text-sm">{p.titulo || p.tipo}</div>
          <div className="text-xs text-[var(--text-tertiary)]">{p.resumen?.slice(0, 80)}</div>
        </div>
      ))}
    </div>
  );
}

function EngagementPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchApi('/pilates/engagement').then(setData).catch(() => {}); }, []);
  if (!data) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Cargando...</p>;
  return (
    <div>
      {data.en_riesgo?.length > 0 && <div className="text-xs text-[var(--accent-red)] font-semibold mb-1">EN RIESGO</div>}
      {data.en_riesgo?.map(r => (
        <div key={r.cliente_id} className="flex justify-between items-center py-1 text-sm">
          <span className="flex-1">{r.nombre} {r.apellidos}</span>
          <span className="text-xs text-[var(--accent-red)]">{r.engagement_score}pts</span>
        </div>
      ))}
      {data.top_rachas?.length > 0 && <div className="text-xs text-[var(--accent-green)] font-semibold mb-1 mt-3">TOP RACHAS</div>}
      {data.top_rachas?.map(r => (
        <div key={r.cliente_id} className="flex justify-between items-center py-1 text-sm">
          <span className="flex-1">{r.nombre}</span>
          <span className="text-xs text-[var(--accent-green)]">{r.racha_actual} sem</span>
        </div>
      ))}
    </div>
  );
}

function FeedInline() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.getFeed({limit: 10}).then(r => setItems(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  const severityColor = { danger:'border-l-red-400', warning:'border-l-amber-400', success:'border-l-emerald-400', info:'border-l-indigo-400' };
  return (
    <div>
      {items.map(f => (
        <div key={f.id} className={`flex items-start gap-2 py-2 border-b border-[var(--border)] border-l-2 pl-2 ${severityColor[f.severidad] || 'border-l-indigo-400'}`}>
          <div className="flex-1">
            <div className="text-sm">{f.icono} {f.titulo}</div>
            {f.detalle && <div className="text-xs text-[var(--text-tertiary)]">{f.detalle}</div>}
          </div>
          <span className="text-[10px] text-[var(--text-ghost)]">{timeAgo(f.created_at)}</span>
        </div>
      ))}
    </div>
  );
}

// === 5 MÓDULOS NUEVOS DEL ORGANISMO ===

function PizarraPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getOrganismoPizarra().then(setData).catch(() => {}); }, []);
  if (!data) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Cargando pizarra...</p>;

  const entradas = data.entradas || [];
  const porCapa = {};
  for (const e of entradas) {
    const capa = e.capa || 'otro';
    if (!porCapa[capa]) porCapa[capa] = [];
    porCapa[capa].push(e);
  }

  const conflictos = entradas.filter(e => e.conflicto_con);

  return (
    <div className="space-y-3">
      {Object.entries(porCapa).map(([capa, agentes]) => (
        <div key={capa}>
          <div className="text-[10px] font-bold tracking-wider uppercase text-[var(--text-ghost)] mb-1.5">{capa}</div>
          <div className="flex flex-wrap gap-1.5">
            {agentes.map(a => (
              <div key={a.agente} className="group relative">
                <AgentBadge agent={a.agente} status={a.estado} confidence={a.confianza} />
                <div className="hidden group-hover:block absolute z-10 top-full left-0 mt-1 p-2 rounded-lg bg-[var(--bg-overlay)] border border-[var(--border)] text-xs max-w-[240px] shadow-[var(--shadow-elevated)]">
                  <div className="text-[var(--text-primary)] mb-1">{a.detectando}</div>
                  {a.accion_propuesta && <div className="text-[var(--text-tertiary)]">{a.accion_propuesta}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      {conflictos.length > 0 && (
        <div>
          <div className="text-[10px] font-bold tracking-wider uppercase text-[var(--accent-red)] mb-1.5">Conflictos</div>
          {conflictos.map((c, i) => (
            <ConflictLine key={i} from={c.agente} to={c.conflicto_con} description={c.detectando} />
          ))}
        </div>
      )}
    </div>
  );
}

function EstrategiaPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getOrganismoDirector().then(setData).catch(() => {}); }, []);
  if (!data || !data.estrategia_global) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin estrategia activa</p>;
  return (
    <div className="space-y-3">
      {data.estado_sistema && (
        <div className="text-sm text-[var(--text-secondary)]">{data.estado_sistema}</div>
      )}
      <div className="text-sm text-[var(--text-primary)] font-medium">{data.estrategia_global}</div>
      {data.configs && data.configs.length > 0 && (
        <div>
          <div className="text-[10px] font-bold tracking-wider uppercase text-[var(--text-ghost)] mb-1.5">Agentes reconfigurados</div>
          <div className="flex flex-wrap gap-1.5">
            {data.configs.map((c, i) => (
              <span key={i} className="px-2 py-1 rounded-full bg-[var(--accent-indigo-glow)] text-xs text-[var(--accent-indigo)] font-medium">
                {c.agente || c}
              </span>
            ))}
          </div>
        </div>
      )}
      {data.fecha && <div className="text-[10px] text-[var(--text-ghost)]">Actualizado: {new Date(data.fecha).toLocaleDateString('es-ES')}</div>}
    </div>
  );
}

function EvaluacionPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getOrganismoEvaluacion().then(setData).catch(() => {}); }, []);
  if (!data || !data.evaluacion_global) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin evaluacion reciente</p>;
  return (
    <div className="space-y-3">
      {data.delta_lentes && (
        <LensBar
          salud={data.delta_lentes?.salud || 0.5}
          sentido={data.delta_lentes?.sentido || 0.5}
          continuidad={data.delta_lentes?.continuidad || 0.5}
        />
      )}
      <div className="text-sm text-[var(--text-primary)]">{data.evaluacion_global?.conclusion || data.evaluacion_global}</div>
      {data.fecha && <div className="text-[10px] text-[var(--text-ghost)]">{new Date(data.fecha).toLocaleDateString('es-ES')}</div>}
    </div>
  );
}

function VozProactivaPanel() {
  const [props, setProps] = useState([]);
  useEffect(() => { api.getPropuestasVoz({estado:'pendiente'}).then(r => setProps(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  const channelColor = { instagram: 'text-rose-400', web: 'text-cyan-400', whatsapp: 'text-emerald-400', email: 'text-amber-400' };
  return (
    <div>
      {props.length === 0 && <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin propuestas pendientes</p>}
      {props.slice(0, 5).map(p => (
        <div key={p.id} className="py-2 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-bold uppercase ${channelColor[p.canal] || 'text-[var(--text-tertiary)]'}`}>{p.canal}</span>
            <span className="text-sm font-medium text-[var(--text-primary)]">{p.titulo || p.tipo}</span>
          </div>
          <div className="text-xs text-[var(--text-tertiary)] mt-0.5">{p.resumen?.slice(0, 100)}</div>
        </div>
      ))}
    </div>
  );
}

function FeedCognitivo() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.getFeed({categoria: 'organismo', limit: 10}).then(r => setItems(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  const severityColor = { danger:'border-l-red-400', warning:'border-l-amber-400', success:'border-l-emerald-400', info:'border-l-violet-400' };
  return (
    <div>
      {items.length === 0 && <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin eventos cognitivos</p>}
      {items.map(f => (
        <div key={f.id} className={`flex items-start gap-2 py-2 border-b border-[var(--border)] border-l-2 pl-2 ${severityColor[f.severidad] || 'border-l-violet-400'}`}>
          <div className="flex-1">
            <div className="text-sm">{f.icono} {f.titulo}</div>
            {f.detalle && <div className="text-xs text-[var(--text-tertiary)]">{f.detalle}</div>}
          </div>
          <span className="text-[10px] text-[var(--text-ghost)]">{timeAgo(f.created_at)}</span>
        </div>
      ))}
    </div>
  );
}

function MotorPanel() {
  const [motor, setMotor] = useState(null);
  useEffect(() => { api.getMotorResumen().then(setMotor).catch(() => {}); }, []);
  if (!motor) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Cargando motor...</p>;
  const pctUsed = motor.presupuesto_restante > 0
    ? ((5 - motor.presupuesto_restante) / 5 * 100).toFixed(0)
    : 100;
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-[var(--text-tertiary)]">Presupuesto semanal</span>
        <span className="text-xs font-mono text-[var(--text-primary)]">
          ${motor.gastado_ciclo?.toFixed(2)} / $5.00
        </span>
      </div>
      <div className="w-full h-2 bg-[var(--bg-void)] rounded-full overflow-hidden mb-3">
        <div
          className={`h-full rounded-full transition-all ${
            pctUsed > 80 ? 'bg-red-500' : pctUsed > 50 ? 'bg-amber-500' : 'bg-emerald-500'
          }`}
          style={{ width: `${Math.min(100, pctUsed)}%` }}
        />
      </div>
      {motor.por_modelo?.length > 0 && (
        <div className="space-y-1">
          {motor.por_modelo.map((m, i) => (
            <div key={i} className="flex justify-between text-xs">
              <span className="text-[var(--text-secondary)]">{m.modelo?.split('/')[1] || m.modelo}</span>
              <span className="font-mono text-[var(--text-tertiary)]">
                {m.calls} calls · ${(parseFloat(m.coste) || 0).toFixed(3)}
                {m.cache_hits > 0 && ` · ${m.cache_hits} cache`}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BusPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getOrganismoBus().then(setData).catch(() => {}); }, []);
  if (!data) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Cargando bus...</p>;
  const raw = Array.isArray(data) ? data : (data.recientes || data.señales || []);
  const signals = raw.slice(0, 15);
  if (signals.length === 0) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin senales recientes</p>;
  return <SignalFlow signals={signals} />;
}

function CalendarioSemanal() {
  return <Calendario onSelectSesion={() => {}} sesionSeleccionadaId={null} />;
}

function Placeholder({ nombre }) {
  return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Modulo &ldquo;{nombre}&rdquo; disponible proximamente</p>;
}

function timeAgo(ts) {
  if (!ts) return '';
  const diff = (Date.now() - new Date(ts).getTime()) / 60000;
  if (diff < 60) return `${Math.round(diff)}m`;
  if (diff < 1440) return `${Math.round(diff / 60)}h`;
  return `${Math.round(diff / 1440)}d`;
}

// ============================================================
// MAPA MODULO → COMPONENTE
// ============================================================

function IdentidadPresenciaPanel() {
  const [identidad, setIdentidad] = useState(null);
  useEffect(() => { api.getIdentidad().then(setIdentidad).catch(() => {}); }, []);
  if (!identidad || !identidad.esencia) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin identidad configurada</p>;
  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold text-[var(--text-primary)]">{identidad.esencia}</div>
      <div className="flex flex-wrap gap-1">
        {identidad.valores?.map(v => (
          <span key={v} className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300">{v}</span>
        ))}
      </div>
      {identidad.anti_identidad?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {identidad.anti_identidad.map(a => (
            <span key={a} className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-300">{a}</span>
          ))}
        </div>
      )}
      <div className="text-xs text-[var(--text-tertiary)] mt-1">{identidad.tono}</div>
    </div>
  );
}

function ContenidoPresenciaPanel() {
  const [contenido, setContenido] = useState([]);
  useEffect(() => { api.getContenido({limit: 5}).then(r => setContenido(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  const estadoColor = { borrador: 'text-gray-400', aprobado: 'text-emerald-400', programado: 'text-cyan-400', publicado: 'text-violet-400' };
  const filtroIcon = { compatible: '\u2705', incompatible: '\u274C', pendiente: '\u23F3' };
  return (
    <div>
      {contenido.length === 0 && <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin contenido generado</p>}
      {contenido.map(c => (
        <div key={c.id} className="py-2 border-b border-[var(--border)]">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">{c.titulo || 'Sin titulo'}</span>
            <span className={`text-[10px] ${estadoColor[c.estado] || 'text-gray-400'}`}>{c.estado}</span>
          </div>
          <div className="text-xs text-[var(--text-tertiary)] truncate">{c.cuerpo?.slice(0, 80)}...</div>
          <div className="flex justify-between items-center mt-0.5">
            <span className="text-[10px] text-[var(--text-ghost)]">{c.canal} · {c.ciclo}</span>
            <span className="text-[10px]">{filtroIcon[c.filtro_identidad] || ''} {c.filtro_identidad}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function AutonomiaDashPanel() {
  const [d, setD] = useState(null);
  useEffect(() => { api.getAutonomiaDashboard().then(setD).catch(() => {}); }, []);
  if (!d) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Cargando...</p>;
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-[var(--text-secondary)]">Auto (7d)</span>
        <span className="font-semibold text-emerald-400">{d.auto_7d}</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-[var(--text-secondary)]">Notificaciones</span>
        <span className="font-semibold text-cyan-400">{d.notificaciones?.length || 0}</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-[var(--text-secondary)]">CR1 pendientes</span>
        <span className={`font-semibold ${d.cr1_pendientes?.length > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>{d.cr1_pendientes?.length || 0}</span>
      </div>
      {d.postmortems?.length > 0 && (
        <div className="mt-2">
          <div className="text-xs text-[var(--text-ghost)] mb-1">Reparaciones recientes:</div>
          {d.postmortems.map((p, i) => (
            <div key={i} className="text-[10px] text-[var(--text-tertiary)] truncate">{p.mensaje?.slice(0, 80)}</div>
          ))}
        </div>
      )}
    </div>
  );
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
  pizarra: PizarraPanel,
  estrategia: EstrategiaPanel,
  evaluacion: EvaluacionPanel,
  feed_cognitivo: FeedCognitivo,
  bus: BusPanel,
  voz_proactiva: VozProactivaPanel,
  motor: MotorPanel,
  contenido: ContenidoPresenciaPanel,
  presencia: IdentidadPresenciaPanel,
  autonomia: AutonomiaDashPanel,
  quick_brief: QuickBrief,
};

// Módulos que necesitan Card variant especial
const MODULO_VARIANTS = {
  pizarra: 'organism',
  estrategia: 'elevated',
  evaluacion: 'default',
  bus: 'default',
};

// ============================================================
// SIDEBAR
// ============================================================

function Sidebar({ modulos, activos, onToggle, capas, visible }) {
  return (
    <aside className={`w-60 min-w-[240px] glass-subtle
                      flex flex-col py-5 overflow-y-auto shrink-0
                      ${visible ? '' : 'hidden md:flex'}
                      fixed md:relative inset-y-0 left-0 z-40 md:z-auto`}>
      <div className="px-5 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--accent-indigo)] to-[var(--accent-violet)] flex items-center justify-center">
            <span className="text-white text-sm font-bold">O</span>
          </div>
          <div>
            <div className="text-sm font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.02em' }}>OMNI-MIND</div>
            <div className="text-[10px] text-[var(--text-ghost)]">Exocortex v3</div>
          </div>
        </div>
      </div>
      {Object.entries(capas).map(([key, capa]) => (
        <div key={key} className="mb-3">
          <div className="px-5 mb-1.5 text-[10px] font-semibold tracking-[0.08em] uppercase text-[var(--text-ghost)]">
            <span className="emoji-icon">{capa.icon}</span> {capa.label}
          </div>
          {capa.modulos.map(id => {
            const mod = modulos.find(m => m.id === id);
            if (!mod) return null;
            const isActive = activos.has(id);
            return (
              <button
                key={id}
                onClick={() => onToggle(id)}
                className={`w-full text-left px-5 py-2 text-[13px] transition-all duration-150 cursor-pointer border-none bg-transparent rounded-lg mx-0
                  ${isActive
                    ? 'text-[var(--accent-indigo)] bg-[var(--accent-indigo-glow)] font-medium'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.03]'
                  }`}
              >
                {mod.icono} {mod.nombre}
              </button>
            );
          })}
        </div>
      ))}
    </aside>
  );
}

// ============================================================
// HEADER
// ============================================================

function HeaderEstudio({ saludo, lentes, chatInput, setChatInput, onChat, chatLoading, chatResp, onVoiceTranscript, onToggleSidebar }) {
  return (
    <header className="glass-subtle sticky top-0 z-20 px-5 md:px-8 pt-[max(env(safe-area-inset-top),12px)] pb-3">
      {/* Fila 1: Saludo + hamburger (mobile) o saludo + lentes + search (desktop) */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 shrink-0">
          <button
            className="md:hidden p-2.5 -ml-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/5 bg-transparent border-none cursor-pointer transition-all active:scale-95"
            onClick={onToggleSidebar}
          >
            <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M3 11h16M3 5.5h16M3 16.5h16" />
            </svg>
          </button>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.02em' }}>
              {saludo}
            </h1>
            <p className="text-[10px] text-[var(--text-ghost)] mt-0.5 font-semibold tracking-widest uppercase">Authentic Pilates</p>
          </div>
        </div>

        {/* Desktop: lentes + search inline */}
        <div className="hidden md:flex items-center gap-4">
          {lentes && (
            <div className="w-72">
              <LensBar salud={lentes.salud || 0.5} sentido={lentes.sentido || 0.5} continuidad={lentes.continuidad || 0.5} />
            </div>
          )}
          <div className="relative group">
            <input
              className="relative w-72 lg:w-80 glass rounded-2xl px-5 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-ghost)] focus:outline-none focus:border-[var(--border-active)] focus:shadow-[var(--shadow-glow)] transition-all duration-200"
              placeholder="Pregunta lo que necesites..."
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && onChat()}
              disabled={chatLoading}
            />
          </div>
          <VoicePanel onTranscript={onVoiceTranscript} />
        </div>
      </div>

      {/* Fila 2 (solo mobile): barra de búsqueda grande */}
      <div className="md:hidden mt-3 flex items-center gap-2">
        <div className="relative flex-1 group">
          <div className="absolute inset-0 rounded-2xl bg-[var(--accent-indigo)] opacity-0 group-focus-within:opacity-[0.06] blur-xl transition-opacity duration-300" />
          <input
            className="relative w-full glass rounded-2xl px-5 py-3.5 text-[15px] text-[var(--text-primary)] placeholder-[var(--text-ghost)] focus:outline-none focus:border-[var(--border-active)] focus:shadow-[var(--shadow-glow)] transition-all duration-200"
            placeholder="Pregunta lo que necesites..."
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && onChat()}
            disabled={chatLoading}
          />
          {chatLoading && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <Pulse color="indigo" size={6} />
            </div>
          )}
        </div>
        <VoicePanel onTranscript={onVoiceTranscript} />
      </div>
    </header>
  );
}

// ============================================================
// COCKPIT PRINCIPAL
// ============================================================

export default function EstudioCockpit() {
  const [contexto, setContexto] = useState(null);
  const [modulosActivos, setModulosActivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chatInput, setChatInput] = useState('');
  const [chatResp, setChatResp] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatHistorial, setChatHistorial] = useState([]);
  const [lentes, setLentes] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);
  const [capas, setCapas] = useState(CAPAS_DEFAULT);
  const [capaActiva, setCapaActiva] = useState('operativo');

  useEffect(() => {
    fetchApi('/pilates/cockpit').then(data => {
      setContexto(data);
      const sugeridos = (data.modulos_sugeridos || []).map(m => ({
        id: m.id, rol: m.rol || 'secundario'
      }));
      setModulosActivos(sugeridos.length > 0 ? sugeridos : []);
      setLoading(false);
    }).catch(() => setLoading(false));

    // Cargar lentes ACD
    fetchApi('/pilates/organismo/evaluacion').then(data => {
      if (data.delta_lentes) setLentes(data.delta_lentes);
    }).catch(() => {});

    // Pizarra interfaz: solo tomar orden de módulos del backend, iconos SIEMPRE del theme.js
    fetchApi('/pilates/pizarra/interfaz').then(data => {
      if (data.capas) {
        const merged = { ...CAPAS_DEFAULT };
        for (const [key, serverCapa] of Object.entries(data.capas)) {
          if (merged[key]) {
            merged[key] = { ...merged[key], modulos: serverCapa.modulos || merged[key].modulos };
          }
        }
        setCapas(merged);
      }
    }).catch(() => {}); // Fallback a CAPAS_DEFAULT
  }, []);

  const saveConfig = useCallback((modulos) => {
    fetchApi('/pilates/cockpit/config', {
      method: 'POST', body: JSON.stringify({modulos}),
    }).catch(() => {});
  }, []);

  const toggleModulo = useCallback((id) => {
    setModulosActivos(prev => {
      const existing = prev.find(m => m.id === id);
      let next;
      if (existing) {
        next = prev.filter(m => m.id !== id);
      } else {
        const hasPrincipal = prev.some(m => m.rol === 'principal');
        next = [...prev, {id, rol: hasPrincipal ? 'secundario' : 'principal'}];
      }
      saveConfig(next);
      return next;
    });
  }, [saveConfig]);

  const enviarChat = useCallback(async () => {
    const msg = chatInput.trim();
    if (!msg || chatLoading) return;
    setChatLoading(true);
    setChatInput('');
    setChatResp('');
    try {
      const data = await fetchApi('/pilates/cockpit/chat', {
        method: 'POST', body: JSON.stringify({ mensaje: msg, modulos_activos: modulosActivos, historial: chatHistorial }),
      });

      if (data.acciones) {
        setModulosActivos(prev => {
          let next = [...prev];
          if (data.acciones.desmontar_todos) next = [];
          if (data.acciones.desmontar?.length) next = next.filter(m => !data.acciones.desmontar.includes(m.id));
          if (data.acciones.montar?.length) {
            for (const nuevo of data.acciones.montar) {
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
      }
      if (data.respuesta) {
        setChatResp(data.respuesta);
        speak(data.respuesta);
      }
      if (data.historial) setChatHistorial(data.historial);
    } catch {
      setChatResp('Error de conexion.');
    }
    setChatLoading(false);
  }, [chatInput, chatLoading, modulosActivos, chatHistorial, saveConfig]);

  const handleVoiceTranscript = useCallback((text) => {
    setChatInput(text);
    setTimeout(() => {
      setChatInput(prev => {
        if (prev === text) {
          // Trigger send
          setChatLoading(true);
          fetchApi('/pilates/cockpit/chat', {
            method: 'POST', body: JSON.stringify({ mensaje: text, modulos_activos: modulosActivos, historial: chatHistorial }),
          }).then(data => {
            if (data.acciones) {
              setModulosActivos(prev2 => {
                let next = [...prev2];
                if (data.acciones.desmontar_todos) next = [];
                if (data.acciones.desmontar?.length) next = next.filter(m => !data.acciones.desmontar.includes(m.id));
                if (data.acciones.montar?.length) {
                  for (const nuevo of data.acciones.montar) {
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
            }
            if (data.respuesta) { setChatResp(data.respuesta); speak(data.respuesta); }
            if (data.historial) setChatHistorial(data.historial);
            setChatLoading(false);
          }).catch(() => { setChatResp('Error de conexion.'); setChatLoading(false); });
        }
        return '';
      });
    }, 100);
  }, [modulosActivos, chatHistorial, saveConfig]);

  if (loading) return (
    <div className="min-h-screen bg-mesh flex items-center justify-center">
      <div className="flex flex-col items-center gap-4 fade-in">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[var(--accent-indigo)] to-[var(--accent-violet)] flex items-center justify-center agent-active">
          <span className="text-white text-lg font-bold">O</span>
        </div>
        <span className="text-sm text-[var(--text-tertiary)]">Preparando tu estudio...</span>
      </div>
    </div>
  );

  const allModulos = contexto?.modulos_disponibles || [];
  const activosIds = new Set(modulosActivos.map(m => m.id));
  const principal = modulosActivos.find(m => m.rol === 'principal');
  const secundarios = modulosActivos.filter(m => m.rol === 'secundario');
  const compactos = modulosActivos.filter(m => m.rol === 'compacto');

  return (
    <div className="min-h-screen bg-mesh flex">
      <Toaster position="top-right" toastOptions={{
        style: { background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border)' }
      }} />

      {/* SIDEBAR — hidden on mobile unless open */}
      <Sidebar modulos={allModulos} activos={activosIds} onToggle={toggleModulo} capas={capas} visible={sidebarOpen} />
      {sidebarOpen && <div className="fixed inset-0 bg-black/50 z-30 md:hidden" onClick={() => setSidebarOpen(false)} />}

      {/* MAIN AREA */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* HEADER */}
        <HeaderEstudio
          saludo={contexto?.saludo || 'Buenos dias.'}
          lentes={lentes}
          chatInput={chatInput}
          setChatInput={setChatInput}
          onChat={enviarChat}
          chatLoading={chatLoading}
          chatResp={chatResp}
          onVoiceTranscript={handleVoiceTranscript}
          onToggleSidebar={() => setSidebarOpen(p => !p)}
        />

        {/* CHAT RESPONSE */}
        {chatResp && (
          <div className="mx-6 mt-3 px-4 py-3 rounded-[var(--radius-md)] bg-[var(--bg-surface)] border-l-2 border-l-[var(--accent-indigo)] text-sm text-[var(--text-primary)] fade-in">
            {chatResp}
          </div>
        )}

        {/* MÓDULOS */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 pb-28 md:pb-6">
          {modulosActivos.length === 0 && (
            <div className="fade-in">
              <QuickBrief />
            </div>
          )}

          {/* PRINCIPAL */}
          {principal && (() => {
            const info = allModulos.find(m => m.id === principal.id);
            const Comp = MODULO_COMPONENTS[principal.id];
            const variant = MODULO_VARIANTS[principal.id] || 'elevated';
            return (
              <div className="mb-6 module-enter">
                <Card variant={variant} glow>
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      <Pulse color="indigo" size={6} />
                      <span className="text-sm font-semibold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
                        {info?.icono} {info?.nombre || principal.id}
                      </span>
                    </div>
                    <span className="text-[9px] font-bold tracking-widest uppercase px-2 py-0.5 rounded-md bg-[var(--accent-indigo)] text-white">FOCO</span>
                  </div>
                  <div className="min-h-[150px]">
                    {Comp ? <Comp /> : <Placeholder nombre={info?.nombre || principal.id} />}
                  </div>
                </Card>
              </div>
            );
          })()}

          {/* SECUNDARIOS + COMPACTOS */}
          {(secundarios.length > 0 || compactos.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {secundarios.map((mod, idx) => {
                const info = allModulos.find(m => m.id === mod.id);
                if (!info) return null;
                const Comp = MODULO_COMPONENTS[mod.id];
                const variant = MODULO_VARIANTS[mod.id] || 'default';
                return (
                  <div key={mod.id} className="module-enter" style={{ animationDelay: `${idx * 60}ms` }}>
                    <Card variant={variant}>
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-sm font-semibold text-[var(--text-primary)]">{info.icono} {info.nombre}</span>
                        <button className="text-[var(--text-ghost)] hover:text-[var(--text-secondary)] transition-colors text-lg leading-none cursor-pointer bg-transparent border-none"
                                onClick={() => toggleModulo(mod.id)}>&times;</button>
                      </div>
                      <div className="max-h-[350px] overflow-y-auto">
                        {Comp ? <Comp /> : <Placeholder nombre={info.nombre} />}
                      </div>
                    </Card>
                  </div>
                );
              })}
              {compactos.map((mod, idx) => {
                const info = allModulos.find(m => m.id === mod.id);
                if (!info) return null;
                const Comp = MODULO_COMPONENTS[mod.id];
                return (
                  <div key={mod.id} className="module-enter" style={{ animationDelay: `${(secundarios.length + idx) * 60}ms` }}>
                    <Card className="opacity-90">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-semibold text-[var(--text-secondary)]">{info.icono} {info.nombre}</span>
                        <button className="text-[var(--text-ghost)] hover:text-[var(--text-secondary)] text-sm leading-none cursor-pointer bg-transparent border-none"
                                onClick={() => toggleModulo(mod.id)}>&times;</button>
                      </div>
                      <div className="max-h-[180px] overflow-y-auto text-xs">
                        {Comp ? <Comp /> : <Placeholder nombre={info.nombre} />}
                      </div>
                    </Card>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Bottom nav mobile */}
      <nav className="fixed bottom-0 left-0 right-0 glass flex justify-around items-end pt-2 pb-[max(8px,env(safe-area-inset-bottom))] md:hidden z-50"
           style={{ borderTop: '0.5px solid rgba(255,255,255,0.08)' }}>
        {Object.entries(capas).map(([key, capa]) => {
          const isActive = capaActiva === key;
          return (
            <button
              key={key}
              onClick={() => setCapaActiva(key)}
              className={`flex flex-col items-center gap-0.5 min-w-[52px] py-1 bg-transparent border-none cursor-pointer transition-all duration-200
                ${isActive ? 'active:scale-95' : 'active:scale-90 opacity-50'}`}
            >
              <span className={`text-2xl emoji-icon transition-transform duration-200 ${isActive ? 'scale-110' : ''}`}>{capa.icon}</span>
              <span className={`text-[9px] font-semibold tracking-wide ${isActive ? 'text-[var(--accent-indigo)]' : 'text-[var(--text-ghost)]'}`}>{capa.label}</span>
              {isActive && <div className="w-5 h-[3px] rounded-full bg-[var(--accent-indigo)] mt-0.5" />}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
