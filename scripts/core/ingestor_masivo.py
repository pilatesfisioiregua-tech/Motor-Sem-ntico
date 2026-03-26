#!/usr/bin/env python3
"""Ingestor masivo — Escala el corpus ACD a 10.000+ textos.

Fuentes:
  1. Textos generados por LLM con variación controlada (cheap, fast)
  2. Textos reales con efecto medido (web scraping futuro)

El truco: usar el LLM para generar pares (texto, efecto_estimado) a escala.
Luego el Perceptor+Razonador analiza la estructura ($0.001/texto).
El resultado: mapa estadístico estructura→efecto con N=10K+.

Uso:
  python3 -m scripts.core.ingestor_masivo --n 100    # Genera e ingesta 100 textos
  python3 -m scripts.core.ingestor_masivo --n 1000   # 1000 textos (~$1 en Haiku)
  python3 -m scripts.core.ingestor_masivo --dominio marketing
  python3 -m scripts.core.ingestor_masivo --stats    # Ver estado del corpus
"""
from __future__ import annotations

import asyncio
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.perceptor import percibir
from core.razonador import razonar
from core.corpus import (
    ingestar, cargar_corpus, correlacionar, generar_recetas,
    extraer_metricas, CORPUS_DIR, CORPUS_FILE
)

import httpx
from dotenv import load_dotenv
load_dotenv()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))

# ===================================================================
# DOMINIOS Y VARIACIONES
# ===================================================================

DOMINIOS = {
    "marketing": {
        "contextos": [
            "email de venta para curso online", "landing page de SaaS",
            "post de Instagram para restaurante", "email frío B2B",
            "anuncio de Facebook para e-commerce", "newsletter semanal",
            "descripción de producto en Amazon", "email de carrito abandonado",
            "copy para banner web", "email de bienvenida",
            "push notification de app", "SMS promocional",
            "copy de Google Ads", "bio de LinkedIn empresa",
            "descripción de YouTube", "tweet promocional",
        ],
        "tonos": ["agresivo", "sutil", "datos", "emocional", "urgente", "premium", "casual"],
        "calidades": ["excelente", "mediocre", "terrible", "manipulativo"],
    },
    "educacion": {
        "contextos": [
            "explicar fotosíntesis a niños de 10 años",
            "explicar derivadas a universitarios",
            "tutorial de programación Python",
            "clase de historia sobre la Revolución Francesa",
            "explicar economía básica a adultos",
            "tutorial de cocina paso a paso",
            "explicar cambio climático",
            "clase de anatomía para fisioterapeutas",
            "tutorial de Excel avanzado",
            "explicar inteligencia artificial a no técnicos",
        ],
        "tonos": ["académico", "coloquial", "visual", "narrativo", "técnico"],
        "calidades": ["excelente", "mediocre", "terrible", "aburrido"],
    },
    "negocio": {
        "contextos": [
            "email a cliente que no paga",
            "propuesta de inversión para startup",
            "informe trimestral al board",
            "feedback a empleado sobre rendimiento",
            "comunicado de crisis",
            "email de negociación de precio",
            "propuesta de partnership",
            "email de follow-up post-reunión",
            "reporte de métricas al equipo",
            "pitch de 30 segundos en elevator",
        ],
        "tonos": ["formal", "directo", "empático", "urgente", "estratégico"],
        "calidades": ["excelente", "mediocre", "terrible", "corporativo_vacío"],
    },
    "terapia": {
        "contextos": [
            "respuesta a paciente con ansiedad",
            "intervención en sesión de coaching",
            "feedback sobre patrón de comportamiento",
            "pregunta exploratoria sobre creencias",
            "validación emocional tras pérdida",
            "confrontación terapéutica suave",
            "resumen de sesión para paciente",
            "mensaje de seguimiento entre sesiones",
        ],
        "tonos": ["empático", "directo", "socrático", "validante", "confrontativo"],
        "calidades": ["excelente", "mediocre", "terrible", "frío"],
    },
    "pilates": {
        "contextos": [
            "WhatsApp a cliente que lleva 2 semanas sin venir",
            "email de bienvenida a nuevo cliente",
            "recordatorio de clase mañana",
            "aviso de deuda pendiente",
            "felicitación por 10 clases seguidas",
            "propuesta de cambio de horario",
            "invitación a clase especial",
            "encuesta de satisfacción",
            "aviso de cierre por vacaciones",
            "oferta de plan anual",
        ],
        "tonos": ["personal", "profesional", "urgente", "celebratorio", "informativo"],
        "calidades": ["excelente", "mediocre", "terrible", "genérico"],
    },
}


# ===================================================================
# GENERAR TEXTO + EFECTO ESTIMADO
# ===================================================================

async def generar_texto_con_efecto(dominio: str, contexto: str, tono: str, calidad: str) -> dict:
    """Genera un texto + estima su efecto usando Haiku (barato)."""

    system = """Genera un texto realista y su efecto estimado.
RESPONDE SOLO EN JSON:
{
  "texto": "el texto generado (50-150 palabras, en español)",
  "efecto": {
    "persuasion": 0.0-1.0,
    "credibilidad": 0.0-1.0,
    "accion": 0.0-1.0,
    "empatia": 0.0-1.0
  }
}

REGLAS según calidad:
- "excelente": datos concretos, nombres, CTAs claros, sujetos específicos. Efectos altos (0.7-0.95)
- "mediocre": algo vago pero funcional. Efectos medios (0.3-0.6)
- "terrible": corporate speak, sin datos, sin sujeto, todo abstracto. Efectos bajos (0.02-0.2)
- "manipulativo": falacias, sujetos falsos, urgencia artificial. Persuasión media pero credibilidad baja
- "corporativo_vacío": jerga sin contenido. Todo bajo
- "aburrido": correcto pero sin engagement. Credibilidad media, resto bajo
- "frío": técnicamente correcto pero sin empatía. Credibilidad alta, empatía baja
- "genérico": podría ser de cualquier negocio. Todo medio-bajo

Solo JSON, sin explicaciones."""

    user = f"Dominio: {dominio}\nContexto: {contexto}\nTono: {tono}\nCalidad: {calidad}"

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 512,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        data = r.json()
        if data.get("type") == "error":
            print(f"  ⚠️ API error: {data.get('error', {}).get('message', 'unknown')[:100]}")
            return None
        text = data.get("content", [{}])[0].get("text", "")

    # Parsear JSON
    try:
        clean = text
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
            return {
                "texto": result.get("texto", ""),
                "efecto": result.get("efecto", {}),
                "categoria": f"{dominio}_{tono}_{calidad}",
            }
    except Exception:
        pass

    return None


# ===================================================================
# INGESTIÓN MASIVA
# ===================================================================

async def ingestar_masivo(n: int, dominio: str = None, batch_size: int = 5):
    """Genera e ingesta N textos al corpus.

    Coste estimado:
      - Generación: ~$0.0005/texto (Haiku)
      - Percepción: ~$0.001/texto (Haiku)
      - Total: ~$0.0015/texto → $1.50 por 1000 textos
    """
    corpus_actual = len(cargar_corpus())
    print(f"\n  📊 Corpus actual: {corpus_actual} textos")
    print(f"  🎯 Objetivo: +{n} textos → {corpus_actual + n} total")
    print(f"  💰 Coste estimado: ~${n * 0.0015:.2f}")

    dominios_usar = [dominio] if dominio else list(DOMINIOS.keys())
    generados = 0
    errores = 0

    for i in range(n):
        # Seleccionar dominio, contexto, tono, calidad aleatoriamente
        dom = random.choice(dominios_usar)
        config = DOMINIOS[dom]
        ctx = random.choice(config["contextos"])
        tono = random.choice(config["tonos"])
        calidad = random.choice(config["calidades"])

        try:
            # 1. Generar texto + efecto
            resultado = await generar_texto_con_efecto(dom, ctx, tono, calidad)
            if not resultado or not resultado.get("texto"):
                errores += 1
                continue

            # 2. Ingestar (percibir + razonar + almacenar)
            await ingestar(
                texto=resultado["texto"],
                efecto=resultado["efecto"],
                categoria=resultado["categoria"],
            )
            generados += 1

            if generados % 10 == 0:
                print(f"\n  📈 Progreso: {generados}/{n} ({errores} errores)")

        except Exception as e:
            errores += 1
            print(f"  ❌ Error [{i+1}/{n}]: {type(e).__name__}: {str(e)[:200]}")
            if "rate" in str(e).lower() or "429" in str(e):
                print(f"  ⏳ Rate limited — esperando 5s...")
                await asyncio.sleep(5)
            continue

        # Rate limiting
        await asyncio.sleep(2.0)

    print(f"\n{'=' * 60}")
    print(f"  INGESTIÓN MASIVA COMPLETADA")
    print(f"  Generados: {generados}")
    print(f"  Errores: {errores}")
    print(f"  Corpus total: {len(cargar_corpus())}")
    print(f"{'=' * 60}")

    return generados


# ===================================================================
# MAIN
# ===================================================================

async def main():
    parser = argparse.ArgumentParser(description="Ingestor masivo ACD")
    parser.add_argument("--n", type=int, default=100, help="Número de textos a generar")
    parser.add_argument("--dominio", type=str, help="Dominio específico")
    parser.add_argument("--stats", action="store_true", help="Ver estadísticas")
    parser.add_argument("--recalcular", action="store_true", help="Recalcular correlaciones")
    args = parser.parse_args()

    if args.stats:
        corpus = cargar_corpus()
        from collections import defaultdict
        cats = defaultdict(int)
        for e in corpus:
            cats[e.get("categoria", "?")] += 1

        print(f"\n  📊 CORPUS: {len(corpus)} textos")
        print(f"\n  Categorías:")
        for cat, n in sorted(cats.items(), key=lambda x: -x[1])[:20]:
            print(f"    {cat}: {n}")
        return

    if args.recalcular:
        print("📊 Recalculando correlaciones...")
        corrs = correlacionar()
        sig = [c for c in corrs if c.p_significativo]
        print(f"  {len(sig)} correlaciones significativas")
        print("\n🧪 Generando recetas...")
        recetas = generar_recetas()
        print(f"  {len(recetas)} recetas generadas")
        return

    print("=" * 60)
    print("  INGESTOR MASIVO — Corpus ACD")
    print(f"  Textos a generar: {args.n}")
    print(f"  Dominio: {args.dominio or 'TODOS'}")
    print("=" * 60)

    await ingestar_masivo(args.n, args.dominio)

    # Recalcular correlaciones
    print("\n📊 Recalculando correlaciones...")
    corrs = correlacionar()
    sig = [c for c in corrs if c.p_significativo]
    print(f"  {len(sig)} correlaciones significativas")

    print("\n🧪 Generando recetas...")
    recetas = generar_recetas()
    print(f"  {len(recetas)} recetas generadas")

    # Top insights
    print(f"\n  🔥 TOP 5:")
    for c in [x for x in corrs if x.p_significativo][:5]:
        emoji = "📈" if c.coeficiente > 0 else "📉"
        print(f"    {emoji} {c.insight}")


if __name__ == "__main__":
    asyncio.run(main())
