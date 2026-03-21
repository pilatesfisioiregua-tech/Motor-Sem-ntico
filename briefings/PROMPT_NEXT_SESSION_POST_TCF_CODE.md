# PROMPT PRÓXIMA SESIÓN — Post implementación módulo TCF

**Fecha creación:** 2026-03-19
**Contexto:** Se implementó el módulo TCF completo (src/tcf/) + 14 reglas del compilador + 4 suites de test

---

## ESTADO ACTUAL

### Completado (sesión 19-mar):

1. **Módulo `src/tcf/` creado** (6 archivos, ~1000 líneas de código):
   - `constantes.py` — 15 tablas numéricas (INT×F, INT×L, dependencias, valoración F→L, 12 arquetipos, firmas, 11 recetas, umbrales)
   - `campo.py` — VectorFuncional, EstadoCampo, evaluar_campo() (Leyes 1-4, 8-11)
   - `arquetipos.py` — scoring_multi_arquetipo(), pre_screening_linguistico()
   - `recetas.py` — generar_receta_mixta(), aplicar_regla_14(), secuencia_universal()
   - `lentes.py` — ecuacion_transferencia(), predecir_impacto(), es_equilibrio_nash()
   - `detector_tcf.py` — detectar_tcf(), enriquecer_detector_result()

2. **`src/config/reglas.py` implementado** (14 reglas como funciones verificables)

3. **4 suites de test** (41 tests total):
   - `tests/test_campo.py` (15 tests)
   - `tests/test_arquetipos.py` (9 tests)
   - `tests/test_recetas.py` (9 tests)
   - `tests/test_lentes.py` (8 tests)

4. **2 briefings listos para Claude Code**:
   - `briefings/BRIEFING_TCF_TEST.md` — ejecutar pytest
   - `briefings/BRIEFING_TCF_06.md` — integrar TCF en pipeline

5. **INDICE_VIVO.md actualizado**

### Pendiente:

1. **BRIEFING_TCF_TEST** — Ejecutar pytest, corregir si falla
2. **BRIEFING_TCF_06** — Integrar TCF en pipeline (detector, router, orchestrator)
3. **Test de integración** (`test_pipeline_tcf.py`) — incluido en BRIEFING_TCF_06

---

## SECUENCIA DE EJECUCIÓN

```
Paso 1: Dile a Claude Code → "Ejecuta BRIEFING_TCF_TEST.md"
  Criterio: 0 failures en pytest

Paso 2: Dile a Claude Code → "Ejecuta BRIEFING_TCF_06.md"
  Criterio: Pipeline funciona con TCF integrada, tests existentes no rotos

Paso 3: Verificar que todo el pipeline arranca:
  cd motor-semantico && python -c "from src.pipeline.orchestrator import run_pipeline; print('OK')"
```

---

## DESPUÉS DE LA INTEGRACIÓN

Una vez TCF esté integrada y testeada, el siguiente trabajo es:

1. **Deploy a fly.io** — el motor con TCF
2. **Caso real**: ejecutar el motor contra el input de Pilates y verificar que:
   - Detecta arquetipo "Máquina sin Alma" (primario)
   - Prescribe receta F5→F3→F7
   - Las INTs seleccionadas incluyen INT-02, INT-17, INT-15, INT-12, INT-16
3. **Reactor v4 hook** — conectar datos reales del Exocortex Pilates → vector funcional → TCF

---

**FIN PROMPT**
