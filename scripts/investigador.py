#!/usr/bin/env python3
"""Agente Investigador (I+D) — Tercer agente de la fabrica OMNI-MIND.

Explora mercado, competidores, ideas, semillas dormidas y oportunidades.
Lee la vision del repo y genera insights accionables.

Uso:
  python3 scripts/investigador.py                # Ejecuta investigacion
  python3 scripts/investigador.py --semillas      # Explora semillas dormidas
  python3 scripts/investigador.py --competidores  # Analiza competencia
  python3 scripts/investigador.py --idea "..."    # Investiga una idea concreta
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Asegurar imports
sys.path.insert(0, str(Path(__file__).parent))
from agente_base import (
    llamar_llm, leer_doc, crear_tarea, guardar_reporte,
    leer_tareas_pendientes, marcar_tarea, MOTOR_DIR
)

NOMBRE = "investigador"


# ============================================================
# INVESTIGAR MERCADO Y COMPETENCIA
# ============================================================

async def investigar_competencia() -> dict:
    """Analiza el mercado de software para pequenos negocios."""
    vision = leer_doc("VISION_NEGOCIO")
    spec = leer_doc("AGENTE_SPEC")

    system = """Eres un analista de mercado senior especializado en SaaS para pequeños negocios.
Tu trabajo: encontrar GAPS que nadie está cubriendo.

FORMATO DE RESPUESTA (JSON):
{
  "competidores": [
    {"nombre": "X", "precio": "€Y/mes", "fortaleza": "...", "debilidad_clave": "..."}
  ],
  "gaps_mercado": [
    {"gap": "...", "oportunidad": "...", "dificultad": "baja|media|alta", "impacto_revenue": "alto|medio|bajo"}
  ],
  "diferenciador_omni": "1 frase de por qué OMNI-MIND es diferente",
  "accion_inmediata": "La cosa más importante que hacer MAÑANA",
  "precio_sugerido": {"min": N, "max": N, "modelo": "..."}
}"""

    user = f"""VISIÓN DEL PRODUCTO:
{vision[:4000]}

ESPECIFICACIÓN DE AGENTES:
{spec[:2000]}

Analiza el mercado de gestión para estudios de Pilates/Yoga/Fitness/Clínicas.
Competidores principales: Cliniko ($45-95/mes), Mindbody ($139-699/mes), Fresha (gratis+comisiones),
Jane App ($54-114/mes), Glofox, Vagaro, Acuity Scheduling.

Encuentra los GAPS que nadie cubre y donde OMNI-MIND puede ganar.
Responde en JSON."""

    print("  🔍 Investigando mercado y competencia...")
    response = await llamar_llm(system, user)

    try:
        # Parsear JSON
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
        print(f"  ⚠️ Error parseando: {e}")

    return {"raw": response[:2000]}


# ============================================================
# EXPLORAR SEMILLAS E IDEAS
# ============================================================

async def explorar_idea(idea: str) -> dict:
    """Investiga una idea concreta y genera un plan de accion."""
    vision = leer_doc("VISION_NEGOCIO")

    system = """Eres un estratega de producto y tecnología.
Tu trabajo: tomar una idea en bruto y convertirla en un plan ejecutable.

FORMATO (JSON):
{
  "idea_original": "...",
  "idea_refinada": "1 frase clara",
  "viabilidad": 0.0-1.0,
  "por_que_funciona": "...",
  "riesgos": ["..."],
  "plan_72h": [
    {"hora": "0-4h", "accion": "...", "agente": "builder|verificador|investigador|manual"},
    ...
  ],
  "metricas_exito": ["..."],
  "tareas_para_agentes": [
    {"agente": "builder|verificador|traductor", "tarea": "...", "prioridad": 1-10}
  ]
}"""

    user = f"""VISIÓN:
{vision[:3000]}

IDEA A INVESTIGAR:
{idea}

Analiza esta idea. Sé brutalmente honesto sobre viabilidad.
Genera un plan de 72 horas con acciones concretas.
Responde en JSON."""

    print(f"  💡 Investigando idea: {idea[:80]}...")
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
            result = json.loads(clean[start:end])
            # Crear tareas para otros agentes
            for t in result.get("tareas_para_agentes", []):
                crear_tarea(t["agente"], {
                    "tipo": "idea_investigada",
                    "origen": "investigador",
                    "prioridad": t.get("prioridad", 5),
                    "descripcion": t["tarea"],
                    "idea": idea[:200],
                })
            return result
    except Exception as e:
        print(f"  ⚠️ Error: {e}")

    return {"raw": response[:2000]}


# ============================================================
# EXPLORAR SEMILLAS DORMIDAS DEL ECOSISTEMA
# ============================================================

async def explorar_semillas() -> dict:
    """Lee semillas dormidas y propone cuales activar."""
    # Leer archivos de semillas si existen
    semillas_doc = ""
    for path in MOTOR_DIR.rglob("*semilla*"):
        if path.is_file() and path.suffix in (".md", ".yaml", ".sql", ".json"):
            try:
                semillas_doc += f"\n--- {path.name} ---\n{path.read_text()[:2000]}\n"
            except Exception:
                continue

    vision = leer_doc("VISION_NEGOCIO")

    system = """Eres un director de I+D evaluando qué proyectos internos priorizar.
FORMATO (JSON):
{
  "semillas_encontradas": N,
  "recomendaciones": [
    {
      "semilla": "nombre",
      "estado_actual": "...",
      "accion": "activar|esperar|descartar",
      "razon": "...",
      "impacto_negocio": "alto|medio|bajo"
    }
  ],
  "nueva_semilla_propuesta": {
    "nombre": "...",
    "descripcion": "...",
    "por_que": "..."
  }
}"""

    user = f"""VISIÓN:
{vision[:2000]}

SEMILLAS ENCONTRADAS EN EL REPO:
{semillas_doc[:5000] if semillas_doc else "No se encontraron archivos de semillas explícitos."}

Evalúa qué semillas/ideas del ecosistema tienen más potencial de generar revenue.
Propón al menos 1 semilla nueva basada en lo que ves.
Responde en JSON."""

    print("  🌱 Explorando semillas dormidas...")
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
# PROCESAR TAREAS PENDIENTES
# ============================================================

async def procesar_tareas():
    """Procesa tareas pendientes asignadas al investigador."""
    tareas = leer_tareas_pendientes(NOMBRE)
    if not tareas:
        print("  📭 Sin tareas pendientes")
        return

    print(f"  📬 {len(tareas)} tareas pendientes")
    for tarea in tareas:
        tipo = tarea.get("tipo", "")
        desc = tarea.get("descripcion", "")
        print(f"    → [{tipo}] {desc[:60]}")

        if tipo == "investigar_idea":
            resultado = await explorar_idea(desc)
        elif tipo == "investigar_competencia":
            resultado = await investigar_competencia()
        elif tipo == "explorar_semillas":
            resultado = await explorar_semillas()
        else:
            resultado = await explorar_idea(desc)

        marcar_tarea(tarea["_archivo"], "completada", resultado)
        guardar_reporte(NOMBRE, {"tipo": tipo, "resultado": resultado})


# ============================================================
# MAIN
# ============================================================

async def main():
    parser = argparse.ArgumentParser(description="Agente Investigador OMNI-MIND")
    parser.add_argument("--competidores", action="store_true", help="Analizar competencia")
    parser.add_argument("--semillas", action="store_true", help="Explorar semillas dormidas")
    parser.add_argument("--idea", type=str, help="Investigar una idea concreta")
    parser.add_argument("--tareas", action="store_true", help="Procesar tareas pendientes")
    args = parser.parse_args()

    print("=" * 60)
    print("  AGENTE INVESTIGADOR — I+D OMNI-MIND")
    print("=" * 60)

    resultados = {}

    if args.idea:
        resultados["idea"] = await explorar_idea(args.idea)
    elif args.competidores:
        resultados["competencia"] = await investigar_competencia()
    elif args.semillas:
        resultados["semillas"] = await explorar_semillas()
    elif args.tareas:
        await procesar_tareas()
        return
    else:
        # Modo completo: todo
        print("\n📊 FASE 1: Competencia")
        resultados["competencia"] = await investigar_competencia()
        print("\n🌱 FASE 2: Semillas")
        resultados["semillas"] = await explorar_semillas()

    # Guardar reporte
    reporte = guardar_reporte(NOMBRE, resultados)

    # Resumen
    print(f"\n{'=' * 60}")
    print(f"  INVESTIGACIÓN COMPLETADA")
    if "competencia" in resultados:
        comp = resultados["competencia"]
        gaps = comp.get("gaps_mercado", [])
        print(f"  Gaps encontrados: {len(gaps)}")
        print(f"  Diferenciador: {comp.get('diferenciador_omni', '?')[:80]}")
        print(f"  Acción inmediata: {comp.get('accion_inmediata', '?')[:80]}")
    if "idea" in resultados:
        idea = resultados["idea"]
        print(f"  Viabilidad: {idea.get('viabilidad', '?')}")
        print(f"  Idea refinada: {idea.get('idea_refinada', '?')[:80]}")
    print(f"  Reporte: {reporte}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
