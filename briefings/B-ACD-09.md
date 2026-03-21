# B-ACD-09: Selección cognitiva INT×P×R (Prescriptor)

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-10 ✅ (nivel_logico.py), B-ACD-11 ✅ (verificar_prohibiciones)
**Secuencial:** Ejecutar DESPUÉS de B-ACD-10 y B-ACD-11.

---

## CONTEXTO

EL BRIEFING MÁS IMPORTANTE de Fase 3. Dado un `DiagnosticoCompleto` (de Fase 2), prescribe QUÉ activar: INTs, Ps, Rs, secuencia de funciones, modos, nivel lógico.

**Lógica:** código puro ($0), NO LLM. Fusiona dos fuentes:
1. **Receta por arquetipo** (ya existe): INTs + secuencia de funciones
2. **Prescripción por estado diagnóstico** (nuevo): Ps + Rs + objetivo

**Pipeline:**
1. Scoring de arquetipos → receta base (INTs + secuencia + frenar)
2. Estado diagnóstico → Ps + Rs prescritos (desde estados.json)
3. Lente faltante → INTs de refuerzo (desde TOP_INTS_POR_LENTE)
4. Lente faltante → nivel lógico + modos (B-ACD-10)
5. Verificar prohibiciones (B-ACD-11)
6. Verificar compatibilidad IC3/IC4/IC5 (código puro)

---

## PASO 1: Crear prescriptor.py

**Crear archivo:** `@project/src/tcf/prescriptor.py`

**Contenido EXACTO:**

```python
"""Prescriptor ACD — selección cognitiva INT×P×R.

Dado un DiagnosticoCompleto, prescribe:
  - Qué INTs activar (base por arquetipo + refuerzo por lente faltante)
  - Qué Ps usar (por estado diagnóstico)
  - Qué Rs usar (por estado diagnóstico)
  - Secuencia de funciones (receta + prohibiciones)
  - Nivel lógico y modos conceptuales
  - Funciones a FRENAR
  - Objetivo de la prescripción

Código puro, $0, sin LLM.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.tcf.arquetipos import scoring_multi_arquetipo
from src.tcf.campo import VectorFuncional
from src.tcf.constantes import TOP_INTS_POR_LENTE, LENTES
from src.tcf.nivel_logico import seleccionar_nivel_modo, NivelModo
from src.tcf.recetas import (
    generar_receta_mixta,
    verificar_prohibiciones,
    RecetaResultado,
    Prohibicion,
)
from src.meta_red import load_pensamientos, load_razonamientos

_ESTADOS_PATH = Path(__file__).parent / "estados.json"


@dataclass
class Prescripcion:
    # INTs
    ints: list[str]               # INTs a activar (base + refuerzo, dedup)
    ints_refuerzo: list[str]      # INTs añadidas por lente faltante (subset de ints)

    # P y R
    ps: list[str]                 # Tipos de pensamiento prescritos
    rs: list[str]                 # Tipos de razonamiento prescritos

    # Secuencia
    secuencia: list[str]          # Funciones en orden de ejecución
    frenar: list[str]             # Funciones a FRENAR (Regla 14 + receta)
    parar_primero: bool           # True solo para "quemado"

    # Nivel y modo
    lente_objetivo: str           # Lente más baja (foco de la intervención)
    nivel_logico: NivelModo       # Nivel + modos (de B-ACD-10)

    # Objetivo
    objetivo: str                 # "CUESTIONAR premisas", "EJECUTAR", etc.

    # Diagnóstico de la prescripción
    prohibiciones_violadas: list[Prohibicion] = field(default_factory=list)
    advertencias_ic: list[str] = field(default_factory=list)

    # Metadata
    arquetipo_base: str = ""      # Arquetipo primario que generó la receta
    estado_id: str = ""           # ID del estado diagnóstico


def prescribir(diagnostico) -> Prescripcion:
    """Genera prescripción completa desde DiagnosticoCompleto.

    Args:
        diagnostico: DiagnosticoCompleto (de B-ACD-08).
                     Type hint omitido para evitar import circular.

    Returns:
        Prescripcion con INTs, Ps, Rs, secuencia, modos, objetivo.
    """
    vector = diagnostico.vector
    estado = diagnostico.estado
    repertorio = diagnostico.repertorio
    lentes = diagnostico.estado_campo.lentes

    # --- 1. Receta base por arquetipo ---
    scoring = scoring_multi_arquetipo(vector)
    receta = generar_receta_mixta(scoring, vector)

    # --- 2. P y R desde estado diagnóstico (estados.json) ---
    estados_data = json.loads(_ESTADOS_PATH.read_text())

    ps_prescritos = []
    rs_prescritos = []
    objetivo = ""

    if estado.tipo == "desequilibrado" and estado.id in estados_data["desequilibrados"]:
        info = estados_data["desequilibrados"][estado.id]
        ps_prescritos = info.get("prescripcion_ps", [])
        rs_prescritos = info.get("prescripcion_rs", [])
        objetivo = info.get("objetivo_prescripcion", "")
    elif estado.tipo == "equilibrado":
        # Estados equilibrados: mantener, no prescribir agresivamente
        objetivo = "MANTENER" if estado.id in ("E3", "E4") else "ACTIVAR"

    # --- 3. INTs de refuerzo por lente faltante ---
    lente_baja = min(lentes, key=lentes.get)
    ints_refuerzo = TOP_INTS_POR_LENTE.get(lente_baja, [])

    # Fusionar INTs: receta base + refuerzo, dedup preservando orden
    ints_base = list(receta.ints)
    ints_todas = list(dict.fromkeys(ints_base + ints_refuerzo))

    # --- 4. Nivel lógico + modos (B-ACD-10) ---
    nivel_modo = seleccionar_nivel_modo(lente_baja)

    # --- 5. Verificar prohibiciones (B-ACD-11) ---
    prohibiciones = verificar_prohibiciones(receta.secuencia, lentes)

    # --- 6. Verificar compatibilidad IC3/IC4/IC5 ---
    advertencias = _verificar_compatibilidad_prescripcion(
        ints_todas, ps_prescritos, rs_prescritos,
    )

    return Prescripcion(
        ints=ints_todas,
        ints_refuerzo=ints_refuerzo,
        ps=ps_prescritos,
        rs=rs_prescritos,
        secuencia=receta.secuencia,
        frenar=receta.frenar,
        parar_primero=receta.parar_primero,
        lente_objetivo=lente_baja,
        nivel_logico=nivel_modo,
        objetivo=objetivo,
        prohibiciones_violadas=prohibiciones,
        advertencias_ic=advertencias,
        arquetipo_base=receta.arquetipo_base,
        estado_id=estado.id,
    )


def _verificar_compatibilidad_prescripcion(
    ints: list[str],
    ps: list[str],
    rs: list[str],
) -> list[str]:
    """Verifica compatibilidad INT-P (IC3) e INT-R (IC4) de la prescripción.

    A diferencia de repertorio.py (que verifica lo que el sistema YA tiene),
    aquí verificamos que lo que PRESCRIBIMOS sea coherente internamente.

    También verifica pares complementarios (IC5).
    """
    advertencias = []
    ps_data = load_pensamientos()
    rs_data = load_razonamientos()

    # IC3: Cada P prescrito debería tener al menos 1 INT compatible prescrita
    for pid in ps:
        p_info = ps_data.get(pid, {})
        ints_compat = p_info.get("ints_compatibles", [])
        if ints_compat and not any(i in ints for i in ints_compat):
            advertencias.append(
                f"IC3-PRE: {pid} prescrito sin INT compatible en prescripción "
                f"(necesita alguna de {ints_compat})."
            )

    # IC4: Cada R prescrito debería tener al menos 1 INT compatible prescrita
    for rid in rs:
        r_info = rs_data.get(rid, {})
        ints_compat = r_info.get("ints_compatibles", [])
        if ints_compat and not any(i in ints for i in ints_compat):
            advertencias.append(
                f"IC4-PRE: {rid} prescrito sin INT compatible en prescripción "
                f"(necesita alguna de {ints_compat})."
            )

    # IC5: Si prescribimos INT-01 (Lógica) sin INT-14 (Divergente), advertir
    pares = [
        ("INT-01", "INT-14", "Lógica sin Divergente"),
        ("INT-02", "INT-17", "Computacional sin Existencial"),
        ("INT-05", "INT-08", "Estratégica sin Social"),
        ("INT-16", "INT-15", "Constructiva sin Estética"),
    ]
    for a, b, desc in pares:
        if a in ints and b not in ints:
            advertencias.append(f"IC5-PRE: {desc} — prescribir {b} como complemento.")

    return advertencias
```

---

## PASO 2: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
from src.tcf.prescriptor import prescribir, Prescripcion
from src.tcf.campo import VectorFuncional, evaluar_campo
from src.tcf.constantes import VECTOR_PILATES, TOP_INTS_POR_LENTE
from src.tcf.diagnostico import clasificar_estado, EstadoDiagnostico
from src.tcf.repertorio import RepertorioCognitivo

# --- Construir DiagnosticoCompleto sintético ($0, sin LLM) ---

class DiagMock:
    pass

# Vector Pilates
vector = VectorFuncional.from_dict(VECTOR_PILATES)
estado_campo = evaluar_campo(vector)

# Estado: operador_ciego (S↑ Se↓ C↓) para test de Se
lentes_oc = {'salud': 0.65, 'sentido': 0.25, 'continuidad': 0.30}
estado_oc = clasificar_estado(lentes_oc)

# Repertorio sintético
repertorio = RepertorioCognitivo(
    ints_activas=['INT-01', 'INT-02', 'INT-05', 'INT-07'],
    ints_atrofiadas=['INT-16'],
    ints_ausentes=['INT-17', 'INT-18', 'INT-03', 'INT-08'],
    ps_activos=['P07', 'P13', 'P14'],
    ps_ausentes=['P08', 'P05', 'P03', 'P01'],
    rs_activos=['R01', 'R07', 'R12'],
    rs_ausentes=['R03', 'R08', 'R10'],
)

# Mock DiagnosticoCompleto
diag = DiagMock()
diag.vector = vector
diag.estado = estado_oc
diag.estado_campo = type('EC', (), {'lentes': lentes_oc})()
diag.repertorio = repertorio
diag.scores_raw = {}  # no se usa en prescriptor

# --- Ejecutar prescripción ---
presc = prescribir(diag)

# Test 1: Tipo correcto
assert isinstance(presc, Prescripcion), f'Tipo incorrecto: {type(presc)}'
print(f'PASS 1: Prescripcion creada')

# Test 2: INTs no vacías
assert len(presc.ints) >= 3, f'Pocas INTs: {presc.ints}'
print(f'PASS 2: INTs prescritas: {presc.ints}')

# Test 3: Ps de sentido prescritos para operador_ciego
assert 'P05' in presc.ps, f'P05 debería estar prescrito para operador_ciego. Ps: {presc.ps}'
assert 'P03' in presc.ps, f'P03 debería estar prescrito. Ps: {presc.ps}'
assert 'P08' in presc.ps, f'P08 debería estar prescrito. Ps: {presc.ps}'
print(f'PASS 3: Ps correctos para operador_ciego: {presc.ps}')

# Test 4: Rs profundos prescritos
assert 'R03' in presc.rs, f'R03 debería estar prescrito. Rs: {presc.rs}'
assert 'R09' in presc.rs, f'R09 debería estar prescrito. Rs: {presc.rs}'
print(f'PASS 4: Rs correctos para operador_ciego: {presc.rs}')

# Test 5: Lente objetivo es sentido (la más baja)
assert presc.lente_objetivo == 'sentido', f'Expected sentido, got {presc.lente_objetivo}'
print(f'PASS 5: Lente objetivo = {presc.lente_objetivo}')

# Test 6: INTs de refuerzo incluyen las de sentido
ints_se = TOP_INTS_POR_LENTE['sentido']
for i in ints_se:
    assert i in presc.ints, f'{i} (refuerzo Se) debería estar en INTs'
print(f'PASS 6: INTs de refuerzo Se: {presc.ints_refuerzo}')

# Test 7: Nivel lógico es 3-5 y modos son ENMARCAR/PERCIBIR
assert presc.nivel_logico.niveles == [3, 4, 5], f'Expected [3,4,5], got {presc.nivel_logico.niveles}'
assert 'ENMARCAR' in presc.nivel_logico.modos
print(f'PASS 7: Nivel={presc.nivel_logico.niveles}, Modos={presc.nivel_logico.modos}')

# Test 8: Objetivo = CUESTIONAR premisas
assert 'CUESTIONAR' in presc.objetivo, f'Expected CUESTIONAR, got {presc.objetivo}'
print(f'PASS 8: Objetivo = {presc.objetivo}')

# Test 9: Secuencia no vacía
assert len(presc.secuencia) >= 2, f'Secuencia vacía o corta: {presc.secuencia}'
print(f'PASS 9: Secuencia = {presc.secuencia}')

# Test 10: Estado ID correcto
assert presc.estado_id == 'operador_ciego', f'Expected operador_ciego, got {presc.estado_id}'
print(f'PASS 10: estado_id = {presc.estado_id}')

# --- Resumen ---
print(f'\\n=== PRESCRIPCION OPERADOR CIEGO ===')
print(f'Arquetipo base: {presc.arquetipo_base}')
print(f'INTs: {presc.ints}')
print(f'INTs refuerzo: {presc.ints_refuerzo}')
print(f'Ps: {presc.ps}')
print(f'Rs: {presc.rs}')
print(f'Secuencia: {presc.secuencia}')
print(f'Frenar: {presc.frenar}')
print(f'Lente objetivo: {presc.lente_objetivo}')
print(f'Nivel: {presc.nivel_logico.niveles}, Modos: {presc.nivel_logico.modos}')
print(f'Objetivo: {presc.objetivo}')
print(f'Prohibiciones: {[p.codigo for p in presc.prohibiciones_violadas]}')
print(f'Advertencias IC: {presc.advertencias_ic}')

print('\\nTODOS LOS TESTS PASAN (10/10)')
"
```

**CRITERIO PASS:**
1. Prescripcion se crea sin crash
2. INTs prescritas ≥ 3
3. operador_ciego → Ps de sentido (P05, P03, P08)
4. operador_ciego → Rs profundos (R03, R09)
5. Lente objetivo = sentido (la más baja)
6. INTs de refuerzo incluyen TOP_INTS_POR_LENTE["sentido"]
7. Nivel lógico 3-5, modos ENMARCAR + PERCIBIR
8. Objetivo contiene "CUESTIONAR"
9. Secuencia no vacía
10. estado_id = operador_ciego

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/prescriptor.py` | CREAR (nuevo) |

## ARCHIVOS QUE NO SE TOCAN

recetas.py, constantes.py, estados.json, nivel_logico.py, arquetipos.py, diagnostico.py, repertorio.py, campo.py, pensamientos.json, razonamientos.json — todo se **lee**, nada se modifica.

## NOTAS

- ~150 líneas, código puro, $0, ~0ms
- El test usa un DiagnosticoCompleto mock ($0) — no necesita LLM
- El prescriptor NO modifica la secuencia si hay prohibiciones violadas — solo las reporta. El orchestrator (Fase 4) decidirá qué hacer.
- Para estados equilibrados (E1-E4), el objetivo es "MANTENER" (E3/E4) o "ACTIVAR" (E1/E2). Ps y Rs quedan vacíos — no se prescribe agresivamente.
- IC3-PRE/IC4-PRE verifican coherencia INTERNA de la prescripción (lo que prescribimos es compatible entre sí), distinto de las advertencias IC del repertorio (que verifican lo que el sistema YA tiene).
- IC5-PRE sugiere complementos (ej: si prescribimos INT-01 sin INT-14, advertir). No bloquea — solo informa.
