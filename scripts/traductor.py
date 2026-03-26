#!/usr/bin/env python3
"""Agente Traductor (Mano Derecha) — Meta-agente orquestador de la fabrica.

Es el puente entre Jesus y los agentes. Hace dos cosas:
1. Traduce vision/ideas de Jesus → ordenes precisas para cada agente
2. Traduce resultados de agentes → resumen claro para Jesus

Uso:
  python3 scripts/traductor.py "quiero que el producto sea vendible"
  python3 scripts/traductor.py --resumen           # Resumen del estado de todo
  python3 scripts/traductor.py --despachar          # Lee tareas y las despacha a agentes
  python3 scripts/traductor.py --loop 3             # N ciclos de orquestacion
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
    llamar_llm, leer_doc, crear_tarea, guardar_reporte,
    leer_tareas_pendientes, marcar_tarea, leer_ultimo_reporte,
    MOTOR_DIR, REPORTS_DIR, TASKS_DIR
)

NOMBRE = "traductor"

# ============================================================
# PERFIL DE JESUS — El traductor aprende a entenderle
# ============================================================

PERFIL_JESUS = """
PERFIL DEL CEO (Jesus):
- Piensa en visiones grandes, no en detalles técnicos
- Dice "quiero X" y espera que se ejecute sin preguntas
- Valora la velocidad sobre la perfección
- Le frustra la complejidad innecesaria — quiere resultados
- Su lenguaje: directo, informal, usa "no?" y "oooks" como muletillas
- Cuando dice "podríamos hacer X" → significa "hazlo"
- Cuando dice "se me ha ocurrido" → es una orden con prioridad alta
- Cuando pregunta "qué te parece?" → quiere validación rápida + acción inmediata
- Le importa: revenue, producto vendible, usuarios reales
- NO le importa: arquitectura elegante, código perfecto, documentación extensa
- ODIA: que le pregunten cosas que él ya respondió, over-engineering
"""


# ============================================================
# TRADUCIR VISION → ORDENES
# ============================================================

async def traducir_vision_a_ordenes(mensaje_jesus: str) -> dict:
    """Toma un mensaje de Jesus y genera ordenes precisas para cada agente."""

    # Contexto: que agentes hay y que saben hacer
    agentes_disponibles = """
AGENTES DISPONIBLES:
1. verificador — Testea endpoints E2E, encuentra fallos. Comando: python3 scripts/verificador.py
2. builder — Lee hallazgos del verificador, genera fixes, deploya. Comando: python3 scripts/builder.py --loop N
3. investigador — Escanea mercado, competencia, ideas. Comando: python3 scripts/investigador.py
4. traductor (yo) — Orquesto a los demás y traduzco para Jesús
5. disenador — (pendiente) UX/UI, flujos, estética
6. pulidor — (pendiente) Copy, micro-UX, coherencia de marca
"""

    # Ultimo estado del producto
    ultimo_verificador = leer_ultimo_reporte("verificador")
    ultimo_investigador = leer_ultimo_reporte("investigador")

    estado = "ESTADO ACTUAL DEL PRODUCTO:\n"
    if ultimo_verificador:
        estado += f"- Verificador: {json.dumps(ultimo_verificador.get('resumen', 'sin datos'), ensure_ascii=False)[:300]}\n"
    if ultimo_investigador:
        estado += f"- Investigador: {json.dumps(ultimo_investigador.get('tipo', 'sin datos'), ensure_ascii=False)[:300]}\n"

    system = f"""Eres la mano derecha de Jesús, el CEO de OMNI-MIND.
Tu trabajo: traducir lo que Jesús dice a órdenes EXACTAS para los agentes.

{PERFIL_JESUS}

{agentes_disponibles}

REGLAS:
1. Cada orden debe ser ejecutable sin ambigüedad
2. Asigna prioridad (1=urgente, 10=nice-to-have)
3. Si un agente no existe aún, créale una tarea al builder para construirlo
4. Siempre incluye métricas de éxito ("cómo sabremos que está hecho")
5. Sé conciso — Jesús odia la verbosidad

FORMATO (JSON):
{{
  "interpretacion": "Lo que Jesús realmente quiere (1 frase)",
  "ordenes": [
    {{
      "agente": "nombre",
      "tarea": "descripción precisa",
      "tipo": "fix|investigar|crear|mejorar|analizar",
      "prioridad": 1-10,
      "metrica_exito": "cómo se verifica que está hecho",
      "comando": "comando shell si aplica"
    }}
  ],
  "resumen_para_jesus": "2-3 líneas de qué se va a hacer"
}}"""

    user = f"""{estado}

JESÚS DICE:
"{mensaje_jesus}"

Traduce esto a órdenes precisas para los agentes. JSON."""

    print(f"  🧠 Traduciendo visión → órdenes...")
    response = await llamar_llm(system, user)

    try:
        clean = response
        if "```json" in clean:
            clean = clean.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in clean:
            parts = clean.split("```")
            if len(parts) >= 3:
                clean = parts[1]
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(clean[start:end])
    except Exception as e:
        print(f"  ⚠️ Error: {e}")

    return {"raw": response[:2000]}


# ============================================================
# DESPACHAR ORDENES → TAREAS PARA AGENTES
# ============================================================

async def despachar_ordenes(ordenes: dict) -> int:
    """Convierte ordenes en tareas concretas para cada agente."""
    lista = ordenes.get("ordenes", [])
    despachadas = 0

    for orden in lista:
        agente = orden.get("agente", "")
        if not agente:
            continue

        crear_tarea(agente, {
            "tipo": orden.get("tipo", "tarea"),
            "origen": "traductor",
            "prioridad": orden.get("prioridad", 5),
            "descripcion": orden.get("tarea", ""),
            "metrica_exito": orden.get("metrica_exito", ""),
            "comando": orden.get("comando", ""),
        })
        despachadas += 1

    return despachadas


# ============================================================
# EJECUTAR AGENTES
# ============================================================

async def ejecutar_agente(nombre: str, comando: str = None) -> dict:
    """Ejecuta un agente y devuelve resultado."""
    if not comando:
        comando = f"python3 scripts/{nombre}.py --tareas"

    print(f"  🚀 Ejecutando {nombre}: {comando}")
    try:
        result = subprocess.run(
            comando, shell=True,
            capture_output=True, text=True,
            cwd=str(MOTOR_DIR),
            timeout=300,
            env={**os.environ},
        )
        output = result.stdout[-2000:] if result.stdout else ""
        error = result.stderr[-500:] if result.stderr else ""
        return {
            "agente": nombre,
            "exito": result.returncode == 0,
            "output": output,
            "error": error,
        }
    except subprocess.TimeoutExpired:
        return {"agente": nombre, "exito": False, "error": "TIMEOUT 300s"}
    except Exception as e:
        return {"agente": nombre, "exito": False, "error": str(e)}


# ============================================================
# GENERAR RESUMEN PARA JESUS
# ============================================================

async def generar_resumen() -> dict:
    """Lee todos los reportes y genera un resumen ejecutivo para Jesus."""

    # Recopilar reportes recientes
    reportes = {}
    for agente in ["verificador", "builder", "investigador", "traductor", "disenador", "pulidor"]:
        rep = leer_ultimo_reporte(agente)
        if rep:
            reportes[agente] = json.dumps(rep, ensure_ascii=False)[:1000]

    # Tareas pendientes por agente
    pendientes = {}
    for carpeta in TASKS_DIR.iterdir():
        if carpeta.is_dir():
            tareas = leer_tareas_pendientes(carpeta.name)
            if tareas:
                pendientes[carpeta.name] = len(tareas)

    system = f"""Eres la mano derecha de Jesús.
{PERFIL_JESUS}

Genera un BRIEFING DIARIO ultra-conciso.
Jesús lo leerá en 30 segundos. Sin bullshit.

FORMATO (JSON):
{{
  "estado_producto": "1 frase",
  "score_vendible": "N/10",
  "lo_que_funciona": ["..."],
  "lo_que_falla": ["..."],
  "siguiente_accion": "La cosa MÁS importante ahora",
  "estimacion_dias_para_vender": N,
  "bloqueantes": ["..."],
  "resumen_30s": "Resumen en 2-3 líneas como se lo diría un amigo"
}}"""

    user = f"""REPORTES DE AGENTES:
{json.dumps(reportes, ensure_ascii=False)[:4000]}

TAREAS PENDIENTES:
{json.dumps(pendientes, ensure_ascii=False)}

Genera el briefing diario para Jesús. JSON."""

    print("  📊 Generando resumen ejecutivo...")
    response = await llamar_llm(system, user)

    try:
        clean = response
        if "```json" in clean:
            clean = clean.split("```json", 1)[1].split("```", 1)[0]
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(clean[start:end])
    except Exception as e:
        print(f"  ⚠️ Error: {e}")

    return {"raw": response[:2000]}


# ============================================================
# LOOP DE ORQUESTACION
# ============================================================

async def ciclo_orquestacion() -> dict:
    """Un ciclo completo: leer tareas → despachar → ejecutar → reportar."""

    print("\n📋 Leyendo tareas del traductor...")
    tareas = leer_tareas_pendientes(NOMBRE)

    if tareas:
        print(f"  📬 {len(tareas)} tareas pendientes para orquestar")
        for tarea in tareas:
            desc = tarea.get("descripcion", "")
            tipo = tarea.get("tipo", "")

            if tipo == "vision_jesus":
                ordenes = await traducir_vision_a_ordenes(desc)
                await despachar_ordenes(ordenes)
                marcar_tarea(tarea["_archivo"], "completada", ordenes)
            else:
                # Tarea genérica → despachar al agente correcto
                ordenes = await traducir_vision_a_ordenes(desc)
                await despachar_ordenes(ordenes)
                marcar_tarea(tarea["_archivo"], "completada", ordenes)

    # Ejecutar agentes que tengan tareas pendientes
    resultados_agentes = {}
    for agente in ["verificador", "builder", "investigador"]:
        tareas_agente = leer_tareas_pendientes(agente)
        if tareas_agente:
            print(f"\n  📨 {agente} tiene {len(tareas_agente)} tareas")
            if agente == "verificador":
                resultado = await ejecutar_agente(agente, "python3 scripts/verificador.py --dry-run")
            elif agente == "builder":
                resultado = await ejecutar_agente(agente, "python3 scripts/builder.py --loop 1")
            elif agente == "investigador":
                resultado = await ejecutar_agente(agente, "python3 scripts/investigador.py --tareas")
            resultados_agentes[agente] = resultado

    return {"tareas_procesadas": len(tareas), "agentes_ejecutados": resultados_agentes}


# ============================================================
# MAIN
# ============================================================

async def main():
    parser = argparse.ArgumentParser(description="Agente Traductor (Mano Derecha)")
    parser.add_argument("mensaje", nargs="?", help="Mensaje de Jesús para traducir")
    parser.add_argument("--resumen", action="store_true", help="Briefing diario")
    parser.add_argument("--despachar", action="store_true", help="Despachar tareas pendientes")
    parser.add_argument("--loop", type=int, default=0, help="N ciclos de orquestación")
    args = parser.parse_args()

    print("=" * 60)
    print("  AGENTE TRADUCTOR — Mano Derecha de Jesús")
    print("=" * 60)

    if args.mensaje:
        # Traducir visión → órdenes → despachar
        print(f"\n  💬 Jesús dice: \"{args.mensaje[:100]}\"")
        ordenes = await traducir_vision_a_ordenes(args.mensaje)

        print(f"\n  🎯 Interpretación: {ordenes.get('interpretacion', '?')}")
        print(f"\n  📋 Órdenes generadas:")
        for o in ordenes.get("ordenes", []):
            print(f"    [{o.get('prioridad', '?')}] {o.get('agente', '?')} → {o.get('tarea', '?')[:70]}")

        print(f"\n  📨 Despachando órdenes...")
        n = await despachar_ordenes(ordenes)
        print(f"  ✅ {n} tareas creadas para agentes")

        print(f"\n  💬 Para Jesús: {ordenes.get('resumen_para_jesus', '?')}")

        guardar_reporte(NOMBRE, ordenes)

    elif args.resumen:
        resumen = await generar_resumen()
        print(f"\n{'─' * 60}")
        print(f"  BRIEFING PARA JESÚS")
        print(f"{'─' * 60}")
        print(f"  Estado: {resumen.get('estado_producto', '?')}")
        print(f"  Score: {resumen.get('score_vendible', '?')}")
        print(f"  Siguiente: {resumen.get('siguiente_accion', '?')}")
        print(f"\n  {resumen.get('resumen_30s', '')}")
        print(f"{'─' * 60}")
        guardar_reporte(NOMBRE, resumen)

    elif args.despachar or args.loop > 0:
        cycles = max(args.loop, 1)
        for i in range(1, cycles + 1):
            print(f"\n{'━' * 60}")
            print(f"  CICLO {i}/{cycles}")
            print(f"{'━' * 60}")
            resultado = await ciclo_orquestacion()

            if i < cycles:
                print(f"\n  ⏳ Siguiente ciclo en 10s...")
                await asyncio.sleep(10)

        # Resumen final
        resumen = await generar_resumen()
        print(f"\n  📊 Resumen final: {resumen.get('resumen_30s', 'Sin datos')}")
        guardar_reporte(NOMBRE, {"ciclos": cycles, "resumen": resumen})

    else:
        # Sin argumentos → resumen
        resumen = await generar_resumen()
        print(f"\n  {resumen.get('resumen_30s', 'Usa --help para ver opciones')}")


if __name__ == "__main__":
    asyncio.run(main())
