"""AgenteFuncional — NodoVivo concreto para AF1-AF7.

Cada agente funcional es un NodoVivo que:
  1. Percibe: lee pizarra estado + sensores SQL de su función
  2. Procesa: motor.pensar() con contexto de su función
  3. Actúa: emite señales al bus + escribe en pizarra
  4. Aprende: registra tasa_cierre y delta en pizarra evolución
"""
from __future__ import annotations

import structlog
from typing import Any

from organismo.nodo_vivo import NodoVivo, Senal
from organismo.pizarras.pizarra import PizarraUnificada

log = structlog.get_logger()


class AgenteFuncional(NodoVivo):
    """Implementación concreta de NodoVivo para un agente funcional.

    Cada AF (AF1=Conservar, AF2=Captar, AF3=Depurar, ..., AF7=Replicar)
    tiene su propia instancia con:
    - funcion: F1-F7
    - sensor_queries: consultas SQL para percibir datos del negocio
    - system_prompt: prompt de sistema específico de la función
    """

    def __init__(
        self,
        funcion: str,
        tenant_id: str,
        system_prompt: str = "",
        sensor_queries: dict[str, str] = None,
    ):
        super().__init__(
            identidad=f"AF-{funcion}",
            tenant_id=tenant_id,
        )
        self.funcion = funcion
        self.system_prompt = system_prompt or f"Eres el agente funcional {funcion} de OMNI-MIND."
        self.sensor_queries = sensor_queries or {}
        self.pizarra = PizarraUnificada(tenant_id)

    async def percibir(self) -> list[Senal]:
        """Lee pizarra estado + ejecuta sensores SQL del negocio."""
        señales = []

        # 1. Leer estado del organismo desde pizarra
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

        # 2. Ejecutar sensores SQL (exterocepción)
        try:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                for nombre, query in self.sensor_queries.items():
                    try:
                        rows = await conn.fetch(query, self.tenant_id)
                        if rows:
                            señales.append(Senal(
                                origen=f"sensor_{nombre}",
                                tipo="ALERTA" if len(rows) > 0 else "RESUMEN",
                                modo="proceso",
                                fuente="exterocepcion",
                                payload={
                                    "sensor": nombre,
                                    "datos": [dict(r) for r in rows[:20]],
                                    "total": len(rows),
                                },
                                tenant_id=self.tenant_id,
                            ))
                    except Exception as e:
                        log.warning("af.sensor_error", sensor=nombre, error=str(e)[:80])
        except Exception as e:
            log.debug("af.db_no_disponible", error=str(e)[:80])

        # 3. Leer identidad F5 (propiocepción)
        identidad = await self.pizarra.leer_identidad()
        if identidad:
            señales.append(Senal(
                origen="pizarra_identidad",
                tipo="RESUMEN",
                modo="agente",
                fuente="propiocepcion_motora",
                payload=identidad,
                tenant_id=self.tenant_id,
            ))

        return señales

    async def procesar(self, señales: list[Senal]) -> Any:
        """Sandwich LLM: kernel_pre → motor.pensar() → kernel_post."""
        from motor.pensar import pensar, ConfigPensamiento

        # Construir contexto desde señales
        contexto_parts = []
        for s in señales:
            contexto_parts.append(f"[{s.fuente}/{s.modo}] {s.origen}: {s.payload}")

        user_message = "\n".join(str(p) for p in contexto_parts)

        config = ConfigPensamiento(
            funcion=self.funcion,
            tenant_id=self.tenant_id,
            complejidad="media",
            verificar_output=True,
        )

        resultado = await pensar(
            system=self.system_prompt,
            user=user_message,
            config=config,
        )

        return resultado

    async def actuar(self, plan: Any) -> list[Senal]:
        """Emite señales basadas en el resultado del motor."""
        from motor.pensar import Pensamiento

        if not isinstance(plan, Pensamiento):
            return []

        señales = []

        # Señal principal: resultado del agente
        señales.append(Senal(
            origen=self.identidad,
            tipo="PRESCRIPCION" if plan.verificacion_score >= 0.7 else "RESUMEN",
            modo="proceso",
            fuente="propiocepcion_motora",
            payload={
                "funcion": self.funcion,
                "texto": plan.texto[:500],
                "modelo": plan.modelo,
                "verificacion_score": plan.verificacion_score,
                "coste_usd": plan.coste_usd,
            },
            tenant_id=self.tenant_id,
        ))

        # Escribir resultado en pizarra estado
        await self.pizarra.escribir(
            "estado",
            f"ultimo_resultado_{self.funcion}",
            {
                "texto": plan.texto[:200],
                "score": plan.verificacion_score,
                "modelo": plan.modelo,
                "timestamp": plan.tiempo_ms,
            },
            notificar=True,
        )

        return señales

    async def aprender(self, resultado: list[Senal]) -> None:
        """Registra resultado en pizarra evolución."""
        if not resultado:
            return

        for s in resultado:
            if s.tipo == "PRESCRIPCION":
                await self.pizarra.escribir(
                    "evolucion",
                    f"ciclo_{self.funcion}",
                    {
                        "verificacion_score": s.payload.get("verificacion_score", 0),
                        "coste": s.payload.get("coste_usd", 0),
                    },
                )

    def __repr__(self):
        return f"<AgenteFuncional:{self.funcion} tenant={self.tenant_id}>"
