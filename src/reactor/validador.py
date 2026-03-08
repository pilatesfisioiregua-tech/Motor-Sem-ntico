"""Validador: muestrea 10% aleatorio para revisión humana."""
import json
import random
from pathlib import Path

import structlog

log = structlog.get_logger()

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "sinteticos" / "validacion"


def validar(datasets: dict[str, list[dict]]) -> dict:
    """Muestrea 10% de cada dataset y genera archivo para revisión humana."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    muestra: list[dict] = []
    stats: dict[str, dict] = {}

    for nombre, items in datasets.items():
        n_muestra = max(1, len(items) // 10)
        seleccion = random.sample(items, min(n_muestra, len(items)))
        for item in seleccion:
            muestra.append({
                "dataset": nombre,
                "item": item,
                "validacion": None,
                "correccion": None,
            })
        stats[nombre] = {
            "total": len(items),
            "muestreados": len(seleccion),
        }

    output_path = OUTPUT_DIR / "muestra_10pct.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(muestra, f, ensure_ascii=False, indent=2)

    log.info("validador_completo",
             total_muestreados=len(muestra),
             archivo=str(output_path),
             stats=stats)

    return {
        "muestra_total": len(muestra),
        "archivo": str(output_path),
        "stats": stats,
    }
