import { useState, useEffect } from 'react';
import Consejo from './Consejo';
import Card from './design/Card';
import Metric from './design/Metric';
import LensBar from './design/LensBar';
import AgentBadge from './design/AgentBadge';
import SignalFlow from './design/SignalFlow';
import ConflictLine from './design/ConflictLine';
import Pulse from './design/Pulse';
import { TABS_PROFUNDO, ESTADO_ACD } from './design/theme';
import * as api from './api';
import { fetchApi } from './context/AppContext';

const P = '/pilates';

function IdentidadTab() {
  const [d, setD] = useState(null);
  useEffect(() => { api.getIdentidad().then(setD).catch(() => {}); }, []);
  if (!d || !d.esencia) return <p className="text-[var(--text-tertiary)] text-sm">Sin identidad</p>;
  return (
    <div className="space-y-2">
      <p className="text-sm">{d.esencia}</p>
      <div className="flex flex-wrap gap-1">{d.valores?.map(v => <span key={v} className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300">{v}</span>)}</div>
      <div className="flex flex-wrap gap-1">{d.anti_identidad?.map(a => <span key={a} className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-300">{a}</span>)}</div>
      <p className="text-xs text-[var(--text-tertiary)]">Tono: {d.tono}</p>
      <p className="text-xs text-[var(--text-tertiary)]">Angulo: {d.angulo_diferencial}</p>
    </div>
  );
}

function ContenidoTab() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.getContenido({limit: 10}).then(r => setItems(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  const estadoColor = { borrador: 'bg-gray-500/20 text-gray-300', aprobado: 'bg-emerald-500/20 text-emerald-300', programado: 'bg-cyan-500/20 text-cyan-300', publicado: 'bg-violet-500/20 text-violet-300' };
  return (
    <div>
      {items.length === 0 && <p className="text-[var(--text-tertiary)] text-sm">Sin contenido</p>}
      {items.map(c => (
        <div key={c.id} className="py-2 border-b border-[var(--border)]">
          <div className="flex justify-between"><span className="text-sm font-medium">{c.titulo}</span><span className={`text-[10px] px-1.5 py-0.5 rounded-full ${estadoColor[c.estado] || ''}`}>{c.estado}</span></div>
          <p className="text-xs text-[var(--text-tertiary)] truncate">{c.cuerpo?.slice(0, 120)}</p>
          <div className="flex gap-1 mt-1">{c.hashtags?.map(h => <span key={h} className="text-[10px] text-[var(--text-ghost)]">#{h}</span>)}</div>
        </div>
      ))}
    </div>
  );
}

function CompetenciaTab() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.getCompetencia().then(r => setItems(Array.isArray(r) ? r : [])).catch(() => {}); }, []);
  return (
    <div>
      {items.length === 0 && <p className="text-[var(--text-tertiary)] text-sm">Sin competidores configurados</p>}
      {items.map(c => (
        <div key={c.id} className="flex justify-between items-center py-1.5 border-b border-[var(--border)] text-sm">
          <span>{c.nombre}</span>
          <span className="text-xs text-[var(--text-ghost)]">{c.canal} · {c.tipo}</span>
        </div>
      ))}
    </div>
  );
}

// ============================================================
// HEADER PROFUNDO
// ============================================================

function HeaderProfundo({ estado, lentes, semana }) {
  const cfg = ESTADO_ACD[estado] || { color: 'slate', label: estado || 'Sin diagnostico' };
  const badgeColors = {
    amber:   'bg-amber-500/10 border-amber-500/20 text-amber-400',
    violet:  'bg-violet-500/10 border-violet-500/20 text-violet-400',
    red:     'bg-red-500/10 border-red-500/20 text-red-400',
    cyan:    'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
    rose:    'bg-rose-500/10 border-rose-500/20 text-rose-400',
    emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    slate:   'bg-slate-500/10 border-slate-500/20 text-slate-400',
  };

  return (
    <header className="px-8 py-6 border-b border-[var(--border)] bg-[var(--bg-deep)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
            Modo Profundo
          </h1>
          <span className="text-sm text-[var(--text-tertiary)]">
            Authentic Pilates {semana ? `\u00B7 ${semana}` : ''}
          </span>
        </div>
        <div className={`px-4 py-2 rounded-xl border ${badgeColors[cfg.color] || badgeColors.slate}`}>
          <span className="text-sm font-bold">{cfg.label}</span>
        </div>
      </div>
      {lentes && <LensBar salud={lentes.S || lentes.salud || 0.5} sentido={lentes.Se || lentes.sentido || 0.5} continuidad={lentes.C || lentes.continuidad || 0.5} />}
    </header>
  );
}

// ============================================================
// TAB ORGANISMO (NUEVO)
// ============================================================

function TabOrganismo() {
  const [pizarra, setPizarra] = useState(null);
  const [bus, setBus] = useState(null);
  const [configs, setConfigs] = useState(null);
  const [mediaciones, setMediaciones] = useState([]);
  const [patrones, setPatrones] = useState([]);
  const [motorResumen, setMotorResumen] = useState(null);

  useEffect(() => {
    api.getOrganismoPizarra().then(setPizarra).catch(() => {});
    api.getOrganismoBus().then(setBus).catch(() => {});
    api.getOrganismoConfigAgentes().then(setConfigs).catch(() => {});
    api.getMediaciones().then(r => setMediaciones(Array.isArray(r) ? r : [])).catch(() => {});
    api.getPatrones().then(r => setPatrones(r?.patrones || [])).catch(() => {});
    api.getMotorResumen().then(setMotorResumen).catch(() => {});
  }, []);

  const entradas = pizarra?.entradas || [];
  const porCapa = {};
  for (const e of entradas) {
    const capa = e.capa || 'otro';
    if (!porCapa[capa]) porCapa[capa] = [];
    porCapa[capa].push(e);
  }
  const conflictos = entradas.filter(e => e.conflicto_con);
  const rawBus = Array.isArray(bus) ? bus : (bus?.recientes || bus?.señales || []);
  const signals = rawBus.slice(0, 20);

  const gomas = [
    { id: 'G1', label: 'Datos\u2192Se\u00F1ales', desc: 'Negocio genera, AF escuchan' },
    { id: 'G2', label: 'Se\u00F1ales\u2192Diagn\u00F3stico', desc: 'Bus acumula, ACD diagnostica' },
    { id: 'G3', label: 'Diagn\u00F3stico\u2192B\u00FAsqueda', desc: 'Gaps generan queries' },
    { id: 'G4', label: 'B\u00FAsqueda\u2192Prescripci\u00F3n', desc: 'Cognitiva diagnostica, Estratega prescribe' },
    { id: 'G5', label: 'Prescripci\u00F3n\u2192Acci\u00F3n', desc: 'AF1-AF7 ejecutan via bus' },
    { id: 'G6', label: 'Acci\u00F3n\u2192Aprendizaje', desc: 'Gestor registra, poda, promueve' },
  ];

  return (
    <div className="space-y-6">
      {/* GOMAS DEL MOTOR PERPETUO */}
      <Card>
        <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>Motor Perpetuo — 6 Gomas</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {gomas.map(g => (
            <div key={g.id} className="p-2 rounded-lg bg-[var(--bg-void)] border border-[var(--border)]">
              <div className="flex items-center gap-1 mb-1">
                <Pulse active size={6} />
                <span className="text-xs font-bold text-[var(--accent-indigo)]" style={{ fontFamily: 'var(--font-mono)' }}>{g.id}</span>
              </div>
              <p className="text-[10px] text-[var(--text-secondary)]">{g.label}</p>
              <p className="text-[10px] text-[var(--text-ghost)]">{g.desc}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* MOTOR LLM */}
      {motorResumen && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>Motor LLM</h3>
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-[var(--text-tertiary)]">Presupuesto semanal</span>
            <span className="text-xs text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-mono)' }}>
              ${motorResumen.gastado_ciclo?.toFixed(2)} / $5.00
            </span>
          </div>
          <div className="w-full h-2 bg-[var(--bg-void)] rounded-full overflow-hidden mb-3">
            <div className={`h-full rounded-full transition-all ${
              ((5 - motorResumen.presupuesto_restante) / 5 * 100) > 80 ? 'bg-red-500' :
              ((5 - motorResumen.presupuesto_restante) / 5 * 100) > 50 ? 'bg-amber-500' : 'bg-emerald-500'
            }`} style={{ width: `${Math.min(100, (5 - motorResumen.presupuesto_restante) / 5 * 100)}%` }} />
          </div>
          {motorResumen.por_modelo?.length > 0 && motorResumen.por_modelo.map((m, i) => (
            <div key={i} className="flex justify-between text-xs py-0.5">
              <span className="text-[var(--text-secondary)]">{m.modelo?.split('/')[1] || m.modelo}</span>
              <span className="text-[var(--text-tertiary)]" style={{ fontFamily: 'var(--font-mono)' }}>
                {m.calls} calls · ${(parseFloat(m.coste) || 0).toFixed(3)}
              </span>
            </div>
          ))}
        </Card>
      )}

      {/* Agentes activos */}
      {configs && configs.length > 0 && (
        <Card variant="organism">
          <h3 className="text-sm font-bold text-[var(--accent-violet)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Agentes activos
          </h3>
          <div className="flex flex-wrap gap-2">
            {configs.map((c, i) => (
              <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--bg-elevated)] border border-[var(--border)]">
                <Pulse color="emerald" size={6} />
                <span className="text-xs font-medium text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-mono)' }}>{c.agente}</span>
                <span className="text-[10px] text-[var(--text-ghost)]">v{c.version}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* MEDIACIONES */}
      {mediaciones.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Mediaciones ({mediaciones.length})
          </h3>
          {mediaciones.map((m, i) => {
            const res = typeof m.resolucion === 'string' ? JSON.parse(m.resolucion) : (m.resolucion || {});
            return (
              <div key={i} className="py-2 border-b border-[var(--border)]">
                <div className="flex gap-1 mb-1">
                  {m.af_involucrados?.map(af => <AgentBadge key={af} agent={af} size="xs" />)}
                </div>
                <p className="text-xs text-[var(--text-secondary)]">{res?.resolucion || res?.accion_final || ''}</p>
              </div>
            );
          })}
        </Card>
      )}

      {/* PATRONES APRENDIDOS */}
      {patrones.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Patrones Aprendidos ({patrones.length})
          </h3>
          {patrones.slice(0, 5).map((p, i) => (
            <div key={i} className="py-2 border-b border-[var(--border)]">
              <div className="flex justify-between mb-1">
                <span className="text-xs font-bold text-[var(--accent-amber)]">{p.tipo}</span>
                <span className="text-[10px] text-[var(--text-ghost)]">
                  confianza {((p.confianza || 0) * 100).toFixed(0)}% · {p.evidencia_ciclos || 0} ciclos
                </span>
              </div>
              <p className="text-xs text-[var(--text-secondary)]">{p.descripcion}</p>
            </div>
          ))}
        </Card>
      )}

      {/* Pizarra por capas */}
      <Card variant="organism">
        <h3 className="text-sm font-bold text-[var(--accent-violet)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>
          Pizarra colectiva
        </h3>
        {Object.keys(porCapa).length === 0 && <p className="text-sm text-[var(--text-tertiary)]">Sin entradas en la pizarra</p>}
        {Object.entries(porCapa).map(([capa, agentes]) => (
          <div key={capa} className="mb-4">
            <div className="text-[10px] font-bold tracking-wider uppercase text-[var(--text-ghost)] mb-2">{capa}</div>
            <div className="space-y-2">
              {agentes.map(a => (
                <div key={a.agente} className="flex items-start gap-3 p-2 rounded-lg hover:bg-[var(--bg-elevated)] transition-colors">
                  <AgentBadge agent={a.agente} status={a.estado} confidence={a.confianza} />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-[var(--text-primary)]">{a.detectando}</div>
                    {a.accion_propuesta && <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">{a.accion_propuesta}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
        {conflictos.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-[10px] font-bold tracking-wider uppercase text-[var(--accent-red)] mb-1">Conflictos</div>
            {conflictos.map((c, i) => (
              <ConflictLine key={i} from={c.agente} to={c.conflicto_con} description={c.detectando} />
            ))}
          </div>
        )}
      </Card>

      {/* Bus de senales */}
      <Card>
        <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>
          Bus de senales
        </h3>
        {signals.length === 0 ? (
          <p className="text-sm text-[var(--text-tertiary)]">Sin senales recientes</p>
        ) : (
          <SignalFlow signals={signals} />
        )}
      </Card>

      {/* Resumen narrativo */}
      {pizarra?.resumen && (
        <Card variant="elevated">
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-2" style={{ fontFamily: 'var(--font-display)' }}>
            Resumen del organismo
          </h3>
          <p className="text-sm text-[var(--text-secondary)] whitespace-pre-wrap">{pizarra.resumen}</p>
        </Card>
      )}
    </div>
  );
}

// ============================================================
// TAB DIRECTOR (NUEVO)
// ============================================================

function TabDirector() {
  const [data, setData] = useState(null);
  const [cognitiva, setCognitiva] = useState(null);
  const [plan, setPlan] = useState(null);

  useEffect(() => {
    api.getOrganismoDirector().then(setData).catch(() => {});
    api.getPizarraCognitiva().then(setCognitiva).catch(() => {});
    api.getPlanTemporal().then(setPlan).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      {/* Estado Director */}
      <Card variant="elevated" glow>
        <h3 className="text-sm font-bold text-[var(--accent-indigo)] mb-2" style={{ fontFamily: 'var(--font-display)' }}>
          Director Opus
        </h3>
        {data?.estrategia_global ? (
          <div>
            {data.estado_sistema && <p className="text-sm text-[var(--text-secondary)] mb-3">{data.estado_sistema}</p>}
            <p className="text-sm text-[var(--text-primary)] font-medium">{data.estrategia_global}</p>
            {data.fecha && <div className="text-[10px] text-[var(--text-ghost)] mt-3">Actualizado: {new Date(data.fecha).toLocaleDateString('es-ES')}</div>}
          </div>
        ) : (
          <p className="text-sm text-[var(--text-tertiary)]">No ejecutado este ciclo</p>
        )}
      </Card>

      {/* Recetas (Pizarra Cognitiva) */}
      {cognitiva?.recetas?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Partituras D_hibrido — Ciclo {cognitiva.ciclo}
          </h3>
          {cognitiva.recetas.map((r, i) => (
            <div key={i} className="py-3 border-b border-[var(--border)]">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-sm text-[var(--accent-violet)]">{r.funcion}</span>
                <span className="text-xs text-[var(--text-ghost)]">
                  {r.lente || '*'} · p{r.prioridad}
                </span>
              </div>
              {r.intencion && <p className="text-xs text-[var(--text-secondary)] mb-2">{r.intencion}</p>}
              <div className="flex flex-wrap gap-1">
                {(r.ints || []).map(int => (
                  <span key={int} className="px-1.5 py-0.5 rounded-full bg-[var(--accent-indigo-glow)] text-[var(--accent-indigo)] text-[10px] font-bold"
                        style={{ fontFamily: 'var(--font-mono)' }}>
                    {int}
                  </span>
                ))}
                {(r.ps || []).map(p => (
                  <span key={p} className="px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-[10px] font-bold"
                        style={{ fontFamily: 'var(--font-mono)' }}>
                    {p}
                  </span>
                ))}
              </div>
              {r.prompt_imperativo && (
                <details className="mt-2">
                  <summary className="text-[10px] text-[var(--text-ghost)] cursor-pointer">Ver prompt</summary>
                  <pre className="text-[10px] text-[var(--text-tertiary)] bg-[var(--bg-void)] p-2 rounded mt-1 whitespace-pre-wrap">
                    {r.prompt_imperativo?.slice(0, 300)}
                  </pre>
                </details>
              )}
            </div>
          ))}
        </Card>
      )}

      {/* Plan Temporal */}
      {plan?.plan?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Plan Temporal — {plan.ciclo}
          </h3>
          {plan.plan.map((p, i) => (
            <div key={i} className={`flex items-center gap-2 py-1.5 border-b border-[var(--border)] text-sm ${!p.activo ? 'opacity-40' : ''}`}>
              <span className="text-xs w-6 text-[var(--text-ghost)]" style={{ fontFamily: 'var(--font-mono)' }}>{p.orden}</span>
              <span className="text-[var(--text-primary)]">{p.componente}</span>
              <span className="text-xs text-[var(--text-tertiary)] ml-auto">{p.fase}</span>
            </div>
          ))}
        </Card>
      )}

      {/* Configs por agente (legacy) */}
      {data?.configs?.map((cfg, i) => {
        const config = typeof cfg.config === 'string' ? JSON.parse(cfg.config) : cfg.config;
        const ints = config?.ints || config?.inteligencias || config?.INT_activas || [];
        const ps = config?.ps || config?.P_activos || [];
        const rs = config?.rs || config?.R_activos || [];

        return (
          <Card key={i}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
                {cfg.agente}
              </span>
              <span className="text-[10px] text-[var(--text-ghost)]" style={{ fontFamily: 'var(--font-mono)' }}>v{cfg.version}</span>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {ints.map((int, j) => (
                <span key={j} className="px-2 py-0.5 rounded-full bg-[var(--accent-indigo-glow)] text-[10px] text-[var(--accent-indigo)] font-bold"
                      style={{ fontFamily: 'var(--font-mono)' }}>
                  {typeof int === 'string' ? int : int.id || int.nombre}
                </span>
              ))}
              {ps.map((p, j) => (
                <span key={`p${j}`} className="px-2 py-0.5 rounded-full bg-amber-500/10 text-[10px] text-amber-400 font-bold"
                      style={{ fontFamily: 'var(--font-mono)' }}>
                  {typeof p === 'string' ? p : p.id || p.nombre}
                </span>
              ))}
              {rs.map((r, j) => (
                <span key={`r${j}`} className="px-2 py-0.5 rounded-full bg-cyan-500/10 text-[10px] text-cyan-400 font-bold"
                      style={{ fontFamily: 'var(--font-mono)' }}>
                  {typeof r === 'string' ? r : r.id || r.nombre}
                </span>
              ))}
            </div>
            {config?.provocacion && (
              <div className="px-3 py-2 rounded-lg bg-amber-500/5 border border-amber-500/10 text-xs text-[var(--accent-amber)] mb-2">
                {config.provocacion}
              </div>
            )}
            {config?.razonamiento && (
              <div className="text-xs text-[var(--text-tertiary)] italic">{config.razonamiento}</div>
            )}
          </Card>
        );
      })}
    </div>
  );
}

// ============================================================
// PROFUNDO PRINCIPAL
// ============================================================

export default function Profundo() {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [acdHistory, setAcdHistory] = useState(null);
  // ADN
  const [adnList, setAdnList] = useState(null);
  const [adnForm, setAdnForm] = useState(false);
  const [adnNew, setAdnNew] = useState({categoria:'principio_innegociable',titulo:'',descripcion:''});
  // Depuracion
  const [depList, setDepList] = useState(null);
  const [depForm, setDepForm] = useState(false);
  const [depNew, setDepNew] = useState({tipo:'proceso_redundante',descripcion:'',impacto_estimado:''});
  // Voz
  const [vozProps, setVozProps] = useState(null);
  const [vozGenerando, setVozGenerando] = useState(false);
  const [vozCapaA, setVozCapaA] = useState(null);
  const [vozCapaQuery, setVozCapaQuery] = useState('');
  const [vozIspCanal, setVozIspCanal] = useState('google_business');
  const [vozIspData, setVozIspData] = useState(null);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    setLoading(true);
    try { setData(await fetchApi(`${P}/dashboard`)); } catch {}
    setLoading(false);
  }
  async function loadACD() { setAcdHistory(await fetchApi(`${P}/acd/historial`)); }
  async function loadADN() { setAdnList(await fetchApi(`${P}/adn`)); }
  async function loadDep() { setDepList(await fetchApi(`${P}/depuracion`)); }
  async function loadVozProps() { setVozProps(await fetchApi(`${P}/voz/propuestas`)); }

  async function crearADN(e) {
    e.preventDefault();
    await fetchApi(`${P}/adn`, { method: 'POST', body: JSON.stringify(adnNew) });
    setAdnForm(false); setAdnNew({categoria:'principio_innegociable',titulo:'',descripcion:''}); loadADN();
  }
  async function desactivarADN(id) { await fetchApi(`${P}/adn/${id}`, { method: 'DELETE' }); loadADN(); }
  async function crearDep(e) {
    e.preventDefault();
    await fetchApi(`${P}/depuracion`, { method: 'POST', body: JSON.stringify(depNew) });
    setDepForm(false); setDepNew({tipo:'proceso_redundante',descripcion:'',impacto_estimado:''}); loadDep();
  }
  async function cambiarEstadoDep(id, estado) {
    await fetchApi(`${P}/depuracion/${id}`, { method: 'PATCH', body: JSON.stringify({ estado }) }); loadDep();
  }
  async function generarVozProps() {
    setVozGenerando(true);
    try { await fetchApi(`${P}/voz/generar-propuestas`, { method: 'POST' }); loadVozProps(); } catch {}
    setVozGenerando(false);
  }
  async function decidirVozProp(id, estado) {
    await fetchApi(`${P}/voz/propuestas/${id}`, { method: 'PATCH', body: JSON.stringify({ estado }) }); loadVozProps();
  }
  async function ejecutarVozProp(id) {
    await fetchApi(`${P}/voz/propuestas/${id}/ejecutar`, { method: 'POST' }); loadVozProps();
  }
  async function consultarCapaA() {
    if (!vozCapaQuery.trim()) return;
    setVozCapaA(await fetchApi(`${P}/voz/capa-a`, { method: 'POST', body: JSON.stringify({ fuente: 'perplexity', query: vozCapaQuery }) }));
  }
  async function consultarMeteo() {
    setVozCapaA(await fetchApi(`${P}/voz/capa-a`, { method: 'POST', body: JSON.stringify({ fuente: 'open_meteo' }) }));
  }
  async function loadISP(canal) {
    setVozIspData(await fetchApi(`${P}/voz/isp/${canal}`));
  }

  if (loading) return (
    <div className="min-h-screen bg-[var(--bg-void)] flex items-center justify-center">
      <div className="flex items-center gap-3 text-[var(--text-tertiary)]">
        <Pulse color="indigo" size={10} /><span>Cargando...</span>
      </div>
    </div>
  );

  if (!data) return (
    <div className="min-h-screen bg-[var(--bg-void)] flex items-center justify-center text-[var(--text-tertiary)]">
      Error cargando dashboard
    </div>
  );

  const n = data.numeros;
  const f = data.financiero;
  const o = data.ocupacion;
  const acd = data.acd;
  const rd = data.readiness;

  const CAT_LABELS = {
    principio_innegociable: 'Principios Innegociables', principio_flexible: 'Principios Flexibles',
    metodo: 'Metodo', filosofia: 'Filosofia', antipatron: 'Antipatrones', criterio_depuracion: 'Criterios de Depuracion',
  };

  const adnByCategory = {};
  if (adnList) adnList.forEach(a => { if (!adnByCategory[a.categoria]) adnByCategory[a.categoria] = []; adnByCategory[a.categoria].push(a); });

  const channelColor = { whatsapp: 'text-emerald-400', instagram: 'text-rose-400', web: 'text-cyan-400', google_business: 'text-blue-400', email: 'text-amber-400' };

  return (
    <div className="min-h-screen bg-[var(--bg-void)] flex">
      {/* VERTICAL TABS */}
      <nav className="w-48 min-w-[192px] border-r border-[var(--border)] bg-[var(--bg-deep)] flex flex-col py-4 shrink-0">
        {TABS_PROFUNDO.map(t => (
          <button
            key={t.id}
            onClick={() => {
              setTab(t.id);
              if (t.id === 'diagnostico' && !acdHistory) loadACD();
              if (t.id === 'adn' && !adnList) loadADN();
              if (t.id === 'depuracion' && !depList) loadDep();
              if (t.id === 'voz' && !vozProps) loadVozProps();
            }}
            className={`w-full text-left px-4 py-2.5 text-sm transition-all duration-150 cursor-pointer border-none bg-transparent
              ${tab === t.id
                ? 'text-[var(--text-primary)] bg-[var(--accent-indigo-glow)] border-r-2 border-r-[var(--accent-indigo)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
              }`}
          >
            <span className="mr-2">{t.icon}</span>{t.label}
          </button>
        ))}
      </nav>

      {/* MAIN */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <HeaderProfundo
          estado={acd?.estado}
          lentes={acd?.lentes}
          semana={data.semana}
        />

        <div className="flex-1 overflow-y-auto p-8">
          {/* DASHBOARD */}
          {tab === 'dashboard' && (
            <div className="space-y-6 module-enter">
              {/* Readiness */}
              {rd && (
                <Card variant="elevated" glow>
                  <div className="flex justify-between items-center">
                    <div>
                      <Metric label="Readiness" value={`${rd.readiness_pct}%`} size="lg"
                              delta={rd.readiness_pct >= 50 ? 1 : -1} />
                    </div>
                    <div className="text-xs text-[var(--text-tertiary)] text-right space-y-1">
                      <div>Procesos: {rd.componentes.procesos.pct}%</div>
                      <div>ADN: {rd.componentes.adn.pct}%</div>
                      <div>Conocimiento: {rd.componentes.conocimiento.pct}%</div>
                    </div>
                  </div>
                  {rd.prescripcion_c && <p className="text-xs text-[var(--text-tertiary)] mt-3">{rd.prescripcion_c}</p>}
                </Card>
              )}

              {/* KPIs */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Card><Metric label="Asistencia" value={`${n.asistencia_pct}%`} size="md" /><p className="text-xs text-[var(--text-tertiary)] mt-1">{n.asistencia_asistidas}/{n.asistencia_total} sesiones</p></Card>
                <Card><Metric label="Ingresos mes" value={`${f.ingresos_mes_acumulado.toFixed(0)}\u20AC`} size="md" delta={1} /><p className="text-xs text-[var(--text-tertiary)] mt-1">Semana: {f.ingresos_semana.toFixed(0)}&euro;</p></Card>
                <Card><Metric label="Ocupacion" value={`${o.pct}%`} size="md" /><p className="text-xs text-[var(--text-tertiary)] mt-1">{o.plazas_ocupadas}/{o.plazas_totales} plazas</p></Card>
                <Card><Metric label="Clientes" value={n.clientes_activos} size="md" /><p className="text-xs text-[var(--text-tertiary)] mt-1">+{n.nuevos_semana} -{n.bajas_semana} semana</p></Card>
              </div>

              {/* Deuda */}
              {f.deuda_pendiente > 0 && (
                <Card variant="danger">
                  <h3 className="text-sm font-bold text-[var(--accent-red)] mb-2">Deuda pendiente: {f.deuda_pendiente.toFixed(0)}&euro;</h3>
                  {f.top_deudores.map((d, i) => (
                    <div key={i} className="flex justify-between py-1 text-sm">
                      <span>{d.nombre}</span>
                      <span className="font-semibold text-[var(--accent-red)]">{d.deuda.toFixed(0)}&euro; (desde {d.desde})</span>
                    </div>
                  ))}
                </Card>
              )}

              {/* Tendencia */}
              <Card>
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Tendencia asistencia (4 semanas)</h3>
                <div className="flex gap-3 items-end h-20">
                  {data.tendencia_asistencia.map((t, i) => (
                    <div key={i} className="flex-1 text-center">
                      <div className="rounded-t" style={{
                        height: `${t.asistencia_pct * 0.7}px`, minHeight: 4,
                        background: t.asistencia_pct >= 80 ? 'var(--accent-green)' : t.asistencia_pct >= 60 ? 'var(--accent-amber)' : 'var(--accent-red)',
                      }} />
                      <div className="text-[11px] text-[var(--text-tertiary)] mt-1">{t.asistencia_pct}%</div>
                      <div className="text-[10px] text-[var(--text-ghost)]">{t.semana.slice(5)}</div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* ACD */}
              {acd.tiene_diagnostico && (
                <Card variant={acd.estado_tipo === 'equilibrado' ? 'success' : 'alert'}>
                  <h3 className="text-sm font-bold text-[var(--text-primary)] mb-2">Diagnostico ACD</h3>
                  <div className="text-base font-semibold">{acd.estado} ({acd.estado_tipo})</div>
                  {acd.lentes && (
                    <div className="mt-3">
                      <LensBar salud={acd.lentes.S || 0.5} sentido={acd.lentes.Se || 0.5} continuidad={acd.lentes.C || 0.5} />
                    </div>
                  )}
                  {acd.prescripcion?.objetivo && (
                    <div className="mt-3 p-3 rounded-lg bg-[var(--bg-elevated)] text-sm">
                      Objetivo: <strong>{acd.prescripcion.objetivo}</strong>
                    </div>
                  )}
                  <div className="text-[11px] text-[var(--text-ghost)] mt-2">Ultimo: {acd.fecha}</div>
                </Card>
              )}

              {/* Alertas */}
              {data.total_alertas > 0 && (
                <Card variant="alert">
                  <h3 className="text-sm font-bold text-[var(--accent-amber)] mb-2">Alertas ({data.total_alertas})</h3>
                  {data.alertas.slice(0, 5).map((a, i) => (
                    <div key={i} className="py-1.5 border-b border-[var(--border)] text-sm">
                      <span className="font-medium">{a.nombre}</span>
                      <span className="text-[var(--text-tertiary)] ml-2">{a.detalle}</span>
                    </div>
                  ))}
                </Card>
              )}
            </div>
          )}

          {/* DIAGNOSTICO TAB */}
          {tab === 'diagnostico' && (
            <div className="space-y-4 module-enter">
              {acd?.tiene_diagnostico && (
                <Card variant={acd.estado_tipo === 'equilibrado' ? 'success' : 'alert'}>
                  <div className="text-lg font-bold text-[var(--text-primary)] mb-2">{acd.estado}</div>
                  {acd.lentes && <LensBar salud={acd.lentes.S || 0.5} sentido={acd.lentes.Se || 0.5} continuidad={acd.lentes.C || 0.5} />}
                  {acd.prescripcion?.objetivo && (
                    <div className="mt-4 p-3 rounded-lg bg-[var(--bg-elevated)] text-sm">
                      <div className="text-xs font-bold text-[var(--text-ghost)] uppercase tracking-wider mb-1">Prescripcion</div>
                      {acd.prescripcion.objetivo}
                    </div>
                  )}
                </Card>
              )}
              {acdHistory && acdHistory.map((d, i) => (
                <Card key={i}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-sm">{d.estado} ({d.estado_tipo})</span>
                    <span className="text-xs text-[var(--text-ghost)]">{String(d.created_at).slice(0, 10)}</span>
                  </div>
                  {d.lentes && (
                    <LensBar salud={d.lentes.S || 0.5} sentido={d.lentes.Se || 0.5} continuidad={d.lentes.C || 0.5} />
                  )}
                  {d.prescripcion?.objetivo && <p className="text-sm text-[var(--text-secondary)] mt-2">Objetivo: {d.prescripcion.objetivo}</p>}
                </Card>
              ))}
            </div>
          )}

          {/* ORGANISMO TAB */}
          {tab === 'organismo' && <div className="module-enter"><TabOrganismo /></div>}

          {/* DIRECTOR TAB */}
          {tab === 'director' && <div className="module-enter"><TabDirector /></div>}

          {/* CONSEJO TAB */}
          {tab === 'consejo' && <div className="module-enter"><Consejo /></div>}

          {/* VOZ TAB */}
          {tab === 'voz' && (
            <div className="space-y-4 module-enter">
              <div className="flex gap-3">
                <button className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--accent-indigo)] text-white text-sm font-medium cursor-pointer border-none hover:bg-[var(--accent-indigo-dim)] transition-colors disabled:opacity-50"
                        onClick={generarVozProps} disabled={vozGenerando}>
                  {vozGenerando ? 'Generando...' : 'Generar propuestas'}
                </button>
                <button className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] text-sm font-medium cursor-pointer border border-[var(--border)] hover:bg-[var(--bg-overlay)] transition-colors"
                        onClick={loadVozProps}>Refrescar</button>
              </div>

              {vozProps && vozProps.length > 0 && vozProps.map((p, i) => (
                <Card key={p.id || i}>
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold uppercase ${channelColor[p.canal] || 'text-[var(--text-tertiary)]'}`}>{p.canal}</span>
                      <span className="text-xs text-[var(--text-ghost)]">{p.tipo?.replace(/_/g, ' ')}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      p.estado === 'pendiente' ? 'bg-amber-500/15 text-amber-400' :
                      p.estado === 'aprobada' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-[var(--bg-elevated)] text-[var(--text-ghost)]'
                    }`}>{p.estado}</span>
                  </div>
                  <p className="text-sm text-[var(--text-secondary)]">{p.justificacion}</p>
                  {p.contenido_propuesto?.texto && (
                    <div className="mt-2 p-3 rounded-lg bg-[var(--bg-elevated)] text-xs text-[var(--text-tertiary)] italic">{p.contenido_propuesto.texto}</div>
                  )}
                  {p.estado === 'pendiente' && (
                    <div className="flex gap-2 mt-3">
                      <button className="px-3 py-1 rounded-md bg-emerald-500 text-white text-xs cursor-pointer border-none" onClick={() => decidirVozProp(p.id, 'aprobada')}>Aprobar</button>
                      <button className="px-3 py-1 rounded-md bg-[var(--bg-overlay)] text-[var(--text-tertiary)] text-xs cursor-pointer border-none" onClick={() => decidirVozProp(p.id, 'descartada')}>Descartar</button>
                    </div>
                  )}
                  {p.estado === 'aprobada' && (
                    <button className="px-3 py-1 rounded-md bg-[var(--accent-indigo)] text-white text-xs cursor-pointer border-none mt-3" onClick={() => ejecutarVozProp(p.id)}>Ejecutar</button>
                  )}
                </Card>
              ))}

              {/* Capa A */}
              <Card variant="elevated">
                <h3 className="text-sm font-bold text-[var(--accent-violet)] mb-3">Capa A &mdash; Datos externos</h3>
                <div className="flex gap-2 mb-3">
                  <input className="flex-1 bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--border-active)]"
                         placeholder="Consulta Perplexity..." value={vozCapaQuery} onChange={e => setVozCapaQuery(e.target.value)} />
                  <button className="px-3 py-1.5 rounded-md bg-[var(--accent-violet)] text-white text-xs cursor-pointer border-none" onClick={consultarCapaA}>Buscar</button>
                </div>
                <button className="px-3 py-1.5 rounded-md bg-cyan-500 text-white text-xs cursor-pointer border-none" onClick={consultarMeteo}>Clima Logrono 7d</button>
                {vozCapaA && (
                  <div className="mt-3 p-3 rounded-lg bg-[var(--bg-surface)] text-sm">
                    <div className="font-semibold text-[var(--text-primary)] mb-1">{vozCapaA.fuente} &mdash; {vozCapaA.status}</div>
                    {vozCapaA.respuesta && <div className="text-[var(--text-secondary)] whitespace-pre-wrap">{vozCapaA.respuesta}</div>}
                    {vozCapaA.prevision && vozCapaA.prevision.time?.map((t, i) => (
                      <div key={i} className="flex gap-4 py-0.5 text-xs text-[var(--text-tertiary)]">
                        <span>{t}</span><span>{vozCapaA.prevision.temperature_2m_max?.[i]}&deg;</span><span>{vozCapaA.prevision.precipitation_sum?.[i]}mm</span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {/* ISP */}
              <Card>
                <h3 className="text-sm font-bold text-[var(--accent-amber)] mb-3">ISP &mdash; Salud de Presencia</h3>
                <div className="flex gap-2 mb-3">
                  {['google_business','instagram','whatsapp'].map(c => (
                    <button key={c} onClick={() => { setVozIspCanal(c); loadISP(c); }}
                      className={`px-3 py-1.5 rounded-md text-xs cursor-pointer border-none transition-colors ${
                        vozIspCanal === c ? 'bg-[var(--accent-amber)] text-white' : 'bg-[var(--bg-elevated)] text-[var(--text-secondary)]'
                      }`}>{c.replace(/_/g, ' ')}</button>
                  ))}
                </div>
                {vozIspData?.checklist && (
                  <div>
                    <p className="text-xs text-[var(--text-tertiary)] mb-2">Max score: {vozIspData.max_score} &mdash; {vozIspData.nota}</p>
                    {vozIspData.checklist.map((e, i) => (
                      <div key={i} className="flex justify-between py-1 border-b border-[var(--border)] text-sm">
                        <span className="text-[var(--text-secondary)]">{e.elemento}</span>
                        <span className="font-semibold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-mono)' }}>{e.peso}pts</span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          )}

          {/* ADN TAB */}
          {tab === 'adn' && (
            <div className="space-y-4 module-enter">
              {rd && (
                <Card variant="elevated" glow>
                  <div className="flex justify-between items-center">
                    <Metric label="Readiness Replicacion" value={`${rd.readiness_pct}%`} size="md" delta={rd.readiness_pct >= 50 ? 1 : -1} />
                    <div className="text-xs text-[var(--text-tertiary)] text-right">
                      ADN: {rd.componentes.adn.categorias_cubiertas}/{rd.componentes.adn.categorias_total} cat. &middot; {rd.componentes.adn.total} principios
                    </div>
                  </div>
                </Card>
              )}

              <button className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--accent-indigo)] text-white text-sm font-medium cursor-pointer border-none"
                      onClick={() => setAdnForm(!adnForm)}>
                {adnForm ? 'Cancelar' : '+ Nuevo principio ADN'}
              </button>

              {adnForm && (
                <Card>
                  <form onSubmit={crearADN} className="space-y-3">
                    <select value={adnNew.categoria} onChange={e => setAdnNew({...adnNew, categoria: e.target.value})}
                      className="w-full bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none">
                      {Object.entries(CAT_LABELS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                    <input placeholder="Titulo" value={adnNew.titulo} required onChange={e => setAdnNew({...adnNew, titulo: e.target.value})}
                      className="w-full bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none" />
                    <textarea placeholder="Descripcion" value={adnNew.descripcion} required rows={3} onChange={e => setAdnNew({...adnNew, descripcion: e.target.value})}
                      className="w-full bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none" />
                    <button type="submit" className="px-4 py-2 rounded-md bg-[var(--accent-indigo)] text-white text-sm cursor-pointer border-none">Crear</button>
                  </form>
                </Card>
              )}

              {adnList && Object.entries(adnByCategory).map(([cat, items]) => (
                <div key={cat}>
                  <h3 className="text-xs font-bold text-[var(--accent-indigo)] uppercase tracking-wider mb-2 mt-4">{CAT_LABELS[cat] || cat}</h3>
                  {items.map(a => (
                    <Card key={a.id} className="mb-3">
                      <div className="flex justify-between items-start">
                        <span className="font-semibold text-sm text-[var(--text-primary)]">{a.titulo}</span>
                        <button onClick={() => desactivarADN(a.id)} className="text-xs text-[var(--accent-red)] cursor-pointer bg-transparent border-none">Desactivar</button>
                      </div>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">{a.descripcion}</p>
                      {a.lente && <span className="text-[11px] text-[var(--text-ghost)]">Lente: {a.lente}</span>}
                    </Card>
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* DEPURACION TAB */}
          {tab === 'depuracion' && (
            <div className="space-y-4 module-enter">
              <button className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--accent-indigo)] text-white text-sm font-medium cursor-pointer border-none"
                      onClick={() => setDepForm(!depForm)}>
                {depForm ? 'Cancelar' : '+ Nueva depuracion'}
              </button>

              {depForm && (
                <Card>
                  <form onSubmit={crearDep} className="space-y-3">
                    <select value={depNew.tipo} onChange={e => setDepNew({...depNew, tipo: e.target.value})}
                      className="w-full bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none">
                      <option value="servicio_eliminar">Servicio a eliminar</option>
                      <option value="cliente_toxico">Cliente toxico</option>
                      <option value="gasto_innecesario">Gasto innecesario</option>
                      <option value="proceso_redundante">Proceso redundante</option>
                      <option value="canal_inefectivo">Canal inefectivo</option>
                      <option value="habito_operativo">Habito operativo</option>
                      <option value="creencia_limitante">Creencia limitante</option>
                    </select>
                    <textarea placeholder="Descripcion" value={depNew.descripcion} required rows={2} onChange={e => setDepNew({...depNew, descripcion: e.target.value})}
                      className="w-full bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none" />
                    <input placeholder="Impacto estimado" value={depNew.impacto_estimado} onChange={e => setDepNew({...depNew, impacto_estimado: e.target.value})}
                      className="w-full bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none" />
                    <button type="submit" className="px-4 py-2 rounded-md bg-[var(--accent-indigo)] text-white text-sm cursor-pointer border-none">Crear</button>
                  </form>
                </Card>
              )}

              {depList && depList.map((d, i) => {
                const statusColor = {
                  propuesta: 'bg-amber-500/15 text-amber-400', aprobada: 'bg-blue-500/15 text-blue-400',
                  ejecutada: 'bg-emerald-500/15 text-emerald-400', descartada: 'bg-[var(--bg-elevated)] text-[var(--text-ghost)]',
                };
                return (
                  <Card key={d.id || i} variant={d.estado === 'propuesta' ? 'alert' : 'default'}>
                    <div className="flex justify-between items-center mb-2">
                      <div className="font-semibold text-sm text-[var(--text-primary)]">{d.descripcion}</div>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${statusColor[d.estado] || ''}`}>{d.estado}</span>
                    </div>
                    <p className="text-xs text-[var(--text-tertiary)]">{d.tipo?.replace(/_/g, ' ')} &middot; {d.impacto_estimado || 'Sin impacto estimado'}</p>
                    <div className="flex gap-2 mt-3">
                      {d.estado === 'propuesta' && <button className="px-3 py-1 rounded-md bg-blue-500 text-white text-xs cursor-pointer border-none" onClick={() => cambiarEstadoDep(d.id, 'aprobada')}>Aprobar</button>}
                      {d.estado === 'aprobada' && <button className="px-3 py-1 rounded-md bg-emerald-500 text-white text-xs cursor-pointer border-none" onClick={() => cambiarEstadoDep(d.id, 'ejecutada')}>Ejecutada</button>}
                      {(d.estado === 'propuesta' || d.estado === 'aprobada') && <button className="px-3 py-1 rounded-md bg-[var(--bg-overlay)] text-[var(--text-ghost)] text-xs cursor-pointer border-none" onClick={() => cambiarEstadoDep(d.id, 'descartada')}>Descartar</button>}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}

          {/* CONTABILIDAD TAB */}
          {tab === 'contabilidad' && (
            <div className="space-y-4 module-enter">
              <Card>
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Ingresos mensuales</h3>
                {data.ingresos_mensuales?.map((m, i) => (
                  <div key={i} className="flex justify-between py-1.5 border-b border-[var(--border)] text-sm">
                    <span className="text-[var(--text-secondary)]">{m.mes}</span>
                    <span className="font-semibold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-mono)' }}>{m.total.toFixed(0)}&euro;</span>
                  </div>
                ))}
              </Card>
              <button className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] text-sm cursor-pointer border border-[var(--border)]"
                      onClick={() => window.open(`/pilates/facturas/paquete-gestor`, '_blank')}>
                Descargar paquete gestor
              </button>
            </div>
          )}
          {tab === 'contenido' && (
            <div className="space-y-4 module-enter">
              <Card>
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Identidad</h3>
                <IdentidadTab />
              </Card>
              <Card>
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Contenido semanal</h3>
                <ContenidoTab />
              </Card>
              <Card>
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Competencia</h3>
                <CompetenciaTab />
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
