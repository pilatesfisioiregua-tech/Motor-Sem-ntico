"""Flags de peligro oculto — detectan estados que métricas convencionales no ven.

Fuente: FRAMEWORK_ACD.md §3.3, §5 Paso 3.
3 flags:
  1. Autómata oculto: S↑ + C↑ + Se↓ — parece sano, es frágil
  2. Monopolio Se: una F con Se alto, resto Se bajo — rigidez de sentido
  3. Zona tóxica: Se_avg < 0.25 — cualquier operación que no inyecte Se es inerte o tóxica
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FlagPeligro:
    nombre: str
    detectado: bool
    detalle: str
    severidad: str  # "critico", "alto", "medio"


def es_automata_oculto(lentes: dict[str, float]) -> FlagPeligro:
    """S>0.60 + C>0.60 + Se<0.30 → sistema que parece sano pero es frágil.

    Invisible para métricas convencionales. Solo Se lo detecta.
    Ejemplos: Boeing pre-737MAX, Maginot pre-1940.
    """
    s = lentes.get("salud", 0)
    se = lentes.get("sentido", 0)
    c = lentes.get("continuidad", 0)

    detectado = s >= 0.60 and c >= 0.60 and se < 0.30

    if detectado:
        detalle_msg = "PELIGRO: Sistema parece sano pero Se<0.30. Frágil ante cambio de contexto."
    else:
        detalle_msg = "No detectado."

    return FlagPeligro(
        nombre="automata_oculto",
        detectado=detectado,
        detalle="S={:.2f} C={:.2f} Se={:.2f}. {}".format(s, c, se, detalle_msg),
        severidad="critico" if detectado else "ninguno",
    )


def es_monopolio_se(scores_f_se: dict[str, float]) -> FlagPeligro:
    """Una función con Se>0.70 + resto Se<0.30 → sentido concentrado en un punto.

    Args:
        scores_f_se: dict con {F1: se_score, F2: se_score, ...} — score de Se por función.
                     Si no se tienen scores por función, pasar dict vacío.
    """
    if not scores_f_se:
        return FlagPeligro(
            nombre="monopolio_se",
            detectado=False,
            detalle="Sin datos de Se por función.",
            severidad="ninguno",
        )

    valores = list(scores_f_se.values())
    max_se = max(valores)
    otras = [v for v in valores if v < max_se]

    detectado = max_se > 0.70 and all(v < 0.30 for v in otras)

    if detectado:
        funcion_monopolio = max(scores_f_se, key=scores_f_se.get)
        detalle_msg = "PELIGRO: Se concentrado en {} ({:.2f}). Resto < 0.30. Rigidez de sentido.".format(
            funcion_monopolio, max_se)
    else:
        detalle_msg = "Se distribuido normalmente."

    return FlagPeligro(
        nombre="monopolio_se",
        detectado=detectado,
        detalle=detalle_msg,
        severidad="alto" if detectado else "ninguno",
    )


def es_zona_toxica(lentes: dict[str, float]) -> FlagPeligro:
    """Se_avg < 0.25 → cualquier operación que no inyecte Se es inerte o tóxica.

    Elemento absorbente del álgebra: Se baja absorbe cualquier intervención.
    """
    se = lentes.get("sentido", 0)

    detectado = se < 0.25

    if detectado:
        detalle_msg = "PELIGRO: Se < 0.25. Cualquier operación que no inyecte Se primero será inerte o dañina."
    else:
        detalle_msg = "Se suficiente."

    return FlagPeligro(
        nombre="zona_toxica",
        detectado=detectado,
        detalle="Se_avg={:.2f}. {}".format(se, detalle_msg),
        severidad="critico" if detectado else "ninguno",
    )


def detectar_todos_flags(
    lentes: dict[str, float],
    scores_f_se: dict[str, float] | None = None,
) -> list[FlagPeligro]:
    """Ejecuta los 3 flags y devuelve solo los detectados."""
    flags = [
        es_automata_oculto(lentes),
        es_monopolio_se(scores_f_se or {}),
        es_zona_toxica(lentes),
    ]
    return [f for f in flags if f.detectado]
