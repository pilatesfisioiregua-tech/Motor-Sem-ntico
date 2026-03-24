"""Cron del organismo — integra Enjambre con CircuitoGomas.

Este modulo es el entry point que conecta:
  - G2 (diagnostico semanal) → Director detecta gaps
  - G4 (prescripcion semanal) → Enjambre ejecuta clusters
  - G6 (aprendizaje cada 50 ejecuciones) → Poda + mejora

Se ejecuta como asyncio task dentro del cron principal de la app.
"""
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime
from zoneinfo import ZoneInfo

from organismo.cognitiva.enjambre import Enjambre
from organismo.cognitiva.director import Director
from organismo.meta.circuito_gomas import CircuitoGomas
from organismo.pizarras.pizarra import PizarraUnificada

log = structlog.get_logger()
MADRID_TZ = ZoneInfo("Europe/Madrid")


class CronOrganismo:
    """Coordinador del ciclo del organismo.

    Integra el Enjambre (cognitiva) con el CircuitoGomas (meta)
    respetando frecuencias de cada goma.
    """

    def __init__(self, tenant_id: str, system_prompts: dict = None,
                 sensor_queries: dict = None):
        self.tenant_id = tenant_id
        self.pizarra = PizarraUnificada(tenant_id)

        # Inicializar capas
        self.circuito = CircuitoGomas(tenant_id)
        self.director = Director(
            tenant_id,
            system_prompts=system_prompts or {},
            sensor_queries=sensor_queries or {},
        )
        self.enjambre = Enjambre(
            tenant_id,
            director=self.director,
            circuito=self.circuito,
        )

        # Registrar gomas con implementaciones
        self._registrar_gomas()

    def _registrar_gomas(self):
        """Conecta las gomas con implementaciones reales."""
        self.circuito.registrar_goma("G1", self._g1_datos_a_senales)
        self.circuito.registrar_goma("G2", self._g2_senales_a_diagnostico)
        self.circuito.registrar_goma("G4", self._g4_busqueda_a_prescripcion)
        self.circuito.registrar_goma("META", self._meta_reparar)

    async def _g1_datos_a_senales(self, datos: any, tenant_id: str) -> list:
        """G1: Recoger datos del negocio via bus percepcion."""
        from organismo.percepcion.bus import BusPercepcion, SensorPizarra
        bus = BusPercepcion(tenant_id=tenant_id)
        bus.registrar(SensorPizarra(
            "estado_organismo", "interocepcion", tenant_id,
            tipo_pizarra="estado",
        ))
        return await bus.recoger()

    async def _g2_senales_a_diagnostico(self, senales: any, tenant_id: str) -> dict:
        """G2: Ejecutar diagnostico ACD sobre senales acumuladas."""
        from motor.diagnosticador import diagnosticar
        # Construir texto del caso desde senales
        if isinstance(senales, list):
            texto = "\n".join(str(s) for s in senales[:10])
        else:
            texto = str(senales)[:2000]
        return await diagnosticar(texto)

    async def _g4_busqueda_a_prescripcion(self, busqueda: any, tenant_id: str) -> list:
        """G4: Enjambre genera prescripciones desde gaps."""
        return await self.enjambre.ciclo()

    async def _meta_reparar(self, datos: any, tenant_id: str) -> dict:
        """META: Intento de reparacion de goma rota."""
        goma_rota = datos.get("goma_rota", "?") if isinstance(datos, dict) else "?"
        error = datos.get("error", "?") if isinstance(datos, dict) else str(datos)

        log.warning("meta.reparando",
                    goma=goma_rota, error=error[:100],
                    tenant=tenant_id)

        # Estrategia simple: resetear estado de la goma rota
        goma = self.circuito.gomas.get(goma_rota)
        if goma:
            from organismo.meta.circuito_gomas import EstadoGoma
            goma.errores_consecutivos = 0
            goma.estado = EstadoGoma.DORMIDA

        return {"reparada": goma_rota, "accion": "reset_estado"}

    async def ejecutar_ciclo_semanal(self):
        """Ejecuta el ciclo semanal completo (G1→G6)."""
        ahora = datetime.now(MADRID_TZ)
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

        log.info("cron.ciclo_semanal_inicio",
                 tenant=self.tenant_id, ciclo=ciclo)

        # Escribir ciclo actual en pizarra temporal
        await self.pizarra.escribir(
            "temporal", "ciclo_actual", {"ciclo": ciclo}, ciclo=ciclo)

        # Reset presupuesto semanal
        from motor.pensar import resetear_presupuesto
        resetear_presupuesto()

        # Ejecutar circuito completo
        resultados = await self.circuito.ciclo_completo()

        log.info("cron.ciclo_semanal_fin",
                 tenant=self.tenant_id, ciclo=ciclo,
                 resultados=len(resultados))

        return resultados

    async def ejecutar_ciclo_rapido(self):
        """Ejecuta solo el enjambre (sin diagnostico completo).

        Util para activaciones intermedias (eventos, alertas).
        """
        return await self.enjambre.ciclo()
