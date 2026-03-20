import { useState, useEffect, useCallback } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import * as api from './api';
import Onboarding from './Onboarding';
import Portal from './Portal';
import PanelWA from './PanelWA';
import Profundo from './Profundo';
import './App.css';

function App() {
  // Routing simple: si la URL es /onboarding/{token}, mostrar formulario público
  const path = window.location.pathname;
  const portalMatch = path.match(/^\/portal\/(.+)$/);
  if (portalMatch) {
    return <Portal token={portalMatch[1]} />;
  }

  const onboardingMatch = path.match(/^\/onboarding\/(.+)$/);
  if (onboardingMatch) {
    return <Onboarding token={onboardingMatch[1]} />;
  }

  if (path === '/profundo') {
    return <Profundo />;
  }

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

  // Nuevo cliente (onboarding)
  const [showNuevoCliente, setShowNuevoCliente] = useState(false);
  const [nuevoNombre, setNuevoNombre] = useState('');
  const [nuevoTel, setNuevoTel] = useState('');
  const [enlaceGenerado, setEnlaceGenerado] = useState(null);

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
      setSesiones(ses.sesiones || []);
      setResumen(res);
      setAlertas(ale.alertas || []);
      if ((ses.sesiones || []).length > 0) {
        selectSesion(ses.sesiones[0]);
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
    if (sesion.asistentes) {
      setAsistentes(sesion.asistentes);
    } else if (sesion.grupo_id) {
      try {
        const agenda = await api.getAgendaGrupo(sesion.grupo_id, sesion.fecha);
        setAsistentes(agenda.asistentes || []);
      } catch (e) {
        setAsistentes([]);
      }
    } else {
      setAsistentes([]);
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

  // ---- CREAR ENLACE ONBOARDING ----
  async function crearEnlaceOnboarding() {
    if (!nuevoNombre || !nuevoTel) return;
    try {
      const result = await api.crearEnlaceOnboarding({
        nombre_provisional: nuevoNombre, telefono: nuevoTel,
      });
      setEnlaceGenerado(result);
      toast.success('Enlace creado');
    } catch (e) { toast.error(e.message); }
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
        case 'F7': e.preventDefault(); setShowNuevoCliente(prev => !prev); break;
        case 'Escape':
          setShowCobro(false); setShowBizum(false); setShowNuevoCliente(false);
          setSearchQuery(''); setSearchResults([]);
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
              {(s.asistentes || []).length} alumnos
              {s.estado === 'completada' && ' · Completada'}
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
                  {sesionSeleccionada.estado === 'completada' && ' · Completada'}
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
                  <div className="nombre">{a.nombre || ''} {a.apellidos || ''}</div>
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
              <div className="valor" style={{color: 'var(--green)'}}>{resumen.ingresos?.toFixed(0) || 0}€</div>
            </div>
            <div className="resumen-card">
              <div className="label">Deuda pendiente</div>
              <div className="valor" style={{color: resumen.deuda_pendiente_total > 0 ? 'var(--red)' : 'var(--text)'}}>
                {resumen.deuda_pendiente_total?.toFixed(0) || 0}€
              </div>
            </div>
            <div className="resumen-card">
              <div className="label">Clientes activos</div>
              <div className="valor">{resumen.clientes_activos || 0}</div>
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

        {/* WhatsApp */}
        <PanelWA />

        {/* Nuevo cliente */}
        <h3>Nuevo cliente <span className="kb-hint">F7</span></h3>
        {showNuevoCliente ? (
          <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
            <input className="input" placeholder="Nombre" value={nuevoNombre}
              onChange={e => setNuevoNombre(e.target.value)} autoFocus />
            <input className="input" placeholder="Teléfono" value={nuevoTel}
              onChange={e => setNuevoTel(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && crearEnlaceOnboarding()} />
            <button className="btn btn-primary" onClick={crearEnlaceOnboarding}>
              Generar enlace
            </button>
            {enlaceGenerado && (
              <div style={{fontSize:12, background:'var(--bg)', padding:8, borderRadius:6, wordBreak:'break-all'}}>
                <div style={{marginBottom:4}}>{enlaceGenerado.enlace}</div>
                <button className="btn btn-sm btn-secondary" onClick={() => {
                  navigator.clipboard.writeText(enlaceGenerado.wa_mensaje);
                  toast.success('Mensaje copiado');
                }}>Copiar mensaje WA</button>
              </div>
            )}
          </div>
        ) : (
          <button className="btn btn-secondary" style={{width:'100%'}}
            onClick={() => setShowNuevoCliente(true)}>
            Crear enlace inscripción
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
          <span className="kb-hint">F7</span> Nuevo cliente &nbsp;
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
