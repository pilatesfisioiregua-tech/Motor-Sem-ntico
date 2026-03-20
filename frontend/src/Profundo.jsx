import { useState, useEffect } from 'react';
import Consejo from './Consejo';

const BASE = import.meta.env.VITE_API_URL || '';
const P = `${BASE}/pilates`;

export default function Profundo() {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [acdHistory, setAcdHistory] = useState(null);
  // ADN
  const [adnList, setAdnList] = useState(null);
  const [adnForm, setAdnForm] = useState(false);
  const [adnNew, setAdnNew] = useState({categoria:'principio_innegociable',titulo:'',descripcion:''});
  // Depuración
  const [depList, setDepList] = useState(null);
  const [depForm, setDepForm] = useState(false);
  const [depNew, setDepNew] = useState({tipo:'proceso_redundante',descripcion:'',impacto_estimado:''});

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const d = await fetch(`${P}/dashboard`).then(r => r.json());
      setData(d);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function loadACD() {
    const h = await fetch(`${P}/acd/historial`).then(r => r.json());
    setAcdHistory(h);
  }

  async function ejecutarACD() {
    const r = await fetch(`${P}/acd/diagnosticar`, { method: 'POST' }).then(r => r.json());
    alert(`Diagnóstico: ${r.estado || r.detail}`);
    loadDashboard();
    loadACD();
  }

  async function loadADN() {
    const list = await fetch(`${P}/adn`).then(r => r.json());
    setAdnList(list);
  }

  async function crearADN(e) {
    e.preventDefault();
    await fetch(`${P}/adn`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(adnNew),
    });
    setAdnForm(false);
    setAdnNew({categoria:'principio_innegociable',titulo:'',descripcion:''});
    loadADN();
  }

  async function desactivarADN(id) {
    await fetch(`${P}/adn/${id}`, { method: 'DELETE' });
    loadADN();
  }

  async function loadDep() {
    const list = await fetch(`${P}/depuracion`).then(r => r.json());
    setDepList(list);
  }

  async function crearDep(e) {
    e.preventDefault();
    await fetch(`${P}/depuracion`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(depNew),
    });
    setDepForm(false);
    setDepNew({tipo:'proceso_redundante',descripcion:'',impacto_estimado:''});
    loadDep();
  }

  async function cambiarEstadoDep(id, estado) {
    await fetch(`${P}/depuracion/${id}`, {
      method: 'PATCH',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ estado }),
    });
    loadDep();
  }

  if (loading) return <div style={s.container}><p>Cargando...</p></div>;
  if (!data) return <div style={s.container}><p>Error cargando dashboard</p></div>;

  const n = data.numeros;
  const f = data.financiero;
  const o = data.ocupacion;
  const acd = data.acd;
  const rd = data.readiness;

  const TABS = ['dashboard','acd','consejo','adn','depuracion','grupos','contabilidad'];
  const TAB_LABELS = {dashboard:'Dashboard',acd:'Diagnóstico ACD',consejo:'Consejo',adn:'ADN',depuracion:'Depuración',grupos:'Grupos',contabilidad:'Contabilidad'};

  // Agrupar ADN por categoría
  const adnByCategory = {};
  if (adnList) {
    adnList.forEach(a => {
      if (!adnByCategory[a.categoria]) adnByCategory[a.categoria] = [];
      adnByCategory[a.categoria].push(a);
    });
  }

  const CAT_LABELS = {
    principio_innegociable: 'Principios Innegociables',
    principio_flexible: 'Principios Flexibles',
    metodo: 'Método',
    filosofia: 'Filosofía',
    antipatron: 'Antipatrones',
    criterio_depuracion: 'Criterios de Depuración',
  };

  const DEP_ESTADOS = {propuesta:'#eab308', aprobada:'#3b82f6', ejecutada:'#22c55e', descartada:'#9ca3af'};

  return (
    <div style={s.container}>
      <div style={s.header}>
        <h1 style={s.h1}>Modo Profundo</h1>
        <span style={{color:'#6b7280', fontSize:13}}>Authentic Pilates · {data.semana}</span>
      </div>

      {/* Tabs */}
      <div style={s.tabs}>
        {TABS.map(t => (
          <button key={t} onClick={() => {
            setTab(t);
            if (t==='acd' && !acdHistory) loadACD();
            if (t==='adn' && !adnList) loadADN();
            if (t==='depuracion' && !depList) loadDep();
          }} style={tab === t ? s.tabActive : s.tab}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {/* DASHBOARD */}
      {tab === 'dashboard' && (
        <div>
          {/* Readiness prominente */}
          {rd && (
            <div style={{...s.card, borderLeft:'4px solid #6366f1', marginBottom:16}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                <div>
                  <div style={s.kpiLabel}>Readiness de Replicación</div>
                  <div style={{fontSize:32, fontWeight:700, color: rd.readiness_pct >= 50 ? '#22c55e' : '#f97316'}}>
                    {rd.readiness_pct}%
                  </div>
                </div>
                <div style={{fontSize:12, color:'#6b7280', textAlign:'right'}}>
                  <div>Procesos: {rd.componentes.procesos.pct}%</div>
                  <div>ADN: {rd.componentes.adn.pct}%</div>
                  <div>Conocimiento: {rd.componentes.conocimiento.pct}%</div>
                </div>
              </div>
              <div style={{fontSize:12, color:'#6b7280', marginTop:6}}>{rd.prescripcion_c}</div>
            </div>
          )}

          {/* KPIs */}
          <div style={s.grid4}>
            <div style={s.kpi}>
              <div style={s.kpiLabel}>Asistencia</div>
              <div style={s.kpiValue}>{n.asistencia_pct}%</div>
              <div style={s.kpiSub}>{n.asistencia_asistidas}/{n.asistencia_total} sesiones</div>
            </div>
            <div style={s.kpi}>
              <div style={s.kpiLabel}>Ingresos mes</div>
              <div style={{...s.kpiValue, color:'#16a34a'}}>{f.ingresos_mes_acumulado.toFixed(0)}€</div>
              <div style={s.kpiSub}>Semana: {f.ingresos_semana.toFixed(0)}€</div>
            </div>
            <div style={s.kpi}>
              <div style={s.kpiLabel}>Ocupación</div>
              <div style={s.kpiValue}>{o.pct}%</div>
              <div style={s.kpiSub}>{o.plazas_ocupadas}/{o.plazas_totales} plazas</div>
            </div>
            <div style={s.kpi}>
              <div style={s.kpiLabel}>Clientes</div>
              <div style={s.kpiValue}>{n.clientes_activos}</div>
              <div style={s.kpiSub}>+{n.nuevos_semana} -{n.bajas_semana} semana</div>
            </div>
          </div>

          {/* Deuda */}
          {f.deuda_pendiente > 0 && (
            <div style={{...s.card, borderLeft:'4px solid #ef4444'}}>
              <h3 style={s.cardTitle}>Deuda pendiente: {f.deuda_pendiente.toFixed(0)}€</h3>
              {f.top_deudores.map((d,i) => (
                <div key={i} style={{display:'flex', justifyContent:'space-between', padding:'4px 0',
                  fontSize:13}}>
                  <span>{d.nombre}</span>
                  <span style={{fontWeight:600, color:'#ef4444'}}>{d.deuda.toFixed(0)}€ (desde {d.desde})</span>
                </div>
              ))}
            </div>
          )}

          {/* Tendencia asistencia */}
          <div style={s.card}>
            <h3 style={s.cardTitle}>Tendencia asistencia (4 semanas)</h3>
            <div style={{display:'flex', gap:12, alignItems:'flex-end', height:80}}>
              {data.tendencia_asistencia.map((t,i) => (
                <div key={i} style={{flex:1, textAlign:'center'}}>
                  <div style={{
                    height: `${t.asistencia_pct * 0.7}px`,
                    background: t.asistencia_pct >= 80 ? '#22c55e' : t.asistencia_pct >= 60 ? '#eab308' : '#ef4444',
                    borderRadius: '4px 4px 0 0',
                    minHeight: 4,
                  }}/>
                  <div style={{fontSize:11, color:'#6b7280', marginTop:4}}>{t.asistencia_pct}%</div>
                  <div style={{fontSize:10, color:'#9ca3af'}}>{t.semana.slice(5)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* ACD resumen */}
          {acd.tiene_diagnostico && (
            <div style={{...s.card, borderLeft:`4px solid ${acd.estado_tipo==='equilibrado'?'#22c55e':'#f97316'}`}}>
              <h3 style={s.cardTitle}>Diagnóstico ACD</h3>
              <div style={{fontSize:15, fontWeight:600}}>{acd.estado} ({acd.estado_tipo})</div>
              {acd.lentes && (
                <div style={{fontSize:13, color:'#6b7280', marginTop:4}}>
                  S={acd.lentes.S} · Se={acd.lentes.Se} · C={acd.lentes.C}
                  {acd.gap && ` · gap=${acd.gap.toFixed(3)}`}
                </div>
              )}
              {acd.prescripcion?.objetivo && (
                <div style={{marginTop:8, padding:8, background:'#f9fafb', borderRadius:6, fontSize:13}}>
                  Objetivo: <strong>{acd.prescripcion.objetivo}</strong>
                </div>
              )}
              <div style={{fontSize:11, color:'#9ca3af', marginTop:4}}>Último: {acd.fecha}</div>
            </div>
          )}

          {/* Alertas */}
          {data.total_alertas > 0 && (
            <div style={s.card}>
              <h3 style={s.cardTitle}>Alertas ({data.total_alertas})</h3>
              {data.alertas.slice(0,5).map((a,i) => (
                <div key={i} style={{padding:'6px 0', borderBottom:'1px solid #f3f4f6', fontSize:13}}>
                  <span style={{fontWeight:500}}>{a.nombre}</span>
                  <span style={{color:'#6b7280', marginLeft:8}}>{a.detalle}</span>
                </div>
              ))}
            </div>
          )}

          {/* Depuraciones F3 */}
          {data.depuraciones?.length > 0 && (
            <div style={{...s.card, borderLeft:'4px solid #8b5cf6'}}>
              <h3 style={s.cardTitle}>Depuración (F3) — lo que dejar de hacer</h3>
              {data.depuraciones.map((d,i) => (
                <div key={i} style={{padding:'6px 0', fontSize:13}}>
                  <div style={{fontWeight:500}}>{d.descripcion}</div>
                  <div style={{color:'#6b7280'}}>{d.impacto_estimado} · {d.estado}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ACD TAB */}
      {tab === 'acd' && (
        <div>
          <button style={s.btn} onClick={ejecutarACD}>
            Ejecutar diagnóstico ACD (~$0.01)
          </button>
          {acdHistory && (
            <div style={{marginTop:16}}>
              <h3 style={s.cardTitle}>Historial de diagnósticos</h3>
              {acdHistory.map((d,i) => (
                <div key={i} style={{...s.card, marginBottom:8}}>
                  <div style={{display:'flex', justifyContent:'space-between'}}>
                    <span style={{fontWeight:600}}>{d.estado} ({d.estado_tipo})</span>
                    <span style={{fontSize:12, color:'#9ca3af'}}>{String(d.created_at).slice(0,10)}</span>
                  </div>
                  {d.lentes && (
                    <div style={{fontSize:13, color:'#6b7280'}}>
                      S={d.lentes.S} Se={d.lentes.Se} C={d.lentes.C} gap={d.gap?.toFixed(3)}
                    </div>
                  )}
                  {d.prescripcion?.objetivo && (
                    <div style={{fontSize:13, marginTop:4}}>Objetivo: {d.prescripcion.objetivo}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* CONSEJO TAB */}
      {tab === 'consejo' && <Consejo />}

      {/* ADN TAB */}
      {tab === 'adn' && (
        <div>
          {/* Readiness prominente */}
          {rd && (
            <div style={{...s.card, borderLeft:'4px solid #6366f1', marginBottom:16}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                <div>
                  <div style={{fontSize:11, color:'#9ca3af', textTransform:'uppercase'}}>Readiness Replicación</div>
                  <div style={{fontSize:28, fontWeight:700, color: rd.readiness_pct >= 50 ? '#22c55e' : '#f97316'}}>
                    {rd.readiness_pct}%
                  </div>
                </div>
                <div style={{fontSize:12, color:'#6b7280'}}>
                  ADN: {rd.componentes.adn.categorias_cubiertas}/{rd.componentes.adn.categorias_total} cat. · {rd.componentes.adn.total} principios
                </div>
              </div>
            </div>
          )}

          <button style={s.btn} onClick={() => setAdnForm(!adnForm)}>
            {adnForm ? 'Cancelar' : '+ Nuevo principio ADN'}
          </button>

          {adnForm && (
            <form onSubmit={crearADN} style={{...s.card, marginTop:12}}>
              <select value={adnNew.categoria} onChange={e => setAdnNew({...adnNew, categoria: e.target.value})}
                style={s.input}>
                {Object.entries(CAT_LABELS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <input placeholder="Título" value={adnNew.titulo} required
                onChange={e => setAdnNew({...adnNew, titulo: e.target.value})} style={{...s.input, marginTop:8}} />
              <textarea placeholder="Descripción" value={adnNew.descripcion} required rows={3}
                onChange={e => setAdnNew({...adnNew, descripcion: e.target.value})} style={{...s.input, marginTop:8}} />
              <button type="submit" style={{...s.btn, marginTop:8}}>Crear</button>
            </form>
          )}

          {adnList && Object.entries(adnByCategory).map(([cat, items]) => (
            <div key={cat} style={{marginTop:16}}>
              <h3 style={{...s.cardTitle, fontSize:13, color:'#6366f1'}}>{CAT_LABELS[cat] || cat}</h3>
              {items.map(a => (
                <div key={a.id} style={{...s.card, marginBottom:8}}>
                  <div style={{display:'flex', justifyContent:'space-between'}}>
                    <span style={{fontWeight:600}}>{a.titulo}</span>
                    <button onClick={() => desactivarADN(a.id)}
                      style={{background:'none', border:'none', color:'#ef4444', fontSize:12, cursor:'pointer'}}>
                      Desactivar
                    </button>
                  </div>
                  <div style={{fontSize:13, color:'#374151', marginTop:4}}>{a.descripcion}</div>
                  {a.lente && <div style={{fontSize:11, color:'#9ca3af', marginTop:4}}>Lente: {a.lente}</div>}
                  {a.funcion_l07 && <div style={{fontSize:11, color:'#9ca3af'}}>Función: {a.funcion_l07}</div>}
                </div>
              ))}
            </div>
          ))}

          {adnList && adnList.length === 0 && (
            <div style={{...s.card, marginTop:16, textAlign:'center', color:'#9ca3af'}}>
              Sin principios ADN. Crea el primero para codificar la identidad del negocio.
            </div>
          )}
        </div>
      )}

      {/* DEPURACIÓN TAB */}
      {tab === 'depuracion' && (
        <div>
          <button style={s.btn} onClick={() => setDepForm(!depForm)}>
            {depForm ? 'Cancelar' : '+ Nueva depuración'}
          </button>

          {depForm && (
            <form onSubmit={crearDep} style={{...s.card, marginTop:12}}>
              <select value={depNew.tipo} onChange={e => setDepNew({...depNew, tipo: e.target.value})}
                style={s.input}>
                <option value="servicio_eliminar">Servicio a eliminar</option>
                <option value="cliente_toxico">Cliente tóxico</option>
                <option value="gasto_innecesario">Gasto innecesario</option>
                <option value="proceso_redundante">Proceso redundante</option>
                <option value="canal_inefectivo">Canal inefectivo</option>
                <option value="habito_operativo">Hábito operativo</option>
                <option value="creencia_limitante">Creencia limitante</option>
              </select>
              <textarea placeholder="Descripción" value={depNew.descripcion} required rows={2}
                onChange={e => setDepNew({...depNew, descripcion: e.target.value})} style={{...s.input, marginTop:8}} />
              <input placeholder="Impacto estimado" value={depNew.impacto_estimado}
                onChange={e => setDepNew({...depNew, impacto_estimado: e.target.value})} style={{...s.input, marginTop:8}} />
              <button type="submit" style={{...s.btn, marginTop:8}}>Crear</button>
            </form>
          )}

          {depList && depList.map((d,i) => (
            <div key={d.id || i} style={{...s.card, marginTop:i===0?16:0, borderLeft:`4px solid ${DEP_ESTADOS[d.estado]||'#9ca3af'}`}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                <div>
                  <div style={{fontWeight:600, fontSize:14}}>{d.descripcion}</div>
                  <div style={{fontSize:12, color:'#6b7280', marginTop:2}}>
                    {d.tipo?.replace(/_/g,' ')} · {d.impacto_estimado || 'Sin impacto estimado'}
                  </div>
                </div>
                <span style={{
                  padding:'2px 8px', borderRadius:12, fontSize:11, fontWeight:600,
                  background: DEP_ESTADOS[d.estado]||'#9ca3af', color:'#fff',
                }}>{d.estado}</span>
              </div>
              <div style={{display:'flex', gap:8, marginTop:8}}>
                {d.estado === 'propuesta' && (
                  <button onClick={() => cambiarEstadoDep(d.id, 'aprobada')}
                    style={{...s.btnSm, background:'#3b82f6'}}>Aprobar</button>
                )}
                {d.estado === 'aprobada' && (
                  <button onClick={() => cambiarEstadoDep(d.id, 'ejecutada')}
                    style={{...s.btnSm, background:'#22c55e'}}>Ejecutada</button>
                )}
                {(d.estado === 'propuesta' || d.estado === 'aprobada') && (
                  <button onClick={() => cambiarEstadoDep(d.id, 'descartada')}
                    style={{...s.btnSm, background:'#9ca3af'}}>Descartar</button>
                )}
              </div>
              {d.origen && d.origen !== 'manual' && (
                <div style={{fontSize:11, color:'#9ca3af', marginTop:4}}>Origen: {d.origen}</div>
              )}
            </div>
          ))}

          {depList && depList.length === 0 && (
            <div style={{...s.card, marginTop:16, textAlign:'center', color:'#9ca3af'}}>
              Sin depuraciones. F3 identifica lo que dejar de hacer.
            </div>
          )}
        </div>
      )}

      {/* GRUPOS TAB */}
      {tab === 'grupos' && data.grupos_detalle && (
        <div>
          {data.grupos_detalle.map((g,i) => (
            <div key={i} style={s.card}>
              <div style={{display:'flex', justifyContent:'space-between'}}>
                <span style={{fontWeight:600}}>{g.nombre}</span>
                <span style={{
                  color: g.ocupadas >= g.capacidad_max ? '#ef4444' : '#16a34a',
                  fontWeight:600,
                }}>{g.ocupadas}/{g.capacidad_max}</span>
              </div>
              <div style={{fontSize:12, color:'#6b7280'}}>
                {g.tipo} · {parseFloat(g.precio_mensual).toFixed(0)}€/mes
              </div>
              <div style={{height:4, background:'#f3f4f6', borderRadius:2, marginTop:6}}>
                <div style={{
                  height:4, borderRadius:2,
                  width:`${(g.ocupadas/g.capacidad_max)*100}%`,
                  background: g.ocupadas >= g.capacidad_max ? '#ef4444' : '#22c55e',
                }}/>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CONTABILIDAD TAB */}
      {tab === 'contabilidad' && (
        <div>
          <div style={s.card}>
            <h3 style={s.cardTitle}>Ingresos mensuales</h3>
            {data.ingresos_mensuales?.map((m,i) => (
              <div key={i} style={{display:'flex', justifyContent:'space-between', padding:'4px 0', fontSize:13}}>
                <span>{m.mes}</span>
                <span style={{fontWeight:600}}>{m.total.toFixed(0)}€</span>
              </div>
            ))}
          </div>
          <button style={{...s.btn, background:'#6b7280', marginTop:8}}
            onClick={() => window.open(`${BASE}/pilates/facturas/paquete-gestor`, '_blank')}>
            Descargar paquete gestor
          </button>
        </div>
      )}
    </div>
  );
}

const s = {
  container: { maxWidth:800, margin:'0 auto', padding:20, fontFamily:"'Inter',-apple-system,sans-serif" },
  header: { marginBottom:20 },
  h1: { fontSize:24, fontWeight:700, margin:0, color:'#111827' },
  tabs: { display:'flex', gap:4, marginBottom:20, borderBottom:'1px solid #e5e7eb', paddingBottom:8, flexWrap:'wrap' },
  tab: { padding:'8px 16px', background:'none', border:'none', fontSize:13, color:'#6b7280', cursor:'pointer', borderRadius:'6px 6px 0 0' },
  tabActive: { padding:'8px 16px', background:'#6366f1', border:'none', fontSize:13, color:'#fff', cursor:'pointer', borderRadius:6 },
  grid4: { display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, marginBottom:16 },
  kpi: { background:'#fff', borderRadius:12, padding:16, boxShadow:'0 1px 3px rgba(0,0,0,0.08)' },
  kpiLabel: { fontSize:11, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.05em' },
  kpiValue: { fontSize:28, fontWeight:700, color:'#111827', marginTop:4 },
  kpiSub: { fontSize:12, color:'#6b7280', marginTop:2 },
  card: { background:'#fff', borderRadius:12, padding:16, marginBottom:12, boxShadow:'0 1px 3px rgba(0,0,0,0.08)' },
  cardTitle: { fontSize:14, fontWeight:600, color:'#374151', marginBottom:8 },
  btn: { padding:'10px 20px', background:'#6366f1', color:'#fff', border:'none', borderRadius:8, fontSize:14, fontWeight:500, cursor:'pointer' },
  btnSm: { padding:'4px 12px', color:'#fff', border:'none', borderRadius:6, fontSize:12, cursor:'pointer' },
  input: { width:'100%', padding:'8px 12px', border:'1px solid #d1d5db', borderRadius:8, fontSize:14, boxSizing:'border-box' },
};
