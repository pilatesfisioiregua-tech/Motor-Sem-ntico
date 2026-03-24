"""Capabilities tipadas — seguridad matematica del kernel (seL4 + Zircon).

Cada agente accede a recursos via capabilities infalsificables:
  - Tipadas: Capability[Pizarra, {leer, escribir}]
  - Atenuables: reducir permisos al delegar
  - Revocables: eliminar acceso inmediatamente
  - Auditables: toda operacion deja traza

Elimina el 'confused deputy': un agente NO puede construir una referencia
a un recurso que no le fue explicitamente concedido.
"""
from __future__ import annotations

import hashlib
import secrets
import structlog
from dataclasses import dataclass, field
from enum import Flag, auto
from typing import Optional

log = structlog.get_logger()


class Permiso(Flag):
    """Permisos atomicos sobre un recurso."""
    LEER = auto()
    ESCRIBIR = auto()
    EJECUTAR = auto()
    DELEGAR = auto()      # Puede pasar la capability a otro agente
    NOTIFICAR = auto()    # Puede activar LISTEN/NOTIFY

    # Combinaciones comunes
    LECTURA = LEER
    ESCRITURA = LEER | ESCRIBIR
    COMPLETO = LEER | ESCRIBIR | EJECUTAR | DELEGAR | NOTIFICAR


class TipoRecurso:
    """Tipos de recurso del kernel."""
    PIZARRA = "pizarra"
    MOTOR = "motor"
    BUS = "bus"
    GOMA = "goma"
    AGENTE = "agente"
    ECOSISTEMA = "ecosistema"


@dataclass(frozen=True)
class Capability:
    """Token de acceso infalsificable a un recurso.

    Una vez creada, no se puede modificar (frozen).
    Solo el CapabilityManager puede crear, atenuar y revocar.

    Atributos:
      - token: hash unico infalsificable
      - titular: quien posee esta capability (identidad F5)
      - recurso: a que recurso da acceso
      - tipo_recurso: tipo del recurso (pizarra, motor, bus, etc.)
      - permisos: que operaciones permite
      - scope: restriccion adicional (tenant_id, tipo_pizarra, funcion)
      - delegable: si se puede pasar a otro agente
    """
    token: str
    titular: str                     # identidad del agente
    recurso: str                     # identificador del recurso
    tipo_recurso: str                # TipoRecurso
    permisos: Permiso
    scope: dict = field(default_factory=dict)
    delegable: bool = False
    origen: str = ""                 # quien creo esta capability
    parent_token: Optional[str] = None  # capability de la que deriva

    def permite(self, permiso: Permiso) -> bool:
        """Verifica si esta capability incluye el permiso solicitado."""
        return permiso in self.permisos

    def cubre_scope(self, **kwargs) -> bool:
        """Verifica si el scope de la capability cubre los parametros."""
        for key, valor in kwargs.items():
            restriccion = self.scope.get(key)
            if restriccion is not None and restriccion != valor and restriccion != "*":
                return False
        return True


class CapabilityManager:
    """Gestor central de capabilities del kernel.

    Es el unico componente que puede crear, atenuar y revocar capabilities.
    Mantiene un registro de todas las capabilities activas.
    """

    def __init__(self):
        self._capabilities: dict[str, Capability] = {}
        self._revocadas: set[str] = set()

    def crear(self, titular: str, recurso: str, tipo_recurso: str,
              permisos: Permiso, scope: dict = None,
              delegable: bool = False) -> Capability:
        """Crea una nueva capability."""
        token = self._generar_token(titular, recurso)
        cap = Capability(
            token=token,
            titular=titular,
            recurso=recurso,
            tipo_recurso=tipo_recurso,
            permisos=permisos,
            scope=scope or {},
            delegable=delegable,
            origen="kernel",
        )
        self._capabilities[token] = cap
        log.debug("capability.creada",
                  titular=titular, recurso=recurso,
                  permisos=str(permisos))
        return cap

    def atenuar(self, cap: Capability, nuevos_permisos: Permiso,
                nuevo_titular: str = "") -> Optional[Capability]:
        """Atenua una capability (reduce permisos) para delegarla.

        Solo puede REDUCIR permisos, nunca ampliar.
        Requiere que la capability original sea delegable.
        """
        if not cap.delegable:
            log.warning("capability.no_delegable", token=cap.token[:8])
            return None

        if cap.token in self._revocadas:
            log.warning("capability.revocada", token=cap.token[:8])
            return None

        # Solo reducir, nunca ampliar
        permisos_resultantes = cap.permisos & nuevos_permisos

        nueva = Capability(
            token=self._generar_token(nuevo_titular or cap.titular, cap.recurso),
            titular=nuevo_titular or cap.titular,
            recurso=cap.recurso,
            tipo_recurso=cap.tipo_recurso,
            permisos=permisos_resultantes,
            scope=cap.scope,
            delegable=False,  # Atenuada no es delegable por defecto
            origen=cap.titular,
            parent_token=cap.token,
        )
        self._capabilities[nueva.token] = nueva
        return nueva

    def revocar(self, token: str) -> bool:
        """Revoca una capability y todas las derivadas."""
        if token not in self._capabilities:
            return False

        self._revocadas.add(token)

        # Revocar cascada: todas las capabilities derivadas
        for t, cap in list(self._capabilities.items()):
            if cap.parent_token == token:
                self._revocadas.add(t)

        log.info("capability.revocada", token=token[:8])
        return True

    def verificar(self, cap: Capability, permiso: Permiso,
                  **scope_kwargs) -> bool:
        """Verifica si una capability es valida y cubre la operacion.

        Retorna True solo si:
          1. La capability no esta revocada
          2. El permiso esta incluido
          3. El scope cubre los parametros
        """
        if cap.token in self._revocadas:
            return False
        if not cap.permite(permiso):
            return False
        if not cap.cubre_scope(**scope_kwargs):
            return False
        return True

    def listar_por_titular(self, titular: str) -> list[Capability]:
        """Lista todas las capabilities activas de un titular."""
        return [
            cap for cap in self._capabilities.values()
            if cap.titular == titular and cap.token not in self._revocadas
        ]

    def _generar_token(self, titular: str, recurso: str) -> str:
        """Genera token unico infalsificable."""
        seed = f"{titular}:{recurso}:{secrets.token_hex(16)}"
        return hashlib.sha256(seed.encode()).hexdigest()[:32]

    @property
    def stats(self) -> dict:
        activas = len(self._capabilities) - len(self._revocadas)
        return {
            "total": len(self._capabilities),
            "activas": activas,
            "revocadas": len(self._revocadas),
        }
