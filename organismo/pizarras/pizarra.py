"""Pizarra unificada — espacio compartido de lectura/escritura (P64).

8 tipos de pizarra en tabla genérica om_pizarra:
  estado, cognitiva, dominio, temporal, modelos, evolucion, interfaz, identidad

CQRS: los agentes LEEN de pizarras (PULL, no PUSH).
LISTEN/NOTIFY: cambios urgentes se propagan vía PostgreSQL channels.
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

log = structlog.get_logger()
MADRID_TZ = ZoneInfo("Europe/Madrid")

TIPOS_PIZARRA = (
    "estado",       # Estado actual del organismo (gomas, alertas, métricas)
    "cognitiva",    # Repertorio INT×P×R activo, último diagnóstico ACD
    "dominio",      # Config del tenant (timezone, moneda, funciones activas)
    "temporal",     # Ciclo actual, fechas clave, calendario
    "modelos",      # Qué modelo LLM usar por función/complejidad
    "evolucion",    # Histórico: scores, deltas, tendencias
    "interfaz",     # Preferencias UI del tenant
    "identidad",    # F5: esencia, narrativa, valores, anti-identidad
)


@dataclass
class EntradaPizarra:
    """Una entrada en la pizarra unificada."""
    tenant_id: str
    tipo: str               # Uno de TIPOS_PIZARRA
    clave: str              # Ej: "ultimo_diagnostico", "modelo_F3_alta"
    valor: Any              # JSONB
    ciclo: str = ""         # Ej: "W13-2026"
    ttl_horas: int = 0      # 0 = sin expiración
    timestamp: datetime = field(default_factory=lambda: datetime.now(MADRID_TZ))

    def __post_init__(self):
        if self.tipo not in TIPOS_PIZARRA:
            log.warning("pizarra_tipo_desconocido", tipo=self.tipo)


class PizarraUnificada:
    """Cliente de lectura/escritura para la pizarra genérica.

    Cada organismo tiene su propia instancia con tenant_id fijo.
    Patrón PULL (P63): los agentes leen cuando quieren, no reciben push.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    async def _get_pool(self):
        from src.db.client import get_pool
        return await get_pool()

    async def leer(self, tipo: str, clave: str) -> Any:
        """Lee un valor de la pizarra. Devuelve None si no existe."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT valor FROM om_pizarra
                    WHERE tenant_id = $1 AND tipo = $2 AND clave = $3
                      AND (ttl_horas = 0 OR created_at + make_interval(hours => ttl_horas) > now())
                    ORDER BY created_at DESC LIMIT 1
                """, self.tenant_id, tipo, clave)
                if row:
                    return json.loads(row["valor"]) if isinstance(row["valor"], str) else row["valor"]
        except Exception as e:
            log.debug("pizarra.leer_error", tipo=tipo, clave=clave, error=str(e)[:80])
        return None

    async def leer_tipo(self, tipo: str) -> dict[str, Any]:
        """Lee todas las entradas de un tipo de pizarra."""
        resultado = {}
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT ON (clave) clave, valor
                    FROM om_pizarra
                    WHERE tenant_id = $1 AND tipo = $2
                      AND (ttl_horas = 0 OR created_at + make_interval(hours => ttl_horas) > now())
                    ORDER BY clave, created_at DESC
                """, self.tenant_id, tipo)
                for row in rows:
                    val = row["valor"]
                    resultado[row["clave"]] = json.loads(val) if isinstance(val, str) else val
        except Exception as e:
            log.debug("pizarra.leer_tipo_error", tipo=tipo, error=str(e)[:80])
        return resultado

    async def escribir(self, tipo: str, clave: str, valor: Any,
                       ciclo: str = "", ttl_horas: int = 0,
                       notificar: bool = False) -> None:
        """Escribe un valor en la pizarra.

        Args:
            notificar: Si True, envía NOTIFY por el channel pg_pizarra_{tenant_id}
        """
        pool = await self._get_pool()
        valor_json = json.dumps(valor) if not isinstance(valor, str) else valor

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_pizarra (tenant_id, tipo, clave, valor, ciclo, ttl_horas)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
            """, self.tenant_id, tipo, clave, valor_json, ciclo, ttl_horas)

            if notificar:
                payload = json.dumps({"tipo": tipo, "clave": clave})
                await conn.execute(
                    f"NOTIFY pg_pizarra_{self.tenant_id.replace('-', '_')}, $1",
                    payload)

        log.debug("pizarra.escrita", tipo=tipo, clave=clave,
                  tenant=self.tenant_id, notificar=notificar)

    async def leer_modelo(self, funcion: str = "*", lente: str = None,
                           complejidad: str = "media") -> Optional[str]:
        """Atajo: lee modelo LLM asignado desde pizarra modelos."""
        clave = f"modelo_{funcion}_{complejidad}"
        return await self.leer("modelos", clave)

    async def leer_identidad(self) -> dict:
        """Atajo: lee la identidad F5 completa del tenant."""
        return await self.leer_tipo("identidad") or {}

    async def leer_estado(self) -> dict:
        """Atajo: lee el estado actual del organismo."""
        return await self.leer_tipo("estado") or {}
