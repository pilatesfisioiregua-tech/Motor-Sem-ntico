"""Exp 4.1: Mesa Redonda Especializada — Runner.
Each model gets a prompt tuned to its empirical strength.
R1 specializada + R2 enriquecimiento. Compara con Exp 4 genérico.
"""
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
import requests as _requests

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data" / "evaluator_test_set"
RESULTS_DIR = BASE_DIR / "results"
R1_FILE = RESULTS_DIR / "exp4_1_ronda1_especializada.json"
R2_FILE = RESULTS_DIR / "exp4_1_ronda2.json"
EXP4_R1_FILE = RESULTS_DIR / "exp4_ronda1_completa.json"
TEST_OUTPUTS_FILE = DATA_DIR / "test_outputs.json"

# ── Providers ────────────────────────────────────────────────────
PROVIDERS = {
    "together":  {"api_key": os.getenv("TOGETHER_API_KEY")},
    "deepseek":  {"api_key": os.getenv("DEEPSEEK_API_KEY")},
    "anthropic": {"api_key": os.getenv("ANTHROPIC_API_KEY")},
}

# ── Models (same as exp4, minus Sonnet which is pre-loaded, minus M1 which is unavailable) ─────
ALL_MODELS = {
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

ALL_ACTIVE = [
    "opus", "v3.2-chat", "v3.2-reasoner", "deepseek-r1",
    "deepseek-v3.1", "cogito-671b", "gpt-oss-120b", "qwen3-235b",
    "minimax-m2.5", "kimi-k2.5", "glm-4.7",
]

ALL_WITH_SONNET = ALL_ACTIVE + ["sonnet"]

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]

# ── Shared system prompt part ───────────────────────────────────
SYSTEM_COMMON = (
    "Eres un evaluador de profundidad analitica. Tu tarea es mapear un output de analisis a la Matriz 3Lx7F y asignar un nivel de profundidad a cada celda.\n\n"
    "3 LENTES: Salud (funciona/recursos/estructura), Sentido (direccion/proposito/identidad), Continuidad (sobrevive/legado/replicabilidad).\n"
    "7 FUNCIONES: Conservar (mantener), Captar (incorporar), Depurar (eliminar sobra), Distribuir (repartir), Frontera (limites), Adaptar (cambio), Replicar (copiar patron).\n\n"
    "NIVELES: 0=no toca, 1=mencion generica, 2=dato/inferencia especifica del caso, 3=revela algo no obvio (contradiccion/patron invisible), 4=redefine la pregunta.\n\n"
    "REGLAS: Evalua SOLO lo que dice el output. Evidencia = cita corta. Celda ausente = nivel 0. Se estricto: 3 requiere genuina no-obviedad, 4 genuina redefinicion. No infles.\n\n"
    "Debes evaluar LAS 21 CELDAS. Pero tu FOCO PRINCIPAL es el que se indica abajo. En tu foco, se especialmente exhaustivo: busca la evidencia mas profunda, las contradicciones mas sutiles, los patrones menos obvios. En el resto de celdas, evalua normalmente.\n\n"
)

# ── Specialized focus per model ─────────────────────────────────
SPECIALIZED_FOCUS = {
    "cogito-671b": (
        "TU FOCO PRINCIPAL: Sentido y Frontera.\n\n"
        "En Sentido (las 7 funciones desde la lente de direccion/proposito/identidad):\n"
        "- Que direccion tiene el sujeto del caso? Es genuina o prestada?\n"
        "- Hay contradiccion entre lo que dice que quiere y lo que hace?\n"
        "- El proposito declarado es una mascara de otro proposito mas profundo?\n\n"
        "En Frontera (las 3 lentes desde la funcion de distinguir propio de ajeno):\n"
        "- Donde estan los limites del caso? Son claros o difusos?\n"
        "- Que se fuga que no deberia? Que entra que no deberia?\n"
        "- El sujeto sabe donde termina el y empieza el otro?\n\n"
        "Busca nivel 3-4 agresivamente en estas celdas. Si hay algo no obvio, encuentralo."
    ),
    "deepseek-r1": (
        "TU FOCO PRINCIPAL: Continuidad.\n\n"
        "En las 7 funciones desde la lente de lo que sobrevive al sistema:\n"
        "- Que patrones del caso sobrevivirian si el sujeto desaparece?\n"
        "- Que se esta transmitiendo (conscientemente o no)?\n"
        "- Que se pierde si esto no cambia? Que legado se esta construyendo sin querer?\n"
        "- Hay algo que se replica pero no deberia? Algo que deberia replicarse pero no lo hace?\n\n"
        "Usa tu capacidad de razonamiento paso a paso para deducir las implicaciones a largo plazo que el output describe pero no nombra explicitamente."
    ),
    "deepseek-v3.1": (
        "TU FOCO PRINCIPAL: Frontera y Conservar.\n\n"
        "En Frontera (distinguir propio de ajeno, en las 3 lentes):\n"
        "- Que limites identifica el output? Son los correctos?\n"
        "- Hay limites que el output no ve pero deberia?\n"
        "- Se confunde lo propio con lo ajeno en algun punto?\n\n"
        "En Conservar (mantener forma, en las 3 lentes):\n"
        "- Que se esta intentando conservar? Vale la pena?\n"
        "- Hay algo que se conserva por inercia, no por valor?\n"
        "- El output detecta que es estructural vs que es accidental?"
    ),
    "v3.2-chat": (
        "TU FOCO PRINCIPAL: Detectar contradicciones y patrones que cruzan varias celdas.\n\n"
        "No te limites a evaluar celda por celda. Busca:\n"
        "- Contradicciones entre lo que el output dice en una celda y lo que implica en otra\n"
        "- Patrones que aparecen en Salud y se repiten en Sentido o Continuidad\n"
        "- Dependencias ocultas: hay celdas que parecen independientes pero estan conectadas?\n"
        "- Lo que el output EVITA decir — los silencios significativos\n\n"
        "Donde detectes una contradiccion o patron invisible, sube a nivel 3 o 4 con la evidencia especifica."
    ),
    "gpt-oss-120b": (
        "TU FOCO PRINCIPAL: Depurar y Captar.\n\n"
        "En Depurar (eliminar lo que sobra o dana, en las 3 lentes):\n"
        "- Que identifica el output como toxico, innecesario o danino?\n"
        "- Hay cosas que deberian depurarse pero el output las normaliza?\n"
        "- El output confunde 'importante' con 'urgente'?\n\n"
        "En Captar (incorporar lo necesario, en las 3 lentes):\n"
        "- Que senales capta el output? Cuales ignora?\n"
        "- Hay informacion disponible que el output no procesa?\n"
        "- Se capta lo facil pero se pierde lo sutil?"
    ),
    "qwen3-235b": (
        "TU FOCO PRINCIPAL: No dejar ninguna celda vacia.\n\n"
        "Tu fortaleza es la cobertura. Otros modelos profundizan en areas especificas. Tu trabajo es asegurar que TODAS las 21 celdas tienen al menos nivel 1, e idealmente nivel 2.\n\n"
        "Para cada celda, preguntate: el output dice ALGO sobre esta celda, por indirecto que sea? Si si -> nivel >= 1 con evidencia. Si genuinamente no -> nivel 0.\n\n"
        "Se el modelo que no se deja nada. Los demas profundizaran donde tu senales."
    ),
    "v3.2-reasoner": (
        "TU FOCO PRINCIPAL: Como el sujeto del caso incorpora significado y como lo distribuye.\n\n"
        "- Captar x Sentido: Que experiencias alimentan el proposito del sujeto? Capta las senales correctas?\n"
        "- Distribuir x Sentido: La energia del sujeto va a lo que importa? O se dispersa en lo urgente?\n\n"
        "Usa tu modo de razonamiento profundo para inferir las motivaciones que el output describe implicitamente."
    ),
    "glm-4.7": (
        "TU FOCO PRINCIPAL: Sentido.\n\n"
        "En Exp 2 fuiste el mejor evaluando Sentido (Spearman 0.755). Repite eso aqui pero con mas profundidad:\n"
        "- El output captura la direccion real del sujeto o solo la superficial?\n"
        "- Hay sentido declarado vs sentido vivido? Coinciden?\n"
        "- El caso tiene un sentido que el propio sujeto no ve?\n\n"
        "Se agresivo buscando nivel 3-4 en las 7 funciones de Sentido."
    ),
    "kimi-k2.5": (
        "TU FOCO PRINCIPAL: Adaptar (respuesta al cambio, en las 3 lentes).\n\n"
        "- Como responde el sujeto al cambio? Se adapta o se rigidiza?\n"
        "- La adaptacion es real o es evitacion disfrazada?\n"
        "- Que deberia cambiar que no esta cambiando? Que esta cambiando que no deberia?\n"
        "- Adaptar x Salud: la operacion se ajusta?\n"
        "- Adaptar x Sentido: el proposito evoluciona?\n"
        "- Adaptar x Continuidad: el legado se actualiza?"
    ),
    "minimax-m2.5": (
        "TU FOCO PRINCIPAL: Lo practico y accionable.\n\n"
        "En Distribuir (repartir recursos, en las 3 lentes):\n"
        "- Se identifican acciones concretas? Tienen coste y plazo?\n"
        "- Los recursos van donde toca o hay fugas?\n\n"
        "En Replicar (copiar el patron, en las 3 lentes):\n"
        "- Hay algo replicable en lo que el output propone?\n"
        "- Se puede escalar o es una solucion unica?\n\n"
        "Evalua con ojo practico: esto se puede HACER o es solo teoria?"
    ),
    "opus": (
        "TU FOCO PRINCIPAL: Vision de conjunto y meta-patrones cross-celda.\n\n"
        "Busca:\n"
        "- Conexiones entre el inicio y el final que otros podrian no ver\n"
        "- Evolucion del argumento a lo largo del output\n"
        "- Inconsistencias entre secciones diferentes del output\n"
        "- Patrones que cruzan las 3 lentes y revelan algo sobre el sistema completo"
    ),
}

JSON_FORMAT = (
    'Responde EXCLUSIVAMENTE con JSON valido. Sin texto ni markdown.\n'
    '{"celdas":{"Salud\u00d7Conservar":{"nivel":N,"evidencia":"..."},"Salud\u00d7Captar":{"nivel":N,"evidencia":"..."},'
    '"Salud\u00d7Depurar":{"nivel":N,"evidencia":"..."},"Salud\u00d7Distribuir":{"nivel":N,"evidencia":"..."},'
    '"Salud\u00d7Frontera":{"nivel":N,"evidencia":"..."},"Salud\u00d7Adaptar":{"nivel":N,"evidencia":"..."},'
    '"Salud\u00d7Replicar":{"nivel":N,"evidencia":"..."},"Sentido\u00d7Conservar":{"nivel":N,"evidencia":"..."},'
    '"Sentido\u00d7Captar":{"nivel":N,"evidencia":"..."},"Sentido\u00d7Depurar":{"nivel":N,"evidencia":"..."},'
    '"Sentido\u00d7Distribuir":{"nivel":N,"evidencia":"..."},"Sentido\u00d7Frontera":{"nivel":N,"evidencia":"..."},'
    '"Sentido\u00d7Adaptar":{"nivel":N,"evidencia":"..."},"Sentido\u00d7Replicar":{"nivel":N,"evidencia":"..."},'
    '"Continuidad\u00d7Conservar":{"nivel":N,"evidencia":"..."},"Continuidad\u00d7Captar":{"nivel":N,"evidencia":"..."},'
    '"Continuidad\u00d7Depurar":{"nivel":N,"evidencia":"..."},"Continuidad\u00d7Distribuir":{"nivel":N,"evidencia":"..."},'
    '"Continuidad\u00d7Frontera":{"nivel":N,"evidencia":"..."},"Continuidad\u00d7Adaptar":{"nivel":N,"evidencia":"..."},'
    '"Continuidad\u00d7Replicar":{"nivel":N,"evidencia":"..."}}}'
)

SYSTEM_R2 = (
    "Eres un evaluador experto en una mesa redonda de enriquecimiento colectivo. "
    "Ya evaluaste un output. Ahora ves las evaluaciones de tus colegas.\n\n"
    "Tu tarea es ENRIQUECER, no debatir:\n"
    "1. MIRA lo que vieron tus colegas que tu no viste\n"
    "2. INCORPORA lo valido — sube niveles donde encontraron evidencia que pasaste por alto\n"
    "3. APORTA lo que solo tu detectaste\n"
    "4. MANTEN tus scores validos aunque otros no los vean\n"
    "5. SENALA angulos genuinamente diferentes\n\n"
    "REGLAS:\n"
    "- NO bajes scores. Solo sube si descubres evidencia nueva en el output original.\n"
    "- Verifica contra el OUTPUT: si un colega vio algo, comprueba que realmente esta ahi.\n"
    "- Tu evaluacion enriquecida >= tu original en cada celda.\n\n"
    "JSON puro, sin texto ni markdown:\n"
    '{"evaluacion_enriquecida":{"celdas":{"Salud\u00d7Conservar":{"nivel":N,"evidencia":"..."},...21 celdas}},'
    '"incorporado_de_otros":[{"celda":"X\u00d7Y","antes":N,"despues":M,"de_quien":"modelo","que_vi_gracias_a_el":"..."}],'
    '"mi_aporte_unico":[{"celda":"X\u00d7Y","mi_score":N,"score_maximo_otros":M,"que_veo_que_nadie_ve":"..."}],'
    '"angulos_diferentes":[{"celda":"X\u00d7Y","mi_lectura":"...","lectura_otros":"...","por_que_ambas_son_validas":"..."}]}'
)


def get_system_r1(model_name):
    """Build specialized R1 system prompt for a model."""
    focus = SPECIALIZED_FOCUS.get(model_name, "")
    return SYSTEM_COMMON + focus + "\n\n" + JSON_FORMAT


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


# ── API Calls (same as exp4) ────────────────────────────────────
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
            "max_tokens": 8192,
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
        "max_tokens": 8192,
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
            "max_tokens": 8192,
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


# ── Prompt Builders ──────────────────────────────────────────────
def build_r1_user_prompt(item):
    return (
        "CASO: %s\n"
        "INTELIGENCIA APLICADA: %s — %s\n"
        "MODELO QUE GENERO EL OUTPUT: %s\n\n"
        "OUTPUT A EVALUAR:\n---\n%s\n---\n\n"
        "Evalua este output mapeando cada hallazgo a la Matriz 3Lx7F. "
        "Asigna nivel de profundidad (0-4) y evidencia por celda. JSON puro."
    ) % (item["case_nombre"], item["int_id"], item["int_nombre"], item["model_key"], item["output"])


def build_r2_user_prompt(output_text, my_celdas, other_evals):
    parts = [
        "OUTPUT ORIGINAL A EVALUAR:\n---",
        output_text,
        "---\n",
        "TU EVALUACION (Ronda 1):",
        json.dumps(my_celdas, ensure_ascii=False),
        "\nEVALUACIONES DE TUS COLEGAS:\n",
    ]
    for name, celdas in other_evals:
        parts.append("Evaluador: " + name)
        parts.append(json.dumps(celdas, ensure_ascii=False))
        parts.append("")
    parts.append(
        "Enriquece tu evaluacion con lo que aportan tus colegas. "
        "Incorpora lo valido, senala lo que tu ves que nadie mas ve, "
        "y marca los angulos genuinamente diferentes. JSON puro."
    )
    return "\n".join(parts)


# ── Load Data ────────────────────────────────────────────────────
def load_test_outputs():
    with open(TEST_OUTPUTS_FILE, encoding="utf-8") as f:
        items = json.load(f)
    return {item["id"]: item for item in items}


def load_sonnet_from_exp4():
    """Load Sonnet evaluations from Exp 4 R1."""
    with open(EXP4_R1_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("evaluaciones", {}).get("sonnet", {})


# ── R1 Specialized ──────────────────────────────────────────────
def eval_output_r1(model_name, model_cfg, item):
    system_prompt = get_system_r1(model_name)
    user_prompt = build_r1_user_prompt(item)
    for attempt in range(2):
        try:
            prompt = user_prompt
            if attempt == 1:
                prompt += "\n\nIMPORTANTE: Responde SOLO con JSON valido. Sin texto adicional."
            content, elapsed = call_model(model_name, model_cfg, system_prompt, prompt)
            parsed = extract_json(content)
            if parsed and "celdas" in parsed:
                return {"celdas": parsed["celdas"], "tiempo_s": elapsed}
            if parsed:
                sample_key = next(iter(parsed.keys()), "")
                if "\u00d7" in sample_key:
                    return {"celdas": parsed, "tiempo_s": elapsed}
            if attempt == 0:
                print("(retry)", end=" ", flush=True)
                time.sleep(2)
        except Exception as e:
            err = str(e)
            if attempt == 0:
                wait = 30 if ("rate" in err.lower() or "429" in err) else 5
                print("(err, wait %ds)" % wait, end=" ", flush=True)
                time.sleep(wait)
    return None


def save_r1(evaluaciones):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "meta": {
            "experiment": "Exp 4.1 - Mesa Redonda Especializada",
            "date": str(date.today()),
            "ronda": 1,
            "n_models": len(evaluaciones),
        },
        "evaluaciones": evaluaciones,
    }
    with open(R1_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_ronda1():
    """R1 specialized: each model gets its specialized prompt."""
    if R1_FILE.exists():
        with open(R1_FILE, encoding="utf-8") as f:
            evaluaciones = json.load(f).get("evaluaciones", {})
    else:
        evaluaciones = {}

    # Pre-load Sonnet from Exp 4
    if "sonnet" not in evaluaciones or len(evaluaciones.get("sonnet", {})) < 5:
        sonnet = load_sonnet_from_exp4()
        evaluaciones["sonnet"] = sonnet
        print("Sonnet: loaded %d/5 from Exp 4" % len(sonnet))
    else:
        print("Sonnet: already loaded (%d/5)" % len(evaluaciones["sonnet"]))

    test_outputs = load_test_outputs()

    # Filter by --model if provided
    model_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--model="):
            model_filter = arg.split("=", 1)[1]

    # Status
    print("\n--- R1 Especializada Status ---")
    to_complete = []
    for model_name in ALL_ACTIVE:
        n = len(evaluaciones.get(model_name, {}))
        missing = [oid for oid in OUTPUT_IDS if oid not in evaluaciones.get(model_name, {})]
        status = "OK" if n >= 5 else "%d/5" % n
        print("  %s: %s" % (model_name, status))
        if missing:
            to_complete.append((model_name, missing))

    total_calls = sum(len(m[1]) for m in to_complete)
    if total_calls == 0:
        print("\nR1 complete, no calls needed.")
        save_r1(evaluaciones)
        return evaluaciones

    print("\n--- Running R1 Especializada (%d calls) ---" % total_calls)
    for model_name, missing_oids in to_complete:
        if model_filter and model_name != model_filter:
            continue
        if model_name not in ALL_MODELS:
            continue
        model_cfg = ALL_MODELS[model_name]
        provider = model_cfg["provider"]
        if not PROVIDERS.get(provider, {}).get("api_key"):
            print("  %s: no API key for %s, skipping" % (model_name, provider))
            continue
        if model_name not in evaluaciones:
            evaluaciones[model_name] = {}

        print("\n  [%s] %d outputs pending (foco: %s)" % (
            model_name, len(missing_oids),
            SPECIALIZED_FOCUS.get(model_name, "general")[:50] + "..."
        ))
        for oid in missing_oids:
            item = test_outputs[oid]
            print("    %s..." % oid, end=" ", flush=True)
            result = eval_output_r1(model_name, model_cfg, item)
            if result:
                evaluaciones[model_name][oid] = result
                niveles = [c.get("nivel", 0) for c in result["celdas"].values()]
                medio = sum(niveles) / max(len(niveles), 1)
                print("OK (%.1fs, medio=%.2f)" % (result["tiempo_s"], medio))
            else:
                print("FAIL")
            time.sleep(2)
        save_r1(evaluaciones)

    # Final status
    print("\n--- R1 Final ---")
    complete = 0
    for m in ALL_WITH_SONNET:
        n = len(evaluaciones.get(m, {}))
        if n >= 5:
            complete += 1
        print("  %s: %d/5" % (m, n))
    print("  Total: %d/%d complete" % (complete, len(ALL_WITH_SONNET)))
    save_r1(evaluaciones)
    return evaluaciones


# ── R2 Enrichment ────────────────────────────────────────────────
def validate_r2(r2_parsed, r1_celdas):
    if not r2_parsed:
        return None
    enriched = None
    if "evaluacion_enriquecida" in r2_parsed:
        enriched = r2_parsed["evaluacion_enriquecida"].get("celdas", {})
    elif "celdas" in r2_parsed:
        enriched = r2_parsed["celdas"]
    else:
        sample = next(iter(r2_parsed.keys()), "")
        if "\u00d7" in sample:
            enriched = r2_parsed
    if not enriched:
        return None
    for celda, r1_val in r1_celdas.items():
        r1_nivel = r1_val.get("nivel", 0) if isinstance(r1_val, dict) else 0
        if celda in enriched:
            r2_nivel = enriched[celda].get("nivel", 0) if isinstance(enriched[celda], dict) else 0
            if r2_nivel < r1_nivel:
                enriched[celda]["nivel"] = r1_nivel
        else:
            enriched[celda] = r1_val
    return {
        "evaluacion_enriquecida": {"celdas": enriched},
        "incorporado_de_otros": r2_parsed.get("incorporado_de_otros", []),
        "mi_aporte_unico": r2_parsed.get("mi_aporte_unico", []),
        "angulos_diferentes": r2_parsed.get("angulos_diferentes", []),
    }


def save_r2(r2_evals):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "meta": {
            "experiment": "Exp 4.1 - Mesa Redonda Especializada",
            "date": str(date.today()),
            "ronda": 2,
            "n_models": len(r2_evals),
        },
        "evaluaciones": r2_evals,
    }
    with open(R2_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_ronda2(evaluaciones):
    """R2 enrichment: each model sees all specialized evaluations."""
    if R2_FILE.exists():
        with open(R2_FILE, encoding="utf-8") as f:
            r2_evals = json.load(f).get("evaluaciones", {})
    else:
        r2_evals = {}

    test_outputs = load_test_outputs()
    r2_models = [
        m for m in ALL_ACTIVE
        if m in evaluaciones and len(evaluaciones[m]) > 0
    ]

    model_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--model="):
            model_filter = arg.split("=", 1)[1]
    if model_filter:
        r2_models = [m for m in r2_models if m == model_filter]

    print("\n" + "=" * 60)
    print("RONDA 2 ESPECIALIZADA: %d modelos" % len(r2_models))
    print("=" * 60)

    for model_name in r2_models:
        if model_name not in ALL_MODELS:
            continue
        model_cfg = ALL_MODELS[model_name]
        provider = model_cfg["provider"]
        if not PROVIDERS.get(provider, {}).get("api_key"):
            continue
        if model_name not in r2_evals:
            r2_evals[model_name] = {}

        model_r1 = evaluaciones[model_name]

        for oid in OUTPUT_IDS:
            if oid not in model_r1:
                continue
            if oid in r2_evals[model_name] and "error" not in r2_evals[model_name][oid]:
                continue

            other_evals = []
            for other in ALL_WITH_SONNET:
                if other == model_name:
                    continue
                if other in evaluaciones and oid in evaluaciones[other]:
                    other_evals.append((other, evaluaciones[other][oid].get("celdas", {})))
            if not other_evals:
                continue

            output_text = test_outputs[oid]["output"]
            my_celdas = model_r1[oid]["celdas"]
            user_prompt = build_r2_user_prompt(output_text, my_celdas, other_evals)

            print("  [%s] %s R2 (%d peers)..." % (model_name, oid, len(other_evals)), end=" ", flush=True)

            r2_cfg = dict(model_cfg)
            r2_cfg["timeout"] = max(model_cfg.get("timeout", 180), 240)

            result = None
            for attempt in range(2):
                try:
                    prompt = user_prompt
                    if attempt == 1:
                        prompt += (
                            "\n\nIMPORTANTE: Responde con JSON completo incluyendo "
                            "evaluacion_enriquecida, incorporado_de_otros, "
                            "mi_aporte_unico, y angulos_diferentes."
                        )
                    content, elapsed = call_model(model_name, r2_cfg, SYSTEM_R2, prompt)
                    parsed = extract_json(content)
                    if parsed:
                        validated = validate_r2(parsed, my_celdas)
                        if validated:
                            validated["tiempo_s"] = elapsed
                            result = validated
                            break
                    if attempt == 0:
                        print("(retry)", end=" ", flush=True)
                        time.sleep(3)
                except Exception as e:
                    err = str(e)
                    if attempt == 0:
                        wait = 30 if ("rate" in err.lower() or "429" in err) else 5
                        print("(err, wait %ds)" % wait, end=" ", flush=True)
                        time.sleep(wait)

            if result:
                r2_evals[model_name][oid] = result
                celdas_r2 = result["evaluacion_enriquecida"]["celdas"]
                niveles = [c.get("nivel", 0) for c in celdas_r2.values() if isinstance(c, dict)]
                medio = sum(niveles) / max(len(niveles), 1)
                n_inc = len(result.get("incorporado_de_otros", []))
                n_uni = len(result.get("mi_aporte_unico", []))
                print("OK (%.1fs, medio=%.2f, +%dinc, %duni)" % (elapsed, medio, n_inc, n_uni))
            else:
                r2_evals[model_name][oid] = {"error": "R2 parse failed"}
                print("FAIL")
            time.sleep(3)

        save_r2(r2_evals)

    print("\n--- R2 Final ---")
    for m in r2_models:
        r2m = r2_evals.get(m, {})
        ok = sum(1 for v in r2m.values() if "error" not in v)
        print("  %s: %d/5 R2 OK" % (m, ok))
    return r2_evals


# ── Main ─────────────────────────────────────────────────────────
def main():
    print("=== EXP 4.1: MESA REDONDA ESPECIALIZADA ===")
    print("%d modelos x 5 outputs x 2 rondas\n" % len(ALL_WITH_SONNET))

    for prov, cfg in PROVIDERS.items():
        s = "OK" if cfg.get("api_key") else "MISSING"
        print("  %s: %s" % (prov, s))

    ronda2_only = "--ronda2-only" in sys.argv
    ronda1_only = "--ronda1-only" in sys.argv

    if not ronda2_only:
        evaluaciones = run_ronda1()
    else:
        with open(R1_FILE, encoding="utf-8") as f:
            evaluaciones = json.load(f)["evaluaciones"]

    if not ronda1_only:
        run_ronda2(evaluaciones)

    print("\nDONE")
    print("R1: %s" % R1_FILE)
    print("R2: %s" % R2_FILE)


if __name__ == "__main__":
    main()
