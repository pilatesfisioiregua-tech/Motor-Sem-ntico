"""Runner: orquesta las 4 sub-pipelines del Reactor v1."""
import asyncio
import json
import time
from pathlib import Path

import structlog

from src.utils.llm_client import llm
from src.reactor.b1_casos_dominio import generar_casos
from src.reactor.b2_peticiones import generar_peticiones
from src.reactor.b3_composicion import generar_composiciones
from src.reactor.b4_scoring import generar_scoring
from src.reactor.validador import validar

log = structlog.get_logger()

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "sinteticos"


def _guardar(nombre: str, datos: list[dict]) -> Path:
    """Guarda dataset como JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{nombre}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return path


async def run() -> dict:
    """Ejecuta las 4 sub-pipelines en paralelo."""
    t0 = time.time()
    sem = asyncio.Semaphore(5)  # Max 5 calls concurrentes a la API

    log.info("reactor_iniciando")

    # Lanzar B1-B4 en paralelo
    b1_task = asyncio.create_task(generar_casos(sem))
    b2_task = asyncio.create_task(generar_peticiones(sem))
    b3_task = asyncio.create_task(generar_composiciones(sem))
    b4_task = asyncio.create_task(generar_scoring(sem))

    b1, b2, b3, b4 = await asyncio.gather(
        b1_task, b2_task, b3_task, b4_task,
        return_exceptions=True,
    )

    # Manejar errores
    datasets: dict[str, list[dict]] = {}
    for nombre, resultado in [("b1_casos", b1), ("b2_peticiones", b2),
                               ("b3_composicion", b3), ("b4_scoring", b4)]:
        if isinstance(resultado, Exception):
            log.error("reactor_pipeline_error", pipeline=nombre, error=str(resultado))
            datasets[nombre] = []
        else:
            datasets[nombre] = resultado

    # Guardar JSONs
    for nombre, datos in datasets.items():
        path = _guardar(nombre, datos)
        log.info("reactor_guardado", archivo=str(path), items=len(datos))

    # Validar
    resultado_validacion = validar(datasets)

    elapsed = time.time() - t0
    coste = llm.total_cost

    # Reporte final
    print("\n" + "=" * 60)
    print("REACTOR v1 — REPORTE FINAL")
    print("=" * 60)
    print(f"\nItems generados:")
    for nombre, datos in datasets.items():
        print(f"  {nombre}: {len(datos)}")
    print(f"\nTotal: {sum(len(d) for d in datasets.values())} items")
    print(f"Coste: ${coste:.4f}")
    print(f"Tiempo: {elapsed:.1f}s")
    print(f"\nValidación: {resultado_validacion['muestra_total']} items muestreados (10%)")
    print(f"Archivo: {resultado_validacion['archivo']}")
    print("=" * 60)

    return {
        "items": {nombre: len(datos) for nombre, datos in datasets.items()},
        "total": sum(len(d) for d in datasets.values()),
        "coste_usd": round(coste, 4),
        "tiempo_s": round(elapsed, 1),
        "validacion": resultado_validacion,
    }


if __name__ == "__main__":
    asyncio.run(run())
