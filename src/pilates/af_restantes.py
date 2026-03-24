"""AF2 + AF4 + AF6 + AF7 — Agentes funcionales restantes conectados al bus.

AF2 Captación: monitoriza leads sin atender + respeta VETOs de AF3
AF4 Distribución: detecta desequilibrios en ocupación de horarios
AF6 Adaptación: detecta tensiones sin resolver + señala cambios de entorno
AF7 Replicación: mide readiness y señala gaps de documentación

Todos emiten al bus. Ejecución semanal en cron.
"""
from __future__ import annotations

import json
import structlog
from datetime import date, timedelta, timezone, datetime

from src.db.client import get_pool

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request

INSTRUCCION_AF2 = """Analiza los leads y la conversión.
Para cada lead perdido, evalúa si merece rescate basándote en su intención original.
Para conversión baja, diagnostica si el problema es el canal, el mensaje, el timing
o el precio. Propón cambios concretos al proceso de cierre.
Respeta los VETOs de AF3: no propongas captar para horarios vetados."""

INSTRUCCION_AF4 = """Analiza la carga semanal.
¿Qué sesiones mover de días sobrecargados a vacíos?
¿Qué clientes podrían cambiar de horario sin impacto?
Si ratio individual es alto, propón cómo migrar clientes de individual a grupo
(qué grupo, cuándo, cómo comunicarlo). Calcula impacto en facturación."""

INSTRUCCION_AF6 = """Analiza tensiones del entorno.
¿Qué está cambiando en el mercado que afecte al negocio?
¿Hay oportunidades que no se están aprovechando? ¿Competidores nuevos?
Si no hay tensiones registradas, eso ES una señal: significa que no estás
monitorizando el entorno. Señala qué debería estar vigilando y no lo está."""

INSTRUCCION_AF7 = """Analiza la capacidad de replicar el negocio.
¿Qué proceso documentar PRIMERO para máximo impacto?
¿Qué principio del ADN es más urgente definir con contra-ejemplos?
Si tuvieras que formar a un instructor sustituto mañana,
¿qué le faltaría saber? Prioriza por riesgo operativo."""


# ============================================================
# AF2 CAPTACIÓN — Proteger y acelerar la entrada de clientes nuevos
# ============================================================

async def ejecutar_af2() -> dict:
    """AF2: Detecta oportunidades y problemas de captación.

    1. Leads sin responder en >24h
    2. Tasa de conversión lead→cliente (últimas 4 semanas)
    3. Respeta VETOs de AF3: no señalar captación para horarios vetados
    """
    pool = await get_pool()
    from src.pilates.bus import emitir, leer_pendientes

    detecciones = []

    async with pool.acquire() as conn:
        # 1. Leads WA sin responder en >24h
        try:
            leads_perdidos = await conn.fetch("""
                SELECT m.id, m.telefono_remitente, m.contenido, m.created_at
                FROM om_mensajes_wa m
                WHERE m.tenant_id = $1 AND m.direccion = 'entrante'
                AND m.intencion IN ('consulta_precio', 'reserva')
                AND m.respondido = false
                AND m.created_at < now() - interval '24 hours'
                AND m.created_at > now() - interval '7 days'
            """, TENANT)

            for lead in leads_perdidos:
                horas = round((datetime.now(timezone.utc) - lead["created_at"]).total_seconds() / 3600)
                detecciones.append({
                    "tipo": "lead_perdido",
                    "telefono": lead["telefono_remitente"],
                    "horas_sin_responder": horas,
                    "accion_sugerida": f"Lead sin responder desde hace {horas}h. Probablemente perdido. Llamar igualmente.",
                })
        except Exception as e:
            log.warning("af2_leads_error", error=str(e))

        # 2. Tasa de conversión (nuevos clientes / leads entrantes)
        try:
            hace_4_sem = date.today() - timedelta(weeks=4)
            leads_totales = await conn.fetchval("""
                SELECT count(*) FROM om_mensajes_wa
                WHERE tenant_id = $1 AND direccion = 'entrante'
                AND intencion IN ('consulta_precio', 'reserva')
                AND created_at >= $2
            """, TENANT, hace_4_sem) or 0

            nuevos = await conn.fetchval("""
                SELECT count(*) FROM om_cliente_tenant
                WHERE tenant_id = $1 AND fecha_alta >= $2
            """, TENANT, hace_4_sem) or 0

            if leads_totales > 3 and nuevos == 0:
                detecciones.append({
                    "tipo": "conversion_cero",
                    "leads": leads_totales,
                    "nuevos": nuevos,
                    "accion_sugerida": f"{leads_totales} leads en 4 semanas pero 0 conversiones. Revisar proceso de cierre.",
                })
            elif leads_totales > 0:
                tasa = round(nuevos / leads_totales * 100)
                if tasa < 20:
                    detecciones.append({
                        "tipo": "conversion_baja",
                        "leads": leads_totales,
                        "nuevos": nuevos,
                        "tasa_pct": tasa,
                        "accion_sugerida": f"Tasa conversión {tasa}% ({nuevos}/{leads_totales}). Objetivo: >30%.",
                    })
        except Exception as e:
            log.warning("af2_conversion_error", error=str(e))

    # 3. Leer VETOs de AF3 para no contradecirlos
    vetos = []
    try:
        señales_veto = await leer_pendientes(tipo="PRESCRIPCION", limite=50)
        for s in señales_veto:
            p = s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"])
            if p.get("subtipo") == "VETO" and "AF2" in p.get("bloquea_af", []):
                vetos.append(p.get("objeto", "desconocido"))
    except Exception as e:
        log.debug("silenced_exception", exc=str(e))

    # === CEREBRO (NIVEL 1) ===
    datos_sensor = {"detecciones": detecciones, "vetos_af3": vetos}
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar("AF2", "F2 Captación", datos_sensor, INSTRUCCION_AF2, nivel=1)

    # Emitir prescripciones razonadas
    alertas = 0
    for accion in razonamiento.get("acciones", []):
        try:
            await emitir("PRESCRIPCION", "AF2", {
                "funcion": "F2", "accion": accion.get("accion", ""),
                "prioridad": accion.get("prioridad", 4),
                "impacto": accion.get("impacto", ""), "esfuerzo": accion.get("esfuerzo", ""),
                "cliente_id": accion.get("cliente_id"), "grupo_id": accion.get("grupo_id"),
                "interpretacion": razonamiento["interpretacion"],
            }, prioridad=accion.get("prioridad", 4))
            alertas += 1
        except Exception as e:
            log.debug("silenced_exception", exc=str(e))

    log.info("af2_completo", detecciones=len(detecciones), vetos=len(vetos))
    return {
        "leads_perdidos": len([d for d in detecciones if d["tipo"] == "lead_perdido"]),
        "alertas_conversion": len([d for d in detecciones if "conversion" in d["tipo"]]),
        "vetos_af3_activos": len(vetos),
        "alertas_emitidas": alertas,
        "razonamiento": razonamiento,
        "detalle": detecciones[:10],
    }


# ============================================================
# AF4 DISTRIBUCIÓN — Equilibrar carga horaria
# ============================================================

async def ejecutar_af4() -> dict:
    """AF4: Detecta desequilibrios en la distribución de sesiones.

    1. Días con sobrecarga (>6 sesiones/día)
    2. Días vacíos (0 sesiones programadas, L-V)
    3. Ratio individual/grupo desequilibrado
    """
    pool = await get_pool()
    from src.pilates.bus import emitir

    detecciones = []
    hace_4_sem = date.today() - timedelta(weeks=4)

    async with pool.acquire() as conn:
        # 1. Distribución por día de semana
        try:
            dist_dias = await conn.fetch("""
                SELECT EXTRACT(DOW FROM fecha) as dow, count(*) as n
                FROM om_sesiones
                WHERE tenant_id = $1 AND fecha >= $2
                GROUP BY dow ORDER BY dow
            """, TENANT, hace_4_sem)

            dias_nombre = {0: "Domingo", 1: "Lunes", 2: "Martes", 3: "Miércoles",
                           4: "Jueves", 5: "Viernes", 6: "Sábado"}

            for d in dist_dias:
                media_sem = d["n"] / 4  # 4 semanas
                if media_sem > 6:
                    detecciones.append({
                        "tipo": "dia_sobrecargado",
                        "dia": dias_nombre.get(int(d["dow"]), str(d["dow"])),
                        "media_sesiones": round(media_sem, 1),
                        "accion_sugerida": f"{dias_nombre.get(int(d['dow']))} tiene {media_sem:.0f} sesiones/día de media. Riesgo de fatiga. Mover alguna sesión.",
                    })

            # Detectar días L-V sin sesiones
            dias_activos = {int(d["dow"]) for d in dist_dias}
            for dow in [1, 2, 3, 4, 5]:  # L-V
                if dow not in dias_activos:
                    detecciones.append({
                        "tipo": "dia_vacio",
                        "dia": dias_nombre[dow],
                        "accion_sugerida": f"{dias_nombre[dow]} sin sesiones en 4 semanas. ¿Cerrado o infrautilizado?",
                    })
        except Exception as e:
            log.warning("af4_distribucion_error", error=str(e))

        # 2. Ratio individual/grupo
        try:
            ratio = await conn.fetchrow("""
                SELECT
                    count(*) FILTER (WHERE tipo = 'individual') as individuales,
                    count(*) FILTER (WHERE tipo = 'grupo') as grupo
                FROM om_sesiones
                WHERE tenant_id = $1 AND fecha >= $2
            """, TENANT, hace_4_sem)

            total = (ratio["individuales"] or 0) + (ratio["grupo"] or 0)
            if total > 0:
                pct_ind = round((ratio["individuales"] or 0) / total * 100)
                if pct_ind > 70:
                    detecciones.append({
                        "tipo": "exceso_individual",
                        "pct_individual": pct_ind,
                        "individuales": ratio["individuales"],
                        "grupo": ratio["grupo"],
                        "accion_sugerida": f"{pct_ind}% sesiones son individuales. Ingresos dependen de tu tiempo. Potenciar grupos.",
                    })
        except Exception as e:
            log.warning("af4_ratio_error", error=str(e))

    # === CEREBRO (NIVEL 1) ===
    datos_sensor = {"detecciones": detecciones}
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar("AF4", "F4 Distribución", datos_sensor, INSTRUCCION_AF4, nivel=1)

    alertas = 0
    for accion in razonamiento.get("acciones", []):
        try:
            await emitir("PRESCRIPCION", "AF4", {
                "funcion": "F4", "accion": accion.get("accion", ""),
                "prioridad": accion.get("prioridad", 5),
                "impacto": accion.get("impacto", ""), "esfuerzo": accion.get("esfuerzo", ""),
                "interpretacion": razonamiento["interpretacion"],
            }, prioridad=accion.get("prioridad", 5))
            alertas += 1
        except Exception as e:
            log.debug("silenced_exception", exc=str(e))

    log.info("af4_completo", detecciones=len(detecciones))
    return {
        "dias_sobrecargados": len([d for d in detecciones if d["tipo"] == "dia_sobrecargado"]),
        "dias_vacios": len([d for d in detecciones if d["tipo"] == "dia_vacio"]),
        "alerta_ratio": len([d for d in detecciones if d["tipo"] == "exceso_individual"]),
        "alertas_emitidas": alertas,
        "razonamiento": razonamiento,
        "detalle": detecciones[:10],
    }


# ============================================================
# AF6 ADAPTACIÓN — Detectar cambios en el entorno
# ============================================================

async def ejecutar_af6() -> dict:
    """AF6: Detecta tensiones sin resolver y señala necesidad de adaptación.

    1. Tensiones abiertas (sin resolver) >30 días
    2. Tensiones de alta severidad sin plan
    """
    pool = await get_pool()
    from src.pilates.bus import emitir

    detecciones = []
    hace_30d = date.today() - timedelta(days=30)

    async with pool.acquire() as conn:
        try:
            tensiones_viejas = await conn.fetch("""
                SELECT id, tipo, descripcion, severidad, created_at
                FROM om_voz_tensiones
                WHERE tenant_id = $1 AND resuelta = false
                AND created_at < $2
                ORDER BY severidad DESC
            """, TENANT, hace_30d)

            for t in tensiones_viejas:
                dias = (date.today() - t["created_at"].date()).days
                detecciones.append({
                    "tipo": "tension_sin_resolver",
                    "tension_id": str(t["id"]),
                    "tension_tipo": t["tipo"],
                    "severidad": t["severidad"],
                    "dias_abierta": dias,
                    "descripcion": t["descripcion"][:100],
                    "accion_sugerida": f"Tensión '{t['tipo']}' ({t['severidad']}) abierta {dias} días. Resolver o documentar como asumida.",
                })
        except Exception as e:
            log.warning("af6_tensiones_error", error=str(e))

        # Tensiones alta/crítica sin importar antigüedad
        try:
            criticas = await conn.fetch("""
                SELECT id, tipo, descripcion, severidad, created_at
                FROM om_voz_tensiones
                WHERE tenant_id = $1 AND resuelta = false
                AND severidad IN ('alta', 'critica')
                AND created_at >= $2
            """, TENANT, hace_30d)

            for t in criticas:
                if not any(d.get("tension_id") == str(t["id"]) for d in detecciones):
                    detecciones.append({
                        "tipo": "tension_critica",
                        "tension_id": str(t["id"]),
                        "tension_tipo": t["tipo"],
                        "severidad": t["severidad"],
                        "descripcion": t["descripcion"][:100],
                        "accion_sugerida": f"Tensión {t['severidad']} activa: {t['descripcion'][:60]}. Priorizar.",
                    })
        except Exception as e:
            log.warning("af6_criticas_error", error=str(e))

    # === CEREBRO (NIVEL 1) ===
    datos_sensor = {"detecciones": detecciones}
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar("AF6", "F6 Adaptación", datos_sensor, INSTRUCCION_AF6, nivel=1)

    alertas = 0
    for accion in razonamiento.get("acciones", []):
        try:
            await emitir("PRESCRIPCION", "AF6", {
                "funcion": "F6", "accion": accion.get("accion", ""),
                "prioridad": accion.get("prioridad", 4),
                "impacto": accion.get("impacto", ""), "esfuerzo": accion.get("esfuerzo", ""),
                "interpretacion": razonamiento["interpretacion"],
            }, prioridad=accion.get("prioridad", 4))
            alertas += 1
        except Exception as e:
            log.debug("silenced_exception", exc=str(e))

    log.info("af6_completo", detecciones=len(detecciones))
    return {
        "tensiones_sin_resolver": len([d for d in detecciones if d["tipo"] == "tension_sin_resolver"]),
        "tensiones_criticas": len([d for d in detecciones if d["tipo"] == "tension_critica"]),
        "alertas_emitidas": alertas,
        "razonamiento": razonamiento,
        "detalle": detecciones[:10],
    }


# ============================================================
# AF7 REPLICACIÓN — Medir capacidad de transferencia
# ============================================================

async def ejecutar_af7() -> dict:
    """AF7: Detecta gaps en documentación y readiness de replicación.

    1. Áreas sin procesos documentados
    2. ADN sin contra-ejemplos (principios sin definir límites)
    3. Readiness general <50%
    """
    pool = await get_pool()
    from src.pilates.bus import emitir

    detecciones = []
    AREAS = {"operativa_diaria", "sesion", "cliente", "emergencia", "administrativa", "instructor"}

    async with pool.acquire() as conn:
        # 1. Áreas sin procesos
        try:
            areas_cubiertas = await conn.fetch("""
                SELECT DISTINCT area FROM om_procesos WHERE tenant_id = $1
            """, TENANT)
            cubiertas = {r["area"] for r in areas_cubiertas}
            sin_cubrir = AREAS - cubiertas

            if sin_cubrir:
                detecciones.append({
                    "tipo": "areas_sin_procesos",
                    "areas": sorted(sin_cubrir),
                    "cubiertas": len(cubiertas),
                    "total": len(AREAS),
                    "accion_sugerida": f"Áreas sin procesos documentados: {', '.join(sorted(sin_cubrir))}. Documentar para subir C.",
                })
        except Exception as e:
            log.warning("af7_procesos_error", error=str(e))

        # 2. ADN sin contra-ejemplos
        try:
            adn_incompleto = await conn.fetchval("""
                SELECT count(*) FROM om_adn
                WHERE tenant_id = $1 AND activo = true
                AND (contra_ejemplos IS NULL OR contra_ejemplos = '[]'::jsonb)
            """, TENANT) or 0

            adn_total = await conn.fetchval("""
                SELECT count(*) FROM om_adn WHERE tenant_id = $1 AND activo = true
            """, TENANT) or 0

            if adn_incompleto > 0 and adn_total > 0:
                pct = round(adn_incompleto / adn_total * 100)
                if pct > 50:
                    detecciones.append({
                        "tipo": "adn_sin_limites",
                        "sin_contra_ejemplos": adn_incompleto,
                        "total": adn_total,
                        "pct_incompleto": pct,
                        "accion_sugerida": f"{pct}% del ADN sin contra-ejemplos. Principios sin límites son ambiguos. Definir qué NO es.",
                    })
        except Exception as e:
            log.warning("af7_adn_error", error=str(e))

        # 3. Readiness general
        try:
            procesos = await conn.fetchval(
                "SELECT count(*) FROM om_procesos WHERE tenant_id = $1", TENANT) or 0
            adn = await conn.fetchval(
                "SELECT count(*) FROM om_adn WHERE tenant_id = $1 AND activo = true", TENANT) or 0

            # Readiness simplificado
            score_procesos = min(procesos / 12, 1.0)  # 12 procesos = pleno
            score_adn = min(adn / 10, 1.0)  # 10 ADN activos = pleno
            readiness = round((score_procesos * 0.5 + score_adn * 0.5) * 100)

            if readiness < 50:
                detecciones.append({
                    "tipo": "readiness_bajo",
                    "readiness_pct": readiness,
                    "procesos": procesos,
                    "adn_activos": adn,
                    "accion_sugerida": f"Readiness {readiness}%. No podrías replicar el negocio hoy. Documentar procesos + ADN.",
                })
        except Exception as e:
            log.warning("af7_readiness_error", error=str(e))

    # === CEREBRO (NIVEL 1) ===
    datos_sensor = {"detecciones": detecciones}
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar("AF7", "F7 Replicación", datos_sensor, INSTRUCCION_AF7, nivel=1)

    alertas = 0
    for accion in razonamiento.get("acciones", []):
        try:
            await emitir("PRESCRIPCION", "AF7", {
                "funcion": "F7", "accion": accion.get("accion", ""),
                "prioridad": accion.get("prioridad", 6),
                "impacto": accion.get("impacto", ""), "esfuerzo": accion.get("esfuerzo", ""),
                "interpretacion": razonamiento["interpretacion"],
            }, prioridad=accion.get("prioridad", 6))
            alertas += 1
        except Exception as e:
            log.debug("silenced_exception", exc=str(e))

    log.info("af7_completo", detecciones=len(detecciones))
    return {
        "areas_sin_procesos": len([d for d in detecciones if d["tipo"] == "areas_sin_procesos"]),
        "adn_sin_limites": len([d for d in detecciones if d["tipo"] == "adn_sin_limites"]),
        "readiness_bajo": len([d for d in detecciones if d["tipo"] == "readiness_bajo"]),
        "alertas_emitidas": alertas,
        "razonamiento": razonamiento,
        "detalle": detecciones[:10],
    }


# ============================================================
# EJECUTAR TODOS
# ============================================================

async def ejecutar_af_restantes() -> dict:
    """Ejecuta AF2 + AF4 + AF6 + AF7 en secuencia. Devuelve resumen combinado."""
    af2 = await ejecutar_af2()
    af4 = await ejecutar_af4()
    af6 = await ejecutar_af6()
    af7 = await ejecutar_af7()

    return {
        "AF2_captacion": af2,
        "AF4_distribucion": af4,
        "AF6_adaptacion": af6,
        "AF7_replicacion": af7,
        "total_alertas": (
            af2["alertas_emitidas"] + af4["alertas_emitidas"] +
            af6["alertas_emitidas"] + af7["alertas_emitidas"]
        ),
    }
