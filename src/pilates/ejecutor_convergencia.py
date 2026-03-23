"""Ejecutor + Convergencia + Gestor — Los 3 agentes que cierran el circuito.

EJECUTOR (G5): Lee prescripciones del bus → determina AF destino → emite ACCION
CONVERGENCIA: Cuando 2+ AF señalan el mismo cliente/grupo → genera insight
GESTOR (G6): Cada N señales o semanal → poda señales expiradas, resume actividad

Estos 3 agentes no generan información nueva — ORQUESTAN la existente.
"""
from __future__ import annotations

import json
import structlog
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"

INSTRUCCION_EJECUTOR = """Tienes prescripciones de múltiples agentes.
Prioriza y resuelve conflictos:
- ¿AF3 dice cerrar un grupo pero AF2 dice captar para él?
- ¿AF1 dice retener un cliente pero AF3 dice que es zombi?
Genera un plan de acción UNIFICADO para la semana con máximo 5 acciones
priorizadas. Sin contradicciones. Cada acción debe indicar qué AF la originó."""

INSTRUCCION_CONVERGENCIA = """Múltiples agentes señalan al mismo cliente/grupo.
¿Qué SIGNIFICA esta convergencia? ¿Es una oportunidad oculta o un problema
sistémico? Genera un insight que ningún agente individual podría haber visto.
Si Carlos aparece como fantasma (AF1) Y como zombi (AF3), eso no son 2
problemas — es 1 decisión: ¿retener con esfuerzo o soltar limpiamente?"""

INSTRUCCION_GESTOR = """Resume la actividad de la semana del organismo.
¿Qué aprendió el sistema? ¿Qué acciones se propusieron? ¿Hay patrones
que emergen semana tras semana? Genera un briefing narrativo en español
coloquial para Jesús — como un socio inteligente que le cuenta
qué ha pasado esta semana en el negocio y qué debería hacer."""


# ============================================================
# EJECUTOR — Lee prescripciones y coordina AF
# ============================================================

async def ejecutar_prescripciones() -> dict:
    """Lee señales PRESCRIPCION del bus, razona con LLM y emite plan unificado.

    CEREBRO NIVEL 2 (Claude Sonnet 4.6): resuelve conflictos cross-AF.
    """
    from src.pilates.bus import leer_pendientes, marcar_procesada, emitir

    prescripciones = await leer_pendientes(tipo="PRESCRIPCION", limite=30)

    vetos_registrados = 0
    prescripciones_normales = []

    for señal in prescripciones:
        señal_id = str(señal["id"])
        payload = señal["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)

        try:
            if payload.get("subtipo") == "VETO":
                vetos_registrados += 1
                await marcar_procesada(señal_id, "EJECUTOR")
            else:
                prescripciones_normales.append({
                    "id": señal_id,
                    "origen": señal.get("origen", ""),
                    "payload": payload,
                })
                await marcar_procesada(señal_id, "EJECUTOR")
        except Exception as e:
            log.warning("ejecutor_error", señal_id=señal_id, error=str(e))

    # === CEREBRO NIVEL 2 (Claude Sonnet 4.6) — resolución cross-AF ===
    razonamiento = None
    acciones_emitidas = 0

    if prescripciones_normales:
        from src.pilates.cerebro_organismo import razonar
        razonamiento = await razonar(
            agente="EJECUTOR",
            funcion="Orquestación cross-AF",
            datos_detectados={"prescripciones": prescripciones_normales},
            instruccion_especifica=INSTRUCCION_EJECUTOR,
            nivel=2,
        )

        for accion in razonamiento.get("acciones", []):
            try:
                await emitir("ACCION", "EJECUTOR", {
                    "accion": accion.get("accion", ""),
                    "prioridad": accion.get("prioridad", 3),
                    "impacto": accion.get("impacto", ""),
                    "esfuerzo": accion.get("esfuerzo", ""),
                    "interpretacion": razonamiento["interpretacion"],
                }, prioridad=accion.get("prioridad", 3))
                acciones_emitidas += 1
            except Exception as e:
                log.warning("ejecutor_accion_error", error=str(e))

    log.info("ejecutor_completo", prescripciones=len(prescripciones),
        acciones=acciones_emitidas, vetos=vetos_registrados)

    return {
        "prescripciones_leidas": len(prescripciones),
        "acciones_emitidas": acciones_emitidas,
        "vetos_registrados": vetos_registrados,
        "razonamiento": razonamiento,
    }


def _funcion_a_af(funcion: str) -> str | None:
    """Mapea función L0.7 a agente funcional."""
    return {
        "F1": "AF1", "F2": "AF2", "F3": "AF3", "F4": "AF4",
        "F5": "AF5", "F6": "AF6", "F7": "AF7",
    }.get(funcion)


# ============================================================
# CONVERGENCIA — 2+ AF señalan el mismo objeto
# ============================================================

async def detectar_convergencia() -> dict:
    """Detecta cuando 2+ AF emitieron señales sobre el mismo cliente o grupo.

    Convergencia = señal de que algo es importante. Si AF1 dice "cliente fantasma"
    y AF3 dice "contrato zombi" del MISMO cliente, eso es convergencia.

    Busca en señales recientes (últimos 7 días) agrupando por cliente_id y grupo_id.
    """
    pool = await get_pool()
    desde = datetime.now(timezone.utc) - timedelta(days=7)

    convergencias = []

    async with pool.acquire() as conn:
        # Convergencia por cliente: 2+ AF distintos señalaron el mismo cliente
        try:
            rows = await conn.fetch("""
                SELECT
                    payload->>'cliente_id' as cliente_id,
                    array_agg(DISTINCT origen) as agentes,
                    count(*) as señales,
                    array_agg(DISTINCT payload->>'tipo') as tipos
                FROM om_senales_agentes
                WHERE tenant_id = $1 AND created_at >= $2
                AND payload->>'cliente_id' IS NOT NULL
                AND tipo = 'ALERTA'
                GROUP BY payload->>'cliente_id'
                HAVING count(DISTINCT origen) >= 2
            """, TENANT, desde)

            for r in rows:
                # Obtener nombre del cliente
                nombre = await conn.fetchval(
                    "SELECT nombre || ' ' || apellidos FROM om_clientes WHERE id = $1::uuid",
                    r["cliente_id"])

                convergencias.append({
                    "tipo": "convergencia_cliente",
                    "cliente_id": r["cliente_id"],
                    "nombre": nombre or "Desconocido",
                    "agentes": list(r["agentes"]),
                    "señales": r["señales"],
                    "tipos_detectados": list(r["tipos"]),
                    "insight": f"{nombre}: señalado por {', '.join(r['agentes'])} — requiere atención prioritaria.",
                })
        except Exception as e:
            log.warning("convergencia_cliente_error", error=str(e))

        # Convergencia por grupo: 2+ AF señalaron el mismo grupo
        try:
            rows_g = await conn.fetch("""
                SELECT
                    payload->>'grupo_id' as grupo_id,
                    array_agg(DISTINCT origen) as agentes,
                    count(*) as señales,
                    array_agg(DISTINCT payload->>'tipo') as tipos
                FROM om_senales_agentes
                WHERE tenant_id = $1 AND created_at >= $2
                AND payload->>'grupo_id' IS NOT NULL
                AND tipo IN ('ALERTA', 'PRESCRIPCION')
                GROUP BY payload->>'grupo_id'
                HAVING count(DISTINCT origen) >= 2
            """, TENANT, desde)

            for r in rows_g:
                nombre_g = await conn.fetchval(
                    "SELECT nombre FROM om_grupos WHERE id = $1::uuid", r["grupo_id"])
                convergencias.append({
                    "tipo": "convergencia_grupo",
                    "grupo_id": r["grupo_id"],
                    "nombre": nombre_g or "Desconocido",
                    "agentes": list(r["agentes"]),
                    "señales": r["señales"],
                    "tipos_detectados": list(r["tipos"]),
                    "insight": f"Grupo '{nombre_g}': señalado por {', '.join(r['agentes'])} — posible acción combinada.",
                })
        except Exception as e:
            log.warning("convergencia_grupo_error", error=str(e))

    # === CEREBRO NIVEL 2 (Claude Sonnet 4.6) — insights sistémicos ===
    razonamiento = None
    emitidas = 0

    if convergencias:
        from src.pilates.cerebro_organismo import razonar
        razonamiento = await razonar(
            agente="CONVERGENCIA",
            funcion="Detección de patrones sistémicos",
            datos_detectados={"convergencias": convergencias},
            instruccion_especifica=INSTRUCCION_CONVERGENCIA,
            nivel=2,
        )

        try:
            from src.pilates.bus import emitir
            for accion in razonamiento.get("acciones", []):
                await emitir("OPORTUNIDAD", "CONVERGENCIA", {
                    "accion": accion.get("accion", ""),
                    "insight": razonamiento["interpretacion"],
                    "prioridad": accion.get("prioridad", 3),
                    "patron": razonamiento.get("patron_detectado"),
                }, prioridad=accion.get("prioridad", 3))
                emitidas += 1
        except Exception as e:
            log.warning("convergencia_bus_error", error=str(e))

    log.info("convergencia_completa", encontradas=len(convergencias))
    return {
        "convergencias_cliente": len([c for c in convergencias if c["tipo"] == "convergencia_cliente"]),
        "convergencias_grupo": len([c for c in convergencias if c["tipo"] == "convergencia_grupo"]),
        "total": len(convergencias),
        "oportunidades_emitidas": emitidas,
        "razonamiento": razonamiento,
        "detalle": convergencias[:15],
    }


# ============================================================
# GESTOR AUTÓNOMO — Poda y mantenimiento del bus
# ============================================================

async def gestionar_bus() -> dict:
    """Gestor: mantiene el bus limpio y genera resumen de actividad.

    1. Señales procesadas >7 días: archivar conteo + eliminar
    2. Señales pendientes >48h: marcar como expiradas
    3. Resumen de actividad: señales por agente, por tipo, por día
    """
    pool = await get_pool()
    hace_7d = datetime.now(timezone.utc) - timedelta(days=7)
    hace_48h = datetime.now(timezone.utc) - timedelta(hours=48)

    archivadas = 0
    expiradas = 0

    async with pool.acquire() as conn:
        # 1. Contar señales viejas procesadas (para registro) y eliminar
        archivadas = await conn.fetchval("""
            SELECT count(*) FROM om_senales_agentes
            WHERE tenant_id = $1 AND estado IN ('procesada', 'error')
            AND created_at < $2
        """, TENANT, hace_7d) or 0

        if archivadas > 0:
            await conn.execute("""
                DELETE FROM om_senales_agentes
                WHERE tenant_id = $1 AND estado IN ('procesada', 'error')
                AND created_at < $2
            """, TENANT, hace_7d)

        # 2. Señales pendientes >48h: expirar
        result = await conn.execute("""
            UPDATE om_senales_agentes
            SET estado = 'error', procesada_por = 'GESTOR',
                procesada_at = now(), error_detalle = 'Expirada (pendiente >48h)'
            WHERE tenant_id = $1 AND estado = 'pendiente'
            AND created_at < $2
        """, TENANT, hace_48h)
        expiradas = int(result.split()[-1]) if result else 0

        # 3. Resumen de actividad (últimos 7 días)
        actividad = await conn.fetch("""
            SELECT origen, tipo, count(*) as n
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND created_at >= $2
            GROUP BY origen, tipo
            ORDER BY n DESC
        """, TENANT, hace_7d)

        resumen = defaultdict(lambda: defaultdict(int))
        for r in actividad:
            resumen[r["origen"]][r["tipo"]] = r["n"]

    # === CEREBRO NIVEL 1 (gpt-4o) — briefing narrativo semanal ===
    datos_gestor = {
        "archivadas_eliminadas": archivadas,
        "expiradas": expiradas,
        "actividad_7d": dict(resumen),
        "agentes_activos": len(resumen),
    }

    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar(
        agente="GESTOR",
        funcion="Gestión autónoma del bus",
        datos_detectados=datos_gestor,
        instruccion_especifica=INSTRUCCION_GESTOR,
        nivel=1,
    )

    resultado = {
        **datos_gestor,
        "razonamiento": razonamiento,
    }

    log.info("gestor_bus_completo", archivadas=archivadas, expiradas=expiradas,
        agentes=len(resumen))
    return resultado


# ============================================================
# EJECUTAR TODO
# ============================================================

async def ejecutar_circuito_completo() -> dict:
    """Ejecuta Ejecutor + Convergencia + Gestor en secuencia.

    Este es el cierre del circuito: las señales que generaron los AF
    son procesadas, las convergencias detectadas, y el bus limpiado.
    """
    ejecutor = await ejecutar_prescripciones()
    convergencia = await detectar_convergencia()
    gestor = await gestionar_bus()

    return {
        "ejecutor": ejecutor,
        "convergencia": convergencia,
        "gestor": gestor,
    }
