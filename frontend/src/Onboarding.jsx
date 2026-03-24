import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { fetchApi } from './context/AppContext';

export default function Onboarding() {
  const { token } = useParams();
  const [step, setStep] = useState(0); // 0=cargando, 1=datos, 2=clinico, 3=servicio, 4=confirmar, 5=done
  const [linkData, setLinkData] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [form, setForm] = useState({
    nombre: '', apellidos: '', telefono: '', email: '',
    fecha_nacimiento: '', nif: '', direccion: '',
    lesiones: '', patologias: '', medicacion: '', restricciones: '', medico_derivante: '',
    tipo_contrato: 'grupo', grupo_id: null,
    frecuencia_semanal: 1, precio_sesion: 35,
    consentimiento_datos: true, consentimiento_marketing: false,
    consentimiento_compartir_tenants: false, acepta_normas: false,
    metodo_pago: 'bizum',
  });

  useEffect(() => {
    fetch(`/pilates/onboarding/${token}`)
      .then(r => {
        if (!r.ok) throw new Error(r.status === 410 ? 'Este enlace ya fue utilizado o ha expirado' : 'Enlace no válido');
        return r.json();
      })
      .then(data => {
        setLinkData(data);
        setForm(f => ({
          ...f,
          nombre: data.nombre_provisional?.split(' ')[0] || '',
          telefono: data.telefono || '',
        }));
        setStep(1);
      })
      .catch(e => setError(e.message));
  }, [token]);

  const update = (field, value) => setForm(f => ({ ...f, [field]: value }));

  async function submit() {
    setSubmitting(true);
    try {
      const res = await fetch(`/pilates/onboarding/${token}/completar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          fecha_nacimiento: form.fecha_nacimiento || null,
          grupo_id: form.tipo_contrato === 'grupo' ? form.grupo_id : null,
          frecuencia_semanal: form.tipo_contrato === 'individual' ? form.frecuencia_semanal : null,
          precio_sesion: form.tipo_contrato === 'individual' ? form.precio_sesion : null,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al completar');
      }
      setStep(5);
    } catch (e) {
      setError(e.message);
    }
    setSubmitting(false);
  }

  if (error) return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.h1}>Authentic Pilates</h1>
        <p style={styles.error}>{error}</p>
      </div>
    </div>
  );

  if (step === 0) return (
    <div style={styles.container}>
      <div style={styles.card}><p>Cargando...</p></div>
    </div>
  );

  if (step === 5) return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.h1}>Bienvenido/a!</h1>
        <p style={{fontSize: 16, marginTop: 12}}>Tu inscripción en Authentic Pilates está completa.</p>
        <p style={{fontSize: 14, color: '#666', marginTop: 8}}>Jesús se pondrá en contacto contigo para confirmar tu primera sesión.</p>
      </div>
    </div>
  );

  const grupoSeleccionado = linkData?.grupos_disponibles?.find(g => g.id === form.grupo_id);

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.h1}>Authentic Pilates</h1>
        <p style={styles.subtitle}>Formulario de inscripción</p>

        {/* Progress */}
        <div style={styles.progress}>
          {['Datos', 'Salud', 'Servicio', 'Confirmar'].map((label, i) => (
            <div key={i} style={{
              ...styles.progressStep,
              background: step > i ? '#6366f1' : step === i + 1 ? '#818cf8' : '#e5e7eb',
              color: step >= i + 1 ? '#fff' : '#9ca3af',
            }}>{label}</div>
          ))}
        </div>

        {/* Step 1: Datos personales */}
        {step === 1 && (
          <div>
            <h2 style={styles.h2}>Datos personales</h2>
            <input style={styles.input} placeholder="Nombre *" value={form.nombre}
              onChange={e => update('nombre', e.target.value)} />
            <input style={styles.input} placeholder="Apellidos *" value={form.apellidos}
              onChange={e => update('apellidos', e.target.value)} />
            <input style={styles.input} placeholder="Teléfono *" type="tel" value={form.telefono}
              onChange={e => update('telefono', e.target.value)} />
            <input style={styles.input} placeholder="Email" type="email" value={form.email}
              onChange={e => update('email', e.target.value)} />
            <input style={styles.input} placeholder="Fecha nacimiento" type="date"
              value={form.fecha_nacimiento} onChange={e => update('fecha_nacimiento', e.target.value)} />
            <input style={styles.input} placeholder="NIF (opcional)" value={form.nif}
              onChange={e => update('nif', e.target.value)} />
            <button style={styles.btn}
              disabled={!form.nombre || !form.apellidos || !form.telefono}
              onClick={() => setStep(2)}>Siguiente</button>
          </div>
        )}

        {/* Step 2: Datos clínicos */}
        {step === 2 && (
          <div>
            <h2 style={styles.h2}>Información de salud</h2>
            <p style={{fontSize: 13, color: '#666', marginBottom: 12}}>
              Esta información es confidencial y nos ayuda a adaptar las sesiones a tus necesidades.
            </p>
            <textarea style={styles.textarea} placeholder="Lesiones actuales o pasadas"
              value={form.lesiones} onChange={e => update('lesiones', e.target.value)} />
            <textarea style={styles.textarea} placeholder="Patologías (hernias, escoliosis, etc.)"
              value={form.patologias} onChange={e => update('patologias', e.target.value)} />
            <textarea style={styles.textarea} placeholder="Medicación actual"
              value={form.medicacion} onChange={e => update('medicacion', e.target.value)} />
            <textarea style={styles.textarea} placeholder="Restricciones de movimiento"
              value={form.restricciones} onChange={e => update('restricciones', e.target.value)} />
            <input style={styles.input} placeholder="Médico/fisio que te deriva (opcional)"
              value={form.medico_derivante} onChange={e => update('medico_derivante', e.target.value)} />
            <div style={{display: 'flex', gap: 8}}>
              <button style={styles.btnSecondary} onClick={() => setStep(1)}>Atrás</button>
              <button style={styles.btn} onClick={() => setStep(3)}>Siguiente</button>
            </div>
          </div>
        )}

        {/* Step 3: Servicio */}
        {step === 3 && (
          <div>
            <h2 style={styles.h2}>Elige tu servicio</h2>

            <div style={{display:'flex', gap:8, marginBottom:16}}>
              <button style={form.tipo_contrato==='grupo' ? styles.tabActive : styles.tab}
                onClick={() => update('tipo_contrato','grupo')}>Grupo</button>
              <button style={form.tipo_contrato==='individual' ? styles.tabActive : styles.tab}
                onClick={() => update('tipo_contrato','individual')}>Individual</button>
            </div>

            {form.tipo_contrato === 'grupo' && linkData?.grupos_disponibles && (
              <div>
                {linkData.grupos_disponibles.map(g => (
                  <div key={g.id} onClick={() => update('grupo_id', g.id)}
                    style={{
                      ...styles.grupoCard,
                      border: form.grupo_id === g.id ? '2px solid #6366f1' : '1px solid #e5e7eb',
                    }}>
                    <div style={{fontWeight:600}}>{g.nombre}</div>
                    <div style={{fontSize:13, color:'#666'}}>
                      {g.precio_mensual} EUR/mes · {g.plazas_libres} plazas libres
                    </div>
                  </div>
                ))}
              </div>
            )}

            {form.tipo_contrato === 'individual' && (
              <div>
                <p style={{fontSize:13, color:'#666', marginBottom:8}}>
                  Individual 1x/semana: 35 EUR/sesión · 2x/semana: 30 EUR/sesión
                </p>
                <select style={styles.input} value={form.frecuencia_semanal}
                  onChange={e => {
                    const freq = parseInt(e.target.value);
                    update('frecuencia_semanal', freq);
                    update('precio_sesion', freq >= 2 ? 30 : 35);
                  }}>
                  <option value={1}>1 vez por semana (35 EUR)</option>
                  <option value={2}>2 veces por semana (30 EUR)</option>
                </select>
              </div>
            )}

            <div style={{display: 'flex', gap: 8, marginTop: 16}}>
              <button style={styles.btnSecondary} onClick={() => setStep(2)}>Atrás</button>
              <button style={styles.btn}
                disabled={form.tipo_contrato === 'grupo' && !form.grupo_id}
                onClick={() => setStep(4)}>Siguiente</button>
            </div>
          </div>
        )}

        {/* Step 4: Confirmar */}
        {step === 4 && (
          <div>
            <h2 style={styles.h2}>Confirmar inscripción</h2>

            <div style={styles.summary}>
              <div><strong>{form.nombre} {form.apellidos}</strong></div>
              <div>{form.telefono} {form.email && `· ${form.email}`}</div>
              <div style={{marginTop:8}}>
                {form.tipo_contrato === 'grupo'
                  ? `Grupo: ${grupoSeleccionado?.nombre || '?'} · ${grupoSeleccionado?.precio_mensual} EUR/mes`
                  : `Individual ${form.frecuencia_semanal}x/sem · ${form.precio_sesion} EUR/sesión`
                }
              </div>
            </div>

            <label style={styles.checkbox}>
              <input type="checkbox" checked={form.consentimiento_datos}
                onChange={e => update('consentimiento_datos', e.target.checked)} />
              <span>Acepto el tratamiento de mis datos personales *</span>
            </label>
            <label style={styles.checkbox}>
              <input type="checkbox" checked={form.acepta_normas}
                onChange={e => update('acepta_normas', e.target.checked)} />
              <span>Acepto las normas del estudio (cancelación, recuperación, pagos) *</span>
            </label>
            <label style={styles.checkbox}>
              <input type="checkbox" checked={form.consentimiento_marketing}
                onChange={e => update('consentimiento_marketing', e.target.checked)} />
              <span>Acepto recibir comunicaciones comerciales</span>
            </label>

            <div style={{display: 'flex', gap: 8, marginTop: 16}}>
              <button style={styles.btnSecondary} onClick={() => setStep(3)}>Atrás</button>
              <button style={styles.btn}
                disabled={!form.consentimiento_datos || !form.acepta_normas || submitting}
                onClick={submit}>
                {submitting ? 'Procesando...' : 'Completar inscripción'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: '#f9fafb', padding: 16, fontFamily: "'Inter', -apple-system, sans-serif",
  },
  card: {
    background: '#fff', borderRadius: 16, padding: 24, maxWidth: 480, width: '100%',
    boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
  },
  h1: { fontSize: 22, fontWeight: 700, margin: 0 },
  h2: { fontSize: 17, fontWeight: 600, margin: '16px 0 12px' },
  subtitle: { fontSize: 14, color: '#6b7280', marginTop: 4 },
  progress: { display: 'flex', gap: 4, margin: '16px 0' },
  progressStep: {
    flex: 1, textAlign: 'center', padding: '6px 0', borderRadius: 6,
    fontSize: 12, fontWeight: 500,
  },
  input: {
    width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: 8,
    fontSize: 14, marginBottom: 8, outline: 'none', boxSizing: 'border-box',
  },
  textarea: {
    width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: 8,
    fontSize: 14, marginBottom: 8, outline: 'none', minHeight: 60, resize: 'vertical',
    boxSizing: 'border-box',
  },
  btn: {
    width: '100%', padding: '12px', background: '#6366f1', color: '#fff', border: 'none',
    borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: 'pointer', marginTop: 8,
  },
  btnSecondary: {
    flex: 1, padding: '10px', background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db',
    borderRadius: 8, fontSize: 14, cursor: 'pointer', marginTop: 8,
  },
  tab: {
    flex: 1, padding: '10px', background: '#f3f4f6', border: '1px solid #d1d5db',
    borderRadius: 8, fontSize: 14, cursor: 'pointer', textAlign: 'center',
  },
  tabActive: {
    flex: 1, padding: '10px', background: '#6366f1', color: '#fff', border: 'none',
    borderRadius: 8, fontSize: 14, cursor: 'pointer', textAlign: 'center',
  },
  grupoCard: {
    padding: 12, borderRadius: 8, marginBottom: 8, cursor: 'pointer',
    transition: 'border 0.15s',
  },
  summary: {
    background: '#f9fafb', padding: 12, borderRadius: 8, marginBottom: 16, fontSize: 14,
  },
  checkbox: {
    display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 8, fontSize: 13,
    cursor: 'pointer',
  },
  error: { color: '#ef4444', marginTop: 12, fontSize: 14 },
};
