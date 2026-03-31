#!/usr/bin/env python3
"""
OMNI-MIND Gold Set v2 — Opus Batch API
=======================================
Envía 3000 textos a Anthropic Message Batches API.
Coste: ~$44 (50% descuento vs API normal).
Tiempo: mayoría <1h, máximo 24h.

Uso:
  # Lanzar batch:
  python launch_opus_batch.py \
    --corpus motor-semantico/corpus/corpus.jsonl \
             motor-semantico/corpus/reales/tematico_filosofia.jsonl \
             motor-semantico/corpus/reales/tematico_psicologia.jsonl \
             motor-semantico/corpus/reales/amazon_reviews.jsonl \
             motor-semantico/corpus/reales/tematico_marketing.jsonl \
             motor-semantico/corpus/reales/tematico_coloquial.jsonl \
    --dims motor-semantico/configs/v2_51_dims.json \
    --output motor-semantico/data/gold_set_v2_3000.jsonl \
    --n 3000

  # Verificar estado:
  python launch_opus_batch.py --status <batch_id>

  # Descargar resultados:
  python launch_opus_batch.py --download <batch_id> \
    --output motor-semantico/data/gold_set_v2_3000.jsonl
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from shared_config import config as _cfg
    ANTHROPIC_API_KEY = _cfg.ANTHROPIC_API_KEY
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

TELEGRAM_CONFIG = ROOT / "scripts" / "telegram_config.json"
CHAT_ID = "8091188679"
STATE_FILE = ROOT / "experiments" / "batch_state.json"


# ── System prompt (idéntico al de create_gold_set_v2.py) ────────────────────

def build_system_prompt(dims_data: dict) -> str:
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
    n_total = len(dims_data.get("dims", []))

    return f"""Eres un analizador lingüístico-cognitivo experto. Tu tarea es etiquetar textos
con {n_total} dimensiones que miden la estructura cognitiva del texto.

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
8. NO incluyas explicaciones — solo el JSON."""


# ── Selección de textos ─────────────────────────────────────────────────────

def select_texts(corpus_paths: list, n: int) -> list:
    all_texts = []
    for path in corpus_paths:
        print(f"  Cargando: {path}")
        try:
            with open(path) as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        text = entry.get("text", entry.get("texto", ""))
                        if len(text) > 80:
                            all_texts.append(text)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"    ⚠️ No encontrado: {path}")
    print(f"  Total textos válidos: {len(all_texts)}")
    if len(all_texts) <= n:
        random.shuffle(all_texts)
        return all_texts
    all_texts.sort(key=len)
    step = len(all_texts) // n
    selected = [all_texts[i * step] for i in range(n)]
    random.shuffle(selected)
    print(f"  Seleccionados {len(selected)}")
    return selected


# ── Crear batch ─────────────────────────────────────────────────────────────

def create_batch(texts: list, system_prompt: str, n_dims: int) -> dict:
    """Envía batch de requests a Anthropic Message Batches API."""

    requests = []
    for i, text in enumerate(texts):
        requests.append({
            "custom_id": f"gold-{i:05d}",
            "params": {
                "model": "claude-opus-4-20250514",
                "max_tokens": 2000,
                "temperature": 0.0,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": f'Etiqueta las {n_dims} dimensiones para este texto:\n"""\n{text[:3000]}\n"""'
                    }
                ]
            }
        })

    print(f"\n  Enviando batch con {len(requests)} requests...")
    print(f"  Coste estimado: ${len(requests) * 0.0145:.2f}")

    # Escribir requests a archivo temporal (puede ser grande)
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump({"requests": requests}, tmp, ensure_ascii=False)
    tmp.close()

    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.anthropic.com/v1/messages/batches",
        "-H", f"x-api-key: {ANTHROPIC_API_KEY}",
        "-H", "anthropic-version: 2023-06-01",
        "-H", "content-type: application/json",
        "-d", f"@{tmp.name}"
    ], capture_output=True, text=True, timeout=300)

    os.unlink(tmp.name)

    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ❌ Error parsing response: {result.stdout[:500]}")
        print(f"  stderr: {result.stderr[:500]}")
        return None

    if "error" in response:
        print(f"  ❌ API Error: {response['error']}")
        return None

    batch_id = response.get("id")
    status = response.get("processing_status")
    counts = response.get("request_counts", {})

    print(f"  ✅ Batch creado: {batch_id}")
    print(f"  Status: {status}")
    print(f"  Counts: {json.dumps(counts)}")

    # Guardar estado
    state = {
        "batch_id": batch_id,
        "n_texts": len(texts),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "texts_file": None,  # Se podría guardar para mapeo
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"  Estado guardado: {STATE_FILE}")

    return response


# ── Check status ────────────────────────────────────────────────────────────

def check_status(batch_id: str) -> dict:
    result = subprocess.run([
        "curl", "-s",
        f"https://api.anthropic.com/v1/messages/batches/{batch_id}",
        "-H", f"x-api-key: {ANTHROPIC_API_KEY}",
        "-H", "anthropic-version: 2023-06-01",
    ], capture_output=True, text=True, timeout=30)

    response = json.loads(result.stdout)
    status = response.get("processing_status")
    counts = response.get("request_counts", {})

    print(f"  Batch: {batch_id}")
    print(f"  Status: {status}")
    print(f"  Succeeded: {counts.get('succeeded', 0)}")
    print(f"  Processing: {counts.get('processing', 0)}")
    print(f"  Errored: {counts.get('errored', 0)}")
    print(f"  Expired: {counts.get('expired', 0)}")

    return response


# ── Download results ────────────────────────────────────────────────────────

def download_results(batch_id: str, output_path: str, dims_data: dict):
    """Descarga resultados y los convierte a formato gold set."""

    dim_names = [d["name"] for d in dims_data.get("dims", [])]

    print(f"  Descargando resultados de {batch_id}...")

    result = subprocess.run([
        "curl", "-s",
        f"https://api.anthropic.com/v1/messages/batches/{batch_id}/results",
        "-H", f"x-api-key: {ANTHROPIC_API_KEY}",
        "-H", "anthropic-version: 2023-06-01",
    ], capture_output=True, text=True, timeout=600)

    # El resultado es JSONL
    lines = result.stdout.strip().split("\n")
    print(f"  Recibidas {len(lines)} líneas")

    success = 0
    errors = 0
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w") as f_out:
        for line in lines:
            try:
                row = json.loads(line)
                custom_id = row.get("custom_id", "")
                result_obj = row.get("result", {})
                result_type = result_obj.get("type", "")

                if result_type == "succeeded":
                    message = result_obj.get("message", {})
                    content_blocks = message.get("content", [])
                    if content_blocks:
                        content = content_blocks[0].get("text", "")
                        labels = _parse_json(content)
                        if labels:
                            # Rellenar dims faltantes
                            for d in dim_names:
                                if d not in labels:
                                    labels[d] = None

                            entry = {
                                "id": custom_id,
                                "labels": labels,
                                "model": "claude-opus-4-batch",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                            success += 1
                        else:
                            errors += 1
                    else:
                        errors += 1
                else:
                    errors += 1
                    print(f"    {custom_id}: {result_type}")

            except json.JSONDecodeError:
                errors += 1

    print(f"\n  ✅ Gold set descargado: {output}")
    print(f"  Exitosos: {success}")
    print(f"  Errores: {errors}")

    # Validar distribución
    _validate_distribution(output)

    return success, errors


def _parse_json(content: str) -> dict:
    if not content:
        return None
    clean = content.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        end_idx = -1 if lines[-1].strip().startswith("```") else len(lines)
        clean = "\n".join(lines[1:end_idx])
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start >= 0 and end > start:
        clean = clean[start:end]
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


def _validate_distribution(output_path: Path):
    counts = {"razonamiento": 0, "pensamiento": 0, "inteligencia": 0}
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
    if total > 0:
        print(f"\n  Distribución:")
        for pos, n in counts.items():
            pct = n / total * 100
            print(f"    {pos}: {n} ({pct:.1f}%)")


# ── Poll (esperar a que termine) ────────────────────────────────────────────

def poll_until_done(batch_id: str, interval: int = 60):
    """Poll cada N segundos hasta que el batch termine."""
    print(f"\n  Polling batch {batch_id} cada {interval}s...")

    while True:
        response = check_status(batch_id)
        status = response.get("processing_status")

        if status == "ended":
            print(f"\n  ✅ Batch completado!")
            send_telegram(
                f"Gold Set v2 Batch COMPLETADO\n"
                f"Batch: {batch_id}\n"
                f"Succeeded: {response.get('request_counts', {}).get('succeeded', 0)}"
            )
            return response

        succeeded = response.get("request_counts", {}).get("succeeded", 0)
        processing = response.get("request_counts", {}).get("processing", 0)
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] "
              f"processing={processing}, succeeded={succeeded}")

        time.sleep(interval)


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
    parser = argparse.ArgumentParser(description="Gold Set v2 via Opus Batch API")

    # Modo crear
    parser.add_argument("--corpus", nargs="+", help="Corpus JSONL files")
    parser.add_argument("--dims", help="Path to v2_51_dims.json")
    parser.add_argument("--output", help="Output JSONL path")
    parser.add_argument("--n", type=int, default=3000, help="Número de textos")

    # Modo status
    parser.add_argument("--status", metavar="BATCH_ID", help="Check batch status")

    # Modo download
    parser.add_argument("--download", metavar="BATCH_ID", help="Download results")

    # Modo poll (esperar)
    parser.add_argument("--poll", metavar="BATCH_ID", help="Poll hasta completar")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval (s)")

    args = parser.parse_args()

    # ── Status ──────────────────────────────────────────────────────────────
    if args.status:
        check_status(args.status)
        return

    # ── Download ────────────────────────────────────────────────────────────
    if args.download:
        if not args.output or not args.dims:
            print("Error: --download requiere --output y --dims")
            sys.exit(1)
        dims_data = json.loads(Path(args.dims).read_text())
        download_results(args.download, args.output, dims_data)
        return

    # ── Poll ────────────────────────────────────────────────────────────────
    if args.poll:
        response = poll_until_done(args.poll, args.interval)
        if args.output and args.dims:
            dims_data = json.loads(Path(args.dims).read_text())
            download_results(args.poll, args.output, dims_data)
        return

    # ── Crear batch ─────────────────────────────────────────────────────────
    if not args.corpus or not args.dims:
        parser.print_help()
        sys.exit(1)

    dims_data = json.loads(Path(args.dims).read_text())
    system_prompt = build_system_prompt(dims_data)
    n_dims = len(dims_data.get("dims", []))

    print("=" * 60)
    print("GOLD SET v2 — Opus Batch API")
    print("=" * 60)
    print(f"  Textos: {args.n}")
    print(f"  Dims: {n_dims}")
    print(f"  Coste: ~${args.n * 0.0145:.0f}")
    print(f"  Tiempo esperado: <1h")
    print("=" * 60)

    # Seleccionar textos
    texts = select_texts(args.corpus, args.n)

    # Crear batch
    response = create_batch(texts, system_prompt, n_dims)

    if response:
        batch_id = response.get("id")
        send_telegram(
            f"Gold Set v2 Batch ENVIADO\n"
            f"Batch: {batch_id}\n"
            f"Textos: {len(texts)}\n"
            f"Coste: ~${len(texts) * 0.0145:.0f}\n"
            f"Esperando resultados..."
        )

        # Guardar textos originales para mapeo posterior
        texts_file = Path(args.output).with_suffix(".texts.jsonl")
        with open(texts_file, "w") as f:
            for i, text in enumerate(texts):
                f.write(json.dumps({
                    "custom_id": f"gold-{i:05d}",
                    "text": text
                }, ensure_ascii=False) + "\n")
        print(f"\n  Textos guardados: {texts_file}")

        print(f"\n  Para verificar estado:")
        print(f"    python {__file__} --status {batch_id}")
        print(f"\n  Para esperar y descargar:")
        print(f"    python {__file__} --poll {batch_id} --output {args.output} --dims {args.dims}")
        print(f"\n  Para descargar cuando termine:")
        print(f"    python {__file__} --download {batch_id} --output {args.output} --dims {args.dims}")


if __name__ == "__main__":
    main()
