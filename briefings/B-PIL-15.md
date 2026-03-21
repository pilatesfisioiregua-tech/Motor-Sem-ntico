# B-PIL-15: Bloque Voz — Motor Tridimensional + Capa A + ISP

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-04 (datos operativos), B-PIL-12 (briefing)
**Coste:** ~$0.01/propuesta (1 LLM call por propuesta generada)

---

## CONTEXTO

El Bloque Voz es el sistema proactivo del exocortex: no espera a que Jesús actúe — genera propuestas de comunicación basadas en datos reales. Las tablas om_voz_propuestas, om_voz_telemetria, om_voz_isp, om_voz_capa_a ya existen (B-PIL-01).

**Motor Tridimensional:** 3 ejes generan propuestas:
- **Eje 1 (IRC):** Índice de Relevancia/Conversión del canal
- **Eje 2 (Celda):** Qué celda de la Matriz 7F×3L necesita atención
- **Eje 3 (PCA/Formato):** Qué formato funciona mejor en ese canal

**Capa A:** Datos externos (Google Trends, Perplexity, meteo, etc.) que alimentan las propuestas.

**ISP:** Índice de Salud de Presencia — auditoría de perfiles digitales.

**Fuente:** Exocortex v2.1 S9, S10.

---

## FASE A: Backend — Motor de Propuestas

### A1. Crear `src/pilates/voz.py`

```python
"""Bloque Voz — Motor Tridimensional de propuestas.

Genera propuestas de comunicación basadas en:
1. Datos internos (asistencia, ocupación, deuda, clientes)
2. Datos externos Capa A (mercado, tendencias, clima)
3. Estado ACD del negocio

Cada propuesta tiene canal, tipo, contenido, justificación.
Jesús aprueba/descarta en Modo Estudio o Profundo.

Fuente: Exocortex v2.1 S9.
"""
from __future__ import annotations

import os
import json
import structlog
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"

# Canales y tipos de propuesta
CANALES = ["whatsapp", "google_business", "instagram", "email", "web"]

TIPOS_PROPUESTA = {
    "broadcast": "Mensaje masivo a clientes (WA Business)",
    "respuesta_resena": "Respuesta a reseña Google",
    "contenido": "Post/story para redes",
    "actualizacion_perfil": "Actualizar perfil de negocio",
    "alerta_oportunidad": "Oportunidad detectada",
    "tarea_asistida": "Tarea que requiere acción de Jesús",
}


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# GENERADOR DE PROPUESTAS
# ============================================================

async def generar_propuestas() -> list[dict]:
    """Genera propuestas de Voz basadas en datos internos.
    
    Analiza: ocupación baja, clientes inactivos, estacionalidad,
    deuda antigua, hitos (nuevo cliente, 100 sesiones, etc.).
    
    Returns: lista de propuestas creadas.
    """
    pool = await _get_pool()
    propuestas = []

    async with pool.acquire() as conn:
        # === 1. GRUPOS CON BAJA OCUPACIÓN → proponer contenido ===
        grupos_bajos = await conn.fetch("""
            SELECT g.nombre, g.capacidad_max, g.precio_mensual,
                   (SELECT count(*) FROM om_contratos c
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
        """, TENANT)

        for g in grupos_bajos:
            libres = g["capacidad_max"] - g["ocupadas"]
            pct = g["ocupadas"] / max(g["capacidad_max"], 1)
            if pct < 0.5 and libres >= 2:
                propuestas.append({
                    "canal": "instagram",
                    "tipo": "contenido",
                    "justificacion": f"Grupo {g['nombre']} al {pct*100:.0f}% — {libres} plazas libres. Promocionar.",
                    "contenido_propuesto": {
                        "texto": f"¿Buscas Pilates reformer en grupo reducido? Nos quedan {libres} plazas en {g['nombre']}. Grupos de máximo {g['capacidad_max']} personas. {float(g['precio_mensual']):.0f}€/mes.",
                        "formato": "story",
                        "cta": "DM para info",
                    },
                    "eje2_celda": "F2_Se",  # Captación × Sentido
                })

        # === 2. CLIENTES INACTIVOS (>2 semanas sin asistir) → WA recordatorio ===
        inactivos = await conn.fetch("""
            SELECT DISTINCT c.id, c.nombre, c.apellidos, c.telefono,
                   MAX(s.fecha) as ultima_sesion
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
            JOIN om_asistencias a ON a.cliente_id = c.id
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE ct.estado = 'activo' AND a.estado = 'asistio'
            GROUP BY c.id, c.nombre, c.apellidos, c.telefono
            HAVING MAX(s.fecha) < CURRENT_DATE - interval '14 days'
        """, TENANT)

        for c in inactivos:
            dias = (date.today() - c["ultima_sesion"]).days
            propuestas.append({
                "canal": "whatsapp",
                "tipo": "broadcast",
                "justificacion": f"{c['nombre']} {c['apellidos']} lleva {dias} días sin venir.",
                "contenido_propuesto": {
                    "telefono": c["telefono"],
                    "texto": f"¡Hola {c['nombre']}! Te echamos de menos en el estudio. ¿Va todo bien? Si quieres, reserva tu próxima sesión aquí.",
                    "cliente_id": str(c["id"]),
                },
                "eje2_celda": "F1_S",  # Conservación × Salud
            })

        # === 3. DEUDA ANTIGUA (>30 días) → WA recordatorio pago ===
        deudores = await conn.fetch("""
            SELECT c.cliente_id, cl.nombre, cl.apellidos, cl.telefono,
                   SUM(c.total) as deuda, MIN(c.fecha_cargo) as desde
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            WHERE c.tenant_id = $1 AND c.estado = 'pendiente'
                AND c.fecha_cargo < CURRENT_DATE - interval '30 days'
            GROUP BY c.cliente_id, cl.nombre, cl.apellidos, cl.telefono
        """, TENANT)

        for d in deudores:
            propuestas.append({
                "canal": "whatsapp",
                "tipo": "tarea_asistida",
                "justificacion": f"{d['nombre']} {d['apellidos']} debe {float(d['deuda']):.0f}€ desde {d['desde']}.",
                "contenido_propuesto": {
                    "telefono": d["telefono"],
                    "texto": f"Hola {d['nombre']}, te recuerdo que tienes un pago pendiente de {float(d['deuda']):.0f}€. ¿Te viene bien hacer Bizum esta semana?",
                    "cliente_id": str(d["cliente_id"]),
                },
                "eje2_celda": "F4_S",  # Distribución × Salud
            })

        # === 4. NUEVO MES → sugerir post resumen ===
        if date.today().day <= 3:
            propuestas.append({
                "canal": "instagram",
                "tipo": "contenido",
                "justificacion": "Inicio de mes — buen momento para post de comunidad.",
                "contenido_propuesto": {
                    "texto": "Nuevo mes, nueva energía. Gracias a todos los que habéis venido este mes. Pilates no es solo ejercicio — es invertir en ti.",
                    "formato": "post",
                    "cta": "Etiqueta a alguien que necesita empezar",
                },
                "eje2_celda": "F5_Se",  # Identidad × Sentido
            })

        # === 5. ALTA OCUPACIÓN → sugerir lista de espera / subir precio ===
        total_cap = sum(g["capacidad_max"] for g in grupos_bajos)
        total_ocu = sum(g["ocupadas"] for g in grupos_bajos)
        if total_cap > 0 and total_ocu / total_cap > 0.85:
            propuestas.append({
                "canal": "web",
                "tipo": "alerta_oportunidad",
                "justificacion": f"Ocupación al {total_ocu/total_cap*100:.0f}%. Considerar lista de espera o ajuste de precios.",
                "contenido_propuesto": {
                    "accion": "Crear lista de espera o evaluar nuevo horario",
                    "datos": {"ocupacion_pct": round(total_ocu/total_cap*100, 1)},
                },
                "eje2_celda": "F6_C",  # Adaptación × Continuidad
            })

        # Almacenar propuestas
        creadas = []
        for p in propuestas:
            # Verificar que no existe propuesta similar pendiente
            exists = await conn.fetchval("""
                SELECT 1 FROM om_voz_propuestas
                WHERE tenant_id = $1 AND canal = $2 AND tipo = $3
                    AND estado = 'pendiente'
                    AND justificacion = $4
            """, TENANT, p["canal"], p["tipo"], p["justificacion"])
            if exists:
                continue

            row = await conn.fetchrow("""
                INSERT INTO om_voz_propuestas (tenant_id, canal, tipo, eje2_celda,
                    justificacion, contenido_propuesto)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb) RETURNING id
            """, TENANT, p["canal"], p["tipo"], p.get("eje2_celda"),
                p["justificacion"], json.dumps(p["contenido_propuesto"]))
            p["id"] = str(row["id"])
            creadas.append(p)

    log.info("voz_propuestas_generadas", total=len(creadas))
    return creadas


# ============================================================
# CAPA A — Datos externos
# ============================================================

async def consultar_capa_a(fuente: str, query: str) -> dict:
    """Consulta fuente externa de Capa A.
    
    Soportadas v0: perplexity (búsqueda), open_meteo (clima).
    Resto: stub que devuelve nota pendiente.
    """
    if fuente == "perplexity":
        return await _capa_a_perplexity(query)
    elif fuente == "open_meteo":
        return await _capa_a_meteo()
    else:
        return {"fuente": fuente, "status": "stub", "nota": f"Fuente {fuente} no implementada en v0"}


async def _capa_a_perplexity(query: str) -> dict:
    """Consulta Perplexity Search API."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return {"fuente": "perplexity", "status": "no_key", "nota": "PERPLEXITY_API_KEY no configurada"}

    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": query}],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            respuesta = data["choices"][0]["message"]["content"]

            # Almacenar en DB
            pool = await _get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_voz_capa_a (tenant_id, fuente, tipo_dato, datos, fecha_dato, funcion_l07)
                    VALUES ($1, 'perplexity', 'consulta', $2::jsonb, CURRENT_DATE, 'F6')
                """, TENANT, json.dumps({"query": query, "respuesta": respuesta}))

            return {"fuente": "perplexity", "status": "ok", "respuesta": respuesta}

    except Exception as e:
        return {"fuente": "perplexity", "status": "error", "detail": str(e)}


async def _capa_a_meteo() -> dict:
    """Consulta Open-Meteo para Logroño (clima afecta asistencia)."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": 42.4627,
                    "longitude": -2.4445,
                    "daily": "temperature_2m_max,precipitation_sum,weathercode",
                    "timezone": "Europe/Madrid",
                    "forecast_days": 7,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            # Almacenar
            pool = await _get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_voz_capa_a (tenant_id, fuente, tipo_dato, datos, fecha_dato, funcion_l07)
                    VALUES ($1, 'open_meteo', 'prevision_7d', $2::jsonb, CURRENT_DATE, 'F6')
                """, TENANT, json.dumps(data.get("daily", {})))

            return {"fuente": "open_meteo", "status": "ok", "prevision": data.get("daily", {})}

    except Exception as e:
        return {"fuente": "open_meteo", "status": "error", "detail": str(e)}


# ============================================================
# ISP — Índice de Salud de Presencia
# ============================================================

async def calcular_isp(canal: str) -> dict:
    """Calcula ISP para un canal.
    
    v0: checklist manual de elementos por canal.
    v1: scraping automático + scoring.
    """
    checklists = {
        "google_business": [
            {"elemento": "Nombre correcto", "peso": 10},
            {"elemento": "Dirección completa", "peso": 10},
            {"elemento": "Teléfono actualizado", "peso": 10},
            {"elemento": "Horarios correctos", "peso": 10},
            {"elemento": "Fotos recientes (<3 meses)", "peso": 15},
            {"elemento": "Descripción completa", "peso": 10},
            {"elemento": "Categoría correcta", "peso": 5},
            {"elemento": "Responde reseñas (<48h)", "peso": 15},
            {"elemento": "Publicaciones recientes", "peso": 10},
            {"elemento": "Enlace web", "peso": 5},
        ],
        "instagram": [
            {"elemento": "Bio con CTA", "peso": 15},
            {"elemento": "Enlace en bio", "peso": 10},
            {"elemento": "Highlights organizados", "peso": 10},
            {"elemento": "Post reciente (<7 días)", "peso": 20},
            {"elemento": "Stories recientes (<48h)", "peso": 15},
            {"elemento": "Responde DMs (<24h)", "peso": 15},
            {"elemento": "Estilo visual coherente", "peso": 10},
            {"elemento": "Hashtags relevantes", "peso": 5},
        ],
        "whatsapp": [
            {"elemento": "Foto de perfil profesional", "peso": 15},
            {"elemento": "Descripción con horarios", "peso": 15},
            {"elemento": "Catálogo de servicios", "peso": 20},
            {"elemento": "Respuesta rápida (<1h horario)", "peso": 25},
            {"elemento": "Mensajes de ausencia activos", "peso": 10},
            {"elemento": "Enlace directo configurado", "peso": 15},
        ],
    }

    checklist = checklists.get(canal, [])
    if not checklist:
        return {"canal": canal, "status": "no_checklist", "nota": f"Canal {canal} sin checklist definido"}

    return {
        "canal": canal,
        "checklist": checklist,
        "max_score": sum(e["peso"] for e in checklist),
        "nota": "Marcar elementos cumplidos para calcular ISP. En v1 será automático.",
    }


async def guardar_isp(canal: str, elementos_cumplidos: list[str], score: float) -> dict:
    """Guarda resultado de auditoría ISP."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_voz_isp (tenant_id, canal, fecha_auditoria, isp_score, elementos)
            VALUES ($1, $2, CURRENT_DATE, $3, $4::jsonb) RETURNING id
        """, TENANT, canal, score, json.dumps(elementos_cumplidos))
    return {"id": str(row["id"]), "score": score}
```

---

## FASE B: Endpoints en router.py

**Archivo:** `@project/src/pilates/router.py` — LEER PRIMERO. AÑADIR:

```python
# ============================================================
# BLOQUE VOZ
# ============================================================

@router.post("/voz/generar-propuestas")
async def generar_propuestas_voz():
    """Genera propuestas de comunicación basadas en datos internos."""
    from src.pilates.voz import generar_propuestas
    propuestas = await generar_propuestas()
    return {"status": "ok", "propuestas_generadas": len(propuestas), "propuestas": propuestas}


@router.get("/voz/propuestas")
async def listar_propuestas_voz(estado: Optional[str] = "pendiente", canal: Optional[str] = None):
    """Lista propuestas de Voz."""
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if estado:
            conditions.append(f"estado = ${idx}"); params.append(estado); idx += 1
        if canal:
            conditions.append(f"canal = ${idx}"); params.append(canal); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_voz_propuestas WHERE {where}
            ORDER BY fecha_propuesta DESC LIMIT 50
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.patch("/voz/propuestas/{propuesta_id}")
async def decidir_propuesta(propuesta_id: UUID, data: dict):
    """Aprobar, descartar o editar propuesta.
    
    data: {"estado": "aprobada|descartada|editada", "contenido_editado": {...}}
    """
    pool = await _get_pool()
    estado = data.get("estado")
    async with pool.acquire() as conn:
        updates = ["fecha_decision = now()"]
        params = [propuesta_id]
        idx = 2
        if estado:
            updates.append(f"estado = ${idx}"); params.append(estado); idx += 1
        if data.get("contenido_editado"):
            updates.append(f"contenido_propuesto = ${idx}::jsonb")
            params.append(json.dumps(data["contenido_editado"])); idx += 1
        set_clause = ", ".join(updates)
        await conn.execute(
            f"UPDATE om_voz_propuestas SET {set_clause} WHERE id = $1 AND tenant_id = '{TENANT}'",
            *params)
    return {"status": "updated"}


@router.post("/voz/propuestas/{propuesta_id}/ejecutar")
async def ejecutar_propuesta(propuesta_id: UUID):
    """Ejecuta propuesta aprobada: envía WA, publica contenido, etc."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        prop = await conn.fetchrow("""
            SELECT * FROM om_voz_propuestas WHERE id = $1 AND tenant_id = $2
        """, propuesta_id, TENANT)
        if not prop:
            raise HTTPException(404, "Propuesta no encontrada")
        if prop["estado"] not in ("aprobada", "editada"):
            raise HTTPException(400, "Solo se pueden ejecutar propuestas aprobadas")

        contenido = prop["contenido_propuesto"]
        resultado = {}

        # Ejecutar según canal
        if prop["canal"] == "whatsapp" and contenido.get("telefono"):
            from src.pilates.whatsapp import enviar_texto
            resultado = await enviar_texto(
                contenido["telefono"], contenido.get("texto", ""),
                UUID(contenido["cliente_id"]) if contenido.get("cliente_id") else None)
        else:
            resultado = {"status": "manual", "nota": f"Canal {prop['canal']} requiere ejecución manual"}

        # Marcar ejecutada
        await conn.execute("""
            UPDATE om_voz_propuestas SET estado = 'ejecutada', fecha_ejecucion = now(),
                resultado = $1::jsonb WHERE id = $2
        """, json.dumps(resultado), propuesta_id)

    return {"status": "ejecutada", "resultado": resultado}


@router.post("/voz/capa-a")
async def consultar_capa_a_endpoint(data: dict):
    """Consulta fuente externa de Capa A.
    
    data: {"fuente": "perplexity|open_meteo", "query": "..."}
    """
    from src.pilates.voz import consultar_capa_a
    fuente = data.get("fuente", "perplexity")
    query = data.get("query", "")
    return await consultar_capa_a(fuente, query)


@router.get("/voz/capa-a/datos")
async def listar_datos_capa_a(fuente: Optional[str] = None, limit: int = 20):
    """Lista datos externos almacenados."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if fuente:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_capa_a WHERE tenant_id = $1 AND fuente = $2
                ORDER BY created_at DESC LIMIT $3
            """, TENANT, fuente, limit)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_capa_a WHERE tenant_id = $1
                ORDER BY created_at DESC LIMIT $2
            """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/voz/isp/{canal}")
async def obtener_checklist_isp(canal: str):
    """Obtiene checklist ISP para un canal."""
    from src.pilates.voz import calcular_isp
    return await calcular_isp(canal)


@router.post("/voz/isp/{canal}")
async def guardar_auditoria_isp(canal: str, data: dict):
    """Guarda resultado de auditoría ISP."""
    from src.pilates.voz import guardar_isp
    return await guardar_isp(
        canal, data.get("elementos_cumplidos", []), data.get("score", 0))


@router.get("/voz/isp")
async def historial_isp():
    """Historial de auditorías ISP por canal."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_voz_isp WHERE tenant_id = $1
            ORDER BY fecha_auditoria DESC LIMIT 20
        """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/voz/telemetria")
async def telemetria_voz(canal: Optional[str] = None):
    """Telemetría de canales de voz."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if canal:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_telemetria WHERE tenant_id = $1 AND canal = $2
                ORDER BY fecha DESC LIMIT 30
            """, TENANT, canal)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_telemetria WHERE tenant_id = $1
                ORDER BY fecha DESC LIMIT 30
            """, TENANT)
    return [_row_to_dict(r) for r in rows]
```

---

## FASE C: Integrar en cron y briefing

**Archivo:** `@project/src/pilates/automatismos.py` — En `ejecutar_cron`, bloque `inicio_semana`, AÑADIR:

```python
        # Generar propuestas Voz
        from src.pilates.voz import generar_propuestas
        props = await generar_propuestas()
        resultados["voz_propuestas"] = {"generadas": len(props)}
```

**Archivo:** `@project/src/pilates/briefing.py` — En `generar_briefing`, AÑADIR sección Voz al briefing dict:

```python
        # Propuestas Voz pendientes
        voz_pendientes = await conn.fetchval("""
            SELECT count(*) FROM om_voz_propuestas
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT)
```

Y añadir al dict: `"voz_propuestas_pendientes": voz_pendientes`

---

## FASE D: Frontend — api.js

```javascript
// Voz
export const generarPropuestasVoz = () => request('/voz/generar-propuestas', { method: 'POST' });
export const getPropuestasVoz = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/voz/propuestas${qs ? `?${qs}` : ''}`);
};
export const decidirPropuesta = (id, data) =>
  request(`/voz/propuestas/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const ejecutarPropuesta = (id) =>
  request(`/voz/propuestas/${id}/ejecutar`, { method: 'POST' });
export const consultarCapaA = (data) =>
  request('/voz/capa-a', { method: 'POST', body: JSON.stringify(data) });
export const getISP = (canal) => request(`/voz/isp/${canal}`);
export const getTelemetriaVoz = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/voz/telemetria${qs ? `?${qs}` : ''}`);
};
```

Pestaña Voz en Profundo.jsx: lista propuestas pendientes con botones aprobar/descartar/ejecutar, sección Capa A con botón consultar Perplexity, historial ISP por canal.

---

## Pass/fail

- `src/pilates/voz.py` creado con generador propuestas + Capa A + ISP
- POST /pilates/voz/generar-propuestas genera propuestas basadas en datos reales (ocupación, inactivos, deuda)
- GET /pilates/voz/propuestas lista con filtros
- PATCH /pilates/voz/propuestas/{id} aprueba/descarta/edita
- POST /pilates/voz/propuestas/{id}/ejecutar envía WA automáticamente (si canal=whatsapp)
- POST /pilates/voz/capa-a consulta Perplexity o Open-Meteo y almacena
- GET /voz/isp/{canal} devuelve checklist de auditoría
- POST /voz/isp/{canal} guarda resultado
- Cron inicio_semana genera propuestas automáticamente
- Propuestas idempotentes (no duplica si ya existe pendiente con misma justificación)
- 10 endpoints Voz nuevos

---

## TRIGGERS DE PROPUESTAS (v0)

| Condición detectada | Canal | Tipo | Celda |
|---|---|---|---|
| Grupo <50% ocupación | Instagram | contenido | F2_Se |
| Cliente >14 días sin venir | WhatsApp | broadcast | F1_S |
| Deuda >30 días | WhatsApp | tarea_asistida | F4_S |
| Inicio de mes | Instagram | contenido | F5_Se |
| Ocupación >85% | Web | alerta_oportunidad | F6_C |

En v1 se añaden: estacionalidad (Capa A meteo), competencia (Perplexity), reseñas (GBP), tendencias (Google Trends).
