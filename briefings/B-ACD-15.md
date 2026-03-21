# B-ACD-15: Decisión ternaria (cierre / inerte / tóxico)

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-14 ✅ (MetricasACD disponible)
**Coste:** $0 (código puro, lógica de decisión)

---

## CONTEXTO

Toda intervención tiene exactamente 3 posibles resultados:
1. **CIERRE** — la intervención cerró el gap (mejoró la lente objetivo)
2. **INERTE** — no hizo nada (outputs genéricos, no atacó el problema)
3. **TÓXICO** — empeoró (violó prohibiciones, amplificó desequilibrio)

Esta decisión es CRÍTICA para el loop de aprendizaje. Si es CIERRE, registrar como éxito. Si es INERTE, intentar de nuevo con más profundidad. Si es TÓXICO, FRENAR y revisar prescripción.

**Nota:** Sin vector funcional POST-ejecución (requeriría re-evaluar el sistema después de la intervención), la decisión es HEURÍSTICA basada en las métricas ACD de B-ACD-14. Cuando exista Reactor v4 con telemetría real, se podrá medir el delta real del campo.

---

## PASO 1: Añadir decisión ternaria a evaluador_acd.py

**Archivo:** `@project/src/tcf/evaluador_acd.py` (ya existe de B-ACD-14)

**Leer primero.** Luego AÑADIR al final:

```python
# ---------------------------------------------------------------------------
# DECISIÓN TERNARIA
# ---------------------------------------------------------------------------

@dataclass
class DecisionTernaria:
    veredicto: str            # "cierre" | "inerte" | "toxico"
    confianza: float          # 0.0 - 1.0
    razon: str                # Explicación en 1 frase
    recomendacion: str        # Qué hacer a continuación
    metricas_clave: dict      # Métricas que determinaron la decisión


def decidir(metricas: MetricasACD) -> DecisionTernaria:
    """Decisión ternaria: ¿la intervención cerró, fue inerte, o fue tóxica?

    Reglas (en orden de prioridad):

    TÓXICO si:
      - Hay prohibiciones críticas violadas (PRH-01 o PRH-03), O
      - Cobertura INTs < 0.20 Y hay prohibiciones de cualquier severidad

    INERTE si:
      - Cobertura INTs < 0.40 (menos de la mitad de INTs prescritas), O
      - Alineación P/R = 0 (ningún P/R detectado en outputs), O
      - Score ACD < 4.0

    CIERRE si:
      - Cobertura INTs >= 0.60 Y
      - Lente objetivo cubierta Y
      - Score ACD >= 6.0

    CIERRE PARCIAL si:
      - No es tóxico ni inerte pero no cumple todos los criterios de cierre

    Args:
        metricas: MetricasACD de la evaluación.

    Returns:
        DecisionTernaria con veredicto y recomendación.
    """
    prohibiciones = metricas.prohibiciones_violadas
    cobertura = metricas.cobertura_ints
    alineacion = metricas.alineacion_pr
    lente_ok = metricas.lente_cubierta
    score = metricas.score_acd

    metricas_clave = {
        "cobertura_ints": cobertura,
        "alineacion_pr": alineacion,
        "lente_cubierta": lente_ok,
        "score_acd": score,
        "prohibiciones": prohibiciones,
    }

    # --- TÓXICO ---
    prohibiciones_criticas = [p for p in prohibiciones if p in ("PRH-01", "PRH-03")]
    if prohibiciones_criticas:
        return DecisionTernaria(
            veredicto="toxico",
            confianza=0.90,
            razon=f"Prohibiciones críticas activas: {prohibiciones_criticas}. "
                  "La intervención amplifica el desequilibrio.",
            recomendacion="FRENAR. Revisar prescripción. Eliminar funciones que violan prohibiciones "
                          "antes de re-ejecutar.",
            metricas_clave=metricas_clave,
        )

    if cobertura < 0.20 and prohibiciones:
        return DecisionTernaria(
            veredicto="toxico",
            confianza=0.75,
            razon=f"Cobertura mínima ({cobertura:.0%}) con prohibiciones activas ({prohibiciones}). "
                  "Ejecución desalineada y dañina.",
            recomendacion="FRENAR. Re-diagnosticar. Las INTs ejecutadas no corresponden a la prescripción.",
            metricas_clave=metricas_clave,
        )

    # --- INERTE ---
    if cobertura < 0.40:
        return DecisionTernaria(
            veredicto="inerte",
            confianza=0.85,
            razon=f"Solo {cobertura:.0%} de INTs prescritas ejecutadas. "
                  "La intervención no atacó el problema.",
            recomendacion="Ampliar presupuesto o forzar INTs prescritas. "
                          "El Router descartó INTs clave.",
            metricas_clave=metricas_clave,
        )

    if alineacion == 0.0 and (metricas.ps_prescritos or metricas.rs_prescritos):
        return DecisionTernaria(
            veredicto="inerte",
            confianza=0.70,
            razon="Ningún P/R prescrito detectado en outputs. "
                  "Las INTs se ejecutaron pero sin la dirección cognitiva correcta.",
            recomendacion="Reforzar bloque P/R en prompts. Los templates no inyectaron "
                          "las directivas correctamente.",
            metricas_clave=metricas_clave,
        )

    if score < 4.0:
        return DecisionTernaria(
            veredicto="inerte",
            confianza=0.65,
            razon=f"Score ACD bajo ({score}/10). Intervención genérica sin foco.",
            recomendacion="Aumentar profundidad (tier 3+). Usar modo específico "
                          f"({metricas.lente_objetivo}) en vez de genérico.",
            metricas_clave=metricas_clave,
        )

    # --- CIERRE ---
    if cobertura >= 0.60 and lente_ok and score >= 6.0:
        return DecisionTernaria(
            veredicto="cierre",
            confianza=min(0.60 + cobertura * 0.20 + (0.10 if alineacion > 0.5 else 0), 0.95),
            razon=f"Cobertura {cobertura:.0%}, lente {metricas.lente_objetivo} cubierta, "
                  f"score {score}/10. Intervención alineada con prescripción.",
            recomendacion="Registrar como éxito. Medir delta real del campo en próxima "
                          "interacción (Reactor v4).",
            metricas_clave=metricas_clave,
        )

    # --- CIERRE PARCIAL ---
    return DecisionTernaria(
        veredicto="cierre",
        confianza=0.45,
        razon=f"Cierre parcial: cobertura={cobertura:.0%}, lente={'sí' if lente_ok else 'no'}, "
              f"score={score}/10. Mejorable pero no inerte.",
        recomendacion="Aceptar como cierre parcial. En próxima iteración, "
                      f"focalizar en {'lente ' + metricas.lente_objetivo if not lente_ok else 'profundidad'}.",
        metricas_clave=metricas_clave,
    )
```

---

## PASO 2: Integrar decisión en evaluador.py

**Archivo:** `@project/src/pipeline/evaluador.py`

**Añadir import:**
```python
from src.tcf.evaluador_acd import evaluar_acd, MetricasACD, decidir, DecisionTernaria
```

**Añadir campo a EvaluationResult:**
```python
    decision_acd: DecisionTernaria | None = None
```

**En `evaluar()`, después de calcular metricas_acd, añadir:**
```python
    decision_acd = None
    if metricas_acd:
        decision_acd = decidir(metricas_acd)
        log.info("acd.decision",
                 veredicto=decision_acd.veredicto,
                 confianza=decision_acd.confianza,
                 razon=decision_acd.razon[:80])
```

Y en el return, añadir `decision_acd=decision_acd`.

---

## PASO 3: Incluir decisión en response del orchestrator

**Archivo:** `@project/src/pipeline/orchestrator.py`

**En la sección `meta` del response, añadir:**
```python
            "acd_decision": {
                "veredicto": evaluation.decision_acd.veredicto if evaluation.decision_acd else None,
                "confianza": evaluation.decision_acd.confianza if evaluation.decision_acd else None,
                "razon": evaluation.decision_acd.razon if evaluation.decision_acd else None,
                "recomendacion": evaluation.decision_acd.recomendacion if evaluation.decision_acd else None,
            } if evaluation.decision_acd else None,
```

---

## PASO 4: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
from src.tcf.evaluador_acd import MetricasACD, decidir, DecisionTernaria
from src.tcf.nivel_logico import NivelModo

# Helper para crear MetricasACD rápido
def make_metricas(**kw):
    defaults = dict(
        ints_prescritas=['INT-17','INT-08','INT-12'],
        ints_ejecutadas=[],
        cobertura_ints=0.0,
        ps_prescritos=['P05'], ps_detectados=[],
        rs_prescritos=['R03'], rs_detectados=[],
        alineacion_pr=0.0,
        lente_objetivo='sentido',
        funciones_atacadas=[],
        lente_cubierta=False,
        prohibiciones_violadas=[],
        score_acd=0.0,
        detalle={},
    )
    defaults.update(kw)
    return MetricasACD(**defaults)

# Test 1: TÓXICO — prohibiciones críticas
m = make_metricas(prohibiciones_violadas=['PRH-01'])
d = decidir(m)
assert d.veredicto == 'toxico', f'Expected toxico, got {d.veredicto}'
print(f'PASS 1: PRH-01 → tóxico (confianza={d.confianza})')

# Test 2: TÓXICO — cobertura mínima + prohibiciones
m = make_metricas(cobertura_ints=0.15, prohibiciones_violadas=['PRH-02'])
d = decidir(m)
assert d.veredicto == 'toxico', f'Expected toxico, got {d.veredicto}'
print(f'PASS 2: Cobertura 15% + prohibición → tóxico')

# Test 3: INERTE — cobertura baja
m = make_metricas(cobertura_ints=0.30)
d = decidir(m)
assert d.veredicto == 'inerte', f'Expected inerte, got {d.veredicto}'
print(f'PASS 3: Cobertura 30% → inerte')

# Test 4: INERTE — alineación P/R = 0
m = make_metricas(cobertura_ints=0.60, alineacion_pr=0.0, score_acd=5.0)
d = decidir(m)
assert d.veredicto == 'inerte', f'Expected inerte, got {d.veredicto}'
print(f'PASS 4: Alineación 0% → inerte')

# Test 5: INERTE — score bajo
m = make_metricas(cobertura_ints=0.60, alineacion_pr=0.5, score_acd=3.0)
d = decidir(m)
assert d.veredicto == 'inerte', f'Expected inerte, got {d.veredicto}'
print(f'PASS 5: Score 3/10 → inerte')

# Test 6: CIERRE — todo bien
m = make_metricas(
    ints_ejecutadas=['INT-17','INT-08'],
    cobertura_ints=0.67,
    ps_detectados=['P05'], rs_detectados=['R03'],
    alineacion_pr=0.5,
    lente_cubierta=True,
    funciones_atacadas=['F3','F5'],
    score_acd=7.5,
)
d = decidir(m)
assert d.veredicto == 'cierre', f'Expected cierre, got {d.veredicto}'
assert d.confianza >= 0.60, f'Confianza baja: {d.confianza}'
print(f'PASS 6: Todo OK → cierre (confianza={d.confianza:.2f})')

# Test 7: CIERRE PARCIAL — cobertura OK pero lente no cubierta
m = make_metricas(
    ints_ejecutadas=['INT-17','INT-08'],
    cobertura_ints=0.67,
    alineacion_pr=0.3,
    lente_cubierta=False,
    score_acd=5.5,
)
d = decidir(m)
assert d.veredicto == 'cierre', f'Expected cierre (parcial), got {d.veredicto}'
assert d.confianza < 0.50, f'Parcial debería tener confianza < 0.50: {d.confianza}'
print(f'PASS 7: Parcial → cierre con confianza {d.confianza:.2f}')

# Test 8: Recomendaciones no vacías
for case in ['toxico', 'inerte', 'cierre']:
    m = make_metricas(
        cobertura_ints={'toxico': 0.1, 'inerte': 0.3, 'cierre': 0.8}[case],
        alineacion_pr={'toxico': 0, 'inerte': 0, 'cierre': 0.6}[case],
        lente_cubierta=(case == 'cierre'),
        score_acd={'toxico': 1, 'inerte': 3, 'cierre': 8}[case],
        prohibiciones_violadas=['PRH-01'] if case == 'toxico' else [],
    )
    d = decidir(m)
    assert d.recomendacion, f'{case}: recomendación vacía'
print('PASS 8: Todas las recomendaciones no vacías')

print('\\nTODOS LOS TESTS PASAN (8/8)')
"
```

**CRITERIO PASS:**
1. PRH-01 → tóxico
2. Cobertura mínima + prohibición → tóxico
3. Cobertura baja → inerte
4. Alineación P/R = 0 → inerte
5. Score bajo → inerte
6. Todo bien → cierre (confianza ≥ 0.60)
7. Parcial → cierre con confianza < 0.50
8. Todas las recomendaciones no vacías

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/evaluador_acd.py` | EDITAR — añadir DecisionTernaria + decidir() |
| `src/pipeline/evaluador.py` | EDITAR — añadir campo decision_acd, llamar decidir() |
| `src/pipeline/orchestrator.py` | EDITAR — incluir acd_decision en response |

## NOTAS

- Código puro, $0
- La confianza es HEURÍSTICA — sin vector post real, la certeza máxima es 0.95
- "cierre parcial" se reporta como veredicto="cierre" con confianza < 0.50 — el consumidor decide si aceptar
- Cuando Reactor v4 esté disponible, se podrá comparar vector_pre vs vector_post para decisión empírica
- La recomendación es ACCIONABLE: dice exactamente qué hacer (frenar, ampliar, focalizar)
- El veredicto alimenta el loop de aprendizaje: cierre → registrar éxito, inerte → reintentar, tóxico → parar
