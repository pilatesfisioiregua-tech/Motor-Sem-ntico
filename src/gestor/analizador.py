"""Gestor Loop Lento v0 — Analiza patrones de ejecución.

Consulta datapoints_efectividad + diagnosticos + ejecuciones.
Produce un informe: qué INTs/P/R funcionan, cuáles no, qué podar, qué promover.

Maestro V4 §7.2, §7.3.
Cadencia: manual (v0), periódico (v1).
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field
from collections import defaultdict

log = structlog.get_logger()


@dataclass
class InformeGestor:
    """Output del loop lento."""
    # Estadísticas globales
    total_ejecuciones: int = 0
    total_diagnosticos: int = 0
    total_datapoints: int = 0

    # Por inteligencia
    ints_efectivas: list[dict] = field(default_factory=list)      # [{id, n, score_medio}]
    ints_inefectivas: list[dict] = field(default_factory=list)    # [{id, n, score_medio}]

    # Por estado ACD
    estados_frecuentes: list[dict] = field(default_factory=list)  # [{estado, n, pct}]
    estados_resultados: list[dict] = field(default_factory=list)  # [{estado, cierre, inerte, toxico}]

    # Por modelo
    modelos_efectivos: list[dict] = field(default_factory=list)   # [{modelo, n, score_medio}]

    # Recomendaciones
    podar: list[str] = field(default_factory=list)       # INTs con score < 0.3 consistente
    promover: list[str] = field(default_factory=list)     # INTs con score > 0.7 consistente
    investigar: list[str] = field(default_factory=list)   # Patrones anómalos

    def to_dict(self) -> dict:
        return {
            'total_ejecuciones': self.total_ejecuciones,
            'total_diagnosticos': self.total_diagnosticos,
            'total_datapoints': self.total_datapoints,
            'ints_efectivas': self.ints_efectivas,
            'ints_inefectivas': self.ints_inefectivas,
            'estados_frecuentes': self.estados_frecuentes,
            'estados_resultados': self.estados_resultados,
            'modelos_efectivos': self.modelos_efectivos,
            'podar': self.podar,
            'promover': self.promover,
            'investigar': self.investigar,
        }


async def analizar() -> InformeGestor:
    """Ejecuta el loop lento: consulta DB → produce informe.

    Returns:
        InformeGestor con estadísticas y recomendaciones.
    """
    from src.db.client import get_pool
    pool = await get_pool()
    informe = InformeGestor()

    async with pool.acquire() as conn:
        # === CONTEOS GLOBALES ===
        informe.total_ejecuciones = await conn.fetchval(
            "SELECT count(*) FROM ejecuciones") or 0
        informe.total_diagnosticos = await conn.fetchval(
            "SELECT count(*) FROM diagnosticos") or 0
        informe.total_datapoints = await conn.fetchval(
            "SELECT count(*) FROM datapoints_efectividad") or 0

        # === EFECTIVIDAD POR INT ===
        rows = await conn.fetch("""
            SELECT inteligencia,
                   count(*) as n,
                   avg(score_calidad) as score_medio,
                   avg(CASE WHEN gap_pre > 0 THEN (gap_pre - COALESCE(gap_post, gap_pre)) / gap_pre ELSE 0 END) as tasa_cierre
            FROM datapoints_efectividad
            WHERE score_calidad IS NOT NULL
            GROUP BY inteligencia
            ORDER BY score_medio DESC
        """)
        for r in rows:
            entry = {'id': r['inteligencia'], 'n': r['n'],
                     'score_medio': round(float(r['score_medio'] or 0), 3),
                     'tasa_cierre': round(float(r['tasa_cierre'] or 0), 3)}
            if float(r['score_medio'] or 0) >= 0.7:
                informe.ints_efectivas.append(entry)
                informe.promover.append(r['inteligencia'])
            elif float(r['score_medio'] or 0) < 0.3 and r['n'] >= 3:
                informe.ints_inefectivas.append(entry)
                informe.podar.append(r['inteligencia'])

        # === ESTADOS DIAGNÓSTICOS FRECUENTES ===
        rows = await conn.fetch("""
            SELECT estado_pre, count(*) as n
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL
            GROUP BY estado_pre
            ORDER BY n DESC
        """)
        total_diag = informe.total_diagnosticos or 1
        for r in rows:
            informe.estados_frecuentes.append({
                'estado': r['estado_pre'],
                'n': r['n'],
                'pct': round(r['n'] / total_diag * 100, 1),
            })

        # === RESULTADO POR ESTADO ===
        rows = await conn.fetch("""
            SELECT estado_pre,
                   count(*) FILTER (WHERE resultado = 'cierre') as cierre,
                   count(*) FILTER (WHERE resultado = 'inerte') as inerte,
                   count(*) FILTER (WHERE resultado = 'toxico') as toxico,
                   count(*) as total
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL AND resultado IS NOT NULL
            GROUP BY estado_pre
            ORDER BY total DESC
        """)
        for r in rows:
            informe.estados_resultados.append({
                'estado': r['estado_pre'],
                'cierre': r['cierre'], 'inerte': r['inerte'], 'toxico': r['toxico'],
                'total': r['total'],
                'tasa_cierre': round(r['cierre'] / max(r['total'], 1), 3),
            })

        # === EFECTIVIDAD POR MODELO ===
        rows = await conn.fetch("""
            SELECT modelo, count(*) as n, avg(score_calidad) as score_medio
            FROM datapoints_efectividad
            WHERE score_calidad IS NOT NULL AND modelo IS NOT NULL
            GROUP BY modelo
            ORDER BY score_medio DESC
        """)
        for r in rows:
            informe.modelos_efectivos.append({
                'modelo': r['modelo'], 'n': r['n'],
                'score_medio': round(float(r['score_medio'] or 0), 3),
            })

        # === DETECTAR ANOMALÍAS ===
        # INTs prescritas mucho pero con bajo cierre
        rows = await conn.fetch("""
            SELECT d.estado_pre, d.prescripcion
            FROM diagnosticos d
            WHERE d.resultado = 'toxico' AND d.prescripcion IS NOT NULL
        """)
        toxic_ints = defaultdict(int)
        for r in rows:
            try:
                presc = json.loads(r['prescripcion']) if isinstance(r['prescripcion'], str) else r['prescripcion']
                for int_id in (presc.get('ints') or []):
                    toxic_ints[int_id] += 1
            except (json.JSONDecodeError, TypeError):
                pass  # expected
        for int_id, count in sorted(toxic_ints.items(), key=lambda x: -x[1]):
            if count >= 2:
                informe.investigar.append(
                    f"{int_id} prescrita {count} veces en casos tóxicos")

    log.info("gestor_analisis_completo",
             ejecuciones=informe.total_ejecuciones,
             diagnosticos=informe.total_diagnosticos,
             podar=len(informe.podar),
             promover=len(informe.promover))

    return informe
