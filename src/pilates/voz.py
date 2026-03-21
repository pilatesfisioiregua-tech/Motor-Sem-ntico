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
    """[DEPRECADO — usar voz_estrategia.calcular_estrategia()]

    Generador táctico de propuestas basado en reglas.
    Mantenido para backward compatibility con endpoints existentes.
    El Motor Tridimensional (B-PIL-20b) lo reemplaza con
    propuestas estratégicas cruzadas por los 3 ejes.

    Migración: POST /pilates/voz/estrategia/calcular
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
