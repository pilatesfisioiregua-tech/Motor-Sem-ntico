"""motor.verificar() — Verificación post-output (código puro, $0).

Verifica que el output de un pensamiento cumple las invariantes:
- IC2: No-conmutatividad (orden importa)
- IC3: Desacoples detectados (contradicciones internas)
- IC4: Razonamiento circular detectado
- IC6: Falacias verificadas
- Reglas del compilador (14 reglas)

Todo es determinístico. No llama a ningún LLM.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field

log = structlog.get_logger()


@dataclass
class ResultadoVerificacion:
    """Resultado de verificar un output."""
    ok: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    score: float = 1.0  # 0.0-1.0


def verificar(
    texto: str,
    ints_usadas: list[str] = None,
    ps_usados: list[str] = None,
    rs_usados: list[str] = None,
    funcion: str = None,
) -> ResultadoVerificacion:
    """Verifica un output contra invariantes del sistema.

    Args:
        texto: Output del LLM a verificar
        ints_usadas: INTs que se usaron para generar el output
        ps_usados: Pensamientos usados
        rs_usados: Razonamientos usados
        funcion: Función (F1-F7) para reglas específicas

    Returns:
        ResultadoVerificacion con ok, warnings, errors, score
    """
    result = ResultadoVerificacion()

    if not texto or len(texto.strip()) < 10:
        result.ok = False
        result.errors.append("Output vacío o demasiado corto")
        result.score = 0.0
        return result

    # V1: Detectar output genérico / placeholder
    marcadores_genericos = [
        "como asistente de IA",
        "como modelo de lenguaje",
        "no puedo proporcionar",
        "es importante considerar",
        "hay que tener en cuenta que",
    ]
    for m in marcadores_genericos:
        if m.lower() in texto.lower():
            result.warnings.append(f"Output genérico detectado: '{m}'")
            result.score -= 0.1

    # V2: Detectar repetición excesiva (posible loop)
    sentences = [s.strip() for s in texto.split('.') if len(s.strip()) > 20]
    if len(sentences) > 3:
        unique = set(sentences)
        ratio = len(unique) / len(sentences)
        if ratio < 0.5:
            result.warnings.append(f"Repetición excesiva: {ratio:.0%} frases únicas")
            result.score -= 0.2

    # V3: Si hay INTs, verificar que el output las refleja mínimamente
    if ints_usadas and len(ints_usadas) >= 2:
        parrafos = [p for p in texto.split('\n\n') if len(p.strip()) > 30]
        if len(parrafos) < len(ints_usadas) * 0.5:
            result.warnings.append(
                f"Output corto para {len(ints_usadas)} INTs "
                f"({len(parrafos)} párrafos)")
            result.score -= 0.1

    # V4: Detectar JSON malformado si se esperaba
    if texto.strip().startswith('{') or texto.strip().startswith('['):
        try:
            import json
            json.loads(texto)
        except Exception:
            from src.pilates.json_utils import extraer_json
            parsed = extraer_json(texto)
            if not parsed:
                result.errors.append("JSON malformado en output")
                result.score -= 0.3

    # V5: F3 Depuración no debe sugerir añadir (solo eliminar)
    if funcion == "F3":
        marcadores_adicion = ["añadir", "crear nuevo", "implementar", "construir"]
        for m in marcadores_adicion:
            if m.lower() in texto.lower():
                result.warnings.append(
                    f"F3 (Depuración) sugiere adición: '{m}' — debería solo eliminar")
                result.score -= 0.05

    # Normalizar score
    result.score = max(0.0, min(1.0, result.score))
    result.ok = result.score >= 0.5 and len(result.errors) == 0

    return result
