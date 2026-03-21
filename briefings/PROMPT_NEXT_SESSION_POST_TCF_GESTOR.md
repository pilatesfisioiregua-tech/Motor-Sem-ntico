# PROMPT PRÓXIMA SESIÓN — Post TCF + Gestor + Gradientes Duales

**Fecha:** 2026-03-19
**Saturación:** Chat anterior saturado. Este es el punto de pickup.

---

## COMPLETADO HOY (19-mar sesión TCF)

### Código implementado y testeado (87+ tests, 0 failures):

1. **Módulo `src/tcf/`** (6 archivos, ~1000 líneas):
   - `constantes.py` — 15 tablas numéricas completas
   - `campo.py` — VectorFuncional, EstadoCampo, evaluar_campo()
   - `arquetipos.py` — scoring_multi_arquetipo(), pre_screening_linguistico()
   - `recetas.py` — generar_receta_mixta(), aplicar_regla_14(), secuencia_universal()
   - `lentes.py` — ecuacion_transferencia(), predecir_impacto(), es_equilibrio_nash()
   - `detector_tcf.py` — detectar_tcf(), enriquecer_detector_result()

2. **`src/config/reglas.py`** — 14 reglas del compilador como funciones verificables

3. **Integración TCF en pipeline** (BRIEFING_TCF_06):
   - `detector_huecos.py` — recibe vector_previo, ejecuta TCF, enriquece INTs sugeridas
   - `router.py` — recibe TCF, receta como base, LLM complementa
   - `orchestrator.py` — log TCF, pasa al router y evaluador

4. **BRIEFING_TCF_07** (3 partes):
   - Router enforce reglas — `verificar_reglas()` + auto-corrección
   - Registrador (`src/pipeline/registrador.py`) — persiste datapoints_efectividad
   - Evaluador con TCF — `evaluar_mejora_campo()`, cobertura de receta

5. **Gestor v0** (`src/gestor/`, BRIEFING_GESTOR_01):
   - `modelos.py` — catálogo de modelos + asignación modelo→celda (Exp 1+4)
   - `compilador.py` — compilar_programa() por scoring de arquetipo
   - `programa.py` — ProgramaCompilado dataclass
   - `tier.py` — decidir_tier() (5 tiers de enjambre)

6. **Doc L0 nuevo:** `docs/L0/GRADIENTES_DUALES.md`
   - Principio 41 (CR0): gradientes duales (número + semántica)
   - CeldaCampo, VectorFuncionalDual, EstadoCampoDual diseñados
   - Fase 0-4 de implementación planificada

### Pendiente (briefing listo, no ejecutado):

7. **BRIEFING_GESTOR_02** — Conectar Gestor al pipeline
   - Archivo: `briefings/BRIEFING_GESTOR_02.md`
   - Insertar Gestor en orchestrator entre detect y route
   - Router usa ProgramaCompilado como fuente principal de INTs
   - 7 tests de integración
   - **Acción: "Lee y ejecuta briefings/BRIEFING_GESTOR_02.md"**

---

## GAPS RESTANTES MAESTRO ↔ CÓDIGO

| Gap | Prioridad | Estado |
|---|---|---|
| Gestor conectado al pipeline | ALTA | BRIEFING_GESTOR_02 listo |
| Detector genera vector funcional desde texto (sin vector previo) | MEDIA | No hay briefing |
| Fase A/B automática (exploración→lookup) | MEDIA | Depende del Gestor |
| 5 tiers de enjambre reales (hoy todo es tier 3) | MEDIA | tier.py existe, falta integrar |
| Auto-diagnóstico (Matriz sobre sí misma) | BAJA | Sin briefing |
| Reactor v4 (datos reales → campo) | BAJA | Sin briefing |
| Gradientes duales (P41) | BAJA | Doc diseño listo, sin código |
| DB completa (23 tablas Maestro §6.6) | BAJA | Solo algunas creadas |
| Actualizar Maestro v3 (marcar TCF como ✅) | BAJA | Pendiente |

---

## SECUENCIA SUGERIDA PRÓXIMA SESIÓN

```
1. Ejecutar BRIEFING_GESTOR_02 (si no se hizo)
   → "Lee y ejecuta briefings/BRIEFING_GESTOR_02.md"

2. Deploy a fly.io con todo lo nuevo
   → Verificar que el motor arranca con TCF + Gestor

3. Caso real: ejecutar pipeline con input Pilates
   → Verificar: detecta "Máquina sin Alma", prescribe F5→F3→F7

4. Decidir siguiente gap a atacar
```

---

## ARCHIVOS CLAVE PARA CONTEXTO

Si necesitas re-leer algo en la sesión nueva:

| Qué | Dónde |
|---|---|
| Módulo TCF completo | `src/tcf/` (6 archivos) |
| Gestor v0 | `src/gestor/` (5 archivos) |
| Pipeline integrado | `src/pipeline/orchestrator.py` |
| Reglas 14 | `src/config/reglas.py` |
| Gradientes duales | `docs/L0/GRADIENTES_DUALES.md` |
| Índice motor | `motor-semantico/docs/INDICE_VIVO.md` |
| Briefing pendiente | `briefings/BRIEFING_GESTOR_02.md` |

---

**FIN PROMPT**
