"""Exp 4.3: Mente Distribuida — Runner.
Shared blackboard architecture: 10 models contribute diffs over micro-rounds.
One collective evaluation emerges from distributed cognition.
"""
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path
from copy import deepcopy

from dotenv import load_dotenv
import requests as _requests

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data" / "evaluator_test_set"
RESULTS_DIR = BASE_DIR / "results"
PIZARRAS_FILE = RESULTS_DIR / "exp4_3_pizarras_finales.json"
CONTRIB_FILE = RESULTS_DIR / "exp4_3_contribuciones_por_modelo.json"
EXP4_R1_FILE = RESULTS_DIR / "exp4_ronda1_completa.json"
TEST_OUTPUTS_FILE = DATA_DIR / "test_outputs.json"

PROVIDERS = {
    "together":  {"api_key": os.getenv("TOGETHER_API_KEY")},
    "deepseek":  {"api_key": os.getenv("DEEPSEEK_API_KEY")},
    "anthropic": {"api_key": os.getenv("ANTHROPIC_API_KEY")},
}

# ── Active models (Sonnet pre-loaded, these are called) ─────────
ACTIVE_MODELS = {
    "opus":           {"id": "claude-opus-4-20250514",                     "provider": "anthropic", "timeout": 180},
    "v3.2-chat":      {"id": "deepseek-chat",                             "provider": "deepseek",  "timeout": 90},
    "v3.2-reasoner":  {"id": "deepseek-reasoner",                         "provider": "deepseek",  "timeout": 300},
    "gpt-oss-120b":   {"id": "openai/gpt-oss-120b",                       "provider": "together",  "timeout": 180},
    "qwen3-235b":     {"id": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",   "provider": "together",  "timeout": 180},
    "deepseek-v3.1":  {"id": "deepseek-ai/DeepSeek-V3.1",                 "provider": "together",  "timeout": 180},
    "deepseek-r1":    {"id": "deepseek-ai/DeepSeek-R1",                   "provider": "together",  "timeout": 300},
    "glm-4.7":        {"id": "zai-org/GLM-4.7",                           "provider": "together",  "timeout": 180},
    "minimax-m2.5":   {"id": "MiniMaxAI/MiniMax-M2.5",                    "provider": "together",  "timeout": 180},
    "kimi-k2.5":      {"id": "moonshotai/Kimi-K2.5",                      "provider": "together",  "timeout": 300},
    "cogito-671b":    {"id": "deepcogito/cogito-v2-1-671b",               "provider": "together",  "timeout": 180},
}

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]

LENTES = ["Salud", "Sentido", "Continuidad"]
FUNCIONES = ["Conservar", "Captar", "Depurar", "Distribuir", "Frontera", "Adaptar", "Replicar"]
ALL_CELLS = ["%s\u00d7%s" % (l, f) for l in LENTES for f in FUNCIONES]

MAX_RONDAS = 5
MIN_CAMBIOS = 3

# ── System Prompt ────────────────────────────────────────────────
SYSTEM_CONTRIB = (
    "Eres una region de un cerebro colectivo. NO estas haciendo tu propia evaluacion. Estas contribuyendo al ESTADO COMPARTIDO de una mente distribuida.\n\n"
    "Recibes:\n"
    "- Un output para evaluar\n"
    "- El estado actual de la PIZARRA (la evaluacion colectiva en construccion)\n\n"
    "Tu trabajo:\n"
    "1. LEE la pizarra. Mira que celdas ya estan cubiertas y a que nivel.\n"
    "2. CONTRIBUYE solo donde puedes ANADIR VALOR:\n"
    "   - Celdas vacias (nivel 0) que puedes llenar con evidencia del output\n"
    "   - Celdas con nivel bajo que puedes subir con evidencia mas profunda\n"
    "   - Conexiones entre celdas que ves ahora que el mapa tiene contenido\n"
    "   - Puntos ciegos: celdas que deberian tener algo pero estan vacias\n"
    "3. NO repitas lo que ya esta. Si una celda tiene nivel 3 con buena evidencia, dejala.\n"
    "4. NO bajes niveles. Solo sube o deja igual.\n"
    "5. Se CONCISO. Solo contribuyes donde tienes algo nuevo.\n\n"
    "NIVELES: 0=no toca, 1=mencion generica, 2=dato/inferencia especifica, 3=revela algo no obvio, 4=redefine la pregunta.\n\n"
    "FORMATO DE RESPUESTA (JSON):\n"
    '{"contribuciones":[{"celda":"Salud\u00d7Conservar","accion":"subir","nivel_actual":2,"nivel_propuesto":3,"evidencia_nueva":"...","razon":"..."}],'
    '"conexiones":[{"celda_a":"X\u00d7Y","celda_b":"W\u00d7Z","conexion":"..."}],'
    '"puntos_ciegos":[{"celda":"X\u00d7Y","razon":"..."}],'
    '"sin_contribucion":false}\n\n'
    'Si no tienes NADA que anadir, responde:\n'
    '{"contribuciones":[],"conexiones":[],"puntos_ciegos":[],"sin_contribucion":true}'
)


# ── JSON Extraction ──────────────────────────────────────────────
def extract_json(text):
    if not text or not text.strip():
        return None
    if "</think>" in text:
        text = text.split("</think>")[-1]
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


# ── API Calls ────────────────────────────────────────────────────
def call_together(model_cfg, system_prompt, user_prompt):
    timeout = model_cfg.get("timeout", 180)
    t0 = time.time()
    resp = _requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + PROVIDERS["together"]["api_key"],
            "Content-Type": "application/json",
        },
        json={
            "model": model_cfg["id"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 4096,
        },
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)
    if resp.status_code != 200:
        raise RuntimeError("Together %d: %s" % (resp.status_code, resp.text[:300]))
    data = resp.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning", "") or ""
    if not content.strip() and reasoning.strip():
        content = reasoning
    return content, elapsed


def call_deepseek(model_cfg, system_prompt, user_prompt):
    body = {
        "model": model_cfg["id"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 4096,
    }
    if model_cfg["id"] != "deepseek-reasoner":
        body["temperature"] = 0.0
    timeout = model_cfg.get("timeout", 180)
    t0 = time.time()
    resp = _requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": "Bearer " + PROVIDERS["deepseek"]["api_key"],
            "Content-Type": "application/json",
        },
        json=body,
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)
    if resp.status_code != 200:
        raise RuntimeError("DeepSeek %d: %s" % (resp.status_code, resp.text[:300]))
    data = resp.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning_content", "") or ""
    if not content.strip() and reasoning.strip():
        content = reasoning
    return content, elapsed


def call_anthropic(model_cfg, system_prompt, user_prompt):
    timeout = model_cfg.get("timeout", 180)
    t0 = time.time()
    resp = _requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": PROVIDERS["anthropic"]["api_key"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model_cfg["id"],
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)
    if resp.status_code != 200:
        raise RuntimeError("Anthropic %d: %s" % (resp.status_code, resp.text[:300]))
    data = resp.json()
    content = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            content += block.get("text", "")
    return content, elapsed


def call_model(model_name, model_cfg, system_prompt, user_prompt):
    provider = model_cfg["provider"]
    if provider == "together":
        return call_together(model_cfg, system_prompt, user_prompt)
    elif provider == "deepseek":
        return call_deepseek(model_cfg, system_prompt, user_prompt)
    elif provider == "anthropic":
        return call_anthropic(model_cfg, system_prompt, user_prompt)
    raise ValueError("Unknown provider: " + provider)


# ── Pizarra ──────────────────────────────────────────────────────
def crear_pizarra_vacia():
    """Create empty blackboard."""
    celdas = {}
    for cell in ALL_CELLS:
        celdas[cell] = {
            "nivel": 0,
            "evidencias": [],
            "nivel_historial": [0],
            "ultima_modificacion": None,
        }
    return {
        "estado": "en_curso",
        "micro_ronda": 0,
        "celdas": celdas,
        "conexiones": [],
        "puntos_ciegos": [],
        "meta": {
            "cambios_por_ronda": [],
            "convergencia": False,
            "rondas_total": 0,
        },
    }


def seed_pizarra_con_sonnet(pizarra, sonnet_celdas):
    """Pre-load Sonnet's R1 evaluation into pizarra as ronda -1."""
    cambios = 0
    for celda_key, val in sonnet_celdas.items():
        if celda_key not in pizarra["celdas"]:
            continue
        nivel = val.get("nivel", 0) if isinstance(val, dict) else 0
        evidencia = val.get("evidencia", "") if isinstance(val, dict) else ""
        if nivel > 0:
            pizarra["celdas"][celda_key]["nivel"] = nivel
            pizarra["celdas"][celda_key]["evidencias"].append({
                "texto": evidencia,
                "fuente": "sonnet",
                "ronda": -1,
            })
            pizarra["celdas"][celda_key]["nivel_historial"].append(nivel)
            pizarra["celdas"][celda_key]["ultima_modificacion"] = {
                "modelo": "sonnet",
                "ronda": -1,
            }
            cambios += 1
    return cambios


def build_pizarra_prompt(item, pizarra, ronda):
    """Build user prompt with output + current pizarra state."""
    # Compact pizarra view for the prompt
    pizarra_compact = {}
    for cell, data in pizarra["celdas"].items():
        nivel = data["nivel"]
        evidencias = [e["texto"] for e in data["evidencias"][-3:]]  # Last 3 evidences
        pizarra_compact[cell] = {
            "nivel": nivel,
            "evidencias": evidencias,
        }

    pizarra_str = json.dumps(pizarra_compact, ensure_ascii=False, indent=1)
    conn_str = json.dumps(pizarra["conexiones"][-10:], ensure_ascii=False) if pizarra["conexiones"] else "[]"

    return (
        "OUTPUT A EVALUAR:\n---\n%s\n---\n\n"
        "CASO: %s | INTELIGENCIA: %s — %s\n\n"
        "ESTADO ACTUAL DE LA PIZARRA (micro-ronda %d):\n%s\n\n"
        "CONEXIONES DETECTADAS HASTA AHORA:\n%s\n\n"
        "Que puedes contribuir al estado compartido? Anade solo donde tengas valor nuevo. JSON puro."
    ) % (item["output"], item["case_nombre"], item["int_id"], item["int_nombre"], ronda, pizarra_str, conn_str)


def merge_contribuciones(pizarra, contribuciones_por_modelo, ronda):
    """Merge all models' contributions into the pizarra."""
    cambios = 0

    for modelo, contrib in contribuciones_por_modelo.items():
        if not contrib or contrib.get("sin_contribucion"):
            continue

        for c in contrib.get("contribuciones", []):
            celda = c.get("celda", "")
            if celda not in pizarra["celdas"]:
                continue
            nivel_propuesto = c.get("nivel_propuesto", 0)
            nivel_actual = pizarra["celdas"][celda]["nivel"]

            if nivel_propuesto > nivel_actual:
                pizarra["celdas"][celda]["nivel"] = nivel_propuesto
                pizarra["celdas"][celda]["evidencias"].append({
                    "texto": c.get("evidencia_nueva", ""),
                    "fuente": modelo,
                    "ronda": ronda,
                })
                pizarra["celdas"][celda]["nivel_historial"].append(nivel_propuesto)
                pizarra["celdas"][celda]["ultima_modificacion"] = {
                    "modelo": modelo,
                    "ronda": ronda,
                }
                cambios += 1
            elif nivel_propuesto == nivel_actual and c.get("evidencia_nueva"):
                # Same level but new evidence — add it
                pizarra["celdas"][celda]["evidencias"].append({
                    "texto": c.get("evidencia_nueva", ""),
                    "fuente": modelo,
                    "ronda": ronda,
                })

        # Merge conexiones
        for conn in contrib.get("conexiones", []):
            conn["fuente"] = modelo
            conn["ronda"] = ronda
            pizarra["conexiones"].append(conn)

        # Merge puntos ciegos
        for pc in contrib.get("puntos_ciegos", []):
            pc["fuente"] = modelo
            pc["ronda"] = ronda
            pizarra["puntos_ciegos"].append(pc)

    return cambios


# ── Load Data ────────────────────────────────────────────────────
def load_test_outputs():
    with open(TEST_OUTPUTS_FILE, encoding="utf-8") as f:
        items = json.load(f)
    return {item["id"]: item for item in items}


def load_sonnet_r1():
    """Load Sonnet evaluations from Exp 4 R1."""
    with open(EXP4_R1_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("evaluaciones", {}).get("sonnet", {})


# ── Run Distributed Mind ─────────────────────────────────────────
def run_one_output(oid, item, sonnet_celdas):
    """Run distributed mind for a single output."""
    print("\n  --- Output: %s ---" % oid)

    # Create and seed pizarra
    pizarra = crear_pizarra_vacia()
    if oid in sonnet_celdas and sonnet_celdas[oid].get("celdas"):
        n_seed = seed_pizarra_con_sonnet(pizarra, sonnet_celdas[oid]["celdas"])
        print("  Sonnet seed: %d celdas" % n_seed)

    # Track consecutive sin_contribucion per model
    sin_contrib_streak = {}  # model -> count
    model_stats = {}  # model -> {contribuciones, conexiones, puntos_ciegos, rondas_activas}

    for modelo in ACTIVE_MODELS:
        sin_contrib_streak[modelo] = 0
        model_stats[modelo] = {
            "contribuciones_aceptadas": 0,
            "conexiones": 0,
            "puntos_ciegos": 0,
            "rondas_activas": 0,
            "contribuciones_por_ronda": [],
        }

    for ronda in range(MAX_RONDAS):
        pizarra["micro_ronda"] = ronda
        print("\n  Micro-ronda %d:" % ronda, flush=True)

        # Snapshot pizarra for this round (all models see same state)
        pizarra_snapshot = deepcopy(pizarra)
        contribuciones = {}

        for modelo, cfg in ACTIVE_MODELS.items():
            provider = cfg["provider"]
            if not PROVIDERS.get(provider, {}).get("api_key"):
                continue

            # Skip if 2 consecutive sin_contribucion
            if sin_contrib_streak.get(modelo, 0) >= 2:
                print("    [%s] skipped (2x sin contribucion)" % modelo, flush=True)
                continue

            user_prompt = build_pizarra_prompt(item, pizarra_snapshot, ronda)
            print("    [%s]..." % modelo, end=" ", flush=True)

            parsed = None
            for attempt in range(2):
                try:
                    prompt = user_prompt
                    if attempt == 1:
                        prompt += "\n\nIMPORTANTE: Responde SOLO con JSON valido."
                    content, elapsed = call_model(modelo, cfg, SYSTEM_CONTRIB, prompt)
                    parsed = extract_json(content)
                    if parsed is not None:
                        break
                    if attempt == 0:
                        print("(retry)", end=" ", flush=True)
                        time.sleep(2)
                except Exception as e:
                    err = str(e)
                    if attempt == 0:
                        wait = 30 if ("rate" in err.lower() or "429" in err) else 5
                        print("(err, wait %ds)" % wait, end=" ", flush=True)
                        time.sleep(wait)

            if parsed:
                contribuciones[modelo] = parsed
                n_contribs = len(parsed.get("contribuciones", []))
                n_conn = len(parsed.get("conexiones", []))
                n_pc = len(parsed.get("puntos_ciegos", []))
                is_sin = parsed.get("sin_contribucion", False)

                if is_sin or n_contribs == 0:
                    sin_contrib_streak[modelo] = sin_contrib_streak.get(modelo, 0) + 1
                    print("sin contribucion (%.1fs)" % elapsed)
                else:
                    sin_contrib_streak[modelo] = 0
                    model_stats[modelo]["rondas_activas"] += 1
                    print("%d contribs, %d conn, %d pc (%.1fs)" % (n_contribs, n_conn, n_pc, elapsed))
            else:
                print("FAIL")

            time.sleep(2)

        # Merge all contributions
        cambios = merge_contribuciones(pizarra, contribuciones, ronda)
        pizarra["meta"]["cambios_por_ronda"].append(cambios)

        # Update model stats
        for modelo, contrib in contribuciones.items():
            if not contrib or contrib.get("sin_contribucion"):
                model_stats[modelo]["contribuciones_por_ronda"].append(0)
                continue
            n_c = len(contrib.get("contribuciones", []))
            model_stats[modelo]["contribuciones_aceptadas"] += n_c
            model_stats[modelo]["conexiones"] += len(contrib.get("conexiones", []))
            model_stats[modelo]["puntos_ciegos"] += len(contrib.get("puntos_ciegos", []))
            model_stats[modelo]["contribuciones_por_ronda"].append(n_c)

        # Count cells covered and nivel
        n_covered = sum(1 for c in pizarra["celdas"].values() if c["nivel"] > 0)
        n_3plus = sum(1 for c in pizarra["celdas"].values() if c["nivel"] >= 3)
        niveles = [c["nivel"] for c in pizarra["celdas"].values()]
        medio = sum(niveles) / max(len(niveles), 1)
        print("  -> %d cambios, %d/21 cubiertas, %d nivel 3+, medio=%.2f" % (cambios, n_covered, n_3plus, medio))

        # Check convergence
        if cambios < MIN_CAMBIOS:
            pizarra["estado"] = "convergido"
            pizarra["meta"]["convergencia"] = True
            print("  CONVERGENCIA en ronda %d (<%d cambios)" % (ronda, MIN_CAMBIOS))
            break

    pizarra["meta"]["rondas_total"] = ronda + 1
    if not pizarra["meta"]["convergencia"]:
        pizarra["estado"] = "max_rondas"
        print("  MAX RONDAS alcanzado (%d)" % MAX_RONDAS)

    return pizarra, model_stats


def run_distributed_mind():
    """Run distributed mind for all 5 outputs."""
    test_outputs = load_test_outputs()
    sonnet_data = load_sonnet_r1()

    # Check for existing results
    if PIZARRAS_FILE.exists():
        with open(PIZARRAS_FILE, encoding="utf-8") as f:
            existing = json.load(f)
        pizarras = existing.get("pizarras", {})
        all_stats = existing.get("contribuciones_por_modelo", {})
    else:
        pizarras = {}
        all_stats = {}

    # Filter by --output if provided
    output_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--output="):
            output_filter = arg.split("=", 1)[1]

    oids = OUTPUT_IDS
    if output_filter:
        oids = [o for o in oids if o == output_filter]

    for oid in oids:
        # Skip if already complete
        if oid in pizarras and pizarras[oid].get("estado") in ("convergido", "max_rondas"):
            n_cov = sum(1 for c in pizarras[oid]["celdas"].values() if c["nivel"] > 0)
            print("\n  %s: already done (%s, %d/21 cubiertas)" % (oid, pizarras[oid]["estado"], n_cov))
            continue

        item = test_outputs[oid]
        pizarra, model_stats = run_one_output(oid, item, sonnet_data)
        pizarras[oid] = pizarra

        # Merge model stats
        for modelo, stats in model_stats.items():
            if modelo not in all_stats:
                all_stats[modelo] = {
                    "contribuciones_aceptadas": 0,
                    "conexiones": 0,
                    "puntos_ciegos": 0,
                    "rondas_activas": 0,
                    "outputs_participados": 0,
                    "por_output": {},
                }
            all_stats[modelo]["contribuciones_aceptadas"] += stats["contribuciones_aceptadas"]
            all_stats[modelo]["conexiones"] += stats["conexiones"]
            all_stats[modelo]["puntos_ciegos"] += stats["puntos_ciegos"]
            all_stats[modelo]["rondas_activas"] += stats["rondas_activas"]
            all_stats[modelo]["outputs_participados"] += 1
            all_stats[modelo]["por_output"][oid] = stats

        # Save after each output
        save_results(pizarras, all_stats)

    return pizarras, all_stats


def save_results(pizarras, all_stats):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "meta": {
            "experiment": "Exp 4.3 - Mente Distribuida",
            "date": str(date.today()),
            "n_outputs": len(pizarras),
            "n_models_active": len(ACTIVE_MODELS),
        },
        "pizarras": pizarras,
        "contribuciones_por_modelo": all_stats,
    }
    with open(PIZARRAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("=== EXP 4.3: MENTE DISTRIBUIDA ===")
    print("%d modelos activos + Sonnet (pre-cargado)" % len(ACTIVE_MODELS))
    print("5 outputs x max %d micro-rondas\n" % MAX_RONDAS)

    for prov, cfg in PROVIDERS.items():
        s = "OK" if cfg.get("api_key") else "MISSING"
        print("  %s: %s" % (prov, s))

    pizarras, all_stats = run_distributed_mind()

    # Summary
    print("\n\n=== RESUMEN ===")
    for oid in OUTPUT_IDS:
        if oid in pizarras:
            p = pizarras[oid]
            n_cov = sum(1 for c in p["celdas"].values() if c["nivel"] > 0)
            n_3p = sum(1 for c in p["celdas"].values() if c["nivel"] >= 3)
            niveles = [c["nivel"] for c in p["celdas"].values()]
            medio = sum(niveles) / max(len(niveles), 1)
            rondas = p["meta"]["rondas_total"]
            estado = p["estado"]
            n_conn = len(p["conexiones"])
            n_pc = len(p["puntos_ciegos"])
            print("  %s: %s en %d rondas, %d/21 cubiertas, %d nivel 3+, medio=%.2f, %d conn, %d pc" % (
                oid, estado, rondas, n_cov, n_3p, medio, n_conn, n_pc
            ))

    print("\n  Top contribuidores:")
    sorted_models = sorted(all_stats.items(), key=lambda x: x[1]["contribuciones_aceptadas"], reverse=True)
    for modelo, stats in sorted_models[:5]:
        print("    %s: %d contribuciones, %d conexiones, %d puntos ciegos" % (
            modelo, stats["contribuciones_aceptadas"], stats["conexiones"], stats["puntos_ciegos"]
        ))

    print("\nDONE")
    print("Pizarras: %s" % PIZARRAS_FILE)


if __name__ == "__main__":
    main()
