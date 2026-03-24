"""Sub-router: Cron, Alertas, Sistema, Autonomía, Predicciones, Onboarding tenant,
Bus de señales, AF (agentes funcionales), Organismo, Pizarras, SSE, Diagnóstico."""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.pilates.router import (
    TENANT, log, _get_pool, _row_to_dict, _calcular_readiness,
    SenalCreate, MarcarLeidoRequest,
)

router = APIRouter(tags=["sistema"])


# ============================================================
# AUTOMATISMOS / CRON
# ============================================================

@router.post("/cron/generar-sesiones")
async def generar_sesiones_endpoint(fecha_inicio: Optional[date] = None):
    """Genera sesiones de la semana para todos los grupos."""
    from src.pilates.automatismos import generar_sesiones_semana
    return await generar_sesiones_semana(fecha_inicio)


@router.post("/cron/{tipo}")
async def ejecutar_cron_endpoint(tipo: str):
    """Ejecuta batch automático. Tipos: inicio_semana, inicio_mes, diario."""
    from src.pilates.automatismos import ejecutar_cron
    result = await ejecutar_cron(tipo)
    if result.get("status") == "error":
        raise HTTPException(400, result["detail"])
    return result


@router.get("/alertas")
async def alertas_retencion():
    """Devuelve alertas de retención actuales."""
    from src.pilates.automatismos import detectar_alertas_retencion
    return await detectar_alertas_retencion()


# ============================================================
# BUS DE SEÑALES — Sistema nervioso del organismo
# ============================================================

@router.post("/bus/emitir")
async def bus_emitir(data: SenalCreate):
    """Emite una señal al bus de agentes."""
    from src.pilates.bus import emitir
    señal_id = await emitir(
        tipo=data.tipo,
        origen=data.origen,
        payload=data.payload,
        destino=data.destino,
        prioridad=data.prioridad,
    )
    return {"id": señal_id, "status": "emitida"}


@router.get("/bus/pendientes")
async def bus_pendientes(
    destino: Optional[str] = None,
    tipo: Optional[str] = None,
    limite: int = Query(default=20, le=100),
):
    """Lee señales pendientes del bus."""
    from src.pilates.bus import leer_pendientes
    señales = await leer_pendientes(destino=destino, tipo=tipo, limite=limite)
    return {"señales": señales, "total": len(señales)}


@router.patch("/bus/{senal_id}/procesar")
async def bus_procesar(senal_id: UUID, procesada_por: str = Query(...)):
    """Marca una señal como procesada."""
    from src.pilates.bus import marcar_procesada
    ok = await marcar_procesada(senal_id, procesada_por)
    if not ok:
        raise HTTPException(404, "Señal no encontrada o ya procesada")
    return {"status": "procesada"}


@router.get("/bus/historial")
async def bus_historial(
    limite: int = Query(default=50, le=200),
    tipo: Optional[str] = None,
    origen: Optional[str] = None,
):
    """Historial de señales del bus."""
    from src.pilates.bus import historial
    señales = await historial(limite=limite, tipo=tipo, origen=origen)
    return {"señales": señales, "total": len(señales)}


# ============================================================
# DIAGNOSTICADOR + BUSCADOR — Agentes autónomos ACD
# ============================================================

@router.post("/acd/diagnosticar-tenant")
async def acd_diagnosticar_tenant():
    """Ejecuta diagnóstico ACD sobre datos reales de Authentic Pilates."""
    from src.pilates.diagnosticador import diagnosticar_tenant
    return await diagnosticar_tenant()


@router.post("/acd/buscar-por-gaps")
async def acd_buscar_por_gaps():
    """Busca información dirigida por gaps ACD vía Perplexity."""
    from src.pilates.buscador import buscar_por_gaps
    return await buscar_por_gaps()


@router.post("/acd/enjambre")
async def acd_enjambre():
    """Ejecuta el enjambre cognitivo v2: modelo causal 4 niveles (3 secuenciales + 6 clusters paralelos)."""
    from src.pilates.enjambre import ejecutar_enjambre
    return await ejecutar_enjambre()


@router.post("/acd/g4")
async def acd_g4():
    """Ejecuta G4 completa: Enjambre -> Compositor -> Estratega -> Orquestador."""
    from src.pilates.compositor import ejecutar_g4
    return await ejecutar_g4()


@router.post("/acd/g4-recompilar")
async def acd_g4_recompilar():
    """G4 + Recompilador: diagnostica y reconfigura agentes automáticamente."""
    from src.pilates.recompilador import ejecutar_g4_con_recompilacion
    return await ejecutar_g4_con_recompilacion()


@router.post("/acd/recompilar")
async def acd_recompilar(request: Request):
    """Recompila configs de agentes desde prescripción manual."""
    body = await request.json()
    from src.pilates.recompilador import recompilar
    return await recompilar(body.get("prescripcion", body))


@router.post("/acd/director-opus")
async def acd_director_opus():
    """Director Opus: lee manual, comprende estado, diseña prompts D_híbrido."""
    from src.pilates.rate_limit import semaforo_opus
    if semaforo_opus.locked():
        raise HTTPException(status_code=429, detail="Director Opus ocupado")
    async with semaforo_opus:
        from src.pilates.director_opus import dirigir_orquesta
        return await dirigir_orquesta()


@router.post("/acd/metacognitivo")
async def acd_metacognitivo():
    """Meta-Cognitivo Opus: evalúa el sistema cognitivo mensualmente."""
    from src.pilates.rate_limit import semaforo_metacog
    if semaforo_metacog.locked():
        raise HTTPException(status_code=429, detail="Metacognitivo ocupado")
    async with semaforo_metacog:
        from src.pilates.metacognitivo import ejecutar_metacognitivo
        return await ejecutar_metacognitivo()


@router.post("/acd/ingeniero")
async def acd_ingeniero():
    """Ingeniero: procesa instrucciones pendientes del Meta-Cognitivo."""
    from src.pilates.ingeniero import procesar_instrucciones_pendientes
    return await procesar_instrucciones_pendientes()


@router.get("/acd/config-agentes")
async def acd_config_agentes(agente: Optional[str] = None):
    """Lista configs dinámicas activas de agentes."""
    from src.db.client import get_pool
    pool = await get_pool()
    conditions = ["tenant_id = $1", "activa = TRUE"]
    params: list = [TENANT]
    idx = 2
    if agente:
        conditions.append(f"agente = ${idx}")
        params.append(agente)
    where = " AND ".join(conditions)
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT agente, version, config, aprobada_por, created_at
            FROM om_config_agentes WHERE {where}
            ORDER BY agente, version DESC
        """, *params)
    return [_row_to_dict(r) for r in rows]


# ============================================================
# VIGÍA + MECÁNICO + AUTÓFAGO — Goma META del organismo
# ============================================================

@router.post("/sistema/vigilar")
async def sistema_vigilar():
    """Ejecuta health checks del Vigía. Emite ALERTAs al bus."""
    from src.pilates.vigia import vigilar
    return await vigilar()


@router.post("/sistema/mecanico")
async def sistema_mecanico():
    """Ejecuta el Mecánico: procesa ALERTAs pendientes."""
    from src.pilates.mecanico import procesar_alertas
    return await procesar_alertas()


@router.post("/sistema/autofagia")
async def sistema_autofagia():
    """Ejecuta autofagia: detecta código muerto, datos caducados, archivos obsoletos.
    NO borra nada. Solo registra propuestas en om_mejoras_pendientes."""
    from src.pilates.autofago import ejecutar_autofagia
    return await ejecutar_autofagia()


# ============================================================
# G4 — Motor Cognitivo (Enjambre + Compositor + Recompilador)
# ============================================================

@router.post("/sistema/enjambre")
async def sistema_enjambre():
    """Ejecuta enjambre cognitivo: 9 agentes diagnostican INT x P x R."""
    from src.pilates.enjambre import ejecutar_enjambre
    return await ejecutar_enjambre()


@router.post("/sistema/g4")
async def sistema_g4():
    """G4 completa: enjambre + compositor + estratega + orquestador."""
    from src.pilates.compositor import ejecutar_g4
    return await ejecutar_g4()


@router.post("/sistema/g4-recompilar")
async def sistema_g4_recompilar():
    """G4 + recompilación: diagnostica, prescribe y reconfigura agentes."""
    from src.pilates.recompilador import ejecutar_g4_con_recompilacion
    return await ejecutar_g4_con_recompilacion()


@router.post("/sistema/evaluador")
async def sistema_evaluador():
    """Evaluador: compara prescripción anterior con resultados actuales."""
    from src.pilates.evaluador_organismo import evaluar_semana
    return await evaluar_semana()


@router.post("/sistema/metacognitivo")
async def sistema_metacognitivo():
    """Meta-Cognitivo Opus: evalúa si la capa cognitiva funciona."""
    from src.pilates.metacognitivo import ejecutar_metacognitivo
    return await ejecutar_metacognitivo()


@router.post("/sistema/ingeniero")
async def sistema_ingeniero():
    """Ingeniero: procesa instrucciones pendientes del Meta-Cognitivo."""
    from src.pilates.ingeniero import procesar_instrucciones_pendientes
    return await procesar_instrucciones_pendientes()


@router.get("/sistema/estado")
async def sistema_estado():
    """Estado completo del sistema: checks + bus + diagnóstico + mejoras pendientes."""
    from src.pilates.vigia import ejecutar_checks
    from src.pilates.bus import contar_pendientes

    checks = await ejecutar_checks()
    bus = await contar_pendientes()

    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        ultimo_diag = await conn.fetchrow("""
            SELECT estado_pre, lentes_pre, created_at FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        mejoras_pend = 0
        try:
            mejoras_pend = await conn.fetchval("""
                SELECT count(*) FROM om_mejoras_pendientes
                WHERE estado = 'pendiente' AND tenant_id = 'authentic_pilates'
            """) or 0
        except Exception as e:
            log.debug("silenced_exception", exc=str(e))

        autofagia_pend = 0
        try:
            autofagia_pend = await conn.fetchval("""
                SELECT count(*) FROM om_mejoras_pendientes
                WHERE estado = 'pendiente' AND tipo = 'AUTOFAGIA' AND tenant_id = 'authentic_pilates'
            """) or 0
        except Exception as e:
            log.debug("silenced_exception", exc=str(e))

    return {
        "health": [{"subsistema": c.subsistema, "estado": c.estado, "mensaje": c.mensaje}
                   for c in checks],
        "bus_pendientes": bus,
        "ultimo_diagnostico": {
            "estado": ultimo_diag["estado_pre"] if ultimo_diag else None,
            "lentes": ultimo_diag["lentes_pre"] if ultimo_diag else None,
            "fecha": str(ultimo_diag["created_at"])[:10] if ultimo_diag else None,
        } if ultimo_diag else None,
        "mejoras_arquitecturales_pendientes": mejoras_pend,
        "propuestas_autofagia_pendientes": autofagia_pend,
    }


@router.get("/sistema/mejoras")
async def sistema_mejoras(
    estado: Optional[str] = "pendiente",
    tipo: Optional[str] = None,
    limite: int = Query(default=30, le=100),
):
    """Lista mejoras pendientes (ARQUITECTURAL + AUTOFAGIA). Para revisión CR1."""
    from src.db.client import get_pool
    pool = await get_pool()
    conditions = ["tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if estado:
        conditions.append(f"estado = ${idx}")
        params.append(estado)
        idx += 1

    if tipo:
        conditions.append(f"tipo = ${idx}")
        params.append(tipo)
        idx += 1

    where = " AND ".join(conditions)
    params.append(limite)

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT id, created_at, tipo, estado, origen, descripcion, metadata
                FROM om_mejoras_pendientes
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ${idx}
            """, *params)
        return [_row_to_dict(r) for r in rows]
    except Exception:
        return []


@router.patch("/sistema/mejoras/{mejora_id}")
async def sistema_mejora_decidir(
    mejora_id: UUID,
    decision: str = Query(..., pattern="^(aprobada|rechazada|completada)$"),
):
    """CR1: Aprobar, rechazar o completar una mejora pendiente."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_mejoras_pendientes SET estado = $1
            WHERE id = $2 AND tenant_id = $3
        """, decision, mejora_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Mejora no encontrada")

    log.info("mejora_decidida", id=str(mejora_id), decision=decision)
    return {"status": decision, "id": str(mejora_id)}


# ============================================================
# AF1 CONSERVACIÓN + AF3 DEPURACIÓN — Agentes funcionales
# ============================================================

@router.post("/af/conservacion")
async def af_conservacion():
    """AF1: Detecta clientes en riesgo de abandono. Emite ALERTAs al bus."""
    from src.pilates.af1_conservacion import ejecutar_af1
    return await ejecutar_af1()


@router.post("/af/depuracion")
async def af_depuracion():
    """AF3: Detecta sesiones y servicios ineficientes. Emite ALERTAs + VETOs al bus."""
    from src.pilates.af3_depuracion import ejecutar_af3
    return await ejecutar_af3()


@router.post("/af/identidad")
async def af_identidad():
    """AF5: Detecta gaps de identidad, coherencia de canales, diferenciación."""
    from src.pilates.af5_identidad import ejecutar_af5
    return await ejecutar_af5()


# ============================================================
# AF2 + AF4 + AF6 + AF7 — Agentes funcionales restantes
# ============================================================

@router.post("/af/captacion")
async def af_captacion():
    """AF2: Detecta leads perdidos + tasa conversión. Respeta VETOs de AF3."""
    from src.pilates.af_restantes import ejecutar_af2
    return await ejecutar_af2()


@router.post("/af/distribucion")
async def af_distribucion():
    """AF4: Detecta desequilibrios horarios y ratio individual/grupo."""
    from src.pilates.af_restantes import ejecutar_af4
    return await ejecutar_af4()


@router.post("/af/adaptacion")
async def af_adaptacion():
    """AF6: Detecta tensiones sin resolver y señala necesidad de adaptación."""
    from src.pilates.af_restantes import ejecutar_af6
    return await ejecutar_af6()


@router.post("/af/replicacion")
async def af_replicacion():
    """AF7: Detecta gaps en documentación y readiness de replicación."""
    from src.pilates.af_restantes import ejecutar_af7
    return await ejecutar_af7()


@router.post("/af/todos")
async def af_todos():
    """Ejecuta TODOS los AF restantes (AF2+AF4+AF6+AF7) de una vez."""
    from src.pilates.af_restantes import ejecutar_af_restantes
    return await ejecutar_af_restantes()


# ============================================================
# PROPIOCEPCIÓN — El organismo se mide a sí mismo
# ============================================================

@router.post("/sistema/propiocepcion")
async def sistema_propiocepcion(periodo: str = Query(default="diario", pattern="^(diario|semanal)$")):
    """Genera snapshot de telemetría del organismo."""
    from src.pilates.propiocepcion import snapshot
    return await snapshot(periodo)


@router.get("/sistema/tendencia")
async def sistema_tendencia(n: int = Query(default=10, le=30)):
    """Últimos N snapshots de telemetría para visualizar tendencia."""
    from src.pilates.propiocepcion import obtener_tendencia
    snapshots = await obtener_tendencia(n)
    return {"snapshots": snapshots, "total": len(snapshots)}


# ============================================================
# EJECUTOR + CONVERGENCIA + GESTOR — Cierre del circuito
# ============================================================

@router.post("/sistema/ejecutor")
async def sistema_ejecutor():
    """Ejecutor: lee prescripciones del bus y emite ACCIONes a AF."""
    from src.pilates.ejecutor_convergencia import ejecutar_prescripciones
    return await ejecutar_prescripciones()


@router.post("/sistema/convergencia")
async def sistema_convergencia():
    """Detecta cuando 2+ AF señalan el mismo cliente/grupo."""
    from src.pilates.ejecutor_convergencia import detectar_convergencia
    return await detectar_convergencia()


@router.post("/sistema/gestor")
async def sistema_gestor():
    """Gestor: limpia bus + resumen de actividad."""
    from src.pilates.ejecutor_convergencia import gestionar_bus
    return await gestionar_bus()


@router.post("/sistema/circuito")
async def sistema_circuito():
    """Ejecuta Ejecutor + Convergencia + Gestor de una vez."""
    from src.pilates.ejecutor_convergencia import ejecutar_circuito_completo
    return await ejecutar_circuito_completo()


# ============================================================
# COLLECTORS — Pull métricas de canales
# ============================================================

@router.post("/collectors")
async def run_collectors():
    """Ejecuta collectors: Instagram, Google Business, WhatsApp."""
    from src.pilates.collectors import collect_all
    return await collect_all()


# ============================================================
# ORGANISMO — Dashboard del sistema cognitivo
# ============================================================

@router.get("/organismo/dashboard")
async def organismo_dashboard():
    """Dashboard completo del organismo: gomas, agentes, diagnóstico, bus."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Último diagnóstico ACD
        diag = await conn.fetchrow("""
            SELECT estado_pre, lentes_pre, vector_pre, metricas, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        # Último enjambre G4
        g4 = await conn.fetchrow("""
            SELECT estado_acd_base, resultado_lentes, resultado_funciones,
                   resultado_clusters, señales_emitidas, tiempo_total_s, created_at
            FROM om_enjambre_diagnosticos
            ORDER BY created_at DESC LIMIT 1
        """)

        # Configs activas de agentes (recompilador)
        configs = await conn.fetch("""
            SELECT agente, version, created_at, aprobada_por
            FROM om_config_agentes
            WHERE tenant_id='authentic_pilates' AND activa=TRUE
            ORDER BY agente
        """)

        # Bus: resumen últimas 48h
        bus_resumen = await conn.fetch("""
            SELECT tipo, count(*) as total, max(prioridad) as max_prioridad,
                   max(created_at) as ultimo
            FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '48 hours'
            GROUP BY tipo ORDER BY total DESC
        """)

        # Bus: señales de alta prioridad no procesadas
        urgentes = await conn.fetch("""
            SELECT tipo, origen, prioridad,
                   payload->>'descripcion' as descripcion,
                   created_at
            FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates'
                AND estado='pendiente' AND prioridad <= 3
            ORDER BY prioridad, created_at DESC LIMIT 10
        """)

        # Propiocepción: último snapshot
        propio = await conn.fetchrow("""
            SELECT periodo, senales_emitidas, senales_procesadas, senales_pendientes,
                   actividad_agentes, agentes_silenciosos,
                   acd_estado, acd_lentes, acd_delta_lentes,
                   fixes_fontaneria, mejoras_arquitecturales, created_at
            FROM om_telemetria_sistema
            WHERE tenant_id='authentic_pilates'
            ORDER BY created_at DESC LIMIT 1
        """)

        # Actividad de agentes: quién emitió señales en los últimos 7 días
        agentes_activos = await conn.fetch("""
            SELECT origen, count(*) as señales, max(created_at) as ultimo
            FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '7 days'
            GROUP BY origen ORDER BY señales DESC
        """)

        # Feed organismo: últimas 10 noticias del sistema
        feed_org = await conn.fetch("""
            SELECT tipo, icono, titulo, detalle, severidad, created_at
            FROM om_feed_estudio
            WHERE tenant_id='authentic_pilates'
                AND tipo LIKE 'organismo_%'
            ORDER BY created_at DESC LIMIT 10
        """)

    def _safe(row):
        if not row:
            return None
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                pass
            elif isinstance(v, str):
                try:
                    d[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    pass  # expected
        return d

    return {
        "diagnostico_acd": _safe(diag),
        "diagnostico_cognitivo_g4": _safe(g4),
        "configs_agentes": [_safe(c) for c in configs],
        "bus": {
            "resumen_48h": [_safe(r) for r in bus_resumen],
            "urgentes": [_safe(u) for u in urgentes],
        },
        "agentes_activos_7d": [_safe(a) for a in agentes_activos],
        "propiocepcion": _safe(propio),
        "feed_organismo": [_safe(f) for f in feed_org],
        "gomas": {
            "G1_datos_senales": True,
            "G2_senales_diagnostico": True,
            "G3_diagnostico_busqueda": True,
            "G4_busqueda_prescripcion": True,
            "G5_prescripcion_accion": True,
            "G6_accion_aprendizaje": True,
            "META_rotura_reparacion": True,
        },
    }


@router.get("/organismo/bus")
async def organismo_bus(horas: int = 48, limit: int = 50):
    """Señales del bus en las últimas N horas."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        señales = await conn.fetch(f"""
            SELECT id, tipo, origen, estado, prioridad,
                   payload, created_at
            FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '{min(horas, 168)} hours'
            ORDER BY created_at DESC LIMIT {min(limit, 200)}
        """)
    return [{
        "id": str(s["id"]),
        "tipo": s["tipo"],
        "origen": s["origen"],
        "estado": s["estado"],
        "prioridad": s["prioridad"],
        "payload": s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"]) if s["payload"] else {},
        "created_at": s["created_at"].isoformat(),
    } for s in señales]


@router.get("/organismo/diagnostico-cognitivo")
async def organismo_diagnostico_cognitivo():
    """Último diagnóstico G4 completo: perfil INT x P x R + disfunciones + prescripción."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        g4 = await conn.fetchrow("""
            SELECT estado_acd_base, resultado_lentes, resultado_funciones,
                   resultado_clusters, señales_emitidas, tiempo_total_s, created_at
            FROM om_enjambre_diagnosticos
            ORDER BY created_at DESC LIMIT 1
        """)
        if not g4:
            return {"status": "sin_diagnostico", "mensaje": "Aún no se ha ejecutado el enjambre cognitivo."}

        # Lentes contiene repertorio + disfunciones
        lentes = g4["resultado_lentes"]
        if isinstance(lentes, str):
            lentes = json.loads(lentes)

        # Funciones contiene mecanismo causal o prescripción
        funciones = g4["resultado_funciones"]
        if isinstance(funciones, str):
            funciones = json.loads(funciones)

        # Clusters
        clusters = g4["resultado_clusters"]
        if isinstance(clusters, str):
            clusters = json.loads(clusters)

    return {
        "perfil": g4["estado_acd_base"],
        "repertorio_y_disfunciones": lentes,
        "mecanismo_causal_o_prescripcion": funciones,
        "clusters": clusters,
        "señales_emitidas": g4["señales_emitidas"],
        "tiempo_s": float(g4["tiempo_total_s"]) if g4["tiempo_total_s"] else 0,
        "fecha": g4["created_at"].isoformat(),
    }


@router.get("/organismo/pizarra")
async def organismo_pizarra():
    """Pizarra compartida del ciclo actual."""
    from src.pilates.pizarra import leer_todo, resumen_narrativo, _ciclo_actual
    return {
        "ciclo": _ciclo_actual(),
        "entradas": await leer_todo(),
        "resumen": await resumen_narrativo(),
    }


@router.get("/organismo/config-agentes")
async def organismo_config_agentes():
    """Configuración INT x P x R actual de cada agente (recompilador)."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        configs = await conn.fetch("""
            SELECT agente, config, version, aprobada_por, created_at
            FROM om_config_agentes
            WHERE tenant_id='authentic_pilates' AND activa=TRUE
            ORDER BY agente
        """)
    return [{
        "agente": c["agente"],
        "config": c["config"] if isinstance(c["config"], dict) else json.loads(c["config"]),
        "version": c["version"],
        "aprobada_por": c["aprobada_por"],
        "fecha": c["created_at"].isoformat(),
    } for c in configs]


@router.get("/organismo/director")
async def organismo_director():
    """Última ejecución del Director Opus."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        señal = await conn.fetchrow("""
            SELECT payload, created_at FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates' AND origen='DIRECTOR_OPUS'
            ORDER BY created_at DESC LIMIT 1
        """)
    if not señal:
        return {"estado_sistema": None, "estrategia_global": None, "configs": []}
    payload = señal["payload"] if isinstance(señal["payload"], dict) else json.loads(señal["payload"])
    return {**payload, "fecha": str(señal["created_at"])}


@router.get("/organismo/evaluacion")
async def organismo_evaluacion():
    """Última evaluación de prescripción."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        señal = await conn.fetchrow("""
            SELECT payload, created_at FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates' AND origen='EVALUADOR'
            ORDER BY created_at DESC LIMIT 1
        """)
    if not señal:
        return {"evaluacion_global": None, "delta_lentes": None}
    payload = señal["payload"] if isinstance(señal["payload"], dict) else json.loads(señal["payload"])
    return {**payload, "fecha": str(señal["created_at"])}


@router.get("/organismo/pizarra-cognitiva")
async def get_pizarra_cognitiva():
    """Recetas del Director para cada función — lo que piensa el organismo."""
    from src.pilates.pizarras import leer_recetas_ciclo
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    recetas = await leer_recetas_ciclo("authentic_pilates", ciclo)
    return {"ciclo": ciclo, "recetas": recetas, "total": len(recetas)}


@router.get("/organismo/plan-temporal")
async def get_plan_temporal():
    """Plan de ejecución del ciclo — qué componentes corren y en qué orden."""
    from src.pilates.pizarras import leer_plan_ciclo
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    plan = await leer_plan_ciclo("authentic_pilates", ciclo)
    return {"ciclo": ciclo, "plan": plan, "total": len(plan)}


@router.get("/organismo/patrones")
async def get_patrones():
    """Patrones aprendidos por el sistema — pizarra evolución."""
    from src.pilates.pizarras import leer_patrones
    patrones = await leer_patrones("authentic_pilates", min_confianza=0.3)
    return {"patrones": patrones, "total": len(patrones)}


@router.get("/organismo/mediaciones")
async def get_mediaciones_recientes():
    """Conflictos cross-AF resueltos por el Mediador."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_mediaciones
            WHERE tenant_id = 'authentic_pilates'
            ORDER BY created_at DESC LIMIT 10
        """)
    return [dict(r) for r in rows]


@router.get("/organismo/motor-resumen")
async def get_motor_resumen():
    """Resumen del motor: gasto, caché hits, presupuesto."""
    from src.motor.pensar import presupuesto_restante, _presupuesto_ciclo
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        semana = await conn.fetch("""
            SELECT modelo, count(*) as calls, SUM(coste_usd) as coste,
                   SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
            FROM om_motor_telemetria
            WHERE tenant_id='authentic_pilates' AND created_at >= date_trunc('week', now())
            GROUP BY modelo ORDER BY coste DESC
        """)
    return {
        "presupuesto_restante": round(presupuesto_restante(), 2),
        "gastado_ciclo": round(_presupuesto_ciclo, 4),
        "por_modelo": [dict(r) for r in semana],
    }


@router.get("/comunicaciones")
async def get_comunicaciones(estado: Optional[str] = None, limit: int = 50):
    """Lee pizarra de comunicaciones — tracking WA."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = """
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id = 'authentic_pilates'
        """
        params = []
        if estado:
            query += " AND estado = $1"
            params.append(estado)
        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]


@router.get("/mediaciones")
async def get_mediaciones(ciclo: Optional[str] = None):
    """Historial de mediaciones cross-AF."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        if ciclo:
            rows = await conn.fetch(
                "SELECT * FROM om_mediaciones WHERE tenant_id=$1 AND ciclo=$2 ORDER BY created_at DESC",
                TENANT, ciclo)
        else:
            rows = await conn.fetch(
                "SELECT * FROM om_mediaciones WHERE tenant_id=$1 ORDER BY created_at DESC LIMIT 50",
                TENANT)
    return [dict(r) for r in rows]


@router.get("/motor/telemetria")
async def motor_telemetria(ciclo: Optional[str] = None):
    """Telemetría del motor unificado: coste, tokens, cache hits por ciclo."""
    from src.db.client import get_pool
    from src.motor.pensar import presupuesto_restante, PRESUPUESTO_MAX_SEMANAL
    pool = await get_pool()
    async with pool.acquire() as conn:
        if ciclo:
            rows = await conn.fetch("""
                SELECT funcion, modelo, count(*) as llamadas,
                       sum(tokens_input) as tokens_in, sum(tokens_output) as tokens_out,
                       sum(coste_usd) as coste_total, sum(case when cache_hit then 1 else 0 end) as cache_hits,
                       avg(tiempo_ms) as avg_ms
                FROM om_motor_telemetria WHERE tenant_id=$1 AND ciclo=$2
                GROUP BY funcion, modelo ORDER BY coste_total DESC
            """, TENANT, ciclo)
        else:
            rows = await conn.fetch("""
                SELECT funcion, modelo, count(*) as llamadas,
                       sum(tokens_input) as tokens_in, sum(tokens_output) as tokens_out,
                       sum(coste_usd) as coste_total, sum(case when cache_hit then 1 else 0 end) as cache_hits,
                       avg(tiempo_ms) as avg_ms
                FROM om_motor_telemetria WHERE tenant_id=$1
                  AND created_at >= now() - interval '7 days'
                GROUP BY funcion, modelo ORDER BY coste_total DESC
            """, TENANT)
        cache_stats = await conn.fetchrow("""
            SELECT count(*) as entradas, sum(hits) as total_hits
            FROM om_pizarra_cache_llm WHERE tenant_id=$1 AND expires_at > now()
        """, TENANT)
    return {
        "presupuesto_restante": presupuesto_restante(),
        "presupuesto_max_semanal": PRESUPUESTO_MAX_SEMANAL,
        "cache": {"entradas_activas": cache_stats["entradas"], "total_hits": cache_stats["total_hits"] or 0},
        "detalle": [{
            "funcion": r["funcion"], "modelo": r["modelo"],
            "llamadas": r["llamadas"], "tokens_in": r["tokens_in"],
            "tokens_out": r["tokens_out"], "coste_usd": round(float(r["coste_total"] or 0), 4),
            "cache_hits": r["cache_hits"], "avg_ms": round(float(r["avg_ms"] or 0)),
        } for r in rows],
    }


@router.get("/pizarra/dominio")
async def get_pizarra_dominio():
    """Lee la pizarra dominio del tenant."""
    from src.pilates.pizarras import leer_dominio
    return await leer_dominio()


@router.get("/pizarra/interfaz")
async def get_pizarra_interfaz():
    """Lee la pizarra interfaz para el ciclo actual."""
    from src.pilates.pizarras import leer_layout_ciclo
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    layout = await leer_layout_ciclo("authentic_pilates", ciclo)

    if not layout:
        return {"source": "default", "capas": {
            "operativo":  {"label": "Operativo",  "icon": "\u26a1", "modulos": ["agenda", "calendario", "buscar", "grupos", "wa"]},
            "financiero": {"label": "Financiero", "icon": "\U0001f4b0", "modulos": ["pagos_pendientes", "resumen_mes", "facturas"]},
            "cognitivo":  {"label": "Cognitivo",  "icon": "\U0001f9e0", "modulos": ["pizarra", "estrategia", "evaluacion", "feed_cognitivo", "bus"]},
            "voz":        {"label": "Voz",        "icon": "\U0001f4e2", "modulos": ["voz_proactiva", "voz"]},
            "motor":      {"label": "Motor",      "icon": "\u2699\ufe0f", "modulos": ["motor"]},
            "identidad":  {"label": "Identidad",  "icon": "\U0001f9ec", "modulos": ["adn", "depuracion", "readiness", "engagement", "contenido", "presencia"]},
            "autonomia":  {"label": "Autonomia",  "icon": "\U0001f916", "modulos": ["autonomia"]},
        }}

    return {"source": "pizarra", "ciclo": ciclo, "layout": layout}


@router.get("/sse/pizarra")
async def sse_pizarra():
    """SSE: retransmite cambios de pizarra en tiempo real."""
    import asyncio as _asyncio
    from fastapi.responses import StreamingResponse

    async def event_generator():
        from src.db.client import get_pool
        pool = await get_pool()
        conn = await pool.acquire()

        queue = _asyncio.Queue()

        def on_notify(conn_ref, pid, channel, payload):
            queue.put_nowait(payload)

        await conn.add_listener("pizarra_actualizada", on_notify)
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"

        try:
            while True:
                try:
                    payload = await _asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {payload}\n\n"
                except _asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await conn.remove_listener("pizarra_actualizada", on_notify)
            await pool.release(conn)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ============================================================
# DIAGNÓSTICO DEL SISTEMA
# ============================================================

@router.get("/sistema/diagnostico")
async def diagnostico_sistema():
    """Diagnóstico completo del sistema — para Jesús en Modo Profundo."""
    from src.db.client import get_pool
    from src.motor.pensar import presupuesto_restante, _presupuesto_ciclo

    pool = await get_pool()
    checks = {}

    async with pool.acquire() as conn:
        # Tablas
        checks["tablas_om"] = await conn.fetchval(
            "SELECT count(*) FROM pg_tables WHERE tablename LIKE 'om_%'")

        # Tamaño DB
        checks["db_size_mb"] = await conn.fetchval(
            "SELECT pg_database_size(current_database()) / 1024 / 1024")

        # Cron state
        cron_rows = await conn.fetch(
            "SELECT tarea, ultima_ejecucion, resultado FROM om_cron_state ORDER BY ultima_ejecucion DESC")
        checks["cron"] = [dict(r) for r in cron_rows]

        # Motor LLM
        checks["motor"] = {
            "presupuesto_restante": presupuesto_restante(),
            "gastado_ciclo": _presupuesto_ciclo,
        }

        # Caché
        try:
            cache = await conn.fetchrow("""
                SELECT count(*) as entradas, SUM(hits) as total_hits
                FROM om_pizarra_cache_llm WHERE tenant_id='authentic_pilates'
            """)
            checks["cache_llm"] = dict(cache) if cache else {}
        except Exception:
            checks["cache_llm"] = "tabla_no_existe"

        # Pizarras
        for tabla in ["om_pizarra_dominio", "om_pizarra_cognitiva", "om_pizarra_temporal",
                      "om_pizarra_modelos", "om_pizarra_evolucion", "om_pizarra_interfaz"]:
            try:
                # SEGURO: tabla viene de lista hardcoded arriba, no de input usuario
                count = await conn.fetchval(f"SELECT count(*) FROM {tabla}")  # noqa: S608
                checks[f"pizarra_{tabla[13:]}"] = count
            except Exception:
                checks[f"pizarra_{tabla[13:]}"] = "no_existe"

        # Señales bus
        try:
            checks["bus_pendientes"] = await conn.fetchval(
                "SELECT count(*) FROM om_senales_agentes WHERE procesada=false AND tenant_id='authentic_pilates'")
        except Exception:
            checks["bus_pendientes"] = "tabla_no_existe"

    return {"timestamp": str(datetime.now()), "checks": checks}


@router.get("/sistema/audit-log")
async def get_audit_log(
    entidad: Optional[str] = None,
    entidad_id: Optional[str] = None,
    limite: int = Query(default=50, le=200),
):
    """Consulta el audit log (solo admin)."""
    from src.db.client import get_pool
    from src.pilates.audit_log import consultar
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await consultar(conn, entidad=entidad, entidad_id=entidad_id, limite=limite)


# ============================================================
# AUTONOMÍA + PREDICCIONES (F8)
# ============================================================

@router.get("/autonomia/dashboard")
async def dashboard_autonomia():
    """Qué ha hecho solo, qué ha pedido permiso, qué espera CR1."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        auto = await conn.fetchval("""
            SELECT count(*) FROM om_pizarra_comunicacion
            WHERE tenant_id='authentic_pilates' AND origen='AUTONOMIA'
                AND tipo='log_auto' AND created_at >= now() - interval '7 days'
        """) or 0
        notif = await conn.fetch("""
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id='authentic_pilates' AND origen='AUTONOMIA'
                AND tipo='notificacion_autonomia' AND created_at >= now() - interval '7 days'
        """)
        cr1 = await conn.fetch("""
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id='authentic_pilates' AND origen='AUTONOMIA'
                AND tipo='solicitud_cr1' AND estado='pendiente'
        """)
        postmortems = await conn.fetch("""
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id='authentic_pilates' AND origen='MECANICO'
                AND tipo='postmortem' AND created_at >= now() - interval '7 days'
            ORDER BY created_at DESC LIMIT 5
        """)
    return {
        "auto_7d": auto,
        "notificaciones": [dict(r) for r in notif],
        "cr1_pendientes": [dict(r) for r in cr1],
        "postmortems": [dict(r) for r in postmortems],
    }


@router.get("/predicciones")
async def get_predicciones():
    """Predicciones: abandonos + demanda + cashflow."""
    from src.pilates.predictor import predecir_abandonos, predecir_demanda_semana, predecir_cashflow_mes
    abandonos = await predecir_abandonos()
    demanda = await predecir_demanda_semana()
    cashflow = await predecir_cashflow_mes()
    return {"abandonos": abandonos, "demanda": demanda, "cashflow": cashflow}


@router.post("/onboarding/tenant")
async def onboarding_nuevo_tenant(request: Request):
    """Wizard: crea un nuevo tenant desde cero."""
    body = await request.json()
    nombre = body.get("nombre")
    ubicacion = body.get("ubicacion", "")
    tipo = body.get("tipo", "pilates")
    email = body.get("email", "")
    telefono = body.get("telefono", "")

    if not nombre:
        raise HTTPException(400, "nombre es requerido")

    # Generar tenant_id
    import re
    tenant_id = re.sub(r'[^a-z0-9_]', '_', nombre.lower().strip())[:40]

    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        # INSERT om_pizarra_dominio
        await conn.execute("""
            INSERT INTO om_pizarra_dominio (tenant_id, nombre, config)
            VALUES ($1, $2, $3::jsonb)
            ON CONFLICT (tenant_id) DO NOTHING
        """, tenant_id, nombre, json.dumps({
            "timezone": "Europe/Madrid", "moneda": "EUR",
            "tipo": tipo, "ubicacion": ubicacion,
            "email": email, "telefono": telefono,
            "funciones_activas": ["F1","F2","F3","F4","F5","F6","F7"],
            "idioma": "es",
        }))

        # INSERT om_pizarra_modelos (seeds)
        await conn.execute("""
            INSERT INTO om_pizarra_modelos (tenant_id, funcion, complejidad, modelo, origen)
            SELECT $1, funcion, complejidad, modelo, 'default'
            FROM om_pizarra_modelos
            WHERE tenant_id = 'authentic_pilates' AND origen = 'default'
            ON CONFLICT DO NOTHING
        """, tenant_id)

        # INSERT om_pizarra_identidad vacía
        await conn.execute("""
            INSERT INTO om_pizarra_identidad (tenant_id, esencia, origen)
            VALUES ($1, $2, 'onboarding')
            ON CONFLICT (tenant_id) DO NOTHING
        """, tenant_id, f"{nombre} — {tipo} en {ubicacion}")

        # INSERT cron state
        await conn.execute("""
            INSERT INTO om_cron_state (tenant_id, tarea, ultima_ejecucion, resultado)
            VALUES ($1, 'diaria', now(), 'onboarding')
            ON CONFLICT DO NOTHING
        """, tenant_id)

    log.info("onboarding_tenant_creado", tenant_id=tenant_id, tipo=tipo)
    return {"status": "ok", "tenant_id": tenant_id}


# ============================================================
# READINESS DE REPLICACIÓN
# ============================================================

@router.get("/readiness")
async def readiness_replicacion():
    """Calcula readiness de replicación del negocio."""
    return await _calcular_readiness()


# ============================================================
# FEED DEL ESTUDIO
# ============================================================

@router.get("/feed")
async def get_feed(limit: int = 20, solo_no_leidos: bool = False):
    """Timeline de noticias del estudio."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if solo_no_leidos:
            rows = await conn.fetch("""
                SELECT * FROM om_feed_estudio
                WHERE tenant_id = $1 AND leido = FALSE
                ORDER BY created_at DESC LIMIT $2
            """, TENANT, limit)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_feed_estudio
                WHERE tenant_id = $1
                ORDER BY created_at DESC LIMIT $2
            """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.post("/feed/marcar-leido")
async def feed_marcar_leido(data: MarcarLeidoRequest):
    """Marcar noticias como leídas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if data.todos:
            result = await conn.execute("""
                UPDATE om_feed_estudio SET leido = TRUE
                WHERE tenant_id = $1 AND leido = FALSE
            """, TENANT)
        elif data.ids:
            from uuid import UUID as _UUID
            uuids = [_UUID(i) for i in data.ids]
            result = await conn.execute("""
                UPDATE om_feed_estudio SET leido = TRUE
                WHERE tenant_id = $1 AND id = ANY($2)
            """, TENANT, uuids)
        else:
            return {"marcadas": 0}
    return {"status": "ok"}


@router.get("/feed/count")
async def feed_count():
    """Badge: número de noticias no leídas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("""
            SELECT count(*) FROM om_feed_estudio
            WHERE tenant_id = $1 AND leido = FALSE
        """, TENANT)
    return {"no_leidos": count}


# ============================================================
# ENGAGEMENT
# ============================================================

@router.get("/engagement")
async def get_engagement():
    """Resumen engagement: clientes en riesgo + top rachas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        riesgo = await conn.fetch("""
            SELECT cp.cliente_id, c.nombre, c.apellidos, cp.engagement_score,
                   cp.riesgo_churn, cp.engagement_tendencia, cp.racha_actual
            FROM om_cliente_perfil cp
            JOIN om_clientes c ON c.id = cp.cliente_id
            WHERE cp.tenant_id = $1 AND cp.riesgo_churn IN ('alto','critico')
            ORDER BY cp.engagement_score ASC LIMIT 10
        """, TENANT)
        rachas = await conn.fetch("""
            SELECT cp.cliente_id, c.nombre, cp.racha_actual, cp.engagement_score
            FROM om_cliente_perfil cp
            JOIN om_clientes c ON c.id = cp.cliente_id
            WHERE cp.tenant_id = $1 AND cp.racha_actual >= 4
            ORDER BY cp.racha_actual DESC LIMIT 5
        """, TENANT)
    return {
        "en_riesgo": [_row_to_dict(r) for r in riesgo],
        "top_rachas": [_row_to_dict(r) for r in rachas],
    }
