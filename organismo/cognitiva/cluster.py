"""Cluster cognitivo — grupo dinamico de agentes para un gap.

Un cluster reune:
  - N AgenteFuncional relevantes para el gap
  - Un Compositor que une las salidas (kernel.algebra.compose)
  - Un Estratega que prescribe receta (motor.pensar alta complejidad)

Patron estigmergia: los agentes no hablan entre si.
Escriben en pizarra compartida, el Compositor lee y compone.
"""
from __future__ import annotations

import asyncio
import structlog
from dataclasses import dataclass, field
from typing import Any

from organismo.nodo_vivo import NodoVivo, Senal
from organismo.pizarras.pizarra import PizarraUnificada

log = structlog.get_logger()


@dataclass
class GapInfo:
    """Informacion sobre un gap detectado por ACD."""
    funcion: str          # F1-F7
    lente: str            # salud, sentido, continuidad
    score: float          # 0-10 actual
    gap: float            # diferencia vs objetivo
    contexto: str = ""    # descripcion textual del gap
    prioridad: int = 5    # 1=urgente


class Compositor:
    """Compone N salidas de agentes en una prescripcion unificada.

    Usa kernel.algebra.compose() para combinar respetando IC2.
    """

    async def componer(self, salidas: list[Senal], gap: GapInfo,
                       tenant_id: str) -> Senal:
        """Compone N senales de agentes en 1 prescripcion."""
        from motor.pensar import pensar, ConfigPensamiento

        if not salidas:
            return Senal(
                origen="compositor",
                tipo="RESUMEN",
                payload={"nota": "sin_salidas_a_componer"},
                tenant_id=tenant_id,
            )

        # Construir contexto de composicion
        partes = []
        for s in salidas:
            partes.append(
                f"[{s.origen}] score={s.payload.get('verificacion_score', '?')}: "
                f"{s.payload.get('texto', '')[:300]}"
            )

        system = (
            f"Eres el Compositor del cluster para gap {gap.funcion}/{gap.lente}. "
            f"Score actual: {gap.score}/10, gap: {gap.gap}. "
            f"Compones {len(salidas)} perspectivas en UNA prescripcion coherente. "
            f"Respeta IC2 (orden importa): las funciones NO son intercambiables. "
            f"Prioriza la perspectiva mas especifica sobre la mas generica."
        )
        user = "\n\n".join(partes)

        resultado = await pensar(
            system=system, user=user,
            config=ConfigPensamiento(
                funcion=gap.funcion,
                lente=gap.lente,
                complejidad="media",
                tenant_id=tenant_id,
                verificar_output=True,
            ),
        )

        return Senal(
            origen="compositor",
            tipo="PRESCRIPCION",
            modo="proceso",
            fuente="propiocepcion_motora",
            payload={
                "texto": resultado.texto,
                "gap": gap.funcion,
                "lente": gap.lente,
                "n_fuentes": len(salidas),
                "verificacion_score": resultado.verificacion_score,
                "coste_usd": resultado.coste_usd,
            },
            tenant_id=tenant_id,
        )


class Estratega:
    """Prescribe receta concreta desde la composicion.

    Lee composicion + pizarra evolucion (que funciono antes)
    y produce receta accionable con CR1 si necesario.
    """

    async def prescribir(self, composicion: Senal, gap: GapInfo,
                         tenant_id: str) -> Senal:
        """Convierte composicion en receta accionable."""
        from motor.pensar import pensar, ConfigPensamiento

        pizarra = PizarraUnificada(tenant_id)
        evolucion = await pizarra.leer_tipo("evolucion")

        system = (
            f"Eres el Estratega prescriptor de OMNI-MIND. "
            f"Gap: {gap.funcion}/{gap.lente} score={gap.score}/10. "
            f"Conviertes la composicion del Compositor en UNA receta concreta. "
            f"La receta debe incluir: accion_principal, responsable (AF), "
            f"metricas_objetivo, plazo_dias, requiere_cr1 (bool). "
            f"Responde SOLO en JSON valido."
        )
        contexto_evol = ""
        if evolucion:
            contexto_evol = f"\n\nHistorico evolucion: {str(evolucion)[:500]}"

        user = (
            f"Composicion:\n{composicion.payload.get('texto', '')[:800]}"
            f"{contexto_evol}"
        )

        resultado = await pensar(
            system=system, user=user,
            config=ConfigPensamiento(
                funcion=gap.funcion,
                lente=gap.lente,
                complejidad="alta",
                tenant_id=tenant_id,
                verificar_output=True,
                json_schema={
                    "name": "receta",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "accion_principal": {"type": "string"},
                            "responsable": {"type": "string"},
                            "metricas_objetivo": {"type": "object"},
                            "plazo_dias": {"type": "integer"},
                            "requiere_cr1": {"type": "boolean"},
                        },
                        "required": ["accion_principal", "responsable", "requiere_cr1"],
                    },
                },
            ),
        )

        return Senal(
            origen="estratega",
            tipo="PRESCRIPCION",
            modo="potencial",
            fuente="propiocepcion_motora",
            prioridad=2,
            payload={
                "receta": resultado.texto,
                "gap": gap.funcion,
                "lente": gap.lente,
                "verificacion_score": resultado.verificacion_score,
                "coste_usd": resultado.coste_usd,
            },
            tenant_id=tenant_id,
        )


class ClusterCognitivo(NodoVivo):
    """Grupo dinamico de agentes para cerrar un gap.

    Ciclo:
      1. percibir: lee gap + sensores relevantes via bus
      2. procesar: ejecuta N agentes en paralelo (estigmergia)
      3. actuar: Compositor + Estratega producen receta
      4. aprender: registra resultado en pizarra evolucion
    """

    def __init__(self, gap: GapInfo, agentes: list[NodoVivo], tenant_id: str):
        super().__init__(
            identidad=f"cluster-{gap.funcion}-{gap.lente}",
            tenant_id=tenant_id,
        )
        self.gap = gap
        self.agentes = agentes
        self.compositor = Compositor()
        self.estratega = Estratega()
        self.pizarra = PizarraUnificada(tenant_id)

    async def percibir(self) -> list[Senal]:
        """Lee el gap como senal principal."""
        return [Senal(
            origen="director",
            tipo="ALERTA",
            modo="estado",
            fuente="interocepcion",
            prioridad=self.gap.prioridad,
            payload={
                "funcion": self.gap.funcion,
                "lente": self.gap.lente,
                "score": self.gap.score,
                "gap": self.gap.gap,
                "contexto": self.gap.contexto,
            },
            tenant_id=self.tenant_id,
        )]

    async def procesar(self, señales: list[Senal]) -> Any:
        """Ejecuta N agentes en paralelo (estigmergia)."""
        tareas = [agente.ciclo() for agente in self.agentes]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)

        salidas = []
        for i, r in enumerate(resultados):
            if isinstance(r, Exception):
                log.warning("cluster.agente_error",
                            agente=self.agentes[i].identidad,
                            error=str(r)[:80])
                continue
            if isinstance(r, list):
                salidas.extend(r)

        return salidas

    async def actuar(self, plan: Any) -> list[Senal]:
        """Compositor + Estratega producen receta."""
        salidas = plan if isinstance(plan, list) else []

        # Compositor: une N perspectivas
        composicion = await self.compositor.componer(
            salidas, self.gap, self.tenant_id)

        # Estratega: prescribe receta
        receta = await self.estratega.prescribir(
            composicion, self.gap, self.tenant_id)

        # Escribir en pizarra cognitiva
        await self.pizarra.escribir(
            "cognitiva",
            f"receta_{self.gap.funcion}_{self.gap.lente}",
            receta.payload,
            notificar=True,
        )

        return [composicion, receta]

    async def aprender(self, resultado: list[Senal]) -> None:
        """Registra resultado en pizarra evolucion."""
        for s in resultado:
            if s.tipo == "PRESCRIPCION":
                await self.pizarra.escribir(
                    "evolucion",
                    f"cluster_{self.gap.funcion}_{self.gap.lente}",
                    {
                        "origen": s.origen,
                        "verificacion_score": s.payload.get("verificacion_score", 0),
                        "coste_usd": s.payload.get("coste_usd", 0),
                    },
                )
