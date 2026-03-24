"""Onboarding de nuevo tenant — crea N-exocortex.

Proceso:
  1. Registrar en ecosistema registry
  2. Crear schema/tablas en DB (MVP: schema compartido con tenant_id)
  3. Seed pizarras iniciales (dominio, modelos, identidad)
  4. Primer diagnostico ACD (datos vacios → E1 bajo)
  5. Escribir en pizarra cognitiva con recetas del sector
"""
from __future__ import annotations

import structlog
from typing import Optional

from organismo.pizarras.pizarra import PizarraUnificada

log = structlog.get_logger()

# Seeds por sector — recetas basicas que funcionan cross-dominio
SEEDS_SECTOR = {
    "wellness": {
        "F1": {"receta": "Sistema retencion post-baja con 3 contactos 48h/1sem/1mes",
               "efectividad_base": 0.65},
        "F2": {"receta": "Campaña referidos: descuento 15% primer mes por referido",
               "efectividad_base": 0.40},
        "F3": {"receta": "Encuesta NPS trimestral + accion correctiva si <7",
               "efectividad_base": 0.55},
    },
    "dental": {
        "F1": {"receta": "Recordatorio revision 6 meses + descuento fidelidad",
               "efectividad_base": 0.60},
        "F4": {"receta": "Dashboard financiero con alertas de rentabilidad por tratamiento",
               "efectividad_base": 0.50},
    },
    "saas": {
        "F1": {"receta": "Onboarding guiado 7 dias + health score semanal",
               "efectividad_base": 0.70},
        "F2": {"receta": "Free trial 14 dias con nurture email secuencia 5 emails",
               "efectividad_base": 0.35},
    },
    "default": {
        "F1": {"receta": "Contacto proactivo ante inactividad >30 dias",
               "efectividad_base": 0.50},
    },
}

# Modelos LLM por defecto por complejidad
MODELOS_DEFAULT = {
    "modelo_*_baja": "deepseek/deepseek-v3.2",
    "modelo_*_media": "openai/gpt-4o",
    "modelo_*_alta": "anthropic/claude-opus-4",
    "modelo_F5_alta": "anthropic/claude-opus-4",  # F5 siempre Opus
}


async def onboarding_tenant(
    tenant_id: str,
    nombre: str,
    sector: str = "default",
    propietario: str = "",
    ubicacion: str = "",
    telefono: str = "",
    email: str = "",
    presupuesto_llm_semanal: float = 5.0,
    autonomia: str = "notificar_4h",
) -> dict:
    """Ejecuta onboarding completo de un nuevo tenant.

    Returns:
        dict con resultado del onboarding y pasos ejecutados.
    """
    pizarra = PizarraUnificada(tenant_id)
    pasos = []

    # 1. Seed pizarra dominio
    await pizarra.escribir("dominio", "config", {
        "tenant_id": tenant_id,
        "nombre": nombre,
        "sector": sector,
        "propietario": propietario,
        "ubicacion": ubicacion,
        "telefono": telefono,
        "email": email,
        "presupuesto_llm_semanal": presupuesto_llm_semanal,
        "autonomia": autonomia,
        "timezone": "Europe/Madrid",
        "moneda": "EUR",
        "funciones_activas": ["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
    })
    pasos.append("dominio_seed")

    # 2. Seed pizarra modelos
    for clave, modelo in MODELOS_DEFAULT.items():
        await pizarra.escribir("modelos", clave, modelo)
    pasos.append("modelos_seed")

    # 3. Seed pizarra identidad (F5 basica)
    await pizarra.escribir("identidad", "esencia", {
        "nombre": nombre,
        "sector": sector,
        "propietario": propietario,
        "narrativa": f"{nombre} es un negocio de {sector}.",
        "valores": [],
        "anti_identidad": [],
    })
    pasos.append("identidad_seed")

    # 4. Seed pizarra cognitiva con recetas del sector
    recetas = SEEDS_SECTOR.get(sector, SEEDS_SECTOR["default"])
    for funcion, receta_data in recetas.items():
        await pizarra.escribir("cognitiva", f"receta_seed_{funcion}", receta_data)
    pasos.append("cognitiva_seed")

    # 5. Diagnostico ACD inicial (datos vacios → E1 bajo)
    await pizarra.escribir("cognitiva", "ultimo_diagnostico", {
        "estado": "E1_bajo",
        "scores": {
            f"F{i}": {"score": 3.0, "objetivo": 7.0, "lente": "salud"}
            for i in range(1, 8)
        },
        "nota": "Diagnostico inicial sin datos. Todos los gaps abiertos.",
    })
    pasos.append("diagnostico_inicial")

    # 6. Estado inicial del organismo
    await pizarra.escribir("estado", "organismo_estado", {
        "fase": "onboarding_completado",
        "gomas": {f"G{i}": "dormida" for i in range(1, 7)},
    })
    pasos.append("estado_inicial")

    # 7. Registrar en ecosistema
    try:
        from ecosistema.registry import EcosistemaRegistry, TenantConfig
        registry = EcosistemaRegistry()
        config = TenantConfig(
            tenant_id=tenant_id,
            nombre=nombre,
            sector=sector,
            propietario=propietario,
            ubicacion=ubicacion,
            presupuesto_llm_semanal=presupuesto_llm_semanal,
            autonomia=autonomia,
        )
        await registry.registrar_tenant(config)
        pasos.append("ecosistema_registrado")
    except Exception as e:
        log.warning("onboarding.ecosistema_skip", error=str(e)[:80])
        pasos.append("ecosistema_skip")

    log.info("onboarding.completado",
             tenant=tenant_id, sector=sector, pasos=len(pasos))

    return {
        "tenant_id": tenant_id,
        "nombre": nombre,
        "sector": sector,
        "pasos_ejecutados": pasos,
        "ok": True,
    }
