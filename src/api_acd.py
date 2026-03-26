"""API de Ingeniería Lingüística ACD.

Endpoints:
  POST /acd/analizar     → Analiza estructura ACD de un texto
  POST /acd/predecir     → Predice qué efecto tendrá un texto
  GET  /acd/recetas      → Devuelve recetas estructura→efecto
  GET  /acd/correlaciones → Correlaciones descubiertas
  GET  /acd/stats        → Estadísticas del corpus
  POST /acd/generar      → Genera texto optimizado para un efecto
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

# Paths
MOTOR_DIR = Path(__file__).parent.parent
CORPUS_DIR = MOTOR_DIR / "corpus"
CORPUS_FILE = CORPUS_DIR / "corpus.jsonl"
CORRELACIONES_FILE = CORPUS_DIR / "correlaciones.json"
RECETAS_FILE = CORPUS_DIR / "recetas.json"

sys.path.insert(0, str(MOTOR_DIR / "scripts"))

router = APIRouter(prefix="/acd", tags=["acd"])


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _cargar_corpus() -> list[dict]:
    if not CORPUS_FILE.exists():
        return []
    entradas = []
    for line in CORPUS_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                entradas.append(json.loads(line))
            except Exception:
                continue
    return entradas


def _cargar_correlaciones() -> list[dict]:
    if not CORRELACIONES_FILE.exists():
        return []
    try:
        return json.loads(CORRELACIONES_FILE.read_text())
    except Exception:
        return []


def _cargar_recetas() -> list[dict]:
    if not RECETAS_FILE.exists():
        return []
    try:
        return json.loads(RECETAS_FILE.read_text())
    except Exception:
        return []


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/analizar")
async def analizar_texto(request: Request):
    """Analiza la estructura ACD de un texto.

    Body: {"texto": "..."}
    Returns: estructura ACD + diagnóstico + métricas
    """
    body = await request.json()
    texto = body.get("texto", "")
    if not texto:
        raise HTTPException(400, "Campo 'texto' requerido")

    try:
        from core.perceptor import percibir
        from core.razonador import razonar
        from core.corpus import extraer_metricas
    except ImportError:
        raise HTTPException(500, "Módulos ACD no disponibles")

    # Percibir
    estructura = await percibir(texto[:2000])
    if "error" in estructura:
        raise HTTPException(500, f"Error percepción: {estructura['error']}")

    # Razonar
    diag = razonar(estructura)
    diag_dict = {
        "salud": diag.salud,
        "n_hallazgos": len(diag.hallazgos),
        "n_falacias": len(diag.falacias_detectadas),
        "n_lentes": len(diag.lentes_cubiertas),
        "lentes": diag.lentes_cubiertas,
        "n_modos": len(diag.modos_presentes),
        "resolucion": {"nivel": diag.nivel_luminico, "score": diag.resolucion_luminica},
        "hallazgos": [
            {"tipo": h.tipo, "operacion": h.operacion, "severidad": h.severidad,
             "descripcion": h.descripcion[:200]}
            for h in diag.hallazgos[:10]
        ],
        "oracion_sistema": diag.oracion_sistema,
    }

    # Métricas
    metricas = extraer_metricas(estructura, diag_dict)

    return {
        "texto": texto[:200],
        "estructura": estructura,
        "diagnostico": diag_dict,
        "metricas": {k: round(v, 3) for k, v in metricas.items()},
    }


@router.post("/predecir")
async def predecir_efecto(request: Request):
    """Predice qué efecto tendrá un texto basándose en el corpus.

    Body: {"texto": "..."}
    Returns: predicciones de persuasion, credibilidad, accion, empatia
    """
    body = await request.json()
    texto = body.get("texto", "")
    if not texto:
        raise HTTPException(400, "Campo 'texto' requerido")

    try:
        from core.corpus import predecir_efecto as _predecir
        resultado = await _predecir(texto)
    except ImportError:
        raise HTTPException(500, "Módulos ACD no disponibles")

    if "error" in resultado:
        raise HTTPException(500, resultado["error"])

    return resultado


@router.get("/recetas")
async def get_recetas():
    """Devuelve las recetas estructura→efecto descubiertas por el corpus."""
    recetas = _cargar_recetas()
    if not recetas:
        raise HTTPException(404, "Sin recetas. Ejecutar: python3 -m scripts.core.corpus recetas")
    return {"recetas": recetas, "n_recetas": len(recetas)}


@router.get("/correlaciones")
async def get_correlaciones():
    """Devuelve las correlaciones significativas descubiertas."""
    corrs = _cargar_correlaciones()
    significativas = [c for c in corrs if c.get("p_significativo")]
    return {
        "total": len(corrs),
        "significativas": len(significativas),
        "top_10": significativas[:10],
        "todas": significativas,
    }


@router.get("/stats")
async def get_stats():
    """Estadísticas del corpus ACD."""
    corpus = _cargar_corpus()
    if not corpus:
        return {"n_textos": 0, "categorias": {}}

    cats = defaultdict(int)
    efectos_promedio = defaultdict(list)
    for e in corpus:
        cats[e.get("categoria", "?")] += 1
        for dim, val in e.get("efecto", {}).items():
            try:
                efectos_promedio[dim].append(float(val))
            except:
                pass

    promedios = {dim: round(sum(vals) / len(vals), 2) for dim, vals in efectos_promedio.items()}

    corrs = _cargar_correlaciones()
    recetas = _cargar_recetas()

    return {
        "n_textos": len(corpus),
        "categorias": dict(sorted(cats.items(), key=lambda x: -x[1])),
        "efectos_promedio": promedios,
        "n_correlaciones_significativas": len([c for c in corrs if c.get("p_significativo")]),
        "n_recetas": len(recetas),
    }


@router.post("/generar")
async def generar_texto(request: Request):
    """Genera texto optimizado para un efecto deseado usando las recetas ACD.

    Body: {"efecto": "credibilidad", "contexto": "email para cliente que no viene"}
    Returns: texto generado + métricas ACD del texto
    """
    body = await request.json()
    efecto_deseado = body.get("efecto", "")
    contexto = body.get("contexto", "")

    if not efecto_deseado:
        raise HTTPException(400, "Campo 'efecto' requerido (persuasion|credibilidad|accion|empatia)")

    # Buscar receta
    recetas = _cargar_recetas()
    receta = next((r for r in recetas if r["efecto"] == efecto_deseado), None)
    if not receta:
        raise HTTPException(404, f"Sin receta para '{efecto_deseado}'. Disponibles: {[r['efecto'] for r in recetas]}")

    # Construir prompt con la receta
    ingredientes_texto = "\n".join(
        f"- {ing['metrica']}: {'ALTO' if ing['direccion'] == 'alto' else 'BAJO'} "
        f"(valor óptimo: {ing['valor_optimo']}, importancia: {ing['importancia']})"
        for ing in receta.get("ingredientes", [])
    )

    try:
        from core.perceptor import percibir
        from core.razonador import razonar
        from core.corpus import extraer_metricas

        import httpx, os
        ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))

        system = f"""Genera un texto que MAXIMICE {efecto_deseado}.

RECETA ESTRUCTURAL (basada en corpus de {len(_cargar_corpus())} textos analizados):
{ingredientes_texto}

REGLAS:
1. Sujeto concreto (nombre o rol, nunca "se debería")
2. Verbos con objeto concreto
3. Datos en vez de adjetivos vacíos
4. Decir CÓMO, no solo QUÉ
5. Sin falacias (sin sujetos falsos, sin causalidades circulares)

Genera SOLO el texto. Sin explicaciones."""

        user = f"Contexto: {contexto}" if contexto else f"Genera un texto que maximice {efecto_deseado}"

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            data = r.json()
            texto_generado = data.get("content", [{}])[0].get("text", "")

        # Analizar el texto generado con ACD
        estructura = await percibir(texto_generado[:2000])
        diag = razonar(estructura) if "error" not in estructura else None
        diag_dict = {}
        if diag:
            diag_dict = {
                "salud": diag.salud,
                "n_falacias": len(diag.falacias_detectadas),
                "n_lentes": len(diag.lentes_cubiertas),
                "resolucion": diag.nivel_luminico,
            }
        metricas = extraer_metricas(estructura, diag_dict) if "error" not in estructura else {}

        return {
            "texto": texto_generado,
            "efecto_objetivo": efecto_deseado,
            "receta_usada": receta["ingredientes"][:5],
            "metricas_resultado": {k: round(v, 3) for k, v in metricas.items()},
            "salud_acd": diag_dict.get("salud", "?"),
        }

    except ImportError:
        raise HTTPException(500, "Módulos ACD no disponibles")
