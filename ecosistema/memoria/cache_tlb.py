"""TLB + Cache LFU — capa de memoria rapida (Linux MM + Redis pattern).

TLB (Translation Lookaside Buffer):
  Cache en memoria Python de las claves mas accedidas de om_pizarra.
  Evita ir a PostgreSQL para datos calientes.

LFU (Least Frequently Used):
  Politica de eviccion que mantiene los datos mas accedidos.
  Combina frecuencia + recencia para decidir que evictar.
"""
from __future__ import annotations

import time
import structlog
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import OrderedDict

log = structlog.get_logger()


@dataclass
class EntradaCache:
    """Una entrada en el cache TLB."""
    clave: str          # tenant:tipo:clave
    valor: Any
    frecuencia: int = 1
    ultimo_acceso: float = field(default_factory=time.time)
    creado: float = field(default_factory=time.time)
    dirty: bool = False  # True si fue modificado localmente


class CacheTLB:
    """Cache LFU en memoria — TLB del OS cognitivo.

    Politica de eviccion: LFU con aging.
    Cuando el cache esta lleno y llega un nuevo dato,
    se evicta el dato con menor (frecuencia * recencia_factor).

    Thread-safe? No (Python GIL + asyncio single-thread lo hace innecesario).
    """

    def __init__(self, max_entradas: int = 1000, ttl_segundos: float = 300):
        self.max_entradas = max_entradas
        self.ttl = ttl_segundos
        self._cache: dict[str, EntradaCache] = {}
        self._hits: int = 0
        self._misses: int = 0

    def _key(self, tenant_id: str, tipo: str, clave: str) -> str:
        return f"{tenant_id}:{tipo}:{clave}"

    def get(self, tenant_id: str, tipo: str, clave: str) -> Optional[Any]:
        """Lee del cache. Retorna None si miss."""
        k = self._key(tenant_id, tipo, clave)
        entry = self._cache.get(k)

        if entry is None:
            self._misses += 1
            return None

        # TTL check
        if time.time() - entry.creado > self.ttl:
            del self._cache[k]
            self._misses += 1
            return None

        # Hit: actualizar frecuencia y recencia
        entry.frecuencia += 1
        entry.ultimo_acceso = time.time()
        self._hits += 1
        return entry.valor

    def put(self, tenant_id: str, tipo: str, clave: str,
            valor: Any, dirty: bool = False):
        """Escribe en el cache. Evicta si necesario."""
        k = self._key(tenant_id, tipo, clave)

        if k in self._cache:
            self._cache[k].valor = valor
            self._cache[k].frecuencia += 1
            self._cache[k].ultimo_acceso = time.time()
            self._cache[k].dirty = dirty
            return

        # Evictar si lleno
        if len(self._cache) >= self.max_entradas:
            self._evictar()

        self._cache[k] = EntradaCache(
            clave=k, valor=valor, dirty=dirty)

    def invalidar(self, tenant_id: str, tipo: str, clave: str):
        """Invalida una entrada (otro agente la modifico)."""
        k = self._key(tenant_id, tipo, clave)
        self._cache.pop(k, None)

    def invalidar_tipo(self, tenant_id: str, tipo: str):
        """Invalida todas las entradas de un tipo."""
        prefix = f"{tenant_id}:{tipo}:"
        keys_to_del = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_del:
            del self._cache[k]

    def flush_dirty(self) -> list[EntradaCache]:
        """Retorna entradas dirty para write-back a DB."""
        dirty = [e for e in self._cache.values() if e.dirty]
        for e in dirty:
            e.dirty = False
        return dirty

    def _evictar(self):
        """Evicta la entrada con menor score LFU."""
        if not self._cache:
            return

        ahora = time.time()
        peor_k = None
        peor_score = float("inf")

        for k, entry in self._cache.items():
            # Score = frecuencia * recencia_factor
            # recencia_factor decae con el tiempo
            edad = ahora - entry.ultimo_acceso
            recencia = 1.0 / (1.0 + edad / 60.0)  # decae por minuto
            score = entry.frecuencia * recencia

            if score < peor_score:
                peor_score = score
                peor_k = k

        if peor_k:
            del self._cache[peor_k]

    def clear(self):
        """Limpia todo el cache."""
        self._cache.clear()

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "entradas": len(self._cache),
            "max": self.max_entradas,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0,
            "dirty": sum(1 for e in self._cache.values() if e.dirty),
        }


# Instancia global (singleton)
_tlb: Optional[CacheTLB] = None


def get_tlb(max_entradas: int = 1000) -> CacheTLB:
    global _tlb
    if _tlb is None:
        _tlb = CacheTLB(max_entradas=max_entradas)
    return _tlb
