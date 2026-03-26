#!/usr/bin/env python3
"""Fabrica OMNI-MIND — Orquestador maestro de todos los agentes.

Ejecuta el loop completo de la fábrica:
  Investigador → Traductor → Builder → Verificador → Pulidor → Loop

Uso:
  python3 scripts/fabrica.py                    # 1 ciclo completo
  python3 scripts/fabrica.py --loop 5           # 5 ciclos
  python3 scripts/fabrica.py --solo verificador # Solo un agente
  python3 scripts/fabrica.py --status           # Estado de la fábrica
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agente_base import (
    guardar_reporte, leer_ultimo_reporte, leer_tareas_pendientes,
    MOTOR_DIR, REPORTS_DIR, TASKS_DIR
)

AGENTES = {
    "verificador": {
        "comando": "python3 scripts/verificador.py --dry-run",
        "descripcion": "Testea E2E, encuentra fallos",
        "timeout": 120,
        "orden": 1,
    },
    "builder": {
        "comando": "python3 scripts/builder.py --loop 1",
        "descripcion": "Arregla bugs, deploya fixes",
        "timeout": 300,
        "orden": 2,
    },
    "investigador": {
        "comando": "python3 scripts/investigador.py",
        "descripcion": "I+D, mercado, semillas",
        "timeout": 120,
        "orden": 3,
    },
    "traductor": {
        "comando": "python3 scripts/traductor.py --despachar",
        "descripcion": "Orquesta y traduce",
        "timeout": 180,
        "orden": 4,
    },
}


def ejecutar_agente(nombre: str, config: dict) -> dict:
    """Ejecuta un agente y devuelve resultado."""
    print(f"\n{'─' * 50}")
    print(f"  🤖 {nombre.upper()} — {config['descripcion']}")
    print(f"  $ {config['comando']}")
    print(f"{'─' * 50}")

    start = time.time()
    try:
        result = subprocess.run(
            config["comando"], shell=True,
            capture_output=True, text=True,
            cwd=str(MOTOR_DIR),
            timeout=config.get("timeout", 120),
            env={**os.environ},
        )
        duracion = round(time.time() - start, 1)

        # Mostrar output resumido
        output = result.stdout or ""
        lines = output.strip().split("\n")

        # Mostrar últimas 10 líneas relevantes
        relevantes = [l for l in lines if l.strip() and not l.startswith("  ")][-10:]
        for line in relevantes:
            print(f"  {line}")

        exito = result.returncode == 0
        status = "✅" if exito else "❌"
        print(f"\n  {status} {nombre} completado en {duracion}s")

        return {
            "agente": nombre,
            "exito": exito,
            "duracion_s": duracion,
            "output_tail": "\n".join(lines[-5:]),
        }

    except subprocess.TimeoutExpired:
        duracion = round(time.time() - start, 1)
        print(f"\n  ⏰ {nombre} TIMEOUT ({config['timeout']}s)")
        return {"agente": nombre, "exito": False, "duracion_s": duracion, "error": "timeout"}

    except Exception as e:
        return {"agente": nombre, "exito": False, "error": str(e)}


def mostrar_status():
    """Muestra estado actual de la fábrica."""
    print("\n" + "=" * 60)
    print("  ESTADO DE LA FÁBRICA OMNI-MIND")
    print("=" * 60)

    # Agentes y sus últimos reportes
    for nombre, config in sorted(AGENTES.items(), key=lambda x: x[1]["orden"]):
        reporte = leer_ultimo_reporte(nombre)
        tareas = leer_tareas_pendientes(nombre)

        status = "🟢" if reporte else "⚪"
        fecha = ""
        if reporte and isinstance(reporte, dict):
            fecha = reporte.get("timestamp", "")[:16] if "timestamp" in reporte else ""

        print(f"\n  {status} {nombre.upper()}")
        print(f"    Descripción: {config['descripcion']}")
        print(f"    Tareas pendientes: {len(tareas)}")
        if reporte:
            # Extraer info útil según agente
            if nombre == "verificador":
                print(f"    Último run: {json.dumps(reporte, ensure_ascii=False)[:150]}")
            else:
                print(f"    Último reporte: disponible")

    # Tareas totales
    total_tareas = 0
    for carpeta in TASKS_DIR.iterdir():
        if carpeta.is_dir():
            total_tareas += len(leer_tareas_pendientes(carpeta.name))

    print(f"\n{'─' * 60}")
    print(f"  Total tareas pendientes: {total_tareas}")
    print(f"  Reportes en: {REPORTS_DIR}")
    print(f"  Tareas en: {TASKS_DIR}")
    print(f"{'─' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Fábrica OMNI-MIND")
    parser.add_argument("--loop", type=int, default=1, help="Número de ciclos")
    parser.add_argument("--solo", type=str, help="Ejecutar solo un agente")
    parser.add_argument("--status", action="store_true", help="Ver estado")
    parser.add_argument("--sin", type=str, nargs="*", help="Excluir agentes")
    args = parser.parse_args()

    if args.status:
        mostrar_status()
        return

    print("\n" + "━" * 60)
    print("  🏭 FÁBRICA OMNI-MIND")
    print(f"  Ciclos: {args.loop}")
    print(f"  Hora: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("━" * 60)

    excluir = set(args.sin or [])

    for ciclo in range(1, args.loop + 1):
        print(f"\n{'━' * 60}")
        print(f"  CICLO {ciclo}/{args.loop}")
        print(f"{'━' * 60}")

        resultados_ciclo = {}

        if args.solo:
            # Solo un agente
            if args.solo in AGENTES:
                resultados_ciclo[args.solo] = ejecutar_agente(args.solo, AGENTES[args.solo])
            else:
                print(f"  ❌ Agente '{args.solo}' no existe. Disponibles: {list(AGENTES.keys())}")
                return
        else:
            # Todos los agentes en orden
            for nombre, config in sorted(AGENTES.items(), key=lambda x: x[1]["orden"]):
                if nombre in excluir:
                    print(f"\n  ⏭️ {nombre} excluido")
                    continue
                resultados_ciclo[nombre] = ejecutar_agente(nombre, config)

        # Resumen del ciclo
        print(f"\n{'═' * 60}")
        print(f"  RESUMEN CICLO {ciclo}")
        exitos = sum(1 for r in resultados_ciclo.values() if r.get("exito"))
        total = len(resultados_ciclo)
        print(f"  Agentes: {exitos}/{total} exitosos")
        for nombre, res in resultados_ciclo.items():
            status = "✅" if res.get("exito") else "❌"
            dur = res.get("duracion_s", "?")
            print(f"    {status} {nombre} ({dur}s)")
        print(f"{'═' * 60}")

        # Guardar reporte del ciclo
        guardar_reporte("fabrica", {
            "ciclo": ciclo,
            "timestamp": datetime.now().isoformat(),
            "resultados": resultados_ciclo,
        })

        if ciclo < args.loop:
            print(f"\n  ⏳ Siguiente ciclo en 15s...")
            time.sleep(15)

    print(f"\n{'━' * 60}")
    print(f"  🏭 FÁBRICA COMPLETADA — {args.loop} ciclos")
    print(f"{'━' * 60}")


if __name__ == "__main__":
    main()
