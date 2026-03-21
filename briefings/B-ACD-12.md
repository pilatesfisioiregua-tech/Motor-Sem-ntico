# B-ACD-12: Integrar P y R en generador de prompts

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-09 ✅ (prescriptor.py con Ps y Rs prescritos)
**Coste:** $0 (modificar templates, código puro)

---

## CONTEXTO

El generador (capa 3) genera prompts usando solo INTs. Los templates (`TEMPLATE_INDIVIDUAL`, `TEMPLATE_COMPOSICION`, etc.) no mencionan P (tipos de pensamiento) ni R (tipos de razonamiento). La prescripción ACD prescribe Ps y Rs específicos que deben inyectarse en los prompts para dirigir HOW piensa el modelo, no solo QUÉ inteligencia usa.

**Principio:** P y R son DIRECTIVAS DE MODO — le dicen al modelo cómo abordar el caso. No reemplazan la inteligencia, la complementan.

---

## PASO 1: Crear bloque P/R para inyección en prompts

**Archivo:** `@project/src/pipeline/generador.py` (ya existe)

**Leer primero.** Luego AÑADIR después de los imports existentes y antes de `TEMPLATE_INDIVIDUAL`:

```python
from src.meta_red import load_pensamientos, load_razonamientos


def _generar_bloque_pr(ps: list[str], rs: list[str]) -> str:
    """Genera bloque de texto con Ps y Rs prescritos para inyectar en prompts.

    Args:
        ps: IDs de pensamientos prescritos (ej: ["P05", "P03", "P08"])
        rs: IDs de razonamientos prescritos (ej: ["R03", "R09", "R08"])

    Returns:
        Bloque de texto formateado, o string vacío si no hay P/R.
    """
    if not ps and not rs:
        return ""

    ps_data = load_pensamientos()
    rs_data = load_razonamientos()

    lines = ["\n## DIRECTIVAS COGNITIVAS (cómo abordar este caso)\n"]

    if ps:
        lines.append("TIPOS DE PENSAMIENTO A APLICAR:")
        for pid in ps:
            p = ps_data.get(pid, {})
            nombre = p.get("nombre", pid)
            pregunta = p.get("pregunta_activadora", "")
            lines.append(f"  - {pid} {nombre}: {pregunta}")
        lines.append("")

    if rs:
        lines.append("TIPOS DE RAZONAMIENTO A USAR:")
        for rid in rs:
            r = rs_data.get(rid, {})
            nombre = r.get("nombre", rid)
            desc = r.get("descripcion", "")[:80]
            lines.append(f"  - {rid} {nombre}: {desc}")
        lines.append("")

    lines.append("INSTRUCCIÓN: Aplica estos tipos de pensamiento y razonamiento "
                 "ACTIVAMENTE durante tu análisis. No los menciones por nombre — "
                 "úsalos como lentes operativas.\n")

    return "\n".join(lines)
```

---

## PASO 2: Extender `format_individual` para aceptar P/R

**Mismo archivo.** Modificar `format_individual` para aceptar parámetro opcional `bloque_pr`:

**ANTES:**
```python
def format_individual(intel: dict, input_text: str, contexto: str | None) -> str:
```

**DESPUÉS:**
```python
def format_individual(intel: dict, input_text: str, contexto: str | None, bloque_pr: str = "") -> str:
```

Y en el cuerpo, inyectar `bloque_pr` ANTES del caso:

**ANTES:**
```python
        input=input_text,
        contexto_extra=f"CONTEXTO ADICIONAL:\n{contexto}" if contexto else "",
```

**DESPUÉS:**
```python
        input=input_text,
        contexto_extra=(
            (bloque_pr if bloque_pr else "") +
            (f"\nCONTEXTO ADICIONAL:\n{contexto}" if contexto else "")
        ),
```

---

## PASO 3: Extender `generar_prompts` para pasar P/R

**Mismo archivo.** Modificar signature:

**ANTES:**
```python
def generar_prompts(
    algoritmo: Algoritmo,
    input_text: str,
    contexto: str | None,
    inteligencias_data: dict,
) -> list[PromptPlan]:
```

**DESPUÉS:**
```python
def generar_prompts(
    algoritmo: Algoritmo,
    input_text: str,
    contexto: str | None,
    inteligencias_data: dict,
    ps: list[str] | None = None,
    rs: list[str] | None = None,
) -> list[PromptPlan]:
```

Y al inicio de la función, generar el bloque:

```python
    bloque_pr = _generar_bloque_pr(ps or [], rs or [])
```

Luego en cada llamada a `format_individual` dentro de `generar_prompts`, pasar `bloque_pr=bloque_pr`:

```python
            prompt = format_individual(intel, input_text, contexto, bloque_pr=bloque_pr)
```

(Hay 2 llamadas: una en el bloque `if operacion.tipo == 'individual':` y otra en `_add_individual`.)

---

## PASO 4: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
from src.pipeline.generador import _generar_bloque_pr, format_individual, generar_prompts
from src.meta_red import load_inteligencias

# Test 1: Bloque P/R vacío → string vacío
assert _generar_bloque_pr([], []) == ''
print('PASS 1: Bloque vacío OK')

# Test 2: Bloque con P y R
bloque = _generar_bloque_pr(['P05', 'P03'], ['R03', 'R09'])
assert 'P05' in bloque
assert 'R03' in bloque
assert 'DIRECTIVAS COGNITIVAS' in bloque
assert 'TIPOS DE PENSAMIENTO' in bloque
assert 'TIPOS DE RAZONAMIENTO' in bloque
print(f'PASS 2: Bloque P/R generado ({len(bloque)} chars)')

# Test 3: format_individual con bloque_pr
intels = load_inteligencias()
intel = intels['INT-01']
prompt_sin = format_individual(intel, 'caso test', None)
prompt_con = format_individual(intel, 'caso test', None, bloque_pr=bloque)
assert len(prompt_con) > len(prompt_sin), 'Prompt con P/R debería ser más largo'
assert 'DIRECTIVAS COGNITIVAS' in prompt_con
assert 'DIRECTIVAS COGNITIVAS' not in prompt_sin
print(f'PASS 3: format_individual con P/R ({len(prompt_con)} vs {len(prompt_sin)} chars)')

# Test 4: format_individual sin P/R → backward compatible
prompt_default = format_individual(intel, 'caso test', None)
assert 'DIRECTIVAS' not in prompt_default
print('PASS 4: Backward compatible (sin P/R = sin bloque)')

# Test 5: generar_prompts acepta ps/rs (signature check)
from src.pipeline.compositor import Algoritmo, Operacion
algo = Algoritmo(
    inteligencias=['INT-01'],
    operaciones=[Operacion(tipo='individual', inteligencias=['INT-01'], orden=1, pasadas=1)],
    loops={},
    grafo=None,
)
prompts = generar_prompts(algo, 'test', None, intels, ps=['P05'], rs=['R03'])
assert len(prompts) >= 1
# El prompt debería contener las directivas
assert 'DIRECTIVAS COGNITIVAS' in prompts[0].prompt_user
print('PASS 5: generar_prompts con ps/rs inyecta bloque')

print('\\nTODOS LOS TESTS PASAN (5/5)')
"
```

**CRITERIO PASS:**
1. Bloque vacío → string vacío (backward compatible)
2. Bloque con P/R → contiene directivas formateadas
3. format_individual con bloque_pr → inyecta en prompt
4. format_individual sin bloque_pr → sin cambio (backward compatible)
5. generar_prompts con ps/rs → prompts contienen directivas

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/pipeline/generador.py` | EDITAR — añadir import, _generar_bloque_pr(), extender format_individual y generar_prompts |

## ARCHIVOS QUE NO SE TOCAN

ejecutor.py, evaluador.py, orchestrator.py, compositor.py, router.py — se tocan en B-ACD-13.

## NOTAS

- Backward compatible: si no se pasan ps/rs, todo funciona igual que antes
- Los P/R se inyectan como "directivas cognitivas" — instrucciones de MODO, no contenido
- La pregunta_activadora de cada P es perfecta para inyectar: es una pregunta directa que el modelo puede usar
- Para R, la descripción corta da contexto suficiente
- Los templates de composición y fusión NO se modifican — P/R solo aplican a prompts individuales (el cruce entre INTs ya es un modo cognitivo implícito)
- El bloque se inyecta en `contexto_extra` del template, que va justo antes del caso — posición óptima para priming
