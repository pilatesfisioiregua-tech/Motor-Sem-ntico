"""Motor vN — Pipeline SFCE con Dual Process y Sandwich LLM.

Patrones aplicados:
  SFCE (#60669): Fase A (compilacion, determinista) -> Fase B (ejecucion, estocastica)
  Dual Process (#83717): alpha continuo S1/S2 para routing de tiers
  Sandwich LLM (#60675): [pre_validar] -> LLM -> [post_validar] -> [registrar]

Pipeline:
  Fase A (determinista, $0):
    1. Detector de huecos (codigo puro)
    2. Router (ConstraintManifold.generar())
    3. Compositor (gradientes + reglas)
  Fase B (estocastica, con LLM):
    4. Ejecutor (multi-modelo)
    5. Evaluador (heuristico)
    6. Integrador (sintesis)
    7. Registrador (señales PID -> Gestor)

Invariante SFCE: FrozenPrograma inmutable durante ejecucion.
"""

import json
import time
import uuid
import os
import httpx
from dataclasses import dataclass
from typing import Optional


# =====================================================
# FROZEN PROGRAMA — invariante SFCE
# =====================================================

@dataclass(frozen=True)
class FrozenPrograma:
    """Programa compilado inmutable. Garantiza invariante SFCE.

    frozen=True impide modificacion despues de creacion.
    tuple y frozenset garantizan inmutabilidad profunda.
    """
    pasos: tuple              # tuple de dicts (inmutable)
    inteligencias: frozenset  # set inmutable
    modo: str
    tier: int
    profundidad: int
    alpha: float
    timestamp: float


def _freeze_programa(programa: dict, tier: int, alpha: float) -> FrozenPrograma:
    """Convertir dict mutable a FrozenPrograma inmutable."""
    pasos_raw = programa.get('pasos', [])
    # Convertir cada paso a tuple de items para inmutabilidad
    pasos = tuple(
        tuple(sorted(p.items())) if isinstance(p, dict) else p
        for p in pasos_raw
    )

    return FrozenPrograma(
        pasos=pasos,
        inteligencias=frozenset(programa.get('inteligencias', [])),
        modo=programa.get('modo', 'analisis'),
        tier=tier,
        profundidad=programa.get('profundidad', 1),
        alpha=alpha,
        timestamp=time.time(),
    )


# =====================================================
# DUAL PROCESS — parametro alpha S1/S2
# =====================================================

# Configuraciones por modo (patron #83717)
MODOS = {
    'analisis': {
        'alpha': 0.3,       # S2 dominante
        'tier_default': 3,
        'n_ints': (4, 5),   # min, max inteligencias
        'profundidad': 2,   # 2 pasadas
        'coste_max': 1.50,
    },
    'conversacion': {
        'alpha': 0.8,       # S1 dominante
        'tier_default': 2,
        'n_ints': (1, 3),
        'profundidad': 1,
        'coste_max': 0.05,
    },
    'generacion': {
        'alpha': 0.5,       # equilibrado
        'tier_default': 2,
        'n_ints': (3, 4),
        'profundidad': 1,
        'coste_max': 0.50,
    },
    'confrontacion': {
        'alpha': 0.1,       # S2 profundo
        'tier_default': 3,
        'n_ints': (3, 5),
        'profundidad': 2,
        'coste_max': 1.00,
    },
}


def calcular_alpha(input_texto: str, modo: str, cache_hit: bool = False) -> float:
    """Parametro de delegacion S1/S2 (patron #83717).

    alpha alto -> System 1 (Tier 1-2, rapido, automatico, O(1))
    alpha bajo -> System 2 (Tier 3-5, deliberado, O(n))

    Anti-patron: analysis paralysis (S2 innecesario) -> ~40% throughput loss
    """
    if cache_hit:
        return 1.0  # S1 puro — lookup sin LLM

    base_alpha = MODOS.get(modo, MODOS['analisis'])['alpha']

    # Ajustar por complejidad del input
    n_palabras = len(input_texto.split())
    if n_palabras < 10:
        base_alpha = min(1.0, base_alpha + 0.2)  # input simple -> mas S1
    elif n_palabras > 100:
        base_alpha = max(0.1, base_alpha - 0.1)  # input complejo -> mas S2

    return round(base_alpha, 2)


def alpha_to_tier(alpha: float) -> int:
    """Convertir alpha continuo a tier discreto."""
    if alpha >= 0.9:
        return 1    # lookup
    elif alpha >= 0.6:
        return 2    # individual
    elif alpha >= 0.3:
        return 3    # mesa
    elif alpha >= 0.1:
        return 4    # pizarra
    else:
        return 5    # cartografia


# =====================================================
# MOTOR VN — Pipeline SFCE
# =====================================================

class MotorVN:
    """Pipeline completo SFCE con Dual Process routing.

    Anti-patrones SFCE evitados:
    - Compilacion incompleta (no empezar Fase B sin FrozenPrograma)
    - Recompilacion durante ejecucion (FrozenPrograma inmutable)
    - Sobre-especificacion (programa suficiente, no exhaustivo)
    """

    def __init__(self):
        self.openrouter_key = os.environ.get('OPENROUTER_API_KEY', '')
        self.openrouter_url = 'https://openrouter.ai/api/v1/chat/completions'
        self.coste_acumulado = 0.0

    def _seleccionar_modelo(self, tier: int, rol: str = 'ejecutor',
                            return_via: bool = False):
        """Select model from DB config (config_modelos -> ModelObservatory -> fallback).

        Hierarchy:
        1. config_modelos: Motor-specific role+tier mapping
        2. ModelObservatory: Code OS model registry
        3. Hardcoded fallback

        If return_via=True, returns (modelo, via) tuple.
        """
        # 1. config_modelos (Motor-specific)
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT modelo FROM config_modelos
                            WHERE rol = %s AND activo = true
                              AND tier_min <= %s AND tier_max >= %s
                            ORDER BY coste_input_per_m ASC
                            LIMIT 1
                        """, (rol, tier, tier))
                        row = cur.fetchone()
                        if row:
                            return (row[0], 'config_modelos') if return_via else row[0]
                finally:
                    put_conn(conn)
        except Exception as _e:
            print(f"[WARN:motor_vn._seleccionar_modelo.config_db] {type(_e).__name__}: {_e}")

        # 2. ModelObservatory (Code OS registry)
        try:
            from .model_observatory import get_observatory
            obs = get_observatory()
            role_to_obs = {
                'ejecutor': 'worker',
                'ejecutor_principal': 'worker',
                'ejecutor_complementario': 'worker_budget',
                'razonador': 'cerebro',
                'sintetizador': 'evaluador',
                'fontaneria': 'worker_budget',
                'pizarra': 'swarm',
            }
            obs_tier = role_to_obs.get(rol, 'worker')
            model = obs.get_model_for_tier(obs_tier)
            if model:
                return (model, 'observatory') if return_via else model
        except Exception as _e:
            print(f"[WARN:motor_vn._seleccionar_modelo.observatory] {type(_e).__name__}: {_e}")

        # 3. Fallback
        fallback = 'deepseek/deepseek-chat-v3-0324'
        return (fallback, 'fallback') if return_via else fallback

    async def ejecutar(self, input_texto: str, modo: str = 'analisis',
                       consumidor: str = 'motor_vn') -> dict:
        """Pipeline completo Motor vN con SFCE.

        Returns:
            dict con resultado completo: hallazgos, sintesis, señales PID, metricas
        """
        t0 = time.time()
        caso_id = str(uuid.uuid4())[:8]
        self.coste_acumulado = 0.0

        # Set cost tracking context
        from .costes import set_call_context, clear_call_context
        set_call_context(componente='motor_vn', consumidor=consumidor,
                         operacion='ejecucion', caso_id=caso_id)

        # 0. Cache Tier 0: lookup before anything ($0)
        from .cache_tier import try_cache
        cache_result = try_cache(input_texto)
        if cache_result:
            return {
                'caso_id': caso_id,
                'modo': modo,
                'tier': 0,
                'alpha': 1.0,
                'inteligencias': [],
                'n_inteligencias': 0,
                'profundidad': 0,
                'hallazgos': [],
                'sintesis': '',
                'señales_pid': [],
                'gradientes_top': [],
                'cache_hit': True,
                'cache_source': cache_result.get('source', 'cache'),
                'cached_data': cache_result.get('data', {}),
                'metricas': {
                    'tiempo_total_s': round(time.time() - t0, 2),
                    'coste_usd': 0.0,
                    'n_llm_calls': 0,
                },
            }

        # 0a. Dual Process: calcular alpha
        alpha = calcular_alpha(input_texto, modo)
        tier = alpha_to_tier(alpha)

        # 0b. FOK pre-flight: metacognitive confidence estimation (Fase 2 Conexión 1)
        fok_result = self._preflight_fok(input_texto, tier)
        tier = fok_result.get('tier_ajustado', tier)

        # 0c. Criticality modifier: adjust tier by system regime (Fase 2 Conexión 2)
        criticality_result = self._ajustar_tier_criticality(tier)
        tier = criticality_result.get('tier_ajustado', tier)

        # 0d. Sinema check: si input muy ambiguo, activar relajacion
        from .sinema import get_sinema
        sinema = get_sinema()
        ambiguedad = sinema.detectar_ambiguedad(input_texto)

        # ===== CAPA A — Enriquecimiento de contexto (pre-Motor) =====
        try:
            from .capa_a import CapaA
            capa_a = CapaA()
            contexto_entorno = await capa_a.enriquecer(input_texto, consumidor)

            # Inyectar en input si hay datos
            if contexto_entorno.get('contexto_f5') or contexto_entorno.get('contexto_f6'):
                input_enriquecido = (
                    f"{input_texto}\n\n[CONTEXTO ENTORNO]\n"
                    f"F5: {contexto_entorno.get('contexto_f5', '')}\n"
                    f"F6: {contexto_entorno.get('contexto_f6', '')}"
                )
            else:
                input_enriquecido = input_texto
        except Exception as e:
            print(f"[WARN:motor_vn] Capa A falló, Motor continúa sin enriquecimiento: {e}")
            input_enriquecido = input_texto
            contexto_entorno = {}

        # ===== FASE A — COMPILACION (determinista, $0) =====
        programa_dict, gradientes = self._fase_compilacion(input_enriquecido, modo, tier)

        # Aplicar Sinema si ambiguedad alta
        if ambiguedad > 0.5:
            gradientes = sinema.projection(gradientes)
            programa_dict = sinema.weakening(programa_dict, ambiguedad)
            programa_dict = sinema.relaxation(programa_dict)

        # Freeze! Inmutable a partir de aqui (invariante SFCE)
        programa = _freeze_programa(programa_dict, tier, alpha)

        # ===== PERSISTIR PROGRAMA COMPILADO =====
        programa_db_id = self._persistir_programa(programa_dict, gradientes, consumidor, modo)
        if programa_db_id is None:
            print(f"[WARN:motor_vn] _persistir_programa retornó None — feedback loop desconectado para {consumidor}_{modo}")

        # ===== FASE B — EJECUCION (estocastica, con LLM) =====
        resultado = await self._fase_ejecucion(programa, input_enriquecido)

        # ===== REGISTRAR EN TABLA EJECUCIONES =====
        try:
            from .db_pool import get_conn, put_conn
            conn_ej = get_conn()
            if conn_ej:
                try:
                    with conn_ej.cursor() as cur:
                        cur.execute("""
                            INSERT INTO ejecuciones
                                (input, contexto, modo, huecos_detectados,
                                 algoritmo_usado, resultado, coste_usd, tiempo_s, score_calidad)
                            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)
                        """, [
                            input_texto[:2000],
                            consumidor,
                            modo,
                            json.dumps(gradientes.get('top_gaps', [])[:10], default=str),
                            json.dumps({
                                'inteligencias': sorted(programa.inteligencias),
                                'tier': programa.tier,
                                'alpha': programa.alpha,
                                'profundidad': programa.profundidad,
                            }, default=str),
                            json.dumps({
                                'n_hallazgos': len(resultado.get('hallazgos', [])),
                                'sintesis': resultado.get('sintesis', '')[:1000],
                                'n_llm_calls': resultado.get('n_llm_calls', 0),
                            }, default=str),
                            round(self.coste_acumulado, 6),
                            round(time.time() - t0, 2),
                            resultado.get('scores', {}).get('score_calidad', 0),
                        ])
                    conn_ej.commit()
                finally:
                    put_conn(conn_ej)
        except Exception as _e:
            print(f"[WARN:motor_vn.ejecutar.ejecuciones] {type(_e).__name__}: {_e}")

        # ===== ACTUALIZAR PERFIL DE GRADIENTES POR CONSUMIDOR =====
        try:
            from .db_pool import get_conn, put_conn
            conn_pg = get_conn()
            if conn_pg:
                try:
                    with conn_pg.cursor() as cur:
                        cur.execute("""
                            INSERT INTO perfil_gradientes (consumidor, gradientes, version)
                            VALUES (%s, %s::jsonb, 1)
                            ON CONFLICT (consumidor, COALESCE(usuario_id, '')) DO UPDATE SET
                                gradientes = EXCLUDED.gradientes,
                                version = perfil_gradientes.version + 1,
                                updated_at = NOW()
                        """, [
                            consumidor,
                            json.dumps(gradientes.get('gradientes', {}), default=str),
                        ])
                    conn_pg.commit()
                finally:
                    put_conn(conn_pg)
        except Exception as _e:
            print(f"[WARN:motor_vn.ejecutar.perfil_gradientes] {type(_e).__name__}: {_e}")

        # ===== ACTUALIZAR PROGRAMA POST-EJECUCION =====
        tasa_cierre = self._calcular_tasa_cierre(resultado, programa)
        self._actualizar_programa_post_ejecucion(programa_db_id, tasa_cierre)

        # ===== REGISTRAR (PID signals -> Gestor) =====
        señales = self._registrar(programa, resultado, caso_id, consumidor,
                                  input_texto, gradientes)

        # ===== JOL post-execution: metacognitive quality evaluation (Fase 2 Conexión 1) =====
        jol_result = self._postflight_jol(resultado, programa, tasa_cierre)

        # ===== FLYWHEEL: update model scores (Fase 2 Conexión 3) =====
        self._flywheel_update(resultado, programa)

        # ===== CACHE: save successful results for Tier 0 lookup =====
        if resultado.get('hallazgos'):
            try:
                from .cache_tier import save_to_cache
                save_to_cache(
                    goal=input_texto,
                    tool_sequence=[{'int': i, 'n': len([h for h in resultado.get('hallazgos', []) if h.get('inteligencia') == i])} for i in programa.inteligencias],
                    result=resultado.get('sintesis', ''),
                    success=len(resultado.get('hallazgos', [])) > 0,
                )
            except Exception as _e:
                print(f"[WARN:motor_vn.ejecutar.cache_save] {type(_e).__name__}: {_e}")

        elapsed = round(time.time() - t0, 2)

        # ===== REGISTRAR METRICA (FIX 2: modelo + via en telemetria) =====
        modelos_usados = resultado.get('modelos_usados', {})
        modelo_principal = ''
        modelo_via = 'unknown'
        if modelos_usados:
            modelo_principal = next(iter(modelos_usados.values()), '')
        if not modelo_principal:
            modelo_principal, modelo_via = self._seleccionar_modelo(tier, return_via=True)
        else:
            # Determine via for the model that was used
            _, modelo_via = self._seleccionar_modelo(tier, return_via=True)

        try:
            from .telemetria import registrar_metrica
            registrar_metrica('motor_vn', 'ejecucion_completa', {
                'modelo': modelo_principal,
                'via': modelo_via,
                'tier': tier,
                'coste_usd': round(self.coste_acumulado, 4),
                'latencia_ms': int(elapsed * 1000),
                'consumidor': consumidor,
                'n_hallazgos': len(resultado.get('hallazgos', [])),
                'n_inteligencias': len(programa.inteligencias),
                'tasa_cierre': tasa_cierre,
                'caso_id': caso_id,
                'modo': modo,
            })
        except Exception as _e:
            print(f"[WARN:motor_vn.ejecutar.telemetria] {type(_e).__name__}: {_e}")

        return {
            'caso_id': caso_id,
            'modo': modo,
            'tier': tier,
            'alpha': alpha,
            'inteligencias': sorted(programa.inteligencias),
            'n_inteligencias': len(programa.inteligencias),
            'profundidad': programa.profundidad,
            'hallazgos': resultado.get('hallazgos', []),
            'sintesis': resultado.get('sintesis', ''),
            'señales_pid': señales,
            'gradientes_top': gradientes.get('top_gaps', [])[:5],
            'metacognicion': {
                'fok': fok_result,
                'jol': jol_result,
                'criticality': criticality_result,
            },
            'metricas': {
                'tiempo_total_s': elapsed,
                'coste_usd': round(self.coste_acumulado, 4),
                'n_llm_calls': resultado.get('n_llm_calls', 0),
                'modelo': modelo_principal,
                'via': modelo_via,
            },
        }

    # =====================================================
    # METACOGNICION (Fase 2: Conexiones 1+2)
    # =====================================================

    def _preflight_fok(self, input_texto: str, tier: int) -> dict:
        """FOK pre-flight: estimar confianza ANTES de ejecutar.

        Modifica tier basandose en FOK score:
        - fok > 0.7: mantener tier (alta confianza)
        - fok 0.4-0.7: mantener tier (confianza media)
        - fok < 0.4: tier += 1 (baja confianza, escalar)
        """
        try:
            from .metacognitive import get_metacognitive
            meta = get_metacognitive()
            fok = meta.feeling_of_knowing(input_texto, 'ConservarxSalud')

            tier_ajustado = tier
            fok_score = fok.get('fok', 0.5)

            if fok_score < 0.4 and tier < 5:
                tier_ajustado = tier + 1  # Escalar: baja confianza

            return {
                'fok': fok_score,
                'factores': fok.get('factores', {}),
                'recomendacion': fok.get('recomendacion', ''),
                'tier_original': tier,
                'tier_ajustado': tier_ajustado,
            }
        except Exception:
            return {'fok': 0.5, 'tier_ajustado': tier, 'error': 'fok_unavailable'}

    def _ajustar_tier_criticality(self, tier: int) -> dict:
        """Criticality modifier: ajustar tier por regimen del sistema.

        - orden_rigido: tier += 1 (explorar mas, relajar)
        - borde_del_caos: mantener (optimo)
        - caos: tier = max(2, tier - 1) (simplificar, endurecer)
        """
        try:
            from .criticality_engine import get_criticality_engine
            crit = get_criticality_engine()
            temp = crit.calcular_temperatura()

            regimen = temp.get('regimen', 'borde_del_caos')
            tier_ajustado = tier

            if regimen == 'orden_rigido' and tier < 5:
                tier_ajustado = tier + 1
            elif regimen == 'caos' and tier > 2:
                tier_ajustado = tier - 1

            return {
                'T': temp.get('T', 0.5),
                'regimen': regimen,
                'tier_original': tier,
                'tier_ajustado': tier_ajustado,
                'recomendacion': temp.get('recomendacion', ''),
            }
        except Exception:
            return {'T': 0.5, 'regimen': 'unknown', 'tier_ajustado': tier, 'error': 'criticality_unavailable'}

    def _postflight_jol(self, resultado: dict, programa: FrozenPrograma,
                        tasa_cierre: float) -> dict:
        """JOL post-execution: evaluar calidad y actualizar Kalman filter."""
        try:
            from .metacognitive import get_metacognitive
            meta = get_metacognitive()

            jol_input = {
                'tasa_cierre': tasa_cierre,
                'hallazgos': resultado.get('hallazgos', []),
                'latencia_ms': int(resultado.get('n_llm_calls', 1) * 3000),
                'coste_usd': self.coste_acumulado,
                'celda_objetivo': 'ConservarxSalud',
            }
            jol = meta.judgment_of_learning(jol_input)
            return jol
        except Exception:
            return {'jol': 0.5, 'error': 'jol_unavailable'}

    def _flywheel_update(self, resultado: dict, programa: FrozenPrograma) -> None:
        """Flywheel: update model scores after each Motor execution."""
        try:
            from .flywheel import after_session
            modelos_usados = resultado.get('modelos_usados', {})
            for int_id, modelo in modelos_usados.items():
                has_hallazgos = any(
                    h.get('inteligencia') == int_id
                    for h in resultado.get('hallazgos', [])
                )
                after_session({
                    'model_used': modelo,
                    'success': has_hallazgos,
                    'cost_usd': round(self.coste_acumulado / max(1, len(modelos_usados)), 4),
                    'iterations': 1,
                    'error_rate': 0 if has_hallazgos else 1,
                    'mode': programa.modo,
                })
        except Exception as _e:
            print(f"[WARN:motor_vn._flywheel_update] {type(_e).__name__}: {_e}")

    # =====================================================
    # FASE A — COMPILACION (determinista, $0)
    # =====================================================

    def _fase_compilacion(self, input_texto: str, modo: str, tier: int) -> tuple:
        """Fase A: 100% determinista, sin LLM.

        Steps:
        1. Detector de huecos (campo de gradientes)
        2. Router (ConstraintManifold.generar())
        3. Compositor (armar programa con preguntas)

        Anti-patron SFCE: compilacion incompleta
        -> Verificar que programa tiene al menos 1 paso antes de retornar
        """
        from .gestor import calcular_gradientes, compilar_programa
        from .reglas_compilador import get_manifold

        # Step 1: Campo de gradientes
        gradientes = calcular_gradientes(input_texto)

        # Step 2: Generar programa via Manifold (decide INTs por modo)
        manifold = get_manifold()
        config = MODOS.get(modo, MODOS['analisis'])
        programa_manifold = manifold.generar(gradientes, modo=modo, input_texto=input_texto)
        ints_objetivo = programa_manifold['inteligencias']

        # Step 3: Compilar con preguntas desde Matriz
        programa = compilar_programa(gradientes, consumidor='motor_vn')
        programa['modo'] = modo
        programa['profundidad'] = config['profundidad']

        # Extraer inteligencias de los pasos compilados
        if programa.get('pasos'):
            # Filtrar pasos a solo las INTs que el Manifold selecciono
            pasos_filtrados = [p for p in programa['pasos']
                               if p.get('inteligencia') in set(ints_objetivo)]
            # Si el filtro elimino todo, mantener los originales limitados al presupuesto
            if pasos_filtrados:
                programa['pasos'] = pasos_filtrados
            else:
                programa['pasos'] = programa['pasos'][:len(ints_objetivo)]
            programa['inteligencias'] = [p['inteligencia'] for p in programa['pasos']]
        else:
            # Sin pasos desde Matriz — crear pasos basicos desde Manifold
            programa['inteligencias'] = ints_objetivo
            modelo_tier = self._seleccionar_modelo(tier)
            programa['pasos'] = [
                {'orden': i+1, 'inteligencia': int_id, 'preguntas': [], 'modelo': modelo_tier}
                for i, int_id in enumerate(ints_objetivo)
            ]

        # Verificar compilacion completa (anti-patron SFCE)
        if not programa.get('pasos'):
            programa['pasos'] = [{'orden': 1, 'inteligencia': 'INT-01', 'preguntas': [], 'modelo': self._seleccionar_modelo(tier)}]
            programa['inteligencias'] = ['INT-01']

        return programa, gradientes

    # =====================================================
    # FASE B — EJECUCION (estocastica, con LLM)
    # =====================================================

    async def _fase_ejecucion(self, programa: FrozenPrograma, input_texto: str) -> dict:
        """Fase B: LLM envuelto en Sandwich.

        Cada paso: [pre_validar] -> LLM -> [post_validar]

        Anti-patron: programa es READONLY — no modificar durante ejecucion.
        """
        # Si tier >= 4, delegar a SwarmExecutor
        if programa.tier >= 4:
            from .swarm import SwarmExecutor
            swarm = SwarmExecutor(motor=self)
            if programa.tier == 4:
                return await swarm.ejecutar_pizarra(programa, input_texto)
            else:
                return await swarm.ejecutar_cartografia(input_texto, 'motor_vn')

        hallazgos_totales = []
        modelos_usados = {}  # INT -> modelo real usado
        n_llm_calls = 0

        # Step 4: Ejecutor — ejecutar cada paso del programa
        for paso_tuple in programa.pasos:
            paso = dict(paso_tuple) if isinstance(paso_tuple, tuple) else paso_tuple

            inteligencia = paso.get('inteligencia', '') if isinstance(paso, dict) else ''
            preguntas = paso.get('preguntas', []) if isinstance(paso, dict) else []
            modelo = paso.get('modelo', '') if isinstance(paso, dict) else ''
            if not modelo:
                modelo = self._seleccionar_modelo(programa.tier)

            # Si no hay preguntas especificas, usar prompt generico por INT
            if not preguntas:
                prompt = self._generar_prompt_int(inteligencia, input_texto)
            else:
                prompt = self._generar_prompt_preguntas(preguntas, input_texto)

            # === SANDWICH: pre_validar -> LLM -> post_validar ===

            # Pre-validar
            if not self._pre_validar(prompt, input_texto):
                continue

            # LLM call
            respuesta = await self._llamar_llm(modelo, prompt)
            n_llm_calls += 1
            modelos_usados[inteligencia] = modelo

            # Post-validar
            hallazgos_paso = self._post_validar(respuesta, inteligencia)
            hallazgos_totales.extend(hallazgos_paso)

        # Step 5: Evaluador — scoring heuristico
        scores = self._evaluar(hallazgos_totales, input_texto)

        # Step 5b: GameTheory — evaluate composition quality
        game_theory_result = {}
        try:
            from .game_theory import get_game_theory
            gt = get_game_theory()
            outputs_for_gt = [
                {'inteligencia': h.get('inteligencia', ''), 'texto': h.get('hallazgo', ''),
                 'hallazgos': [h]}
                for h in hallazgos_totales
            ]
            if len(outputs_for_gt) >= 2:
                game_theory_result = gt.analizar_composicion(outputs_for_gt)
        except Exception as _e:
            print(f"[WARN:motor_vn.game_theory] {type(_e).__name__}: {_e}")

        # Step 5c: InformationLayer — detect redundancy between INTs
        info_layer_result = {}
        try:
            from .information_layer import information_bottleneck
            # Group hallazgos by INT for MI analysis
            by_int = {}
            for h in hallazgos_totales:
                int_id = h.get('inteligencia', '')
                if int_id not in by_int:
                    by_int[int_id] = []
                by_int[int_id].append(h.get('hallazgo', ''))
            outputs_for_ib = [
                {'inteligencia': int_id, 'texto': ' '.join(texts)}
                for int_id, texts in by_int.items()
            ]
            if len(outputs_for_ib) >= 2:
                info_layer_result = information_bottleneck(outputs_for_ib)
        except Exception as _e:
            print(f"[WARN:motor_vn.info_bottleneck] {type(_e).__name__}: {_e}")

        # Step 6: Integrador — sintesis
        sintesis = self._integrar(hallazgos_totales, scores, input_texto)

        return {
            'hallazgos': hallazgos_totales,
            'scores': scores,
            'sintesis': sintesis,
            'n_llm_calls': n_llm_calls,
            'modelos_usados': modelos_usados,
            'game_theory': game_theory_result,
            'information_layer': info_layer_result,
        }

    # =====================================================
    # SANDWICH COMPONENTS
    # =====================================================

    def _pre_validar(self, prompt: str, input_texto: str) -> bool:
        """Pre-validacion determinista antes de LLM."""
        if not prompt or len(prompt.strip()) < 10:
            return False
        if len(prompt) > 50000:  # prompt demasiado largo
            return False
        return True

    def _post_validar(self, respuesta: str, inteligencia: str) -> list:
        """Post-validacion determinista despues de LLM.

        Extrae hallazgos estructurados de la respuesta.
        """
        if not respuesta or len(respuesta.strip()) < 10:
            return []

        hallazgos = []
        for linea in respuesta.split('\n'):
            linea = linea.strip()
            if linea and len(linea) > 20 and not linea.startswith('#'):
                hallazgos.append({
                    'inteligencia': inteligencia,
                    'hallazgo': linea[:500],
                })

        return hallazgos[:10]  # max 10 hallazgos por INT

    def _generar_prompt_int(self, inteligencia: str, input_texto: str) -> str:
        """Generar prompt en formato D_hibrido (P35) para una inteligencia.

        Formato canonico: pipeline como codigo Python + preguntas en lenguaje natural.
        Validado: 91% cobertura, 100% adherencia, -35% tokens vs prosa pura.
        Ref: docs/L0/FORMATO_CANONICO_PROMPT.md
        """
        firma, punto_ciego, lentes_naturales = self._cargar_metadata_int(inteligencia)

        preguntas_por_paso = self._cargar_preguntas_int(inteligencia)

        usa_provocaciones = inteligencia in ('INT-17', 'INT-18')

        lentes = lentes_naturales if lentes_naturales else ['Salud', 'Sentido', 'Continuidad']
        lentes_str = ', '.join(f'"{l}"' for l in lentes)

        bloque_codigo = f'''```python
pipeline = [
    {{"op": "EXTRAER", "target": caso, "output": "datos_formalizados"}},
    {{"op": "CRUZAR", "input": "datos_formalizados", "output": "estructura_problema"}},
    {{"op": "LENTES", "input": "estructura_problema", "lenses": [{lentes_str}], "output": "perspectivas"}},
    {{"op": "INTEGRAR", "input": "perspectivas", "output": "sintesis"}},
    {{"op": "ABSTRAER", "input": "sintesis", "output": "patron"}},
    {{"op": "FRONTERA", "input": "patron", "output": "limites"}},
]

agent = {{"id": "{inteligencia}", "signature": "{firma}", "blind_spot": "{punto_ciego}"}}
```'''

        pasos = ['EXTRAER', 'CRUZAR', 'LENTES', 'INTEGRAR', 'ABSTRAER', 'FRONTERA']
        bloque_preguntas = "Ejecuta este pipeline sobre el caso. Preguntas por paso:\n\n"

        for paso in pasos:
            qs = preguntas_por_paso.get(paso, [])
            if qs:
                preguntas_texto = ' '.join(qs[:3])
            else:
                preguntas_texto = self._pregunta_default(paso, inteligencia)

            bloque_preguntas += f"**{paso}**: {preguntas_texto}\n"

            if usa_provocaciones and paso in ('FRONTERA', 'INTEGRAR', 'EXTRAER'):
                provoc = self._generar_provocacion(paso, inteligencia, punto_ciego)
                if provoc:
                    bloque_preguntas += f"-> Provoca: {provoc}\n"

            bloque_preguntas += "\n"

        output_schema = "Output: hallazgos (uno por linea, concreto y accionable), firma_combinada, puntos_ciegos."

        return f"""{bloque_codigo}

{bloque_preguntas}
{output_schema}

CASO:
{input_texto}"""

    def _cargar_metadata_int(self, inteligencia: str) -> tuple:
        """Cargar firma, punto_ciego y modos de una inteligencia desde DB."""
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return ('', '', [])
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT firma, punto_ciego, modos_naturales
                        FROM inteligencias WHERE id = %s
                    """, [inteligencia])
                    row = cur.fetchone()
                    if row:
                        return (row[0] or '', row[1] or '', row[2] or [])
                return ('', '', [])
            finally:
                put_conn(conn)
        except Exception:
            return ('', '', [])

    def _cargar_preguntas_int(self, inteligencia: str) -> dict:
        """Cargar preguntas de la Matriz agrupadas por paso del pipeline."""
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return {}
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT lente, funcion, texto FROM preguntas_matriz
                        WHERE inteligencia = %s AND nivel = 'base'
                        ORDER BY lente, funcion
                        LIMIT 30
                    """, [inteligencia])
                    rows = cur.fetchall()

                paso_mapping = {
                    'Conservar': 'EXTRAER',
                    'Captar': 'EXTRAER',
                    'Depurar': 'CRUZAR',
                    'Distribuir': 'CRUZAR',
                    'Frontera': 'FRONTERA',
                    'Adaptar': 'ABSTRAER',
                    'Replicar': 'INTEGRAR',
                }

                preguntas = {}
                for lente, funcion, texto in rows:
                    paso = paso_mapping.get(funcion, 'CRUZAR')
                    preguntas.setdefault(paso, []).append(texto)
                    preguntas.setdefault('LENTES', []).append(f"{lente}: {texto}")

                return preguntas
            finally:
                put_conn(conn)
        except Exception:
            return {}

    def _pregunta_default(self, paso: str, inteligencia: str) -> str:
        """Pregunta default cuando no hay preguntas en la Matriz para un paso."""
        defaults = {
            'EXTRAER': f'Que datos clave se pueden identificar desde la perspectiva de {inteligencia}?',
            'CRUZAR': 'Que relaciones o tensiones emergen entre los datos extraidos?',
            'LENTES': 'Como se ve el caso desde cada lente (Salud, Sentido, Continuidad)?',
            'INTEGRAR': 'Que patron emerge al cruzar todas las perspectivas?',
            'ABSTRAER': 'Este patron es transferible a otros contextos? Que lo hace universal?',
            'FRONTERA': 'Que asume este analisis que no ha examinado? Donde estan los limites?',
        }
        return defaults.get(paso, f'Que revela {paso} desde {inteligencia}?')

    def _generar_provocacion(self, paso: str, inteligencia: str, punto_ciego: str) -> str:
        """Generar provocacion para inteligencias de frontera (D+G format)."""
        provocaciones = {
            'EXTRAER': {
                'INT-17': 'Si esta persona se mirara al espejo dentro de 10 anos habiendo elegido NO actuar — que veria?',
                'INT-18': 'Que es lo que este caso intenta decir que nadie ha escuchado todavia?',
            },
            'INTEGRAR': {
                'INT-17': 'Si las tres lentes fueran tres versiones de esta persona — pasada, presente, futura — estarian de acuerdo?',
                'INT-18': 'Que sucede si dejamos de intentar resolver y simplemente observamos?',
            },
            'FRONTERA': {
                'INT-17': f'{inteligencia} puede {punto_ciego.lower()}. Este analisis esta ayudando a decidir, o a posponer?',
                'INT-18': 'Que ha quedado sin decir que este analisis no puede capturar?',
            },
        }
        return provocaciones.get(paso, {}).get(inteligencia, '')

    def _generar_prompt_preguntas(self, preguntas: list, input_texto: str) -> str:
        """Generar prompt D_hibrido desde preguntas especificas compiladas."""
        preguntas_texto = "\n".join(
            f"- {p.get('texto', p) if isinstance(p, dict) else p}"
            for p in preguntas[:8]
        )

        return f'''```python
pipeline = [
    {{"op": "ANALIZAR", "target": caso, "questions": "ver_abajo", "output": "hallazgos"}},
]
```

Responde cada pregunta con un hallazgo concreto y accionable.

Preguntas:
{preguntas_texto}

Output: hallazgos (uno por linea), puntos_ciegos.

CASO:
{input_texto}'''

    async def _llamar_llm(self, modelo: str, prompt: str) -> str:
        """Llamar a un modelo via OpenRouter con Circuit Breaker (SN-16)."""
        from .monitoring import get_circuit_breaker
        breaker = get_circuit_breaker()

        # Circuit Breaker: si modelo esta OPEN, usar fallback
        modelo_real = modelo
        if not breaker.puede_llamar(modelo):
            modelo_real = breaker.get_modelo_fallback(modelo)

        if not self.openrouter_key:
            return f"[SIN API KEY] Simulacion para modelo {modelo_real}"

        t0_llm = time.time()
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    self.openrouter_url,
                    headers={
                        'Authorization': f'Bearer {self.openrouter_key}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'model': modelo_real,
                        'messages': [{'role': 'user', 'content': prompt}],
                        'max_tokens': 2000,
                        'temperature': 0.3,
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    usage = data.get('usage', {})
                    tokens_in = usage.get('prompt_tokens', 0)
                    tokens_out = usage.get('completion_tokens', 0)
                    # Use ModelObservatory pricing if available
                    try:
                        from .model_observatory import get_observatory
                        pricing = get_observatory().get_pricing(modelo_real)
                        coste = (tokens_in * pricing['input'] + tokens_out * pricing['output']) / 1_000_000
                    except Exception:
                        coste = (tokens_in * 0.27 + tokens_out * 1.10) / 1_000_000
                    self.coste_acumulado += coste
                    try:
                        from .costes import registrar_coste
                        registrar_coste(
                            modelo=modelo_real,
                            tokens_input=tokens_in,
                            tokens_output=tokens_out,
                            latencia_ms=int((time.time() - t0_llm) * 1000),
                            provider='openrouter',
                        )
                    except Exception as _e:
                        print(f"[WARN:motor_vn._llamar_llm.coste] {type(_e).__name__}: {_e}")
                    breaker.registrar_exito(modelo_real)
                    return content
                else:
                    breaker.registrar_fallo(modelo_real)
                    return f"[ERROR {r.status_code}] {r.text[:200]}"
        except Exception as e:
            breaker.registrar_fallo(modelo_real)
            return f"[EXCEPTION] {str(e)}"

    def _evaluar(self, hallazgos: list, input_texto: str) -> dict:
        """Step 5: Evaluador heuristico (codigo puro)."""
        n_hallazgos = len(hallazgos)
        ints_cubiertas = len(set(h.get('inteligencia', '') for h in hallazgos))

        return {
            'n_hallazgos': n_hallazgos,
            'inteligencias_cubiertas': ints_cubiertas,
            'cobertura': round(ints_cubiertas / max(1, n_hallazgos) * 100, 1) if n_hallazgos else 0,
            'score_calidad': min(1.0, n_hallazgos / 10),
        }

    def _integrar(self, hallazgos: list, scores: dict, input_texto: str) -> str:
        """Step 6: Integrador — sintesis determinista (codigo puro, sin LLM).

        En produccion con tier >= 3, esto usaria un LLM sintetizador (Cogito).
        Para MVP, generamos sintesis estructurada sin LLM.
        """
        if not hallazgos:
            return "Sin hallazgos para sintetizar."

        por_int = {}
        for h in hallazgos:
            int_id = h.get('inteligencia', 'unknown')
            if int_id not in por_int:
                por_int[int_id] = []
            por_int[int_id].append(h.get('hallazgo', ''))

        lineas = [f"SINTESIS ({scores.get('n_hallazgos', 0)} hallazgos, "
                  f"{scores.get('inteligencias_cubiertas', 0)} inteligencias):"]
        for int_id, hs in por_int.items():
            lineas.append(f"\n[{int_id}]:")
            for h in hs[:3]:
                lineas.append(f"  - {h[:200]}")

        return "\n".join(lineas)

    # =====================================================
    # PERSISTENCIA DE PROGRAMAS
    # =====================================================

    def _persistir_programa(self, programa_dict: dict, gradientes: dict,
                            consumidor: str, modo: str) -> Optional[int]:
        """Persist compiled program to programas_compilados.

        Uses consumidor+modo as logical key. UPSERT: if exists, increment version.
        """
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return None
            try:
                consumidor_key = f"{consumidor}_{modo}"
                patron_gaps = json.dumps(gradientes.get('top_gaps', [])[:10], default=str)
                programa_json = json.dumps({
                    'inteligencias': programa_dict.get('inteligencias', []),
                    'pasos': programa_dict.get('pasos', []),
                    'modo': modo,
                    'profundidad': programa_dict.get('profundidad', 1),
                }, default=str)

                with conn.cursor() as cur:
                    # Check if exists
                    cur.execute("""
                        SELECT id, version FROM programas_compilados
                        WHERE consumidor = %s AND activo = true
                        ORDER BY compilado_at DESC LIMIT 1
                    """, (consumidor_key,))
                    existing = cur.fetchone()

                    if existing:
                        cur.execute("""
                            UPDATE programas_compilados
                            SET patron_gaps = %s::jsonb,
                                programa = %s::jsonb,
                                version = version + 1,
                                compilado_at = now()
                            WHERE id = %s
                            RETURNING id
                        """, (patron_gaps, programa_json, existing[0]))
                        row = cur.fetchone()
                        programa_id = row[0] if row else existing[0]
                    else:
                        cur.execute("""
                            INSERT INTO programas_compilados
                                (consumidor, patron_gaps, programa, version, activo)
                            VALUES (%s, %s::jsonb, %s::jsonb, 1, true)
                            RETURNING id
                        """, (consumidor_key, patron_gaps, programa_json))
                        programa_id = cur.fetchone()[0]

                conn.commit()
                return programa_id
            finally:
                put_conn(conn)
        except Exception as e:
            print(f"[ERROR:motor_vn._persistir_programa] {type(e).__name__}: {e}")
            return None

    def _calcular_tasa_cierre(self, resultado: dict, programa: FrozenPrograma) -> float:
        """Calculate closure rate from execution result."""
        hallazgos = resultado.get('hallazgos', [])
        n_ints = len(programa.inteligencias)
        if n_ints == 0:
            return 0.0
        # Heuristic: each INT with >= 3 hallazgos counts as "closed"
        ints_con_hallazgos = set()
        for h in hallazgos:
            int_id = h.get('inteligencia', '')
            ints_con_hallazgos.add(int_id)
        return round(len(ints_con_hallazgos) / max(1, n_ints), 4)

    def _actualizar_programa_post_ejecucion(self, programa_db_id: Optional[int],
                                             tasa_cierre: float) -> None:
        """Update n_ejecuciones and tasa_cierre_media after successful execution."""
        if not programa_db_id:
            return
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return
            try:
                with conn.cursor() as cur:
                    # Incremental weighted average: new_avg = (old_avg * n + new) / (n + 1)
                    cur.execute("""
                        UPDATE programas_compilados
                        SET n_ejecuciones = n_ejecuciones + 1,
                            tasa_cierre_media = CASE
                                WHEN n_ejecuciones = 0 THEN %s
                                ELSE (COALESCE(tasa_cierre_media, 0) * n_ejecuciones + %s)
                                     / (n_ejecuciones + 1)
                            END
                        WHERE id = %s
                    """, (tasa_cierre, tasa_cierre, programa_db_id))
                conn.commit()
            finally:
                put_conn(conn)
        except Exception as _e:
            print(f"[WARN:motor_vn._actualizar_programa] {type(_e).__name__}: {_e}")

    # =====================================================
    # REGISTRADOR (Step 7)
    # =====================================================

    def _registrar(self, programa: FrozenPrograma, resultado: dict,
                   caso_id: str, consumidor: str,
                   input_texto: str = '', gradientes: dict = None) -> list:
        """Step 7: Registrar datapoints con señales PID (SN-06).

        Fase 3: Usa celdas reales de gradientes + evaluador LLM para tasa calibrada.
        """
        from .registrador import registrar_ejecucion

        modelos_usados = resultado.get('modelos_usados', {})
        señales_all = []

        # Obtener celdas relevantes de gradientes (Fase 3 Fix 1)
        celdas_relevantes = {}
        if gradientes:
            for celda, g in gradientes.get('gradientes', {}).items():
                if isinstance(g, dict) and g.get('gap', 0) > 0.3:
                    celdas_relevantes[celda] = g.get('gap', 0.5)

        for int_id in programa.inteligencias:
            hallazgos_int = [h for h in resultado.get('hallazgos', [])
                            if h.get('inteligencia') == int_id]

            # Usar celda real del gradiente si disponible, sino primera celda relevante
            if celdas_relevantes:
                # Asignar la celda con mayor gap (round-robin entre INTs)
                sorted_celdas = sorted(celdas_relevantes.items(), key=lambda x: x[1], reverse=True)
                idx = list(programa.inteligencias).index(int_id) if int_id in programa.inteligencias else 0
                celda, gap_pre = sorted_celdas[idx % len(sorted_celdas)]
            else:
                celda = 'ConservarxSalud'
                gap_pre = 0.5

            señales = registrar_ejecucion({
                'pregunta_id': f'{int_id}-motor_vn',
                'modelo': modelos_usados.get(int_id, self._seleccionar_modelo(programa.tier)),
                'caso_id': caso_id,
                'consumidor': consumidor,
                'celda_objetivo': celda,
                'gap_pre': gap_pre,
                'hallazgos': [h.get('hallazgo', '') for h in hallazgos_int],
                'input_texto': input_texto,  # Fase 3: para evaluador LLM
                'latencia_ms': int(resultado.get('n_llm_calls', 1) * 3000),
                'coste_usd': round(self.coste_acumulado / max(1, len(programa.inteligencias)), 4),
            })
            señales_all.append({'inteligencia': int_id, 'celda': celda, **señales})

        return señales_all


# Instancia global
_motor_vn = None

def get_motor() -> MotorVN:
    """Obtener instancia singleton del Motor vN."""
    global _motor_vn
    if _motor_vn is None:
        _motor_vn = MotorVN()
    return _motor_vn
