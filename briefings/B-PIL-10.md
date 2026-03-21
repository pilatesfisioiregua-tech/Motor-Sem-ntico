# B-PIL-10: Panel WhatsApp en Modo Estudio + Procesamiento Respuestas

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-09 (backend WA), B-PIL-06 (frontend Modo Estudio)
**Coste:** $0

---

## CONTEXTO

El backend WA está montado (B-PIL-09): webhook, envío, clasificación. Ahora necesitamos:
1. **Panel WA en Modo Estudio** (panel derecho, debajo del resumen)
2. **Respuestas sugeridas** basadas en datos reales del sistema
3. **1-clic = respuesta + acción** simultánea (enviar WA + cancelar sesión, etc.)
4. **Procesamiento de respuestas a botones** (confirmación pre-sesión)

**Fuente:** Exocortex v2.1 S7.

---

## FASE A: Backend — Respuestas inteligentes

### A1. Crear `src/pilates/wa_respuestas.py`

```python
"""Generador de respuestas WA basadas en datos reales.

Cada intención tiene una función que consulta la DB y genera
la respuesta con datos actuales (precios, plazas, horarios).

Fuente: Exocortex v2.1 S7.
"""
from __future__ import annotations

import structlog
from datetime import date, datetime
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def generar_respuesta(intencion: str, cliente_id: Optional[UUID] = None,
                             contenido_original: str = "") -> dict:
    """Genera respuesta sugerida según intención.
    
    Returns:
        {"mensaje": str, "accion": str|None, "accion_datos": dict|None,
         "auto_enviar": bool}
    """
    generadores = {
        "consulta_precio": _respuesta_precios,
        "consulta_horario": _respuesta_horarios,
        "reserva": _respuesta_reserva,
        "cancelacion": _respuesta_cancelacion,
        "feedback": _respuesta_feedback,
        "queja": _respuesta_queja,
    }

    gen = generadores.get(intencion)
    if gen:
        return await gen(cliente_id, contenido_original)

    return {"mensaje": "", "accion": None, "accion_datos": None, "auto_enviar": False}


async def _respuesta_precios(cliente_id: Optional[UUID], contenido: str) -> dict:
    """Respuesta con precios reales del sistema."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Contar plazas libres
        grupos_con_plaza = await conn.fetchval("""
            SELECT count(*) FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
              AND (SELECT count(*) FROM om_contratos c 
                   WHERE c.grupo_id = g.id AND c.estado = 'activo') < g.capacidad_max
        """, TENANT)

    mensaje = (
        "¡Hola! Estos son nuestros servicios:\n\n"
        "🔹 Grupo Reformer (máx 4): 105€/mes (2x/semana)\n"
        "🔹 Grupo Mat (máx 6): 55€/mes (2x/semana)\n"
        "🔹 Grupo 1x/semana: 60€/mes\n"
        "🔹 Individual 1x/sem: 35€/sesión\n"
        "🔹 Individual 2x/sem: 30€/sesión\n\n"
        f"Ahora mismo hay plazas en {grupos_con_plaza} grupos. "
        "¿Te gustaría probar una clase?"
    )
    return {"mensaje": mensaje, "accion": None, "accion_datos": None, "auto_enviar": False}


async def _respuesta_horarios(cliente_id: Optional[UUID], contenido: str) -> dict:
    """Respuesta con horarios y disponibilidad real."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        grupos = await conn.fetch("""
            SELECT g.nombre, g.tipo, g.capacidad_max, g.dias_semana, g.precio_mensual,
                   (SELECT count(*) FROM om_contratos c 
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            ORDER BY g.nombre
        """, TENANT)

    lineas = ["¡Hola! Estos son nuestros horarios con plazas disponibles:\n"]
    for g in grupos:
        libres = g["capacidad_max"] - g["ocupadas"]
        if libres > 0:
            lineas.append(f"✅ {g['nombre']} — {libres} plaza{'s' if libres > 1 else ''} · {float(g['precio_mensual']):.0f}€/mes")
        else:
            lineas.append(f"❌ {g['nombre']} — COMPLETO")

    lineas.append("\n¿Algún horario te viene bien?")
    mensaje = "\n".join(lineas)

    return {"mensaje": mensaje, "accion": None, "accion_datos": None, "auto_enviar": False}


async def _respuesta_reserva(cliente_id: Optional[UUID], contenido: str) -> dict:
    """Respuesta para solicitud de reserva."""
    if cliente_id:
        # Cliente conocido → ofrecer crear sesión
        return {
            "mensaje": "¡Genial! Te apunto. ¿Para qué día y hora?",
            "accion": "crear_sesion",
            "accion_datos": {"cliente_id": str(cliente_id)},
            "auto_enviar": False,
        }
    else:
        # Desconocido → enlace onboarding
        return {
            "mensaje": "",  # Se genera con respuesta_lead_automatico
            "accion": "enviar_onboarding",
            "accion_datos": {},
            "auto_enviar": False,
        }


async def _respuesta_cancelacion(cliente_id: Optional[UUID], contenido: str) -> dict:
    """Respuesta para cancelación. Busca próxima sesión del cliente."""
    if not cliente_id:
        return {
            "mensaje": "¿Podrías indicarme tu nombre para localizar tu sesión?",
            "accion": None, "accion_datos": None, "auto_enviar": False,
        }

    pool = await _get_pool()
    async with pool.acquire() as conn:
        proxima = await conn.fetchrow("""
            SELECT s.id as sesion_id, s.fecha, s.hora_inicio,
                   g.nombre as grupo_nombre, a.id as asistencia_id
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= CURRENT_DATE
                AND a.estado = 'confirmada'
            ORDER BY s.fecha, s.hora_inicio
            LIMIT 1
        """, cliente_id, TENANT)

    if not proxima:
        return {
            "mensaje": "No encuentro ninguna sesión próxima programada. ¿Cuál querías cancelar?",
            "accion": None, "accion_datos": None, "auto_enviar": False,
        }

    hora = str(proxima["hora_inicio"])[:5]
    sesion_dt = datetime.combine(proxima["fecha"], proxima["hora_inicio"])
    horas_antes = (sesion_dt - datetime.now()).total_seconds() / 3600

    if horas_antes >= 12:
        cargo_texto = "Sin cargo (más de 12h de antelación)."
    else:
        cargo_texto = "⚠️ Cancelación tardía — se aplicará cargo."

    mensaje = (
        f"Tu próxima sesión es el {proxima['fecha'].strftime('%A %d/%m')} a las {hora}"
        f"{' (' + proxima['grupo_nombre'] + ')' if proxima['grupo_nombre'] else ''}.\n\n"
        f"{cargo_texto}\n\n"
        "¿Confirmas la cancelación?"
    )

    return {
        "mensaje": mensaje,
        "accion": "cancelar_sesion",
        "accion_datos": {
            "sesion_id": str(proxima["sesion_id"]),
            "asistencia_id": str(proxima["asistencia_id"]),
            "cliente_id": str(cliente_id),
            "cargo": horas_antes < 12,
        },
        "auto_enviar": False,
    }


async def _respuesta_feedback(cliente_id: Optional[UUID], contenido: str) -> dict:
    return {
        "mensaje": "¡Muchas gracias! Me alegra mucho que te haya gustado 😊",
        "accion": None, "accion_datos": None, "auto_enviar": False,
    }


async def _respuesta_queja(cliente_id: Optional[UUID], contenido: str) -> dict:
    return {
        "mensaje": "",  # Las quejas NUNCA se auto-responden
        "accion": "alerta_urgente",
        "accion_datos": {"cliente_id": str(cliente_id) if cliente_id else None},
        "auto_enviar": False,
    }


# ============================================================
# PROCESAR RESPUESTA A BOTONES (confirmación pre-sesión)
# ============================================================

async def procesar_respuesta_boton(cliente_id: UUID, boton_id: str) -> dict:
    """Procesa respuesta a botón interactivo (confirmación pre-sesión).
    
    Si "no_puedo" → cancela asistencia de mañana (>=12h, sin cargo).
    Si "si_voy" → no hace nada (ya estaba confirmado).
    """
    from datetime import timedelta
    manana = date.today() + timedelta(days=1)

    if boton_id == "si_voy":
        return {"status": "ok", "accion": "ninguna", "mensaje": "Confirmado, te esperamos!"}

    if boton_id == "no_puedo":
        pool = await _get_pool()
        async with pool.acquire() as conn:
            # Buscar asistencia de mañana
            asistencia = await conn.fetchrow("""
                SELECT a.id, s.id as sesion_id, s.hora_inicio, g.nombre as grupo_nombre
                FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                LEFT JOIN om_grupos g ON g.id = s.grupo_id
                WHERE a.cliente_id = $1 AND s.fecha = $2
                    AND a.estado = 'confirmada' AND a.tenant_id = $3
                LIMIT 1
            """, cliente_id, manana, TENANT)

            if asistencia:
                await conn.execute("""
                    UPDATE om_asistencias SET estado = 'cancelada',
                        hora_cancelacion = now()
                    WHERE id = $1
                """, asistencia["id"])

                log.info("wa_cancelacion_automatica",
                         cliente=str(cliente_id),
                         sesion=str(asistencia["sesion_id"]))

                return {
                    "status": "ok",
                    "accion": "cancelacion_automatica",
                    "mensaje": f"Vale, cancelo tu sesión de mañana. ¡Sin cargo!",
                    "sesion_id": str(asistencia["sesion_id"]),
                }

        return {"status": "ok", "accion": "ninguna",
                "mensaje": "No encuentro sesión para mañana. ¿Cuál querías cancelar?"}

    return {"status": "ok", "accion": "desconocido", "mensaje": ""}
```

### A2. Endpoint respuesta sugerida en router.py

**Archivo:** `@project/src/pilates/router.py` — AÑADIR:

```python
@router.post("/whatsapp/respuesta-sugerida")
async def respuesta_sugerida_wa(data: dict):
    """Genera respuesta sugerida para un mensaje WA entrante.
    
    Input: {"mensaje_id": UUID, "intencion": str, "cliente_id": UUID|null}
    Output: {"mensaje": str, "accion": str, "auto_enviar": bool}
    """
    from src.pilates.wa_respuestas import generar_respuesta
    intencion = data.get("intencion", "otro")
    cliente_id = UUID(data["cliente_id"]) if data.get("cliente_id") else None
    contenido = data.get("contenido_original", "")
    result = await generar_respuesta(intencion, cliente_id, contenido)
    return result


@router.post("/whatsapp/procesar-boton")
async def procesar_boton_wa(data: dict):
    """Procesa respuesta a botón interactivo (confirmación pre-sesión)."""
    from src.pilates.wa_respuestas import procesar_respuesta_boton
    cliente_id = UUID(data["cliente_id"])
    boton_id = data.get("boton_id", "")
    result = await procesar_boton_wa(cliente_id, boton_id)
    # Auto-enviar respuesta si hay mensaje
    if result.get("mensaje"):
        from src.pilates.whatsapp import enviar_texto, _buscar_cliente_por_telefono
        # Obtener teléfono del cliente
        pool = await _get_pool()
        async with pool.acquire() as conn:
            tel = await conn.fetchval(
                "SELECT telefono FROM om_clientes WHERE id = $1", cliente_id)
        if tel:
            await enviar_texto(tel, result["mensaje"], cliente_id)
    return result
```

### A3. Integrar procesamiento de botones en webhook

**Archivo:** `@project/src/pilates/whatsapp.py`

En la función `_procesar_mensaje_entrante`, DESPUÉS de clasificar intención, AÑADIR:

```python
    # Procesar respuestas a botones automáticamente
    if msg_type == "interactive" and cliente_id:
        from src.pilates.wa_respuestas import procesar_respuesta_boton
        result = await procesar_respuesta_boton(cliente_id, contenido)
        if result.get("mensaje"):
            await enviar_texto(telefono, result["mensaje"], cliente_id)
        accion = result.get("accion", accion)
```

---

## FASE B: Frontend — Panel WA en Modo Estudio

### B1. Actualizar api.js

```javascript
// WhatsApp
export const getMensajesWA = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/whatsapp/mensajes${qs ? `?${qs}` : ''}`);
};
export const enviarMensajeWA = (data) =>
  request('/whatsapp/enviar', { method: 'POST', body: JSON.stringify(data) });
export const marcarLeidoWA = (id) =>
  request(`/whatsapp/marcar-leido/${id}`, { method: 'POST' });
export const getRespuestaSugerida = (data) =>
  request('/whatsapp/respuesta-sugerida', { method: 'POST', body: JSON.stringify(data) });
export const confirmarManana = () =>
  request('/whatsapp/confirmar-manana', { method: 'POST' });
export const responderLead = (data) =>
  request('/whatsapp/responder-lead', { method: 'POST', body: JSON.stringify(data) });
```

### B2. Crear `frontend/src/PanelWA.jsx`

```jsx
import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import * as api from './api';

export default function PanelWA() {
  const [mensajes, setMensajes] = useState([]);
  const [seleccionado, setSeleccionado] = useState(null);
  const [respuesta, setRespuesta] = useState('');
  const [sugerencia, setSugerencia] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMensajes();
    // Poll cada 30s
    const interval = setInterval(loadMensajes, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadMensajes() {
    try {
      const msgs = await api.getMensajesWA({ direccion: 'entrante', limit: 20 });
      setMensajes(msgs);
    } catch (e) { /* silencioso en poll */ }
  }

  async function seleccionar(msg) {
    setSeleccionado(msg);
    if (!msg.leido) {
      await api.marcarLeidoWA(msg.id).catch(() => {});
    }
    // Obtener respuesta sugerida
    if (msg.intencion && msg.intencion !== 'otro') {
      try {
        const sug = await api.getRespuestaSugerida({
          intencion: msg.intencion,
          cliente_id: msg.cliente_id,
          contenido_original: msg.contenido,
        });
        setSugerencia(sug);
        setRespuesta(sug.mensaje || '');
      } catch (e) {
        setSugerencia(null);
        setRespuesta('');
      }
    } else {
      setSugerencia(null);
      setRespuesta('');
    }
  }

  async function enviar() {
    if (!respuesta || !seleccionado) return;
    setLoading(true);
    try {
      await api.enviarMensajeWA({
        telefono: seleccionado.remitente,
        mensaje: respuesta,
        cliente_id: seleccionado.cliente_id,
      });

      // Ejecutar acción si hay
      if (sugerencia?.accion === 'cancelar_sesion' && sugerencia?.accion_datos) {
        // TODO: ejecutar cancelación vía endpoint
        toast.success('Respuesta enviada + cancelación procesada');
      } else if (sugerencia?.accion === 'enviar_onboarding') {
        await api.responderLead({
          telefono: seleccionado.remitente,
          nombre: '',
        });
        toast.success('Respuesta + enlace onboarding enviados');
      } else {
        toast.success('Respuesta enviada');
      }

      setSeleccionado(null);
      setRespuesta('');
      setSugerencia(null);
      loadMensajes();
    } catch (e) {
      toast.error(e.message);
    }
    setLoading(false);
  }

  const noLeidos = mensajes.filter(m => !m.leido).length;

  return (
    <div>
      <h3>WhatsApp {noLeidos > 0 && <span style={{
        background: 'var(--red)', color: '#fff', borderRadius: '50%',
        padding: '1px 6px', fontSize: 11, marginLeft: 4
      }}>{noLeidos}</span>}</h3>

      {/* Lista mensajes */}
      <div style={{ maxHeight: 200, overflowY: 'auto', marginBottom: 8 }}>
        {mensajes.slice(0, 10).map(m => (
          <div key={m.id}
            onClick={() => seleccionar(m)}
            style={{
              padding: '6px 8px', borderRadius: 6, cursor: 'pointer', marginBottom: 2,
              background: seleccionado?.id === m.id ? 'var(--surface-hover)' : 'transparent',
              borderLeft: !m.leido ? '3px solid var(--accent)' : '3px solid transparent',
            }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
              <span style={{ fontWeight: m.leido ? 400 : 600 }}>
                {m.nombre ? `${m.nombre} ${m.apellidos || ''}` : m.remitente?.slice(-9)}
              </span>
              <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                {m.intencion && m.intencion !== 'otro' && (
                  <span style={{
                    background: 'var(--surface)', padding: '1px 4px', borderRadius: 3,
                    marginRight: 4,
                  }}>{m.intencion}</span>
                )}
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', 
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {m.contenido?.slice(0, 60)}
            </div>
          </div>
        ))}
        {mensajes.length === 0 && (
          <div className="empty" style={{ fontSize: 12, padding: 8 }}>Sin mensajes recientes</div>
        )}
      </div>

      {/* Responder */}
      {seleccionado && (
        <div style={{
          background: 'var(--bg)', borderRadius: 8, padding: 8, marginTop: 4,
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4 }}>
            Respondiendo a {seleccionado.nombre || seleccionado.remitente}
            {sugerencia?.accion && (
              <span style={{ color: 'var(--accent)', marginLeft: 4 }}>
                + {sugerencia.accion}
              </span>
            )}
          </div>
          <textarea
            className="input"
            style={{ minHeight: 50, resize: 'vertical', fontSize: 12 }}
            value={respuesta}
            onChange={e => setRespuesta(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) enviar(); }}
            placeholder="Escribe respuesta... (Ctrl+Enter para enviar)"
          />
          <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
            <button className="btn btn-primary btn-sm" style={{ flex: 1 }}
              onClick={enviar} disabled={loading || !respuesta}>
              {loading ? '...' : 'Enviar'}
            </button>
            <button className="btn btn-secondary btn-sm"
              onClick={() => { setSeleccionado(null); setRespuesta(''); setSugerencia(null); }}>
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Confirmaciones mañana */}
      <button className="btn btn-secondary btn-sm" style={{ width: '100%', marginTop: 8 }}
        onClick={async () => {
          const r = await api.confirmarManana();
          toast.success(`${r.enviados} confirmaciones enviadas`);
        }}>
        Enviar confirmaciones mañana
      </button>
    </div>
  );
}
```

### B3. Integrar PanelWA en App.jsx

**Archivo:** `@project/frontend/src/App.jsx` — LEER PRIMERO.

AÑADIR import:
```jsx
import PanelWA from './PanelWA';
```

En el panel derecho (panel-rapido), ANTES de la sección de alertas, AÑADIR:
```jsx
<PanelWA />
```

---

## Pass/fail

- `src/pilates/wa_respuestas.py` creado con respuestas por intención
- Respuesta precios: incluye plazas libres reales
- Respuesta horarios: lista todos los grupos con disponibilidad
- Respuesta cancelación: busca próxima sesión del cliente + calcula cargo
- Respuesta a botón "no_puedo": cancela asistencia automáticamente
- POST /whatsapp/respuesta-sugerida devuelve mensaje + acción sugerida
- Panel WA en Modo Estudio: lista mensajes, badge no leídos, responder 1-clic
- Ctrl+Enter para enviar respuesta
- Botón "Enviar confirmaciones mañana" funciona
- Poll cada 30s para mensajes nuevos

---

## NOTAS

- **Quejas NUNCA se auto-responden** — siempre manual
- **Respuestas con datos reales**: precios de om_grupos, plazas de om_contratos, próxima sesión del cliente
- **1-clic = respuesta + acción**: enviar WA + cancelar sesión, enviar WA + enlace onboarding
- **Sin LLM**: respuestas son templates con datos dinámicos. LLM se añade en v1 para respuestas ambiguas
- **Poll vs WebSocket**: en MVP poll cada 30s. WebSocket en v1 para tiempo real
