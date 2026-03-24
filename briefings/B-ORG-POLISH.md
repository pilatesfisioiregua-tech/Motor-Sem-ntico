# B-ORG-POLISH — Arreglos quirúrgicos post-auditoría

**Fecha:** 23 marzo 2026
**Autor:** Claude (Opus)
**Para:** Claude Code
**Tipo:** Briefing de ejecución directa

---

## CONTEXTO

Auditoría del organismo (64 piezas) encontró 6 huecos. 3 ya están resueltos en código:
- ✅ HUECO 1: Endpoints GET `/organismo/director` y `/organismo/evaluacion` — YA EXISTEN en router.py
- ✅ HUECO 2: Cockpit con 6 módulos nuevos + pizarra — YA IMPLEMENTADO en cockpit.py
- ✅ HUECO 3: voz_ciclos acepta contexto_organismo — YA IMPLEMENTADO con `_enriquecer_con_organismo`

Quedan 3 huecos + 1 mejora. Total: ~80 líneas de cambios.

---

## HUECO 4: G4 desperdicia $0.05/semana en Sonnet antes de Opus

**Archivo:** `src/pilates/recompilador.py`
**Función:** `ejecutar_g4_con_recompilacion()`
**Problema:** Ejecuta Sonnet ($0.05) Y DESPUÉS Opus ($0.40). Opus sobrescribe las configs de Sonnet. $0.05/semana desperdiciados = $2.60/año.

**ANTES** (buscar esta sección, ~línea 305):
```python
    # 5. Recompilar (Sonnet — fallback si Opus falla)
    prescripcion = g4.get("prescripcion_completa", {})
    if prescripcion and "error" not in prescripcion:
        recomp = await recompilar(
            prescripcion.get("prescripcion_nivel_1", prescripcion),
            diagnostico_id=None,
        )
        g4["recompilacion"] = recomp
    else:
        g4["recompilacion"] = {"status": "skip", "razon": "Sin prescripción válida"}

    # 6. Director Opus — diseña prompts D_híbrido (sobrescribe configs Sonnet)
    try:
        from src.pilates.director_opus import dirigir_orquesta
        director = await dirigir_orquesta()
        g4["director_opus"] = director
        if director.get("status") == "ok":
            log.info("g4_director_opus_ok",
                     configs=director.get("configs_aplicadas"),
                     tiempo=director.get("tiempo_s"))
    except Exception as e:
        log.warning("g4_director_opus_error", error=str(e))
        g4["director_opus"] = {"status": "error", "error": str(e)[:200]}

    return g4
```

**DESPUÉS:**
```python
    # 5. Director Opus PRIMERO — diseña prompts D_híbrido (~$0.40)
    opus_ok = False
    try:
        from src.pilates.director_opus import dirigir_orquesta
        director = await dirigir_orquesta()
        g4["director_opus"] = director
        if director.get("status") == "ok":
            opus_ok = True
            log.info("g4_director_opus_ok",
                     configs=director.get("configs_aplicadas"),
                     tiempo=director.get("tiempo_s"))
    except Exception as e:
        log.warning("g4_director_opus_error", error=str(e))
        g4["director_opus"] = {"status": "error", "error": str(e)[:200]}

    # 6. Recompilar con Sonnet SOLO si Opus falló (fallback ~$0.05)
    if not opus_ok:
        prescripcion = g4.get("prescripcion_completa", {})
        if prescripcion and "error" not in prescripcion:
            recomp = await recompilar(
                prescripcion.get("prescripcion_nivel_1", prescripcion),
                diagnostico_id=None,
            )
            g4["recompilacion"] = recomp
            log.info("g4_sonnet_fallback", configs=recomp.get("configs_aplicadas"))
        else:
            g4["recompilacion"] = {"status": "skip", "razon": "Sin prescripción válida"}
    else:
        g4["recompilacion"] = {"status": "skip", "razon": "Opus OK, Sonnet innecesario"}

    return g4
```

---

## HUECO 5: JSON parsing inconsistente — compartir `_parse_json_robusto`

**Paso A: Crear** `src/pilates/json_utils.py` (archivo nuevo)

```python
"""Utilidades de parsing JSON robusto — compartidas por todos los agentes.

Extraído de director_opus.py para reutilización en:
evaluador_organismo.py, compositor.py, enjambre.py, guardian_sesgos.py
"""
from __future__ import annotations

import json
import re


def parse_json_robusto(raw: str) -> dict:
    """Parsea JSON con reparación de truncamiento y markdown fences.

    Estrategia en orden:
    1. Parse directo (feliz path)
    2. Extraer de markdown fences
    3. Reparar truncamiento (cerrar strings, brackets, braces)
    4. Último recurso: buscar último } que cierra JSON válido
    """
    clean = raw.strip()

    # Quitar markdown fences
    if "```" in clean:
        parts = clean.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    clean = part
                    break

    # Extraer JSON principal (del primer { al último })
    start = clean.find("{")
    if start != -1:
        clean = clean[start:]

    # Intento directo
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # --- REPARACIÓN DE TRUNCAMIENTO ---
    repaired = clean.rstrip()

    # 1. Detectar y cerrar string abierto
    in_string = False
    escaped = False
    for ch in repaired:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
    if in_string:
        repaired += '"'

    # 2. Limpiar trailing parcial
    repaired = re.sub(r',\s*"[^"]*"\s*:\s*$', '', repaired)
    repaired = re.sub(r',\s*"[^"]*"\s*$', '', repaired)
    repaired = re.sub(r',\s*$', '', repaired)

    # 3. Cerrar brackets y braces en orden correcto
    stack = []
    in_str = False
    esc = False
    for ch in repaired:
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch in ('{', '['):
            stack.append(ch)
        elif ch == '}' and stack and stack[-1] == '{':
            stack.pop()
        elif ch == ']' and stack and stack[-1] == '[':
            stack.pop()

    for opener in reversed(stack):
        repaired += ']' if opener == '[' else '}'

    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # --- ÚLTIMO RECURSO: buscar último } que forma JSON válido ---
    brace_positions = [i for i, ch in enumerate(clean) if ch == '}']
    for pos in reversed(brace_positions):
        candidate = clean[:pos + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"No se pudo parsear JSON ({len(raw)} chars)")
```

**Paso B: Actualizar** `src/pilates/director_opus.py`

Buscar la definición de `_parse_json_robusto` (empieza con `def _parse_json_robusto(raw: str) -> dict:`) y REEMPLAZAR toda la función por:

```python
def _parse_json_robusto(raw: str) -> dict:
    """Wrapper legacy — usa json_utils.parse_json_robusto."""
    from src.pilates.json_utils import parse_json_robusto
    return parse_json_robusto(raw)
```

**Paso C: Actualizar** `src/pilates/evaluador_organismo.py`

Buscar el bloque de parsing manual dentro de `evaluar_semana()` (la parte que hace `clean.split("```")` etc). REEMPLAZAR el bloque:

```python
            # Parse JSON robusto
            clean = raw.strip()
            if "```" in clean:
                parts = clean.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        try:
                            resultado_interpretacion = json.loads(part)
                            break
                        except json.JSONDecodeError:
                            continue
            if not resultado_interpretacion:
                start = clean.find("{")
                end = clean.rfind("}")
                if start != -1 and end != -1:
                    clean = clean[start:end + 1]
                resultado_interpretacion = json.loads(clean)
```

Por:
```python
            from src.pilates.json_utils import parse_json_robusto
            resultado_interpretacion = parse_json_robusto(raw)
```

**Paso D: Actualizar** `src/pilates/compositor.py`, `src/pilates/enjambre.py`, `src/pilates/guardian_sesgos.py`

En cada archivo, buscar bloques de parsing JSON manual (patrones: `clean.split("```")`, `clean.find("{")`, `clean.rfind("}")`, `json.loads(clean)` fuera de un try directo) y reemplazar por:

```python
from src.pilates.json_utils import parse_json_robusto
resultado = parse_json_robusto(raw)
```

NOTA: Si alguno ya importa `_parse_json_robusto` de `director_opus`, cambiar el import a:
```python
from src.pilates.json_utils import parse_json_robusto
```

---

## HUECO 6: Sin rate limiting en endpoints Opus

**Archivo:** `src/pilates/router.py`
**Problema:** `/acd/director-opus` ($0.40) y `/acd/metacognitivo` ($0.50) sin protección contra doble click.

**Añadir al inicio de router.py** (después de los imports existentes, antes de `log = structlog.get_logger()`):

```python
import asyncio

# Semáforos para endpoints costosos (evitar doble ejecución)
_semaforo_director = asyncio.Semaphore(1)
_semaforo_metacog = asyncio.Semaphore(1)
```

NOTA: `import asyncio` ya existe en router.py. Solo añadir las 2 líneas de semáforos.

**Actualizar endpoint** `/acd/director-opus`:

ANTES:
```python
@router.post("/acd/director-opus")
async def acd_director_opus():
    """Director Opus: lee manual, comprende estado, diseña prompts D_híbrido."""
    from src.pilates.director_opus import dirigir_orquesta
    return await dirigir_orquesta()
```

DESPUÉS:
```python
@router.post("/acd/director-opus")
async def acd_director_opus():
    """Director Opus: lee manual, comprende estado, diseña prompts D_híbrido."""
    if _semaforo_director.locked():
        return {"status": "en_curso", "mensaje": "Director Opus ya ejecutándose"}
    async with _semaforo_director:
        from src.pilates.director_opus import dirigir_orquesta
        return await dirigir_orquesta()
```

**Actualizar endpoint** `/acd/metacognitivo`:

ANTES:
```python
@router.post("/acd/metacognitivo")
async def acd_metacognitivo():
    """Meta-Cognitivo Opus: evalúa el sistema cognitivo mensualmente."""
    from src.pilates.metacognitivo import ejecutar_metacognitivo
    return await ejecutar_metacognitivo()
```

DESPUÉS:
```python
@router.post("/acd/metacognitivo")
async def acd_metacognitivo():
    """Meta-Cognitivo Opus: evalúa el sistema cognitivo mensualmente."""
    if _semaforo_metacog.locked():
        return {"status": "en_curso", "mensaje": "Meta-Cognitivo ya ejecutándose"}
    async with _semaforo_metacog:
        from src.pilates.metacognitivo import ejecutar_metacognitivo
        return await ejecutar_metacognitivo()
```

---

## MEJORA: Evaluador → Director por pizarra

**Archivo:** `src/pilates/evaluador_organismo.py`
**Función:** `evaluar_semana()`, sección 5 (Pizarra + bus + feed)

Buscar:
```python
        necesita_de=["COMPOSITOR", "ESTRATEGA"],
```

Reemplazar por:
```python
        necesita_de=["DIRECTOR_OPUS"],
```

Y en el bloque `datos={}` del mismo `escribir()`, buscar:
```python
        datos={
            "delta_lentes": comparacion["delta_lentes"],
            "estado_cambio": comparacion["estado"],
            "recomendaciones": resultado_interpretacion.get("recomendaciones_director", []),
        },
```

Reemplazar por:
```python
        datos={
            "delta_lentes": comparacion["delta_lentes"],
            "estado_cambio": comparacion["estado"],
            "recomendaciones": resultado_interpretacion.get("recomendaciones_director", []),
            "recomendaciones_director": resultado_interpretacion.get("recomendaciones_director", []),
            "evaluacion_por_agente": resultado_interpretacion.get("evaluacion_por_agente", []),
            "patrones_entre_semanas": resultado_interpretacion.get("patrones_entre_semanas", []),
        },
```

---

## TESTS DE VERIFICACIÓN

```bash
# 1. Verificar que json_utils.py existe y es importable
python -c "from src.pilates.json_utils import parse_json_robusto; print('OK: json_utils importable')"

# 2. Verificar parse robusto funciona
python -c "
from src.pilates.json_utils import parse_json_robusto
# Test 1: JSON limpio
assert parse_json_robusto('{\"a\": 1}') == {'a': 1}
# Test 2: Con markdown fences
assert parse_json_robusto('\`\`\`json\n{\"a\": 1}\n\`\`\`') == {'a': 1}
# Test 3: Truncado
assert 'a' in parse_json_robusto('{\"a\": 1, \"b\": [1, 2')
print('OK: parse_json_robusto pasa 3 tests')
"

# 3. Verificar que los imports no se rompen
python -c "from src.pilates.director_opus import _parse_json_robusto; print('OK: director_opus compatible')"
python -c "from src.pilates.evaluador_organismo import evaluar_semana; print('OK: evaluador importable')"

# 4. Verificar semáforos existen
python -c "from src.pilates.router import _semaforo_director, _semaforo_metacog; print('OK: semáforos definidos')"

# 5. Verificar orden en recompilador (Opus primero)
grep -n "Director Opus PRIMERO" src/pilates/recompilador.py && echo "OK: Opus primero" || echo "FAIL: orden no cambiado"

# 6. Verificar evaluador apunta a DIRECTOR_OPUS
grep -n "DIRECTOR_OPUS" src/pilates/evaluador_organismo.py && echo "OK: evaluador→director" || echo "FAIL: sigue COMPOSITOR"
```

**PASS = los 6 checks imprimen OK.**

---

## RESUMEN DE ARCHIVOS

| # | Archivo | Cambio | Líneas |
|---|---------|--------|--------|
| 1 | `src/pilates/json_utils.py` | NUEVO — parse_json_robusto compartido | ~70 |
| 2 | `src/pilates/director_opus.py` | Reemplazar función por wrapper | -60, +3 |
| 3 | `src/pilates/evaluador_organismo.py` | Usar json_utils + necesita_de + datos | ~10 |
| 4 | `src/pilates/compositor.py` | Usar json_utils | ~3 |
| 5 | `src/pilates/enjambre.py` | Usar json_utils | ~3 |
| 6 | `src/pilates/guardian_sesgos.py` | Usar json_utils | ~3 |
| 7 | `src/pilates/recompilador.py` | Opus primero, Sonnet fallback | ~15 |
| 8 | `src/pilates/router.py` | 2 semáforos + 2 endpoints | ~12 |

**Total neto: ~50 líneas nuevas + json_utils.py (70 líneas extraídas de director_opus).**
