"""Almacen unificado — wrapper de DB como filesystem del OS.

El Almacen es la capa de abstraccion entre el OS y PostgreSQL.
Cada app (exocortex) accede a su espacio de memoria via tenant_id.

Analogia:
  Almacen        = VFS (Virtual File System) del OS
  om_pizarra     = ext4 (filesystem principal)
  tenant_id      = /home/{user}/ (directorio del usuario)
  tipo pizarra   = subdirectorio (/estado, /cognitiva, /modelos, etc.)
  clave          = fichero individual
  valor (JSONB)  = contenido del fichero
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

log = structlog.get_logger()
MADRID_TZ = ZoneInfo("Europe/Madrid")


@dataclass
class ArchivoMemoria:
    """Un archivo en el filesystem del OS."""
    tenant_id: str
    tipo: str          # directorio: estado|cognitiva|dominio|temporal|modelos|evolucion|interfaz|identidad
    clave: str         # nombre del archivo
    valor: Any         # contenido (JSONB)
    ciclo: str = ""    # version/snapshot
    ttl_horas: int = 0
    origen: str = "sistema"
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(MADRID_TZ)


class Almacen:
    """Virtual File System del OS — acceso unificado a toda la memoria.

    Cada app accede SOLO a su espacio (/home/{tenant_id}/).
    El OS puede acceder a la telemetria anonimizada de todas las apps.
    """

    def __init__(self, tenant_id: str = "os"):
        self.tenant_id = tenant_id

    async def _get_pool(self):
        from src.db.client import get_pool
        return await get_pool()

    # ==========================================================
    # FILESYSTEM BASICO (pizarra)
    # ==========================================================

    async def leer(self, tipo: str, clave: str) -> Any:
        """Lee un archivo de la memoria del tenant."""
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
            log.debug("memoria.leer_error", tipo=tipo, clave=clave, error=str(e)[:80])
        return None

    async def escribir(self, tipo: str, clave: str, valor: Any,
                       ciclo: str = "", ttl_horas: int = 0,
                       notificar: bool = False) -> None:
        """Escribe un archivo en la memoria del tenant."""
        pool = await self._get_pool()
        valor_json = json.dumps(valor) if not isinstance(valor, str) else valor

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_pizarra (tenant_id, tipo, clave, valor, ciclo, ttl_horas)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                ON CONFLICT (tenant_id, tipo, clave, ciclo)
                DO UPDATE SET valor = $4::jsonb, updated_at = now()
            """, self.tenant_id, tipo, clave, valor_json, ciclo, ttl_horas)

            if notificar:
                payload = json.dumps({"tipo": tipo, "clave": clave})
                await conn.execute(
                    f"NOTIFY pg_pizarra_{self.tenant_id.replace('-', '_')}, $1",
                    payload)

    async def listar(self, tipo: str) -> dict[str, Any]:
        """Lista todos los archivos de un directorio (tipo)."""
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
            log.debug("memoria.listar_error", tipo=tipo, error=str(e)[:80])
        return resultado

    async def borrar(self, tipo: str, clave: str) -> bool:
        """Borra un archivo de la memoria."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM om_pizarra
                    WHERE tenant_id = $1 AND tipo = $2 AND clave = $3
                """, self.tenant_id, tipo, clave)
                return "DELETE" in result
        except Exception as e:
            log.warning("memoria.borrar_error", error=str(e)[:80])
            return False

    # ==========================================================
    # CACHE (pagina de memoria rapida)
    # ==========================================================

    async def cache_leer(self, prompt_hash: str, modelo: str) -> Optional[str]:
        """Lee del cache LLM."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, respuesta FROM om_pizarra_cache_llm
                    WHERE prompt_hash = $1 AND modelo = $2 AND expires_at > now()
                    ORDER BY created_at DESC LIMIT 1
                """, prompt_hash, modelo)
                if row:
                    await conn.execute(
                        "UPDATE om_pizarra_cache_llm SET hits = hits + 1 WHERE id = $1",
                        row["id"])
                    return row["respuesta"]
        except Exception:
            pass
        return None

    # ==========================================================
    # LOGS DEL SISTEMA (telemetria)
    # ==========================================================

    async def log_telemetria(self, funcion: str, modelo: str,
                              tokens_in: int, tokens_out: int,
                              coste: float, tiempo_ms: int,
                              cache_hit: bool, ciclo: str) -> None:
        """Registra una entrada en los logs del sistema."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_motor_telemetria
                        (tenant_id, funcion, modelo, tokens_input, tokens_output,
                         coste_usd, tiempo_ms, cache_hit, ciclo)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, self.tenant_id, funcion, modelo, tokens_in, tokens_out,
                    coste, tiempo_ms, cache_hit, ciclo)
        except Exception as e:
            log.debug("memoria.telemetria_error", error=str(e)[:80])

    # ==========================================================
    # SNAPSHOTS (backups)
    # ==========================================================

    async def snapshot(self, ciclo: str) -> int:
        """Crea un snapshot completo de la memoria del tenant."""
        datos = {}
        for tipo in ("estado", "cognitiva", "dominio", "temporal",
                     "modelos", "evolucion", "interfaz", "identidad"):
            datos[tipo] = await self.listar(tipo)

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_pizarra_snapshot (tenant_id, ciclo, snapshot, n_entradas)
                VALUES ($1, $2, $3::jsonb, $4)
            """, self.tenant_id, ciclo, json.dumps(datos),
                sum(len(v) for v in datos.values()))

        n = sum(len(v) for v in datos.values())
        log.info("memoria.snapshot", tenant=self.tenant_id, ciclo=ciclo, n=n)
        return n

    # ==========================================================
    # ACCESO OS (cross-tenant, solo para el OS)
    # ==========================================================

    async def leer_todos_tenants(self) -> list[str]:
        """[Solo OS] Lista todos los tenant_id registrados."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT tenant_id FROM om_pizarra
                    WHERE tipo = 'dominio' AND clave = 'config'
                """)
                return [r["tenant_id"] for r in rows]
        except Exception as e:
            log.warning("memoria.tenants_error", error=str(e)[:80])
            return []

    async def leer_telemetria_global(self) -> list[dict]:
        """[Solo OS] Lee telemetria anonimizada de todas las apps."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT tenant_id,
                           SUM(coste_usd) as coste_total,
                           COUNT(*) as n_llamadas,
                           AVG(tiempo_ms) as tiempo_promedio,
                           SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::float
                             / NULLIF(COUNT(*), 0) as cache_rate
                    FROM om_motor_telemetria
                    WHERE created_at > now() - interval '7 days'
                    GROUP BY tenant_id
                """)
                return [dict(r) for r in rows]
        except Exception as e:
            log.warning("memoria.telemetria_global_error", error=str(e)[:80])
            return []
