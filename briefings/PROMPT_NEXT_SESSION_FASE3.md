# PROMPT SIGUIENTE SESION — Fase 3: Prescripcion ACD

**Fecha:** 2026-03-20
**Sesion anterior:** Ejecuto Fase 2 (diagnostico end-to-end: evaluador funcional + clasificador 10 estados + repertorio INT×P×R)
**Objetivo:** Escribir y ejecutar briefings B-ACD-09 a B-ACD-11

---

## ESTADO AL CERRAR (asumiendo Fase 2 completada)

### Completados
- Fase 0: B-ACD-00 (Code OS rediseno) PASS
- Fase 1: B-ACD-01 a 04 (datos P, R, estados, DB) PASS
- Fase 2: B-ACD-05 a 08 (diagnostico end-to-end) PASS (verificar CHECKLIST)

### Disponible
- `src/tcf/diagnostico.py` — `diagnosticar(texto) -> DiagnosticoCompleto` funciona
- `src/tcf/evaluador_funcional.py` — V3.2 via OpenRouter → 21 scores + VectorFuncional
- `src/tcf/repertorio.py` — V3.2 via OpenRouter → RepertorioCognitivo + verificaciones IC
- `src/utils/openrouter_client.py` — Cliente OpenRouter con json_schema + Response Healing

### Checklist maestra
- `motor-semantico/briefings/CHECKLIST_ACD.md` — leer primero, verificar Fase 2 completa

---

## QUE HACER EN ESTA SESION

### 1. Verificar que Fase 2 esta completa
```
Leer CHECKLIST_ACD.md → confirmar 05-08 todos PASS
Si algo fallo → arreglar antes de continuar
```

### 2. Escribir briefings de Fase 3 (Prescripcion)

**B-ACD-09: Seleccion cognitiva INT×P×R**
- EL BRIEFING MAS IMPORTANTE de Fase 3. Dado un DiagnosticoCompleto, prescribir que INT, P y R activar.
- Crear `src/tcf/prescriptor.py`
- Logica: codigo puro ($0), NO LLM.
  1. Desde estado diagnostico → consultar prescripcion_ps/prescripcion_rs de estados.json
  2. Desde repertorio → identificar INT ausentes que cubren la lente faltante
  3. Desde constantes → AFINIDAD_INT_L y AFINIDAD_INT_F para seleccionar INTs optimas
  4. Verificar compatibilidad INT-P (IC3) e INT-R (IC4) cruzando con pensamientos.json y razonamientos.json
  5. Asegurar pares complementarios (IC5)
  6. Output: `Prescripcion(ints, ps, rs, secuencia_funciones, frenar, lente_objetivo, objetivo)`
- YA EXISTE: `recetas.py` genera receta por arquetipo con INTs + secuencia. El prescriptor EXTIENDE esto anadiendo P y R.
- YA EXISTE: `estados.json` tiene `prescripcion_ps`, `prescripcion_rs`, `objetivo_prescripcion` por cada estado desequilibrado.
- Leer: `src/tcf/recetas.py`, `src/tcf/constantes.py` (RECETAS, AFINIDAD_INT_L, TOP_INTS_POR_LENTE), `src/tcf/estados.json`
- Pass/fail: diagnostico "operador ciego" → prescribe Ps de sentido (P05, P03, P08) + Rs profundos (R03, R09, R08) + INTs de Se

**B-ACD-10: Mapeo lente faltante → nivel logico → modo**
- Crear `src/tcf/nivel_logico.py` (~50 lineas, codigo puro $0)
- Tabla: lente faltante → que nivel logico necesita → que modo conceptual usar
- Maestro v3 define 6 modos: ANALIZAR, PERCIBIR, MOVER, SENTIR, GENERAR, ENMARCAR
- Mapeo:
  - salud faltante → nivel 1 (operativo) → MOVER, GENERAR
  - sentido faltante → nivel 3-5 (semantico/existencial) → ENMARCAR, PERCIBIR
  - continuidad faltante → nivel 4 (transferencia) → GENERAR, ANALIZAR
- El prescriptor de B-ACD-09 llama a esta funcion para completar la prescripcion con modo
- Pass/fail: `seleccionar_nivel_modo("sentido")` retorna nivel 3-5 + ENMARCAR/PERCIBIR

**B-ACD-11: Secuenciacion con prohibiciones formales**
- Extender `src/tcf/recetas.py` con `verificar_prohibiciones(secuencia, lentes) -> list[str]`
- Prohibiciones formales (derivadas de leyes TCF):
  1. NUNCA F7 sin Se previo (F7 con Se < 0.40 → amplifica sin sentido)
  2. NUNCA F2 sin F3 antes (captar sin depurar → intoxicacion)
  3. NUNCA escalar (F7) con gap > 0.30 (amplifica desequilibrio)
  4. NUNCA F6 sin F5 (adaptar sin identidad → perder esencia)
- YA EXISTE: `secuencia_universal()` en recetas.py ordena pasos. Las prohibiciones son un FILTRO posterior.
- YA EXISTE: `aplicar_regla_14()` detecta FRENAR. Las prohibiciones son complementarias.
- Pass/fail: secuencia [F7, F2, F5] con Se=0.20 → detecta "F7 sin Se previo" + "F2 sin F3"

### 3. Ejecutar briefings

Dependencias:
```
B-ACD-09 (prescriptor) ──→ B-ACD-11 (prohibiciones, se integra en prescripcion)
B-ACD-10 (nivel logico) ──→ B-ACD-09 lo usa
```

Orden: B-ACD-10 primero (es la tabla mas simple). Luego B-ACD-09 (usa B-ACD-10). Luego B-ACD-11 (filtro sobre output de B-ACD-09).

Paralelismo posible: B-ACD-10 + B-ACD-11 en paralelo (WIP=2, independientes). Luego B-ACD-09 que los integra.

---

## ARCHIVOS CLAVE A LEER

**Para estado:**
- `briefings/CHECKLIST_ACD.md`

**Para disenar B-ACD-09 (prescriptor):**
- `src/tcf/recetas.py` — RecetaResultado, generar_receta_mixta(), aplicar_regla_14(), secuencia_universal()
- `src/tcf/constantes.py` — RECETAS (11 recetas por arquetipo), AFINIDAD_INT_L, AFINIDAD_INT_F, TOP_INTS_POR_LENTE, TOP_INTS_POR_FUNCION
- `src/tcf/estados.json` — prescripcion_ps, prescripcion_rs, objetivo_prescripcion por cada desequilibrado
- `src/tcf/diagnostico.py` — DiagnosticoCompleto (input del prescriptor)
- `src/tcf/repertorio.py` — RepertorioCognitivo (input del prescriptor)
- `src/meta_red/pensamientos.json` — ints_compatibles por P (para verificar IC3)
- `src/meta_red/razonamientos.json` — ints_compatibles por R (para verificar IC4)
- `src/pipeline/router.py` — RouterResult, enforce_rules() (referencia, NO modificar)

**Para disenar B-ACD-10 (nivel logico):**
- MAESTRO_V3.md §modos — definicion de los 6 modos conceptuales (solo si necesitas consultarlo)

**Para disenar B-ACD-11 (prohibiciones):**
- `src/tcf/recetas.py` — secuencia_universal(), aplicar_regla_14() (ya existen, extender)
- `src/tcf/constantes.py` — DEPENDENCIAS (11 dependencias B/D entre funciones)

**NO leer en esta sesion:**
- evaluador_funcional.py (ya funciona, no se toca)
- openrouter_client.py (ya funciona, no se toca)
- MAESTRO_V4.md (ya procesado)
- FRAMEWORK_ACD.md (ya procesado)
- agent_loop.py, mochila.py (Code OS, no relevante)

---

## DISENO DE ALTO NIVEL (de PLAN_IMPLEMENTACION_ACD.md)

### B-ACD-09: Prescriptor
```python
def prescribir(diagnostico: DiagnosticoCompleto) -> Prescripcion:
    # 1. Receta base por arquetipo (ya existe en recetas.py)
    receta = generar_receta_mixta(scoring_arquetipos, diagnostico.vector)
    
    # 2. P y R desde estado diagnostico
    estado_data = estados_json[diagnostico.estado.id]
    ps = estado_data.get("prescripcion_ps", [])
    rs = estado_data.get("prescripcion_rs", [])
    
    # 3. INTs adicionales por lente faltante
    lente_baja = min(diagnostico.estado_campo.lentes, key=diagnostico.estado_campo.lentes.get)
    ints_refuerzo = TOP_INTS_POR_LENTE[lente_baja]
    
    # 4. Nivel logico + modo (B-ACD-10)
    nivel, modos = seleccionar_nivel_modo(lente_baja)
    
    # 5. Verificar prohibiciones (B-ACD-11)
    errores = verificar_prohibiciones(receta.secuencia, diagnostico.estado_campo.lentes)
    
    # 6. Verificar compatibilidad IC3/IC4/IC5
    ...
    
    return Prescripcion(
        ints=receta.ints + ints_refuerzo,
        ps=ps, rs=rs,
        secuencia=receta.secuencia,
        frenar=receta.frenar,
        lente_objetivo=lente_baja,
        nivel_logico=nivel,
        modos=modos,
        objetivo=estado_data.get("objetivo_prescripcion", ""),
        prohibiciones_violadas=errores,
    )
```

### B-ACD-10: Nivel logico
```python
MAPEO_LENTE_NIVEL_MODO = {
    "salud":       {"niveles": [1, 2], "modos": ["MOVER", "GENERAR"]},
    "sentido":     {"niveles": [3, 4, 5], "modos": ["ENMARCAR", "PERCIBIR"]},
    "continuidad": {"niveles": [4], "modos": ["GENERAR", "ANALIZAR"]},
}
```

### B-ACD-11: Prohibiciones
```python
PROHIBICIONES = [
    ("F7 sin Se", lambda seq, l: "F7" in seq[:2] and l["sentido"] < 0.40),
    ("F2 sin F3", lambda seq, l: idx(seq,"F2") < idx(seq,"F3") if both_present else False),
    ("F7 con gap>0.30", lambda seq, l: "F7" in seq and gap(l) > 0.30),
    ("F6 sin F5", lambda seq, l: idx(seq,"F6") < idx(seq,"F5") if both_present else False),
]
```

---

## DECISIONES ABIERTAS (CR1 de esta sesion)

1. **¿Prescriptor usa scoring de arquetipos o estado diagnostico?** 
   CR0: Ambos. El estado diagnostico da los P/R (nuevos). El arquetipo da la receta base de INTs + secuencia (existente). Se fusionan.

2. **¿B-ACD-09 reemplaza o extiende router.py?**
   CR0: NO toca router.py. El prescriptor es un modulo nuevo (`prescriptor.py`) que el orchestrator llamara en Fase 4 (B-ACD-13). router.py sigue funcionando como antes para casos sin diagnostico ACD.

3. **¿Los 3 briefings van directo a Claude Code?**
   CR0: Si. Son codigo puro ($0), sin LLM, logica clara. No necesitan validacion previa en chat.

---

## ESTIMACION

| Briefing | Complejidad | Tiempo estimado |
|----------|-------------|-----------------|
| B-ACD-10 | Baja (~50 lineas, tabla) | 15 min |
| B-ACD-11 | Baja (~40 lineas, 4 checks) | 15 min |
| B-ACD-09 | Media (~150 lineas, integracion) | 30 min |
| **Total Fase 3** | | **~1 hora** |

Toda la Fase 3 es codigo puro, $0. No usa LLM.
