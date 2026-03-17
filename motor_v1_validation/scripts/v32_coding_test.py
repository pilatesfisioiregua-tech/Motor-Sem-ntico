"""Send coding briefing to DeepSeek V3.2 Reasoner and save the result."""
import json
import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
OUTPUT_DIR = BASE_DIR / "results" / "v32_coding_test"

BRIEFING = """Implementa una función Python que:
1. Reciba un JSON con 21 celdas de la Matriz (3L×7F), cada una con grado_actual y grado_objetivo
2. Calcule el gap de cada celda
3. Ordene por gap descendente
4. Aplique las 13 reglas del compilador para seleccionar las top 4-5 inteligencias
5. Devuelva un JSON con: celdas_priorizadas, inteligencias_seleccionadas, configuracion_propuesta

Las 13 reglas son:
- Selección: (1) Núcleo irreducible: 1 cuantitativa + 1 humana + INT-16. (2) Máximo diferencial entre categorías. (3) Sweet spot: 4-5 inteligencias.
- Orden: (4) Formal primero. (5) No reorganizar secuencia. (6) Fusiones: primero la más alineada con el sujeto.
- Profundidad: (7) 2 pasadas por defecto. (8) No tercera pasada.
- Paralelización: (9) Fusiones izquierda paralelizables al ~70%. (10) Cruce derecho no factorizable.
- Patrones: (11) Marco binario universal → INT-14+INT-01 primero. (12) Conversación pendiente universal. (13) Infrautilización antes de expansión.

Las inteligencias disponibles son:
- Cuantitativa: INT-01 (Lógico-Matemática), INT-02 (Computacional), INT-07 (Financiera)
- Sistémica: INT-03 (Estructural), INT-04 (Ecológica)
- Posicional: INT-05 (Social), INT-06 (Estratégica)
- Interpretativa: INT-08 (Estética), INT-09 (Lingüística), INT-12 (Narrativa)
- Corporal: INT-10 (Cinestésica), INT-15 (Espacial)
- Expansiva: INT-13 (Prospectiva), INT-14 (Divergente)
- Operativa: INT-16 (Constructiva)
- Contemplativa: INT-17 (Contemplativa), INT-18 (Existencial)

6 irreducibles (no sustituibles): INT-01, INT-02, INT-06, INT-08, INT-14, INT-16.

Incluye tests unitarios que verifiquen:
- Test 1: gaps se calculan correctamente
- Test 2: regla 1 se cumple (1 cuantitativa + 1 humana + INT-16)
- Test 3: regla 3 se cumple (4-5 inteligencias seleccionadas)
- Test 4: regla 4 se cumple (formal primero en el orden)
- Test 5: regla 11 se cumple (marco binario → INT-14+INT-01 primero si aplica)

Devuelve TODO el código en un solo bloque Python ejecutable. Incluye los tests al final con unittest.
"""


def main():
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    print("Sending coding briefing to DeepSeek V3.2 Reasoner...")
    t0 = time.time()

    resp = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[{"role": "user", "content": BRIEFING}],
        max_tokens=8192,
    )

    elapsed = round(time.time() - t0, 2)
    content = resp.choices[0].message.content or ""
    reasoning = getattr(resp.choices[0].message, "reasoning_content", "") or ""

    if not content.strip() and reasoning.strip():
        content = reasoning

    usage = {
        "prompt": resp.usage.prompt_tokens,
        "completion": resp.usage.completion_tokens,
        "total": resp.usage.total_tokens,
    }

    print(f"OK ({elapsed}s, {usage['total']} tokens)")
    print(f"Output length: {len(content)} chars")
    print(f"Reasoning length: {len(reasoning)} chars")

    # Save full response
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "model": "deepseek-reasoner",
        "elapsed_s": elapsed,
        "tokens": usage,
        "content": content,
        "reasoning": reasoning,
    }
    with open(OUTPUT_DIR / "v32_response.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Extract Python code blocks
    import re
    code_blocks = re.findall(r"```python\n(.*?)```", content, re.DOTALL)
    if code_blocks:
        # Join all blocks into one file
        full_code = "\n\n".join(code_blocks)
        with open(OUTPUT_DIR / "compiler.py", "w", encoding="utf-8") as f:
            f.write(full_code)
        print(f"Extracted {len(code_blocks)} code block(s) -> compiler.py")
    else:
        # Maybe the whole thing is code
        with open(OUTPUT_DIR / "compiler.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("No code blocks found, saved raw content as compiler.py")

    print(f"\nResults saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
