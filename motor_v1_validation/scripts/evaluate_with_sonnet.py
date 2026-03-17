"""Paso 2: Evalúa outputs de Llama contra referencia usando Sonnet — multi-modelo × multi-variante."""
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import anthropic

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY no configurada.")
    sys.exit(1)

MODEL = "claude-sonnet-4-20250514"
OUTPUT_DIR = BASE_DIR / "outputs"
INPUT_FILE = OUTPUT_DIR / "all_outputs.json"
EVAL_FILE = OUTPUT_DIR / "all_evaluations.json"


def load_data() -> tuple[list[dict], dict]:
    if not INPUT_FILE.exists():
        print(f"ERROR: No se encontró {INPUT_FILE.name}. Ejecuta run_validation.py primero.")
        sys.exit(1)
    with open(INPUT_FILE, encoding="utf-8") as f:
        outputs = json.load(f)
    with open(BASE_DIR / "data" / "reference_outputs.json", encoding="utf-8") as f:
        reference = json.load(f)
    return outputs, reference


def eval_key(r: dict) -> str:
    return f"{r['case_id']}_{r['int_id']}_{r.get('model_key','70B')}_{r.get('variant','A')}"


def load_existing_evals() -> dict[str, dict]:
    if not EVAL_FILE.exists():
        return {}
    with open(EVAL_FILE, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for e in data:
        if "error" not in e and "error" not in e.get("evaluacion", {}):
            key = eval_key(e)
            out[key] = e
    return out


def build_eval_prompt(llama_output: str, ref: dict, int_id: str, int_nombre: str, case_nombre: str) -> str:
    hallazgos_ref = "\n".join(f"  {i+1}. {h}" for i, h in enumerate(ref["hallazgos_clave"]))

    return f"""Compara el OUTPUT de un modelo open-source contra la REFERENCIA (Claude) para {case_nombre} con {int_id} ({int_nombre}).

## REFERENCIA (gold standard)

**Resumen:** {ref['resumen']}

**Firma:** {ref['firma']}

**Hallazgos clave:**
{hallazgos_ref}

## OUTPUT A EVALUAR

{llama_output}

## EVALUACIÓN

Puntúa de 0 a 10 en 5 dimensiones:
1. **COBERTURA**: ¿Qué % de hallazgos clave de la ref aparecen? (0=ninguno, 10=todos)
2. **PROFUNDIDAD**: ¿Genérico o específico con datos del caso? (0=genérico, 10=igual que ref)
3. **HALLAZGOS EXCLUSIVOS**: ¿Encontró algo valioso que la ref NO menciona? (0=nada, 10=múltiples)
4. **ERRORES FACTUALES**: ¿Errores en datos, contradicciones? (10=ningún error, 0=graves)
5. **CIERRE DE GAP**: ¿Cuánto gap analítico cierra vs referencia? (0=nada, 5=mitad, 10=iguala)

Responde SOLO JSON:
```json
{{
  "cobertura": {{"score": X, "justificacion": "..."}},
  "profundidad": {{"score": X, "justificacion": "..."}},
  "hallazgos_exclusivos": {{"score": X, "justificacion": "..."}},
  "errores_factuales": {{"score": X, "justificacion": "..."}},
  "cierre_gap": {{"score": X, "justificacion": "..."}},
  "hallazgos_llama_no_en_ref": ["..."],
  "hallazgos_ref_no_en_llama": ["..."],
  "veredicto": "..."
}}
```"""


def evaluate_single(client: anthropic.Anthropic, result: dict, reference: dict) -> dict:
    int_id = result["int_id"]
    case_id = result["case_id"]
    ref = reference["outputs"].get(int_id, {}).get(case_id)
    if not ref:
        return {"error": f"Sin referencia para {int_id} × {case_id}"}

    prompt = build_eval_prompt(
        result["output"], ref, int_id,
        result.get("int_nombre", int_id),
        result.get("case_nombre", case_id),
    )

    t0 = time.time()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = round(time.time() - t0, 2)

    raw = response.content[0].text
    try:
        j_start = raw.find("{")
        j_end = raw.rfind("}") + 1
        eval_data = json.loads(raw[j_start:j_end]) if j_start >= 0 else {"error": "No JSON", "raw": raw}
    except json.JSONDecodeError:
        eval_data = {"error": "JSON inválido", "raw": raw}

    return {
        "case_id": case_id,
        "int_id": int_id,
        "model_key": result.get("model_key", "70B"),
        "variant": result.get("variant", "A"),
        "evaluacion": eval_data,
        "tiempo_eval_s": elapsed,
        "tokens_eval": {
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens,
        },
    }


def main():
    outputs, reference = load_data()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    valid = [r for r in outputs if "error" not in r and r.get("output")]
    existing_evals = load_existing_evals()

    # Filter out already-evaluated
    to_eval = [r for r in valid if eval_key(r) not in existing_evals]
    print(f"Outputs totales: {len(valid)}, ya evaluados: {len(existing_evals)}, pendientes: {len(to_eval)}")

    evaluations = list(existing_evals.values())

    for i, result in enumerate(to_eval):
        mk = result.get("model_key", "70B")
        var = result.get("variant", "A")
        label = f"{result.get('case_nombre', result['case_id'])} × {result.get('int_nombre', result['int_id'])} [{mk}/{var}]"
        print(f"[{i+1}/{len(to_eval)}] {label}...", end=" ", flush=True)

        try:
            ev = evaluate_single(client, result, reference)
            evaluations.append(ev)

            scores = ev.get("evaluacion", {})
            if "error" not in scores:
                gap = scores.get("cierre_gap", {}).get("score", "?")
                print(f"OK (gap={gap}/10, {ev['tiempo_eval_s']}s)")
            else:
                print(f"PARSE ERROR")
        except Exception as e:
            print(f"ERROR: {e}")
            evaluations.append({
                "case_id": result["case_id"],
                "int_id": result["int_id"],
                "model_key": mk,
                "variant": var,
                "error": str(e),
            })

        # Save incrementally
        with open(EVAL_FILE, "w", encoding="utf-8") as f:
            json.dump(evaluations, f, ensure_ascii=False, indent=2)

        if i < len(to_eval) - 1:
            time.sleep(1)

    # Final save
    with open(EVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(evaluations, f, ensure_ascii=False, indent=2)

    print(f"\nEvaluaciones guardadas: {EVAL_FILE}")

    # Summary
    good = [e for e in evaluations if "error" not in e and "error" not in e.get("evaluacion", {})]
    if good:
        avg = sum(e["evaluacion"]["cierre_gap"]["score"] for e in good) / len(good)
        print(f"Gap closure medio global: {avg:.1f}/10 ({avg*10:.0f}%)")


if __name__ == "__main__":
    main()
