# B-ACD-07: Inferir repertorio cognitivo INT×P×R

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-05 ✅ (necesita VectorFuncional + openrouter_client.py)
**Modelo:** DeepSeek V3.2 (`deepseek/deepseek-v3.2`) vía OpenRouter

---

## CONTEXTO

Paso P4 del pipeline ACD. Dado un caso (texto) + su VectorFuncional, inferir qué INT, P y R están activas, atrofiadas o ausentes. Combinación de LLM (inferencia) + código puro (verificaciones IC).

---

## PASO 1: Crear repertorio.py

**Crear archivo:** `@project/src/tcf/repertorio.py`

**Contenido EXACTO:**

```python
"""Repertorio cognitivo — infiere INT×P×R activas/atrofiadas/ausentes.

Paso P4 del pipeline ACD:
  1. V3.2 (OpenRouter, json_schema) infiere repertorio desde texto + vector
  2. Código puro verifica leyes IC (invariantes cognitivos)
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field

from src.tcf.campo import VectorFuncional
from src.tcf.constantes import (
    FUNCIONES, NOMBRES_FUNCIONES, NOMBRES_INTELIGENCIAS,
    AFINIDAD_INT_F, AFINIDAD_INT_L,
)
from src.meta_red import load_inteligencias, load_pensamientos, load_razonamientos
from src.utils.openrouter_client import openrouter_json, MODEL_EXTRACTOR_OR

log = structlog.get_logger()


@dataclass
class RepertorioCognitivo:
    ints_activas: list[str]      # ["INT-10", "INT-07", ...]
    ints_atrofiadas: list[str]   # Presentes pero infrautilizadas
    ints_ausentes: list[str]     # No detectadas
    ps_activos: list[str]        # ["P07", "P13", ...]
    ps_ausentes: list[str]
    rs_activos: list[str]        # ["R01", "R07", ...]
    rs_ausentes: list[str]
    advertencias_ic: list[str] = field(default_factory=list)


SYSTEM_PROMPT_REPERTORIO = """Eres un analista cognitivo. Dado un caso y su perfil funcional, infiere qué herramientas cognitivas usa el sistema.

## HERRAMIENTAS COGNITIVAS

### 18 Inteligencias (INT)
{inteligencias_resumen}

### 15 Tipos de Pensamiento (P)
{pensamientos_resumen}

### 12 Tipos de Razonamiento (R)
{razonamientos_resumen}

## INSTRUCCIONES

Analiza el caso y su vector funcional. Clasifica cada INT, P y R en:
- **activa**: claramente presente y operando
- **atrofiada**: presente pero infrautilizada o mecánica
- **ausente**: no detectada

REGLAS:
- Toda INT debe aparecer en exactamente una categoría (activa, atrofiada o ausente)
- Todo P debe aparecer en activos o ausentes
- Todo R debe aparecer en activos o ausentes
- Sé conservador: si no hay evidencia clara, marca como ausente"""


# JSON Schema para response_format
SCHEMA_REPERTORIO = {
    "type": "object",
    "properties": {
        "ints_activas": {"type": "array", "items": {"type": "string"}},
        "ints_atrofiadas": {"type": "array", "items": {"type": "string"}},
        "ints_ausentes": {"type": "array", "items": {"type": "string"}},
        "ps_activos": {"type": "array", "items": {"type": "string"}},
        "ps_ausentes": {"type": "array", "items": {"type": "string"}},
        "rs_activos": {"type": "array", "items": {"type": "string"}},
        "rs_ausentes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "ints_activas", "ints_atrofiadas", "ints_ausentes",
        "ps_activos", "ps_ausentes", "rs_activos", "rs_ausentes",
    ],
    "additionalProperties": False,
}


def _construir_resumen_ints() -> str:
    ints = load_inteligencias()
    lineas = []
    for int_id in sorted(ints.keys()):
        nombre = NOMBRES_INTELIGENCIAS.get(int_id, int_id)
        firma = ints[int_id].get("firma_semantica", "")
        if firma:
            lineas.append(f"- {int_id} ({nombre}): {firma}")
        else:
            lineas.append(f"- {int_id} ({nombre})")
    return "\n".join(lineas)


def _construir_resumen_ps() -> str:
    ps = load_pensamientos()
    lineas = []
    for pid in sorted(ps.keys()):
        nombre = ps[pid].get("nombre", pid)
        desc = ps[pid].get("descripcion", "")[:80]
        lineas.append(f"- {pid} ({nombre}): {desc}")
    return "\n".join(lineas)


def _construir_resumen_rs() -> str:
    rs = load_razonamientos()
    lineas = []
    for rid in sorted(rs.keys()):
        nombre = rs[rid].get("nombre", rid)
        desc = rs[rid].get("descripcion", "")[:80]
        lineas.append(f"- {rid} ({nombre}): {desc}")
    return "\n".join(lineas)


async def inferir_repertorio(
    caso_texto: str,
    vector: VectorFuncional,
) -> RepertorioCognitivo:
    """Infiere repertorio cognitivo INT×P×R desde texto + vector.

    Args:
        caso_texto: Descripción del caso.
        vector: VectorFuncional del caso (de evaluador_funcional).

    Returns:
        RepertorioCognitivo con clasificación + advertencias IC.
    """
    log.info("repertorio.start")

    system = SYSTEM_PROMPT_REPERTORIO.format(
        inteligencias_resumen=_construir_resumen_ints(),
        pensamientos_resumen=_construir_resumen_ps(),
        razonamientos_resumen=_construir_resumen_rs(),
    )

    user_msg = (
        f"CASO:\n{caso_texto}\n\n"
        f"VECTOR FUNCIONAL:\n{json.dumps(vector.to_dict(), indent=2)}\n"
        f"Eslabón débil: {vector.eslabon_debil()}"
    )

    data = await openrouter_json(
        model=MODEL_EXTRACTOR_OR,
        system=system,
        user_message=user_msg,
        schema_name="repertorio_cognitivo",
        schema=SCHEMA_REPERTORIO,
        max_tokens=1024,
        temperature=0.1,
    )

    repertorio = RepertorioCognitivo(
        ints_activas=data.get("ints_activas", []),
        ints_atrofiadas=data.get("ints_atrofiadas", []),
        ints_ausentes=data.get("ints_ausentes", []),
        ps_activos=data.get("ps_activos", []),
        ps_ausentes=data.get("ps_ausentes", []),
        rs_activos=data.get("rs_activos", []),
        rs_ausentes=data.get("rs_ausentes", []),
    )

    # Verificaciones IC (código puro, post-LLM)
    repertorio.advertencias_ic = _verificar_invariantes(repertorio, vector)

    log.info(
        "repertorio.ok",
        n_activas=len(repertorio.ints_activas),
        n_atrofiadas=len(repertorio.ints_atrofiadas),
        n_ausentes=len(repertorio.ints_ausentes),
        n_advertencias=len(repertorio.advertencias_ic),
    )

    return repertorio


def _verificar_invariantes(rep: RepertorioCognitivo, vector: VectorFuncional) -> list[str]:
    """Verificaciones IC post-LLM (código puro).

    IC2: Monopolio INT — una sola INT activa
    IC3: Desacople INT-P — INT activa sin P compatible
    IC4: Desacople INT-R — INT activa sin R compatible
    IC5: Pares complementarios faltantes
    IC6: R aislados — R activo sin INT que lo soporte
    """
    advertencias = []
    ps_data = load_pensamientos()
    rs_data = load_razonamientos()

    # IC2: Monopolio INT
    if len(rep.ints_activas) == 1 and len(rep.ints_atrofiadas) == 0:
        advertencias.append(
            f"IC2: Monopolio INT — solo {rep.ints_activas[0]} activa. "
            "Sistema frágil ante cambios."
        )

    # IC3: Desacople INT-P
    for int_id in rep.ints_activas:
        tiene_p_compatible = False
        for pid in rep.ps_activos:
            p_info = ps_data.get(pid, {})
            ints_compat = p_info.get("ints_compatibles", [])
            if int_id in ints_compat:
                tiene_p_compatible = True
                break
        if not tiene_p_compatible and rep.ps_activos:
            advertencias.append(
                f"IC3: {int_id} activa sin P compatible entre {rep.ps_activos}."
            )

    # IC4: Desacople INT-R
    for int_id in rep.ints_activas:
        tiene_r_compatible = False
        for rid in rep.rs_activos:
            r_info = rs_data.get(rid, {})
            ints_compat = r_info.get("ints_compatibles", [])
            if int_id in ints_compat:
                tiene_r_compatible = True
                break
        if not tiene_r_compatible and rep.rs_activos:
            advertencias.append(
                f"IC4: {int_id} activa sin R compatible entre {rep.rs_activos}."
            )

    # IC5: Pares complementarios básicos
    pares = [
        ("INT-01", "INT-14", "Lógica sin Divergente"),
        ("INT-02", "INT-17", "Computacional sin Existencial"),
        ("INT-05", "INT-08", "Estratégica sin Social"),
        ("INT-16", "INT-15", "Constructiva sin Estética"),
    ]
    for a, b, desc in pares:
        if a in rep.ints_activas and b in rep.ints_ausentes:
            advertencias.append(f"IC5: {desc} — {a} activa, {b} ausente.")

    # IC6: R aislados
    for rid in rep.rs_activos:
        r_info = rs_data.get(rid, {})
        ints_compat = r_info.get("ints_compatibles", [])
        if ints_compat and not any(i in rep.ints_activas for i in ints_compat):
            advertencias.append(
                f"IC6: {rid} activo sin INT soporte (necesita {ints_compat})."
            )

    return advertencias
```

---

## PASO 2: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
import asyncio
from src.tcf.repertorio import inferir_repertorio, _verificar_invariantes, RepertorioCognitivo
from src.tcf.repertorio import _construir_resumen_ints, _construir_resumen_ps, _construir_resumen_rs
from src.tcf.campo import VectorFuncional
from src.tcf.constantes import VECTOR_PILATES

# Test 1: Resúmenes no crashean
ints_res = _construir_resumen_ints()
ps_res = _construir_resumen_ps()
rs_res = _construir_resumen_rs()
assert 'INT-01' in ints_res and 'INT-18' in ints_res
assert 'P01' in ps_res
assert 'R01' in rs_res
print(f'PASS 1: Resúmenes OK (INT={len(ints_res)}ch, P={len(ps_res)}ch, R={len(rs_res)}ch)')

# Test 2: IC con repertorio sintético ($0)
rep_test = RepertorioCognitivo(
    ints_activas=['INT-10'],
    ints_atrofiadas=[],
    ints_ausentes=[f'INT-{i:02d}' for i in range(1, 19) if i != 10],
    ps_activos=['P07'],
    ps_ausentes=[f'P{i:02d}' for i in range(1, 16) if i != 7],
    rs_activos=['R01'],
    rs_ausentes=[f'R{i:02d}' for i in range(1, 13) if i != 1],
)
v_test = VectorFuncional.from_dict(VECTOR_PILATES)
advs = _verificar_invariantes(rep_test, v_test)
assert any('IC2' in a for a in advs), 'Deberia detectar IC2 (monopolio INT)'
print(f'PASS 2: IC detecta {len(advs)} advertencias')

# Test 3: LLM real con caso Pilates
async def test_llm():
    caso = '''Estudio de Pilates con 8 años. Rentable pero dependiente de la instructora principal.
    Sin ella, las clases se cancelan. No hay manual de operaciones. Los clientes vienen por ella.
    Identidad clara (Pilates reformer premium). Sin plan de expansión ni formación de instructores.'''

    v = VectorFuncional.from_dict(VECTOR_PILATES)
    rep = await inferir_repertorio(caso, v)

    total_ints = len(rep.ints_activas) + len(rep.ints_atrofiadas) + len(rep.ints_ausentes)
    assert total_ints >= 10, f'Pocas INT clasificadas: {total_ints}'
    print(f'PASS 3: Repertorio — {len(rep.ints_activas)} activas, {len(rep.ints_atrofiadas)} atrofiadas, {len(rep.ints_ausentes)} ausentes')

    # INT-10 (Cinestésica) debería ser activa o atrofiada
    assert 'INT-10' in rep.ints_activas or 'INT-10' in rep.ints_atrofiadas, \
        f'INT-10 deberia estar activa/atrofiada para Pilates'
    print(f'PASS 4: INT-10 detectada (coherente con Pilates)')

    print(f'\\nRepertorio: activas={rep.ints_activas}, ausentes={rep.ints_ausentes}')
    print(f'P activos={rep.ps_activos}, R activos={rep.rs_activos}')
    print(f'Advertencias IC: {rep.advertencias_ic}')

asyncio.run(test_llm())
print('\\nTODOS LOS TESTS PASAN')
"
```

**CRITERIO PASS:**
1. Resúmenes de INT/P/R se generan sin crash
2. IC detecta monopolio (código puro, $0)
3. V3.2 devuelve repertorio con estructura válida (json_schema forzado)
4. INT-10 activa/atrofiada para caso Pilates

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/repertorio.py` | CREAR (nuevo) |

## ARCHIVOS QUE NO SE TOCAN

Todo lo demás. Usa openrouter_client.py creado en B-ACD-05.

## NOTAS

- MODEL_EXTRACTOR_OR = `deepseek/deepseek-v3.2` (compartido con evaluador_funcional)
- json_schema forzado garantiza estructura sin limpieza manual
- Token count estimado: ~2000 input (definiciones INT+P+R + caso) → ~$0.0005/caso con V3.2
- Las verificaciones IC son post-LLM, código puro. No corrigen — solo advierten.
