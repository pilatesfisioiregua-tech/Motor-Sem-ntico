# B-ACD-10: Mapeo lente faltante → nivel lógico → modo

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** Ninguna (tabla pura, código puro $0)
**Paralelizable con:** B-ACD-11

---

## CONTEXTO

Cada lente faltante requiere intervenir en un nivel lógico distinto y usar modos conceptuales específicos. Esta tabla conecta el diagnóstico de lentes (B-ACD-06) con los 6 modos conceptuales del Maestro v3: ANALIZAR, PERCIBIR, MOVER, SENTIR, GENERAR, ENMARCAR.

El prescriptor (B-ACD-09) llamará a `seleccionar_nivel_modo()` para completar la prescripción.

---

## PASO 1: Crear nivel_logico.py

**Crear archivo:** `@project/src/tcf/nivel_logico.py`

**Contenido EXACTO:**

```python
"""Nivel lógico — mapea lente faltante a nivel de intervención y modos.

Tabla derivada de Maestro v3 §modos + TCF:
  - salud faltante → nivel operativo (1-2) → MOVER, GENERAR
  - sentido faltante → nivel semántico/existencial (3-5) → ENMARCAR, PERCIBIR
  - continuidad faltante → nivel transferencia (4) → GENERAR, ANALIZAR

Código puro, $0.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NivelModo:
    lente: str                # "salud" | "sentido" | "continuidad"
    niveles: list[int]        # niveles lógicos de intervención (1-5)
    modos: list[str]          # modos conceptuales a activar
    descripcion: str          # para logs/debug


# Tabla maestra: lente faltante → niveles + modos
MAPEO_LENTE_NIVEL_MODO: dict[str, dict] = {
    "salud": {
        "niveles": [1, 2],
        "modos": ["MOVER", "GENERAR"],
        "descripcion": "Nivel operativo: acciones concretas, producción, ejecución inmediata.",
    },
    "sentido": {
        "niveles": [3, 4, 5],
        "modos": ["ENMARCAR", "PERCIBIR"],
        "descripcion": "Nivel semántico/existencial: cuestionar premisas, redefinir marcos, buscar propósito.",
    },
    "continuidad": {
        "niveles": [4],
        "modos": ["GENERAR", "ANALIZAR"],
        "descripcion": "Nivel transferencia: sistematizar, documentar, diseñar replicación.",
    },
}

# Modos secundarios que refuerzan la lente faltante sin ser el foco principal
MODOS_SECUNDARIOS: dict[str, list[str]] = {
    "salud": ["ANALIZAR"],        # Diagnosticar qué falla operativamente
    "sentido": ["SENTIR"],        # Conectar con el porqué emocional
    "continuidad": ["ENMARCAR"],  # Definir qué merece transmitirse
}


def seleccionar_nivel_modo(lente_faltante: str) -> NivelModo:
    """Dado la lente más baja, retorna nivel lógico y modos de intervención.

    Args:
        lente_faltante: "salud" | "sentido" | "continuidad"

    Returns:
        NivelModo con niveles, modos y descripción.

    Raises:
        ValueError: Si la lente no existe.
    """
    if lente_faltante not in MAPEO_LENTE_NIVEL_MODO:
        raise ValueError(
            f"Lente '{lente_faltante}' no válida. "
            f"Opciones: {list(MAPEO_LENTE_NIVEL_MODO.keys())}"
        )

    data = MAPEO_LENTE_NIVEL_MODO[lente_faltante]
    return NivelModo(
        lente=lente_faltante,
        niveles=data["niveles"],
        modos=data["modos"],
        descripcion=data["descripcion"],
    )


def modos_secundarios(lente_faltante: str) -> list[str]:
    """Retorna modos secundarios de refuerzo para la lente faltante."""
    return MODOS_SECUNDARIOS.get(lente_faltante, [])
```

---

## PASO 2: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
from src.tcf.nivel_logico import seleccionar_nivel_modo, modos_secundarios, NivelModo

# Test 1: salud faltante → nivel 1-2, MOVER + GENERAR
nm_s = seleccionar_nivel_modo('salud')
assert nm_s.niveles == [1, 2], f'Expected [1,2], got {nm_s.niveles}'
assert nm_s.modos == ['MOVER', 'GENERAR'], f'Expected MOVER+GENERAR, got {nm_s.modos}'
print(f'PASS 1: salud → niveles={nm_s.niveles}, modos={nm_s.modos}')

# Test 2: sentido faltante → nivel 3-5, ENMARCAR + PERCIBIR
nm_se = seleccionar_nivel_modo('sentido')
assert nm_se.niveles == [3, 4, 5], f'Expected [3,4,5], got {nm_se.niveles}'
assert nm_se.modos == ['ENMARCAR', 'PERCIBIR'], f'Expected ENMARCAR+PERCIBIR, got {nm_se.modos}'
print(f'PASS 2: sentido → niveles={nm_se.niveles}, modos={nm_se.modos}')

# Test 3: continuidad faltante → nivel 4, GENERAR + ANALIZAR
nm_c = seleccionar_nivel_modo('continuidad')
assert nm_c.niveles == [4], f'Expected [4], got {nm_c.niveles}'
assert nm_c.modos == ['GENERAR', 'ANALIZAR'], f'Expected GENERAR+ANALIZAR, got {nm_c.modos}'
print(f'PASS 3: continuidad → niveles={nm_c.niveles}, modos={nm_c.modos}')

# Test 4: lente inválida → ValueError
try:
    seleccionar_nivel_modo('inexistente')
    assert False, 'Debería lanzar ValueError'
except ValueError:
    print('PASS 4: ValueError para lente inválida')

# Test 5: modos secundarios
assert modos_secundarios('salud') == ['ANALIZAR']
assert modos_secundarios('sentido') == ['SENTIR']
assert modos_secundarios('continuidad') == ['ENMARCAR']
print('PASS 5: Modos secundarios correctos')

print('\\nTODOS LOS TESTS PASAN (5/5)')
"
```

**CRITERIO PASS:**
1. salud → niveles [1,2], modos [MOVER, GENERAR]
2. sentido → niveles [3,4,5], modos [ENMARCAR, PERCIBIR]
3. continuidad → niveles [4], modos [GENERAR, ANALIZAR]
4. Lente inválida → ValueError
5. Modos secundarios correctos

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/nivel_logico.py` | CREAR (nuevo) |

## ARCHIVOS QUE NO SE TOCAN

Todo lo demás.

## NOTAS

- ~50 líneas, código puro, $0, ~0ms
- Los niveles lógicos (1-5) vienen de la jerarquía del Maestro v3: 1=operativo, 2=táctico, 3=semántico, 4=transferencia, 5=existencial
- Los 6 modos (ANALIZAR, PERCIBIR, MOVER, SENTIR, GENERAR, ENMARCAR) son los del Maestro v3 §modos
- Los modos secundarios son un bonus: refuerzan sin ser el foco principal
