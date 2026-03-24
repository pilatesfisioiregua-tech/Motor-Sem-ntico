"""eBPF cognitivo — probes programables en checkpoints del kernel.

Inspirado en eBPF de Linux: programas verificados que se ejecutan
en puntos clave del kernel sin poder crashearlo.

Cada probe:
  - Se registra en un checkpoint (pre_compose, post_verify, on_error, etc.)
  - Es una funcion pura (no puede modificar estado externo)
  - Es verificada antes de deployment (tipo, no loops, bounded)
  - Puede observar, filtrar, o alertar, pero NUNCA bloquear el kernel

Uso:
  probes.registrar("post_pensar", mi_probe)
  probes.registrar("pre_compose", filtro_seguridad)
"""
from __future__ import annotations

import structlog
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

log = structlog.get_logger()

# Checkpoints disponibles en el kernel
CHECKPOINTS = (
    "pre_pensar",       # Antes de motor.pensar() — system, user, config
    "post_pensar",      # Despues de motor.pensar() — pensamiento resultante
    "pre_compose",      # Antes de composicion algebraica
    "post_compose",     # Despues de composicion
    "pre_verify",       # Antes de verificacion IC
    "post_verify",      # Despues de verificacion — score, warnings
    "on_error",         # Cualquier error en el kernel
    "on_cache_hit",     # Cache hit del motor
    "on_cascade",       # Cascade: modelo escalado
    "on_breaker_open",  # Circuit breaker se abrio
    "pre_pizarra_write",  # Antes de escribir en pizarra
    "post_pizarra_read",  # Despues de leer de pizarra
    "on_ciclo_inicio",    # Inicio del ciclo de un NodoVivo
    "on_ciclo_fin",       # Fin del ciclo
)


@dataclass
class ProbeResult:
    """Resultado de la ejecucion de un probe."""
    probe_id: str
    checkpoint: str
    datos: Any = None
    alerta: Optional[str] = None  # Si no es None, se loguea como warning
    filtrar: bool = False          # Si True, el dato se descarta (para filters)
    duracion_us: int = 0           # Microsegundos de ejecucion


@dataclass
class Probe:
    """Un probe registrado en un checkpoint.

    Propiedades:
      - id: identificador unico
      - checkpoint: donde se ejecuta
      - funcion: callable que recibe datos y retorna ProbeResult
      - activo: se puede desactivar sin desregistrar
      - max_duracion_ms: si tarda mas, se desactiva automaticamente
      - descripcion: para debugging
    """
    id: str
    checkpoint: str
    funcion: Callable[..., ProbeResult]
    activo: bool = True
    max_duracion_ms: float = 10.0   # Probes deben ser rapidos
    descripcion: str = ""
    ejecuciones: int = 0
    errores: int = 0
    desactivado_por_timeout: bool = False


class SistemaProbes:
    """Gestor de probes del kernel (eBPF cognitivo).

    Registra probes en checkpoints y los ejecuta cuando el kernel
    pasa por esos puntos. Los probes no pueden crashear el kernel:
    errores se capturan y el probe se desactiva tras N fallos.
    """

    def __init__(self, max_errores_antes_desactivar: int = 3):
        self._probes: dict[str, list[Probe]] = {cp: [] for cp in CHECKPOINTS}
        self._max_errores = max_errores_antes_desactivar

    def registrar(self, checkpoint: str, funcion: Callable,
                  probe_id: str = "", descripcion: str = "",
                  max_duracion_ms: float = 10.0) -> str:
        """Registra un probe en un checkpoint.

        Verificacion pre-deployment:
          - El checkpoint debe existir
          - La funcion debe ser callable
        """
        if checkpoint not in CHECKPOINTS:
            raise ValueError(f"Checkpoint desconocido: {checkpoint}. "
                           f"Disponibles: {CHECKPOINTS}")

        if not callable(funcion):
            raise TypeError("El probe debe ser callable")

        pid = probe_id or f"probe_{checkpoint}_{len(self._probes[checkpoint])}"
        probe = Probe(
            id=pid,
            checkpoint=checkpoint,
            funcion=funcion,
            max_duracion_ms=max_duracion_ms,
            descripcion=descripcion,
        )
        self._probes[checkpoint].append(probe)
        log.debug("probe.registrado", id=pid, checkpoint=checkpoint)
        return pid

    def desregistrar(self, probe_id: str) -> bool:
        """Desregistra un probe por ID."""
        for cp, probes in self._probes.items():
            for i, p in enumerate(probes):
                if p.id == probe_id:
                    probes.pop(i)
                    log.debug("probe.desregistrado", id=probe_id)
                    return True
        return False

    def ejecutar(self, checkpoint: str, datos: Any = None) -> list[ProbeResult]:
        """Ejecuta todos los probes de un checkpoint.

        Los probes se ejecutan secuencialmente. Errores se capturan.
        Probes lentos se desactivan automaticamente.
        """
        if checkpoint not in self._probes:
            return []

        resultados = []
        for probe in self._probes[checkpoint]:
            if not probe.activo:
                continue

            t0 = time.perf_counter()
            try:
                result = probe.funcion(datos)
                duracion_us = int((time.perf_counter() - t0) * 1_000_000)
                duracion_ms = duracion_us / 1000

                # Timeout check
                if duracion_ms > probe.max_duracion_ms:
                    probe.activo = False
                    probe.desactivado_por_timeout = True
                    log.warning("probe.timeout",
                                id=probe.id, duracion_ms=round(duracion_ms, 1),
                                max_ms=probe.max_duracion_ms)
                    continue

                if isinstance(result, ProbeResult):
                    result.duracion_us = duracion_us
                    resultados.append(result)
                    if result.alerta:
                        log.warning("probe.alerta",
                                    id=probe.id, alerta=result.alerta)

                probe.ejecuciones += 1

            except Exception as e:
                probe.errores += 1
                if probe.errores >= self._max_errores:
                    probe.activo = False
                    log.warning("probe.desactivado_por_errores",
                                id=probe.id, errores=probe.errores)
                else:
                    log.debug("probe.error",
                              id=probe.id, error=str(e)[:80])

        return resultados

    def listar(self, checkpoint: str = None) -> list[dict]:
        """Lista probes, opcionalmente filtrado por checkpoint."""
        resultado = []
        for cp, probes in self._probes.items():
            if checkpoint and cp != checkpoint:
                continue
            for p in probes:
                resultado.append({
                    "id": p.id,
                    "checkpoint": cp,
                    "activo": p.activo,
                    "ejecuciones": p.ejecuciones,
                    "errores": p.errores,
                    "descripcion": p.descripcion,
                })
        return resultado

    @property
    def stats(self) -> dict:
        total = sum(len(ps) for ps in self._probes.values())
        activos = sum(1 for ps in self._probes.values()
                      for p in ps if p.activo)
        return {"total": total, "activos": activos,
                "checkpoints_con_probes": sum(
                    1 for ps in self._probes.values() if ps)}


# Instancia global
_probes: Optional[SistemaProbes] = None


def get_probes() -> SistemaProbes:
    global _probes
    if _probes is None:
        _probes = SistemaProbes()
    return _probes
