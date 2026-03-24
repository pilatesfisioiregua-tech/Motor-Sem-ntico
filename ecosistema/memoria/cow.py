"""Copy-on-Write — branching cognitivo sin coste de almacenamiento.

Inspirado en fork() de Linux: crear una "copia" de un estado
sin duplicar datos. Solo se copian los campos que cambian.

Permite experimentacion cognitiva:
  "que pasaria si cambio esta decision?"
  "como seria el diagnostico con estos datos diferentes?"
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

log = structlog.get_logger()
MADRID_TZ = ZoneInfo("Europe/Madrid")


@dataclass
class Branch:
    """Un branch cognitivo (fork del estado actual).

    No duplica datos — solo almacena las diferencias (overlay).
    Al leer: primero busca en el overlay, luego en el estado base.
    """
    id: str
    tenant_id: str
    nombre: str
    descripcion: str = ""
    base_ciclo: str = ""           # Ciclo del estado base
    overlay: dict = field(default_factory=dict)  # {tipo/clave: valor}
    creado: datetime = field(default_factory=lambda: datetime.now(MADRID_TZ))
    cerrado: bool = False
    resultado: Optional[str] = None  # "aceptado" | "descartado"

    def escribir(self, tipo: str, clave: str, valor: Any):
        """Escribe en el overlay (no toca el estado base)."""
        self.overlay[f"{tipo}/{clave}"] = valor

    def leer_overlay(self, tipo: str, clave: str) -> Optional[Any]:
        """Lee del overlay. None si no hay cambio vs base."""
        return self.overlay.get(f"{tipo}/{clave}")

    def tiene_cambios(self, tipo: str, clave: str) -> bool:
        return f"{tipo}/{clave}" in self.overlay

    @property
    def n_cambios(self) -> int:
        return len(self.overlay)


class GestorBranches:
    """Gestor de branches cognitivos (Copy-on-Write).

    Operaciones:
      - fork: crea branch desde estado actual
      - leer: busca en overlay, luego en base
      - merge: aplica overlay al estado base (requiere CR1)
      - descartar: cierra branch sin aplicar
      - diff: muestra cambios del branch vs base
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._branches: dict[str, Branch] = {}

    def fork(self, nombre: str, descripcion: str = "",
             ciclo: str = "") -> Branch:
        """Crea un nuevo branch (fork del estado actual)."""
        import secrets
        branch_id = f"br_{secrets.token_hex(4)}"

        branch = Branch(
            id=branch_id,
            tenant_id=self.tenant_id,
            nombre=nombre,
            descripcion=descripcion,
            base_ciclo=ciclo,
        )
        self._branches[branch_id] = branch

        log.info("cow.fork", branch=branch_id, nombre=nombre)
        return branch

    async def leer(self, branch_id: str, tipo: str, clave: str) -> Any:
        """Lee con CoW: overlay primero, base despues."""
        branch = self._branches.get(branch_id)
        if not branch:
            raise ValueError(f"Branch {branch_id} no existe")

        # 1. Buscar en overlay
        overlay_val = branch.leer_overlay(tipo, clave)
        if overlay_val is not None:
            return overlay_val

        # 2. Fallback a estado base (DB)
        from ecosistema.memoria.almacen import Almacen
        almacen = Almacen(self.tenant_id)
        return await almacen.leer(tipo, clave)

    def escribir(self, branch_id: str, tipo: str, clave: str, valor: Any):
        """Escribe solo en el overlay del branch."""
        branch = self._branches.get(branch_id)
        if not branch:
            raise ValueError(f"Branch {branch_id} no existe")
        if branch.cerrado:
            raise ValueError(f"Branch {branch_id} esta cerrado")
        branch.escribir(tipo, clave, valor)

    async def merge(self, branch_id: str) -> int:
        """Aplica overlay del branch al estado base.

        Esto es una operacion CR1 — el propietario decide.
        """
        branch = self._branches.get(branch_id)
        if not branch:
            raise ValueError(f"Branch {branch_id} no existe")

        from ecosistema.memoria.almacen import Almacen
        almacen = Almacen(self.tenant_id)

        n = 0
        for key, valor in branch.overlay.items():
            tipo, clave = key.split("/", 1)
            await almacen.escribir(tipo, clave, valor)
            n += 1

        branch.cerrado = True
        branch.resultado = "aceptado"

        log.info("cow.merge", branch=branch_id, cambios=n)
        return n

    def descartar(self, branch_id: str):
        """Descarta un branch sin aplicar cambios."""
        branch = self._branches.get(branch_id)
        if branch:
            branch.cerrado = True
            branch.resultado = "descartado"
            log.info("cow.descartado", branch=branch_id)

    def diff(self, branch_id: str) -> dict:
        """Muestra cambios del branch vs base."""
        branch = self._branches.get(branch_id)
        if not branch:
            return {}
        return {
            "branch": branch_id,
            "nombre": branch.nombre,
            "n_cambios": branch.n_cambios,
            "cambios": dict(branch.overlay),
        }

    def listar(self, incluir_cerrados: bool = False) -> list[dict]:
        """Lista branches activos."""
        return [
            {
                "id": b.id,
                "nombre": b.nombre,
                "cambios": b.n_cambios,
                "cerrado": b.cerrado,
                "resultado": b.resultado,
            }
            for b in self._branches.values()
            if incluir_cerrados or not b.cerrado
        ]
