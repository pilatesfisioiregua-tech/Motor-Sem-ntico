"""Entry point: entrena los 4 modelos C1-C4 desde datos Reactor v1."""
import json
import time
import structlog
from pathlib import Path

from src.models import router_embeddings, clasificador, compositor_weights, scorer

log = structlog.get_logger()

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sinteticos"


def _load_json(filename: str) -> list[dict]:
    """Carga un JSON de datos sintéticos."""
    path = DATA_DIR / filename
    if not path.exists():
        log.warning("data_not_found", file=str(path))
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return []


def train_all() -> dict:
    """Entrena los 4 modelos. Devuelve resultados con métricas."""
    t0 = time.time()

    # Cargar datos
    b1 = _load_json("b1_casos.json")
    b2 = _load_json("b2_peticiones.json")
    b3 = _load_json("b3_composicion.json")
    b4 = _load_json("b4_scoring.json")

    log.info("datos_cargados", b1=len(b1), b2=len(b2), b3=len(b3), b4=len(b4))

    resultados: list[dict] = []

    # C1: Router Embeddings
    log.info("entrenando_c1")
    try:
        r1 = router_embeddings.train(b1, b2)
        resultados.append(r1)
        log.info("c1_completado", **{k: v for k, v in r1.items() if k != "archivo"})
    except Exception as e:
        log.error("c1_error", error=str(e))
        resultados.append({"modelo": "C1_router_embeddings", "error": str(e), "cumple": False})

    # C2: Clasificador Multi-label
    log.info("entrenando_c2")
    try:
        r2 = clasificador.train(b2)
        resultados.append(r2)
        log.info("c2_completado", **{k: v for k, v in r2.items() if k != "archivo"})
    except Exception as e:
        log.error("c2_error", error=str(e))
        resultados.append({"modelo": "C2_clasificador", "error": str(e), "cumple": False})

    # C3: Compositor Weights
    log.info("entrenando_c3")
    try:
        r3 = compositor_weights.train(b3)
        resultados.append(r3)
        log.info("c3_completado", **{k: v for k, v in r3.items() if k != "archivo"})
    except Exception as e:
        log.error("c3_error", error=str(e))
        resultados.append({"modelo": "C3_compositor_weights", "error": str(e), "cumple": False})

    # C4: Scorer
    log.info("entrenando_c4")
    try:
        r4 = scorer.train(b4)
        resultados.append(r4)
        log.info("c4_completado", **{k: v for k, v in r4.items() if k != "archivo"})
    except Exception as e:
        log.error("c4_error", error=str(e))
        resultados.append({"modelo": "C4_scorer", "error": str(e), "cumple": False})

    tiempo_total = round(time.time() - t0, 2)
    cumplen = sum(1 for r in resultados if r.get("cumple", False))

    return {
        "resultados": resultados,
        "modelos_entrenados": len(resultados),
        "criterios_cumplidos": cumplen,
        "criterios_total": 4,
        "tiempo_s": tiempo_total,
        "datos": {"b1": len(b1), "b2": len(b2), "b3": len(b3), "b4": len(b4)},
    }
