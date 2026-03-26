#!/usr/bin/env python3
"""Corpus ACD — Motor de análisis estadístico estructura→efecto.

Ingesta textos + efecto medido → analiza con ACD → almacena → correlaciona.

Pipeline:
  Texto + Efecto → Perceptor → Razonador → Almacén → Correlación

Con N textos analizados, puede responder:
  "¿Qué estructura lingüística produce X efecto?"
  "¿Qué efecto tendrá este texto?"
  "Genera un texto optimizado para este efecto."

Uso:
  python3 -m scripts.core.corpus ingestar --texto "..." --efecto persuasion:0.8
  python3 -m scripts.core.corpus ingestar --archivo textos.jsonl
  python3 -m scripts.core.corpus correlacion
  python3 -m scripts.core.corpus predecir --texto "..."
  python3 -m scripts.core.corpus receta --efecto "persuasion:alta,credibilidad:alta"
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.perceptor import percibir
from core.razonador import razonar, Diagnostico

CORPUS_DIR = Path(__file__).parent.parent.parent / "corpus"
CORPUS_FILE = CORPUS_DIR / "corpus.jsonl"
CORRELACIONES_FILE = CORPUS_DIR / "correlaciones.json"
RECETAS_FILE = CORPUS_DIR / "recetas.json"


# ===================================================================
# TIPOS
# ===================================================================

@dataclass
class EntradaCorpus:
    """Una entrada del corpus: texto + estructura ACD + efecto medido."""
    id: str
    texto: str
    categoria: str                    # email_venta, discurso, producto, educacion, terapia
    efecto: dict                      # {dimension: valor} — ej: {"persuasion": 0.8, "credibilidad": 0.6}
    estructura: dict                  # Output del Perceptor (7 dimensiones ACD)
    diagnostico: dict                 # Output del Razonador (hallazgos, salud, falacias)
    metricas_acd: dict               # Métricas extraídas para correlación
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Correlacion:
    """Correlación entre una métrica ACD y un efecto."""
    metrica: str                      # ej: "agencia", "falacias_count", "salud"
    efecto: str                       # ej: "persuasion", "credibilidad"
    coeficiente: float                # -1.0 a 1.0 (Pearson simplificado)
    n_muestras: int
    p_significativo: bool             # > 10 muestras y |coef| > 0.3
    insight: str                      # Explicación legible


@dataclass
class Receta:
    """Receta estructural: qué métricas ACD producen un efecto deseado."""
    efecto: str
    ingredientes: list                # [{metrica, valor_optimo, importancia}]
    confianza: float                  # 0-1 basada en N muestras y fuerza correlación
    ejemplo_texto: str                # El mejor texto del corpus para este efecto


# ===================================================================
# EXTRAER MÉTRICAS ACD (las variables para correlación)
# ===================================================================

def extraer_metricas(estructura: dict, diagnostico: dict) -> dict:
    """Extrae métricas numéricas de una estructura ACD para correlación estadística.

    Estas son las 'variables independientes' del modelo.
    Cada una es un dial que el texto puede tener alto o bajo.
    """
    sp = estructura.get("sujeto_predicado", {})
    adj = estructura.get("adjetivos", {})
    adv = estructura.get("adverbios", {})
    prep = estructura.get("preposiciones", {})
    conj = estructura.get("conjunciones", {})
    verb = estructura.get("verbo", {})
    sust = estructura.get("sustantivos", {})

    # Métricas del Perceptor (estructura)
    metricas = {
        # Dimensión 1: Agencia
        "agencia": float(sp.get("agencia", 0)),
        "sujeto_concreto": 1.0 if sp.get("sujeto") and len(str(sp.get("sujeto", ""))) > 2 else 0.0,

        # Dimensión 2: Precisión cualitativa
        "precision_adjetivos": float(adj.get("precision", 0)),
        "n_vacios": len(adj.get("vacios", [])),
        "n_cualidades": len(adj.get("cualidades", [])),

        # Dimensión 3: Explicitud operativa
        "explicitud": float(adv.get("explicitud", 0)),
        "n_modos_ocultos": len(adv.get("modos_ocultos", [])),

        # Dimensión 4: Conectividad
        "n_relaciones": len(prep.get("relaciones", [])),
        "n_conexiones_rotas": len(prep.get("conexiones_rotas", [])),
        "n_colapsos": len(prep.get("colapsos", [])),

        # Dimensión 5: Estructura conectiva
        "n_falsas_dicotomias": len(conj.get("falsas_dicotomias", [])),
        "n_causalidades_circulares": len(conj.get("causalidades_circulares", [])),
        "n_piezas_sueltas": len(conj.get("piezas_sueltas", [])),

        # Dimensión 6: Fuerza verbal
        "fuerza_verbo": float(verb.get("fuerza", 0)),
        "produce_resultado": 1.0 if verb.get("produce_resultado") else 0.0,

        # Dimensión 7: Compresión
        "n_perdido": len(sust.get("perdido", [])),
    }

    # Métricas del Razonador (diagnóstico)
    if isinstance(diagnostico, dict):
        metricas.update({
            "salud": float(diagnostico.get("salud", 0)),
            "n_hallazgos": diagnostico.get("n_hallazgos", 0),
            "n_falacias": diagnostico.get("n_falacias", 0),
            "n_lentes": diagnostico.get("n_lentes", 0),
            "n_modos": diagnostico.get("n_modos", 0),
            "resolucion_nivel": {"vela": 0.33, "habitacion": 0.66, "estadio": 1.0}.get(
                diagnostico.get("resolucion", {}).get("nivel", ""), 0.5
            ),
        })

    return metricas


# ===================================================================
# INGESTAR TEXTO
# ===================================================================

async def ingestar(texto: str, efecto: dict, categoria: str = "general") -> EntradaCorpus:
    """Ingesta un texto: analiza con ACD + almacena con efecto medido.

    Args:
        texto: El texto a analizar
        efecto: Dict con dimensiones de efecto medido, ej: {"persuasion": 0.8}
        categoria: Tipo de texto (email_venta, discurso, etc.)

    Returns:
        EntradaCorpus con estructura + diagnóstico + métricas
    """
    # 1. Percibir estructura
    estructura = await percibir(texto[:2000])
    if "error" in estructura:
        print(f"  ⚠️ Error en percepción: {estructura['error']}")
        estructura = {}

    # 2. Razonar sobre estructura
    diag = razonar(estructura) if estructura else None
    diag_dict = {}
    if diag:
        diag_dict = {
            "salud": diag.salud,
            "n_hallazgos": len(diag.hallazgos),
            "n_falacias": len(diag.falacias_detectadas),
            "n_lentes": len(diag.lentes_cubiertas),
            "n_modos": len(diag.modos_presentes),
            "resolucion": {"nivel": diag.nivel_luminico, "score": diag.resolucion_luminica},
            "operaciones_activas": diag.operaciones_detectadas[:5],
        }

    # 3. Extraer métricas para correlación
    metricas = extraer_metricas(estructura, diag_dict)

    # 4. Crear entrada
    entrada = EntradaCorpus(
        id=f"c_{int(time.time()*1000)}",
        texto=texto[:500],  # Guardar solo preview
        categoria=categoria,
        efecto=efecto,
        estructura=estructura,
        diagnostico=diag_dict,
        metricas_acd=metricas,
        timestamp=datetime.now().isoformat(),
    )

    # 5. Almacenar
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_FILE, "a") as f:
        f.write(json.dumps(entrada.to_dict(), ensure_ascii=False) + "\n")

    print(f"  📥 Ingestado: {texto[:50]}... → {efecto}")
    print(f"     Salud ACD: {metricas.get('salud', '?')} | Agencia: {metricas.get('agencia', '?')} | Fuerza: {metricas.get('fuerza_verbo', '?')}")

    return entrada


async def ingestar_batch(textos: list[dict]) -> list[EntradaCorpus]:
    """Ingesta múltiples textos. Cada dict tiene: texto, efecto, categoria."""
    entradas = []
    for i, item in enumerate(textos, 1):
        print(f"\n  [{i}/{len(textos)}]")
        entrada = await ingestar(
            texto=item["texto"],
            efecto=item["efecto"],
            categoria=item.get("categoria", "general"),
        )
        entradas.append(entrada)
        await asyncio.sleep(1.5)  # Rate limiting (1.5s para evitar 429)
    return entradas


# ===================================================================
# CARGAR CORPUS
# ===================================================================

def cargar_corpus() -> list[dict]:
    """Carga todas las entradas del corpus."""
    if not CORPUS_FILE.exists():
        return []
    entradas = []
    for line in CORPUS_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                entradas.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entradas


# ===================================================================
# CORRELACIÓN ESTRUCTURA → EFECTO
# ===================================================================

def correlacionar() -> list[Correlacion]:
    """Calcula correlaciones entre métricas ACD y efectos medidos.

    Para cada par (métrica_acd, dimensión_efecto), calcula correlación.
    Devuelve las correlaciones significativas (|r| > 0.3, N > 5).
    """
    corpus = cargar_corpus()
    if len(corpus) < 5:
        print(f"  ⚠️ Solo {len(corpus)} entradas — necesitas mínimo 5 para correlaciones útiles")
        return []

    # Recopilar todas las dimensiones de efecto
    dimensiones_efecto = set()
    for e in corpus:
        dimensiones_efecto.update(e.get("efecto", {}).keys())

    # Recopilar todas las métricas ACD
    metricas_nombres = set()
    for e in corpus:
        metricas_nombres.update(e.get("metricas_acd", {}).keys())

    correlaciones = []

    for metrica in sorted(metricas_nombres):
        for efecto_dim in sorted(dimensiones_efecto):
            # Extraer pares (x, y) donde ambos existen
            pares = []
            for e in corpus:
                x = e.get("metricas_acd", {}).get(metrica)
                y = e.get("efecto", {}).get(efecto_dim)
                if x is not None and y is not None:
                    try:
                        pares.append((float(x), float(y)))
                    except (TypeError, ValueError):
                        continue

            if len(pares) < 5:
                continue

            # Correlación de Pearson simplificada
            n = len(pares)
            xs = [p[0] for p in pares]
            ys = [p[1] for p in pares]

            mean_x = sum(xs) / n
            mean_y = sum(ys) / n

            cov = sum((x - mean_x) * (y - mean_y) for x, y in pares) / n
            std_x = (sum((x - mean_x) ** 2 for x in xs) / n) ** 0.5
            std_y = (sum((y - mean_y) ** 2 for y in ys) / n) ** 0.5

            if std_x == 0 or std_y == 0:
                continue

            r = cov / (std_x * std_y)
            significativo = abs(r) > 0.3 and n >= 5

            # Generar insight
            if abs(r) > 0.7:
                fuerza = "fuerte"
            elif abs(r) > 0.4:
                fuerza = "moderada"
            else:
                fuerza = "débil"

            direccion = "más" if r > 0 else "menos"

            insight = f"Correlación {fuerza}: {direccion} {metrica} → {direccion} {efecto_dim} (r={r:.2f}, N={n})"

            correlaciones.append(Correlacion(
                metrica=metrica,
                efecto=efecto_dim,
                coeficiente=round(r, 3),
                n_muestras=n,
                p_significativo=significativo,
                insight=insight,
            ))

    # Ordenar por fuerza de correlación
    correlaciones.sort(key=lambda c: abs(c.coeficiente), reverse=True)

    # Guardar
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CORRELACIONES_FILE, "w") as f:
        json.dump([asdict(c) for c in correlaciones], f, ensure_ascii=False, indent=2)

    return correlaciones


# ===================================================================
# GENERAR RECETAS
# ===================================================================

def generar_recetas() -> list[Receta]:
    """Genera recetas estructurales: para cada efecto, qué métricas ACD optimizar.

    Una receta dice: "Para lograr alta persuasión, necesitas: agencia > 0.7,
    fuerza_verbo > 0.8, falacias = 0, explicitud > 0.6"
    """
    corpus = cargar_corpus()
    correlaciones = correlacionar()

    if not correlaciones:
        return []

    # Agrupar correlaciones significativas por efecto
    por_efecto = defaultdict(list)
    for c in correlaciones:
        if c.p_significativo:
            por_efecto[c.efecto].append(c)

    recetas = []

    for efecto, corrs in por_efecto.items():
        # Top correlaciones para este efecto
        top = sorted(corrs, key=lambda c: abs(c.coeficiente), reverse=True)[:5]

        ingredientes = []
        for c in top:
            # Calcular valor óptimo de la métrica para maximizar el efecto
            pares = []
            for e in corpus:
                x = e.get("metricas_acd", {}).get(c.metrica)
                y = e.get("efecto", {}).get(efecto)
                if x is not None and y is not None:
                    try:
                        pares.append((float(x), float(y)))
                    except:
                        continue

            if not pares:
                continue

            # Top 20% por efecto → valor medio de la métrica
            pares.sort(key=lambda p: p[1], reverse=True)
            top_20 = pares[:max(1, len(pares) // 5)]
            valor_optimo = sum(p[0] for p in top_20) / len(top_20)

            ingredientes.append({
                "metrica": c.metrica,
                "valor_optimo": round(valor_optimo, 2),
                "correlacion": c.coeficiente,
                "importancia": round(abs(c.coeficiente), 2),
                "direccion": "alto" if c.coeficiente > 0 else "bajo",
            })

        # Encontrar el mejor texto del corpus para este efecto
        mejor = max(corpus, key=lambda e: float(e.get("efecto", {}).get(efecto, 0)), default=None)
        ejemplo = mejor.get("texto", "")[:200] if mejor else ""

        # Confianza basada en N muestras y fuerza promedio
        n_total = sum(c.n_muestras for c in top) / max(len(top), 1)
        fuerza_media = sum(abs(c.coeficiente) for c in top) / max(len(top), 1)
        confianza = min(1.0, (n_total / 50) * fuerza_media)

        recetas.append(Receta(
            efecto=efecto,
            ingredientes=ingredientes,
            confianza=round(confianza, 2),
            ejemplo_texto=ejemplo,
        ))

    # Guardar
    with open(RECETAS_FILE, "w") as f:
        json.dump([asdict(r) for r in recetas], f, ensure_ascii=False, indent=2)

    return recetas


# ===================================================================
# PREDECIR EFECTO DE UN TEXTO
# ===================================================================

async def predecir_efecto(texto: str) -> dict:
    """Predice qué efecto tendrá un texto basándose en el corpus.

    Analiza estructura ACD → busca textos similares en corpus →
    predice efecto basándose en correlaciones.
    """
    # 1. Analizar estructura
    estructura = await percibir(texto[:2000])
    if "error" in estructura:
        return {"error": estructura["error"]}

    diag = razonar(estructura)
    diag_dict = {
        "salud": diag.salud,
        "n_hallazgos": len(diag.hallazgos),
        "n_falacias": len(diag.falacias_detectadas),
        "n_lentes": len(diag.lentes_cubiertas),
        "n_modos": len(diag.modos_presentes),
        "resolucion": {"nivel": diag.nivel_luminico, "score": diag.resolucion_luminica},
    }
    metricas = extraer_metricas(estructura, diag_dict)

    # 2. Cargar correlaciones
    if not CORRELACIONES_FILE.exists():
        return {"error": "Sin correlaciones. Ejecuta: python3 -m scripts.core.corpus correlacion"}

    correlaciones = json.loads(CORRELACIONES_FILE.read_text())

    # 3. Predecir cada efecto usando las correlaciones
    predicciones = {}
    for corr in correlaciones:
        if not corr.get("p_significativo"):
            continue

        metrica = corr["metrica"]
        efecto = corr["efecto"]
        r = corr["coeficiente"]

        valor_metrica = metricas.get(metrica, 0)

        # Contribución ponderada por correlación
        if efecto not in predicciones:
            predicciones[efecto] = {"total": 0, "peso": 0, "contribuciones": []}

        contribucion = valor_metrica * r
        predicciones[efecto]["total"] += contribucion
        predicciones[efecto]["peso"] += abs(r)
        predicciones[efecto]["contribuciones"].append({
            "metrica": metrica,
            "valor": round(valor_metrica, 2),
            "correlacion": r,
            "contribucion": round(contribucion, 3),
        })

    # Normalizar predicciones a 0-1
    resultado = {}
    for efecto, data in predicciones.items():
        if data["peso"] > 0:
            score = max(0, min(1, data["total"] / data["peso"]))
            resultado[efecto] = {
                "prediccion": round(score, 2),
                "confianza": round(min(1, data["peso"] / 3), 2),
                "top_factores": sorted(data["contribuciones"],
                                      key=lambda c: abs(c["contribucion"]),
                                      reverse=True)[:3],
            }

    return {
        "texto_preview": texto[:100],
        "metricas_acd": {k: round(v, 2) for k, v in metricas.items()},
        "predicciones": resultado,
    }


# ===================================================================
# SEMILLA: TEXTOS INICIALES PARA BOOTSTRAPPING
# ===================================================================

SEMILLAS = [
    # === ALTA PERSUASIÓN ===
    {
        "texto": "Ana, llevas 3 semanas sin venir a Pilates. Tu grupo de los martes te echa de menos. ¿Qué te parece si reservo tu plaza para este martes a las 10? Solo tienes que responder 'sí'.",
        "efecto": {"persuasion": 0.85, "credibilidad": 0.7, "accion": 0.9, "empatia": 0.8},
        "categoria": "email_retencion",
    },
    {
        "texto": "El 73% de nuestros clientes que dejaron de venir durante 3+ semanas no volvieron. Tú llevas 18 días. Te propongo una sesión de cortesía el viernes para reconectar.",
        "efecto": {"persuasion": 0.8, "credibilidad": 0.9, "accion": 0.7, "empatia": 0.5},
        "categoria": "email_retencion",
    },
    # === BAJA PERSUASIÓN (vago corporativo) ===
    {
        "texto": "Estimado cliente, le comunicamos que estamos mejorando significativamente nuestros servicios para ofrecerle una experiencia optimizada acorde a las mejores prácticas del sector.",
        "efecto": {"persuasion": 0.1, "credibilidad": 0.2, "accion": 0.05, "empatia": 0.1},
        "categoria": "email_corporativo",
    },
    {
        "texto": "Se informa que se han implementado mejoras en los procesos internos que redundarán en beneficio de la calidad del servicio prestado.",
        "efecto": {"persuasion": 0.05, "credibilidad": 0.15, "accion": 0.02, "empatia": 0.05},
        "categoria": "email_corporativo",
    },
    # === ALTA CREDIBILIDAD ===
    {
        "texto": "En las últimas 4 semanas, 8 de tus 12 clientes del grupo de martes han asistido al menos 3 veces. La tasa de cancelación bajó del 15% al 6%. El único grupo con baja asistencia es el de viernes (3/8 media).",
        "efecto": {"persuasion": 0.5, "credibilidad": 0.95, "accion": 0.4, "empatia": 0.3},
        "categoria": "reporte_negocio",
    },
    {
        "texto": "Tu cashflow de marzo: ingresos recurrentes 4.200€, gastos fijos 1.800€, gap positivo de 2.400€. Comparado con febrero: +12% ingresos, -3% gastos. Previsión abril: estable si retienes los 5 clientes en riesgo.",
        "efecto": {"persuasion": 0.3, "credibilidad": 0.95, "accion": 0.6, "empatia": 0.2},
        "categoria": "reporte_financiero",
    },
    # === ALTA EMPATÍA ===
    {
        "texto": "Entiendo que los últimos meses han sido complicados. La espalda duele más cuando dejamos de movernos, ¿verdad? Marta (tu monitora) me comentó que preguntó por ti. Si quieres, hablamos y buscamos un horario que te venga mejor.",
        "efecto": {"persuasion": 0.7, "credibilidad": 0.6, "accion": 0.5, "empatia": 0.95},
        "categoria": "whatsapp_personal",
    },
    {
        "texto": "Hola, quería agradecerte personalmente por venir todos los martes sin faltar. Llevas 8 semanas seguidas y se nota en tu postura. Gracias por confiar en nosotros.",
        "efecto": {"persuasion": 0.3, "credibilidad": 0.8, "accion": 0.2, "empatia": 0.9},
        "categoria": "whatsapp_fidelizacion",
    },
    # === ALTA ACCIÓN (call-to-action) ===
    {
        "texto": "Carlos, tu plaza del jueves 18:00 está confirmada. Llega 5 minutos antes, trae toalla y ropa cómoda. Si no puedes venir, cancela antes de las 12:00 para no perder tu plaza.",
        "efecto": {"persuasion": 0.4, "credibilidad": 0.8, "accion": 0.95, "empatia": 0.3},
        "categoria": "confirmacion_cita",
    },
    {
        "texto": "Tienes 3 clientes con deuda superior a 100€. Laura Pérez (180€, 3 meses), Miguel Torres (120€, 2 meses), Sara García (105€, 1 mes). ¿Quieres que les envíe un recordatorio personalizado por WhatsApp?",
        "efecto": {"persuasion": 0.6, "credibilidad": 0.9, "accion": 0.85, "empatia": 0.2},
        "categoria": "alerta_cobros",
    },
    # === DISCURSO MANIPULATIVO (falacias intencionales) ===
    {
        "texto": "La ciencia demuestra que el Pilates es la mejor forma de ejercicio. Si no vienes, tu salud empeorará drásticamente. Miles de personas ya se han beneficiado de nuestro método exclusivo.",
        "efecto": {"persuasion": 0.6, "credibilidad": 0.1, "accion": 0.4, "empatia": 0.0},
        "categoria": "marketing_agresivo",
    },
    {
        "texto": "O vienes al estudio o tu dolor de espalda seguirá empeorando. No hay término medio. El 95% de nuestros clientes mejoran en la primera sesión.",
        "efecto": {"persuasion": 0.5, "credibilidad": 0.05, "accion": 0.5, "empatia": 0.0},
        "categoria": "marketing_agresivo",
    },
    # === EDUCATIVO ===
    {
        "texto": "Tu core está formado por 4 músculos principales: transverso abdominal (estabiliza la columna), oblicuos internos y externos (rotación), recto abdominal (flexión) y multífidos (extensión). En Pilates trabajamos los 4 en cada ejercicio, no solo los abdominales visibles.",
        "efecto": {"persuasion": 0.3, "credibilidad": 0.85, "accion": 0.2, "empatia": 0.4},
        "categoria": "educativo",
    },
    # === VENTA EFECTIVA ===
    {
        "texto": "Ofrecemos 3 planes: Básico (2 clases/semana, 89€), Estándar (3 clases, 119€) y Premium (ilimitado + fisio mensual, 169€). El 68% de nuestros clientes eligen Estándar. ¿Cuál prefieres? Puedes probar 1 semana gratis antes de decidir.",
        "efecto": {"persuasion": 0.8, "credibilidad": 0.85, "accion": 0.8, "empatia": 0.4},
        "categoria": "venta",
    },
    {
        "texto": "Nuestro estudio es el mejor de la zona con profesionales altamente cualificados que ofrecen una experiencia premium de bienestar holístico personalizado.",
        "efecto": {"persuasion": 0.15, "credibilidad": 0.1, "accion": 0.1, "empatia": 0.1},
        "categoria": "venta_vaga",
    },
]


# ===================================================================
# MAIN
# ===================================================================

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Corpus ACD — Estructura→Efecto")
    sub = parser.add_subparsers(dest="comando")

    # Comandos
    sub.add_parser("semilla", help="Cargar textos semilla iniciales")
    sub.add_parser("correlacion", help="Calcular correlaciones")
    sub.add_parser("recetas", help="Generar recetas estructurales")

    p_ingestar = sub.add_parser("ingestar", help="Ingestar un texto")
    p_ingestar.add_argument("--texto", required=True)
    p_ingestar.add_argument("--efecto", required=True, help="formato: dim1:val1,dim2:val2")
    p_ingestar.add_argument("--categoria", default="general")

    p_predecir = sub.add_parser("predecir", help="Predecir efecto de un texto")
    p_predecir.add_argument("--texto", required=True)

    sub.add_parser("stats", help="Estadísticas del corpus")
    sub.add_parser("todo", help="Semilla + correlación + recetas (pipeline completo)")

    args = parser.parse_args()

    if args.comando == "semilla":
        print("=" * 60)
        print("  CORPUS ACD — Cargando semillas")
        print("=" * 60)
        await ingestar_batch(SEMILLAS)
        print(f"\n  ✅ {len(SEMILLAS)} textos ingestados")

    elif args.comando == "correlacion":
        print("=" * 60)
        print("  CORPUS ACD — Calculando correlaciones")
        print("=" * 60)
        corrs = correlacionar()
        sig = [c for c in corrs if c.p_significativo]
        print(f"\n  Total: {len(corrs)} correlaciones, {len(sig)} significativas")
        print(f"\n  TOP 10:")
        for c in sig[:10]:
            emoji = "📈" if c.coeficiente > 0 else "📉"
            print(f"    {emoji} {c.insight}")

    elif args.comando == "recetas":
        print("=" * 60)
        print("  CORPUS ACD — Generando recetas")
        print("=" * 60)
        recetas = generar_recetas()
        for r in recetas:
            print(f"\n  🧪 RECETA: {r.efecto} (confianza: {r.confianza})")
            for ing in r.ingredientes:
                dir_emoji = "⬆️" if ing["direccion"] == "alto" else "⬇️"
                print(f"    {dir_emoji} {ing['metrica']}: {ing['valor_optimo']} (r={ing['correlacion']:.2f})")

    elif args.comando == "predecir":
        print("=" * 60)
        print("  CORPUS ACD — Predicción de efecto")
        print("=" * 60)
        resultado = await predecir_efecto(args.texto)
        if "error" in resultado:
            print(f"  ❌ {resultado['error']}")
        else:
            print(f"\n  Texto: {resultado['texto_preview']}...")
            for efecto, pred in resultado.get("predicciones", {}).items():
                nivel = "🟢" if pred["prediccion"] > 0.6 else "🟡" if pred["prediccion"] > 0.3 else "🔴"
                print(f"    {nivel} {efecto}: {pred['prediccion']} (confianza: {pred['confianza']})")

    elif args.comando == "stats":
        corpus = cargar_corpus()
        print(f"\n  📊 CORPUS: {len(corpus)} entradas")
        cats = defaultdict(int)
        for e in corpus:
            cats[e.get("categoria", "?")] += 1
        for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"    {cat}: {n}")

    elif args.comando == "todo":
        # Pipeline completo
        print("=" * 60)
        print("  CORPUS ACD — Pipeline completo")
        print("=" * 60)

        print("\n📥 FASE 1: Ingestando semillas...")
        try:
            from core.semillas_200 import SEMILLAS_EXTRA
            todas = SEMILLAS + SEMILLAS_EXTRA
        except ImportError:
            todas = SEMILLAS

        # Continuar desde donde se quedó
        ya_ingestados = len(cargar_corpus())
        if ya_ingestados > 0 and ya_ingestados < len(todas):
            print(f"  Continuando desde texto {ya_ingestados + 1}/{len(todas)}")
            todas = todas[ya_ingestados:]
        elif ya_ingestados >= len(todas):
            print(f"  Ya ingestados {ya_ingestados} textos, saltando ingesta")
            todas = []

        if todas:
            print(f"  Textos a ingestar: {len(todas)}")
            await ingestar_batch(todas)

        print("\n📊 FASE 2: Calculando correlaciones...")
        corrs = correlacionar()
        sig = [c for c in corrs if c.p_significativo]
        print(f"  {len(sig)} correlaciones significativas")

        print("\n🧪 FASE 3: Generando recetas...")
        recetas = generar_recetas()

        print(f"\n{'=' * 60}")
        print(f"  RESULTADO")
        print(f"  Textos analizados: {len(SEMILLAS)}")
        print(f"  Correlaciones significativas: {len(sig)}")
        print(f"  Recetas generadas: {len(recetas)}")
        print(f"{'=' * 60}")

        # Mostrar top insights
        print(f"\n  🔥 TOP INSIGHTS:")
        for c in sig[:5]:
            emoji = "📈" if c.coeficiente > 0 else "📉"
            print(f"    {emoji} {c.insight}")

        print(f"\n  🧪 RECETAS:")
        for r in recetas:
            resumen = ', '.join(str(i["metrica"]) + "=" + str(i["valor_optimo"]) for i in r.ingredientes[:3])
            print(f"    {r.efecto}: {resumen}")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
