"""Manifiesto de App — metadata de un exocortex.

Cada app tiene un manifiesto que describe:
  - Que es (sector, nombre, propietario)
  - Que necesita (funciones activas, presupuesto, autonomia)
  - Que ofrece (capabilities, recetas publicables)

Analogia:
  Manifiesto   = Info.plist (iOS) / AndroidManifest.xml
  Capabilities = entitlements (permisos de la app)
  Requirements = dependencias (que servicios del OS necesita)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AppManifiesto:
    """Manifiesto de una app (exocortex)."""

    # Identidad
    app_id: str                  # Identificador unico (tenant_id)
    nombre: str                  # Nombre legible
    sector: str                  # wellness, dental, saas, etc.
    version: str = "1.0.0"

    # Propietario
    propietario: str = ""
    email: str = ""
    telefono: str = ""
    ubicacion: str = ""

    # Configuracion
    funciones_activas: list[str] = field(
        default_factory=lambda: ["F1", "F2", "F3", "F4", "F5", "F6", "F7"])
    presupuesto_semanal: float = 5.0
    autonomia: str = "notificar_4h"  # auto | notificar_4h | cr1
    timezone: str = "Europe/Madrid"
    moneda: str = "EUR"

    # Capabilities (que puede hacer esta app)
    capabilities: list[str] = field(default_factory=lambda: [
        "diagnostico_acd",       # Puede diagnosticar con ACD
        "prescripcion_basica",   # Puede generar prescripciones
        "telemetria",            # Reporta metricas al OS
    ])

    # Requirements (que necesita del OS)
    requirements: list[str] = field(default_factory=lambda: [
        "motor.pensar",          # Acceso al motor LLM
        "pizarra",               # Acceso a pizarras
        "bus_percepcion",        # Acceso a sensores
    ])

    def to_dict(self) -> dict:
        """Serializa a dict para guardar en pizarra dominio."""
        return {
            "app_id": self.app_id,
            "nombre": self.nombre,
            "sector": self.sector,
            "version": self.version,
            "propietario": self.propietario,
            "email": self.email,
            "telefono": self.telefono,
            "ubicacion": self.ubicacion,
            "funciones_activas": self.funciones_activas,
            "presupuesto_llm_semanal": self.presupuesto_semanal,
            "autonomia": self.autonomia,
            "timezone": self.timezone,
            "moneda": self.moneda,
            "capabilities": self.capabilities,
            "requirements": self.requirements,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppManifiesto":
        """Deserializa desde dict de pizarra."""
        return cls(
            app_id=data.get("app_id", data.get("tenant_id", "")),
            nombre=data.get("nombre", ""),
            sector=data.get("sector", "general"),
            version=data.get("version", "1.0.0"),
            propietario=data.get("propietario", ""),
            email=data.get("email", ""),
            telefono=data.get("telefono", ""),
            ubicacion=data.get("ubicacion", ""),
            funciones_activas=data.get("funciones_activas",
                                       ["F1", "F2", "F3", "F4", "F5", "F6", "F7"]),
            presupuesto_semanal=data.get("presupuesto_llm_semanal", 5.0),
            autonomia=data.get("autonomia", "notificar_4h"),
            timezone=data.get("timezone", "Europe/Madrid"),
            moneda=data.get("moneda", "EUR"),
            capabilities=data.get("capabilities", []),
            requirements=data.get("requirements", []),
        )
