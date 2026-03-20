import { useState, useEffect } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

export default function Profundo() {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [acdHistory, setAcdHistory] = useState(null);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const d = await fetch(`${BASE}/pilates/dashboard`).then(r => r.json());
      setData(d);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function loadACD() {
    const h = await fetch(`${BASE}/pilates/acd/historial`).then(r => r.json());
    setAcdHistory(h);
  }

  async function ejecutarACD() {
    const r = await fetch(`${BASE}/pilates/acd/diagnosticar`, { method: 'POST' }).then(r => r.json());
    alert(`Diagnóstico: ${r.estado || r.detail}`);
    loadDashboard();
    loadACD();
  }

  if (loading) return <div style={s.container}><p>Cargando...</p></div>;
  if (!data) return <div style={s.container}><p>Error cargando dashboard</p></div>;

  const n = data.numeros;
  const f = data.financiero;
  const o = data.ocupacion;
  const acd = data.acd;

  return (
    <div style={s.container}>
      <div style={s.header}>
        <h1 style={s.h1}>Modo Profundo</h1>
        <span style={{color:'#6b7280', fontSize:13}}>Authentic Pilates · {data.semana}</span>
      </div>

      {/* Tabs */}
      <div style={s.tabs}>
        {['dashboard','acd','grupos','contabilidad'].map(t => (
          <button key={t} onClick={() => { setTab(t); if(t==='acd' && !acdHistory) loadACD(); }}
            style={tab === t ? s.tabActive : s.tab}>
            {{dashboard:'Dashboard',acd:'Diagnóstico ACD',grupos:'Grupos',contabilidad:'Contabilidad'}[t]}
          </button>
        ))}
      </div>

      {/* DASHBOARD */}
      {tab === 'dashboard' && (
        <div>
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
              {/* Barra ocupación */}
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
  tabs: { display:'flex', gap:4, marginBottom:20, borderBottom:'1px solid #e5e7eb', paddingBottom:8 },
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
};
