"""NodoVivo — Interfaz fractal base de la Matrioska OMNI-MIND.

Cada nivel del ecosistema (llamada LLM → agente → enjambre → organismo → ecosistema)
implementa esta misma interfaz. Es S+C aplicado a la propia arquitectura.

Principios:
- P63: Los agentes NO reciben instrucciones — leen intenciones de pizarras
- P64: Todo acoplamiento es una lectura de un espacio compartido
- Invariante 2 L0: Fractalidad — misma operación a toda escala
- §23 Marco Lingüístico: Emergencia = sujeto se convierte en predicado de escala superior
"""
from __future__ import annotations

import asyncio
import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

log = structlog.get_logger()

MADRID_TZ = ZoneInfo("Europe/Madrid")

# 9 modos de percepción del Marco Lingüístico (§6)
MODOS_PERCEPCION = (
    "proceso",      # qué ocurre (deverbales) — 14 operadores
    "propiedad",    # cómo es (deadjetivales) — 11 operadores
    "relacion",     # qué interactúa — 11 operadores
    "forma",        # dónde está (topológico) — 11 operadores
    "ley",          # qué se cumple — 6 operadores
    "agente",       # quién opera — 2 operadores
    "estado",       # en qué condición — HUECO detectado §6
    "evento",       # qué acaba de pasar — parcial
    "potencial",    # qué podría pasar — HUECO detectado §6
)

# 6 tipos de señal del bus (L0_8)
TIPOS_SENAL = ("ALERTA", "PRESCRIPCION", "VETO", "OPORTUNIDAD", "ACCION", "RESUMEN")

# 3 fuentes de percepción
FUENTES_PERCEPCION = ("exterocepcion", "interocepcion", "propiocepcion_motora")


@dataclass
class Senal:
    """Unidad mínima de comunicación en el ecosistema.

    Cada señal lleva:
    - origen: quién la emitió (identidad F5 del emisor)
    - tipo: qué tipo de señal es (6 tipos L0_8)
    - modo: qué modo de percepción representa (9 modos §6)
    - fuente: de dónde viene (exterocepción/interocepción/propiocepción motora)
    - payload: contenido libre
    - prioridad: 1=urgente (LISTEN/NOTIFY), 5=normal (cron)
    """
    origen: str
    tipo: str
    payload: dict = field(default_factory=dict)
    modo: str = "proceso"
    fuente: str = "exterocepcion"
    prioridad: int = 5
    destino: Optional[str] = None
    tenant_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(MADRID_TZ))

    def __post_init__(self):
        if self.tipo not in TIPOS_SENAL:
            log.warning("senal_tipo_desconocido", tipo=self.tipo)
        if self.modo not in MODOS_PERCEPCION:
            log.warning("senal_modo_desconocido", modo=self.modo)


class NodoVivo(ABC):
    """Interfaz base que se repite a toda escala de la Matrioska.

    Un AF3, un Enjambre, un Organismo y el Ecosistema completo
    implementan esta misma interfaz. La diferencia está en:
    - Qué perciben (sensores SQL vs telemetría vs health)
    - Cómo procesan (motor.pensar vs álgebra vs gomas)
    - Qué emiten (señales vs prescripciones vs transferencias)
    - De qué aprenden (tasa_cierre vs patrones vs cross-dominio)

    Cada NodoVivo:
    1. Sabe QUÉ ES (F5 — identidad)
    2. Lee lo que necesita de un espacio compartido (pizarra)
    3. Se comprime en comportamiento (ciclo)
    """

    def __init__(self, identidad: str, tenant_id: str = ""):
        self.identidad = identidad      # F5 — qué soy
        self.tenant_id = tenant_id      # a qué organismo pertenezco
        self._ciclo_activo = False

    @abstractmethod
    async def percibir(self) -> list[Senal]:
        """Lee pizarras + sensores.

        Doble percepción (Principio 1 de Jesús):
        - EXTERNO: datos del negocio, canales, webhooks
        - INTERNO: telemetría, estado componentes, drift
        """
        ...

    @abstractmethod
    async def procesar(self, señales: list[Senal]) -> Any:
        """Sandwich LLM: código_pre → LLM → código_post.

        El código_pre (kernel) es determinista y $0.
        El LLM es para lo genuinamente no computable.
        El código_post (verificador) valida IC2-IC7.
        """
        ...

    @abstractmethod
    async def actuar(self, plan: Any) -> list[Senal]:
        """Emite señales al bus o ejecuta acciones.

        Respeta CR1: acciones sobre clientes/negocio
        requieren aprobación del propietario del tenant.
        """
        ...

    @abstractmethod
    async def aprender(self, resultado: list[Senal]) -> None:
        """Feedback a pizarra evolución.

        Registra: qué funcionó, qué no, delta esperado vs real.
        Alimenta al Gestor (loop lento) y al Ecosistema (cross-dominio).
        """
        ...

    async def ciclo(self) -> list[Senal]:
        """El loop universal: percibir → procesar → actuar → aprender.

        Es el mismo ciclo a toda escala:
        - Nivel 0 (llamada LLM): prompt → respuesta → verificación → telemetría
        - Nivel 1 (agente AF): sensor → motor.pensar → señal → pizarra estado
        - Nivel 2 (enjambre): diagnóstico → clusters → composición → prescripción
        - Nivel 3 (organismo): 6 gomas G1→G6 + META
        - Nivel 4 (ecosistema): telemetría N → patrones → transferencias → evolución
        """
        if self._ciclo_activo:
            log.warning("nodo_ciclo_ya_activo", identidad=self.identidad)
            return []

        self._ciclo_activo = True
        try:
            señales = await self.percibir()
            if not señales:
                log.debug("nodo_sin_señales", identidad=self.identidad)
                return []

            plan = await self.procesar(señales)
            resultado = await self.actuar(plan)
            await self.aprender(resultado)

            log.info("nodo_ciclo_completo",
                     identidad=self.identidad,
                     señales_entrada=len(señales),
                     señales_salida=len(resultado))
            return resultado
        except Exception as e:
            log.error("nodo_ciclo_error",
                      identidad=self.identidad,
                      error=str(e))
            return [Senal(
                origen=self.identidad,
                tipo="ALERTA",
                modo="estado",
                fuente="interocepcion",
                prioridad=2,
                payload={"error": str(e), "fase": "ciclo"},
                tenant_id=self.tenant_id,
            )]
        finally:
            self._ciclo_activo = False

    def __repr__(self):
        return f"<NodoVivo:{self.identidad} tenant={self.tenant_id}>"
