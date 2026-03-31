#!/usr/bin/env python3
"""
Test de Consistencia — posicion_observador
===========================================
Valida si un LLM puede etiquetar de forma consistente la dim
`posicion_observador` (razonamiento/pensamiento/inteligencia).

Protocolo:
  1. Selecciona 50 textos diversos del corpus
  2. Run A: etiqueta con Opus via CLI (temperatura 0)
  3. Run B: etiqueta de nuevo (mismo prompt, mismos textos)
  4. Mide acuerdo (% coincidencia entre run A y run B)
  5. Si acuerdo >= 70%: la dim entra en gold set v2
     Si acuerdo < 70%: la dim se descarta antes de gastar $25

Uso:
  # Con Claude CLI (Opus local — sin coste API):
  python test_consistencia_posicion.py \
    --corpus motor-semantico/data/shard_001.jsonl \
    --n 50 \
    --method cli

  # Con API (Opus via OpenRouter — ~$2):
  python test_consistencia_posicion.py \
    --corpus motor-semantico/data/shard_001.jsonl \
    --n 50 \
    --method api

  # Con Qwen 14B (simula labeling real — coste GPU):
  python test_consistencia_posicion.py \
    --corpus motor-semantico/data/shard_001.jsonl \
    --n 50 \
    --method qwen \
    --qwen-url http://gpu-ip:8000/v1/chat/completions

Teoría (§16-§17 TEORIA_UNIFICADA_ALGEBRA_VIVA.md):
  - Razonamiento = posición SUJETO: verbos copulativos, adjetivos predicativos,
    clasificar sujetos en conjuntos. Operaciones de membresía (∈, ∉, ⊂, ∩, ∪).
  - Pensamiento = posición PREDICADO: nominalizaciones, verbos de acción,
    sustantivos en función adverbial. Descomponer/componer/transformar procesos.
  - Inteligencia = posición AMBAS: nominalizaciones de orden superior,
    operar sobre la estructura S+P+O completa, recursión.
"""

import json
import os
import sys
import time
import random
import argparse
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from shared_config import config as _cfg
    OPENROUTER_API_KEY = _cfg.OPENROUTER_API_KEY
    ANTHROPIC_API_KEY = _cfg.ANTHROPIC_API_KEY
    OPUS_MODEL = _cfg.OPUS_MODEL
except ImportError:
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    OPUS_MODEL = "anthropic/claude-opus-4"

TELEGRAM_CONFIG = ROOT / "scripts" / "telegram_config.json"
CHAT_ID = "8091188679"

# ── Prompt de labeling ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un analizador lingüístico-cognitivo experto. Tu tarea es identificar
la POSICIÓN DEL OBSERVADOR en un texto, basándote en la estructura gramatical,
no en el contenido semántico.

## Las tres posiciones (Teoría Unificada §16)

### RAZONAMIENTO — posición SUJETO
El texto opera clasificando sujetos en conjuntos. Señales gramaticales:
- Verbos copulativos dominantes: "es", "resulta", "pertenece a", "se clasifica como"
- Adjetivos predicativos: "es viable", "resulta ineficiente", "parece sostenible"
- Estructura dominante: SUJETO + copulativo + ADJETIVO/CLASE
- Operaciones de membresía: incluir/excluir/comparar/jerarquizar sujetos
- Pregunta implícita: "¿A qué conjunto pertenece X?" / "¿Qué propiedades hereda X?"

### PENSAMIENTO — posición PREDICADO
El texto opera sobre procesos, nominalizándolos o descomponiéndolos. Señales:
- Verbos de acción dominantes: "implementar", "analizar", "crear", "transformar"
- Nominalizaciones de verbos: "la decisión", "la implementación", "el análisis"
- Sustantivos en función adverbial: "opera con eficiencia", "avanza mediante sistematización"
- Estructura dominante: VERBO + complemento instrumental/modal
- Pregunta implícita: "¿Cómo funciona X?" / "¿Qué procesos opera X?"

### INTELIGENCIA — posición AMBAS
El texto opera sobre la estructura completa o sobre sí mismo. Señales:
- Nominalizaciones de orden superior: "esa estructura inferencial", "ese patrón"
- Opera sobre oraciones completas tratándolas como objetos
- Recursión: el proceso se aplica a sí mismo ("pensar sobre el pensar")
- Alto ratio abstracto/concreto
- Pregunta implícita: "¿Desde qué marco se generó esto?" / "¿Qué presupone esta estructura?"

## Instrucciones

Para el texto dado, responde SOLO con un JSON válido:

{
  "posicion": "razonamiento" | "pensamiento" | "inteligencia",
  "confianza": 0.0-1.0,
  "señales": ["señal1", "señal2", "señal3"],
  "direccion": "todo_parte" | "parte_todo" | "parte_parte" | "todo_todo",
  "marco": "financiero" | "ecologico" | "operativo" | "social" | "existencial" | "computacional" | "narrativo" | "otro"
}

Reglas:
- Basa tu clasificación en la ESTRUCTURA GRAMATICAL, no en el tema del texto.
- "confianza" refleja cuán clara es la señal gramatical (no tu certeza general).
- "señales" son las 3 señales gramaticales más fuertes que detectas.
- Si hay mezcla de posiciones, elige la DOMINANTE (>50% del texto).
- Solo JSON, sin explicación adicional."""


USER_PROMPT_TEMPLATE = 'Analiza la posición del observador en este texto:\n"""\n{text}\n"""'


# ── Métodos de llamada ──────────────────────────────────────────────────────

def call_cli(text: str, run_id: str) -> dict:
    """Llama a Opus via Claude CLI. Sin coste API — usa el plan local."""
    user_msg = USER_PROMPT_TEMPLATE.format(text=text[:3000])
    full_prompt = f"SYSTEM:\n{SYSTEM_PROMPT}\n\nUSER:\n{user_msg}"

    try:
        result = subprocess.run(
            ["claude", "-p", full_prompt, "--output-format", "json"],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, "CLAUDE_MODEL": "opus"}
        )

        if result.returncode != 0:
            print(f"  [CLI {run_id}] Error: {result.stderr[:200]}")
            return None

        # Claude CLI con --output-format json devuelve {"result": "...", ...}
        cli_output = json.loads(result.stdout)
        content = cli_output.get("result", result.stdout)

        # Extraer JSON del contenido
        return _parse_json_response(content)

    except subprocess.TimeoutExpired:
        print(f"  [CLI {run_id}] Timeout (120s)")
        return None
    except Exception as e:
        print(f"  [CLI {run_id}] Error: {e}")
        return None


def call_anthropic(text: str, run_id: str) -> dict:
    """Llama a Opus via Anthropic API directa."""
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://api.anthropic.com/v1/messages",
            "-H", f"x-api-key: {ANTHROPIC_API_KEY}",
            "-H", "anthropic-version: 2023-06-01",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": "claude-opus-4-20250514",
                "max_tokens": 500,
                "temperature": 0.0,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text[:3000])}
                ]
            })
        ], capture_output=True, text=True, timeout=120)

        response = json.loads(result.stdout)
        content_blocks = response.get("content", [])
        if not content_blocks:
            error = response.get("error", {}).get("message", "unknown")
            print(f"  [ANTH {run_id}] Error: {error}")
            return None
        content = content_blocks[0].get("text", "")
        return _parse_json_response(content)

    except Exception as e:
        print(f"  [ANTH {run_id}] Error: {e}")
        return None


def call_api(text: str, run_id: str) -> dict:
    """Llama a Opus via OpenRouter API."""
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": OPUS_MODEL,
                "max_tokens": 500,
                "temperature": 0.0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text[:3000])}
                ]
            })
        ], capture_output=True, text=True, timeout=120)

        response = json.loads(result.stdout)
        choices = response.get("choices", [])
        if not choices:
            error = response.get("error", {}).get("message", "unknown")
            print(f"  [API {run_id}] Error: {error}")
            return None
        content = choices[0].get("message", {}).get("content", "")
        return _parse_json_response(content)

    except Exception as e:
        print(f"  [API {run_id}] Error: {e}")
        return None


def call_qwen(text: str, run_id: str, qwen_url: str) -> dict:
    """Llama a Qwen 14B via vLLM (simula labeling real)."""
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{qwen_url}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": "Qwen/Qwen2.5-14B-AWQ",
                "max_tokens": 500,
                "temperature": 0.0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text[:3000])}
                ]
            })
        ], capture_output=True, text=True, timeout=120)

        response = json.loads(result.stdout)
        choices = response.get("choices", [])
        if not choices:
            return None
        content = choices[0].get("message", {}).get("content", "")
        return _parse_json_response(content)

    except Exception as e:
        print(f"  [QWEN {run_id}] Error: {e}")
        return None


def _parse_json_response(content: str) -> dict:
    """Extrae JSON de la respuesta del modelo."""
    clean = content.strip()
    # Quitar markdown code blocks
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    # Buscar primer { ... último }
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start >= 0 and end > start:
        clean = clean[start:end]
    try:
        parsed = json.loads(clean)
        # Validar campos mínimos
        if "posicion" not in parsed:
            return None
        if parsed["posicion"] not in ("razonamiento", "pensamiento", "inteligencia"):
            return None
        return parsed
    except json.JSONDecodeError:
        return None


# ── Selección de textos ─────────────────────────────────────────────────────

def select_texts(corpus_path: str, n: int) -> list:
    """Selecciona N textos diversos del corpus."""
    print(f"Cargando corpus: {corpus_path}")
    texts = []
    with open(corpus_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                text = entry.get("text", entry.get("texto", ""))
                if len(text) > 80:
                    texts.append(text)
            except json.JSONDecodeError:
                continue

    print(f"  {len(texts)} textos válidos")
    if len(texts) <= n:
        return texts

    # Diversidad por longitud
    texts.sort(key=len)
    step = len(texts) // n
    selected = [texts[i * step] for i in range(n)]
    random.shuffle(selected)
    print(f"  Seleccionados {len(selected)} textos diversos")
    return selected


# ── Ejecución del test ──────────────────────────────────────────────────────

def run_test(texts: list, method: str, run_label: str, qwen_url: str = None) -> list:
    """Ejecuta un run completo de labeling sobre todos los textos."""
    results = []
    total = len(texts)

    for i, text in enumerate(texts):
        print(f"  [{run_label}] {i+1}/{total}", end="", flush=True)

        if method == "cli":
            label = call_cli(text, run_label)
        elif method == "anthropic":
            label = call_anthropic(text, run_label)
        elif method == "api":
            label = call_api(text, run_label)
        elif method == "qwen":
            label = call_qwen(text, run_label, qwen_url)
        else:
            raise ValueError(f"Método desconocido: {method}")

        if label:
            results.append(label)
            pos = label.get("posicion", "?")
            conf = label.get("confianza", 0)
            print(f" → {pos} ({conf:.2f})")
        else:
            results.append(None)
            print(f" → FALLO")

        # Rate limiting suave
        if method in ("api", "qwen"):
            time.sleep(1)
        elif method == "cli":
            time.sleep(0.5)

    success = sum(1 for r in results if r is not None)
    print(f"  [{run_label}] {success}/{total} exitosos")
    return results


def compute_agreement(run_a: list, run_b: list) -> dict:
    """Calcula métricas de acuerdo entre dos runs."""
    assert len(run_a) == len(run_b), "Runs deben tener misma longitud"

    total = len(run_a)
    both_valid = 0
    agree_posicion = 0
    agree_direccion = 0
    agree_marco = 0

    posiciones_a = {"razonamiento": 0, "pensamiento": 0, "inteligencia": 0}
    posiciones_b = {"razonamiento": 0, "pensamiento": 0, "inteligencia": 0}
    confianzas = []

    disagreements = []

    for i, (a, b) in enumerate(zip(run_a, run_b)):
        if a is None or b is None:
            continue
        both_valid += 1

        pos_a = a.get("posicion")
        pos_b = b.get("posicion")
        dir_a = a.get("direccion")
        dir_b = b.get("direccion")
        mar_a = a.get("marco")
        mar_b = b.get("marco")

        if pos_a in posiciones_a:
            posiciones_a[pos_a] += 1
        if pos_b in posiciones_b:
            posiciones_b[pos_b] += 1

        conf_a = a.get("confianza", 0)
        conf_b = b.get("confianza", 0)
        confianzas.append((conf_a + conf_b) / 2)

        if pos_a == pos_b:
            agree_posicion += 1
        else:
            disagreements.append({
                "index": i,
                "run_a": pos_a,
                "run_b": pos_b,
                "conf_a": conf_a,
                "conf_b": conf_b
            })

        if dir_a == dir_b:
            agree_direccion += 1
        if mar_a == mar_b:
            agree_marco += 1

    if both_valid == 0:
        return {"error": "No hay pares válidos para comparar"}

    avg_conf = sum(confianzas) / len(confianzas) if confianzas else 0

    return {
        "total_textos": total,
        "ambos_validos": both_valid,
        "fallos": total - both_valid,
        "acuerdo_posicion": agree_posicion / both_valid,
        "acuerdo_direccion": agree_direccion / both_valid,
        "acuerdo_marco": agree_marco / both_valid,
        "acuerdo_posicion_n": agree_posicion,
        "acuerdo_posicion_pct": f"{agree_posicion / both_valid * 100:.1f}%",
        "distribucion_run_a": posiciones_a,
        "distribucion_run_b": posiciones_b,
        "confianza_media": round(avg_conf, 3),
        "disagreements": disagreements[:10],  # max 10 para el reporte
        "DECISION": "INCLUIR en gold set v2" if agree_posicion / both_valid >= 0.70
                    else "EXCLUIR — acuerdo insuficiente (<70%)",
        "threshold": 0.70,
    }


# ── Reporte ─────────────────────────────────────────────────────────────────

def send_telegram(msg: str):
    try:
        config = json.loads(TELEGRAM_CONFIG.read_text())
        token = config.get("bot_token", "")
        subprocess.run([
            "curl", "-s", "-X", "POST",
            f"https://api.telegram.org/bot{token}/sendMessage",
            "-d", f"chat_id={CHAT_ID}",
            "-d", f"text={msg}",
        ], capture_output=True, timeout=10)
    except Exception:
        pass


def save_report(agreement: dict, run_a: list, run_b: list, output_dir: Path):
    """Guarda reporte completo del test."""
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Reporte JSON
    report_path = output_dir / f"test_consistencia_{ts}.json"
    report = {
        "test": "consistencia_posicion_observador",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agreement": agreement,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n📊 Reporte guardado: {report_path}")

    # Runs detallados
    runs_path = output_dir / f"test_consistencia_{ts}_runs.jsonl"
    with open(runs_path, "w") as f:
        for i, (a, b) in enumerate(zip(run_a, run_b)):
            f.write(json.dumps({
                "index": i,
                "run_a": a,
                "run_b": b,
                "agree": (a or {}).get("posicion") == (b or {}).get("posicion")
                         if a and b else None
            }, ensure_ascii=False) + "\n")
    print(f"📋 Runs detallados: {runs_path}")

    return report_path


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Test de consistencia para dim posicion_observador"
    )
    parser.add_argument("--corpus", required=True,
                        help="Path to corpus JSONL")
    parser.add_argument("--n", type=int, default=50,
                        help="Número de textos a testear (default: 50)")
    parser.add_argument("--method", choices=["cli", "api", "anthropic", "qwen"], default="anthropic",
                        help="Método de llamada al modelo (default: anthropic)")
    parser.add_argument("--qwen-url", type=str,
                        default="http://localhost:8000/v1/chat/completions",
                        help="URL del servidor vLLM para Qwen")
    parser.add_argument("--output-dir", type=str,
                        default=str(ROOT / "experiments" / "test_consistencia"),
                        help="Directorio de salida para reportes")
    args = parser.parse_args()

    print("=" * 60)
    print("TEST DE CONSISTENCIA — posicion_observador")
    print(f"Método: {args.method} | Textos: {args.n} | Threshold: 70%")
    print("=" * 60)

    # 1. Seleccionar textos
    texts = select_texts(args.corpus, args.n)
    if len(texts) < 10:
        print("ERROR: Menos de 10 textos válidos. Abortando.")
        sys.exit(1)

    # 2. Run A
    print(f"\n{'='*40}")
    print("RUN A")
    print(f"{'='*40}")
    run_a = run_test(texts, args.method, "A", args.qwen_url)

    # Pausa entre runs para evitar cache effects
    print("\n⏳ Pausa de 5s entre runs...")
    time.sleep(5)

    # 3. Run B
    print(f"\n{'='*40}")
    print("RUN B")
    print(f"{'='*40}")
    run_b = run_test(texts, args.method, "B", args.qwen_url)

    # 4. Calcular acuerdo
    print(f"\n{'='*40}")
    print("RESULTADOS")
    print(f"{'='*40}")
    agreement = compute_agreement(run_a, run_b)

    if "error" in agreement:
        print(f"❌ {agreement['error']}")
        sys.exit(1)

    print(f"\n  Textos totales:     {agreement['total_textos']}")
    print(f"  Ambos válidos:      {agreement['ambos_validos']}")
    print(f"  Fallos:             {agreement['fallos']}")
    print(f"\n  ACUERDO posición:   {agreement['acuerdo_posicion_pct']} "
          f"({agreement['acuerdo_posicion_n']}/{agreement['ambos_validos']})")
    print(f"  ACUERDO dirección:  {agreement['acuerdo_direccion']*100:.1f}%")
    print(f"  ACUERDO marco:      {agreement['acuerdo_marco']*100:.1f}%")
    print(f"  Confianza media:    {agreement['confianza_media']}")
    print(f"\n  Distribución Run A: {agreement['distribucion_run_a']}")
    print(f"  Distribución Run B: {agreement['distribucion_run_b']}")

    if agreement['disagreements']:
        print(f"\n  Desacuerdos (primeros {len(agreement['disagreements'])}):")
        for d in agreement['disagreements']:
            print(f"    #{d['index']}: A={d['run_a']}({d['conf_a']:.2f}) "
                  f"vs B={d['run_b']}({d['conf_b']:.2f})")

    # 5. Decisión
    print(f"\n{'='*40}")
    decision = agreement['DECISION']
    if "INCLUIR" in decision:
        print(f"  ✅ {decision}")
    else:
        print(f"  ❌ {decision}")
    print(f"{'='*40}")

    # 6. Guardar reporte
    output_dir = Path(args.output_dir)
    report_path = save_report(agreement, run_a, run_b, output_dir)

    # 7. Telegram
    emoji = "✅" if "INCLUIR" in decision else "❌"
    send_telegram(
        f"{emoji} Test consistencia posicion_observador\n"
        f"Acuerdo: {agreement['acuerdo_posicion_pct']}\n"
        f"Método: {args.method}\n"
        f"Decisión: {decision}"
    )

    # Exit code
    sys.exit(0 if "INCLUIR" in decision else 1)


if __name__ == "__main__":
    main()
