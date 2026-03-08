"""Orquesta las 7 capas del pipeline."""
import time
import json
import structlog

from src.pipeline.detector_huecos import detect
from src.pipeline.router import route
from src.pipeline.compositor import compose
from src.pipeline.generador import generar_prompts
from src.pipeline.ejecutor import ejecutar_plan
from src.pipeline.evaluador import evaluar
from src.pipeline.integrador import integrar
from src.meta_red import load_inteligencias
from src.utils.llm_client import llm

log = structlog.get_logger()

# Cache en memoria
_inteligencias_data: dict | None = None
_aristas_data: list[dict] | None = None


async def get_inteligencias() -> dict:
    global _inteligencias_data
    if _inteligencias_data is None:
        _inteligencias_data = load_inteligencias()
    return _inteligencias_data


async def get_aristas() -> list[dict]:
    """Carga aristas desde DB o fallback en memoria."""
    global _aristas_data
    if _aristas_data is not None:
        return _aristas_data
    try:
        from src.db.client import fetch_aristas
        _aristas_data = await fetch_aristas()
    except Exception:
        log.warning("aristas_db_fallback", msg="DB no disponible, usando aristas en memoria")
        _aristas_data = _aristas_seed()
    return _aristas_data


def _aristas_seed() -> list[dict]:
    """Aristas hardcoded del seed.sql como fallback."""
    return [
        {'origen':'INT-01','destino':'INT-08','tipo':'diferencial','peso':0.95,'direccion_optima':'INT-01→INT-08','hallazgo_emergente':'Coste financiero de la ruptura emocional.'},
        {'origen':'INT-07','destino':'INT-17','tipo':'diferencial','peso':0.93,'direccion_optima':'INT-07→INT-17','hallazgo_emergente':'Precio de la autenticidad cuantificado.'},
        {'origen':'INT-02','destino':'INT-15','tipo':'diferencial','peso':0.90,'direccion_optima':'INT-02→INT-15','hallazgo_emergente':'Dato trivializador + isomorfismo.'},
        {'origen':'INT-09','destino':'INT-16','tipo':'diferencial','peso':0.88,'direccion_optima':'INT-09→INT-16','hallazgo_emergente':'Marcos lingüísticos + prototipo construible.'},
        {'origen':'INT-04','destino':'INT-14','tipo':'diferencial','peso':0.87,'direccion_optima':'INT-04→INT-14','hallazgo_emergente':'Monocultivo + 20 opciones.'},
        {'origen':'INT-06','destino':'INT-18','tipo':'diferencial','peso':0.86,'direccion_optima':'INT-06→INT-18','hallazgo_emergente':'Coaliciones + urgencia inventada.'},
        {'origen':'INT-02','destino':'INT-17','tipo':'diferencial','peso':0.88,'direccion_optima':'INT-02→INT-17','hallazgo_emergente':'Optimización como evitación existencial.'},
        {'origen':'INT-06','destino':'INT-16','tipo':'diferencial','peso':0.85,'direccion_optima':'INT-06→INT-16','hallazgo_emergente':'Gobernanza como prototipo construible.'},
        {'origen':'INT-14','destino':'INT-01','tipo':'diferencial','peso':0.86,'direccion_optima':'INT-14→INT-01','hallazgo_emergente':'Divergencia describe cambio de modelo.'},
        {'origen':'INT-03','destino':'INT-18','tipo':'diferencial','peso':0.84,'direccion_optima':'INT-03→INT-18','hallazgo_emergente':'Gap id↔ir + pausa como acto.'},
        {'origen':'INT-05','destino':'INT-09','tipo':'diferencial','peso':0.82,'direccion_optima':'INT-05→INT-09','hallazgo_emergente':'Secuencia obligatoria + metáfora-prisión.'},
        {'origen':'INT-01','destino':'INT-08','tipo':'composicion','peso':0.92,'direccion_optima':'INT-01→INT-08','hallazgo_emergente':'El análisis racional replica la defensa psicológica.'},
        {'origen':'INT-02','destino':'INT-17','tipo':'composicion','peso':0.90,'direccion_optima':'INT-02→INT-17','hallazgo_emergente':'Optimización técnica como evitación existencial.'},
        {'origen':'INT-06','destino':'INT-16','tipo':'composicion','peso':0.88,'direccion_optima':'INT-06→INT-16','hallazgo_emergente':'Gobernanza construible.'},
        {'origen':'INT-14','destino':'INT-01','tipo':'composicion','peso':0.85,'direccion_optima':'INT-14→INT-01','hallazgo_emergente':'Divergencia sin filtro revela cambio total.'},
        {'origen':'INT-01','destino':'INT-08','tipo':'fusion','peso':0.95,'direccion_optima':None,'hallazgo_emergente':'Coste financiero de la ruptura emocional: 14% runway/mes.'},
        {'origen':'INT-06','destino':'INT-16','tipo':'fusion','peso':0.88,'direccion_optima':None,'hallazgo_emergente':'Propuesta premium es zona de acuerdo política.'},
        {'origen':'INT-07','destino':'INT-17','tipo':'fusion','peso':0.93,'direccion_optima':None,'hallazgo_emergente':'Precio autenticidad = 30-50K€/año.'},
        {'origen':'INT-03','destino':'INT-18','tipo':'fusion','peso':0.84,'direccion_optima':None,'hallazgo_emergente':'Sillón vacío: optimización + recuperación existencial.'},
        {'origen':'INT-07','destino':'INT-14','tipo':'fusion','peso':0.82,'direccion_optima':None,'hallazgo_emergente':'VP da falsa certeza al marco binario.'},
        {'origen':'INT-03','destino':'INT-04','tipo':'redundancia','peso':0.35,'direccion_optima':None,'hallazgo_emergente':'Ambas ven sistema completo.'},
        {'origen':'INT-03','destino':'INT-10','tipo':'redundancia','peso':0.40,'direccion_optima':None,'hallazgo_emergente':'Ambas ven partes conectadas.'},
        {'origen':'INT-04','destino':'INT-10','tipo':'redundancia','peso':0.38,'direccion_optima':None,'hallazgo_emergente':'Sistémicas: solapan 50-75%.'},
        {'origen':'INT-08','destino':'INT-12','tipo':'redundancia','peso':0.40,'direccion_optima':None,'hallazgo_emergente':'Dimensión humana del drama.'},
        {'origen':'INT-17','destino':'INT-18','tipo':'redundancia','peso':0.35,'direccion_optima':None,'hallazgo_emergente':'Significado profundo.'},
        {'origen':'INT-09','destino':'INT-15','tipo':'redundancia','peso':0.40,'direccion_optima':None,'hallazgo_emergente':'Incongruencias de forma.'},
    ]


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
    aristas = await get_aristas()
    algoritmo = await compose(router_result.inteligencias, config.modo, aristas=aristas)
    log.info("pipeline_compositor_done", operaciones=len(algoritmo.operaciones))

    # CAPA 3: Generador
    log.info("pipeline_generador_start")
    prompts = generar_prompts(algoritmo, request.input, request.contexto, inteligencias_data)
    log.info("pipeline_generador_done", prompts=len(prompts))

    # CAPA 4: Ejecutor
    log.info("pipeline_ejecutor_start")
    execution = await ejecutar_plan(
        prompts, request.input, request.contexto,
        inteligencias_data, config.presupuesto_max,
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
    falacias_json = json.dumps(evaluation.falacias) if evaluation.falacias else None

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
            "falacias": evaluation.falacias,
            "diagnostico_acople": huecos.diagnostico_acople,
            "errors": execution.errors,
        },
    }

    # Log a DB (fire and forget)
    try:
        from src.db.client import log_ejecucion
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
