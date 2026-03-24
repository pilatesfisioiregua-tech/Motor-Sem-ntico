"""Motor de Transferencia Cross-Dominio — Ley 10 TCF.

La transferencia es por SIMILARIDAD DEL GAP, no del dominio.
Un estudio de Pilates con F3 baja tiene más en común con una
clínica dental con F3 baja que con otro estudio con F3 alta.

El MOAT: N organismos × M ciclos = dataset intransferible
de "qué funciona para qué tipo de gap".
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass
from typing import Optional

log = structlog.get_logger()


@dataclass
class Transferencia:
    """Una receta transferible entre organismos."""
    origen_tenant: str
    destino_tenant: str
    gap: str                    # "F3_baja", "F6_baja", etc.
    receta: dict                # Receta completa de la pizarra cognitiva
    similaridad: float          # Coseno entre contextos del gap (pgvector)
    confianza: float            # tasa_cierre × similaridad
    evidencia: str              # Texto: "Cerró F3 en wellness_001 con tasa 0.82"
    requiere_cr1: bool = True   # SIEMPRE True — el propietario decide


class MotorTransferencia:
    """Detecta y propone transferencias cross-dominio.

    Flujo:
    1. Recopilar telemetría de todos los organismos
    2. Para cada organismo con gaps activos
    3. Buscar recetas que cerraron ESE gap en OTROS organismos
    4. Calcular similaridad semántica del CONTEXTO (no del dominio)
    5. Proponer en pizarra del tenant destino (CR1 — propietario decide)
    """

    def __init__(self, registry, db_pool):
        self.registry = registry
        self.pool = db_pool

    async def detectar_transferencias(
        self,
        min_tasa_cierre: float = 0.60,
        min_ejecuciones: int = 5,
        min_similaridad: float = 0.85,
    ) -> list[Transferencia]:
        """Busca recetas exitosas transferibles entre organismos."""

        transferencias = []

        # 1. Telemetría de todos los organismos
        tenants = self.registry.listar_tenants()
        telemetrias = []
        for t in tenants:
            tel = await self.registry.obtener_telemetria(t.tenant_id)
            if tel:
                telemetrias.append(tel)

        if len(telemetrias) < 2:
            log.info("cross_tenant_insuficiente", n_tenants=len(telemetrias))
            return []

        # 2. Para cada organismo con gaps activos
        for tel in telemetrias:
            for gap in tel.gaps:
                # 3. Buscar recetas que cerraron ese gap en OTROS organismos
                for otro in telemetrias:
                    if otro.tenant_id == tel.tenant_id:
                        continue

                    for receta in otro.recetas_activas:
                        # ¿Esta receta cerró este gap?
                        if not self._receta_cierra_gap(receta, gap):
                            continue
                        if receta.get("tasa_cierre", 0) < min_tasa_cierre:
                            continue
                        if receta.get("n_ejecuciones", 0) < min_ejecuciones:
                            continue

                        # 4. Similaridad semántica del contexto
                        similaridad = await self._calcular_similaridad(
                            gap_contexto_origen=receta.get("contexto_gap", ""),
                            gap_contexto_destino=self._contexto_gap(tel, gap),
                        )

                        if similaridad >= min_similaridad:
                            transferencias.append(Transferencia(
                                origen_tenant=otro.tenant_id,
                                destino_tenant=tel.tenant_id,
                                gap=gap,
                                receta=receta,
                                similaridad=similaridad,
                                confianza=receta.get("tasa_cierre", 0) * similaridad,
                                evidencia=(
                                    f"Cerró {gap} en {otro.tenant_id} "
                                    f"({otro.sector}) con tasa "
                                    f"{receta.get('tasa_cierre', 0):.2f}"
                                ),
                            ))

        log.info("cross_tenant_transferencias",
                 n_transferencias=len(transferencias),
                 n_tenants=len(telemetrias))
        return transferencias

    async def proponer_mejoras(self, transferencias: list[Transferencia]):
        """PROPONE — nunca ejecuta directo. CR1 por tenant."""
        import json

        async with self.pool.acquire() as conn:
            for t in transferencias:
                await conn.execute("""
                    INSERT INTO om_pizarra (tenant_id, tipo, clave, valor, prioridad, origen)
                    VALUES ($1, 'cognitiva', $2, $3::jsonb, 3, 'ecosistema')
                    ON CONFLICT (tenant_id, tipo, clave, ciclo)
                    DO UPDATE SET valor = $3::jsonb, updated_at = now()
                """,
                    t.destino_tenant,
                    f"propuesta_transfer_{t.gap}",
                    json.dumps({
                        "origen": "ecosistema",
                        "tipo": "transferencia_cross_dominio",
                        "gap": t.gap,
                        "receta_propuesta": t.receta,
                        "evidencia": t.evidencia,
                        "similaridad": t.similaridad,
                        "confianza": t.confianza,
                        "requiere_cr1": True,
                    }),
                )

        log.info("cross_tenant_propuestas_escritas", n=len(transferencias))

    def _receta_cierra_gap(self, receta: dict, gap: str) -> bool:
        """¿Esta receta está dirigida a este gap?"""
        funcion_gap = gap.split("_")[0]  # "F3_baja" → "F3"
        funcion_map = {
            "F1": "conservacion", "F2": "captacion", "F3": "depuracion",
            "F4": "distribucion", "F5": "identidad", "F6": "adaptacion",
            "F7": "replicacion",
        }
        return receta.get("funcion") == funcion_map.get(funcion_gap)

    def _contexto_gap(self, tel: 'TelemetriaOrganismo', gap: str) -> str:
        """Construye contexto semántico del gap para embedding."""
        return f"sector:{tel.sector} tamano:{tel.tamano} gap:{gap} estado:{tel.estado_diagnostico}"

    async def _calcular_similaridad(
        self,
        gap_contexto_origen: str,
        gap_contexto_destino: str,
    ) -> float:
        """Calcula similaridad semántica entre contextos de gap.

        MVP: similaridad basada en sector + gap + estado (reglas).
        Scale: pgvector coseno con embeddings reales (>85%).
        """
        # MVP: heurística basada en gap compartido
        # Cuando tengamos embeddings reales → pgvector coseno
        origen_parts = set(gap_contexto_origen.split())
        destino_parts = set(gap_contexto_destino.split())

        if not origen_parts or not destino_parts:
            return 0.0

        interseccion = len(origen_parts & destino_parts)
        union = len(origen_parts | destino_parts)
        jaccard = interseccion / union if union > 0 else 0.0

        return jaccard
