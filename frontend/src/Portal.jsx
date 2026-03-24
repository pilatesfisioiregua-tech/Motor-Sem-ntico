import { useState, useEffect } from 'react';

export default function Portal({ token }) {
  const [data, setData] = useState(null);
  const [view, setView] = useState('home');
  const [sesiones, setSesiones] = useState(null);
  const [recuperaciones, setRecuperaciones] = useState(null);
  const [pagos, setPagos] = useState(null);
  const [facturas, setFacturas] = useState(null);
  const [error, setError] = useState(null);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    fetch(`/portal/${token}/data`)
      .then(r => { if (!r.ok) throw new Error('Portal no disponible'); return r.json(); })
      .then(setData)
      .catch(e => setError(e.message));
  }, [token]);

  async function loadView(v) {
    setView(v);
    try {
      if (v === 'sesiones' && !sesiones) {
        const r = await fetch(`/portal/${token}/sesiones`).then(r => r.json());
        setSesiones(r);
      }
      if (v === 'recuperar' && !recuperaciones) {
        const r = await fetch(`/portal/${token}/recuperaciones`).then(r => r.json());
        setRecuperaciones(r);
      }
      if (v === 'pagos' && !pagos) {
        const r = await fetch(`/portal/${token}/pagos`).then(r => r.json());
        setPagos(r);
      }
      if (v === 'facturas' && !facturas) {
        const r = await fetch(`/portal/${token}/facturas`).then(r => r.json());
        setFacturas(r);
      }
    } catch (e) { setError(e.message); }
  }

  async function cancelar(sesionId) {
    if (!confirm('¿Seguro que quieres cancelar esta sesión?')) return;
    try {
      const r = await fetch(`/portal/${token}/cancelar/${sesionId}`, { method: 'POST' });
      const result = await r.json();
      setMsg(result.mensaje);
      // Reload
      const home = await fetch(`/portal/${token}/data`).then(r => r.json());
      setData(home);
    } catch (e) { setError(e.message); }
  }

  async function solicitar_recuperacion(sesionId) {
    try {
      const r = await fetch(`/portal/${token}/recuperar`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ sesion_id: sesionId }),
      });
      if (!r.ok) { const err = await r.json(); throw new Error(err.detail); }
      const result = await r.json();
      setMsg(result.mensaje);
      setRecuperaciones(null); // force reload
    } catch (e) { setMsg(e.message); }
  }

  if (error) return <div style={s.container}><div style={s.card}><p style={{color:'#ef4444'}}>{error}</p></div></div>;
  if (!data) return <div style={s.container}><div style={s.card}><p>Cargando...</p></div></div>;

  return (
    <div style={s.container}>
      <div style={s.card}>
        <h1 style={s.h1}>Authentic Pilates</h1>
        <p style={s.greeting}>Hola, {data.cliente.nombre}!</p>

        {msg && <div style={s.toast}>{msg} <span style={{cursor:'pointer'}} onClick={()=>setMsg(null)}>✕</span></div>}

        {/* Nav */}
        <div style={s.nav}>
          {['home','sesiones','recuperar','pagos','facturas'].map(v => (
            <button key={v} onClick={() => loadView(v)}
              style={view === v ? s.navActive : s.navBtn}>
              {{home:'Inicio',sesiones:'Sesiones',recuperar:'Recuperar',pagos:'Pagos',facturas:'Facturas'}[v]}
            </button>
          ))}
        </div>

        {/* HOME */}
        {view === 'home' && (
          <div>
            {data.contrato && (
              <div style={s.section}>
                <div style={s.label}>Tu servicio</div>
                <div style={s.value}>{data.contrato.grupo_nombre || 'Individual'}</div>
              </div>
            )}
            <div style={s.section}>
              <div style={s.label}>Este mes</div>
              <div style={{display:'flex',gap:16}}>
                <div><span style={s.big}>{data.asistencia_mes.asistidas}</span> asistidas</div>
                <div><span style={{...s.big, color:'#ef4444'}}>{data.asistencia_mes.faltas}</span> faltas</div>
              </div>
            </div>
            {data.saldo_pendiente > 0 && (
              <div style={{...s.section, background:'#fef2f2', borderRadius:8, padding:12}}>
                <div style={s.label}>Saldo pendiente</div>
                <div style={{...s.big, color:'#ef4444'}}>{data.saldo_pendiente.toFixed(2)}€</div>
              </div>
            )}
            <div style={s.section}>
              <div style={s.label}>Próximas sesiones</div>
              {data.proximas_sesiones.length === 0
                ? <p style={{color:'#9ca3af', fontSize:13}}>Sin sesiones programadas esta semana</p>
                : data.proximas_sesiones.map((ses, i) => (
                  <div key={i} style={s.row}>
                    <div>
                      <div style={{fontWeight:500}}>{ses.fecha} · {String(ses.hora_inicio).slice(0,5)}</div>
                      <div style={{fontSize:12, color:'#6b7280'}}>{ses.grupo_nombre || 'Individual'}</div>
                    </div>
                    {ses.asistencia_estado === 'confirmada' && (
                      <button style={s.btnDanger} onClick={() => cancelar(ses.id)}>No puedo ir</button>
                    )}
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* SESIONES */}
        {view === 'sesiones' && sesiones && (
          <div>
            <div style={s.label}>Sesiones de {sesiones.mes}</div>
            {sesiones.sesiones.map((ses, i) => (
              <div key={i} style={s.row}>
                <div>
                  <div style={{fontWeight:500}}>{ses.fecha} · {String(ses.hora_inicio).slice(0,5)}</div>
                  <div style={{fontSize:12, color:'#6b7280'}}>{ses.grupo_nombre || 'Individual'}</div>
                </div>
                <span style={{
                  fontSize:11, padding:'2px 8px', borderRadius:4,
                  background: ses.estado === 'asistio' ? '#dcfce7' : ses.estado === 'no_vino' ? '#fee2e2' : '#f3f4f6',
                  color: ses.estado === 'asistio' ? '#16a34a' : ses.estado === 'no_vino' ? '#dc2626' : '#6b7280',
                }}>{ses.estado.replace('_',' ')}{ses.es_recuperacion ? ' (rec.)' : ''}</span>
              </div>
            ))}
          </div>
        )}

        {/* RECUPERAR */}
        {view === 'recuperar' && recuperaciones && (
          <div>
            {!recuperaciones.puede_recuperar
              ? <p style={{color:'#6b7280'}}>{recuperaciones.mensaje}</p>
              : (
                <>
                  <p style={{fontSize:13, marginBottom:12}}>
                    Tienes {recuperaciones.faltas - recuperaciones.recuperaciones} falta(s) por recuperar.
                  </p>
                  {recuperaciones.huecos.length === 0
                    ? <p style={{color:'#9ca3af'}}>No hay huecos disponibles esta semana</p>
                    : recuperaciones.huecos.map((h, i) => (
                      <div key={i} style={s.row}>
                        <div>
                          <div style={{fontWeight:500}}>{h.fecha} · {h.hora}</div>
                          <div style={{fontSize:12, color:'#6b7280'}}>{h.grupo} · {h.plazas_libres} plazas</div>
                        </div>
                        <button style={s.btn} onClick={() => solicitar_recuperacion(h.sesion_id)}>
                          Solicitar
                        </button>
                      </div>
                    ))
                  }
                </>
              )
            }
          </div>
        )}

        {/* PAGOS */}
        {view === 'pagos' && pagos && (
          <div>
            {pagos.saldo_pendiente > 0 && (
              <div style={{background:'#fef2f2', padding:12, borderRadius:8, marginBottom:12}}>
                Saldo pendiente: <strong>{pagos.saldo_pendiente.toFixed(2)}€</strong>
              </div>
            )}
            {pagos.pagos.map((p, i) => (
              <div key={i} style={s.row}>
                <div>
                  <div style={{fontWeight:500}}>{p.fecha_pago}</div>
                  <div style={{fontSize:12, color:'#6b7280'}}>{p.metodo}</div>
                </div>
                <span style={{fontWeight:600}}>{parseFloat(p.monto).toFixed(2)}€</span>
              </div>
            ))}
          </div>
        )}

        {/* FACTURAS */}
        {view === 'facturas' && facturas && (
          <div>
            {facturas.facturas.length === 0
              ? <p style={{color:'#9ca3af'}}>Sin facturas</p>
              : facturas.facturas.map((f, i) => (
                <div key={i} style={s.row}>
                  <div>
                    <div style={{fontWeight:500}}>{f.numero_factura}</div>
                    <div style={{fontSize:12, color:'#6b7280'}}>{f.fecha_emision}</div>
                  </div>
                  <div style={{textAlign:'right'}}>
                    <div style={{fontWeight:600}}>{parseFloat(f.total).toFixed(2)}€</div>
                    <a href={`${f.pdf_url}`} target="_blank"
                      style={{fontSize:12, color:'#6366f1'}}>Descargar</a>
                  </div>
                </div>
              ))
            }
          </div>
        )}
      </div>
    </div>
  );
}

const s = {
  container: {
    minHeight:'100vh', display:'flex', alignItems:'flex-start', justifyContent:'center',
    background:'#f9fafb', padding:16, fontFamily:"'Inter',-apple-system,sans-serif",
  },
  card: { background:'#fff', borderRadius:16, padding:20, maxWidth:480, width:'100%',
    boxShadow:'0 4px 24px rgba(0,0,0,0.08)', marginTop:20 },
  h1: { fontSize:20, fontWeight:700, margin:0 },
  greeting: { fontSize:15, color:'#374151', marginTop:4 },
  nav: { display:'flex', gap:4, margin:'16px 0', overflowX:'auto' },
  navBtn: { padding:'6px 12px', borderRadius:6, border:'1px solid #e5e7eb', background:'#fff',
    fontSize:12, cursor:'pointer', whiteSpace:'nowrap' },
  navActive: { padding:'6px 12px', borderRadius:6, border:'none', background:'#6366f1',
    color:'#fff', fontSize:12, cursor:'pointer', whiteSpace:'nowrap' },
  section: { marginBottom:16 },
  label: { fontSize:11, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:4 },
  value: { fontSize:15, fontWeight:500 },
  big: { fontSize:22, fontWeight:700 },
  row: { display:'flex', justifyContent:'space-between', alignItems:'center',
    padding:'8px 0', borderBottom:'1px solid #f3f4f6' },
  btn: { padding:'6px 12px', borderRadius:6, background:'#6366f1', color:'#fff',
    border:'none', fontSize:12, cursor:'pointer' },
  btnDanger: { padding:'6px 12px', borderRadius:6, background:'#fee2e2', color:'#dc2626',
    border:'none', fontSize:12, cursor:'pointer' },
  toast: { background:'#ecfdf5', padding:'8px 12px', borderRadius:8, fontSize:13, marginBottom:12,
    display:'flex', justifyContent:'space-between' },
};
