# B-PIL-07: Onboarding Self-Service — QR/Enlace + Formulario + Contrato Digital

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-04 (endpoints clientes/contratos/cargos)
**Coste:** $0

---

## CONTEXTO

Jesús necesita dar de alta clientes sin teclear datos. Flujo actual: 5-10 min por alta manual. Flujo objetivo: 5 segundos.

```
Jesús crea lead (nombre+tel) → enlace generado → envía por WA → 
cliente rellena desde su móvil → exocortex crea todo automáticamente →
Jesús recibe notificación
```

La tabla `om_onboarding_links` ya existe (B-PIL-01). Falta:
1. Backend: endpoints para generar/consultar enlaces + endpoint público para completar
2. Frontend: formulario público (sin auth) que el cliente rellena en su móvil

**Fuente:** Exocortex v2.1 S16.1

---

## FASE A: Backend — Endpoints onboarding en router.py

**Archivo:** `@project/src/pilates/router.py` — LEER PRIMERO. AÑADIR schemas + endpoints.

### Schemas

```python
class OnboardingLinkCreate(BaseModel):
    """Jesús crea un enlace para un lead."""
    nombre_provisional: str
    telefono: str


class OnboardingComplete(BaseModel):
    """El cliente completa el formulario de onboarding."""
    # Datos personales
    nombre: str
    apellidos: str
    telefono: str
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nif: Optional[str] = None
    direccion: Optional[str] = None

    # Datos clínicos (texto libre, se guardará cifrado en v2)
    lesiones: Optional[str] = None
    patologias: Optional[str] = None
    medicacion: Optional[str] = None
    restricciones: Optional[str] = None
    medico_derivante: Optional[str] = None

    # Servicio seleccionado
    tipo_contrato: str = Field(pattern="^(grupo|individual)$")
    grupo_id: Optional[UUID] = None          # si grupo
    frecuencia_semanal: Optional[int] = None  # si individual
    precio_sesion: Optional[float] = None     # si individual
    ciclo_cobro: Optional[str] = None         # si individual

    # Consentimientos
    consentimiento_datos: bool = True
    consentimiento_marketing: bool = False
    consentimiento_compartir_tenants: bool = False
    acepta_normas: bool = True

    # Pago
    metodo_pago: Optional[str] = None  # tpv, bizum, efectivo, transferencia
```

### Endpoints

```python
# ============================================================
# ONBOARDING SELF-SERVICE
# ============================================================

@router.post("/onboarding/crear-enlace", status_code=201)
async def crear_enlace_onboarding(data: OnboardingLinkCreate):
    """Jesús crea enlace de onboarding para un lead.
    
    Modo Estudio: F7 o botón "Nuevo cliente" → nombre + teléfono → enlace generado.
    """
    import secrets
    pool = await _get_pool()
    token = secrets.token_urlsafe(32)
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_onboarding_links (tenant_id, token, nombre_provisional, telefono,
                fecha_expiracion)
            VALUES ($1, $2, $3, $4, now() + interval '7 days')
            RETURNING id, token
        """, TENANT, token, data.nombre_provisional, data.telefono)
    
    # URL del formulario público
    base_url = "https://motor-semantico-omni.fly.dev"
    enlace = f"{base_url}/onboarding/{token}"
    
    log.info("onboarding_enlace_creado", token=token[:8],
             nombre=data.nombre_provisional)
    return {
        "id": str(row["id"]),
        "token": token,
        "enlace": enlace,
        "wa_mensaje": f"Hola {data.nombre_provisional}! Para inscribirte en Authentic Pilates, "
                      f"rellena esta ficha: {enlace}",
        "expira_en": "7 días",
    }


@router.get("/onboarding/{token}")
async def obtener_onboarding(token: str):
    """Endpoint público: devuelve datos del enlace + grupos disponibles.
    
    El frontend del formulario llama aquí para cargar el formulario
    con datos pre-rellenados y grupos con plazas.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        link = await conn.fetchrow("""
            SELECT * FROM om_onboarding_links WHERE token = $1 AND tenant_id = $2
        """, token, TENANT)
        
        if not link:
            raise HTTPException(404, "Enlace no encontrado")
        if link["estado"] == "completado":
            raise HTTPException(410, "Este enlace ya fue utilizado")
        if link["estado"] == "expirado" or (link["fecha_expiracion"] and 
            link["fecha_expiracion"] < datetime.now(link["fecha_expiracion"].tzinfo)):
            raise HTTPException(410, "Este enlace ha expirado")
        
        # Grupos con plazas disponibles
        grupos = await conn.fetch("""
            SELECT g.id, g.nombre, g.tipo, g.capacidad_max, g.dias_semana,
                   g.precio_mensual, g.frecuencia_semanal,
                   (SELECT count(*) FROM om_contratos c 
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            ORDER BY g.nombre
        """, TENANT)
        
        grupos_disponibles = []
        for g in grupos:
            if g["ocupadas"] < g["capacidad_max"]:
                grupos_disponibles.append({
                    "id": str(g["id"]),
                    "nombre": g["nombre"],
                    "tipo": g["tipo"],
                    "precio_mensual": float(g["precio_mensual"]),
                    "frecuencia_semanal": g["frecuencia_semanal"],
                    "plazas_libres": g["capacidad_max"] - g["ocupadas"],
                    "dias_semana": g["dias_semana"],
                })
    
    return {
        "nombre_provisional": link["nombre_provisional"],
        "telefono": link["telefono"],
        "grupos_disponibles": grupos_disponibles,
        "precios": {
            "individual_1x": 35.00,
            "individual_2x": 30.00,
            "grupo_estandar": 105.00,
            "grupo_mat": 55.00,
            "grupo_1x": 60.00,
        },
    }


@router.post("/onboarding/{token}/completar")
async def completar_onboarding(token: str, data: OnboardingComplete):
    """Endpoint público: el cliente completa el formulario.
    
    Crea: om_clientes + om_cliente_tenant + om_datos_clinicos + om_contratos.
    Si grupo: valida plaza disponible.
    Marca enlace como completado.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Verificar enlace válido
        link = await conn.fetchrow("""
            SELECT * FROM om_onboarding_links WHERE token = $1 AND tenant_id = $2
        """, token, TENANT)
        
        if not link:
            raise HTTPException(404, "Enlace no encontrado")
        if link["estado"] != "pendiente":
            raise HTTPException(410, "Este enlace ya no es válido")
        
        async with conn.transaction():
            # 1. Crear cliente
            cliente_row = await conn.fetchrow("""
                INSERT INTO om_clientes (nombre, apellidos, telefono, email,
                    fecha_nacimiento, nif, direccion,
                    metodo_pago_habitual,
                    consentimiento_datos, consentimiento_marketing,
                    consentimiento_compartir_tenants, fecha_consentimiento)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, now())
                RETURNING id
            """, data.nombre, data.apellidos, data.telefono, data.email,
                data.fecha_nacimiento, data.nif, data.direccion,
                data.metodo_pago,
                data.consentimiento_datos, data.consentimiento_marketing,
                data.consentimiento_compartir_tenants)
            
            cliente_id = cliente_row["id"]
            
            # 2. Crear relación tenant
            await conn.execute("""
                INSERT INTO om_cliente_tenant (cliente_id, tenant_id, estado, fuente_captacion)
                VALUES ($1, $2, 'activo', 'onboarding_selfservice')
            """, cliente_id, TENANT)
            
            # 3. Datos clínicos (si hay)
            datos_clinicos = []
            if data.lesiones:
                datos_clinicos.append(("restriccion", "Lesiones", data.lesiones))
            if data.patologias:
                datos_clinicos.append(("diagnostico", "Patologías", data.patologias))
            if data.medicacion:
                datos_clinicos.append(("medicacion", "Medicación", data.medicacion))
            if data.restricciones:
                datos_clinicos.append(("restriccion", "Restricciones", data.restricciones))
            if data.medico_derivante:
                datos_clinicos.append(("derivacion_medica", "Derivado por", data.medico_derivante))
            
            for tipo, titulo, contenido in datos_clinicos:
                await conn.execute("""
                    INSERT INTO om_datos_clinicos (cliente_id, tenant_id, tipo, titulo,
                        contenido, autor, visible_para, consentimiento_registrado, base_legal)
                    VALUES ($1, $2, $3, $4, $5, 'cliente_autoregistro', $6, true, 'consentimiento')
                """, cliente_id, TENANT, tipo, titulo, contenido,
                    [TENANT])  # visible solo para este tenant
            
            # 4. Crear contrato
            if data.tipo_contrato == "grupo" and data.grupo_id:
                # Validar plaza disponible
                grupo = await conn.fetchrow("""
                    SELECT capacidad_max FROM om_grupos WHERE id = $1 AND tenant_id = $2
                """, data.grupo_id, TENANT)
                if not grupo:
                    raise HTTPException(404, "Grupo no encontrado")
                
                ocupados = await conn.fetchval("""
                    SELECT count(*) FROM om_contratos
                    WHERE grupo_id = $1 AND tenant_id = $2 AND estado = 'activo'
                """, data.grupo_id, TENANT)
                if ocupados >= grupo["capacidad_max"]:
                    raise HTTPException(409, "Grupo lleno, selecciona otro")
                
                # Obtener precio del grupo
                precio = await conn.fetchval(
                    "SELECT precio_mensual FROM om_grupos WHERE id = $1", data.grupo_id)
                
                contrato_row = await conn.fetchrow("""
                    INSERT INTO om_contratos (tenant_id, cliente_id, tipo, grupo_id,
                        precio_mensual, fecha_inicio)
                    VALUES ($1, $2, 'grupo', $3, $4, CURRENT_DATE)
                    RETURNING id
                """, TENANT, cliente_id, data.grupo_id, precio)
            
            elif data.tipo_contrato == "individual":
                precio = data.precio_sesion or 35.00
                contrato_row = await conn.fetchrow("""
                    INSERT INTO om_contratos (tenant_id, cliente_id, tipo,
                        frecuencia_semanal, precio_sesion, ciclo_cobro, fecha_inicio)
                    VALUES ($1, $2, 'individual', $3, $4, $5, CURRENT_DATE)
                    RETURNING id
                """, TENANT, cliente_id,
                    data.frecuencia_semanal or 1, precio,
                    data.ciclo_cobro or 'sesion')
            
            contrato_id = contrato_row["id"]
            
            # 5. Marcar enlace como completado
            await conn.execute("""
                UPDATE om_onboarding_links
                SET estado = 'completado', cliente_id = $1,
                    fecha_completado = now()
                WHERE token = $2
            """, cliente_id, token)
    
    log.info("onboarding_completado", cliente_id=str(cliente_id),
             nombre=f"{data.nombre} {data.apellidos}",
             tipo=data.tipo_contrato)
    
    return {
        "status": "ok",
        "cliente_id": str(cliente_id),
        "contrato_id": str(contrato_id),
        "mensaje": f"Bienvenido/a {data.nombre}! Tu inscripción está completa.",
    }


@router.get("/onboarding/enlaces")
async def listar_enlaces_onboarding(estado: Optional[str] = None):
    """Lista enlaces de onboarding creados (para Jesús)."""
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT l.*, c.nombre, c.apellidos
                FROM om_onboarding_links l
                LEFT JOIN om_clientes c ON c.id = l.cliente_id
                WHERE l.tenant_id = $1 AND l.estado = $2
                ORDER BY l.created_at DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT l.*, c.nombre, c.apellidos
                FROM om_onboarding_links l
                LEFT JOIN om_clientes c ON c.id = l.cliente_id
                WHERE l.tenant_id = $1
                ORDER BY l.created_at DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]
```

---

## FASE B: Frontend — Formulario público

### B1. Crear `frontend/src/Onboarding.jsx`

Este componente se renderiza cuando la URL es `/onboarding/{token}`. Es público (sin auth), responsive (móvil-first), y guía al cliente paso a paso.

```jsx
import { useState, useEffect } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

export default function Onboarding({ token }) {
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
    fetch(`${BASE}/pilates/onboarding/${token}`)
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
      const res = await fetch(`${BASE}/pilates/onboarding/${token}/completar`, {
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
      const result = await res.json();
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
```

### B2. Integrar en App.jsx

**Archivo:** `@project/frontend/src/App.jsx` — LEER PRIMERO.

AÑADIR al inicio del archivo, después de los imports:

```jsx
import Onboarding from './Onboarding';
```

AÑADIR antes del `return` principal del componente App:

```jsx
  // Routing simple: si la URL es /onboarding/{token}, mostrar formulario público
  const path = window.location.pathname;
  const onboardingMatch = path.match(/^\/onboarding\/(.+)$/);
  if (onboardingMatch) {
    return <Onboarding token={onboardingMatch[1]} />;
  }
```

### B3. Servir ruta /onboarding/{token} desde FastAPI

**Archivo:** `@project/src/main.py` — LEER PRIMERO.

Donde se monta el frontend estático, AÑADIR antes del mount de `/assets`:

```python
    @app.get("/onboarding/{token}")
    async def onboarding_page(token: str):
        """Sirve el HTML del formulario de onboarding."""
        return FileResponse(frontend_dist / "index.html")
```

Esto hace que `/onboarding/{cualquier-token}` sirva el SPA, y el componente React se encarga del routing.

---

## FASE C: Integrar en Modo Estudio

### C1. Añadir botón "Nuevo cliente" en el panel derecho de App.jsx

En el panel-rapido, AÑADIR sección:

```jsx
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
```

Y añadir los states y la función en App():

```jsx
const [showNuevoCliente, setShowNuevoCliente] = useState(false);
const [nuevoNombre, setNuevoNombre] = useState('');
const [nuevoTel, setNuevoTel] = useState('');
const [enlaceGenerado, setEnlaceGenerado] = useState(null);

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
```

Y en api.js:

```javascript
export const crearEnlaceOnboarding = (data) =>
  request('/onboarding/crear-enlace', { method: 'POST', body: JSON.stringify(data) });
```

Y atajo F7 en el handler de teclado:

```javascript
case 'F7': e.preventDefault(); setShowNuevoCliente(prev => !prev); break;
```

---

## Pass/fail

- POST /pilates/onboarding/crear-enlace genera token + URL + mensaje WA listo
- GET /pilates/onboarding/{token} devuelve datos pre-rellenados + grupos con plazas
- POST /pilates/onboarding/{token}/completar crea cliente + tenant + clínicos + contrato
- Enlace expirado/usado devuelve 410
- Grupo lleno devuelve 409
- Frontend formulario: 4 pasos, responsive, funciona en móvil
- Modo Estudio: F7 → nombre + tel → enlace → copiar mensaje WA (5 seg total)
- GET /pilates/onboarding/enlaces lista todos los enlaces creados
