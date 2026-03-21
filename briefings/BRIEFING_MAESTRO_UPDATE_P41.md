# BRIEFING_MAESTRO_UPDATE_P41 — Actualizar Maestro v3 con TCF+Gestor+P41

**Fecha:** 2026-03-19
**Archivo objetivo:** `docs/maestro/MAESTRO_V3.md`
**Tipo:** 9 edits quirúrgicos (str_replace). NO reescribir el archivo completo.
**Referencia:** `docs/maestro/ACTUALIZACION_MAESTRO_V3_P41_TCF_GESTOR.md`

---

## INSTRUCCIONES

Lee `docs/maestro/MAESTRO_V3.md`. Aplica los 9 edits en orden usando str_replace (busca el texto BEFORE exacto, reemplaza por AFTER). Cada edit es independiente.

**REGLA:** No modifiques nada fuera de los bloques indicados. El archivo tiene 2318 líneas — los edits tocan ~120 líneas en total.

---

## EDIT 1 — §2.8: Insertar gradientes duales antes de "Documento fuente completo"

**BEFORE:**
```
**Firma lingüística (§11 TCF):** Cada arquetipo produce patrones lingüísticos detectables (ej: "TODO depende de mí" = Máquina sin Alma). Capa 0 del Detector como pre-screening rápido.

Documento fuente completo: `docs/L0/TEORIA_CAMPO_FUNCIONAL.md` (v1.1), `docs/L0/RESULTADO_CALCULOS_ANALITICOS_v1.md`, `docs/L0/VALIDACION_TCF_CASO_PILATES.md`.
```

**AFTER:**
```
**Firma lingüística (§11 TCF):** Cada arquetipo produce patrones lingüísticos detectables (ej: "TODO depende de mí" = Máquina sin Alma). Capa 0 del Detector como pre-screening rápido.

**Gradientes duales (P41, CR0):** El campo funcional tiene DOS representaciones que coexisten por celda:
- **Numérica:** `F3 = 0.25` — para cálculos TCF, scoring de arquetipos, distancia euclídea, Tiers 1-2 (lookup rápido), dashboard.
- **Semántica:** `F3 = "No elimina horario sábados con 1 alumno. No hay señales tempranas. Tracking manual impide detectar desperdicio."` — para diagnóstico concreto, recetas específicas, evaluación de cierre real, comunicación con el usuario.

La semántica es la fuente de verdad. El número es un resumen derivado. El número NUNCA contradice la semántica. Ambos coexisten — el número sin semántica es válido (Tier 1-2), la semántica sin número es válido (pre-análisis), pero el sistema COMPLETO tiene ambos. Las intervenciones concretas ("cierra el horario de sábados") solo se derivan de la capa semántica, no de los números.

Estructura de datos: `CeldaCampo` (grado + estado + objetivo + gap_semantico + evidencias + fuente + confianza). `VectorFuncionalDual` envuelve 7 `CeldaCampo` y expone `.numerico()` → `VectorFuncional` para compatibilidad total con TCF existente.

Documento fuente completo: `docs/L0/TEORIA_CAMPO_FUNCIONAL.md` (v1.1), `docs/L0/RESULTADO_CALCULOS_ANALITICOS_v1.md`, `docs/L0/VALIDACION_TCF_CASO_PILATES.md`, `docs/L0/GRADIENTES_DUALES.md`.
```

---

## EDIT 2 — §5.1: Reemplazar los 7 pasos del pipeline

**BEFORE:**
```
PASO 0 — PRE-SCREENING LINGÜÍSTICO      ~50ms | $0 | código puro
  Input: caso en lenguaje natural
  Detecta: firma lingüística del input (patrones sintácticos)
  Output: arquetipos candidatos (hipótesis para Paso 1)
  Ej: "TODO depende de mí" → Máquina sin Alma (70%)

PASO 1 — DETECTOR DE HUECOS           ~200ms | $0 | código puro
  Input: caso en lenguaje natural + arquetipos candidatos de Paso 0
  7 primitivas + 8 operaciones sintácticas + 14 leyes TCF
  Output: vector funcional 7F×3L + scoring multi-arquetipo + campo de gradientes
  Detecta: falacias aritméticas + violaciones de leyes TCF + coalición de lentes dominante

PASO 2 — ROUTER                        ~500ms-3s | ~$0.001 | reglas + modelo OS
  Input: campo de gradientes + scoring multi-arquetipo
  Selecciona receta del arquetipo primario como BASE
  Mezcla funciones de secundarios/terciarios (score ≥ 0.15)
  Para cada celda con gap > 0.3:
    ¿Qué INT cierra ESTE gap con más efectividad?
  Output: receta mixta + selección de INTs + orden + modelos asignados
  Usa: 14 reglas compilador + asignación modelo→celda del Gestor + TCF Teorema 2
  Si Regla 14 aplica: FRENAR antes de construir
  Tier 1-2: reglas heurísticas. Tier 3+: modelo OS ligero

PASO 3 — COMPOSITOR                    ~200ms | $0 | NetworkX/código puro
  Input: INTs seleccionadas + orden
  Output: prompt compilado (red de preguntas)
  Álgebra ensambla red: fusión, composición, etc.
  13 reglas como restricciones duras
  Dependencias lentes/funciones informan secuencia

PASO 4 — EJECUTOR                      30-120s | $0.001-0.003/modelo OS
  Input: prompt compilado
  Output: respuestas por modelo×inteligencia
  1 modelo (Tier 2), 3-5 (Tier 3), 7+ (Tier 4)
  Modelo OS asignado por Gestor según celda
  Multi-modelo en paralelo si celda requiere complementariedad

PASO 5 — EVALUADOR                     ~1-3s | ~$0.01
  Input: respuestas + gaps originales
  Re-evalúa campo de gradientes POST-ejecución
  Output: scores de cierre de gap, falacias detectadas
  Si persisten gaps > 0.3: escalar (otra INT, otra profundidad)
  Max 2 re-intentos por celda
  Panel V3.2+V3.1+R1 o Cogito (no Sonnet)

PASO 6 — INTEGRADOR                    10-20s | ~$0.05
  Input: respuestas evaluadas
  Output: narrativa + JSON estructurado
  Cogito como sintetizador (#1, 3.6 conexiones/output)

PASO 7 — REGISTRADOR                   ~100ms | $0 | código puro
  Input: todo lo anterior
  Output: datapoint en datapoints_efectividad → alimenta Gestor
  Registra gap_cerrado por pregunta×modelo con coordenadas

TOTAL: ~$0.10-0.35 (OS-first) | ~40-150s
```

**AFTER:**
```
PASO 0 — PRE-SCREENING LINGÜÍSTICO      ~50ms | $0 | código puro ✅
  Input: caso en lenguaje natural
  Detecta: firma lingüística del input (patrones sintácticos)
  Output: arquetipos candidatos (hipótesis para Paso 1)
  Ej: "TODO depende de mí" → Máquina sin Alma (70%)

PASO 1 — DETECTOR DE HUECOS + TCF     ~200ms | $0 | código puro ✅
  Input: caso en lenguaje natural + arquetipos candidatos de Paso 0
  7 primitivas + 8 operaciones sintácticas + 14 leyes TCF
  Output: vector funcional 7F×3L + scoring multi-arquetipo + EstadoCampo completo
  Detecta: falacias aritméticas + violaciones de leyes TCF + coalición de lentes dominante
  Con P41 (Fase 1): además extrae evidencias semánticas del texto → campo DUAL

PASO 1.5 — GESTOR (compilar programa)  ~50ms | $0 | código puro ✅
  Input: scoring multi-arquetipo + vector funcional
  Compila: receta mixta → pasos con INTs + modelos + orden + tier
  Output: ProgramaCompilado (base para el Router)
  Si no hay scoring TCF → skip, Router opera en modo fallback

PASO 2 — ROUTER                        ~500ms-3s | ~$0.001 | reglas + modelo OS ✅
  Input: ProgramaCompilado del Gestor + campo de gradientes
  Programa como BASE (INTs + orden + modelos). LLM complementa/ajusta.
  Verifica 14 reglas compilador. Auto-corrige violaciones.
  Con P41 (Fase 1): usa gap SEMÁNTICO para refinar selección de INTs
    (ej: gap="percibe compromiso, no desperdicio" → INT-17 > INT-04 para ESTE gap)
  Si Regla 14 aplica: FRENAR antes de construir
  Tier 1-2: reglas heurísticas. Tier 3+: modelo OS ligero

PASO 3 — COMPOSITOR                    ~200ms | $0 | NetworkX/código puro ✅
  Input: INTs seleccionadas + orden
  Output: prompt compilado (red de preguntas)
  Álgebra ensambla red: fusión, composición, etc.
  14 reglas como restricciones duras
  Dependencias lentes/funciones informan secuencia

PASO 4 — EJECUTOR                      30-120s | $0.001-0.003/modelo OS ✅
  Input: prompt compilado
  Output: respuestas por modelo×inteligencia
  1 modelo (Tier 2), 3-5 (Tier 3), 7+ (Tier 4)
  Modelo OS asignado por Gestor según celda
  Multi-modelo en paralelo si celda requiere complementariedad

PASO 5 — EVALUADOR                     ~1-3s | ~$0.01 ✅
  Input: respuestas + gaps originales + TCF pre-ejecución
  Re-evalúa campo de gradientes POST-ejecución
  Output: scores de cierre de gap, falacias detectadas, mejora de campo TCF
  Si persisten gaps > 0.3: escalar (otra INT, otra profundidad)
  Max 2 re-intentos por celda
  Panel V3.2+V3.1+R1 o Cogito (no Sonnet)
  Con P41 (Fase 2): compara estado_pre vs estado_post SEMÁNTICAMENTE
    Un LLM evalúa: "¿pasó de 'percibe compromiso' a 'percibe desperdicio'?"

PASO 6 — INTEGRADOR                    10-20s | ~$0.05 ✅
  Input: respuestas evaluadas
  Output: narrativa + JSON estructurado
  Cogito como sintetizador (#1, 3.6 conexiones/output)

PASO 7 — REGISTRADOR                   ~100ms | $0 | código puro ✅
  Input: todo lo anterior
  Output: datapoint en datapoints_efectividad → alimenta Gestor
  Registra gap_cerrado por pregunta×modelo con coordenadas
  Con P41 (Fase 2): registra también gap_semantico_pre, gap_semantico_post

TOTAL: ~$0.10-0.35 (OS-first) | ~40-150s
```

---

## EDIT 3 — §5.4: Actualizar tabla de estado de implementación

**BEFORE:**
```
| Componente | Estado |
|------------|--------|
| Motor Semántico v1 MVP en fly.io | ✅ 3 casos validados, 8.5-9.5/10 |
| Detector de huecos | 🔧 Diseñado |
| Router | ✅ Parcial (Sonnet fallback) |
| Compositor | ✅ NetworkX + 13 reglas |
| Ejecutor multi-modelo | ✅ 6+ modelos OS paralelo |
| Evaluador consenso | ✅ Panel > Sonnet individual (Exp 4) |
| Integrador Cogito | ✅ #1 sin discusión (Exp 4.2) |
| Registrador | 🔧 Schema diseñado |
```

**AFTER:**
```
| Componente | Estado |
|------------|--------|
| Motor Semántico v1 MVP en fly.io | ✅ 3 casos validados, 8.5-9.5/10 |
| TCF completa (6 archivos, ~1000 líneas) | ✅ 14 leyes, 12 arquetipos, 11 recetas, firmas lingüísticas. 87+ tests |
| Detector de huecos + TCF integrada | ✅ Firmas → scoring multi-arquetipo → EstadoCampo |
| Gestor v0 (compilador de programas) | ✅ compilar_programa() por scoring de arquetipo. 92 tests |
| Router con ProgramaCompilado | ✅ Recibe programa del Gestor como base. Verifica 14 reglas. |
| Compositor | ✅ NetworkX + 14 reglas |
| Ejecutor multi-modelo | ✅ 6+ modelos OS paralelo |
| Evaluador consenso + TCF | ✅ Panel > Sonnet individual (Exp 4). Mide mejora de campo. |
| Integrador Cogito | ✅ #1 sin discusión (Exp 4.2) |
| Registrador (Capa 7) | ✅ Persiste datapoints_efectividad por INT×modelo×celda |
| Gradientes duales (P41) | 🔧 Doc de diseño listo. Código: Fase 0 pendiente |
```

---

## EDIT 4 — §6.1: Actualizar estado del Gestor

**BEFORE:**
```
**Estado: DISEÑADO, POR IMPLEMENTAR. Cuello de botella principal. Prioridad #1 del roadmap.**
```

**AFTER:**
```
**Estado: v0 IMPLEMENTADO (19-Mar-2026).** Compilador funcional: scoring → receta mixta → ProgramaCompilado con INTs + modelos + tier. Integrado en pipeline entre Detector y Router. 92 tests, 0 failures.

**Pendiente del Gestor:** loop lento (recompilación periódica), Fase A/B (exploración→lookup), selección natural de preguntas, complementariedad modelo×modelo, transferencia cross-dominio, compilación por semántica de gap (P41 Fase 3).
```

---

## EDIT 5a — §6.6: Añadir columna semántica a campo_gradientes

**BEFORE:**
```
CREATE TABLE campo_gradientes (
    ejecucion_id TEXT PRIMARY KEY,
    input_texto TEXT,
    gradientes JSONB NOT NULL,         -- {celda: {actual, objetivo, gap}}
    dependencias_lentes JSONB,
    dependencias_funciones JSONB,
    top_gaps JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**AFTER:**
```
CREATE TABLE campo_gradientes (
    ejecucion_id TEXT PRIMARY KEY,
    input_texto TEXT,
    gradientes JSONB NOT NULL,         -- {celda: {actual, objetivo, gap}}
    semantica JSONB,                   -- P41: {Fi: {estado, objetivo, gap_semantico, evidencias[]}}
    dependencias_lentes JSONB,
    dependencias_funciones JSONB,
    top_gaps JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## EDIT 5b — §6.6: Añadir columna semántica a perfil_gradientes

**BEFORE:**
```
CREATE TABLE perfil_gradientes (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,           -- "exocortex:pilates"
    usuario_id TEXT,                    -- si múltiples usuarios por exocortex
    gradientes JSONB NOT NULL,          -- {celda: {actual, objetivo, gap, n_ejecuciones}}
    version INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**AFTER:**
```
CREATE TABLE perfil_gradientes (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,           -- "exocortex:pilates"
    usuario_id TEXT,                    -- si múltiples usuarios por exocortex
    gradientes JSONB NOT NULL,          -- {celda: {actual, objetivo, gap, n_ejecuciones}}
    semantica JSONB,                   -- P41: capa semántica acumulada por consumidor
    version INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## EDIT 5c — §6.6: Añadir columnas semánticas a datapoints_efectividad

**BEFORE:**
```
CREATE TABLE datapoints_efectividad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pregunta_id TEXT NOT NULL,
    modelo TEXT NOT NULL,
    caso_id TEXT NOT NULL,
    consumidor TEXT NOT NULL,
    celda_objetivo TEXT NOT NULL,
    gap_pre FLOAT NOT NULL,
    gap_post FLOAT NOT NULL,
    gap_cerrado FLOAT GENERATED ALWAYS AS (gap_pre - gap_post) STORED,
    tasa_cierre FLOAT GENERATED ALWAYS AS (
        CASE WHEN gap_pre > 0 THEN (gap_pre - gap_post) / gap_pre ELSE 0 END
    ) STORED,
    operacion TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

**AFTER:**
```
CREATE TABLE datapoints_efectividad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pregunta_id TEXT NOT NULL,
    modelo TEXT NOT NULL,
    caso_id TEXT NOT NULL,
    consumidor TEXT NOT NULL,
    celda_objetivo TEXT NOT NULL,
    gap_pre FLOAT NOT NULL,
    gap_post FLOAT NOT NULL,
    gap_cerrado FLOAT GENERATED ALWAYS AS (gap_pre - gap_post) STORED,
    tasa_cierre FLOAT GENERATED ALWAYS AS (
        CASE WHEN gap_pre > 0 THEN (gap_pre - gap_post) / gap_pre ELSE 0 END
    ) STORED,
    operacion TEXT,
    gap_semantico_pre TEXT,             -- P41: descripción semántica del gap antes
    gap_semantico_post TEXT,            -- P41: descripción semántica del gap después
    gap_semantico_cerrado BOOLEAN,      -- P41: ¿el evaluador semántico considera cerrado?
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

---

## EDIT 6 — §10: Reemplazar secciones Motor vN y Gestor del checklist

**BEFORE:**
```
### Motor vN 🔧 EN CURSO
- [x] MVP desplegado en fly.io
- [x] 3 casos validados (8.5-9.5/10)
- [ ] Detector de huecos funcional
- [ ] Campo de gradientes sobre input
- [ ] Router por gradiente (modelo OS)
- [ ] Red de preguntas como prompt del agente
- [ ] Verificación de cierre de gaps
- [ ] Telemetría en DB

### Gestor ⬜ POR IMPLEMENTAR (PRIORIDAD #1)
- [x] Arquitectura diseñada
- [x] 3 mecanismos de aprendizaje definidos
- [x] Pipeline del Gestor definido (7 pasos)
- [x] Schema BD completo: 23 tablas + 1 vista materializada (§6.6)
- [x] Programas compilados diseñados (caché Fase A→B)
- [x] Perfil gradientes por consumidor diseñado
- [x] Log de auditoría del Gestor diseñado
- [ ] Crear schema en fly.io Postgres (migrations)
- [ ] Seed desde JSONs cartografía + Exp 4
- [ ] Compilador de programas funcional
```

**AFTER:**
```
### Motor vN ✅ OPERATIVO (19-Mar-2026)
- [x] MVP desplegado en fly.io
- [x] 3 casos validados (8.5-9.5/10)
- [x] TCF completa: 14 leyes, 12 arquetipos, 11 recetas, firmas lingüísticas (87+ tests)
- [x] Detector de huecos funcional + TCF integrada
- [x] Campo de gradientes numérico sobre input
- [x] Router por gradiente + ProgramaCompilado del Gestor
- [x] 14 reglas compilador como funciones verificables
- [x] Registrador (Capa 7) — persiste datapoints_efectividad
- [ ] Campo de gradientes DUAL (P41 — Fase 0-1)
- [ ] Verificación de cierre semántica (P41 — Fase 2)
- [ ] Red de preguntas como prompt del agente (usa definiciones estáticas aún)
- [ ] Telemetría en DB (persiste en logs, no en tablas Postgres aún)

### Gestor ✅ v0 IMPLEMENTADO (19-Mar-2026)
- [x] Arquitectura diseñada
- [x] 3 mecanismos de aprendizaje definidos
- [x] Pipeline del Gestor definido (10 pasos)
- [x] Schema BD completo: 23 tablas + 1 vista materializada (§6.6)
- [x] Compilador de programas funcional (compilar_programa)
- [x] Modelo→celda asignado (datos Exp 1+4)
- [x] Tier decidido por modo/presupuesto
- [x] Integrado en pipeline entre Detector y Router
- [ ] Loop lento (recompilación periódica por datos de efectividad)
- [ ] Fase A→B (exploración→lookup con programas_compilados en DB)
- [ ] Selección natural de preguntas (poda+promoción)
- [ ] Complementariedad modelo×modelo
- [ ] Transferencia cross-dominio
- [ ] Compilación por semántica de gap (P41 Fase 3)
- [ ] Crear schema en fly.io Postgres (migrations)
- [ ] Seed desde JSONs cartografía + Exp 4

### Gradientes Duales (P41) 🔧 DISEÑADO
- [x] Documento de diseño completo (docs/L0/GRADIENTES_DUALES.md)
- [x] CeldaCampo, VectorFuncionalDual, EstadoCampoDual diseñados
- [x] Plan de implementación 5 fases definido
- [ ] Fase 0: Crear CeldaCampo + VectorFuncionalDual (aditivo, sin romper nada)
- [ ] Fase 1: Detector extrae evidencias semánticas del texto
- [ ] Fase 2: Evaluador compara pre/post semánticamente
- [ ] Fase 3: Gestor aprende por contexto semántico del gap
- [ ] Fase 4: Exocortex habla semántica (dashboard con significados)
```

---

## EDIT 7 — §12: Añadir P41 después de P38

**BEFORE:**
```
38. **(=P40, CR0) La degradación es inversa a la construcción.** Se construye Salud→Sentido→Continuidad. Se pierde Continuidad→Sentido→Salud. Lo que se construye último se pierde primero.

---

## §13. HORIZONTE (sin fechas, sin plan)
```

**AFTER:**
```
38. **(=P40, CR0) La degradación es inversa a la construcción.** Se construye Salud→Sentido→Continuidad. Se pierde Continuidad→Sentido→Salud. Lo que se construye último se pierde primero.
39. **(=P41, CR0) Los gradientes son duales: número para calcular, significado para diagnosticar.** El número NUNCA contradice la semántica. La semántica es la fuente de verdad. El número es un resumen derivado. Ambos coexisten — el número sin semántica es válido (Tier 1-2), la semántica sin número es válido (pre-análisis), pero el sistema COMPLETO tiene ambos. Las intervenciones concretas solo se derivan de la capa semántica.

---

## §13. HORIZONTE (sin fechas, sin plan)
```

---

## EDIT 8 — §14: Añadir GRADIENTES_DUALES.md a tabla de documentos

**BEFORE:**
```
| VALIDACION_TCF_CASO_PILATES.md | Primera validación empírica TCF, N=1 | Datos |
| L0_5_MECANISMO_UNIVERSAL_VINCULACION.md | Mecanismo universal de mapas | L0 |
```

**AFTER:**
```
| VALIDACION_TCF_CASO_PILATES.md | Primera validación empírica TCF, N=1 | Datos |
| GRADIENTES_DUALES.md | Extensión TCF: representación dual numérica+semántica del campo | L0 (CR0) |
| L0_5_MECANISMO_UNIVERSAL_VINCULACION.md | Mecanismo universal de mapas | L0 |
```

---

## EDIT 9 — Footer: Actualizar con cambios aplicados

**BEFORE:**
```
**FIN DOCUMENTO MAESTRO v3 — CR0 — Actualizado 19-Mar-2026 con TCF + Juegos de Lentes + P36 (CR1) + Regla 14 (CR1)**
```

**AFTER:**
```
**FIN DOCUMENTO MAESTRO v3 — CR0 — Actualizado 19-Mar-2026 con TCF + Juegos de Lentes + P36 (CR1) + Regla 14 (CR1) + TCF implementada (✅) + Gestor v0 implementado (✅) + P41 Gradientes Duales (CR0)**
```

---

## CRITERIOS PASS/FAIL

**PASS si:**
1. Los 9 edits (EDIT 1 a EDIT 9) se aplicaron correctamente
2. El archivo tiene ~2380-2420 líneas (era 2318, se añaden ~80-100 líneas)
3. `grep -c "P41" docs/maestro/MAESTRO_V3.md` devuelve ≥ 5
4. `grep -c "✅" docs/maestro/MAESTRO_V3.md` es mayor que antes (era ~50, ahora ~65+)
5. `grep "GRADIENTES_DUALES" docs/maestro/MAESTRO_V3.md` aparece al menos 2 veces (§2.8 y §14)
6. `grep "Gestor v0" docs/maestro/MAESTRO_V3.md` aparece al menos 1 vez
7. `grep "PASO 1.5" docs/maestro/MAESTRO_V3.md` aparece exactamente 1 vez
8. No se perdió ninguna sección del Maestro (verificar que §0 a §14 siguen presentes)

**FAIL si:**
- Se reescribió el archivo completo en vez de hacer edits quirúrgicos
- Algún BEFORE no matcheó (reportar cuál y por qué)
- Se modificó texto fuera de los bloques BEFORE/AFTER

---

**FIN BRIEFING**
