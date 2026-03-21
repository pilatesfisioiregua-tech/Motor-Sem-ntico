"""5 Ciclos del Bloque Voz — ESCUCHAR → PRIORIZAR → PROPONER → EJECUTAR → APRENDER.

Conecta todos los módulos del Bloque Voz en un flujo operativo:
- Detecta señales de Capa A (mercado) + Capa B (negocio) + Capa C (audiencia)
- Prioriza por urgencia e impacto en ingresos
- Genera propuestas (delega en voz_estrategia)
- Registra telemetría y retroalimenta IRC/PCA

Basado en B2.8 v3.0 §3.1 — Los 5 ciclos operativos.
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


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# CICLO 1: ESCUCHAR — Detectar señales
# ============================================================

async def escuchar() -> dict:
    """Detecta señales de las 3 capas y las registra en om_voz_senales.

    Capa A (mercado): Perplexity, Open-Meteo, datos existentes en om_voz_capa_a.
    Capa B (negocio): Señales internas (ocupación, inactivos, deuda, altas/bajas).
    Capa C (audiencia): Actividad en om_voz_telemetria_canal.

    Las APIs de Google Business, Instagram, WA Business se conectarán
    en el futuro como detectores adicionales — la arquitectura está lista.
    """
    pool = await _get_pool()
    senales_creadas = 0

    async with pool.acquire() as conn:
        # ── CAPA B: Señales internas ─────────────────────────
        from src.pilates.voz_estrategia import _recoger_senales_internas
        senales_b = await _recoger_senales_internas()

        # Señal: ocupación baja
        if senales_b["ocupacion_pct"] < 60:
            senales_creadas += await _registrar_senal(conn, {
                "origen": "ocupacion",
                "capa": "B",
                "urgencia": "alta" if senales_b["ocupacion_pct"] < 40 else "media",
                "contenido": {
                    "tipo": "ocupacion_baja",
                    "ocupacion_pct": senales_b["ocupacion_pct"],
                    "grupos_bajos": senales_b["grupos_baja_ocupacion"],
                },
            })

        # Señal: clientes inactivos
        if senales_b["clientes_inactivos_14d"] > 0:
            senales_creadas += await _registrar_senal(conn, {
                "origen": "inactividad",
                "capa": "B",
                "urgencia": "alta" if senales_b["clientes_inactivos_14d"] >= 3 else "media",
                "contenido": {
                    "tipo": "clientes_inactivos",
                    "cantidad": senales_b["clientes_inactivos_14d"],
                },
            })

        # Señal: deuda antigua
        if senales_b["deuda_pendiente"]["total_eur"] > 0:
            senales_creadas += await _registrar_senal(conn, {
                "origen": "deuda",
                "capa": "B",
                "urgencia": "alta" if senales_b["deuda_pendiente"]["total_eur"] > 300 else "baja",
                "contenido": {
                    "tipo": "deuda_pendiente",
                    "clientes": senales_b["deuda_pendiente"]["clientes"],
                    "total_eur": senales_b["deuda_pendiente"]["total_eur"],
                },
            })

        # Señal: bajas recientes
        if senales_b["bajas_30d"] > 0:
            senales_creadas += await _registrar_senal(conn, {
                "origen": "bajas",
                "capa": "B",
                "urgencia": "alta" if senales_b["bajas_30d"] >= 2 else "media",
                "contenido": {
                    "tipo": "bajas_recientes",
                    "cantidad": senales_b["bajas_30d"],
                    "altas_30d": senales_b["altas_30d"],
                    "balance": senales_b["altas_30d"] - senales_b["bajas_30d"],
                },
            })

        # Señal: alta ocupación (oportunidad)
        if senales_b["ocupacion_pct"] > 85:
            senales_creadas += await _registrar_senal(conn, {
                "origen": "alta_ocupacion",
                "capa": "B",
                "urgencia": "media",
                "contenido": {
                    "tipo": "alta_ocupacion",
                    "ocupacion_pct": senales_b["ocupacion_pct"],
                    "accion_sugerida": "Considerar lista de espera o nuevo horario",
                },
            })

        # ── CAPA A: Datos externos recientes ─────────────────
        # Revisar datos de Capa A de los últimos 7 días
        datos_capa_a = await conn.fetch("""
            SELECT fuente, tipo_dato, datos, fecha_dato
            FROM om_voz_capa_a
            WHERE tenant_id = $1 AND fecha_dato >= CURRENT_DATE - interval '7 days'
            ORDER BY fecha_dato DESC
        """, TENANT)

        for dato in datos_capa_a:
            datos_json = dato["datos"]
            if isinstance(datos_json, str):
                try:
                    datos_json = json.loads(datos_json)
                except (json.JSONDecodeError, TypeError):
                    continue

            # Señal meteo: lluvia en los próximos días
            if dato["fuente"] == "open_meteo" and isinstance(datos_json, dict):
                precip = datos_json.get("precipitation_sum", [])
                if isinstance(precip, list) and any(p and float(p) > 5 for p in precip[:3]):
                    senales_creadas += await _registrar_senal(conn, {
                        "origen": "clima",
                        "capa": "A",
                        "urgencia": "media",
                        "contenido": {
                            "tipo": "lluvia_prevista",
                            "precipitacion": precip[:3],
                            "accion_sugerida": "Anticipar cancelaciones, enviar WA preventivo",
                        },
                    })

            # Señal perplexity: cualquier consulta reciente
            if dato["fuente"] == "perplexity" and isinstance(datos_json, dict):
                senales_creadas += await _registrar_senal(conn, {
                    "origen": "perplexity",
                    "capa": "A",
                    "urgencia": "baja",
                    "contenido": {
                        "tipo": "insight_mercado",
                        "query": datos_json.get("query", ""),
                        "resumen": datos_json.get("respuesta", "")[:200],
                    },
                })

    log.info("voz_ciclo_escuchar", senales=senales_creadas)
    return {"status": "ok", "senales_creadas": senales_creadas}


async def _registrar_senal(conn, senal: dict) -> int:
    """Registra señal en om_voz_senales si no existe una similar pendiente."""
    # Evitar duplicados del mismo tipo en las últimas 24h
    tipo = senal["contenido"].get("tipo", "")
    exists = await conn.fetchval("""
        SELECT 1 FROM om_voz_senales
        WHERE tenant_id = $1 AND origen = $2
            AND contenido->>'tipo' = $3
            AND procesada = FALSE
            AND created_at > now() - interval '24 hours'
    """, TENANT, senal["origen"], tipo)

    if exists:
        return 0

    await conn.execute("""
        INSERT INTO om_voz_senales (tenant_id, origen, capa, urgencia, contenido)
        VALUES ($1, $2, $3, $4, $5::jsonb)
    """, TENANT, senal["origen"], senal["capa"],
        senal["urgencia"], json.dumps(senal["contenido"], ensure_ascii=False))

    return 1


# ============================================================
# CICLO 2: PRIORIZAR — Clasificar señales pendientes
# ============================================================

async def priorizar() -> dict:
    """Clasifica señales pendientes por urgencia/impacto.

    Devuelve señales ordenadas con acción recomendada.
    Las señales 'critica' y 'alta' se procesan primero.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        senales = await conn.fetch("""
            SELECT id, origen, capa, urgencia, contenido, created_at
            FROM om_voz_senales
            WHERE tenant_id = $1 AND procesada = FALSE
            ORDER BY
                CASE urgencia
                    WHEN 'critica' THEN 1
                    WHEN 'alta' THEN 2
                    WHEN 'media' THEN 3
                    WHEN 'baja' THEN 4
                END,
                created_at DESC
        """, TENANT)

    priorizado = []
    for s in senales:
        contenido = s["contenido"]
        if isinstance(contenido, str):
            try:
                contenido = json.loads(contenido)
            except (json.JSONDecodeError, TypeError):
                contenido = {}

        priorizado.append({
            "id": str(s["id"]),
            "origen": s["origen"],
            "capa": s["capa"],
            "urgencia": s["urgencia"],
            "tipo": contenido.get("tipo", "desconocido"),
            "resumen": _resumir_senal(contenido),
            "created_at": str(s["created_at"]),
        })

    return {
        "status": "ok",
        "total": len(priorizado),
        "criticas": sum(1 for s in priorizado if s["urgencia"] == "critica"),
        "altas": sum(1 for s in priorizado if s["urgencia"] == "alta"),
        "medias": sum(1 for s in priorizado if s["urgencia"] == "media"),
        "bajas": sum(1 for s in priorizado if s["urgencia"] == "baja"),
        "senales": priorizado,
    }


def _resumir_senal(contenido: dict) -> str:
    """Genera resumen legible de una señal."""
    tipo = contenido.get("tipo", "")
    resumenes = {
        "ocupacion_baja": f"Ocupación al {contenido.get('ocupacion_pct', '?')}%",
        "clientes_inactivos": f"{contenido.get('cantidad', '?')} clientes inactivos >14 días",
        "deuda_pendiente": f"{contenido.get('total_eur', '?')}€ deuda de {contenido.get('clientes', '?')} clientes",
        "bajas_recientes": f"{contenido.get('cantidad', '?')} bajas (balance: {contenido.get('balance', '?')})",
        "alta_ocupacion": f"Ocupación al {contenido.get('ocupacion_pct', '?')}% — considerar expansión",
        "lluvia_prevista": "Lluvia próximos días — anticipar cancelaciones",
        "insight_mercado": contenido.get("resumen", "")[:100],
    }
    return resumenes.get(tipo, json.dumps(contenido, ensure_ascii=False)[:100])


async def marcar_procesada(senal_id: str) -> dict:
    """Marca una señal como procesada."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_voz_senales SET procesada = TRUE
            WHERE id = $1 AND tenant_id = $2
        """, UUID(senal_id), TENANT)
        if result == "UPDATE 0":
            return {"error": "Señal no encontrada"}
    return {"status": "procesada", "id": senal_id}


# ============================================================
# CICLO 5: APRENDER — Telemetría + Recalcular IRC
# ============================================================

async def registrar_telemetria(canal: str, periodo: str, metricas: dict) -> dict:
    """Registra métricas de un canal para un periodo.

    Args:
        canal: whatsapp, google_business, instagram, facebook, web
        periodo: "2026-W12" o "2026-03"
        metricas: dict con leads_generados, reservas_directas, etc.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_voz_telemetria_canal (
                tenant_id, canal, periodo,
                leads_generados, reservas_directas, conversiones_cliente,
                mensajes_respondidos, tasa_respuesta, tasa_apertura,
                resenas_recibidas, resenas_respondidas,
                contenido_publicado, mejor_formato, mejor_tema,
                engagement_medio, primer_contacto_pct
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                $12, $13, $14, $15, $16
            )
            ON CONFLICT ON CONSTRAINT uq_telemetria_canal_periodo
            DO UPDATE SET
                leads_generados = EXCLUDED.leads_generados,
                reservas_directas = EXCLUDED.reservas_directas,
                conversiones_cliente = EXCLUDED.conversiones_cliente,
                mensajes_respondidos = EXCLUDED.mensajes_respondidos,
                tasa_respuesta = EXCLUDED.tasa_respuesta,
                tasa_apertura = EXCLUDED.tasa_apertura,
                resenas_recibidas = EXCLUDED.resenas_recibidas,
                resenas_respondidas = EXCLUDED.resenas_respondidas,
                contenido_publicado = EXCLUDED.contenido_publicado,
                mejor_formato = EXCLUDED.mejor_formato,
                mejor_tema = EXCLUDED.mejor_tema,
                engagement_medio = EXCLUDED.engagement_medio,
                primer_contacto_pct = EXCLUDED.primer_contacto_pct
        """, TENANT, canal, periodo,
            metricas.get("leads_generados", 0),
            metricas.get("reservas_directas", 0),
            metricas.get("conversiones_cliente", 0),
            metricas.get("mensajes_respondidos", 0),
            metricas.get("tasa_respuesta"),
            metricas.get("tasa_apertura"),
            metricas.get("resenas_recibidas", 0),
            metricas.get("resenas_respondidas", 0),
            metricas.get("contenido_publicado", 0),
            metricas.get("mejor_formato"),
            metricas.get("mejor_tema"),
            metricas.get("engagement_medio"),
            metricas.get("primer_contacto_pct"),
        )

    log.info("voz_telemetria_registrada", canal=canal, periodo=periodo)
    return {"status": "ok", "canal": canal, "periodo": periodo}


async def recalcular_irc() -> dict:
    """Recalcula IRC de cada canal basándose en telemetría real.

    Si hay datos de telemetría, ajusta tasa_conversion_historica.
    Si no hay datos, mantiene valores estimados del seed.
    """
    pool = await _get_pool()

    async with pool.acquire() as conn:
        canales = await conn.fetch("""
            SELECT * FROM om_voz_irc
            WHERE tenant_id = $1 AND activo = TRUE
        """, TENANT)

        actualizados = 0
        for canal in canales:
            # Buscar telemetría de los últimos 3 meses
            telem = await conn.fetch("""
                SELECT canal,
                    SUM(leads_generados) as total_leads,
                    SUM(reservas_directas) as total_reservas,
                    SUM(conversiones_cliente) as total_conversiones,
                    AVG(tasa_respuesta) as avg_respuesta,
                    AVG(engagement_medio) as avg_engagement,
                    AVG(primer_contacto_pct) as avg_primer_contacto
                FROM om_voz_telemetria_canal
                WHERE tenant_id = $1 AND canal = $2
                    AND created_at > now() - interval '90 days'
                GROUP BY canal
            """, TENANT, canal["canal"])

            if not telem:
                continue  # Sin datos, mantener estimados

            t = telem[0]
            total_conv = (t["total_conversiones"] or 0)

            # Recalcular tasa_conversion_historica (0-1)
            # Si generó conversiones reales, ajustar
            if total_conv > 0:
                # Normalizar: 10+ conversiones en 3 meses = 1.0
                nueva_conversion = min(total_conv / 10.0, 1.0)
            else:
                nueva_conversion = 0.1  # Algo generó, pero no conversiones directas

            # Recalcular IRC con nuevo dato
            pesos_raw = canal["pesos"]
            if isinstance(pesos_raw, str):
                pesos = json.loads(pesos_raw)
            else:
                pesos = pesos_raw or {"w1": 0.2, "w2": 0.2, "w3": 0.2, "w4": 0.1, "w5": 0.1, "w6": 0.2}

            nuevo_irc = (
                pesos.get("w1", 0.2) * float(canal["demanda_busqueda_local"]) +
                pesos.get("w2", 0.2) * float(canal["audiencia_objetivo_presente"]) +
                pesos.get("w3", 0.2) * round(nueva_conversion, 2) +
                pesos.get("w4", 0.1) * float(canal["coste_tiempo_dueno"]) +
                pesos.get("w5", 0.1) * float(canal["capacidad_disponible"]) +
                pesos.get("w6", 0.2) * float(canal["afinidad_consumo_audiencia"])
            )

            await conn.execute("""
                UPDATE om_voz_irc
                SET tasa_conversion_historica = $3,
                    irc_score = $4
                WHERE tenant_id = $1 AND canal = $2
            """, TENANT, canal["canal"],
                round(nueva_conversion, 2), round(nuevo_irc, 2))

            actualizados += 1

    log.info("voz_irc_recalculado", canales=actualizados)
    return {"status": "ok", "canales_actualizados": actualizados}


# ============================================================
# ISP AUTOMÁTICO — reemplaza checklist manual de voz.py
# ============================================================

async def calcular_isp_automatico() -> dict:
    """Calcula ISP automático para cada canal basándose en datos reales.

    Evalúa:
    - Plantillas de perfil (de 20c): ¿aprobadas? ¿aplicadas?
    - Calendario (de 20b): ¿contenido publicado recientemente?
    - Telemetría: ¿hay datos de actividad?
    - Señales: ¿hay señales pendientes sin procesar?

    Almacena resultado en om_voz_isp.
    """
    pool = await _get_pool()
    resultados = {}

    canales = ["whatsapp", "google_business", "instagram", "facebook"]

    async with pool.acquire() as conn:
        for canal in canales:
            score = 0
            max_score = 0
            elementos = []

            # ── 1. Perfil configurado (plantillas de 20c) ───
            plantillas = await conn.fetch("""
                SELECT tipo, estado FROM om_voz_perfil_plantilla
                WHERE tenant_id = $1 AND canal = $2
                ORDER BY created_at DESC
            """, TENANT, canal)

            # ¿Tiene plantillas generadas?
            tiene_plantillas = len(plantillas) > 0
            max_score += 20
            if tiene_plantillas:
                score += 10
                elementos.append({"elemento": "Perfil generado", "estado": "ok", "peso": 10})

                # ¿Plantillas aprobadas?
                aprobadas = sum(1 for p in plantillas if p["estado"] in ("aprobado", "aplicado"))
                if aprobadas > 0:
                    score += 5
                    elementos.append({"elemento": "Plantillas aprobadas", "estado": "ok", "peso": 5})
                else:
                    elementos.append({"elemento": "Plantillas aprobadas", "estado": "pendiente", "peso": 5})

                # ¿Plantillas aplicadas?
                aplicadas = sum(1 for p in plantillas if p["estado"] == "aplicado")
                if aplicadas > 0:
                    score += 5
                    elementos.append({"elemento": "Plantillas aplicadas", "estado": "ok", "peso": 5})
                else:
                    elementos.append({"elemento": "Plantillas aplicadas", "estado": "pendiente", "peso": 5})
            else:
                elementos.append({"elemento": "Perfil generado", "estado": "falta", "peso": 20})

            # ── 2. Contenido reciente (calendario de 20b) ────
            semana = date.today().isocalendar()
            semana_str = f"{semana[0]}-W{semana[1]:02d}"

            contenido_semana = await conn.fetchrow("""
                SELECT
                    count(*) as total,
                    count(*) FILTER (WHERE estado = 'publicado') as publicados,
                    count(*) FILTER (WHERE estado = 'aprobado') as aprobados
                FROM om_voz_calendario
                WHERE tenant_id = $1 AND canal = $2 AND semana = $3
            """, TENANT, canal, semana_str)

            max_score += 30
            if contenido_semana and contenido_semana["total"] > 0:
                score += 10
                elementos.append({"elemento": "Contenido planificado", "estado": "ok", "peso": 10})

                if contenido_semana["publicados"] > 0:
                    score += 20
                    elementos.append({"elemento": "Contenido publicado", "estado": "ok", "peso": 20})
                elif contenido_semana["aprobados"] > 0:
                    score += 10
                    elementos.append({"elemento": "Contenido aprobado (sin publicar)", "estado": "parcial", "peso": 20})
                else:
                    elementos.append({"elemento": "Contenido publicado", "estado": "pendiente", "peso": 20})
            else:
                elementos.append({"elemento": "Contenido planificado", "estado": "falta", "peso": 30})

            # ── 3. Telemetría existente ──────────────────────
            tiene_telemetria = await conn.fetchval("""
                SELECT 1 FROM om_voz_telemetria_canal
                WHERE tenant_id = $1 AND canal = $2
                    AND created_at > now() - interval '30 days'
            """, TENANT, canal)

            max_score += 20
            if tiene_telemetria:
                score += 20
                elementos.append({"elemento": "Telemetría registrada", "estado": "ok", "peso": 20})
            else:
                elementos.append({"elemento": "Telemetría registrada", "estado": "falta", "peso": 20})

            # ── 4. IRC del canal ─────────────────────────────
            irc = await conn.fetchval("""
                SELECT irc_score FROM om_voz_irc
                WHERE tenant_id = $1 AND canal = $2 AND activo = TRUE
            """, TENANT, canal)

            max_score += 10
            if irc and float(irc) >= 0.3:
                score += 10
                elementos.append({"elemento": "IRC calculado", "estado": "ok", "peso": 10})
            else:
                elementos.append({"elemento": "IRC calculado", "estado": "bajo", "peso": 10})

            # ── 5. Estrategia activa ─────────────────────────
            tiene_estrategia = await conn.fetchval("""
                SELECT 1 FROM om_voz_estrategia
                WHERE tenant_id = $1 AND activa = TRUE
            """, TENANT)

            max_score += 20
            if tiene_estrategia:
                score += 20
                elementos.append({"elemento": "Estrategia activa", "estado": "ok", "peso": 20})
            else:
                elementos.append({"elemento": "Estrategia activa", "estado": "falta", "peso": 20})

            # Calcular ISP como porcentaje
            isp_score = round(score / max(max_score, 1) * 100, 1)

            # Almacenar
            await conn.execute("""
                INSERT INTO om_voz_isp (
                    tenant_id, canal, fecha_auditoria, isp_score,
                    elementos, elementos_evaluados, acciones_generadas,
                    posicion_matricial, automatico
                ) VALUES ($1, $2, CURRENT_DATE, $3, $4::jsonb,
                    $5::jsonb, $6::jsonb, $7, TRUE)
            """, TENANT, canal, isp_score,
                json.dumps(elementos, ensure_ascii=False),
                json.dumps({"total": len(elementos), "ok": sum(1 for e in elementos if e["estado"] == "ok")}),
                json.dumps([]),  # acciones se generan en el briefing
                "",  # posicion
            )

            resultados[canal] = {
                "isp_score": isp_score,
                "elementos": len(elementos),
                "ok": sum(1 for e in elementos if e["estado"] == "ok"),
                "pendientes": sum(1 for e in elementos if e["estado"] in ("pendiente", "falta")),
            }

    # ISP global (ponderado por IRC)
    from src.pilates.voz_identidad import obtener_irc
    irc_all = await obtener_irc()
    irc_map = {c["canal"]: float(c["irc_score"]) for c in irc_all}

    total_peso = sum(irc_map.get(c, 0.1) for c in resultados)
    isp_global = round(
        sum(resultados[c]["isp_score"] * irc_map.get(c, 0.1) for c in resultados)
        / max(total_peso, 0.1),
        1
    )

    log.info("voz_isp_automatico", global_score=isp_global)

    return {
        "status": "ok",
        "isp_global": isp_global,
        "canales": resultados,
    }


# ============================================================
# CICLO COMPLETO — Ejecutar los 5 ciclos en secuencia
# ============================================================

async def ejecutar_ciclo_completo() -> dict:
    """Ejecuta los 5 ciclos en orden.

    1. ESCUCHAR → detectar señales
    2. PRIORIZAR → clasificar pendientes
    3. PROPONER → ya existe en calendario (no recalcula aquí)
    4. EJECUTAR → pendiente de APIs reales (devuelve estado actual)
    5. APRENDER → recalcular IRC + ISP

    Se ejecutará cada lunes vía cron (20e).
    También bajo demanda desde cockpit.
    """
    resultados = {}

    # 1. ESCUCHAR
    r1 = await escuchar()
    resultados["escuchar"] = r1

    # 2. PRIORIZAR
    r2 = await priorizar()
    resultados["priorizar"] = {
        "total": r2["total"],
        "criticas": r2["criticas"],
        "altas": r2["altas"],
    }

    # 3. PROPONER (estado del calendario)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        semana = date.today().isocalendar()
        semana_str = f"{semana[0]}-W{semana[1]:02d}"
        cal = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE estado = 'planificado') as planificados,
                count(*) FILTER (WHERE estado = 'aprobado') as aprobados,
                count(*) FILTER (WHERE estado = 'publicado') as publicados
            FROM om_voz_calendario
            WHERE tenant_id = $1 AND semana = $2
        """, TENANT, semana_str)

    resultados["proponer"] = {
        "semana": semana_str,
        "total": cal["total"] if cal else 0,
        "planificados": cal["planificados"] if cal else 0,
        "aprobados": cal["aprobados"] if cal else 0,
        "publicados": cal["publicados"] if cal else 0,
    }

    # 4. EJECUTAR (estado — no ejecuta nada automáticamente)
    resultados["ejecutar"] = {
        "modo": "manual",
        "nota": "APIs de canales no conectadas. Ejecución manual via cockpit.",
    }

    # 5. APRENDER
    r5_irc = await recalcular_irc()
    r5_isp = await calcular_isp_automatico()
    resultados["aprender"] = {
        "irc_actualizados": r5_irc["canales_actualizados"],
        "isp_global": r5_isp["isp_global"],
    }

    return {"status": "ok", "ciclos": resultados}


# ============================================================
# SECCIÓN VOZ PARA BRIEFING SEMANAL
# ============================================================

async def seccion_voz_briefing() -> dict:
    """Genera la sección Voz para el briefing semanal.

    Incluye:
    - Resumen de estrategia activa
    - ISP por canal
    - Señales pendientes
    - Calendario de la semana
    - Recomendaciones
    """
    pool = await _get_pool()

    # Estrategia activa
    from src.pilates.voz_estrategia import obtener_estrategia_activa
    estrategia = await obtener_estrategia_activa()

    # ISP
    isp = await calcular_isp_automatico()

    # Señales pendientes
    senales = await priorizar()

    # Telemetría reciente (última semana)
    async with pool.acquire() as conn:
        telem_reciente = await conn.fetch("""
            SELECT canal,
                SUM(leads_generados) as leads,
                SUM(reservas_directas) as reservas,
                SUM(conversiones_cliente) as conversiones
            FROM om_voz_telemetria_canal
            WHERE tenant_id = $1
                AND created_at > now() - interval '7 days'
            GROUP BY canal
        """, TENANT)

    return {
        "estrategia": {
            "foco": estrategia.get("estrategia", {}).get("foco_principal", "sin_estrategia"),
            "narrativa": estrategia.get("estrategia", {}).get("narrativa", ""),
        } if "error" not in estrategia else {"foco": "sin_estrategia", "narrativa": "No hay estrategia activa"},
        "isp": {
            "global": isp.get("isp_global", 0),
            "canales": isp.get("canales", {}),
        },
        "senales": {
            "total": senales.get("total", 0),
            "criticas": senales.get("criticas", 0),
            "altas": senales.get("altas", 0),
        },
        "calendario": {
            "items": len(estrategia.get("calendario", [])) if "error" not in estrategia else 0,
        },
        "telemetria_semana": [
            {
                "canal": t["canal"],
                "leads": t["leads"] or 0,
                "reservas": t["reservas"] or 0,
                "conversiones": t["conversiones"] or 0,
            }
            for t in telem_reciente
        ],
    }
