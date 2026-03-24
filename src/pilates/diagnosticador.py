"""Diagnosticador autónomo — Agente G2: datos reales → diagnóstico ACD completo.

Pipeline: métricas → evaluar_funcional (LLM percibe) → campo + estado + repertorio + prescripción (código razona).

Ejecuta semanalmente (lunes) en cron.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta, timezone

from src.db.client import get_pool, log_diagnostico
from src.tcf.diagnostico import clasificar_estado

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request
ORIGEN = "DIAGNOSTICADOR"


async def _recopilar_metricas() -> dict:
    """Recopila métricas reales de las últimas 4 semanas."""
    pool = await get_pool()
    ahora = datetime.now(timezone.utc)
    hace_4_sem = ahora - timedelta(weeks=4)

    async with pool.acquire() as conn:
        total_activos = await conn.fetchval(
            "SELECT count(*) FROM om_contratos WHERE tenant_id = $1 AND estado = 'activo'",
            TENANT) or 0

        bajas_periodo = await conn.fetchval(
            "SELECT count(*) FROM om_contratos WHERE tenant_id = $1 AND estado = 'cancelado' AND updated_at >= $2",
            TENANT, hace_4_sem) or 0

        nuevos_clientes = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id = $1 AND fecha_alta >= $2::date",
            TENANT, hace_4_sem.date()) or 0

        sesiones_grupo = await conn.fetchval(
            "SELECT count(*) FROM om_sesiones WHERE tenant_id = $1 AND tipo = 'grupo' AND fecha >= $2::date",
            TENANT, hace_4_sem.date()) or 0

        sesiones_bajas = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones s
            WHERE s.tenant_id = $1 AND s.tipo = 'grupo' AND s.fecha >= $2::date
            AND (SELECT count(*) FROM om_asistencias a WHERE a.sesion_id = s.id AND a.estado = 'asistio') < 3
        """, TENANT, hace_4_sem.date()) or 0

        total_asistencias = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON a.sesion_id = s.id
            WHERE s.tenant_id = $1 AND s.fecha >= $2::date AND a.estado = 'asistio'
        """, TENANT, hace_4_sem.date()) or 0

        try:
            senales_voz = await conn.fetchval(
                "SELECT count(*) FROM om_voz_senales WHERE tenant_id = $1 AND created_at >= $2",
                TENANT, hace_4_sem) or 0
        except Exception:
            senales_voz = 0

        try:
            tensiones = await conn.fetchval(
                "SELECT count(*) FROM om_voz_tensiones WHERE tenant_id = $1 AND created_at >= $2",
                TENANT, hace_4_sem) or 0
        except Exception:
            tensiones = 0

        try:
            procesos = await conn.fetchval(
                "SELECT count(*) FROM om_voz_adn_procesos WHERE tenant_id = $1",
                TENANT) or 0
        except Exception:
            procesos = 0

        cobrado = await conn.fetchval("""
            SELECT COALESCE(sum(monto), 0) FROM om_pagos
            WHERE tenant_id = $1 AND created_at >= $2
        """, TENANT, hace_4_sem) or 0

        pendiente = await conn.fetchval("""
            SELECT COALESCE(sum(total), 0) FROM om_cargos
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT) or 0

    return {
        "total_activos": total_activos,
        "bajas_periodo": bajas_periodo,
        "nuevos_clientes": nuevos_clientes,
        "sesiones_grupo": sesiones_grupo,
        "sesiones_bajas": sesiones_bajas,
        "total_asistencias": total_asistencias,
        "senales_voz": senales_voz,
        "tensiones": tensiones,
        "procesos": procesos,
        "cobrado": float(cobrado),
        "pendiente": float(pendiente),
    }


def _fallback_heuristico(metricas: dict) -> tuple:
    """Fallback si el LLM del evaluador funcional falla.

    Usa fórmulas simples (PEOR que LLM pero mejor que nada).
    SOLO se usa si evaluar_funcional() lanza excepción.
    """
    from src.tcf.campo import VectorFuncional

    tasa_ret = max(0, min(1, 1.0 - (metricas["bajas_periodo"] / max(metricas["total_activos"], 1))))
    eficiencia = max(0, min(1, 1.0 - (metricas["sesiones_bajas"] / max(metricas["sesiones_grupo"], 1))))
    asist_media = metricas["total_asistencias"] / max(metricas["sesiones_grupo"], 1)

    grados = {
        "F1": round(tasa_ret, 3),
        "F2": round(min(1, metricas["nuevos_clientes"] / max(metricas["total_activos"] * 0.1, 1)), 3),
        "F3": round(eficiencia, 3),
        "F4": round(min(1, asist_media / 6.0), 3),
        "F5": round(min(1, metricas["senales_voz"] / 20.0), 3),
        "F6": round(min(1, metricas["tensiones"] / 5.0), 3),
        "F7": round(min(1, metricas["procesos"] / 10.0), 3),
    }

    vector = VectorFuncional.from_dict(grados)
    lentes_heur = {
        "salud": round((grados["F1"] * 0.4 + grados["F3"] * 0.3 + grados["F4"] * 0.3), 3),
        "sentido": round((grados["F2"] * 0.3 + grados["F5"] * 0.4 + grados["F6"] * 0.3), 3),
        "continuidad": round((grados["F7"] * 0.5 + min(1, metricas["cobrado"] / max(metricas["cobrado"] + metricas["pendiente"], 1)) * 0.5), 3),
    }

    scores_raw = {}
    for fi, g in grados.items():
        scores_raw[fi] = {"salud": g, "sentido": round(g * 0.7, 3), "continuidad": round(g * 0.5, 3)}

    return scores_raw, vector, lentes_heur


async def diagnosticar_tenant() -> dict:
    """Ejecuta diagnóstico ACD completo sobre datos reales.

    Pipeline:
    1. Recopilar métricas (código puro, $0)
    2. P1: evaluar_funcional (LLM percibe matices, ~$0.005)
    3. P2: evaluar_campo (código puro, $0)
    4. P3: clasificar_estado (código puro, $0)
    5. P4: inferir_repertorio (1 LLM barata + IC2-IC6 en código, ~$0.003)
    6. Prescribir (código puro, $0)
    7. Persistir + emitir al bus + pizarra + feed
    """
    # 1. Recopilar métricas
    metricas = await _recopilar_metricas()
    log.info("diagnosticador_metricas", activos=metricas["total_activos"],
             bajas=metricas["bajas_periodo"], nuevos=metricas["nuevos_clientes"])

    # === P1: EVALUAR FUNCIONAL via LLM (percepción real, no heurística) ===
    from src.tcf.evaluador_funcional import evaluar_funcional

    texto_caso = f"""AUTHENTIC PILATES — Estudio de Pilates en Albelda de Iregua (La Rioja, España).
Instructor único: Jesús. Método EEDAP (Pilates auténtico/terapéutico).
Pueblo de ~4.000 habitantes, cabeza de comarca, cerca de Logroño.

DATOS REALES DE LAS ÚLTIMAS 4 SEMANAS:

RETENCIÓN (F1):
- Clientes con contrato activo: {metricas['total_activos']}
- Bajas en el periodo: {metricas['bajas_periodo']}
- Tasa retención: {100 - round(metricas['bajas_periodo'] / max(metricas['total_activos'], 1) * 100)}%

CAPTACIÓN (F2):
- Nuevos clientes: {metricas['nuevos_clientes']}
- Ratio nuevos/activos: {round(metricas['nuevos_clientes'] / max(metricas['total_activos'], 1) * 100, 1)}%

DEPURACIÓN (F3):
- Sesiones grupo totales: {metricas['sesiones_grupo']}
- Sesiones con menos de 3 alumnos (infrautilizadas): {metricas['sesiones_bajas']}
- % sesiones infrautilizadas: {round(metricas['sesiones_bajas'] / max(metricas['sesiones_grupo'], 1) * 100)}%
- NOTA: El estudio tiene ~16 grupos programados. Si la mayoría están infrautilizados
  y no se cierran ni fusionan, eso indica F3 MUY baja — no hay proceso de eliminar
  lo que no funciona.

DISTRIBUCIÓN (F4):
- Total asistencias registradas: {metricas['total_asistencias']}
- Media asistentes por sesión grupo: {round(metricas['total_asistencias'] / max(metricas['sesiones_grupo'], 1), 1)}
- NOTA: Si hay días sobrecargados y otros vacíos, F4 es baja.
  Instructor único = cuello de botella de distribución.

IDENTIDAD/FRONTERA (F5):
- Señales de voz (contenido, comunicación): {metricas['senales_voz']}
- Tensiones registradas: {metricas['tensiones']}
- NOTA: Si hay pocas señales de voz, el estudio no comunica su diferenciación.
  Si hay pocas tensiones registradas, no se está monitorizando el entorno.
  Método EEDAP es potencialmente un diferenciador fuerte, pero ¿está articulado?

ADAPTACIÓN (F6):
- Tensiones abiertas: {metricas['tensiones']}
- NOTA: Si hay tensiones sin resolver durante semanas, F6 es baja.
  Si no hay tensiones registradas, puede ser que no se monitoriza el entorno
  (F6 también baja pero por ceguera, no por estabilidad).

REPLICACIÓN (F7):
- Procesos documentados: {metricas['procesos']}
- NOTA: Instructor único sin procesos documentados = F7 MUY baja.
  Si Jesús no puede venir mañana, ¿un sustituto sabría qué hacer?
  ¿Cuánto del método está en su cabeza vs documentado?

FINANZAS (contexto para todas las F):
- Cobrado en el periodo: {metricas['cobrado']:.0f}€
- Pendiente de cobro: {metricas['pendiente']:.0f}€
- Ratio cobro: {round(metricas['cobrado'] / max(metricas['cobrado'] + metricas['pendiente'], 1) * 100)}%

EVALÚA las 7 funciones × 3 lentes con estos datos reales.
Para la lente SENTIDO (Se): pregúntate si el negocio COMPRENDE POR QUÉ hace lo que hace.
Si tiene 16 grupos y la mayoría están infrautilizados sin cerrar ninguno, Se es baja
(no cuestiona, no depura con criterio, opera por inercia).
Para la lente CONTINUIDAD (C): pregúntate si esto sobreviviría sin el fundador.
Si 0 procesos documentados y método en la cabeza de una persona, C es MUY baja."""

    try:
        scores_raw, vector = await evaluar_funcional(texto_caso)
        log.info("diagnosticador_p1_ok", vector=vector.to_dict(),
                 eslabon=vector.eslabon_debil())
    except Exception as e:
        log.error("diagnosticador_p1_error", error=str(e))
        # Fallback: si el LLM falla, usar heurística degradada
        scores_raw, vector, lentes = _fallback_heuristico(metricas)
        estado = clasificar_estado(lentes)
        return {
            "diagnostico_id": None,
            "estado": estado.id, "nombre": estado.nombre,
            "lentes": lentes,
            "vector_f": vector.to_dict(),
            "fallback": True, "error": str(e)[:200],
        }

    # === P2: EVALUAR CAMPO COMPLETO (código puro, $0) ===
    from src.tcf.campo import evaluar_campo
    estado_campo = evaluar_campo(vector)
    lentes = estado_campo.lentes
    log.info("diagnosticador_p2_ok", lentes=lentes)

    # === P3: CLASIFICAR ESTADO (código puro, $0) ===
    scores_f_se = {fi: scores_raw[fi]["sentido"] for fi in scores_raw}
    estado = clasificar_estado(lentes, scores_f_se)
    log.info("diagnosticador_p3_ok", estado=estado.id, gap=estado.gap)

    # === P4: INFERIR REPERTORIO INT×P×R (1 LLM barata + IC2-IC6 en código) ===
    from src.tcf.repertorio import inferir_repertorio

    repertorio = None
    try:
        repertorio = await inferir_repertorio(texto_caso, vector)
        log.info("diagnosticador_p4_ok",
                 activas=len(repertorio.ints_activas),
                 advertencias=len(repertorio.advertencias_ic))
    except Exception as e:
        log.warning("diagnosticador_p4_error", error=str(e))

    # === ENSAMBLAR DIAGNÓSTICO COMPLETO ===
    from src.tcf.diagnostico import DiagnosticoCompleto
    diagnostico_completo = DiagnosticoCompleto(
        scores_raw=scores_raw,
        vector=vector,
        estado_campo=estado_campo,
        estado=estado,
        repertorio=repertorio,
    ) if repertorio else None

    # === PRESCRIPCIÓN (código puro, $0) ===
    prescripcion_acd = None
    if diagnostico_completo:
        try:
            from src.tcf.prescriptor import prescribir
            prescripcion_acd = prescribir(diagnostico_completo)
            log.info("diagnosticador_prescripcion_ok",
                     ints=len(prescripcion_acd.ints),
                     ps=len(prescripcion_acd.ps),
                     rs=len(prescripcion_acd.rs),
                     objetivo=prescripcion_acd.objetivo)
        except Exception as e:
            log.warning("diagnosticador_prescripcion_error", error=str(e))

    # === PERSISTIR ===
    diag_data = {
        "caso_input": f"Diagnóstico autónomo Authentic Pilates — {datetime.now(timezone.utc).isoformat()[:10]}",
        "vector_pre": json.dumps(vector.to_dict()),
        "lentes_pre": json.dumps(lentes),
        "estado_pre": estado.id,
        "flags_pre": [f.nombre for f in estado.flags] if estado.flags else [],
        "metricas": json.dumps({
            "raw": metricas,
            "scores_21": scores_raw,
            "repertorio": {
                "ints_activas": repertorio.ints_activas,
                "ints_atrofiadas": repertorio.ints_atrofiadas,
                "advertencias_ic": repertorio.advertencias_ic,
            } if repertorio else None,
        }),
        "resultado": "pendiente",
    }
    diag_id = await log_diagnostico(diag_data)

    # === COMPARAR CON ANTERIOR ===
    cambio = False
    pool = await get_pool()
    async with pool.acquire() as conn:
        anterior = await conn.fetchrow("""
            SELECT estado_pre FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC OFFSET 1 LIMIT 1
        """)
    if anterior and anterior["estado_pre"] != estado.id:
        cambio = True

    # === EMITIR AL BUS con scores_21 + repertorio + prescripción ===
    if cambio or estado.flags or repertorio:
        try:
            from src.pilates.bus import emitir
            payload = {
                "estado": estado.id,
                "nombre": estado.nombre,
                "lentes": lentes,
                "gap": estado.gap,
                "flags": [f.nombre for f in estado.flags],
                "cambio": cambio,
                "anterior": anterior["estado_pre"] if anterior else None,
                "diagnostico_id": diag_id,
                "scores_21": scores_raw,
            }
            if repertorio:
                payload["repertorio"] = {
                    "ints_activas": repertorio.ints_activas,
                    "ints_atrofiadas": repertorio.ints_atrofiadas,
                    "ints_ausentes": repertorio.ints_ausentes,
                    "ps_activos": repertorio.ps_activos,
                    "rs_activos": repertorio.rs_activos,
                    "advertencias_ic": repertorio.advertencias_ic,
                }
            if prescripcion_acd:
                payload["prescripcion"] = {
                    "ints": prescripcion_acd.ints,
                    "ps": prescripcion_acd.ps,
                    "rs": prescripcion_acd.rs,
                    "secuencia": prescripcion_acd.secuencia,
                    "frenar": prescripcion_acd.frenar,
                    "lente_objetivo": prescripcion_acd.lente_objetivo,
                    "objetivo": prescripcion_acd.objetivo,
                    "advertencias_ic": prescripcion_acd.advertencias_ic,
                }
            await emitir("DIAGNOSTICO", ORIGEN, payload,
                         prioridad=2 if cambio else 4)
        except Exception as e:
            log.warning("diagnosticador_bus_error", error=str(e))

    # === ESCRIBIR EN PIZARRA ===
    try:
        from src.pilates.pizarra import escribir
        await escribir(
            agente="DIAGNOSTICADOR",
            capa="sensorial",
            estado="completado",
            detectando=f"Estado {estado.id} ({estado.nombre}), gap={estado.gap:.2f}",
            interpretacion=f"S={lentes['salud']:.2f} Se={lentes['sentido']:.2f} C={lentes['continuidad']:.2f}. "
                           f"{'Cambió vs anterior' if cambio else 'Sin cambio'}. "
                           f"{len(estado.flags)} flags de peligro.",
            accion_propuesta=f"Prescripción: {prescripcion_acd.objetivo}" if prescripcion_acd else "Sin prescripción",
            necesita_de=["ENJAMBRE"] if repertorio else [],
            confianza=0.8,
            prioridad=2 if cambio else 4,
            datos={
                "repertorio_ints_activas": repertorio.ints_activas if repertorio else [],
                "advertencias_ic": repertorio.advertencias_ic if repertorio else [],
                "prescripcion_ints": prescripcion_acd.ints if prescripcion_acd else [],
            },
        )
    except Exception as e:
        log.debug("silenced_exception", exc=str(e))

    # === PUBLICAR AL FEED ===
    try:
        from src.pilates.feed import feed_diagnostico_acd
        await feed_diagnostico_acd(
            estado=estado.id,
            s=lentes.get("salud", 0), se=lentes.get("sentido", 0), c=lentes.get("continuidad", 0),
            cambio=str(cambio) if cambio else None)
    except Exception as e:
        log.warning("diagnosticador_feed_error", error=str(e))

    # === RETURN ===
    resultado = {
        "diagnostico_id": diag_id,
        "estado": estado.id,
        "nombre": estado.nombre,
        "tipo": estado.tipo,
        "lentes": lentes,
        "scores_21": scores_raw,
        "vector_f": vector.to_dict(),
        "gap": estado.gap,
        "flags": [f.nombre for f in estado.flags],
        "cambio_vs_anterior": cambio,
        "metricas_raw": metricas,
        "repertorio": {
            "ints_activas": repertorio.ints_activas,
            "ints_atrofiadas": repertorio.ints_atrofiadas,
            "ints_ausentes": repertorio.ints_ausentes,
            "ps_activos": repertorio.ps_activos,
            "rs_activos": repertorio.rs_activos,
            "advertencias_ic": repertorio.advertencias_ic,
        } if repertorio else None,
        "prescripcion": {
            "ints": prescripcion_acd.ints,
            "ps": prescripcion_acd.ps,
            "rs": prescripcion_acd.rs,
            "secuencia": prescripcion_acd.secuencia,
            "frenar": prescripcion_acd.frenar,
            "lente_objetivo": prescripcion_acd.lente_objetivo,
            "objetivo": prescripcion_acd.objetivo,
            "advertencias_ic": prescripcion_acd.advertencias_ic,
        } if prescripcion_acd else None,
    }

    log.info("diagnosticador_completo",
             estado=estado.id, cambio=cambio,
             flags=len(estado.flags),
             repertorio=bool(repertorio),
             prescripcion=bool(prescripcion_acd))
    return resultado
