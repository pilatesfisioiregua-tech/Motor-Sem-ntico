"""Router Admin — endpoints de administracion del ecosistema.

Solo accesible por admin. Gestiona tenants y ecosistema.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

log = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["admin"])


class OnboardingRequest(BaseModel):
    tenant_id: str
    nombre: str
    sector: str = "default"
    propietario: str = ""
    ubicacion: str = ""
    telefono: str = ""
    email: str = ""
    presupuesto_llm_semanal: float = 5.0
    autonomia: str = "notificar_4h"


@router.post("/onboarding")
async def onboarding_nuevo_tenant(req: OnboardingRequest):
    """Crea un nuevo exocortex (tenant) en el ecosistema."""
    from tenant.onboarding import onboarding_tenant

    try:
        resultado = await onboarding_tenant(
            tenant_id=req.tenant_id,
            nombre=req.nombre,
            sector=req.sector,
            propietario=req.propietario,
            ubicacion=req.ubicacion,
            telefono=req.telefono,
            email=req.email,
            presupuesto_llm_semanal=req.presupuesto_llm_semanal,
            autonomia=req.autonomia,
        )
        return resultado
    except Exception as e:
        log.error("admin.onboarding_error", error=str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:200])


@router.get("/tenants")
async def listar_tenants():
    """Lista todos los tenants activos."""
    from organismo.pizarras.pizarra import PizarraUnificada

    # Leer todos los tenants desde pizarra dominio
    # MVP: query directa ya que registry necesita pool
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT tenant_id, valor
                FROM om_pizarra
                WHERE tipo = 'dominio' AND clave = 'config'
            """)
        import json
        tenants = []
        for r in rows:
            val = json.loads(r["valor"]) if isinstance(r["valor"], str) else r["valor"]
            tenants.append({
                "tenant_id": r["tenant_id"],
                "nombre": val.get("nombre", r["tenant_id"]),
                "sector": val.get("sector", "?"),
            })
        return {"tenants": tenants}
    except Exception as e:
        return {"tenants": [], "error": str(e)[:100]}


@router.get("/ecosistema/telemetria")
async def telemetria_ecosistema():
    """Telemetria anonimizada de todos los organismos."""
    try:
        from src.db.client import get_pool
        from ecosistema.registry import EcosistemaRegistry
        pool = await get_pool()
        registry = EcosistemaRegistry(pool)
        await registry.cargar_tenants()

        telemetrias = []
        for t in registry.listar_tenants():
            tel = await registry.obtener_telemetria(t.tenant_id)
            if tel:
                telemetrias.append({
                    "tenant_id": tel.tenant_id,
                    "sector": tel.sector,
                    "estado": tel.estado_diagnostico,
                    "gaps": tel.gaps,
                    "coste_semanal": tel.coste_llm_semanal,
                })
        return {"organismos": telemetrias}
    except Exception as e:
        return {"organismos": [], "error": str(e)[:100]}
