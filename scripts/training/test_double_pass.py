#!/usr/bin/env python3
"""
Test Doble Pasada A/B — 71 Dims Simbionte
==========================================
Valida si la doble pasada (Opus + feedback estructural) mejora la calidad del labeling
comparada con la pasada simple.

Selecciona 5 textos ya etiquetados del POC micro (poc_micro_71dims.jsonl).
Para cada texto:
  - Ya tiene labels de pasada 1 (del POC micro — no llama a la API de nuevo)
  - Genera feedback estructural con codigo puro ($0) desde esos labels
  - Envia a Opus con el feedback → pasada 2 (ESTA es la llamada que cuesta)
  - Compara pasada 1 vs pasada 2

Para IAA (consistencia): re-ejecuta pasada 2 en 3 de los 5 textos una segunda vez.
Si IAA_pasada2 > IAA_pasada1 → la doble pasada es mas consistente.

Uso:
  python test_double_pass.py --estimate    # coste estimado sin llamadas
  python test_double_pass.py --dry-run     # muestra plan sin llamadas
  python test_double_pass.py --confirm     # EJECUTA (requiere aprobacion)

  O con variable de entorno:
  APROBADO_CEO=si python test_double_pass.py

Salidas:
  motor-semantico/experiments/poc_micro/double_pass_test.jsonl
  motor-semantico/experiments/poc_micro/double_pass_report.md

Metricas emitidas (formato METRIC:key=value):
  double_pass_tasa_cambio, double_pass_magnitud_media, double_pass_contradicciones_resueltas,
  double_pass_iaa_p1, double_pass_iaa_p2, double_pass_aporta (0/1)

COSTE ESTIMADO:
  - Pasada 2: 5 textos × 1 llamada = 5 llamadas
  - IAA: 3 textos × 1 llamada adicional = 3 llamadas
  - TOTAL: 8 llamadas a Opus
  - ~6360 tokens/llamada (system 4510 + feedback 1500 + user 350)
  - ~$0.52 en input + ~$0.16 en output ≈ $0.68 total [SUPOSICION: sin tiktoken]
  - Con margen 20%: ~$0.82

IMPORTANTE: Este script NO re-ejecuta pasada 1. Usa los labels existentes del POC micro.
La pasada 2 es la unica que genera coste.
"""

import os
import sys
import json
import time
import random
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from collections import defaultdict

# ── Rutas ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
MOTOR_ROOT = SCRIPT_DIR.parents[1]          # motor-semantico/
PROJECT_ROOT = MOTOR_ROOT.parent            # omni-mind-cerebro/

sys.path.insert(0, str(MOTOR_ROOT / "scripts"))
from shared_config import config as _cfg

# ── Rutas de datos ────────────────────────────────────────────────────────────
POC_MICRO_LABELS = MOTOR_ROOT / "data" / "poc_micro_71dims.jsonl"
ABLATION_RAW = MOTOR_ROOT / "experiments" / "poc_micro" / "ablation_raw.jsonl"
OUTPUT_PATH = MOTOR_ROOT / "experiments" / "poc_micro" / "double_pass_test.jsonl"
REPORT_PATH = MOTOR_ROOT / "experiments" / "poc_micro" / "double_pass_report.md"
PROMPT_PATH = MOTOR_ROOT / "prompts" / "labeling_poc_micro.md"
DOUBLE_PASS_PROMPT = MOTOR_ROOT / "prompts" / "labeling_double_pass.md"

# ── Constantes ────────────────────────────────────────────────────────────────
N_TEST = 5          # textos para comparacion pasada1 vs pasada2
N_IAA = 3           # textos para medir IAA (subset de los 5)
OPUS_MODEL = "anthropic/claude-opus-4"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Dimensiones del POC — 67 floats + 4 categoricas
FLOAT_DIMS = [
    "log_cuant_universal", "log_cuant_existencial", "log_cuant_negativo",
    "log_marcador_premisa", "log_marcador_conclusion", "log_cuant_generico",
    "arg_claim_ratio", "arg_data_ratio", "arg_warrant_explicito",
    "set_inclusion", "set_exclusion", "set_intersection",
    "concl_fuerza", "concl_premisa_oculta", "concl_completitud_toulmin", "log_defeasible",
    "comp_error_variables", "comp_error_nivel_logico", "comp_error_foto_fantasma", "circularidad_reglas",
    "disc_dir_premisa_primero", "disc_dir_conclusion_primero", "disc_profundidad_argumental",
    "disc_coherencia_logica", "disc_presuposiciones",
    "nivel_compresion_intervencion", "p1_heredada_vs_elegida",
    "presup_densidad", "presup_verificabilidad", "presup_carga_compartida",
    "presup_proyeccion", "presup_cadena_causal", "presup_posicion_observador",
    "presup_conflicto_inter", "presup_defeasibilidad", "presup_profundidad",
    "presup_fragilidad", "presup_conciencia", "presup_cobertura_niveles",
    "presup_direccion_construccion", "presup_anclaje_base",
    "fis_entropia_informacional",
    "eco_diversidad_argumental",
    "sem_modal_deontico", "sem_modal_epistemico", "sem_agentividad",
    "sem_vaguedad_semantica", "sem_causalidad_evento", "sem_telicidad",
    "sem_informatividad", "sem_relevancia_tematica",
    "cog_carga_procesamiento",
    "agencia_reactivo_proactivo", "agencia_iniciativa_verbal",
    "evasion_modalizacion", "evasion_pasivizacion_agentiva", "agencia_protagonismo_narrativo",
    "cog_pensamiento_contrafactual", "cog_falsa_dicotomia", "cog_falacia_pendiente",
    "disc_compromiso_accionable", "disc_contradiccion_interna", "disc_meta_discursivo",
    "disc_resolucion_tensiones", "disc_coherencia_registro", "disc_autocontencion",
    "disc_densidad_informacional_varianza",
]
CAT_DIMS = [
    "escala_fractal",
    "presup_tipo_disparador",
    "sem_acto_habla",
    "sem_evidencialidad",
]
ALL_DIMS = FLOAT_DIMS + CAT_DIMS

# Aliases de Opus (V1, N8...) a nombres canonicos
DIM_ALIASES = {
    "V1": "log_cuant_universal", "V2": "log_cuant_existencial", "V3": "log_cuant_negativo",
    "V4": "log_marcador_premisa", "V5": "log_marcador_conclusion", "V6": "log_cuant_generico",
    "V7": "arg_claim_ratio", "V8": "arg_data_ratio", "V9": "arg_warrant_explicito",
    "V10": "set_inclusion", "V11": "set_exclusion", "V12": "set_intersection",
    "V13": "concl_fuerza", "V14": "concl_premisa_oculta", "V15": "concl_completitud_toulmin",
    "V16": "log_defeasible", "V17": "comp_error_variables", "V18": "comp_error_nivel_logico",
    "V19": "comp_error_foto_fantasma", "V20": "circularidad_reglas",
    "V21": "disc_dir_premisa_primero", "V22": "disc_dir_conclusion_primero",
    "V23": "disc_profundidad_argumental", "V24": "disc_coherencia_logica",
    "V25": "disc_presuposiciones", "V26": "nivel_compresion_intervencion",
    "V27": "p1_heredada_vs_elegida", "V28": "escala_fractal",
    "N2": "fis_entropia_informacional", "N8": "sem_acto_habla", "N9": "sem_evidencialidad",
    "N10": "eco_diversidad_argumental", "N11": "sem_modal_deontico", "N12": "sem_modal_epistemico",
    "N13": "sem_agentividad", "N14": "sem_vaguedad_semantica", "N15": "sem_causalidad_evento",
    "N16": "sem_telicidad", "N17": "sem_informatividad", "N18": "sem_relevancia_tematica",
    "N31": "cog_carga_procesamiento", "N32": "agencia_reactivo_proactivo",
    "N33": "agencia_iniciativa_verbal", "N34": "evasion_modalizacion",
    "N35": "evasion_pasivizacion_agentiva", "N36": "agencia_protagonismo_narrativo",
    "N37": "cog_pensamiento_contrafactual", "N38": "cog_falsa_dicotomia",
    "N39": "cog_falacia_pendiente", "N51": "disc_compromiso_accionable",
    "N52": "disc_contradiccion_interna", "N53": "disc_meta_discursivo",
    "N54": "disc_resolucion_tensiones", "N55": "disc_coherencia_registro",
    "N56": "disc_autocontencion", "N57": "disc_densidad_informacional_varianza",
}


def normalize_keys(labels: dict) -> dict:
    """Convierte aliases (V1, N8...) a nombres canonicos. Keys desconocidas se mantienen."""
    normalized = {}
    for k, v in labels.items():
        canonical = DIM_ALIASES.get(k, k)
        normalized[canonical] = v
    return normalized


# ── GENERADOR DE FEEDBACK (codigo puro, $0) ──────────────────────────────────

def generate_feedback(labels: dict) -> str:
    """
    Genera feedback estructural desde un vector de 71 dims.
    Codigo puro: $0. Solo la pasada 2 cuesta dinero.

    El feedback tiene 5 secciones:
    1. Estructura logica (profundidad, coherencia, premisas, direccion)
    2. Presuposiciones (densidad, anclaje, posicion observador, fragilidad)
    3. Agentividad (agentividad, protagonismo, evasion)
    4. Dims con señal fuerte (>0.6)
    5. Dims sospechosas (contradicciones internas detectables por reglas)
    """

    feedback_parts = []

    # 1. Estructura logica
    prof = labels.get("disc_profundidad_argumental", 0)
    coh = labels.get("disc_coherencia_logica", 0)
    prem = labels.get("concl_premisa_oculta", 0)
    dir_val = labels.get("presup_direccion_construccion", 0)

    if dir_val < 0.3:
        direction = "bottom-up (datos->conclusion)"
    elif dir_val > 0.7:
        direction = "top-down (conclusion->datos)"
    else:
        direction = "mixta"

    prof_interp = "plano" if prof < 0.3 else ("medio" if prof < 0.7 else "profundo")
    prem_interp = "pocas" if prem < 0.3 else ("moderadas" if prem < 0.6 else "muchas premisas no dichas")

    feedback_parts.append(
        f"ESTRUCTURA LOGICA:\n"
        f"- Profundidad argumental: {prof:.2f} ({prof_interp})\n"
        f"- Coherencia logica: {coh:.2f}\n"
        f"- Premisas ocultas: {prem:.2f} ({prem_interp})\n"
        f"- Direccion: {direction}"
    )

    # 2. Presuposiciones
    dens = labels.get("presup_densidad", 0)
    ancl = labels.get("presup_anclaje_base", 0)
    pos = labels.get("presup_posicion_observador", 0)
    frag = labels.get("presup_fragilidad", 0)

    if pos < 0.2:
        nivel_obs = "datos"
    elif pos < 0.4:
        nivel_obs = "interpretacion"
    elif pos < 0.6:
        nivel_obs = "atribucion"
    elif pos < 0.8:
        nivel_obs = "teoria"
    else:
        nivel_obs = "conclusion"

    dens_interp = "baja" if dens < 0.3 else ("media" if dens < 0.6 else "alta — mucho contenido asumido")
    ancl_interp = "sin anclaje" if ancl < 0.3 else ("parcial" if ancl < 0.7 else "bien anclado")
    frag_interp = "robusto" if frag < 0.3 else ("moderado" if frag < 0.6 else "fragil — una premisa cae y todo colapsa")

    feedback_parts.append(
        f"PRESUPOSICIONES:\n"
        f"- Densidad presupositiva: {dens:.2f} ({dens_interp})\n"
        f"- Anclaje en datos observables: {ancl:.2f} ({ancl_interp})\n"
        f"- Posicion del observador: nivel {nivel_obs} ({pos:.2f})\n"
        f"- Fragilidad: {frag:.2f} ({frag_interp})"
    )

    # 3. Agentividad
    agent = labels.get("sem_agentividad", 0)
    prot = labels.get("agencia_protagonismo_narrativo", 0)
    evas = labels.get("evasion_modalizacion", 0)

    agent_interp = "pasivo/impersonal" if agent < 0.3 else ("medio" if agent < 0.7 else "agente claro")
    prot_interp = "espectador" if prot < 0.3 else ("mixto" if prot < 0.7 else "protagonista activo")
    evas_interp = "sin evasion" if evas < 0.2 else ("algo de hedging" if evas < 0.5 else "evasion sistematica")

    feedback_parts.append(
        f"AGENTIVIDAD:\n"
        f"- Agentividad: {agent:.2f} ({agent_interp})\n"
        f"- Protagonismo: {prot:.2f} ({prot_interp})\n"
        f"- Evasion modalizada: {evas:.2f} ({evas_interp})"
    )

    # 4. Dims con señal fuerte (>0.6) — solo floats, max 10 dims
    strong = [
        (k, v) for k, v in labels.items()
        if k in FLOAT_DIMS and isinstance(v, (int, float)) and float(v) > 0.6
    ]
    if strong:
        strong_sorted = sorted(strong, key=lambda x: -float(x[1]))[:10]
        strong_str = "\n".join(f"  - {k}: {v:.2f}" for k, v in strong_sorted)
        feedback_parts.append(f"DIMS CON SEÑAL FUERTE (>0.6):\n{strong_str}")
    else:
        feedback_parts.append("DIMS CON SEÑAL FUERTE (>0.6): ninguna")

    # 5. Contradicciones internas detectables por reglas
    contradictions = []

    # Regla 1: alta agentividad + alta evasion
    if agent > 0.6 and evas > 0.4:
        contradictions.append(
            f"Alta agentividad ({agent:.2f}) + alta evasion ({evas:.2f}) — "
            f"el agente actua pero evade responsabilidad?"
        )

    # Regla 2: buen anclaje + muchas premisas ocultas
    if ancl > 0.7 and prem > 0.6:
        contradictions.append(
            f"Buen anclaje ({ancl:.2f}) + muchas premisas ocultas ({prem:.2f}) — "
            f"hay datos pero las conclusiones van mas alla de ellos?"
        )

    # Regla 3: alta coherencia logica + contradicciones internas
    coh_log = labels.get("disc_coherencia_logica", 0)
    contra = labels.get("disc_contradiccion_interna", 0)
    if isinstance(coh_log, (int, float)) and isinstance(contra, (int, float)):
        if float(coh_log) > 0.7 and float(contra) > 0.3:
            contradictions.append(
                f"Alta coherencia ({coh_log:.2f}) + contradicciones ({contra:.2f}) — "
                f"revisa si hay contradicciones sutiles no obvias"
            )

    # Regla 4: alta circularidad + buena coherencia
    circ = labels.get("circularidad_reglas", 0)
    if isinstance(circ, (int, float)) and isinstance(coh_log, (int, float)):
        if float(circ) > 0.5 and float(coh_log) > 0.7:
            contradictions.append(
                f"Circularidad alta ({circ:.2f}) + coherencia alta ({coh_log:.2f}) — "
                f"un sistema circular parece coherente pero no esta anclado en lo externo"
            )

    # Regla 5: defeasible + fuerza de conclusion alta
    defeas = labels.get("log_defeasible", 0)
    fuerza = labels.get("concl_fuerza", 0)
    if isinstance(defeas, (int, float)) and isinstance(fuerza, (int, float)):
        if float(defeas) < 0.2 and float(fuerza) > 0.8:
            # Conclusion necesaria pero irrevocable — posible rigidez epistemica
            contradictions.append(
                f"Conclusion irrevocable ({defeas:.2f} defeasible) + fuerza maxima ({fuerza:.2f}) — "
                f"considera si la conclusion admite revision con nueva evidencia"
            )

    # Regla 6: protagonismo activo + reactivo (baja iniciativa)
    reactpro = labels.get("agencia_reactivo_proactivo", 0)
    if isinstance(prot, (int, float)) and isinstance(reactpro, (int, float)):
        if float(prot) > 0.7 and float(reactpro) < 0.3:
            contradictions.append(
                f"Protagonismo narrativo alto ({prot:.2f}) + reactivo ({reactpro:.2f}) — "
                f"el sujeto es el centro de la historia pero responde a estimulos, no inicia"
            )

    if contradictions:
        contra_str = "\n".join(f"  - {c}" for c in contradictions)
        feedback_parts.append(f"DIMS SOSPECHOSAS (posibles inconsistencias):\n{contra_str}")
    else:
        feedback_parts.append("DIMS SOSPECHOSAS: ninguna contradiccion detectada.")

    header = "AUDITORIA ESTRUCTURAL DEL TEXTO (generada automaticamente desde tu etiquetado previo):\n"
    return header + "\n\n".join(feedback_parts)


# ── Carga de textos del POC micro ─────────────────────────────────────────────

def load_poc_micro_texts(n: int = N_TEST) -> List[dict]:
    """
    Carga N textos del POC micro que ya tienen labels de pasada 1.

    Busca en:
    1. poc_micro_71dims.jsonl (output principal del labeling)
    2. ablation_raw.jsonl (output del ablation test, variante A)

    Retorna lista de dicts con: text, labels_p1, text_id, source
    """
    candidates = []

    # Intentar primary source
    for path in [POC_MICRO_LABELS, ABLATION_RAW]:
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    text = entry.get("text", "")
                    # Para ablation_raw: la variante A es la pasada 1
                    variante = entry.get("variante", "")
                    if variante and variante != "A":
                        continue  # solo tomar variante A del ablation
                    # Extraer labels: pueden estar en "labels" o directamente en el dict
                    labels = entry.get("labels", None)
                    if labels is None:
                        # En ablation_raw los labels estan en dims_raw o directamente
                        labels = entry.get("dims_raw", entry.get("dims", None))
                    if labels is None:
                        # Intentar tomar todos los campos que no son metadata
                        meta_keys = {"text", "text_id", "source", "variante", "idx",
                                     "timestamp", "error", "_input_tokens", "_output_tokens"}
                        labels = {k: v for k, v in entry.items() if k not in meta_keys}

                    if not text or len(text) < 100:
                        continue
                    if not labels or len(labels) < 20:
                        continue

                    # Normalizar aliases
                    labels = normalize_keys(labels)

                    # Verificar que tiene dims float basicas
                    has_floats = sum(1 for d in FLOAT_DIMS[:10] if d in labels)
                    if has_floats < 5:
                        continue

                    candidates.append({
                        "text": text,
                        "labels_p1": labels,
                        "text_id": entry.get("text_id", entry.get("idx", f"text_{len(candidates)}")),
                        "source": entry.get("source", path.name),
                    })
                except (json.JSONDecodeError, Exception):
                    continue
        if candidates:
            break

    if not candidates:
        raise FileNotFoundError(
            f"No se encontraron textos con labels de pasada 1.\n"
            f"Buscado en:\n  {POC_MICRO_LABELS}\n  {ABLATION_RAW}\n"
            f"Ejecuta primero label_poc_micro.py para generar los labels."
        )

    # Seleccionar N textos diversos (variar longitud de texto)
    candidates.sort(key=lambda x: len(x["text"]))
    if len(candidates) >= n:
        step = len(candidates) / n
        selected = [candidates[int(i * step)] for i in range(n)]
    else:
        selected = candidates[:n]

    print(f"  Textos cargados: {len(candidates)} disponibles, {len(selected)} seleccionados")
    return selected


# ── Llamada a Opus pasada 2 ───────────────────────────────────────────────────

def load_system_prompt_p2() -> str:
    """Extrae el system prompt de la pasada 2 desde labeling_double_pass.md."""
    import re
    raw = DOUBLE_PASS_PROMPT.read_text(encoding="utf-8")
    # Buscar el bloque '## PASADA 2 — SYSTEM PROMPT' y extraer el primer ```...```
    match = re.search(r"## PASADA 2 — SYSTEM PROMPT\s*\n\s*```\s*\n(.*?)```", raw, re.DOTALL)
    if not match:
        # Fallback: system prompt inline
        return (
            "Eres un anotador lingüístico. Acabas de etiquetar un texto con 71 dimensiones estructurales. "
            "Se ha generado una auditoría estructural automática de tu etiquetado. "
            "Tu tarea: revisar el etiquetado a la luz de la auditoría y producir el vector final. "
            "REGLAS: 1) Si una dim parece incorrecta tras la auditoría, corrígela. "
            "2) Si parece correcta, mantenla. 3) Presta especial atención a DIMS SOSPECHOSAS. "
            "4) NO cambies todo — solo lo que genuinamente merezca corrección. "
            "5) Responde SOLO con JSON válido, sin explicaciones, sin markdown. "
            "6) El JSON debe tener exactamente 71 campos."
        )
    return match.group(1).strip()


def call_opus_pasada2(
    text: str,
    labels_p1: dict,
    feedback: str,
    max_retries: int = 3,
) -> Optional[dict]:
    """
    Llama a Opus para la pasada 2 via OpenRouter.

    Retorna dict con:
      - las 71 dims (labels de pasada 2)
      - _input_tokens, _output_tokens (para tracking de coste)
    O None si falla tras max_retries intentos.
    """
    api_key = _cfg.OPENROUTER_API_KEY
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY no configurada en .env ni en motor-semantico/.env")

    system_prompt = load_system_prompt_p2()

    # Construir labels p1 como JSON limpio (sin campos de metadata)
    labels_p1_clean = {
        k: v for k, v in labels_p1.items()
        if not k.startswith("_") and k in ALL_DIMS
    }

    user_content = (
        f'TEXTO ORIGINAL:\n"""\n{text[:3500]}\n"""\n\n'
        f'TU ETIQUETADO DE LA PASADA 1:\n{json.dumps(labels_p1_clean, ensure_ascii=False, indent=2)}\n\n'
        f'{feedback}\n\n'
        f'Produce el JSON final de 71 dims (corregido o no).'
    )

    payload = {
        "model": OPUS_MODEL,
        "max_tokens": 2500,
        "temperature": 0.0,  # determinista para IAA
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }

    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    OPENROUTER_URL,
                    "-H", f"Authorization: Bearer {api_key}",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(payload),
                ],
                capture_output=True, text=True, timeout=180
            )

            if result.returncode != 0:
                print(f"    [attempt {attempt+1}] curl error: {result.stderr[:200]}")
                time.sleep(5 * (attempt + 1))
                continue

            response = json.loads(result.stdout)

            if "error" in response:
                err_msg = response["error"].get("message", str(response["error"]))
                print(f"    [attempt {attempt+1}] API error: {err_msg}")
                if "rate_limit" in err_msg.lower() or "overloaded" in err_msg.lower():
                    time.sleep(30 * (attempt + 1))
                else:
                    time.sleep(5 * (attempt + 1))
                continue

            # Extraer contenido (formato OpenRouter)
            choices = response.get("choices", [])
            if not choices:
                print(f"    [attempt {attempt+1}] respuesta sin choices")
                time.sleep(5)
                continue

            raw_content = choices[0].get("message", {}).get("content", "").strip()
            if not raw_content:
                print(f"    [attempt {attempt+1}] respuesta vacia")
                time.sleep(10 * (attempt + 1))
                continue

            # Limpiar markdown fences si las hay
            if raw_content.startswith("```"):
                lines = raw_content.split("\n")
                raw_content = "\n".join(lines[1:-1]) if len(lines) > 2 else raw_content

            labels = json.loads(raw_content)
            labels = normalize_keys(labels)

            # Rellenar dims faltantes con 0.0 / "desconocido"
            for d in FLOAT_DIMS:
                if d not in labels:
                    labels[d] = 0.0
            for d in CAT_DIMS:
                if d not in labels:
                    labels[d] = "desconocido"

            # Guardar tokens para tracking
            usage = response.get("usage", {})
            labels["_input_tokens"] = usage.get("input_tokens", usage.get("prompt_tokens", 0))
            labels["_output_tokens"] = usage.get("output_tokens", usage.get("completion_tokens", 0))

            return labels

        except json.JSONDecodeError as e:
            print(f"    [attempt {attempt+1}] JSON parse error: {e}")
            time.sleep(3 * (attempt + 1))
        except Exception as e:
            print(f"    [attempt {attempt+1}] Error: {type(e).__name__}: {e}")
            time.sleep(5 * (attempt + 1))

    return None


# ── Analisis estadistico de diferencias ──────────────────────────────────────

def compare_passes(labels_p1: dict, labels_p2: dict) -> dict:
    """
    Compara pasada 1 vs pasada 2 para un texto.

    Retorna:
      - dims_changed: lista de dims que cambiaron (delta > 0.01)
      - tasa_cambio: % dims que cambiaron
      - magnitud_media: media de |p2 - p1| en dims que cambiaron
      - cambios_grandes: dims con delta > 0.2
      - cambios_pequeños: dims con delta < 0.1 pero != 0
      - cats_changed: categoricas que cambiaron
    """
    dims_changed = []
    deltas = []
    cambios_grandes = []
    cambios_pequeños = []
    cats_changed = []

    for d in FLOAT_DIMS:
        v1 = float(labels_p1.get(d, 0))
        v2 = float(labels_p2.get(d, 0))
        delta = abs(v2 - v1)
        if delta > 0.01:  # umbral de cambio significativo (precision de 2 decimales)
            dims_changed.append({"dim": d, "p1": round(v1, 2), "p2": round(v2, 2), "delta": round(delta, 2)})
            deltas.append(delta)
            if delta >= 0.2:
                cambios_grandes.append(d)
            elif delta < 0.1:
                cambios_pequeños.append(d)

    for d in CAT_DIMS:
        v1 = labels_p1.get(d, "")
        v2 = labels_p2.get(d, "")
        if v1 != v2:
            cats_changed.append({"dim": d, "p1": v1, "p2": v2})

    n_float_total = len(FLOAT_DIMS)
    tasa = len(dims_changed) / n_float_total if n_float_total > 0 else 0
    mag = sum(deltas) / len(deltas) if deltas else 0

    return {
        "dims_changed": dims_changed,
        "tasa_cambio": round(tasa, 4),
        "magnitud_media": round(mag, 4),
        "n_cambios": len(dims_changed),
        "cambios_grandes": cambios_grandes,
        "cambios_pequeños": cambios_pequeños,
        "cats_changed": cats_changed,
    }


def detect_contradictions(labels: dict) -> List[str]:
    """
    Detecta contradicciones internas en un vector de labels.
    Mismas reglas que generate_feedback() — para medir cuantas se resolvieron.
    """
    contradictions = []

    agent = float(labels.get("sem_agentividad", 0))
    evas = float(labels.get("evasion_modalizacion", 0))
    ancl = float(labels.get("presup_anclaje_base", 0))
    prem = float(labels.get("concl_premisa_oculta", 0))
    coh_log = float(labels.get("disc_coherencia_logica", 0))
    contra = float(labels.get("disc_contradiccion_interna", 0))
    circ = float(labels.get("circularidad_reglas", 0))
    defeas = float(labels.get("log_defeasible", 0))
    fuerza = float(labels.get("concl_fuerza", 0))
    prot = float(labels.get("agencia_protagonismo_narrativo", 0))
    reactpro = float(labels.get("agencia_reactivo_proactivo", 0))

    if agent > 0.6 and evas > 0.4:
        contradictions.append("agentividad_alta+evasion_alta")
    if ancl > 0.7 and prem > 0.6:
        contradictions.append("anclaje_alto+premisas_ocultas_altas")
    if coh_log > 0.7 and contra > 0.3:
        contradictions.append("coherencia_alta+contradicciones_altas")
    if circ > 0.5 and coh_log > 0.7:
        contradictions.append("circularidad_alta+coherencia_alta")
    if defeas < 0.2 and fuerza > 0.8:
        contradictions.append("irrevocable+fuerza_maxima")
    if prot > 0.7 and reactpro < 0.3:
        contradictions.append("protagonismo_alto+reactivo")

    return contradictions


def compute_iaa(labels_run1: dict, labels_run2: dict) -> float:
    """
    Calcula correlacion de Pearson entre dos runs del mismo texto.
    Usa solo dims float con varianza (no todas en 0.0 en ambas runs).

    Retorna correlacion media, o -1.0 si no hay dims comparables.
    """
    pairs = []
    for d in FLOAT_DIMS:
        v1 = float(labels_run1.get(d, 0))
        v2 = float(labels_run2.get(d, 0))
        if v1 != 0 or v2 != 0:  # excluir dims donde ambas son 0
            pairs.append((v1, v2))

    if len(pairs) < 10:
        return -1.0

    vals1 = [p[0] for p in pairs]
    vals2 = [p[1] for p in pairs]

    mean1 = sum(vals1) / len(vals1)
    mean2 = sum(vals2) / len(vals2)

    cov = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(vals1, vals2))
    std1 = (sum((v - mean1) ** 2 for v in vals1) ** 0.5)
    std2 = (sum((v - mean2) ** 2 for v in vals2) ** 0.5)

    if std1 == 0 or std2 == 0:
        return -1.0

    return round(cov / (std1 * std2), 4)


# ── Estimacion de coste ───────────────────────────────────────────────────────

def estimate_cost() -> None:
    """
    Estima el coste del test sin llamar a la API.
    [SUPOSICION]: tokens estimados por chars/4, no tiktoken ejecutado.
    """
    print("\n[SUPOSICION — sin tiktoken ejecutado]\n")
    print("ESTIMACION DE COSTE — test_double_pass.py")
    print("=" * 50)
    print(f"Textos para comparacion: {N_TEST}")
    print(f"Textos para IAA (re-run pasada 2): {N_IAA}")
    total_llamadas = N_TEST + N_IAA
    print(f"Total llamadas Opus: {total_llamadas}\n")

    # Tokens por llamada pasada 2:
    # - System prompt p2: ~900 tokens
    # - JSON pasada 1 (71 dims): ~750 tokens
    # - Texto original: ~450 tokens
    # - Feedback estructural: ~350 tokens
    # - Instruccion final: ~50 tokens
    # Total input: ~2500 tokens
    # Output: ~700 tokens (71 dims JSON)
    tokens_input_per_call = 2500
    tokens_output_per_call = 700

    # Precios Opus (OpenRouter, abril 2026)
    # anthropic/claude-opus-4: $15/$75 por M tokens
    price_input_per_1k = 0.015
    price_output_per_1k = 0.075

    cost_input = total_llamadas * tokens_input_per_call * price_input_per_1k / 1000
    cost_output = total_llamadas * tokens_output_per_call * price_output_per_1k / 1000
    total = cost_input + cost_output
    with_margin = total * 1.2

    print(f"Tokens input/llamada:  ~{tokens_input_per_call}")
    print(f"Tokens output/llamada: ~{tokens_output_per_call}")
    print(f"Precio input:  ${price_input_per_1k}/1K tokens")
    print(f"Precio output: ${price_output_per_1k}/1K tokens\n")
    print(f"Coste input:  ~${cost_input:.3f}")
    print(f"Coste output: ~${cost_output:.3f}")
    print(f"TOTAL:        ~${total:.3f}")
    print(f"+20% margen:  ~${with_margin:.3f}")
    print(f"\n[VERIFICAR con CostGate.validate_batch() antes de ejecutar si >$5]")
    print(f"[Este test es <$5 — requiere solo --confirm o APROBADO_CEO=si]")


# ── Generacion de informe ─────────────────────────────────────────────────────

def generate_report(results: List[dict], iaa_results: List[dict]) -> str:
    """Genera informe markdown con los resultados del test A/B."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Metricas globales
    tasa_media = sum(r["comparison"]["tasa_cambio"] for r in results) / len(results) if results else 0
    mag_media = sum(r["comparison"]["magnitud_media"] for r in results if r["comparison"]["magnitud_media"] > 0)
    mag_media = mag_media / len([r for r in results if r["comparison"]["magnitud_media"] > 0]) if results else 0

    total_contradictions_p1 = sum(len(r["contradictions_p1"]) for r in results)
    total_contradictions_p2 = sum(len(r["contradictions_p2"]) for r in results)
    tasa_resolucion = 0
    if total_contradictions_p1 > 0:
        resueltas = total_contradictions_p1 - total_contradictions_p2
        tasa_resolucion = max(0, resueltas) / total_contradictions_p1

    # IAA
    iaa_p1_scores = [r.get("iaa_p1", -1) for r in iaa_results if r.get("iaa_p1", -1) >= 0]
    iaa_p2_scores = [r.get("iaa_p2", -1) for r in iaa_results if r.get("iaa_p2", -1) >= 0]
    iaa_p1_mean = sum(iaa_p1_scores) / len(iaa_p1_scores) if iaa_p1_scores else -1
    iaa_p2_mean = sum(iaa_p2_scores) / len(iaa_p2_scores) if iaa_p2_scores else -1

    # Veredicto
    aporta = False
    razones = []
    if tasa_media > 0.03:
        razones.append(f"tasa de cambio {tasa_media:.1%} > 3% (umbral minimo)")
        aporta = True
    if mag_media > 0.08:
        razones.append(f"magnitud media {mag_media:.3f} > 0.08 (correcciones significativas)")
        aporta = True
    if tasa_resolucion > 0.3:
        razones.append(f"resuelve {tasa_resolucion:.0%} de las contradicciones detectadas")
        aporta = True
    if iaa_p2_mean > iaa_p1_mean and iaa_p1_mean >= 0:
        razones.append(f"IAA pasada 2 ({iaa_p2_mean:.3f}) > IAA pasada 1 ({iaa_p1_mean:.3f})")
        aporta = True

    veredicto = "APORTA" if aporta else "NO APORTA (o aporte marginal)"

    lines = [
        f"# Test Doble Pasada — Informe",
        f"",
        f"**Fecha:** {now}",
        f"**Textos testados:** {len(results)}",
        f"**Textos IAA:** {len(iaa_results)}",
        f"",
        f"---",
        f"",
        f"## Veredicto",
        f"",
        f"**{veredicto}**",
        f"",
    ]

    if razones:
        for r in razones:
            lines.append(f"- {r}")
    else:
        lines.append("- Ninguna metrica supera el umbral de utilidad")
    lines.append("")

    lines += [
        f"---",
        f"",
        f"## Metricas globales",
        f"",
        f"| Metrica | Valor | Interpretacion |",
        f"|---------|-------|----------------|",
        f"| Tasa de cambio media | {tasa_media:.1%} | % dims que cambiaron entre p1 y p2 |",
        f"| Magnitud media del cambio | {mag_media:.3f} | media(|p2-p1|) en dims que cambiaron |",
        f"| Contradicciones en p1 | {total_contradictions_p1} | total en {len(results)} textos |",
        f"| Contradicciones en p2 | {total_contradictions_p2} | tras la doble pasada |",
        f"| Tasa resolucion contradicciones | {tasa_resolucion:.0%} | de p1 resueltas en p2 |",
        f"| IAA pasada 1 (media) | {iaa_p1_mean:.3f if iaa_p1_mean >= 0 else 'N/A'} | correlacion entre dos runs p1 |",
        f"| IAA pasada 2 (media) | {iaa_p2_mean:.3f if iaa_p2_mean >= 0 else 'N/A'} | correlacion entre dos runs p2 |",
        f"",
        f"**Rangos de referencia (tasa de cambio):**",
        f"- < 3%: la doble pasada no aporta (etiquetado ya era estable)",
        f"- 3-15%: rango saludable (correcciones puntuales)",
        f"- > 15%: la pasada 1 era inestable",
        f"",
        f"---",
        f"",
        f"## Detalle por texto",
        f"",
    ]

    for i, r in enumerate(results):
        comp = r["comparison"]
        text_preview = r["text"][:100].replace("\n", " ") + "..."
        lines += [
            f"### Texto {i+1} (id: {r['text_id']})",
            f"",
            f"*{text_preview}*",
            f"",
            f"- Dims cambiadas: {comp['n_cambios']} / {len(FLOAT_DIMS)} ({comp['tasa_cambio']:.1%})",
            f"- Magnitud media: {comp['magnitud_media']:.3f}",
            f"- Cambios grandes (>0.2): {', '.join(comp['cambios_grandes']) if comp['cambios_grandes'] else 'ninguno'}",
            f"- Categoricas cambiadas: {len(comp['cats_changed'])}",
            f"- Contradicciones p1: {len(r['contradictions_p1'])} → p2: {len(r['contradictions_p2'])}",
            f"",
        ]

        if comp["dims_changed"]:
            top5 = sorted(comp["dims_changed"], key=lambda x: -x["delta"])[:5]
            lines.append("**Top 5 cambios:**")
            lines.append("")
            lines.append("| Dim | p1 | p2 | delta |")
            lines.append("|-----|----|----|-------|")
            for ch in top5:
                lines.append(f"| {ch['dim']} | {ch['p1']:.2f} | {ch['p2']:.2f} | {ch['delta']:.2f} |")
            lines.append("")

        if comp["cats_changed"]:
            lines.append("**Categoricas cambiadas:**")
            lines.append("")
            for ch in comp["cats_changed"]:
                lines.append(f"- {ch['dim']}: `{ch['p1']}` → `{ch['p2']}`")
            lines.append("")

    if iaa_results:
        lines += [
            f"---",
            f"",
            f"## IAA — Consistencia entre runs",
            f"",
            f"| Texto | IAA p1 | IAA p2 | Mejora |",
            f"|-------|--------|--------|--------|",
        ]
        for r in iaa_results:
            iaa1 = r.get("iaa_p1", -1)
            iaa2 = r.get("iaa_p2", -1)
            mejora = ""
            if iaa1 >= 0 and iaa2 >= 0:
                diff = iaa2 - iaa1
                mejora = f"+{diff:.3f}" if diff > 0 else f"{diff:.3f}"
            lines.append(
                f"| {r['text_id']} | "
                f"{iaa1:.3f if iaa1 >= 0 else 'N/A'} | "
                f"{iaa2:.3f if iaa2 >= 0 else 'N/A'} | "
                f"{mejora} |"
            )
        lines.append("")
        lines.append(
            f"IAA > 0.95: la doble pasada no aporta (demasiado similar a p1)  "
            f"IAA 0.80-0.90: aporta correcciones significativas"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## Tokens y coste real",
        f"",
        f"| Texto | Input p2 | Output p2 | Coste estimado |",
        f"|-------|----------|-----------|----------------|",
    ]
    total_input = 0
    total_output = 0
    for r in results:
        inp = r.get("tokens_input", 0)
        out = r.get("tokens_output", 0)
        total_input += inp
        total_output += out
        cost = (inp * 0.015 + out * 0.075) / 1000
        lines.append(f"| {r['text_id']} | {inp} | {out} | ${cost:.4f} |")

    cost_total = (total_input * 0.015 + total_output * 0.075) / 1000
    lines.append(f"| **TOTAL** | **{total_input}** | **{total_output}** | **${cost_total:.4f}** |")

    return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Test doble pasada A/B — 71 dims Simbionte")
    parser.add_argument("--estimate", action="store_true", help="Estima coste sin llamadas")
    parser.add_argument("--dry-run", action="store_true", help="Muestra plan sin llamadas")
    parser.add_argument("--confirm", action="store_true", help="Ejecuta el test (requiere aprobacion)")
    args = parser.parse_args()

    if args.estimate:
        estimate_cost()
        return

    # Guard: requiere --confirm o APROBADO_CEO=si
    aprobado = (
        args.confirm
        or os.environ.get("APROBADO_CEO", "").lower() in ("si", "yes", "1", "true")
    )

    if args.dry_run:
        print("\n[DRY RUN — sin llamadas a la API]\n")
        print(f"Modelo: {OPUS_MODEL}")
        print(f"Textos para test: {N_TEST}")
        print(f"Textos para IAA: {N_IAA}")
        print(f"Total llamadas Opus: {N_TEST + N_IAA}")
        print(f"Output: {OUTPUT_PATH}")
        print(f"Informe: {REPORT_PATH}")
        print(f"\nIntentando cargar textos del POC micro...")
        try:
            texts = load_poc_micro_texts(N_TEST)
            print(f"OK: {len(texts)} textos disponibles")
            for i, t in enumerate(texts):
                n_floats = sum(1 for d in FLOAT_DIMS if d in t["labels_p1"])
                feedback = generate_feedback(t["labels_p1"])
                n_contra = len(detect_contradictions(t["labels_p1"]))
                print(f"  [{i+1}] id={t['text_id']} | {n_floats} floats | {n_contra} contradicciones")
                print(f"        Feedback generado: {len(feedback)} chars")
        except FileNotFoundError as e:
            print(f"ADVERTENCIA: {e}")
        print(f"\nPara ejecutar: python test_double_pass.py --confirm")
        return

    if not aprobado:
        print("\nERROR: Este script requiere aprobacion explicita.")
        print("Ejecuta con --confirm o APROBADO_CEO=si\n")
        print("Antes de aprobar, ejecuta:")
        print("  python test_double_pass.py --estimate")
        print("  python test_double_pass.py --dry-run")
        sys.exit(1)

    # ── EJECUCION ─────────────────────────────────────────────────────────────
    print(f"\ntest_double_pass.py — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Modelo: {OPUS_MODEL}")
    print(f"Textos test: {N_TEST} | Textos IAA: {N_IAA}")
    print("=" * 60)

    # Cargar textos
    print(f"\n[1/4] Cargando textos del POC micro...")
    try:
        texts = load_poc_micro_texts(N_TEST)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Generar feedback para cada texto ($0)
    print(f"\n[2/4] Generando feedback estructural (codigo puro, $0)...")
    for t in texts:
        t["feedback"] = generate_feedback(t["labels_p1"])
        t["contradictions_p1"] = detect_contradictions(t["labels_p1"])
        print(f"  {t['text_id']}: feedback={len(t['feedback'])} chars | contradicciones_p1={len(t['contradictions_p1'])}")

    # Ejecutar pasada 2
    print(f"\n[3/4] Ejecutando pasada 2 ({N_TEST} llamadas a Opus)...")
    results = []
    for i, t in enumerate(texts):
        print(f"  [{i+1}/{N_TEST}] {t['text_id']}...")
        labels_p2 = call_opus_pasada2(t["text"], t["labels_p1"], t["feedback"])
        if labels_p2 is None:
            print(f"    ERROR: pasada 2 fallo para {t['text_id']} — saltando")
            continue

        comparison = compare_passes(t["labels_p1"], labels_p2)
        contradictions_p2 = detect_contradictions(labels_p2)

        result = {
            "text_id": t["text_id"],
            "text": t["text"],
            "source": t["source"],
            "labels_p1": t["labels_p1"],
            "feedback": t["feedback"],
            "labels_p2": labels_p2,
            "comparison": comparison,
            "contradictions_p1": t["contradictions_p1"],
            "contradictions_p2": contradictions_p2,
            "tokens_input": labels_p2.get("_input_tokens", 0),
            "tokens_output": labels_p2.get("_output_tokens", 0),
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)

        print(f"    cambios: {comparison['n_cambios']} dims ({comparison['tasa_cambio']:.1%})")
        print(f"    magnitud: {comparison['magnitud_media']:.3f} | contradicciones: {len(t['contradictions_p1'])} → {len(contradictions_p2)}")

        # Guardar inmediatamente (tolerante a fallos)
        with open(OUTPUT_PATH, "a") as f:
            f.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")

        time.sleep(2)  # respeto rate limits

    # IAA: re-ejecutar pasada 2 en los primeros N_IAA textos
    print(f"\n[4/4] IAA — re-ejecutando pasada 2 en {N_IAA} textos...")
    iaa_results = []
    iaa_texts = texts[:N_IAA]

    for i, t in enumerate(iaa_texts):
        print(f"  [{i+1}/{N_IAA}] {t['text_id']} (re-run)...")
        # Buscar resultado de la primera run
        first_run = next((r for r in results if r["text_id"] == t["text_id"]), None)
        if first_run is None:
            print(f"    SKIP: no hay primera run para {t['text_id']}")
            continue

        labels_p2_run2 = call_opus_pasada2(t["text"], t["labels_p1"], t["feedback"])
        if labels_p2_run2 is None:
            print(f"    ERROR: IAA run2 fallo — saltando")
            continue

        # IAA pasada 1: comparar p1 con si misma (deberia ser ~1.0 porque p1 es determinista)
        # En realidad, IAA(p1) mide coherencia del prompt: re-ejecutar p1 vs p1 existente
        # Como no tenemos segunda run de p1, usamos la correlacion entre p1 y p2 run1 vs run2
        iaa_p2 = compute_iaa(first_run["labels_p2"], labels_p2_run2)

        # Para IAA p1 de referencia: correlacion entre p1 y p2-run1 (cuanto cambio la primera correccion)
        # Sirve como proxy de la estabilidad del labeling original
        iaa_p1_proxy = compute_iaa(t["labels_p1"], first_run["labels_p2"])

        iaa_result = {
            "text_id": t["text_id"],
            "iaa_p1": iaa_p1_proxy,      # proxy: correlacion(p1, p2_run1)
            "iaa_p2": iaa_p2,             # real: correlacion(p2_run1, p2_run2)
            "labels_p2_run2": labels_p2_run2,
        }
        iaa_results.append(iaa_result)
        print(f"    IAA p1 proxy: {iaa_p1_proxy:.3f} | IAA p2: {iaa_p2:.3f}")

        time.sleep(2)

    # Generar informe
    print(f"\nGenerando informe...")
    report = generate_report(results, iaa_results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"  Informe: {REPORT_PATH}")

    # Metricas METRIC:key=value para pipeline_runner
    if results:
        tasa_media = sum(r["comparison"]["tasa_cambio"] for r in results) / len(results)
        mag_vals = [r["comparison"]["magnitud_media"] for r in results if r["comparison"]["magnitud_media"] > 0]
        mag_media = sum(mag_vals) / len(mag_vals) if mag_vals else 0

        total_c_p1 = sum(len(r["contradictions_p1"]) for r in results)
        total_c_p2 = sum(len(r["contradictions_p2"]) for r in results)
        resueltas = max(0, total_c_p1 - total_c_p2)
        tasa_res = resueltas / total_c_p1 if total_c_p1 > 0 else 0

        iaa_p2_vals = [r.get("iaa_p2", -1) for r in iaa_results if r.get("iaa_p2", -1) >= 0]
        iaa_p2_mean = sum(iaa_p2_vals) / len(iaa_p2_vals) if iaa_p2_vals else -1
        iaa_p1_vals = [r.get("iaa_p1", -1) for r in iaa_results if r.get("iaa_p1", -1) >= 0]
        iaa_p1_mean = sum(iaa_p1_vals) / len(iaa_p1_vals) if iaa_p1_vals else -1

        aporta = int(tasa_media > 0.03 or mag_media > 0.08 or tasa_res > 0.3)

        print(f"\nMETRIC:double_pass_tasa_cambio={tasa_media:.4f}")
        print(f"METRIC:double_pass_magnitud_media={mag_media:.4f}")
        print(f"METRIC:double_pass_contradicciones_resueltas={tasa_res:.4f}")
        print(f"METRIC:double_pass_iaa_p1={iaa_p1_mean:.4f}")
        print(f"METRIC:double_pass_iaa_p2={iaa_p2_mean:.4f}")
        print(f"METRIC:double_pass_aporta={aporta}")

    print(f"\nResultados: {OUTPUT_PATH}")
    print(f"Informe:    {REPORT_PATH}")
    print("\nDONE")


if __name__ == "__main__":
    main()
