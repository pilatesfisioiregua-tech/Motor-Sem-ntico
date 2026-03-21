# B-PIL-06: Frontend React — Modo Estudio (Agenda + Asistencias + Cobro Rápido)

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-04 (endpoints backend), B-PIL-05 (automatismos)
**Coste:** $0

---

## CONTEXTO

El backend está completo: CRUD, lógica de negocio, automatismos. Ahora el frontend que Jesús usa entre clases. Fuente: Exocortex v2.1 S6.

**Principio fundamental:** Modo Estudio = teclado-first, <30s por acción, zero navegación.

**Stack frontend:** React + Vite (SPA estática servida desde fly.io o Cloudflare Pages). Comunicación con backend via fetch al mismo dominio.

**Pantalla única** con 3 paneles:
1. **Izquierda:** Agenda del día (sesiones ordenadas por hora)
2. **Centro:** Detalle sesión seleccionada (asistentes + marcar ausencias)
3. **Derecha:** Panel rápido (cobro, alertas, búsqueda)

---

## FASE A: Estructura del proyecto frontend

### A1. Crear proyecto React + Vite

```bash
cd @project/
mkdir -p frontend
cd frontend
npm create vite@latest . -- --template react
npm install
```

### A2. Dependencias mínimas

```bash
cd @project/frontend
npm install react-hot-toast
```

No instalar más. Sin Tailwind (CSS vanilla para control total). Sin router (SPA de una pantalla). Sin state manager (useState + useEffect suficiente para MVP).

---

## FASE B: Configuración base

### B1. Crear `frontend/src/api.js`

```javascript
/**
 * Cliente API para Exocortex Pilates.
 * Base URL configurable para dev/prod.
 */

const BASE = import.meta.env.VITE_API_URL || '';
const PREFIX = `${BASE}/pilates`;

async function request(path, options = {}) {
  const url = `${PREFIX}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Error ${res.status}`);
  }
  return res.json();
}

// GRUPOS
export const getGrupos = () => request('/grupos');
export const getGrupo = (id) => request(`/grupos/${id}`);
export const getAgendaGrupo = (id, fecha) =>
  request(`/grupos/${id}/agenda${fecha ? `?fecha=${fecha}` : ''}`);

// SESIONES
export const getSesionesHoy = () => request('/sesiones/hoy');
export const crearSesion = (data) => request('/sesiones', { method: 'POST', body: JSON.stringify(data) });
export const completarSesion = (id) => request(`/sesiones/${id}/completar`, { method: 'POST' });
export const marcarGrupo = (id, data) =>
  request(`/sesiones/${id}/marcar-grupo`, { method: 'POST', body: JSON.stringify(data) });

// CLIENTES
export const getClientes = () => request('/clientes');
export const getCliente = (id) => request(`/clientes/${id}`);
export const crearCliente = (data) => request('/clientes', { method: 'POST', body: JSON.stringify(data) });
export const buscar = (q) => request(`/buscar?q=${encodeURIComponent(q)}`);

// CONTRATOS
export const crearContrato = (data) => request('/contratos', { method: 'POST', body: JSON.stringify(data) });

// CARGOS + PAGOS
export const getCargos = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/cargos${qs ? `?${qs}` : ''}`);
};
export const registrarPago = (data) => request('/pagos', { method: 'POST', body: JSON.stringify(data) });
export const getResumen = () => request('/resumen');

// AUTOMATISMOS
export const generarSesionesSemana = () => request('/cron/generar-sesiones', { method: 'POST' });
export const getAlertas = () => request('/alertas');
export const bizumEntrante = (data) => request('/bizum-entrante', { method: 'POST', body: JSON.stringify(data) });
export const cronInicioSemana = () => request('/cron/inicio_semana', { method: 'POST' });
export const cronInicioMes = () => request('/cron/inicio_mes', { method: 'POST' });
```

### B2. Crear `frontend/src/App.css`

```css
/* Modo Estudio — Teclado-first, <30s por acción */

:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface-hover: #242833;
  --border: #2a2e3a;
  --text: #e4e4e7;
  --text-dim: #71717a;
  --accent: #6366f1;
  --accent-hover: #818cf8;
  --green: #22c55e;
  --red: #ef4444;
  --yellow: #eab308;
  --orange: #f97316;
  font-family: 'Inter', -apple-system, system-ui, sans-serif;
  font-size: 14px;
  color: var(--text);
  background: var(--bg);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

.app {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  height: 100vh;
  gap: 1px;
  background: var(--border);
}

/* Panel izquierdo: Agenda */
.panel-agenda {
  background: var(--surface);
  overflow-y: auto;
  padding: 12px;
}

.panel-agenda h2 {
  font-size: 13px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.sesion-card {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}
.sesion-card:hover { background: var(--surface-hover); }
.sesion-card.selected { background: var(--surface-hover); border-left-color: var(--accent); }
.sesion-card .hora { font-size: 13px; font-weight: 600; }
.sesion-card .grupo { font-size: 12px; color: var(--text-dim); }
.sesion-card .stats { font-size: 11px; color: var(--text-dim); margin-top: 4px; }
.sesion-card .stats .ausentes { color: var(--red); }

/* Panel central: Detalle sesión */
.panel-detalle {
  background: var(--bg);
  overflow-y: auto;
  padding: 16px 20px;
}

.detalle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.detalle-header h2 { font-size: 18px; font-weight: 600; }

.asistente-row {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 2px;
  transition: background 0.15s;
}
.asistente-row:hover { background: var(--surface); }
.asistente-row .nombre { flex: 1; font-size: 14px; }
.asistente-row .estado-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.badge-asistio { background: rgba(34,197,94,0.15); color: var(--green); }
.badge-confirmada { background: rgba(99,102,241,0.15); color: var(--accent); }
.badge-no-vino { background: rgba(239,68,68,0.15); color: var(--red); }
.badge-recuperacion { background: rgba(234,179,8,0.15); color: var(--yellow); }

.toggle-ausencia {
  width: 32px; height: 32px;
  border: 2px solid var(--border);
  border-radius: 6px;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 16px;
  color: var(--text-dim);
  transition: all 0.15s;
}
.toggle-ausencia.ausente { border-color: var(--red); background: rgba(239,68,68,0.15); color: var(--red); }

/* Panel derecho: Acciones rápidas */
.panel-rapido {
  background: var(--surface);
  overflow-y: auto;
  padding: 12px;
}

.panel-rapido h3 {
  font-size: 12px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
  margin-top: 16px;
}
.panel-rapido h3:first-child { margin-top: 0; }

.resumen-card {
  background: var(--bg);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}
.resumen-card .label { font-size: 11px; color: var(--text-dim); }
.resumen-card .valor { font-size: 20px; font-weight: 700; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s;
}
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary { background: var(--surface-hover); color: var(--text); border: 1px solid var(--border); }
.btn-success { background: var(--green); color: white; }
.btn-danger { background: var(--red); color: white; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.input {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-size: 13px;
  outline: none;
}
.input:focus { border-color: var(--accent); }

.alerta {
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 4px;
  font-size: 12px;
  border-left: 3px solid;
}
.alerta-alta { border-color: var(--red); background: rgba(239,68,68,0.08); }
.alerta-media { border-color: var(--orange); background: rgba(249,115,22,0.08); }
.alerta-baja { border-color: var(--yellow); background: rgba(234,179,8,0.08); }

.kb-hint {
  font-size: 10px;
  color: var(--text-dim);
  background: var(--bg);
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid var(--border);
}

.empty { color: var(--text-dim); font-size: 13px; padding: 20px; text-align: center; }
.loading { color: var(--text-dim); font-size: 13px; padding: 20px; text-align: center; }
```

### B3. Crear `frontend/src/App.jsx`

**Este es el componente principal.** Implementa la pantalla única del Modo Estudio.

```jsx
import { useState, useEffect, useCallback } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import * as api from './api';
import './App.css';

function App() {
  // Estado principal
  const [sesiones, setSesiones] = useState([]);
  const [sesionSeleccionada, setSesionSeleccionada] = useState(null);
  const [asistentes, setAsistentes] = useState([]);
  const [ausencias, setAusencias] = useState(new Set());
  const [resumen, setResumen] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(true);

  // Panel cobro
  const [showCobro, setShowCobro] = useState(false);
  const [cargosPendientes, setCargosPendientes] = useState([]);

  // Panel bizum
  const [showBizum, setShowBizum] = useState(false);
  const [bizumTel, setBizumTel] = useState('');
  const [bizumMonto, setBizumMonto] = useState('');

  // Búsqueda
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  // ---- CARGA INICIAL ----
  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const [ses, res, ale] = await Promise.all([
        api.getSesionesHoy(),
        api.getResumen(),
        api.getAlertas(),
      ]);
      setSesiones(ses);
      setResumen(res);
      setAlertas(ale.alertas || []);
      if (ses.length > 0) {
        selectSesion(ses[0]);
      }
    } catch (e) {
      toast.error(`Error cargando datos: ${e.message}`);
    }
    setLoading(false);
  }

  // ---- SELECCIONAR SESIÓN ----
  async function selectSesion(sesion) {
    setSesionSeleccionada(sesion);
    setAusencias(new Set());
    if (sesion.grupo_nombre) {
      try {
        const agenda = await api.getAgendaGrupo(sesion.grupo_id, sesion.fecha);
        setAsistentes(agenda.asistentes || []);
      } catch (e) {
        setAsistentes([]);
      }
    }
  }

  // ---- TOGGLE AUSENCIA ----
  function toggleAusencia(clienteId) {
    setAusencias(prev => {
      const next = new Set(prev);
      if (next.has(clienteId)) next.delete(clienteId);
      else next.add(clienteId);
      return next;
    });
  }

  // ---- GUARDAR ASISTENCIA GRUPO ----
  async function guardarAsistencia() {
    if (!sesionSeleccionada) return;
    try {
      await api.marcarGrupo(sesionSeleccionada.id, {
        ausencias: Array.from(ausencias),
      });
      await api.completarSesion(sesionSeleccionada.id);
      toast.success(`Sesión completada · ${ausencias.size} ausencias`);
      loadDashboard();
    } catch (e) {
      toast.error(e.message);
    }
  }

  // ---- COBRO RÁPIDO ----
  async function abrirCobro(clienteId) {
    try {
      const cargos = await api.getCargos({ cliente_id: clienteId, estado: 'pendiente' });
      setCargosPendientes(cargos);
      setShowCobro(clienteId);
    } catch (e) {
      toast.error(e.message);
    }
  }

  async function cobrar(clienteId, metodo) {
    const total = cargosPendientes.reduce((s, c) => s + parseFloat(c.total), 0);
    if (total <= 0) { toast('Sin cargos pendientes'); return; }
    try {
      const result = await api.registrarPago({ cliente_id: clienteId, metodo, monto: total });
      toast.success(`Cobrado ${total.toFixed(2)}€ · ${result.cargos_conciliados} cargos`);
      setShowCobro(false);
      loadDashboard();
    } catch (e) {
      toast.error(e.message);
    }
  }

  // ---- BIZUM ENTRANTE ----
  async function enviarBizum() {
    if (!bizumTel || !bizumMonto) return;
    try {
      const result = await api.bizumEntrante({
        telefono: bizumTel, monto: parseFloat(bizumMonto),
      });
      toast.success(`Bizum registrado · ${result.cargos_conciliados} cargos conciliados`);
      setBizumTel(''); setBizumMonto(''); setShowBizum(false);
      loadDashboard();
    } catch (e) {
      toast.error(e.message);
    }
  }

  // ---- BÚSQUEDA ----
  useEffect(() => {
    if (searchQuery.length < 2) { setSearchResults([]); return; }
    const timer = setTimeout(async () => {
      try {
        const results = await api.buscar(searchQuery);
        setSearchResults(results);
      } catch (e) { setSearchResults([]); }
    }, 200);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // ---- ATAJOS TECLADO ----
  useEffect(() => {
    function handleKey(e) {
      if (e.target.tagName === 'INPUT') return;

      switch(e.key) {
        case 'F1': e.preventDefault(); setShowCobro(prev => !prev); break;
        case 'F3': e.preventDefault(); document.querySelector('.search-input')?.focus(); break;
        case 'b': case 'B':
          if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); setShowBizum(prev => !prev); }
          break;
        case ' ':
          // Space: toggle ausencia del asistente focused
          break;
        case 'Escape':
          setShowCobro(false); setShowBizum(false); setSearchQuery(''); setSearchResults([]);
          break;
      }
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, []);

  // ---- RENDER ----
  if (loading) return <div className="loading">Cargando Modo Estudio...</div>;

  return (
    <div className="app">
      <Toaster position="top-right" toastOptions={{
        style: { background: '#1a1d27', color: '#e4e4e7', border: '1px solid #2a2e3a' }
      }} />

      {/* PANEL IZQUIERDO: AGENDA */}
      <div className="panel-agenda">
        <h2>Hoy · {new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'short' })}</h2>
        {sesiones.length === 0 ? (
          <div className="empty">
            Sin sesiones hoy
            <br/>
            <button className="btn btn-secondary btn-sm" style={{marginTop: 8}}
              onClick={() => api.generarSesionesSemana().then(loadDashboard)}>
              Generar semana
            </button>
          </div>
        ) : sesiones.map(s => (
          <div key={s.id}
            className={`sesion-card ${sesionSeleccionada?.id === s.id ? 'selected' : ''}`}
            onClick={() => selectSesion(s)}>
            <div className="hora">{s.hora_inicio?.slice(0,5)}</div>
            <div className="grupo">{s.grupo_nombre || 'Individual'}</div>
            <div className="stats">
              {s.presentes} presentes
              {s.ausentes > 0 && <span className="ausentes"> · {s.ausentes} ausentes</span>}
            </div>
          </div>
        ))}
      </div>

      {/* PANEL CENTRAL: DETALLE SESIÓN */}
      <div className="panel-detalle">
        {sesionSeleccionada ? (
          <>
            <div className="detalle-header">
              <div>
                <h2>{sesionSeleccionada.grupo_nombre || 'Sesión Individual'}</h2>
                <span style={{color: 'var(--text-dim)', fontSize: 13}}>
                  {sesionSeleccionada.hora_inicio?.slice(0,5)} – {sesionSeleccionada.hora_fin?.slice(0,5)}
                  {sesionSeleccionada.estado === 'completada' && ' · ✓ Completada'}
                </span>
              </div>
              {sesionSeleccionada.estado !== 'completada' && (
                <button className="btn btn-success" onClick={guardarAsistencia}>
                  Completar sesión {ausencias.size > 0 && `(${ausencias.size} ausencias)`}
                </button>
              )}
            </div>

            {asistentes.map(a => {
              const cid = a.cliente_id;
              const isAusente = ausencias.has(cid);
              const estadoActual = isAusente ? 'no_vino' : (a.estado || 'confirmada');

              return (
                <div key={cid} className="asistente-row">
                  {sesionSeleccionada.estado !== 'completada' && (
                    <button className={`toggle-ausencia ${isAusente ? 'ausente' : ''}`}
                      onClick={() => toggleAusencia(cid)}
                      title="Space para toggle">
                      {isAusente ? '✕' : '✓'}
                    </button>
                  )}
                  <div className="nombre">{a.nombre || a.apellidos || 'Cliente'} {a.apellidos || ''}</div>
                  <span className={`estado-badge badge-${estadoActual.replace('_','-')}`}>
                    {estadoActual.replace('_', ' ')}
                  </span>
                  <button className="btn btn-sm btn-secondary" style={{marginLeft: 8}}
                    onClick={() => abrirCobro(cid)} title="F1 Cobrar">
                    €
                  </button>
                </div>
              );
            })}
            {asistentes.length === 0 && (
              <div className="empty">Sin asistentes en esta sesión</div>
            )}
          </>
        ) : (
          <div className="empty">Selecciona una sesión de la agenda</div>
        )}
      </div>

      {/* PANEL DERECHO: ACCIONES RÁPIDAS */}
      <div className="panel-rapido">
        {/* Resumen */}
        {resumen && (
          <>
            <h3>Resumen mes</h3>
            <div className="resumen-card">
              <div className="label">Ingresos</div>
              <div className="valor" style={{color: 'var(--green)'}}>{resumen.ingresos_mes?.toFixed(0)}€</div>
            </div>
            <div className="resumen-card">
              <div className="label">Deuda pendiente</div>
              <div className="valor" style={{color: resumen.deuda_pendiente > 0 ? 'var(--red)' : 'var(--text)'}}>
                {resumen.deuda_pendiente?.toFixed(0)}€
              </div>
            </div>
            <div className="resumen-card">
              <div className="label">Ocupación</div>
              <div className="valor">{resumen.ocupacion_pct}% <span style={{fontSize:12, color:'var(--text-dim)'}}>({resumen.plazas_ocupadas}/{resumen.plazas_totales})</span></div>
            </div>
          </>
        )}

        {/* Búsqueda */}
        <h3>Buscar <span className="kb-hint">F3</span></h3>
        <input className="input search-input" placeholder="Nombre, teléfono..."
          value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        {searchResults.map(r => (
          <div key={r.id} className="sesion-card" style={{marginTop: 4}}>
            <div style={{fontSize: 13}}>{r.nombre} {r.apellidos}</div>
            <div style={{fontSize: 11, color: 'var(--text-dim)'}}>{r.telefono}</div>
          </div>
        ))}

        {/* Bizum entrante */}
        <h3>Bizum entrante <span className="kb-hint">B</span></h3>
        {showBizum ? (
          <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
            <input className="input" placeholder="Teléfono" value={bizumTel}
              onChange={e => setBizumTel(e.target.value)} autoFocus />
            <input className="input" placeholder="Monto €" type="number" value={bizumMonto}
              onChange={e => setBizumMonto(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && enviarBizum()} />
            <button className="btn btn-primary" onClick={enviarBizum}>Registrar Bizum</button>
          </div>
        ) : (
          <button className="btn btn-secondary" style={{width: '100%'}} onClick={() => setShowBizum(true)}>
            Registrar Bizum entrante
          </button>
        )}

        {/* Alertas */}
        {alertas.length > 0 && (
          <>
            <h3>Alertas ({alertas.length})</h3>
            {alertas.slice(0, 5).map((a, i) => (
              <div key={i} className={`alerta alerta-${a.severidad}`}>
                <div style={{fontWeight: 500}}>{a.nombre}</div>
                <div>{a.detalle}</div>
              </div>
            ))}
          </>
        )}

        {/* Atajos */}
        <h3>Atajos teclado</h3>
        <div style={{fontSize: 11, color: 'var(--text-dim)', lineHeight: 1.8}}>
          <span className="kb-hint">F1</span> Cobrar &nbsp;
          <span className="kb-hint">F3</span> Buscar &nbsp;
          <span className="kb-hint">B</span> Bizum &nbsp;
          <span className="kb-hint">Space</span> Toggle ausencia &nbsp;
          <span className="kb-hint">Esc</span> Cerrar
        </div>

        {/* Cron manual */}
        <h3>Operaciones</h3>
        <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
          <button className="btn btn-secondary btn-sm" onClick={() =>
            api.cronInicioSemana().then(r => { toast.success(`Semana generada`); loadDashboard(); })}>
            Generar sesiones semana
          </button>
          <button className="btn btn-secondary btn-sm" onClick={() =>
            api.cronInicioMes().then(r => { toast.success(`Suscripciones: ${r.suscripciones?.cargos_creados || 0}`); loadDashboard(); })}>
            Generar suscripciones mes
          </button>
        </div>
      </div>

      {/* MODAL COBRO */}
      {showCobro && (
        <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.6)', display:'flex',
          alignItems:'center', justifyContent:'center', zIndex:100}}
          onClick={() => setShowCobro(false)}>
          <div style={{background:'var(--surface)', borderRadius:12, padding:20, width:360}}
            onClick={e => e.stopPropagation()}>
            <h3 style={{marginBottom: 12}}>Cobrar</h3>
            {cargosPendientes.length === 0 ? (
              <div className="empty">Sin cargos pendientes</div>
            ) : (
              <>
                {cargosPendientes.map(c => (
                  <div key={c.id} style={{display:'flex', justifyContent:'space-between',
                    padding:'6px 0', borderBottom:'1px solid var(--border)', fontSize:13}}>
                    <span>{c.descripcion || c.tipo}</span>
                    <span style={{fontWeight:600}}>{parseFloat(c.total).toFixed(2)}€</span>
                  </div>
                ))}
                <div style={{display:'flex', justifyContent:'space-between', padding:'10px 0',
                  fontWeight:700, fontSize:15}}>
                  <span>Total</span>
                  <span>{cargosPendientes.reduce((s,c) => s + parseFloat(c.total), 0).toFixed(2)}€</span>
                </div>
                <div style={{display:'flex', gap:8, marginTop:8}}>
                  <button className="btn btn-primary" style={{flex:1}}
                    onClick={() => cobrar(showCobro, 'bizum')}>Bizum</button>
                  <button className="btn btn-secondary" style={{flex:1}}
                    onClick={() => cobrar(showCobro, 'efectivo')}>Efectivo</button>
                  <button className="btn btn-secondary" style={{flex:1}}
                    onClick={() => cobrar(showCobro, 'tpv')}>TPV</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
```

---

## FASE C: Servir desde fly.io

### C1. Build estático

```bash
cd @project/frontend && npm run build
```

Esto genera `frontend/dist/` con HTML/JS/CSS estáticos.

### C2. Servir con FastAPI

**Archivo:** `@project/src/main.py` — AÑADIR al final (después de todos los routers):

```python
# Serve frontend static files (Modo Estudio)
from pathlib import Path
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    @app.get("/estudio")
    async def estudio():
        return FileResponse(frontend_dist / "index.html")

    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    log.info("frontend_mounted", path=str(frontend_dist))
```

### C3. Dockerfile — añadir build frontend

**Archivo:** `@project/Dockerfile` — LEER PRIMERO.

Añadir ANTES del CMD final:

```dockerfile
# Build frontend
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci
COPY frontend/ frontend/
RUN cd frontend && npm run build
```

Nota: Si esto añade demasiado peso al container, alternativa es build local + copiar `dist/` al repo.

---

## FASE D: Tests

### D1. Test local dev

```bash
cd @project/frontend && npm run dev
# Abrir http://localhost:5173
# Configurar VITE_API_URL=https://motor-semantico-omni.fly.dev en .env.development
```

### D2. Test post-deploy

```bash
curl https://motor-semantico-omni.fly.dev/estudio
# Debería devolver HTML del frontend
```

---

## Pass/fail

- `frontend/` creado con React + Vite
- `npm run build` genera `dist/` sin errores
- Pantalla muestra 3 paneles: agenda, detalle sesión, panel rápido
- Click en sesión → carga asistentes del grupo
- Toggle ausencia funciona (click o Space)
- Botón "Completar sesión" marca asistencia + cierra sesión
- Modal cobro muestra cargos pendientes + cobra en 1 clic
- Bizum entrante funciona (B → teléfono → monto → Enter)
- Búsqueda typeahead (F3) encuentra clientes
- Atajos teclado: F1, F3, B, Esc funcionan
- Resumen financiero muestra ingresos, deuda, ocupación

---

## NOTAS IMPORTANTES

- El frontend es **una sola pantalla** — no hay navegación, no hay router
- CSS vanilla, no Tailwind — control total del look
- Dark mode por defecto (el estudio de Pilates probablemente tiene poca luz)
- Las acciones del Modo Profundo (Matriz, ACD, Consejo) NO están en este briefing — son B-PIL-10+
- El frontend NO tiene autenticación — es para uso local en el estudio
- Si el Dockerfile se hace muy pesado, alternativa: build `dist/` local y commitear
- Los atajos de teclado están diseñados para no conflictar con el browser
