"""Director Orquestador — cerebro del organismo (NodoVivo nivel 2).

Lee pizarra cognitiva + diagnostico ACD.
Decide QUE clusters activar, con que agentes, y prioridad.
NO toma decisiones de negocio — solo orquesta.

Patron PULL (P63): Director lee pizarras, no recibe instrucciones.
"""
from __future__ import annotations

import asyncio
import structlog
from typing import Any

from organismo.nodo_vivo import NodoVivo, Senal
from organismo.pizarras.pizarra import PizarraUnificada
from organismo.cognitiva.cluster import ClusterCognitivo, GapInfo
from organismo.agentes.agente_funcional import AgenteFuncional

log = structlog.get_logger()

# Mapeo funcion → agentes relevantes (que AF ayudan a cerrar cada gap)
MAPA_FUNCIONES_AGENTES = {
    "F1": ["F1", "F5"],           # Conservar: identidad + conservacion
    "F2": ["F2", "F4"],           # Captar: captacion + decidir
    "F3": ["F3", "F1"],           # Depurar: depuracion + conservar (para no perder)
    "F4": ["F4", "F2", "F6"],     # Decidir: decidir + captar + adaptar
    "F5": ["F5", "F1"],           # Identidad: identidad + conservar
    "F6": ["F6", "F4"],           # Adaptar: adaptar + decidir
    "F7": ["F7", "F2", "F6"],     # Replicar: replicar + captar + adaptar
}


class Director(NodoVivo):
    """Orquestador del enjambre cognitivo.

    Ciclo (NodoVivo nivel 2):
      1. percibir: lee diagnostico ACD + estado gomas + pizarra temporal
      2. procesar: decide que clusters activar segun gaps detectados
      3. actuar: lanza clusters en paralelo, recoge recetas
      4. aprender: registra coste, tiempo, scores en pizarra evolucion

    NO toma decisiones de negocio — eso es CR1 del propietario.
    """

    def __init__(self, tenant_id: str, system_prompts: dict[str, str] = None,
                 sensor_queries: dict[str, dict[str, str]] = None):
        super().__init__(identidad="director", tenant_id=tenant_id)
        self.pizarra = PizarraUnificada(tenant_id)
        self.system_prompts = system_prompts or {}
        self.sensor_queries = sensor_queries or {}
        self._fabrica_agentes: dict[str, AgenteFuncional] = {}

    def _obtener_agente(self, funcion: str) -> AgenteFuncional:
        """Obtiene o crea un agente funcional (lazy)."""
        if funcion not in self._fabrica_agentes:
            self._fabrica_agentes[funcion] = AgenteFuncional(
                funcion=funcion,
                tenant_id=self.tenant_id,
                system_prompt=self.system_prompts.get(funcion, ""),
                sensor_queries=self.sensor_queries.get(funcion, {}),
            )
        return self._fabrica_agentes[funcion]

    async def percibir(self) -> list[Senal]:
        """Lee diagnostico ACD + estado gomas + pizarra temporal."""
        señales = []

        # 1. Diagnostico ACD (gap principal)
        cognitiva = await self.pizarra.leer_tipo("cognitiva")
        if cognitiva:
            señales.append(Senal(
                origen="pizarra_cognitiva",
                tipo="RESUMEN",
                modo="estado",
                fuente="interocepcion",
                payload=cognitiva,
                tenant_id=self.tenant_id,
            ))

        # 2. Estado gomas
        estado = await self.pizarra.leer_estado()
        if estado:
            señales.append(Senal(
                origen="pizarra_estado",
                tipo="RESUMEN",
                modo="estado",
                fuente="interocepcion",
                payload=estado,
                tenant_id=self.tenant_id,
            ))

        # 3. Temporal (ciclo actual, fechas clave)
        temporal = await self.pizarra.leer_tipo("temporal")
        if temporal:
            señales.append(Senal(
                origen="pizarra_temporal",
                tipo="RESUMEN",
                modo="evento",
                fuente="interocepcion",
                payload=temporal,
                tenant_id=self.tenant_id,
            ))

        return señales

    async def procesar(self, señales: list[Senal]) -> Any:
        """Decide que clusters activar segun gaps detectados."""
        gaps = self._extraer_gaps(señales)

        if not gaps:
            log.info("director.sin_gaps", tenant=self.tenant_id)
            return []

        # Ordenar por prioridad (gap mayor primero)
        gaps.sort(key=lambda g: g.gap, reverse=True)

        # Limitar a 3 clusters simultaneos (presupuesto)
        gaps_activos = gaps[:3]

        clusters = []
        for gap in gaps_activos:
            funciones = MAPA_FUNCIONES_AGENTES.get(gap.funcion, [gap.funcion])
            agentes = [self._obtener_agente(f) for f in funciones]
            cluster = ClusterCognitivo(
                gap=gap,
                agentes=agentes,
                tenant_id=self.tenant_id,
            )
            clusters.append(cluster)

        log.info("director.clusters_activados",
                 tenant=self.tenant_id,
                 clusters=len(clusters),
                 gaps=[g.funcion for g in gaps_activos])

        return clusters

    async def actuar(self, plan: Any) -> list[Senal]:
        """Lanza clusters en paralelo, recoge recetas."""
        clusters = plan if isinstance(plan, list) else []

        if not clusters:
            return []

        # Lanzar todos los clusters en paralelo
        tareas = [cluster.ciclo() for cluster in clusters]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)

        señales_salida = []
        coste_total = 0.0

        for i, resultado in enumerate(resultados):
            if isinstance(resultado, Exception):
                log.warning("director.cluster_error",
                            cluster=clusters[i].identidad,
                            error=str(resultado)[:80])
                señales_salida.append(Senal(
                    origen=self.identidad,
                    tipo="ALERTA",
                    modo="estado",
                    fuente="interocepcion",
                    prioridad=2,
                    payload={
                        "error": str(resultado)[:200],
                        "cluster": clusters[i].identidad,
                    },
                    tenant_id=self.tenant_id,
                ))
                continue

            if isinstance(resultado, list):
                señales_salida.extend(resultado)
                for s in resultado:
                    coste_total += s.payload.get("coste_usd", 0)

        # Escribir resumen en pizarra estado
        await self.pizarra.escribir(
            "estado", "ultimo_ciclo_director",
            {
                "clusters_lanzados": len(clusters),
                "clusters_ok": len([r for r in resultados if not isinstance(r, Exception)]),
                "prescripciones": len([s for s in señales_salida if s.tipo == "PRESCRIPCION"]),
                "coste_total_usd": round(coste_total, 4),
            },
            notificar=True,
        )

        return señales_salida

    async def aprender(self, resultado: list[Senal]) -> None:
        """Registra metricas del ciclo en pizarra evolucion."""
        prescripciones = [s for s in resultado if s.tipo == "PRESCRIPCION"]
        if prescripciones:
            scores = [s.payload.get("verificacion_score", 0) for s in prescripciones]
            await self.pizarra.escribir(
                "evolucion", "ciclo_director",
                {
                    "n_prescripciones": len(prescripciones),
                    "score_promedio": round(sum(scores) / len(scores), 2) if scores else 0,
                    "coste_total": sum(s.payload.get("coste_usd", 0) for s in prescripciones),
                },
            )

    def _extraer_gaps(self, señales: list[Senal]) -> list[GapInfo]:
        """Extrae gaps del diagnostico ACD en las senales."""
        gaps = []
        for s in señales:
            if s.origen != "pizarra_cognitiva":
                continue
            payload = s.payload or {}

            # Buscar diagnostico ACD
            diagnostico = payload.get("ultimo_diagnostico", {})
            if isinstance(diagnostico, dict):
                scores = diagnostico.get("scores", {})
                for funcion, score_data in scores.items():
                    if isinstance(score_data, dict):
                        score = score_data.get("score", 5)
                        objetivo = score_data.get("objetivo", 7)
                    else:
                        score = float(score_data) if score_data else 5
                        objetivo = 7

                    gap_val = max(0, objetivo - score)
                    if gap_val > 0.5:  # Solo gaps significativos
                        gaps.append(GapInfo(
                            funcion=funcion,
                            lente=score_data.get("lente", "salud") if isinstance(score_data, dict) else "salud",
                            score=score,
                            gap=gap_val,
                            prioridad=1 if gap_val > 3 else (3 if gap_val > 1.5 else 5),
                        ))

            # Buscar gaps explicitos en pizarra
            for clave, valor in payload.items():
                if clave.startswith("gap_") and isinstance(valor, dict):
                    gaps.append(GapInfo(
                        funcion=valor.get("funcion", clave.replace("gap_", "")),
                        lente=valor.get("lente", "salud"),
                        score=valor.get("score", 5),
                        gap=valor.get("gap", 2),
                        contexto=valor.get("contexto", ""),
                        prioridad=valor.get("prioridad", 5),
                    ))

        return gaps
