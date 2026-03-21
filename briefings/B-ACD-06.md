# B-ACD-06: Clasificador de 10 estados

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-03 ✅ (estados.json + flags.py)
**Paralelizable con:** B-ACD-05 (no depende de evaluador_funcional)

---

## CONTEXTO

`campo.py` tiene `atractor_mas_cercano()` con 4 atractores genéricos (colapso, aislamiento, rigidez, equilibrio). El ACD define 10 estados diagnósticos formales: 4 equilibrados (E1-E4) + 6 desequilibrados. Este briefing implementa la clasificación precisa.

---

## PASO 1: Crear diagnostico.py con clasificador

**Crear archivo:** `@project/src/tcf/diagnostico.py`

**Contenido EXACTO:**

```python
"""Diagnóstico ACD — clasificación de estado y detección de flags.

Paso P3 del pipeline ACD: lentes → estado diagnóstico (1 de 10).
Lógica pura, sin LLM ($0).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.tcf.constantes import UMBRAL_LENTE_ALTA, UMBRAL_LENTE_BAJA
from src.tcf.flags import FlagPeligro, detectar_todos_flags

_ESTADOS_PATH = Path(__file__).parent / "estados.json"


@dataclass
class EstadoDiagnostico:
    id: str                     # "E1", "operador_ciego", etc.
    nombre: str
    tipo: str                   # "equilibrado" | "desequilibrado"
    descripcion: str
    gap: float                  # max(lentes) - min(lentes)
    gradiente: float            # media de las 3 lentes
    lentes: dict[str, float]    # {salud, sentido, continuidad}
    flags: list[FlagPeligro] = field(default_factory=list)


def clasificar_estado(
    lentes: dict[str, float],
    scores_f_se: dict[str, float] | None = None,
) -> EstadoDiagnostico:
    """Clasifica un sistema en uno de los 10 estados ACD.

    Args:
        lentes: {salud: float, sentido: float, continuidad: float}
        scores_f_se: Scores de Se por función (para flag monopolio_se). Opcional.

    Returns:
        EstadoDiagnostico con estado, flags y métricas.
    """
    s = lentes["salud"]
    se = lentes["sentido"]
    c = lentes["continuidad"]

    gap = max(s, se, c) - min(s, se, c)
    gradiente = (s + se + c) / 3.0

    # Cargar estados para descripción/nombre
    estados_data = json.loads(_ESTADOS_PATH.read_text())

    # Detectar flags de peligro
    flags = detectar_todos_flags(lentes, scores_f_se)

    if gap < 0.15:
        # EQUILIBRADO: clasificar por gradiente
        if gradiente < 0.20:
            eid = "E1"
        elif gradiente < 0.40:
            eid = "E2"
        elif gradiente < 0.65:
            eid = "E3"
        else:
            eid = "E4"

        info = estados_data["equilibrados"][eid]
        return EstadoDiagnostico(
            id=eid,
            nombre=info["nombre"],
            tipo="equilibrado",
            descripcion=info["descripcion"],
            gap=round(gap, 3),
            gradiente=round(gradiente, 3),
            lentes=lentes,
            flags=flags,
        )

    # DESEQUILIBRADO: clasificar por distribución S/Se/C
    s_alta = s >= UMBRAL_LENTE_ALTA
    se_alta = se >= UMBRAL_LENTE_ALTA
    c_alta = c >= UMBRAL_LENTE_ALTA

    # 6 perfiles posibles (1 alta + 2 bajas, o 2 altas + 1 baja)
    if s_alta and not se_alta and not c_alta:
        did = "operador_ciego"
    elif not s_alta and se_alta and not c_alta:
        did = "visionario_atrapado"
    elif not s_alta and not se_alta and c_alta:
        did = "zombi_inmortal"
    elif s_alta and se_alta and not c_alta:
        did = "genio_mortal"
    elif s_alta and not se_alta and c_alta:
        did = "automata_eterno"
    elif not s_alta and se_alta and c_alta:
        did = "potencial_dormido"
    else:
        # Caso borde: todas bajas o todas altas pero gap >= 0.15
        # → clasificar por lente más desviada de la media
        desviaciones = {
            "salud": abs(s - gradiente),
            "sentido": abs(se - gradiente),
            "continuidad": abs(c - gradiente),
        }
        lente_max_desv = max(desviaciones, key=desviaciones.get)
        lente_val = lentes[lente_max_desv]

        if lente_val > gradiente:
            # Una lente sube por encima → perfil de 1 alta
            if lente_max_desv == "salud":
                did = "operador_ciego"
            elif lente_max_desv == "sentido":
                did = "visionario_atrapado"
            else:
                did = "zombi_inmortal"
        else:
            # Una lente baja por debajo → perfil de 2 altas
            if lente_max_desv == "salud":
                did = "potencial_dormido"
            elif lente_max_desv == "sentido":
                did = "automata_eterno"
            else:
                did = "genio_mortal"

    info = estados_data["desequilibrados"][did]
    return EstadoDiagnostico(
        id=did,
        nombre=info["nombre"],
        tipo="desequilibrado",
        descripcion=info["descripcion"],
        gap=round(gap, 3),
        gradiente=round(gradiente, 3),
        lentes=lentes,
        flags=flags,
    )
```

---

## PASO 2: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
from src.tcf.diagnostico import clasificar_estado

# === EQUILIBRADOS ===

# E1: Muerte simétrica (gradiente < 0.20, gap < 0.15)
e1 = clasificar_estado({'salud': 0.10, 'sentido': 0.12, 'continuidad': 0.08})
assert e1.id == 'E1', f'Expected E1, got {e1.id}'
assert e1.tipo == 'equilibrado'
print(f'PASS: E1 — {e1.nombre} (gap={e1.gap}, grad={e1.gradiente})')

# E2: Latencia (0.20 <= gradiente < 0.40, gap < 0.15)
e2 = clasificar_estado({'salud': 0.30, 'sentido': 0.28, 'continuidad': 0.32})
assert e2.id == 'E2', f'Expected E2, got {e2.id}'
print(f'PASS: E2 — {e2.nombre} (gap={e2.gap}, grad={e2.gradiente})')

# E3: Funcional (0.40 <= gradiente < 0.65, gap < 0.15)
e3 = clasificar_estado({'salud': 0.50, 'sentido': 0.52, 'continuidad': 0.48})
assert e3.id == 'E3', f'Expected E3, got {e3.id}'
print(f'PASS: E3 — {e3.nombre} (gap={e3.gap}, grad={e3.gradiente})')

# E4: Plenitud (gradiente >= 0.65, gap < 0.15)
e4 = clasificar_estado({'salud': 0.75, 'sentido': 0.72, 'continuidad': 0.78})
assert e4.id == 'E4', f'Expected E4, got {e4.id}'
print(f'PASS: E4 — {e4.nombre} (gap={e4.gap}, grad={e4.gradiente})')

# === DESEQUILIBRADOS ===

# Operador ciego: S↑ Se↓ C↓
oc = clasificar_estado({'salud': 0.65, 'sentido': 0.25, 'continuidad': 0.30})
assert oc.id == 'operador_ciego', f'Expected operador_ciego, got {oc.id}'
print(f'PASS: {oc.id} — {oc.nombre} (gap={oc.gap})')

# Visionario atrapado: S↓ Se↑ C↓
va = clasificar_estado({'salud': 0.25, 'sentido': 0.65, 'continuidad': 0.30})
assert va.id == 'visionario_atrapado', f'Expected visionario_atrapado, got {va.id}'
print(f'PASS: {va.id} — {va.nombre}')

# Zombi inmortal: S↓ Se↓ C↑
zi = clasificar_estado({'salud': 0.30, 'sentido': 0.25, 'continuidad': 0.65})
assert zi.id == 'zombi_inmortal', f'Expected zombi_inmortal, got {zi.id}'
print(f'PASS: {zi.id} — {zi.nombre}')

# Genio mortal: S↑ Se↑ C↓
gm = clasificar_estado({'salud': 0.60, 'sentido': 0.65, 'continuidad': 0.25})
assert gm.id == 'genio_mortal', f'Expected genio_mortal, got {gm.id}'
print(f'PASS: {gm.id} — {gm.nombre}')

# Autómata eterno: S↑ Se↓ C↑
ae = clasificar_estado({'salud': 0.65, 'sentido': 0.20, 'continuidad': 0.60})
assert ae.id == 'automata_eterno', f'Expected automata_eterno, got {ae.id}'
print(f'PASS: {ae.id} — {ae.nombre}')

# Potencial dormido: S↓ Se↑ C↑
pd = clasificar_estado({'salud': 0.25, 'sentido': 0.60, 'continuidad': 0.65})
assert pd.id == 'potencial_dormido', f'Expected potencial_dormido, got {pd.id}'
print(f'PASS: {pd.id} — {pd.nombre}')

# === FLAGS ===

# Autómata eterno debería disparar flag automata_oculto + zona_toxica
assert any(f.nombre == 'automata_oculto' for f in ae.flags), 'automata_eterno debería disparar flag automata_oculto'
assert any(f.nombre == 'zona_toxica' for f in ae.flags), 'automata_eterno con Se=0.20 debería disparar zona_toxica'
print(f'PASS: Flags de automata_eterno: {[f.nombre for f in ae.flags]}')

# === TEST CASO PILATES ===
# Lentes esperadas: S≈0.49, Se≈0.46, C≈0.32 (de calcular_lentes con VECTOR_PILATES)
from src.tcf.campo import VectorFuncional, calcular_lentes
from src.tcf.constantes import VECTOR_PILATES
v = VectorFuncional.from_dict(VECTOR_PILATES)
lentes = calcular_lentes(v)
pilates = clasificar_estado(lentes)
print(f'\\nCaso Pilates: estado={pilates.id} ({pilates.nombre}), gap={pilates.gap}, grad={pilates.gradiente}')
print(f'Lentes: S={lentes[\"salud\"]:.3f} Se={lentes[\"sentido\"]:.3f} C={lentes[\"continuidad\"]:.3f}')
# Pilates debería ser genio_mortal (S↑ Se↑ C↓) o E3 funcional (si gap < 0.15)
# Depende de lentes calculadas reales — el test verifica que no crashea y da resultado coherente
assert pilates.tipo in ('equilibrado', 'desequilibrado'), 'Tipo inválido'
print(f'PASS: Caso Pilates clasificado como {pilates.id}')

print('\\nTODOS LOS TESTS PASAN (10/10 estados + flags + Pilates)')
"
```

**CRITERIO PASS:**
1. 4 vectores equilibrados → E1, E2, E3, E4 correctamente
2. 6 vectores desequilibrados → 6 estados correctamente
3. Flags se detectan donde corresponde
4. Caso Pilates (vector real) → clasificación coherente sin crash

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/diagnostico.py` | CREAR (nuevo) |

## ARCHIVOS QUE NO SE TOCAN

campo.py, constantes.py, flags.py, estados.json — todo se lee, nada se modifica.

## NOTAS

- UMBRAL_LENTE_ALTA = 0.50 (de constantes.py) es el corte para "alta" vs "no alta"
- El caso borde (todas altas o todas bajas con gap >= 0.15) usa la lente más desviada de la media para desambiguar
- estados.json se carga en cada llamada (no singleton). Es un archivo pequeño (<3KB). Si el profiling lo requiere, se puede hacer singleton después.
- clasificar_estado() es código puro, $0, ~0ms
