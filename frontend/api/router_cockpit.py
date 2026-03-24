"""Router Cockpit — API REST para el frontend del organismo.

Endpoints:
  GET /cockpit/estado       — Estado completo del organismo
  GET /cockpit/gomas        — Estado de las 6 gomas + META
  GET /cockpit/diagnostico  — Ultimo diagnostico ACD
  GET /cockpit/prescripciones — Prescripciones activas
  GET /cockpit/metricas     — Metricas de coste y rendimiento
  POST /cockpit/frenar      — CR1: frena el circuito (solo propietario)
  POST /cockpit/reanudar    — CR1: reanuda el circuito
  POST /cockpit/ciclo       — Trigger manual de ciclo enjambre
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from organismo.pizarras.pizarra import PizarraUnificada
from tenant.tenant_context import get_tenant_id

log = structlog.get_logger()
router = APIRouter(prefix="/cockpit", tags=["cockpit"])


def _get_pizarra() -> PizarraUnificada:
    return PizarraUnificada(get_tenant_id())


@router.get("/estado")
async def estado_organismo():
    """Estado completo del organismo: gomas + diagnostico + metricas."""
    tenant_id = get_tenant_id()
    pizarra = PizarraUnificada(tenant_id)

    estado = await pizarra.leer_estado()
    cognitiva = await pizarra.leer_tipo("cognitiva")
    temporal = await pizarra.leer_tipo("temporal")

    return {
        "tenant_id": tenant_id,
        "estado": estado,
        "cognitiva_resumen": {
            k: v for k, v in cognitiva.items()
            if k.startswith("ultimo_") or k.startswith("receta_")
        } if cognitiva else {},
        "temporal": temporal,
    }


@router.get("/gomas")
async def estado_gomas():
    """Estado de las 6 gomas + META."""
    pizarra = PizarraUnificada(get_tenant_id())
    estado = await pizarra.leer("estado", "organismo_estado")

    if not estado:
        return {"gomas": {f"G{i}": "dormida" for i in range(1, 7)}, "meta": "dormida"}

    gomas = estado.get("gomas", {})
    return {"gomas": gomas}


@router.get("/diagnostico")
async def ultimo_diagnostico():
    """Ultimo diagnostico ACD."""
    pizarra = PizarraUnificada(get_tenant_id())
    diag = await pizarra.leer("cognitiva", "ultimo_diagnostico")
    return {"diagnostico": diag or {"estado": "sin_diagnostico"}}


@router.get("/prescripciones")
async def prescripciones_activas():
    """Prescripciones activas del enjambre."""
    pizarra = PizarraUnificada(get_tenant_id())
    cognitiva = await pizarra.leer_tipo("cognitiva")

    prescripciones = {
        k: v for k, v in cognitiva.items()
        if k.startswith("prescripcion_") or k.startswith("receta_")
    }
    return {"prescripciones": prescripciones}


@router.get("/metricas")
async def metricas():
    """Metricas de coste y rendimiento."""
    pizarra = PizarraUnificada(get_tenant_id())
    evolucion = await pizarra.leer_tipo("evolucion")
    enjambre = await pizarra.leer("estado", "enjambre_estado")
    director = await pizarra.leer("estado", "ultimo_ciclo_director")

    from motor.pensar import presupuesto_restante, _presupuesto_ciclo
    return {
        "presupuesto": {
            "gastado": round(_presupuesto_ciclo, 4),
            "restante": round(presupuesto_restante(), 4),
        },
        "enjambre": enjambre or {},
        "director": director or {},
        "evolucion": evolucion,
    }


@router.post("/frenar")
async def frenar_circuito():
    """CR1: Frena todo el circuito. Solo propietario."""
    tenant_id = get_tenant_id()
    pizarra = PizarraUnificada(tenant_id)

    await pizarra.escribir(
        "estado", "circuito_frenado",
        {"frenado": True, "motivo": "CR1_manual"},
        notificar=True,
    )

    log.warning("cockpit.CR1_frenar", tenant=tenant_id)
    return {"ok": True, "estado": "frenado"}


@router.post("/reanudar")
async def reanudar_circuito():
    """CR1: Reanuda el circuito."""
    tenant_id = get_tenant_id()
    pizarra = PizarraUnificada(tenant_id)

    await pizarra.escribir(
        "estado", "circuito_frenado",
        {"frenado": False, "motivo": "CR1_reanudado"},
        notificar=True,
    )

    log.info("cockpit.CR1_reanudar", tenant=tenant_id)
    return {"ok": True, "estado": "reanudado"}


@router.post("/ciclo")
async def trigger_ciclo():
    """Trigger manual de un ciclo del enjambre."""
    tenant_id = get_tenant_id()

    from organismo.ejecutiva.cron_organismo import CronOrganismo
    cron = CronOrganismo(tenant_id)

    try:
        resultado = await cron.ejecutar_ciclo_rapido()
        return {
            "ok": True,
            "señales": len(resultado) if isinstance(resultado, list) else 0,
        }
    except Exception as e:
        log.error("cockpit.ciclo_error", error=str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:200])


@router.get("/identidad")
async def identidad_f5():
    """Identidad F5 del tenant."""
    pizarra = PizarraUnificada(get_tenant_id())
    return {"identidad": await pizarra.leer_identidad()}
