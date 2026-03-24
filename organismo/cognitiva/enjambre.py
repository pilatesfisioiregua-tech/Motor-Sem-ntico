"""Enjambre Cognitivo — NodoVivo nivel 2 que ejecuta clusters.

El Enjambre es la capa entre Director y AFs individuales.
Es tambien un NodoVivo (fractalidad): percibe, procesa, actua, aprende.

Diferencia vs Director:
  - Director decide QUE activar (estrategia)
  - Enjambre ejecuta HOW (tactica): gestiona ciclo de vida de clusters

Estigmergia: agentes no hablan entre si, solo escriben/leen pizarras.
El Director lee pizarras, activa clusters, el enjambre los ejecuta.
"""
from __future__ import annotations

import asyncio
import structlog
from dataclasses import dataclass, field
from typing import Any

from organismo.nodo_vivo import NodoVivo, Senal
from organismo.pizarras.pizarra import PizarraUnificada
from organismo.cognitiva.director import Director
from organismo.meta.circuito_gomas import CircuitoGomas

log = structlog.get_logger()


@dataclass
class MetricasEnjambre:
    """Metricas acumuladas del enjambre."""
    ciclos_ejecutados: int = 0
    prescripciones_emitidas: int = 0
    coste_total_usd: float = 0.0
    score_promedio: float = 0.0
    errores: int = 0

    def registrar_ciclo(self, señales: list[Senal]):
        self.ciclos_ejecutados += 1
        prescripciones = [s for s in señales if s.tipo == "PRESCRIPCION"]
        self.prescripciones_emitidas += len(prescripciones)
        for s in prescripciones:
            self.coste_total_usd += s.payload.get("coste_usd", 0)
        scores = [s.payload.get("verificacion_score", 0)
                  for s in prescripciones if "verificacion_score" in s.payload]
        if scores:
            # Media movil exponencial
            nuevo = sum(scores) / len(scores)
            self.score_promedio = (0.8 * self.score_promedio + 0.2 * nuevo
                                   if self.score_promedio > 0 else nuevo)


class Enjambre(NodoVivo):
    """Enjambre cognitivo — ejecuta el Director + CircuitoGomas.

    Es el NodoVivo de nivel mas alto dentro de un organismo individual.
    Coordina:
      - Director (decide clusters)
      - CircuitoGomas (pipeline G1-G6)
      - Pizarras (estado compartido)

    Ciclo:
      1. percibir: verifica salud del circuito + presupuesto
      2. procesar: ejecuta director.ciclo() (que a su vez lanza clusters)
      3. actuar: propaga recetas a pizarra + notifica
      4. aprender: actualiza metricas + pizarra evolucion
    """

    def __init__(self, tenant_id: str, director: Director = None,
                 circuito: CircuitoGomas = None):
        super().__init__(identidad="enjambre", tenant_id=tenant_id)
        self.director = director or Director(tenant_id)
        self.circuito = circuito or CircuitoGomas(tenant_id)
        self.pizarra = PizarraUnificada(tenant_id)
        self.metricas = MetricasEnjambre()

    async def percibir(self) -> list[Senal]:
        """Verifica salud del sistema antes de activar director."""
        señales = []

        # 1. Circuito tiene roturas?
        if self.circuito.hay_roturas:
            señales.append(Senal(
                origen="circuito_gomas",
                tipo="ALERTA",
                modo="estado",
                fuente="interocepcion",
                prioridad=1,
                payload={
                    "roturas": {n: g.estado.value
                                for n, g in self.circuito.gomas.items()
                                if g.estado.value == "rota"},
                },
                tenant_id=self.tenant_id,
            ))

        # 2. Circuito frenado (CR1)?
        if self.circuito.frenado:
            señales.append(Senal(
                origen="circuito_gomas",
                tipo="VETO",
                modo="estado",
                fuente="interocepcion",
                prioridad=1,
                payload={"motivo": "CR1_frenado"},
                tenant_id=self.tenant_id,
            ))
            return señales  # No proceder si frenado

        # 3. Presupuesto restante
        from motor.pensar import presupuesto_restante
        restante = presupuesto_restante()
        if restante <= 0:
            señales.append(Senal(
                origen="motor",
                tipo="VETO",
                modo="ley",
                fuente="interocepcion",
                prioridad=1,
                payload={"motivo": "presupuesto_agotado", "restante": restante},
                tenant_id=self.tenant_id,
            ))
            return señales

        # 4. Senal de "todo ok, activar director"
        señales.append(Senal(
            origen="enjambre",
            tipo="ACCION",
            modo="proceso",
            fuente="interocepcion",
            payload={
                "presupuesto_restante": round(restante, 2),
                "gomas_ok": not self.circuito.hay_roturas,
                "metricas": {
                    "ciclos": self.metricas.ciclos_ejecutados,
                    "coste_total": round(self.metricas.coste_total_usd, 4),
                },
            },
            tenant_id=self.tenant_id,
        ))

        return señales

    async def procesar(self, señales: list[Senal]) -> Any:
        """Ejecuta director.ciclo() si no hay vetos."""
        # Verificar vetos
        vetos = [s for s in señales if s.tipo == "VETO"]
        if vetos:
            motivos = [s.payload.get("motivo", "desconocido") for s in vetos]
            log.warning("enjambre.veto", motivos=motivos, tenant=self.tenant_id)
            return vetos

        # Ejecutar director
        resultado = await self.director.ciclo()
        return resultado

    async def actuar(self, plan: Any) -> list[Senal]:
        """Propaga recetas y alertas."""
        señales = plan if isinstance(plan, list) else []

        # Filtrar prescripciones para escribir en pizarra
        prescripciones = [s for s in señales if s.tipo == "PRESCRIPCION"]
        for p in prescripciones:
            await self.pizarra.escribir(
                "cognitiva",
                f"prescripcion_{p.payload.get('gap', 'general')}",
                p.payload,
                notificar=True,
            )

        # Estado del enjambre
        await self.pizarra.escribir(
            "estado", "enjambre_estado",
            {
                "ciclos": self.metricas.ciclos_ejecutados + 1,
                "prescripciones_ciclo": len(prescripciones),
                "alertas_ciclo": len([s for s in señales if s.tipo == "ALERTA"]),
                "coste_total": round(self.metricas.coste_total_usd, 4),
            },
        )

        return señales

    async def aprender(self, resultado: list[Senal]) -> None:
        """Actualiza metricas del enjambre."""
        self.metricas.registrar_ciclo(resultado)

        await self.pizarra.escribir(
            "evolucion", "enjambre_metricas",
            {
                "ciclos_ejecutados": self.metricas.ciclos_ejecutados,
                "prescripciones_total": self.metricas.prescripciones_emitidas,
                "coste_total": round(self.metricas.coste_total_usd, 4),
                "score_promedio": round(self.metricas.score_promedio, 2),
            },
        )
