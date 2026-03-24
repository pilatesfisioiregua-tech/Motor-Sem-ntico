"""Reactor v4 — Detecta patrones en telemetría real.

Lee diagnosticos + ejecuciones de DB. Detecta:
1. Estados más frecuentes → ¿estamos cubriendo los perfiles comunes?
2. Transiciones reales → ¿se cumplen las transiciones teóricas (§3.2)?
3. Prescripciones que funcionan → ¿qué INT×P×R realmente cierran gaps?
4. Brechas de cobertura → ¿hay estados sin prescripción efectiva?

Maestro V4 §8.3, §8.4.
Cadencia: manual (v0), post-N-ejecuciones (v1).
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field
from collections import defaultdict

log = structlog.get_logger()


@dataclass
class PatronTelemetria:
    """Un patrón detectado en datos reales."""
    tipo: str                # 'transicion', 'prescripcion_efectiva', 'brecha', 'recurrencia'
    descripcion: str
    datos: dict = field(default_factory=dict)
    confianza: float = 0.0  # 0-1, basado en N observaciones
    accion_sugerida: str = ""


@dataclass
class InformeReactor:
    """Output del Reactor v4."""
    total_diagnosticos: int = 0
    patrones: list[PatronTelemetria] = field(default_factory=list)
    preguntas_sugeridas: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'total_diagnosticos': self.total_diagnosticos,
            'patrones': [{'tipo': p.tipo, 'descripcion': p.descripcion,
                          'datos': p.datos, 'confianza': p.confianza,
                          'accion_sugerida': p.accion_sugerida}
                         for p in self.patrones],
            'preguntas_sugeridas': self.preguntas_sugeridas,
        }


async def detectar_patrones() -> InformeReactor:
    """Analiza diagnosticos en DB y detecta patrones accionables."""
    from src.db.client import get_pool
    pool = await get_pool()
    informe = InformeReactor()

    async with pool.acquire() as conn:
        informe.total_diagnosticos = await conn.fetchval(
            "SELECT count(*) FROM diagnosticos") or 0

        if informe.total_diagnosticos == 0:
            informe.patrones.append(PatronTelemetria(
                tipo='brecha',
                descripcion='Sin datos — ejecutar pipeline con casos reales primero',
                accion_sugerida='POST /motor/ejecutar con casos reales',
            ))
            return informe

        # === 1. RECURRENCIA DE ESTADOS ===
        rows = await conn.fetch("""
            SELECT estado_pre, count(*) as n,
                   avg(CASE WHEN resultado = 'cierre' THEN 1.0
                            WHEN resultado = 'inerte' THEN 0.5
                            WHEN resultado = 'toxico' THEN 0.0
                            ELSE NULL END) as score_medio
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL
            GROUP BY estado_pre
            HAVING count(*) >= 2
            ORDER BY n DESC
        """)
        for r in rows:
            informe.patrones.append(PatronTelemetria(
                tipo='recurrencia',
                descripcion=f"Estado '{r['estado_pre']}' aparece {r['n']} veces (score medio: {round(float(r['score_medio'] or 0), 2)})",
                datos={'estado': r['estado_pre'], 'n': r['n'], 'score': round(float(r['score_medio'] or 0), 3)},
                confianza=min(r['n'] / 10, 1.0),
                accion_sugerida=f"Optimizar prescripción para '{r['estado_pre']}'" if float(r['score_medio'] or 0) < 0.6 else "Prescripción efectiva — documentar",
            ))

        # === 2. TRANSICIONES REALES ===
        rows = await conn.fetch("""
            SELECT estado_pre, estado_post, resultado, count(*) as n
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL AND estado_post IS NOT NULL
            GROUP BY estado_pre, estado_post, resultado
            ORDER BY n DESC
        """)
        for r in rows:
            informe.patrones.append(PatronTelemetria(
                tipo='transicion',
                descripcion=f"{r['estado_pre']} → {r['estado_post']} ({r['resultado']}, n={r['n']})",
                datos={'de': r['estado_pre'], 'a': r['estado_post'],
                       'resultado': r['resultado'], 'n': r['n']},
                confianza=min(r['n'] / 5, 1.0),
            ))

        # === 3. PRESCRIPCIONES EFECTIVAS ===
        rows = await conn.fetch("""
            SELECT prescripcion, resultado, estado_pre
            FROM diagnosticos
            WHERE prescripcion IS NOT NULL AND resultado = 'cierre'
        """)
        int_cierre = defaultdict(int)
        p_cierre = defaultdict(int)
        r_cierre = defaultdict(int)
        for row in rows:
            try:
                presc = json.loads(row['prescripcion']) if isinstance(row['prescripcion'], str) else row['prescripcion']
                for i in (presc.get('ints') or []):
                    int_cierre[i] += 1
                for p in (presc.get('ps') or []):
                    p_cierre[p] += 1
                for r in (presc.get('rs') or []):
                    r_cierre[r] += 1
            except (json.JSONDecodeError, TypeError):
                pass  # expected

        if int_cierre:
            top_ints = sorted(int_cierre.items(), key=lambda x: -x[1])[:5]
            informe.patrones.append(PatronTelemetria(
                tipo='prescripcion_efectiva',
                descripcion=f"INTs que más cierran: {', '.join(f'{k}({v})' for k,v in top_ints)}",
                datos={'ints': dict(top_ints), 'ps': dict(sorted(p_cierre.items(), key=lambda x: -x[1])[:5]),
                       'rs': dict(sorted(r_cierre.items(), key=lambda x: -x[1])[:5])},
                confianza=min(sum(int_cierre.values()) / 20, 1.0),
            ))

        # === 4. BRECHAS ===
        # Estados sin cierre
        rows = await conn.fetch("""
            SELECT estado_pre
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL
            GROUP BY estado_pre
            HAVING count(*) FILTER (WHERE resultado = 'cierre') = 0
                   AND count(*) >= 2
        """)
        for r in rows:
            informe.patrones.append(PatronTelemetria(
                tipo='brecha',
                descripcion=f"Estado '{r['estado_pre']}' nunca cierra — revisar prescripción",
                datos={'estado': r['estado_pre']},
                confianza=0.8,
                accion_sugerida=f"Rediseñar prescripción para '{r['estado_pre']}'",
            ))

    log.info("reactor_v4_completo",
             diagnosticos=informe.total_diagnosticos,
             patrones=len(informe.patrones))

    return informe
