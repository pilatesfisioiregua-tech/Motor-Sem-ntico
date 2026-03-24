import { useState, useEffect } from 'react';

export default function Consejo() {
  const [pregunta, setPregunta] = useState('');
  const [profundidad, setProfundidad] = useState('normal');
  const [resultado, setResultado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('nuevo'); // nuevo | historial | resultado

  useEffect(() => { loadHistorial(); }, []);

  async function loadHistorial() {
    const h = await fetch(`/pilates/consejo/historial`).then(r => r.json());
    setHistorial(h);
  }

  async function convocar() {
    if (!pregunta.trim()) return;
    setLoading(true);
    try {
      const r = await fetch(`/pilates/consejo`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ pregunta, profundidad }),
      }).then(r => r.json());
      setResultado(r);
      setView('resultado');
      loadHistorial();
    } catch (e) { alert(e.message); }
    setLoading(false);
  }

  async function registrarDecision(sesionId, decision) {
    const confianza = prompt('Confianza (0-1):', '0.7');
    if (!confianza) return;
    await fetch(`/pilates/consejo/${sesionId}/decision`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ decision, confianza: parseFloat(confianza) }),
    });
    loadHistorial();
  }

  return (
    <div>
      {/* Nav */}
      <div style={{display:'flex', gap:8, marginBottom:16}}>
        <button onClick={() => setView('nuevo')}
          style={view === 'nuevo' ? s.tabActive : s.tab}>Nueva consulta</button>
        <button onClick={() => setView('historial')}
          style={view === 'historial' ? s.tabActive : s.tab}>Historial</button>
      </div>

      {/* NUEVA CONSULTA */}
      {view === 'nuevo' && (
        <div>
          <textarea style={s.textarea} rows={4}
            placeholder="¿Qué decisión necesitas tomar? ¿Qué quieres explorar?"
            value={pregunta} onChange={e => setPregunta(e.target.value)} />
          <div style={{display:'flex', gap:8, margin:'12px 0'}}>
            {['rapida','normal','profunda'].map(p => (
              <button key={p} onClick={() => setProfundidad(p)}
                style={profundidad === p ? s.chipActive : s.chip}>
                {p} ({p === 'rapida' ? '3' : p === 'normal' ? '5' : '8'} asesores)
              </button>
            ))}
          </div>
          <button style={s.btn} onClick={convocar} disabled={loading || !pregunta.trim()}>
            {loading ? 'Convocando consejo...' : `Convocar (~$${
              profundidad === 'rapida' ? '0.05' : profundidad === 'normal' ? '0.15' : '0.40'
            })`}
          </button>
        </div>
      )}

      {/* RESULTADO */}
      {view === 'resultado' && resultado && (
        <div>
          <div style={s.card}>
            <div style={{fontSize:12, color:'#9ca3af'}}>
              Estado ACD: {resultado.estado_acd || 'sin diagnóstico'} ·
              {resultado.asesores_convocados} asesores · ${resultado.coste_usd} · {resultado.tiempo_s}s
            </div>
          </div>

          {/* Respuestas por asesor */}
          {resultado.respuestas.map((r, i) => (
            <div key={i} style={{...s.card, borderLeft:`3px solid hsl(${i*40}, 70%, 60%)`}}>
              <div style={{fontWeight:600, fontSize:14}}>
                {r.nombre} <span style={{color:'#9ca3af', fontWeight:400}}>({r.int_id} · {r.P}+{r.R})</span>
              </div>
              <div style={{fontSize:13, marginTop:6, lineHeight:1.6, whiteSpace:'pre-wrap'}}>
                {r.respuesta}
              </div>
            </div>
          ))}

          {/* Síntesis */}
          <div style={{...s.card, borderLeft:'3px solid #6366f1', background:'#faf5ff'}}>
            <h3 style={{fontSize:14, fontWeight:600, marginBottom:8}}>Síntesis del Integrador</h3>
            <div style={{fontSize:13, lineHeight:1.6, whiteSpace:'pre-wrap'}}>{resultado.sintesis}</div>
          </div>

          {/* Puntos ciegos */}
          {resultado.puntos_ciegos?.length > 0 && (
            <div style={{...s.card, borderLeft:'3px solid #f97316'}}>
              <h3 style={{fontSize:14, fontWeight:600, marginBottom:8}}>Puntos ciegos cruzados</h3>
              {resultado.puntos_ciegos.map((p, i) => (
                <div key={i} style={{fontSize:13, padding:'4px 0'}}>• {p}</div>
              ))}
            </div>
          )}

          <button style={{...s.btn, marginTop:12}} onClick={() => { setView('nuevo'); setPregunta(''); setResultado(null); }}>
            Nueva consulta
          </button>
        </div>
      )}

      {/* HISTORIAL */}
      {view === 'historial' && (
        <div>
          {historial.length === 0
            ? <p style={{color:'#9ca3af'}}>Sin sesiones anteriores</p>
            : historial.map((h, i) => (
              <div key={i} style={s.card}>
                <div style={{fontWeight:500}}>{h.pregunta?.slice(0, 100)}</div>
                <div style={{fontSize:12, color:'#6b7280', marginTop:4}}>
                  {h.inteligencias_convocadas?.join(', ')} ·
                  {h.profundidad} · ${h.coste_api} ·
                  {String(h.created_at).slice(0, 10)}
                </div>
                <div style={{fontSize:12, marginTop:4}}>
                  {h.sintesis?.slice(0, 150)}...
                </div>
                {h.decision_ternaria
                  ? <span style={{
                      fontSize:11, padding:'2px 8px', borderRadius:4, marginTop:6, display:'inline-block',
                      background: h.decision_ternaria === 'cierre' ? '#dcfce7' :
                                  h.decision_ternaria === 'toxico' ? '#fee2e2' : '#f3f4f6',
                      color: h.decision_ternaria === 'cierre' ? '#16a34a' :
                             h.decision_ternaria === 'toxico' ? '#dc2626' : '#6b7280',
                    }}>{h.decision_ternaria}</span>
                  : <div style={{display:'flex', gap:4, marginTop:8}}>
                      <button style={s.chipGreen} onClick={() => registrarDecision(h.id, 'cierre')}>Cierre</button>
                      <button style={s.chipGray} onClick={() => registrarDecision(h.id, 'inerte')}>Inerte</button>
                      <button style={s.chipRed} onClick={() => registrarDecision(h.id, 'toxico')}>Tóxico</button>
                    </div>
                }
              </div>
            ))
          }
        </div>
      )}
    </div>
  );
}

const s = {
  tab: { padding:'6px 14px', background:'none', border:'1px solid #e5e7eb', borderRadius:6, fontSize:13, cursor:'pointer' },
  tabActive: { padding:'6px 14px', background:'#6366f1', border:'none', borderRadius:6, fontSize:13, color:'#fff', cursor:'pointer' },
  textarea: { width:'100%', padding:12, border:'1px solid #d1d5db', borderRadius:8, fontSize:14, resize:'vertical', boxSizing:'border-box' },
  chip: { padding:'4px 12px', border:'1px solid #d1d5db', borderRadius:20, fontSize:12, cursor:'pointer', background:'#fff' },
  chipActive: { padding:'4px 12px', border:'none', borderRadius:20, fontSize:12, cursor:'pointer', background:'#6366f1', color:'#fff' },
  chipGreen: { padding:'4px 10px', border:'none', borderRadius:4, fontSize:11, cursor:'pointer', background:'#dcfce7', color:'#16a34a' },
  chipGray: { padding:'4px 10px', border:'none', borderRadius:4, fontSize:11, cursor:'pointer', background:'#f3f4f6', color:'#6b7280' },
  chipRed: { padding:'4px 10px', border:'none', borderRadius:4, fontSize:11, cursor:'pointer', background:'#fee2e2', color:'#dc2626' },
  btn: { padding:'10px 20px', background:'#6366f1', color:'#fff', border:'none', borderRadius:8, fontSize:14, fontWeight:500, cursor:'pointer', width:'100%' },
  card: { background:'#fff', borderRadius:10, padding:14, marginBottom:10, boxShadow:'0 1px 3px rgba(0,0,0,0.06)' },
};
