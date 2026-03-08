# BRIEFING_03 — PIPELINE CAPAS 4-6 (EJECUCIÓN) + ORQUESTADOR

**Objetivo:** Ejecutor (LLM calls), Evaluador (scorer heurístico + detección falacias), Integrador (síntesis), Orquestador (pipeline completo 7 capas).
**Pre-requisito:** BRIEFING_00, 01, 02 completados.
**Output:** Pipeline end-to-end funcional. POST /motor/ejecutar produce output real.

---

## CAPA 4: EJECUTOR (src/pipeline/ejecutor.py)

### Qué hace
Recibe los prompts del generador y los ejecuta contra Anthropic API, respetando dependencias entre operaciones.

### Lógica

1. Identifica qué prompts pueden ejecutarse en paralelo (sin dependencias)
2. Ejecuta en paralelo los independientes (asyncio.gather)
3. Cuando un prompt completa, inyecta su output en los dependientes
4. Para composiciones: ejecuta A, luego genera prompt B con output de A, luego ejecuta B
5. Para fusiones: espera outputs de A y B, luego genera prompt de fusión, luego ejecuta
6. Para loops: espera output de pasada 1, genera prompt loop, ejecuta pasada 2
7. Tracking de coste y tiempo por operación

### Modelo de datos

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ExecutionResult:
    intel_id: str
    operacion_tipo: str  # 'individual', 'composicion', 'fusion', 'loop'
    output_raw: str  # texto completo del LLM
    output_json: dict | None  # JSON parseado si disponible
    modelo_usado: str
    input_tokens: int
    output_tokens: int
    coste_usd: float
    tiempo_s: float
    pasada: int = 1

@dataclass
class ExecutionPlan:
    results: dict[str, ExecutionResult] = field(default_factory=dict)
    total_cost: float = 0.0
    total_time: float = 0.0
    errors: list[str] = field(default_factory=list)
```

### Ejecución

```python
import asyncio
import json
import time
from src.utils.llm_client import llm
from src.pipeline.generador import PromptPlan, TEMPLATE_COMPOSICION, TEMPLATE_FUSION, TEMPLATE_LOOP

async def ejecutar_plan(prompts: list[PromptPlan], input_text: str, 
                        contexto: str | None, inteligencias_data: dict,
                        presupuesto_max: float) -> ExecutionPlan:
    """Ejecuta todos los prompts respetando dependencias y presupuesto."""
    plan = ExecutionPlan()
    outputs: dict[str, str] = {}  # intel_id → output text
    
    # Fase 1: Ejecutar independientes en paralelo
    independientes = [p for p in prompts if not p.depende_de and p.operacion.tipo != 'loop']
    
    async def ejecutar_uno(prompt_plan: PromptPlan) -> ExecutionResult:
        t0 = time.time()
        response = await llm.complete(
            model=prompt_plan.modelo,
            system="Responde en español. Sé preciso y estructurado.",
            user_message=prompt_plan.prompt_user,
            max_tokens=4096,
            temperature=0.3,
        )
        elapsed = time.time() - t0
        
        # Intentar parsear JSON del response
        parsed = try_parse_json(response)
        
        intel_id = prompt_plan.operacion.inteligencias[0]
        outputs[intel_id] = response
        
        return ExecutionResult(
            intel_id=intel_id,
            operacion_tipo=prompt_plan.operacion.tipo,
            output_raw=response,
            output_json=parsed,
            modelo_usado=prompt_plan.modelo,
            input_tokens=0,  # se actualizará desde llm client
            output_tokens=0,
            coste_usd=0,
            tiempo_s=elapsed,
            pasada=1
        )
    
    # Ejecutar independientes
    if independientes:
        results = await asyncio.gather(
            *[ejecutar_uno(p) for p in independientes],
            return_exceptions=True
        )
        for r in results:
            if isinstance(r, Exception):
                plan.errors.append(str(r))
            else:
                plan.results[r.intel_id] = r
                plan.total_cost += r.coste_usd
    
    # Check presupuesto
    if plan.total_cost >= presupuesto_max:
        plan.errors.append(f"Presupuesto agotado: ${plan.total_cost:.2f} >= ${presupuesto_max:.2f}")
        return plan
    
    # Fase 2: Ejecutar dependientes (composiciones, fusiones)
    dependientes = [p for p in prompts if p.depende_de and p.operacion.tipo != 'loop']
    for prompt_plan in sorted(dependientes, key=lambda p: p.operacion.orden):
        # Verificar que las dependencias están resueltas
        deps_ok = all(d in outputs for d in prompt_plan.depende_de)
        if not deps_ok:
            plan.errors.append(f"Dependencias no resueltas para {prompt_plan.operacion}")
            continue
        
        # Generar prompt dinámico
        if prompt_plan.template == 'composicion':
            id_a = prompt_plan.depende_de[0]
            prompt_text = format_composicion(
                prompt_plan.intel_a, prompt_plan.intel_b,
                outputs[id_a], input_text
            )
        elif prompt_plan.template == 'fusion':
            id_a, id_b = prompt_plan.depende_de
            prompt_text = format_fusion(
                prompt_plan.intel_a, prompt_plan.intel_b,
                outputs[id_a], outputs[id_b], input_text
            )
        else:
            continue
        
        t0 = time.time()
        response = await llm.complete(
            model=prompt_plan.modelo,
            system="Responde en español. Sé preciso y estructurado.",
            user_message=prompt_text,
            max_tokens=4096,
            temperature=0.3,
        )
        elapsed = time.time() - t0
        
        intel_id = prompt_plan.operacion.inteligencias[-1]  # Último de la cadena
        outputs[intel_id + '_comp'] = response
        
        plan.results[intel_id + '_' + prompt_plan.template] = ExecutionResult(
            intel_id=intel_id,
            operacion_tipo=prompt_plan.template,
            output_raw=response,
            output_json=try_parse_json(response),
            modelo_usado=prompt_plan.modelo,
            input_tokens=0,
            output_tokens=0,
            coste_usd=0,
            tiempo_s=elapsed,
        )
    
    # Fase 3: Loop tests (pasada 2)
    loops = [p for p in prompts if p.operacion.tipo == 'loop']
    for prompt_plan in loops:
        intel_id = prompt_plan.operacion.inteligencias[0]
        if intel_id not in outputs:
            continue
        
        prompt_text = format_loop(
            prompt_plan.intel_data, outputs[intel_id]
        )
        
        t0 = time.time()
        response = await llm.complete(
            model=prompt_plan.modelo,
            system="Responde en español. Solo hallazgos NUEVOS.",
            user_message=prompt_text,
            max_tokens=2048,
            temperature=0.2,
        )
        elapsed = time.time() - t0
        
        outputs[intel_id + '_loop'] = response
        plan.results[intel_id + '_loop'] = ExecutionResult(
            intel_id=intel_id,
            operacion_tipo='loop',
            output_raw=response,
            output_json=try_parse_json(response),
            modelo_usado=prompt_plan.modelo,
            input_tokens=0,
            output_tokens=0,
            coste_usd=0,
            tiempo_s=elapsed,
            pasada=2
        )
    
    plan.total_time = sum(r.tiempo_s for r in plan.results.values())
    plan.total_cost = llm.total_cost  # acumulado real
    
    return plan


def try_parse_json(text: str) -> dict | None:
    """Intenta extraer JSON de una respuesta que puede tener texto alrededor."""
    import re
    # Buscar bloques JSON
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    # Intento directo
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
```

---

## CAPA 5: EVALUADOR (src/pipeline/evaluador.py)

### Qué hace
Evalúa la calidad del output del ejecutor con un scorer heurístico. Si el score es bajo, recomienda relanzar.

### Criterios (derivados de la cartografía)

```python
def evaluar(plan: ExecutionPlan, algoritmo: Algoritmo) -> EvaluationResult:
    """Scorer heurístico. Devuelve score 0-10 y recomendaciones."""
    scores = []
    issues = []
    
    # 1. Cobertura: ¿Se ejecutaron todas las operaciones planeadas?
    planned = len(algoritmo.operaciones)
    executed = len([r for r in plan.results.values() if r.operacion_tipo != 'loop'])
    coverage = executed / max(planned, 1)
    scores.append(('cobertura', coverage * 10))
    if coverage < 0.8:
        issues.append(f"Solo {executed}/{planned} operaciones ejecutadas")
    
    # 2. JSON parseables: ¿Los outputs tienen estructura?
    total_results = len(plan.results)
    json_ok = len([r for r in plan.results.values() if r.output_json])
    structure = json_ok / max(total_results, 1)
    scores.append(('estructura', structure * 10))
    if structure < 0.5:
        issues.append("Más de 50% de outputs sin JSON parseable")
    
    # 3. Hallazgos: ¿Hay hallazgos no triviales?
    hallazgos_count = 0
    for r in plan.results.values():
        if r.output_json:
            h = r.output_json.get('hallazgos', [])
            hallazgos_count += len(h)
    hallazgos_score = min(hallazgos_count / (len(algoritmo.inteligencias) * 2), 1.0)
    scores.append(('hallazgos', hallazgos_score * 10))
    if hallazgos_count < 3:
        issues.append(f"Solo {hallazgos_count} hallazgos (mínimo esperado: {len(algoritmo.inteligencias)*2})")
    
    # 4. Emergencia: ¿Las composiciones/fusiones produjeron hallazgos emergentes?
    emergentes = 0
    for r in plan.results.values():
        if r.output_json and r.operacion_tipo in ('composicion', 'fusion'):
            if r.output_json.get('hallazgo_emergente') or r.output_json.get('emergente'):
                emergentes += 1
    comp_fus = len([o for o in algoritmo.operaciones if o.tipo in ('composicion', 'fusion')])
    emergencia = emergentes / max(comp_fus, 1) if comp_fus > 0 else 1.0
    scores.append(('emergencia', emergencia * 10))
    
    # 5. Loop quality: ¿Los loops encontraron algo nuevo?
    loops = [r for r in plan.results.values() if r.operacion_tipo == 'loop']
    if loops:
        loops_with_new = len([l for l in loops if l.output_json and 
                             l.output_json.get('hallazgos_nuevos')])
        loop_score = loops_with_new / len(loops)
        scores.append(('loops', loop_score * 10))
    
    # 6. Coste efficiency
    if plan.total_cost > 0:
        cost_per_hallazgo = plan.total_cost / max(hallazgos_count, 1)
        cost_score = max(0, 10 - cost_per_hallazgo * 20)  # Penalizar si >$0.50/hallazgo
        scores.append(('eficiencia', cost_score))
    
    # 7. [v2] Detección de falacias aritméticas en los outputs
    falacias_detectadas = detectar_falacias(plan)
    if falacias_detectadas:
        # Penalizar proporcionalmente al número de falacias
        falacia_penalty = min(len(falacias_detectadas) * 0.5, 3.0)
        scores.append(('falacias', max(0, 10 - falacia_penalty)))
    
    # Score final (media ponderada)
    weights = {
        'cobertura': 0.20,
        'estructura': 0.15,
        'hallazgos': 0.25,
        'emergencia': 0.20,
        'loops': 0.10,
        'eficiencia': 0.10,
    }
    
    total_score = sum(
        score * weights.get(name, 0.1) 
        for name, score in scores
    )
    
    # Recomendación
    should_relaunch = total_score < 6.0
    
    return EvaluationResult(
        score=round(total_score, 1),
        scores_detalle={name: round(s, 1) for name, s in scores},
        issues=issues,
        falacias=falacias_detectadas,  # [v2]
        should_relaunch=should_relaunch,
        relaunch_suggestion="Añadir inteligencia complementaria o aumentar profundidad" if should_relaunch else None
    )


def detectar_falacias(plan: ExecutionPlan) -> list[dict]:
    """[v2] Detecta falacias aritméticas en los outputs del ejecutor.
    
    Las 6 falacias del Marco Lingüístico:
    - conducta_valor: confundir hacer con ser
    - optimizacion_sin_finalidad: optimizar sin saber para qué
    - friccion_es_fallo: asumir que toda tensión es mala
    - creencia_como_regla: tratar opinión como obligación
    - cualidad_como_funcion: confundir ser con hacer
    - verbo_sin_objeto: función declarada pero no definida
    """
    falacias = []
    
    for key, result in plan.results.items():
        if not result.output_raw:
            continue
        text = result.output_raw.lower()
        
        # Heurísticas simples para MVP. Se refinan con datos reales.
        
        # conducta_valor / cualidad_como_funcion
        if 'es innovador' in text or 'es líder' in text or 'es emprendedor' in text:
            if 'innova' not in text and 'lidera' not in text:
                falacias.append({
                    'tipo': 'cualidad_como_funcion',
                    'fuente': key,
                    'fragmento': 'Atribuye cualidad sin verificar función'
                })
        
        # optimizacion_sin_finalidad
        if ('optimizar' in text or 'mejorar' in text or 'escalar' in text):
            if 'para' not in text and 'objetivo' not in text and 'fin' not in text:
                falacias.append({
                    'tipo': 'optimizacion_sin_finalidad',
                    'fuente': key,
                    'fragmento': 'Optimización sin finalidad explícita'
                })
        
        # verbo_sin_objeto
        if 'lidera' in text or 'gestiona' in text or 'dirige' in text:
            # Check if followed by object
            for verbo in ['lidera', 'gestiona', 'dirige']:
                if verbo in text:
                    idx = text.index(verbo)
                    after = text[idx+len(verbo):idx+len(verbo)+20].strip()
                    if not after or after[0] in '.!?,;':
                        falacias.append({
                            'tipo': 'verbo_sin_objeto',
                            'fuente': key,
                            'fragmento': f'"{verbo}" sin objeto definido'
                        })
    
    return falacias
```

---

## CAPA 6: INTEGRADOR (src/pipeline/integrador.py)

### Qué hace
Toma todos los outputs del ejecutor y produce la síntesis final para el usuario.

### Prompt de integración

```python
INTEGRADOR_SYSTEM = """Eres el integrador del Motor Semántico OMNI-MIND. 
Tu trabajo es sintetizar los análisis de múltiples inteligencias en un output coherente y accionable para el usuario.

REGLAS:
1. No repitas lo que cada inteligencia dijo — sintetiza.
2. Prioriza HALLAZGOS EMERGENTES (lo que solo aparece al cruzar inteligencias).
3. Identifica CONTRADICCIONES entre inteligencias — son señales, no errores.
4. La síntesis debe ser ACCIONABLE — termina con acciones concretas.
5. Identifica PUNTOS CIEGOS — lo que NINGUNA inteligencia pudo ver.
6. Máximo 800 palabras. Densidad > extensión."""

INTEGRADOR_USER = """CASO ORIGINAL:
{input}

{contexto_extra}

ANÁLISIS POR INTELIGENCIA:
{analisis_formateados}

ALGORITMO USADO:
- Inteligencias: {inteligencias}
- Operaciones: {operaciones}
- Pasadas: {loops}

Produce una síntesis final con esta estructura exacta:

1. DIAGNÓSTICO (3-5 líneas): ¿Qué pasa realmente aquí?
2. HALLAZGOS CLAVE (3-5 bullets): Lo más importante que emerge del cruce de inteligencias.
3. CONTRADICCIONES: ¿Dónde las inteligencias se contradicen? ¿Qué señala eso?
4. FIRMA COMBINADA (1-2 frases): La firma única de este análisis multi-inteligencia.
5. PUNTOS CIEGOS (2-3 bullets): Lo que este análisis NO puede ver.
6. ACCIONES (3-5, ordenadas por prioridad): Qué hacer, en qué orden, con qué coste/riesgo.

Responde TAMBIÉN con un JSON al final:
{{
  "narrativa": "la síntesis en prosa",
  "hallazgos": ["hallazgo 1", ...],
  "firma_combinada": "firma del análisis",
  "puntos_ciegos": ["punto ciego 1", ...],
  "acciones": [{{"accion": "...", "prioridad": 1, "coste": "...", "riesgo": "..."}}],
  "contradicciones": ["contradicción 1", ...]
}}"""

async def integrar(plan: ExecutionPlan, input_text: str, 
                   contexto: str | None, algoritmo: Algoritmo) -> dict:
    """Síntesis final con Sonnet."""
    # Formatear outputs
    analisis = []
    for key, result in plan.results.items():
        analisis.append(f"### {result.intel_id} ({result.operacion_tipo}, pasada {result.pasada})\n{result.output_raw[:2000]}")
    
    prompt = INTEGRADOR_USER.format(
        input=input_text,
        contexto_extra=f"CONTEXTO: {contexto}" if contexto else "",
        analisis_formateados="\n\n".join(analisis),
        inteligencias=", ".join(algoritmo.inteligencias),
        operaciones=", ".join(str(o) for o in algoritmo.operaciones),
        loops=str(algoritmo.loops),
    )
    
    response = await llm.complete(
        model=MODEL_INTEGRATOR,
        system=INTEGRADOR_SYSTEM,
        user_message=prompt,
        max_tokens=4096,
        temperature=0.3,
    )
    
    parsed = try_parse_json(response)
    
    return {
        "narrativa": parsed.get("narrativa", response) if parsed else response,
        "hallazgos": parsed.get("hallazgos", []) if parsed else [],
        "firma_combinada": parsed.get("firma_combinada", "") if parsed else "",
        "puntos_ciegos": parsed.get("puntos_ciegos", []) if parsed else [],
        "acciones": parsed.get("acciones", []) if parsed else [],
        "contradicciones": parsed.get("contradicciones", []) if parsed else [],
    }
```

---

## ORQUESTADOR (src/pipeline/orchestrator.py)

### Qué hace
Conecta las 7 capas en secuencia. Es el entry point del pipeline.

```python
import time
import structlog
import json
from src.pipeline.detector_huecos import detect
from src.pipeline.router import route
from src.pipeline.compositor import compose
from src.pipeline.generador import generar_prompts, load_inteligencias
from src.pipeline.ejecutor import ejecutar_plan
from src.pipeline.evaluador import evaluar
from src.pipeline.integrador import integrar
from src.db.client import log_ejecucion
from src.utils.llm_client import llm

log = structlog.get_logger()

# Cache de inteligencias en memoria
_inteligencias_data: dict | None = None

async def get_inteligencias():
    global _inteligencias_data
    if _inteligencias_data is None:
        _inteligencias_data = load_inteligencias()
    return _inteligencias_data


async def run_pipeline(request) -> dict:
    """Pipeline completo: Detector → Router → Compositor → Generador → Ejecutor → Evaluador → Integrador."""
    t0 = time.time()
    llm.reset_cost()
    
    config = request.config
    inteligencias_data = await get_inteligencias()
    
    # CAPA 0: Detector de Huecos (código puro, $0)
    log.info("pipeline_detector_start")
    huecos = await detect(request.input)
    log.info("pipeline_detector_done", huecos=len(huecos.huecos), 
             sugeridas=huecos.inteligencias_sugeridas)
    
    # CAPA 1: Router
    log.info("pipeline_router_start", modo=config.modo)
    router_result = await route(
        input_text=request.input,
        contexto=request.contexto,
        modo=config.modo,
        forzadas=config.inteligencias_forzadas,
        excluidas=config.inteligencias_excluidas,
        huecos=huecos,
    )
    log.info("pipeline_router_done", inteligencias=router_result.inteligencias)
    
    # CAPA 2: Compositor
    log.info("pipeline_compositor_start")
    algoritmo = await compose(router_result.inteligencias, config.modo)
    log.info("pipeline_compositor_done", operaciones=len(algoritmo.operaciones))
    
    # CAPA 3: Generador
    log.info("pipeline_generador_start")
    prompts = generar_prompts(algoritmo, request.input, request.contexto, inteligencias_data)
    log.info("pipeline_generador_done", prompts=len(prompts))
    
    # CAPA 4: Ejecutor
    log.info("pipeline_ejecutor_start")
    execution = await ejecutar_plan(
        prompts, request.input, request.contexto, 
        inteligencias_data, config.presupuesto_max
    )
    log.info("pipeline_ejecutor_done", 
             results=len(execution.results), 
             cost=execution.total_cost,
             errors=len(execution.errors))
    
    # CAPA 5: Evaluador (incluye detección de falacias v2)
    log.info("pipeline_evaluador_start")
    evaluation = evaluar(execution, algoritmo)
    log.info("pipeline_evaluador_done", score=evaluation.score)
    
    # Re-launch si score bajo (una sola vez)
    if evaluation.should_relaunch and execution.total_cost < config.presupuesto_max * 0.7:
        log.info("pipeline_relaunch", score=evaluation.score)
        # Añadir 1 inteligencia complementaria y re-ejecutar
        # TODO: implementar relaunch inteligente
    
    # CAPA 6: Integrador
    log.info("pipeline_integrador_start")
    resultado = await integrar(execution, request.input, request.contexto, algoritmo)
    log.info("pipeline_integrador_done")
    
    total_time = time.time() - t0
    total_cost = llm.total_cost
    
    # Telemetría
    huecos_json = json.dumps({
        "huecos": [{"tipo": h.tipo, "operacion": h.operacion, "capa": h.capa} for h in huecos.huecos],
        "perfil_acoples": huecos.perfil_acoples,
        "diagnostico": huecos.diagnostico_acople,
    })
    falacias_json = json.dumps(evaluation.falacias) if hasattr(evaluation, 'falacias') and evaluation.falacias else None
    
    response = {
        "algoritmo_usado": {
            "inteligencias": algoritmo.inteligencias,
            "operaciones": [
                {"tipo": o.tipo, "inteligencias": o.inteligencias, 
                 "direccion": o.direccion, "pasadas": o.pasadas}
                for o in algoritmo.operaciones
            ],
            "loops": algoritmo.loops,
            "huecos_detectados": len(huecos.huecos),
        },
        "resultado": resultado,
        "meta": {
            "coste": round(total_cost, 4),
            "tiempo_s": round(total_time, 1),
            "score_calidad": evaluation.score,
            "inteligencias_descartadas": router_result.descartadas,
            "evaluacion_detalle": evaluation.scores_detalle,
            "falacias": evaluation.falacias if hasattr(evaluation, 'falacias') else [],
            "diagnostico_acople": huecos.diagnostico_acople,
            "errors": execution.errors,
        }
    }
    
    # Log a DB (fire and forget)
    try:
        await log_ejecucion({
            'input': request.input,
            'contexto': request.contexto,
            'modo': config.modo,
            'huecos_detectados': huecos_json,
            'algoritmo_usado': json.dumps(response['algoritmo_usado']),
            'resultado': json.dumps(response['resultado']),
            'coste_usd': total_cost,
            'tiempo_s': total_time,
            'score_calidad': evaluation.score,
            'falacias_detectadas': falacias_json,
        })
    except Exception as e:
        log.error("telemetry_error", error=str(e))
    
    return response
```

---

## VERIFICACIÓN

1. Test E2E con mock LLM: el pipeline completo debe ejecutarse sin error y devolver la estructura correcta
2. Test E2E real (con API key): `curl -X POST localhost:8080/motor/ejecutar -H "Content-Type: application/json" -d '{"input": "Tengo una clínica dental con 3 sillones, solo uso 2, y estoy pensando en abrir una segunda sede"}'`
3. El response debe tener: algoritmo_usado (con inteligencias y operaciones), resultado (con narrativa, hallazgos, firma), meta (con coste, tiempo, score)
4. Coste < $1.50, tiempo < 150s en modo análisis
