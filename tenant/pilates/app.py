"""App Pilates — configuracion completa como App del OS.

Conecta:
  - AppManifiesto (identidad de la app)
  - Sandbox + Entitlements (permisos)
  - Sensores F1-F7 (percepcion del negocio)
  - System prompts AF1-AF7 (como piensa cada agente)
  - Activation Events (cuando se activa)
  - Hooks (extensiones)
"""
from __future__ import annotations

from ecosistema.apps.manifiesto import AppManifiesto
from ecosistema.apps.sandbox import (
    Sandbox, Entitlement, ReglasActivacion, DurableObject
)

TENANT_ID = "authentic_pilates"

# ============================================================
# MANIFIESTO
# ============================================================

MANIFIESTO = AppManifiesto(
    app_id=TENANT_ID,
    nombre="Authentic Pilates",
    sector="wellness",
    version="2.1.0",
    propietario="Jesus Fernandez",
    email="pilatesfisioiregua@gmail.com",
    telefono="34607466631",
    ubicacion="Albelda de Iregua, La Rioja",
    funciones_activas=["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
    presupuesto_semanal=5.0,
    autonomia="notificar_4h",
    timezone="Europe/Madrid",
    moneda="EUR",
    capabilities=[
        "diagnostico_acd",
        "prescripcion_basica",
        "prescripcion_avanzada",
        "telemetria",
        "whatsapp_bidireccional",
        "sequito_24_asesores",
        "portal_cliente",
        "portal_publico",
        "contabilidad_fusionada",
        "redsys_pagos",
    ],
    requirements=[
        "motor.pensar",
        "pizarra",
        "bus_percepcion",
        "cron",
        "api_externa",
        "webhook",
    ],
)


# ============================================================
# SANDBOX
# ============================================================

SANDBOX = Sandbox(
    app_id=TENANT_ID,
    tenant_id=TENANT_ID,
    entitlements=Entitlement.COMPLETO,  # Todo menos CR1_FRENAR
    tipos_pizarra_permitidos=[
        "estado", "cognitiva", "dominio", "temporal",
        "modelos", "evolucion", "interfaz", "identidad",
    ],
    apis_externas_permitidas=[
        "openrouter.ai",       # LLM
        "api.whatsapp.com",    # WhatsApp Business
        "api.redsys.es",       # Pagos TPV
    ],
)


# ============================================================
# ACTIVATION EVENTS
# ============================================================

ACTIVACION = ReglasActivacion(
    app_id=TENANT_ID,
    eventos=[
        {"tipo": "onSchedule", "valor": "lunes-06:00"},    # Briefing semanal
        {"tipo": "onSchedule", "valor": "diario-07:00"},    # Check rapido diario
        {"tipo": "onEvent", "valor": "nuevo_cliente"},
        {"tipo": "onEvent", "valor": "cancelacion"},
        {"tipo": "onEvent", "valor": "pago_recibido"},
        {"tipo": "onEvent", "valor": "whatsapp_entrante"},
        {"tipo": "onTopic", "valor": "pilates"},
        {"tipo": "onTopic", "valor": "clientes"},
        {"tipo": "onTopic", "valor": "sesiones"},
        {"tipo": "onMention", "valor": "@pilates"},
    ],
)


# ============================================================
# DURABLE OBJECT
# ============================================================

DURABLE_OBJECT = DurableObject(
    id=f"do_{TENANT_ID}",
    tenant_id=TENANT_ID,
    app_id="wellness_pilates",
)
