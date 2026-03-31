#!/usr/bin/env python3
"""
OMNI-MIND Gold Set Creator v2
================================
Crea gold set de 3000 textos etiquetados por Opus para v2 (51 dims).

Métodos de llamada:
  - cli:       Claude CLI (plan Max, $0, ~15h para 3000 textos)
  - anthropic: Anthropic API directa (~$300 para 3000 textos)
  - api:       OpenRouter API (~$300 para 3000 textos)

Uso:
  # Recomendado — via CLI con plan Max ($0):
  python create_gold_set_v2.py \
    --corpus motor-semantico/corpus/corpus.jsonl \
    --dims motor-semantico/configs/v2_51_dims.json \
    --output motor-semantico/data/gold_set_v2_3000.jsonl \
    --n 3000 \
    --method cli \
    --concurrency 3

  # Via API (si no puedes usar CLI):
  python create_gold_set_v2.py \
    --corpus motor-semantico/corpus/corpus.jsonl \
    --dims motor-semantico/configs/v2_51_dims.json \
    --output motor-semantico/data/gold_set_v2_3000.jsonl \
    --n 3000 \
    --method anthropic

Cambios vs v1:
  - 51 dims (38 float + 10 binary + 3 categorical)
  - Soporte CLI para plan Max ($0)
  - Prompt actualizado con §16-§17 (posicion_observador, direccion, marco)
  - Concurrencia configurable para CLI
  - Resume robusto (checkpoint cada texto)
  - Validación de distribución al final
"""

import json
import os
import sys
import time
import random
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

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


# ── Prompt de labeling v2 ───────────────────────────────────────────────────

def build_system_prompt(dims_data: dict) -> str:
    """Construye el system prompt dinámicamente desde la config de dims."""

    float_dims = []
    binary_dims = []
    cat_dims = []

    for d in dims_data.get("dims", []):
        entry = f"- `{d['name']}`: {d['description']}"
        if d["type"] == "float":
            float_dims.append(entry)
        elif d["type"] == "binary":
            binary_dims.append(entry)
        elif d["type"] == "categorical":
            classes = d.get("classes", [])
            entry += f" — Clases: {', '.join(classes)}"
            cat_dims.append(entry)

    float_list = "\n".join(float_dims)
    binary_list = "\n".join(binary_dims)
    cat_list = "\n".join(cat_dims)

    return f"""Eres un analizador lingüístico-cognitivo experto. Tu tarea es etiquetar textos
con {len(dims_data.get('dims', []))} dimensiones que miden la estructura cognitiva del texto.

## Teoría base (Teoría Unificada §16-§17)

### Tres posiciones del observador:
- **Razonamiento** (posición SUJETO): opera clasificando sujetos en conjuntos.
  Señales: verbos copulativos (es, resulta, pertenece), adjetivos predicativos,
  estructura S + copulativo + adjetivo/clase. Operaciones de membresía.
- **Pensamiento** (posición PREDICADO): opera sobre procesos, nominalizándolos.
  Señales: verbos de acción, nominalizaciones (la decisión, el análisis),
  sustantivos en función adverbial (con eficiencia, mediante sistematización).
- **Inteligencia** (posición AMBAS): opera sobre la estructura completa S+P+O
  o aplica la operación a sí misma. Señales: nominalizaciones de orden superior,
  alta abstracción, recursión (pensar sobre el pensar).

### Cuatro direcciones de navegación todo↔partes:
- **todo_parte** (deducción): del conjunto general al miembro específico
- **parte_todo** (inducción): de miembros específicos al conjunto general
- **parte_parte** (analogía): transferencia horizontal entre miembros
- **todo_todo** (transitividad): cadena entre conjuntos (A⊂B⊂C)

### Marco de referencia = conjunto universo de operandos:
El vocabulario del sujeto y los adjetivos revelan el marco activo.
"rentabilidad" → financiero. "ecosistema" → ecológico. "identidad" → existencial.

## Dimensiones a etiquetar

### Float [0.0 - 1.0] ({len(float_dims)} dims):
{float_list}

### Binary (0 o 1) ({len(binary_dims)} dims):
{binary_list}

### Categorical ({len(cat_dims)} dims):
{cat_list}

## Instrucciones

1. Lee el texto cuidadosamente.
2. Analiza la ESTRUCTURA GRAMATICAL (no solo el contenido semántico).
3. Responde SOLO con un JSON válido con todas las dimensiones.
4. Para floats: valor entre 0.0 y 1.0 con 2 decimales.
5. Para binary: 0 o 1.
6. Para categorical: una de las clases listadas (string exacto).
7. Si una dimensión no es detectable, usa 0.0 (float), 0 (binary), o la clase por defecto.
8. NO incluyas explicaciones — solo el JSON.

Ejemplo de formato de respuesta:
{{
  "sust_densidad": 0.45,
  "adj_densidad": 0.22,
  ...
  "h01_confirmacion": 0,
  ...
  "posicion_observador": "razonamiento",
  "direccion_navegacion": "todo_parte",
  "marco_dominante": "financiero",
  "profundidad_estructura": 0.35
}}"""


USER_PROMPT = 'Etiqueta las {n_dims} dimensiones para este texto:\n"""\n{text}\n"""'


# ── Métodos de llamada ──────────────────────────────────────────────────────

def call_cli(system_prompt: str, text: str, n_dims: int, max_retries: int = 3) -> dict:
    """Llama a Opus via Claude CLI. Plan Max = $0."""
    user_msg = USER_PROMPT.format(text=text[:3000], n_dims=n_dims)
    full_prompt = f"{system_prompt}\n\n---\n\n{user_msg}"

    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["claude", "-p", full_prompt, "--output-format", "json"],
                capture_output=True, text=True, timeout=180,
                env={
                    **{k: v for k, v in os.environ.items() if k != "CLAUDECODE"},
                    "CLAUDE_MODEL": "opus"
                }
            )

            if result.returncode != 0:
                stderr = result.stderr[:200] if result.stderr else "unknown"
                print(f"    [CLI retry {attempt+1}] rc={result.returncode}: {stderr}")
                time.sleep(3 * (attempt + 1))
                continue

            # Claude CLI --output-format json → {"result": "...", ...}
            try:
                cli_output = json.loads(result.stdout)
                content = cli_output.get("result", result.stdout)
            except json.JSONDecodeError:
                content = result.stdout

            return _parse_json_response(content)

        except subprocess.TimeoutExpired:
            print(f"    [CLI retry {attempt+1}] Timeout 180s")
            time.sleep(5)
        except Exception as e:
            print(f"    [CLI retry {attempt+1}] {e}")
            time.sleep(3 * (attempt + 1))

    return None


def call_anthropic(system_prompt: str, text: str, n_dims: int, max_retries: int = 3) -> dict:
    """Llama a Opus via Anthropic API directa."""
    for attempt in range(max_retries):
        try:
            result = subprocess.run([
                "curl", "-s", "-X", "POST",
                "https://api.anthropic.com/v1/messages",
                "-H", f"x-api-key: {ANTHROPIC_API_KEY}",
                "-H", "anthropic-version: 2023-06-01",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "model": "claude-opus-4-20250514",
                    "max_tokens": 2000,
                    "temperature": 0.0,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": USER_PROMPT.format(
                            text=text[:3000], n_dims=n_dims
                        )}
                    ]
                })
            ], capture_output=True, text=True, timeout=120)

            response = json.loads(result.stdout)
            content_blocks = response.get("content", [])
            if not content_blocks:
                error = response.get("error", {}).get("message", "unknown")
                print(f"    [API retry {attempt+1}] {error}")
                time.sleep(5 * (attempt + 1))
                continue
            content = content_blocks[0].get("text", "")
            return _parse_json_response(content)

        except Exception as e:
            print(f"    [API retry {attempt+1}] {e}")
            time.sleep(5 * (attempt + 1))

    return None


def call_openrouter(system_prompt: str, text: str, n_dims: int, max_retries: int = 3) -> dict:
    """Llama a Opus via OpenRouter."""
    for attempt in range(max_retries):
        try:
            result = subprocess.run([
                "curl", "-s", "-X", "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "model": OPUS_MODEL,
                    "max_tokens": 2000,
                    "temperature": 0.0,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": USER_PROMPT.format(
                            text=text[:3000], n_dims=n_dims
                        )}
                    ]
                })
            ], capture_output=True, text=True, timeout=120)

            response = json.loads(result.stdout)
            choices = response.get("choices", [])
            if not choices:
                error = response.get("error", {}).get("message", "unknown")
                print(f"    [OR retry {attempt+1}] {error}")
                time.sleep(5 * (attempt + 1))
                continue
            content = choices[0].get("message", {}).get("content", "")
            return _parse_json_response(content)

        except Exception as e:
            print(f"    [OR retry {attempt+1}] {e}")
            time.sleep(5 * (attempt + 1))

    return None


def _parse_json_response(content: str) -> dict:
    """Extrae JSON de la respuesta del modelo."""
    if not content:
        return None
    clean = content.strip()
    # Quitar markdown code blocks
    if clean.startswith("```"):
        lines = clean.split("\n")
        end_idx = -1 if lines[-1].strip().startswith("```") else len(lines)
        clean = "\n".join(lines[1:end_idx])
    # Buscar primer { ... último }
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start >= 0 and end > start:
        clean = clean[start:end]
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


# ── Selección de textos (mejorada: multi-corpus) ───────────────────────────

def select_diverse_texts(corpus_paths: list, n: int) -> list:
    """Selecciona N textos diversos de uno o más corpus JSONL."""
    all_texts = []

    for corpus_path in corpus_paths:
        print(f"  Cargando: {corpus_path}")
        try:
            with open(corpus_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        text = entry.get("text", entry.get("texto", ""))
                        if len(text) > 80:
                            all_texts.append(text)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"    ⚠️ No encontrado: {corpus_path}")

    print(f"  Total textos válidos: {len(all_texts)}")

    if len(all_texts) <= n:
        print(f"  Usando todos ({len(all_texts)})")
        random.shuffle(all_texts)
        return all_texts

    # Selección por estratos de longitud (diversidad)
    all_texts.sort(key=len)
    step = len(all_texts) // n
    selected = [all_texts[i * step] for i in range(n)]
    random.shuffle(selected)
    print(f"  Seleccionados {len(selected)} textos diversos")
    return selected


# ── Telegram ────────────────────────────────────────────────────────────────

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


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OMNI-MIND Gold Set Creator v2")
    parser.add_argument("--corpus", required=True, nargs="+",
                        help="Path(s) to corpus JSONL (puede ser múltiples)")
    parser.add_argument("--dims", required=True,
                        help="Path to dims JSON (v2_51_dims.json)")
    parser.add_argument("--output", required=True,
                        help="Output JSONL path")
    parser.add_argument("--n", type=int, default=3000,
                        help="Number of texts (default 3000)")
    parser.add_argument("--method", choices=["cli", "anthropic", "api"],
                        default="cli",
                        help="Método: cli (Max plan $0), anthropic, api (OpenRouter)")
    parser.add_argument("--concurrency", type=int, default=1,
                        help="Concurrencia para CLI (default 1, max recomendado 3)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing output")
    args = parser.parse_args()

    # Cargar dims
    dims_data = json.loads(Path(args.dims).read_text())
    dim_names = [d["name"] for d in dims_data.get("dims", [])]
    n_dims = len(dim_names)
    system_prompt = build_system_prompt(dims_data)

    output_path = Path(args.output)
    errors_path = output_path.with_suffix(".errors.jsonl")

    # Dispatch de método
    def call_model(text):
        if args.method == "cli":
            return call_cli(system_prompt, text, n_dims)
        elif args.method == "anthropic":
            return call_anthropic(system_prompt, text, n_dims)
        elif args.method == "api":
            return call_openrouter(system_prompt, text, n_dims)

    cost_label = "$0 (Max plan)" if args.method == "cli" else f"~${args.n * 0.10:.0f}"

    print(f"\n{'='*60}")
    print(f"GOLD SET CREATOR v2")
    print(f"{'='*60}")
    print(f"Método:     {args.method}")
    print(f"Modelo:     Opus")
    print(f"Dims:       {n_dims}")
    print(f"Textos:     {args.n}")
    print(f"Concurrencia: {args.concurrency}")
    print(f"Coste est:  {cost_label}")
    print(f"Output:     {args.output}")
    print(f"{'='*60}\n")

    send_telegram(
        f"Gold Set v2 iniciado\n"
        f"Metodo: {args.method}\n"
        f"Textos: {args.n} | Dims: {n_dims}\n"
        f"Coste: {cost_label}"
    )

    # Seleccionar textos
    texts = select_diverse_texts(args.corpus, args.n)

    # Resume
    existing = 0
    if args.resume and output_path.exists():
        with open(output_path, "r") as f:
            existing = sum(1 for line in f if line.strip())
        print(f"  Resume: {existing} labels existentes, continuando desde {existing+1}")
        texts = texts[existing:]

    # Etiquetar
    success = existing
    errors = 0
    start_time = time.time()

    output_mode = "a" if args.resume and output_path.exists() else "w"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, output_mode) as f_out, open(errors_path, output_mode) as f_err:

        if args.concurrency > 1 and args.method == "cli":
            # Concurrencia para CLI
            batch_size = args.concurrency
            for batch_start in range(0, len(texts), batch_size):
                batch = texts[batch_start:batch_start + batch_size]
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = {executor.submit(call_model, t): t for t in batch}
                    for future in as_completed(futures):
                        text = futures[future]
                        idx = existing + batch_start + list(futures.values()).index(text) + 1
                        try:
                            labels = future.result()
                        except Exception as e:
                            labels = None
                            print(f"  [{idx}/{args.n}] Error: {e}")

                        if labels:
                            _write_result(f_out, text, labels, dim_names)
                            success += 1
                            print(f"  [{idx}/{args.n}] OK")
                        else:
                            f_err.write(json.dumps({"text": text[:200], "error": "no_response"}) + "\n")
                            errors += 1
                            print(f"  [{idx}/{args.n}] FALLO")

                # Progress
                _print_progress(success, errors, existing, args.n, start_time)

        else:
            # Secuencial
            for i, text in enumerate(texts):
                idx = existing + i + 1
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta_min = (len(texts) - i - 1) / rate / 60 if rate > 0 else 0

                print(f"  [{idx}/{args.n}] ", end="", flush=True)

                labels = call_model(text)

                if labels:
                    _write_result(f_out, text, labels, dim_names)
                    success += 1
                    pos = labels.get("posicion_observador", "?")
                    print(f"OK (pos={pos}, {rate:.1f}/min, ETA:{eta_min:.0f}m)")
                else:
                    f_err.write(json.dumps({
                        "text": text[:200], "error": "no_response"
                    }, ensure_ascii=False) + "\n")
                    errors += 1
                    print(f"FALLO")

                # Checkpoint cada 100
                if idx % 100 == 0:
                    _print_progress(success, errors, existing, args.n, start_time)
                    send_telegram(
                        f"Gold Set v2 checkpoint\n"
                        f"{success}/{args.n} OK | {errors} err\n"
                        f"ETA: {eta_min:.0f} min"
                    )

                # Rate limiting
                if args.method != "cli":
                    time.sleep(0.5)

    # Resumen final
    total_time = time.time() - start_time
    _print_final(success, errors, args.n, total_time, output_path, args.method)

    # Validar distribución
    _validate_distribution(output_path)

    send_telegram(
        f"Gold Set v2 COMPLETADO\n"
        f"{success}/{args.n} textos OK\n"
        f"{errors} errores\n"
        f"Tiempo: {total_time/3600:.1f}h\n"
        f"Archivo: {output_path.name}"
    )


def _write_result(f_out, text: str, labels: dict, dim_names: list):
    """Escribe un resultado validado."""
    # Rellenar dims faltantes
    missing = [d for d in dim_names if d not in labels]
    if missing:
        for d in missing:
            labels[d] = None

    entry = {
        "text": text,
        "labels": labels,
        "model": "claude-opus-4",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
    f_out.flush()  # Flush para no perder datos en crash


def _print_progress(success, errors, existing, total, start_time):
    elapsed = time.time() - start_time
    done = success + errors - existing
    rate = done / elapsed * 60 if elapsed > 0 else 0
    remaining = total - success - errors
    eta_h = remaining / (rate / 60) / 3600 if rate > 0 else 0
    print(f"\n  {'='*40}")
    print(f"  Checkpoint: {success} OK, {errors} err, {rate:.1f}/min, ETA: {eta_h:.1f}h")
    print(f"  {'='*40}\n")


def _print_final(success, errors, total, total_time, output_path, method):
    cost = "$0 (Max)" if method == "cli" else f"~${success * 0.10:.0f}"
    print(f"\n{'='*60}")
    print(f"GOLD SET v2 COMPLETADO")
    print(f"{'='*60}")
    print(f"  Textos OK:  {success}/{total}")
    print(f"  Errores:    {errors}")
    print(f"  Tiempo:     {total_time/3600:.1f}h ({total_time/60:.0f}min)")
    print(f"  Coste:      {cost}")
    print(f"  Output:     {output_path}")
    print(f"{'='*60}\n")


def _validate_distribution(output_path: Path):
    """Valida que la distribución de posiciones es razonable."""
    print("Validando distribución de posiciones...")
    counts = {"razonamiento": 0, "pensamiento": 0, "inteligencia": 0, "otro": 0}
    total = 0

    with open(output_path) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                pos = entry.get("labels", {}).get("posicion_observador", "otro")
                counts[pos] = counts.get(pos, 0) + 1
                total += 1
            except json.JSONDecodeError:
                continue

    if total == 0:
        print("  ⚠️ No hay datos para validar")
        return

    print(f"  Total: {total}")
    for pos, n in counts.items():
        pct = n / total * 100
        marker = "⚠️" if pos == "inteligencia" and n < 30 else "✅"
        print(f"  {marker} {pos}: {n} ({pct:.1f}%)")

    if counts.get("inteligencia", 0) < 30:
        print(f"\n  ⚠️ AVISO: Solo {counts.get('inteligencia', 0)} muestras de inteligencia.")
        print(f"     Considerar añadir textos filosóficos/metacognitivos al corpus.")


if __name__ == "__main__":
    main()
