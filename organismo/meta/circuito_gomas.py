"""CircuitoGomas — Motor perpetuo del organismo (L0_10).

6 gomas elásticas que transmiten energía en circuito cerrado:
  G1: DATOS → SEÑALES       (negocio genera datos, sensores los capturan)
  G2: SEÑALES → DIAGNÓSTICO (bus acumula, ACD diagnostica semanal)
  G3: DIAGNÓSTICO → BÚSQUEDA (gaps generan queries dirigidas)
  G4: BÚSQUEDA → PRESCRIPCIÓN (cognitiva diagnostica, Estratega prescribe)
  G5: PRESCRIPCIÓN → ACCIÓN   (AF1-AF7 ejecutan via bus)
  G6: ACCIÓN → APRENDIZAJE    (Gestor registra, poda cada 50 exec)

Goma META: detecta roturas en las 6 gomas y auto-repara.

El circuito gira solo. Solo Jesús puede frenarlo (CR1).
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Optional
from zoneinfo import ZoneInfo

from organismo.nodo_vivo import Senal

log = structlog.get_logger()
MADRID_TZ = ZoneInfo("Europe/Madrid")


class EstadoGoma(str, Enum):
    """Estado de una goma del circuito."""
    GIRANDO = "girando"         # Funcionando normal
    TENSA = "tensa"             # Funcionando pero con presión (latencia alta, errores parciales)
    ROTA = "rota"               # No funciona — requiere META
    FRENADA = "frenada"         # Parada por CR1 (Jesús)
    DORMIDA = "dormida"         # No activada aún


@dataclass
class Goma:
    """Una goma del circuito perpetuo.

    Cada goma tiene:
    - nombre: G1-G6 o META
    - entrada: qué recibe (tipo de dato/señal)
    - salida: qué produce
    - ejecutar: función async que implementa la transformación
    - frecuencia: cada cuánto gira (cron-like)
    - estado: actual
    - métricas: últimas ejecuciones
    """
    nombre: str
    entrada: str
    salida: str
    ejecutar: Optional[Callable[..., Coroutine]] = None
    frecuencia: str = "semanal"       # continua | 15min | diaria | semanal | 50exec
    estado: EstadoGoma = EstadoGoma.DORMIDA
    ultima_ejecucion: Optional[datetime] = None
    errores_consecutivos: int = 0
    total_ejecuciones: int = 0

    async def girar(self, entrada: Any, tenant_id: str = "") -> Any:
        """Ejecuta la goma: transforma entrada → salida."""
        if self.estado == EstadoGoma.FRENADA:
            log.warning("goma.frenada", nombre=self.nombre)
            return None
        if self.estado == EstadoGoma.ROTA:
            log.error("goma.rota", nombre=self.nombre)
            return None
        if self.ejecutar is None:
            log.warning("goma.sin_implementar", nombre=self.nombre)
            return None

        self.estado = EstadoGoma.GIRANDO
        try:
            resultado = await self.ejecutar(entrada, tenant_id)
            self.errores_consecutivos = 0
            self.total_ejecuciones += 1
            self.ultima_ejecucion = datetime.now(MADRID_TZ)
            return resultado
        except Exception as e:
            self.errores_consecutivos += 1
            if self.errores_consecutivos >= 3:
                self.estado = EstadoGoma.ROTA
                log.error("goma.rota_por_errores", nombre=self.nombre,
                          errores=self.errores_consecutivos, error=str(e)[:80])
            else:
                self.estado = EstadoGoma.TENSA
                log.warning("goma.error", nombre=self.nombre,
                            errores=self.errores_consecutivos, error=str(e)[:80])
            raise


@dataclass
class CircuitoGomas:
    """El motor perpetuo del organismo.

    Encadena G1→G2→G3→G4→G5→G6 en circuito cerrado.
    META supervisa y repara las 6 gomas.
    """
    tenant_id: str
    gomas: dict[str, Goma] = field(default_factory=dict)
    frenado: bool = False              # CR1: solo Jesús frena

    def __post_init__(self):
        """Inicializa las 6 gomas + META con stubs."""
        definiciones = [
            ("G1", "datos", "señales", "continua"),
            ("G2", "señales", "diagnóstico", "semanal"),
            ("G3", "diagnóstico", "búsqueda", "diaria"),
            ("G4", "búsqueda", "prescripción", "semanal"),
            ("G5", "prescripción", "acción", "continua"),
            ("G6", "acción", "aprendizaje", "50exec"),
            ("META", "rotura", "reparación", "15min"),
        ]
        for nombre, entrada, salida, frecuencia in definiciones:
            if nombre not in self.gomas:
                self.gomas[nombre] = Goma(
                    nombre=nombre,
                    entrada=entrada,
                    salida=salida,
                    frecuencia=frecuencia,
                )

    def registrar_goma(self, nombre: str,
                       ejecutar: Callable[..., Coroutine]) -> None:
        """Registra la implementación de una goma."""
        if nombre in self.gomas:
            self.gomas[nombre].ejecutar = ejecutar
            self.gomas[nombre].estado = EstadoGoma.DORMIDA
            log.info("goma.registrada", nombre=nombre)

    def frenar(self) -> None:
        """CR1: Jesús frena todo el circuito."""
        self.frenado = True
        for g in self.gomas.values():
            g.estado = EstadoGoma.FRENADA
        log.warning("circuito.FRENADO_CR1", tenant=self.tenant_id)

    def reanudar(self) -> None:
        """CR1: Jesús reanuda el circuito."""
        self.frenado = False
        for g in self.gomas.values():
            if g.estado == EstadoGoma.FRENADA:
                g.estado = EstadoGoma.DORMIDA
        log.info("circuito.reanudado", tenant=self.tenant_id)

    async def girar_goma(self, nombre: str, entrada: Any) -> Any:
        """Ejecuta una goma individual."""
        if self.frenado:
            log.warning("circuito.frenado", nombre=nombre)
            return None
        goma = self.gomas.get(nombre)
        if not goma:
            raise ValueError(f"Goma {nombre} no existe")
        return await goma.girar(entrada, self.tenant_id)

    async def ciclo_completo(self, datos_iniciales: Any = None) -> dict[str, Any]:
        """Ejecuta G1→G2→G3→G4→G5→G6 en secuencia.

        Cada goma recibe la salida de la anterior.
        Si una goma falla, el ciclo se detiene y META se activa.
        """
        if self.frenado:
            log.warning("circuito.frenado_completo", tenant=self.tenant_id)
            return {"estado": "frenado"}

        resultados: dict[str, Any] = {}
        datos = datos_iniciales

        for nombre in ["G1", "G2", "G3", "G4", "G5", "G6"]:
            goma = self.gomas[nombre]
            if goma.ejecutar is None:
                log.debug("goma.no_implementada", nombre=nombre)
                continue
            try:
                datos = await goma.girar(datos, self.tenant_id)
                resultados[nombre] = datos
            except Exception as e:
                resultados[nombre] = {"error": str(e)[:200]}
                # Activar META
                await self._activar_meta(nombre, e)
                break

        log.info("circuito.ciclo_completo",
                 tenant=self.tenant_id,
                 gomas_ok=len([r for r in resultados.values() if not isinstance(r, dict) or "error" not in r]),
                 gomas_total=len(resultados))

        return resultados

    async def _activar_meta(self, goma_rota: str, error: Exception) -> None:
        """Activa la goma META para reparar una goma rota."""
        meta = self.gomas.get("META")
        if meta and meta.ejecutar:
            try:
                await meta.girar(
                    {"goma_rota": goma_rota, "error": str(error)},
                    self.tenant_id,
                )
            except Exception as e:
                log.error("meta.fallo_reparacion",
                          goma_rota=goma_rota, error=str(e)[:80])

    @property
    def estado_resumen(self) -> dict[str, str]:
        """Resumen del estado de todas las gomas."""
        return {nombre: goma.estado.value for nombre, goma in self.gomas.items()}

    @property
    def hay_roturas(self) -> bool:
        return any(g.estado == EstadoGoma.ROTA for g in self.gomas.values())
