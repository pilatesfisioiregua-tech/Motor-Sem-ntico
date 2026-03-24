"""Seeds comunes para nuevos tenants.

Datos base que todo organismo necesita al nacer.
Se ejecutan durante onboarding.
"""
from __future__ import annotations

from organismo.pizarras.pizarra import PizarraUnificada


async def seed_pizarra_interfaz(tenant_id: str, tema: str = "claro"):
    """Seed de preferencias UI por defecto."""
    pizarra = PizarraUnificada(tenant_id)
    await pizarra.escribir("interfaz", "tema", tema)
    await pizarra.escribir("interfaz", "layout", {
        "sidebar": True,
        "cockpit_cards": ["gomas", "diagnostico", "prescripciones", "coste"],
        "idioma": "es",
    })


async def seed_pizarra_temporal(tenant_id: str, ciclo: str = ""):
    """Seed de datos temporales iniciales."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    if not ciclo:
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    pizarra = PizarraUnificada(tenant_id)
    await pizarra.escribir("temporal", "ciclo_actual", {"ciclo": ciclo}, ciclo=ciclo)
    await pizarra.escribir("temporal", "fechas_clave", {
        "proximo_diagnostico": None,
        "proxima_revision": None,
    })
