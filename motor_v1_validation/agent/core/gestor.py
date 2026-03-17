"""Gestor de la Matriz — mira hacia dentro, mantiene y compila.

El Gestor tiene 3 funciones basicas:
1. Calcular campo de gradientes (que celdas tienen gap)
2. Compilar programa de preguntas (que preguntas + modelos usar)
3. Registrar efectividad (feedback loop)

Referencia: Maestro v3 §6
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

# Las 3 lentes y 7 funciones (L0 — invariantes)
LENTES = ['Salud', 'Sentido', 'Continuidad']
FUNCIONES = ['Conservar', 'Captar', 'Depurar', 'Distribuir', 'Frontera', 'Adaptar', 'Replicar']

# 6 irreducibles (Maestro v3 §1.5)
IRREDUCIBLES = ['INT-01', 'INT-02', 'INT-06', 'INT-08', 'INT-14', 'INT-16']

# Parametros del controlador (segundo orden — se auto-ajustan)
# El operador GAMC modifica estos parametros cada ciclo
GESTOR_PARAMS = {
    'umbral_poda': 0.05,        # tasa < umbral → candidata a poda
    'umbral_promocion': 0.40,   # tasa > umbral → promover a Tier 1
    'min_n_decision': 10,       # minimo N datapoints para decidir
    'ventana_pid': 50,          # ventana para señales PID
    'agresividad_poda': 0.5,    # 0=conservador, 1=agresivo
    'gamma_adaptacion': 0.1,    # tasa de adaptacion (trade-off velocidad/estabilidad)
    'epsilon_estabilidad': 0.10, # Lyapunov: repertorio no encoge mas de 10% por ciclo
}


def calcular_gradientes(input_texto: str, conn=None) -> dict:
    """Calcula campo de gradientes para un input.

    Usa LLM barato (MiMo) para detectar gaps REALES en celdas relevantes.
    Fallback a heuristico de keywords si LLM falla.

    Args:
        input_texto: Caso en lenguaje natural
        conn: Conexion DB

    Returns:
        dict con gradientes por celda: {celda: {actual, objetivo, gap}}
    """
    own_conn = conn is None
    if own_conn:
        from .db_pool import get_conn
        conn = get_conn()

    try:
        # Detector LLM (Fase 3 Fix 1) — solo celdas relevantes
        gradientes = _detectar_gaps_llm(input_texto)

        # Fallback si LLM no devolvio nada
        if not gradientes:
            gradientes = _detectar_gaps_heuristico(input_texto)

        # B3: Blend con datos materializados de celdas_matriz
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, grado_actual, grado_objetivo, gap
                        FROM celdas_matriz
                    """)
                    db_gaps = {row[0]: row[3] for row in cur.fetchall()}
                if db_gaps:
                    for celda, g in gradientes.items():
                        if celda in db_gaps and db_gaps[celda] is not None:
                            gap_llm = g.get('gap', 0.0)
                            gap_db = db_gaps[celda]
                            g['gap'] = round(0.7 * gap_llm + 0.3 * gap_db, 4)
            except Exception:
                pass  # tabla no existe aun — no romper

        # Ordenar por gap descendente
        top_gaps = sorted(
            [(celda, g['gap']) for celda, g in gradientes.items()],
            key=lambda x: x[1], reverse=True
        )[:10]

        # Guardar en DB
        ejecucion_id = str(uuid.uuid4())[:8]
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO campo_gradientes (ejecucion_id, input_texto, gradientes, top_gaps)
                VALUES (%s, %s, %s::jsonb, %s::jsonb)
            """, [ejecucion_id, input_texto[:500],
                  json.dumps(gradientes, default=str), json.dumps(top_gaps)])
        conn.commit()

        return {
            'ejecucion_id': ejecucion_id,
            'gradientes': gradientes,
            'top_gaps': top_gaps,
        }
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {'error': str(e), 'gradientes': {}, 'top_gaps': []}
    finally:
        if own_conn:
            from .db_pool import put_conn
            put_conn(conn)


def _detectar_gaps_llm(input_texto: str) -> dict:
    """Detecta gaps reales usando un modelo OS barato (MiMo/V3.2).

    Reemplaza el heuristico de keywords. Solo devuelve celdas relevantes.
    Coste: ~$0.001 (MiMo, ~500 tokens).

    Returns:
        dict: {celda: {actual, objetivo, gap, relevancia, motivo}}
    """
    import re

    prompt = f"""Analiza este caso y determina qué celdas de la Matriz 3L×7F son relevantes.

Caso: {input_texto[:1000]}

Matriz:
- 3 Lentes: Salud (funciona hoy), Sentido (tiene propósito), Continuidad (sobrevive sin ti)
- 7 Funciones: Conservar (mantener), Captar (obtener recursos), Depurar (eliminar lo que sobra), Distribuir (asignar prioridades), Frontera (definir límites), Adaptar (responder a cambios), Replicar (escalar/reproducir)

Para cada celda relevante al caso (NO todas — solo las que el caso realmente toca), responde:
- celda: "FunciónxLente" (ej: "CaptarxSalud")
- relevancia: 0.0-1.0 (cuánto toca el caso esta celda)
- gap: 0.0-1.0 (cuánta información FALTA sobre esta celda en el caso)
- motivo: por qué esta celda es relevante (1 frase)

Responde SOLO en JSON. Array de objetos. Máximo 8 celdas. No incluyas celdas con relevancia < 0.3.

[{{"celda": "CaptarxSalud", "relevancia": 0.9, "gap": 0.7, "motivo": "..."}}]"""

    try:
        from .api import call_openrouter

        # Seleccionar modelo de fontanería desde config_modelos
        modelo = 'xiaomi/mimo-v2-flash'
        try:
            from .db_pool import get_conn, put_conn
            c = get_conn()
            if c:
                try:
                    with c.cursor() as cur:
                        cur.execute("""
                            SELECT modelo FROM config_modelos
                            WHERE rol = 'fontaneria' AND activo = true
                            ORDER BY coste_input_per_m ASC LIMIT 1
                        """)
                        row = cur.fetchone()
                        if row:
                            modelo = row[0]
                            print(f"[detector_gaps_llm] modelo from DB: {modelo}")
                finally:
                    put_conn(c)
        except Exception as db_err:
            print(f"[detector_gaps_llm] DB lookup failed, using default: {db_err}")

        print(f"[detector_gaps_llm] calling {modelo} with {len(input_texto)} chars")
        from .costes import set_call_context
        set_call_context(componente='detector_gaps', operacion='deteccion_gaps')
        response = call_openrouter(
            messages=[{"role": "user", "content": prompt}],
            model=modelo,
            max_tokens=800,
            temperature=0.1,
        )

        texto = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        if not texto:
            print(f"[detector_gaps_llm] empty response from {modelo}")
            return {}

        print(f"[detector_gaps_llm] raw response ({len(texto)} chars): {texto[:200]}")

        # Limpiar respuesta (quitar markdown fences)
        texto = texto.strip()
        if texto.startswith('```'):
            texto = texto.split('\n', 1)[1].rsplit('```', 1)[0].strip()

        # Intentar extraer array JSON de la respuesta
        json_match = re.search(r'\[.*\]', texto, re.DOTALL)
        if json_match:
            texto = json_match.group(0)

        celdas_raw = json.loads(texto)

        # Convertir a formato gradientes
        gradientes = {}
        for celda_data in celdas_raw:
            celda = celda_data.get('celda', '')
            if not celda:
                continue
            # Normalizar separador: × → x
            celda = celda.replace('×', 'x')
            # Normalizar mayúsculas/minúsculas
            parts = celda.split('x')
            if len(parts) != 2:
                print(f"[detector_gaps_llm] skipping malformed celda: {celda}")
                continue
            # Title-case para coincidir con FUNCIONES/LENTES
            funcion = parts[0].strip().capitalize()
            lente = parts[1].strip().capitalize()
            if funcion not in FUNCIONES or lente not in LENTES:
                print(f"[detector_gaps_llm] skipping unknown celda: {funcion}x{lente}")
                continue
            celda = f"{funcion}x{lente}"

            relevancia = min(1.0, max(0.0, float(celda_data.get('relevancia', 0))))
            gap = min(1.0, max(0.0, float(celda_data.get('gap', 0))))
            if relevancia < 0.3:
                continue

            gradientes[celda] = {
                'actual': round(1.0 - gap, 4),
                'objetivo': 1.0,
                'gap': round(gap, 4),
                'relevancia': round(relevancia, 4),
                'motivo': celda_data.get('motivo', '')[:200],
            }

        print(f"[detector_gaps_llm] detected {len(gradientes)} celdas: {list(gradientes.keys())}")

        # Telemetria
        try:
            from .telemetria import registrar_metrica
            registrar_metrica('gestor', 'detector_gaps_llm', {
                'celdas_detectadas': len(gradientes),
                'modelo': modelo,
                'celdas': list(gradientes.keys()),
            })
        except Exception:
            pass

        return gradientes

    except Exception as e:
        print(f"[detector_gaps_llm] EXCEPTION: {type(e).__name__}: {e}")
        # Telemetria del fallback
        try:
            from .telemetria import registrar_metrica
            registrar_metrica('gestor', 'detector_gaps_llm_fallback', {'error': str(e)[:200]})
        except Exception:
            pass
        return {}


def _detectar_gaps_heuristico(input_texto: str) -> dict:
    """Heuristico de keywords original — solo como fallback."""
    gradientes = {}
    input_lower = input_texto.lower()
    for lente in LENTES:
        for funcion in FUNCIONES:
            celda = f"{funcion}x{lente}"
            gap = _detectar_gap_celda(input_lower, lente, funcion)
            gradientes[celda] = {
                'actual': 0.0 if gap > 0.3 else 0.5,
                'objetivo': 1.0,
                'gap': gap,
            }
    return gradientes


def _detectar_gap_celda(input_lower: str, lente: str, funcion: str) -> float:
    """Heuristico para detectar gap en una celda.

    Returns:
        float entre 0.0 (cubierto) y 1.0 (gap total)
    """
    keywords_funcion = {
        'Conservar': ['mantener', 'preservar', 'conservar', 'proteger', 'estable', 'funciona'],
        'Captar': ['captar', 'incorporar', 'recurso', 'ingreso', 'obtener', 'atraer', 'vender'],
        'Depurar': ['eliminar', 'depurar', 'filtrar', 'limpiar', 'sobra', 'coste', 'gasto'],
        'Distribuir': ['distribuir', 'asignar', 'repartir', 'priorizar', 'donde'],
        'Frontera': ['frontera', 'limite', 'dentro', 'fuera', 'definir', 'alcance'],
        'Adaptar': ['adaptar', 'cambiar', 'evolucionar', 'responder', 'ajustar'],
        'Replicar': ['replicar', 'escalar', 'reproducir', 'crecer', 'expandir'],
    }

    keywords_lente = {
        'Salud': ['funciona', 'roto', 'problema', 'fallo', 'operativo', 'salud'],
        'Sentido': ['sentido', 'proposito', 'mision', 'direccion', 'por que', 'para que'],
        'Continuidad': ['futuro', 'sobrevivir', 'continuidad', 'sostenible', 'sin mi', 'escalar'],
    }

    kw_funcion = keywords_funcion.get(funcion, [])
    kw_lente = keywords_lente.get(lente, [])

    presencia_funcion = sum(1 for kw in kw_funcion if kw in input_lower)
    presencia_lente = sum(1 for kw in kw_lente if kw in input_lower)

    if presencia_funcion == 0 and presencia_lente == 0:
        return 0.8
    elif presencia_funcion > 0 and presencia_lente > 0:
        return 0.2
    else:
        return 0.5


def compilar_programa(gradientes: dict, consumidor: str = 'motor_vn',
                      conn=None) -> dict:
    """Compila un programa de preguntas para un patron de gaps.

    Busca primero en programas_compilados (cache Fase B).
    Si no hay cache, compila desde la Matriz (Fase A).
    """
    own_conn = conn is None
    if own_conn:
        from .db_pool import get_conn
        conn = get_conn()

    try:
        top_gaps = gradientes.get('top_gaps', [])
        if not top_gaps:
            return {'pasos': [], 'fase': 'sin_gaps'}

        # Fase B: buscar programa compilado en cache
        patron_gaps = {celda: gap for celda, gap in top_gaps if gap > 0.3}

        with conn.cursor() as cur:
            cur.execute("""
                SELECT programa, tasa_cierre_media, n_ejecuciones
                FROM programas_compilados
                WHERE consumidor = %s AND activo = true
                  AND patron_gaps @> %s::jsonb
                ORDER BY tasa_cierre_media DESC
                LIMIT 1
            """, [consumidor, json.dumps(patron_gaps)])
            row = cur.fetchone()

            if row and row[2] > 30 and (row[1] or 0) > 0.60:
                return {
                    'pasos': row[0].get('pasos', []),
                    'fase': 'B_lookup',
                    'tasa_cierre': row[1],
                    'n_ejecuciones': row[2],
                }

            # Fase A — compilar desde la Matriz
            programa = _compilar_desde_matriz(top_gaps, conn)

            return {
                'pasos': programa,
                'fase': 'A_exploracion',
            }

    except Exception as e:
        return {'pasos': [], 'fase': 'error', 'error': str(e)}
    finally:
        if own_conn:
            from .db_pool import put_conn
            put_conn(conn)


def _compilar_desde_matriz(top_gaps: list, conn, modo: str = 'analisis') -> list:
    """Compila programa desde la Matriz (Fase A).

    Usa ConstraintManifold (SN-08) para generar programas validos
    por construccion, en vez de aplicar reglas ad-hoc.
    """
    from .reglas_compilador import get_manifold
    manifold = get_manifold()

    # Generar programa usando el Manifold (satisface 13 reglas por construccion)
    gradientes = {'top_gaps': top_gaps}
    programa = manifold.generar(gradientes, modo=modo)
    ints_seleccionadas = programa.get('inteligencias', [])

    pasos = []

    with conn.cursor() as cur:
        ints_lista = list(ints_seleccionadas)[:5]

        for idx, int_id in enumerate(ints_lista):
            preguntas_pasos = []
            for celda, gap in top_gaps[:7]:
                if gap < 0.3:
                    continue
                parts = celda.split('x')
                funcion = parts[0] if len(parts) > 0 else 'Conservar'
                lente = parts[1] if len(parts) > 1 else 'Salud'

                cur.execute("""
                    SELECT id, texto FROM preguntas_matriz
                    WHERE inteligencia = %s AND lente = %s AND funcion = %s
                    ORDER BY score_efectividad DESC NULLS LAST
                    LIMIT 3
                """, [int_id, lente, funcion])
                for row in cur.fetchall():
                    preguntas_pasos.append({
                        'pregunta_id': row[0],
                        'texto': row[1],
                        'celda': celda,
                    })

            # Modelo desde config
            cur.execute("""
                SELECT modelo FROM config_modelos
                WHERE rol = 'ejecutor_principal' AND activo = true
                LIMIT 1
            """)
            modelo_row = cur.fetchone()
            modelo = modelo_row[0] if modelo_row else 'deepseek/deepseek-chat-v3-0324'

            pasos.append({
                'orden': idx + 1,
                'inteligencia': int_id,
                'preguntas': preguntas_pasos,
                'modelo': modelo,
                'operacion': 'individual',
            })

    return pasos


def registrar_efectividad(pregunta_id: str, modelo: str, caso_id: str,
                          consumidor: str, celda_objetivo: str,
                          gap_pre: float, gap_post: float,
                          operacion: str = 'individual',
                          conn=None):
    """Wrapper de compatibilidad — delega a core/registrador.py (SN-06)."""
    from .registrador import registrar_ejecucion
    return registrar_ejecucion({
        'pregunta_id': pregunta_id,
        'modelo': modelo,
        'caso_id': caso_id,
        'consumidor': consumidor,
        'celda_objetivo': celda_objetivo,
        'gap_pre': gap_pre,
        'gap_post': gap_post,
        'operacion': operacion,
    }, conn=conn)


def refrescar_vista():
    """Refresca la vista materializada pregunta_efectividad."""
    from .db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW pregunta_efectividad")
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        put_conn(conn)


class GestorGAMC:
    """Operador de segundo orden G: Phi → Phi'.

    Patron GAMC (#60677): no solo ajusta la Matriz, sino que ajusta
    como ajusta la Matriz. Tiene 10 pasos de primer orden + 1 paso
    de segundo orden (auto-ajuste de parametros).

    Invariantes:
    1. Campo de gradientes SIEMPRE existe antes de ejecucion
    2. Repertorio Phi NUNCA vacio
    3. Loop es infinito por diseño
    """

    def __init__(self):
        self.params = dict(GESTOR_PARAMS)  # copia mutable
        self.ciclo_n = 0

    def ejecutar_loop(self, conn=None) -> dict:
        """Ejecuta los 10 pasos del loop lento + auto-ajuste.

        Returns:
            dict con resultados de cada paso + metricas del ciclo
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        # Clear any dirty transaction state from previous operations
        try:
            conn.rollback()
        except Exception:
            pass

        try:
            from .mejora_continua import log_gestor

            self.ciclo_n += 1
            t0 = time.time()
            resultados = {}

            # --- PRIMER ORDEN: 10 pasos sobre la Matriz ---
            pasos = [
                ('actualizar_scores', self._paso1_actualizar_scores),
                ('podar', self._paso2_podar),
                ('promover', self._paso3_promover),
                ('complementariedad', self._paso4_complementariedad),
                ('transferencia', self._paso5_transferencia),
                ('recalcular_modelos', self._paso6_recalcular_modelos),
                ('recompilar', self._paso7_recompilar),
                ('marcar_obsoletos', self._paso8_marcar_obsoletos),
                ('contradicciones', self._paso9_contradicciones),
                ('expirar', self._paso10_expirar),
            ]

            for nombre, fn in pasos:
                try:
                    resultados[nombre] = fn(conn)
                    conn.commit()
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    resultados[nombre] = {'error': str(e)}

            # --- PREDICTIVE CONTROLLER: inform loop with trajectory + planned actions ---
            try:
                from .predictive_controller import get_predictive_controller
                pc = get_predictive_controller()
                trayectoria = pc.predecir_trayectoria(conn)
                plan_acciones = pc.planificar_acciones(conn)
                resultados['predictive'] = {
                    'tendencia': trayectoria.get('tendencia', 'unknown'),
                    'tasa_predicha': trayectoria.get('tasa_predicha_horizonte', 0),
                    'acciones_planificadas': len(plan_acciones.get('acciones_planificadas', [])),
                    'top_accion': plan_acciones.get('acciones_planificadas', [{}])[0] if plan_acciones.get('acciones_planificadas') else None,
                }
            except Exception:
                resultados['predictive'] = {'error': 'unavailable'}

            # --- SEGUNDO ORDEN: auto-ajustar parametros ---
            ajuste = self._auto_ajustar_parametros(resultados, conn)
            resultados['auto_ajuste'] = ajuste

            # Metricas del ciclo
            elapsed = round(time.time() - t0, 2)
            resultados['ciclo'] = {
                'n': self.ciclo_n,
                'tiempo_s': elapsed,
                'parametros': dict(self.params),
            }

            # Calcular tasa media global (para Flywheel en SN-10)
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT AVG(tasa_cierre) FROM datapoints_efectividad
                        WHERE timestamp > NOW() - INTERVAL '7 days'
                          AND calibrado = true
                    """)
                    row = cur.fetchone()
                    resultados['tasa_media_global'] = round(row[0], 4) if row and row[0] else 0.0
            except Exception:
                resultados['tasa_media_global'] = 0.0

            # --- FLYWHEEL: update model scores from cycle results (Fase 2 Conexión 3) ---
            try:
                from .flywheel import after_session, check_promotion
                tasa = resultados.get('tasa_media_global', 0)
                after_session({
                    'model_used': 'gestor_loop',
                    'success': tasa > 0.3,
                    'cost_usd': 0,
                    'iterations': self.ciclo_n,
                    'error_rate': 1.0 - tasa if tasa else 0.5,
                    'mode': 'gestor',
                })
                promo = check_promotion()
                if promo:
                    resultados['flywheel_promocion'] = promo
                    log_gestor('flywheel_promocion', promo, nivel='auto', conn=conn)
            except Exception:
                pass

            # --- TOOL EVOLUTION: automatic analysis (Fase 2 Conexión 4) ---
            try:
                from .tool_evolution import get_tool_evolution
                evo = get_tool_evolution()
                top_gaps = evo.get_top_gaps(limit=5)
                if top_gaps:
                    resultados['tool_gaps_abiertos'] = len(top_gaps)
                    log_gestor('tool_evolution_gaps', {
                        'n_gaps': len(top_gaps),
                        'top_gap': top_gaps[0].get('description', '')[:100] if top_gaps else '',
                    }, nivel='auto', conn=conn)
                # Suggest compositions from telemetry patterns
                sugerencias = evo.suggest_compositions()
                if sugerencias:
                    resultados['tool_compositions_sugeridas'] = len(sugerencias)
            except Exception:
                pass

            # Log del ciclo completo
            log_gestor('loop_completo', {
                'ciclo': self.ciclo_n,
                'tiempo_s': elapsed,
                'tasa_media_global': resultados.get('tasa_media_global', 0),
                'pasos_ok': sum(1 for v in resultados.values() if isinstance(v, dict) and 'error' not in v),
                'pasos_error': sum(1 for v in resultados.values() if isinstance(v, dict) and 'error' in v),
                'flywheel_promocion': 'flywheel_promocion' in resultados,
                'tool_gaps': resultados.get('tool_gaps_abiertos', 0),
            }, nivel='auto', conn=conn)

            return resultados

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    # =========================================
    # PRIMER ORDEN: 10 pasos sobre la Matriz
    # =========================================

    def _paso1_actualizar_scores(self, conn) -> dict:
        """Refrescar vista materializada + actualizar scores en preguntas_matriz."""
        with conn.cursor() as cur:
            # Refrescar vista materializada (si existe)
            try:
                cur.execute("REFRESH MATERIALIZED VIEW pregunta_efectividad")
            except Exception:
                conn.rollback()

            # Actualizar score_efectividad en preguntas_matriz desde datapoints
            cur.execute("""
                UPDATE preguntas_matriz pm SET
                    score_efectividad = sub.avg_tasa,
                    gap_medio_cerrado = sub.avg_gap_cerrado
                FROM (
                    SELECT pregunta_id,
                           AVG(tasa_cierre) as avg_tasa,
                           AVG(gap_cerrado) as avg_gap_cerrado
                    FROM datapoints_efectividad
                    WHERE calibrado = true
                    GROUP BY pregunta_id
                    HAVING COUNT(*) >= 3
                ) sub
                WHERE pm.id = sub.pregunta_id
            """)
            updated = cur.rowcount

        conn.commit()
        return {'preguntas_actualizadas': updated}

    def _paso2_podar(self, conn) -> dict:
        """Poda informada por PID: solo si I alto Y D >= 0 (no mejorando).

        A diferencia de la version naive que poda por tasa < umbral,
        esta version usa señales PID del Registrador (SN-06):
        - Solo poda si I alto (problema cronico, no puntual)
        - No poda si D < 0 (la pregunta esta mejorando)
        """
        from .registrador import computar_señales_pid

        podadas = []
        with conn.cursor() as cur:
            # Candidatas: n > min_n_decision AND tasa < umbral_poda
            cur.execute("""
                SELECT pregunta_id, celda_objetivo,
                       COUNT(*) as n, AVG(tasa_cierre) as tasa
                FROM datapoints_efectividad
                WHERE calibrado = true
                GROUP BY pregunta_id, celda_objetivo
                HAVING COUNT(*) > %s AND AVG(tasa_cierre) < %s
            """, [self.params['min_n_decision'], self.params['umbral_poda']])

            for row in cur.fetchall():
                pregunta_id, celda, n, tasa = row

                # Consultar señales PID para esta celda
                señales = computar_señales_pid(celda, conn=conn)
                I = señales.get('I_anti_windup', 0)
                D = señales.get('D_filtrado', 0)

                # Poda informada: solo si I alto (>2) Y D >= 0 (no mejorando)
                I_threshold = 2.0 * self.params['agresividad_poda']
                if I > I_threshold and D >= 0:
                    # Marcar como podada (no borrar, solo desactivar)
                    cur.execute("""
                        UPDATE preguntas_matriz
                        SET nivel = 'podada'
                        WHERE id = %s AND nivel != 'podada'
                    """, [pregunta_id])
                    if cur.rowcount > 0:
                        podadas.append({
                            'pregunta_id': pregunta_id,
                            'celda': celda,
                            'n': n, 'tasa': round(float(tasa), 4),
                            'I': I, 'D': round(D, 4),
                            'razon': f'I={I:.2f} > {I_threshold:.2f} AND D={D:.4f} >= 0'
                        })

        # Verificar estabilidad Lyapunov: no podar mas de epsilon% del repertorio
        if podadas:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM preguntas_matriz WHERE nivel != 'podada'")
                total_activas = cur.fetchone()[0]
                max_poda = int(total_activas * self.params['epsilon_estabilidad'])
                if len(podadas) > max_poda:
                    # Rollback excess pruning — keep only top N by severity
                    podadas_exceso = podadas[max_poda:]
                    for p in podadas_exceso:
                        cur.execute("""
                            UPDATE preguntas_matriz SET nivel = 'base'
                            WHERE id = %s
                        """, [p['pregunta_id']])
                    podadas = podadas[:max_poda]

        conn.commit()
        return {'podadas': len(podadas), 'detalle': podadas}

    def _paso3_promover(self, conn) -> dict:
        """Promocion: tasa > umbral Y D < 0 (tendencia positiva)."""
        from .registrador import computar_señales_pid

        promovidas = []
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pregunta_id, celda_objetivo,
                       COUNT(*) as n, AVG(tasa_cierre) as tasa
                FROM datapoints_efectividad
                WHERE calibrado = true
                GROUP BY pregunta_id, celda_objetivo
                HAVING COUNT(*) > %s AND AVG(tasa_cierre) > %s
            """, [self.params['min_n_decision'], self.params['umbral_promocion']])

            for row in cur.fetchall():
                pregunta_id, celda, n, tasa = row
                señales = computar_señales_pid(celda, conn=conn)
                D = señales.get('D_filtrado', 0)

                # Promover si D < 0 (tendencia positiva = gaps decrecientes)
                if D < 0:
                    cur.execute("""
                        UPDATE preguntas_matriz
                        SET nivel = 'tier_1'
                        WHERE id = %s AND nivel != 'tier_1'
                    """, [pregunta_id])
                    if cur.rowcount > 0:
                        promovidas.append({
                            'pregunta_id': pregunta_id,
                            'celda': celda,
                            'n': n, 'tasa': round(float(tasa), 4),
                            'D': round(D, 4),
                        })

        conn.commit()
        return {'promovidas': len(promovidas), 'detalle': promovidas}

    def _paso4_complementariedad(self, conn) -> dict:
        """Detectar pares complementarios: P(A cierra|B no) * P(B cierra|A no)."""
        pares = []
        with conn.cursor() as cur:
            cur.execute("""
                WITH pregunta_stats AS (
                    SELECT pregunta_id, celda_objetivo, caso_id,
                           CASE WHEN tasa_cierre > 0.3 THEN 1 ELSE 0 END as cierra
                    FROM datapoints_efectividad
                    WHERE calibrado = true
                )
                SELECT a.pregunta_id as p_a, b.pregunta_id as p_b,
                       a.celda_objetivo,
                       COUNT(*) as n_comun,
                       AVG(CASE WHEN a.cierra=1 AND b.cierra=0 THEN 1.0 ELSE 0.0 END) as p_a_not_b,
                       AVG(CASE WHEN b.cierra=1 AND a.cierra=0 THEN 1.0 ELSE 0.0 END) as p_b_not_a
                FROM pregunta_stats a
                JOIN pregunta_stats b ON a.caso_id = b.caso_id
                    AND a.celda_objetivo = b.celda_objetivo
                    AND a.pregunta_id < b.pregunta_id
                GROUP BY a.pregunta_id, b.pregunta_id, a.celda_objetivo
                HAVING COUNT(*) >= 5
            """)

            for row in cur.fetchall():
                p_a, p_b, celda, n, p_a_not_b, p_b_not_a = row
                complementariedad = (p_a_not_b or 0) * (p_b_not_a or 0)
                if complementariedad > 0.1:
                    pares.append({
                        'par': [p_a, p_b],
                        'celda': celda,
                        'complementariedad': round(float(complementariedad), 4),
                        'n_comun': n,
                    })

        return {'pares_complementarios': len(pares), 'detalle': pares[:20]}

    def _paso5_transferencia(self, conn) -> dict:
        """Detectar preguntas que funcionan en un dominio y podrian servir en otro."""
        transferencias = []
        with conn.cursor() as cur:
            cur.execute("""
                WITH buenas AS (
                    SELECT pregunta_id, celda_objetivo,
                           AVG(tasa_cierre) as tasa, COUNT(*) as n
                    FROM datapoints_efectividad
                    WHERE calibrado = true
                    GROUP BY pregunta_id, celda_objetivo
                    HAVING AVG(tasa_cierre) > 0.30 AND COUNT(*) > 5
                ),
                celdas_sin_datos AS (
                    SELECT DISTINCT pm.id as pregunta_id,
                           f.funcion || 'x' || l.lente as celda_destino
                    FROM preguntas_matriz pm
                    CROSS JOIN (VALUES ('Conservar'),('Captar'),('Depurar'),
                                       ('Distribuir'),('Frontera'),('Adaptar'),('Replicar')) f(funcion)
                    CROSS JOIN (VALUES ('Salud'),('Sentido'),('Continuidad')) l(lente)
                    WHERE NOT EXISTS (
                        SELECT 1 FROM datapoints_efectividad de
                        WHERE de.pregunta_id = pm.id
                          AND de.celda_objetivo = f.funcion || 'x' || l.lente
                          AND de.calibrado = true
                    )
                )
                SELECT b.pregunta_id, b.celda_objetivo as celda_origen,
                       c.celda_destino, b.tasa
                FROM buenas b
                JOIN celdas_sin_datos c ON b.pregunta_id = c.pregunta_id
                ORDER BY b.tasa DESC
                LIMIT 20
            """)

            for row in cur.fetchall():
                transferencias.append({
                    'pregunta_id': row[0],
                    'celda_origen': row[1],
                    'celda_destino': row[2],
                    'tasa_origen': round(float(row[3]), 4),
                })

        # Generar peticiones al reactor para celdas sin datos
        if transferencias:
            from .mejora_continua import crear_marca_estigmergica
            for t in transferencias[:5]:
                crear_marca_estigmergica('peticion_reactor', 'gestor_paso5', {
                    'celda': t['celda_destino'],
                    'razon': f"transferencia desde {t['celda_origen']} (tasa={t['tasa_origen']})",
                }, conn=conn)

        return {'transferencias_sugeridas': len(transferencias), 'detalle': transferencias}

    def _paso6_recalcular_modelos(self, conn) -> dict:
        """Ranking modelos por tasa_media_cierre por celda."""
        cambios = []
        with conn.cursor() as cur:
            cur.execute("""
                SELECT celda_objetivo, modelo,
                       AVG(tasa_cierre) as tasa_media,
                       COUNT(*) as n
                FROM datapoints_efectividad
                WHERE calibrado = true
                GROUP BY celda_objetivo, modelo
                HAVING COUNT(*) >= 5
                ORDER BY celda_objetivo, tasa_media DESC
            """)

            ranking_por_celda = {}
            for row in cur.fetchall():
                celda = row[0]
                if celda not in ranking_por_celda:
                    ranking_por_celda[celda] = []
                ranking_por_celda[celda].append({
                    'modelo': row[1],
                    'tasa': round(float(row[2]), 4),
                    'n': row[3],
                })

            for celda, ranking in ranking_por_celda.items():
                if len(ranking) >= 2:
                    mejor = ranking[0]
                    segundo = ranking[1]
                    if mejor['tasa'] > segundo['tasa'] * 1.3:
                        cambios.append({
                            'celda': celda,
                            'modelo_ganador': mejor['modelo'],
                            'tasa_ganador': mejor['tasa'],
                            'modelo_segundo': segundo['modelo'],
                            'tasa_segundo': segundo['tasa'],
                        })

        return {
            'ranking_por_celda': ranking_por_celda,
            'cambios_sugeridos': len(cambios),
            'detalle': cambios,
        }

    def _paso7_recompilar(self, conn) -> dict:
        """Recompilar programas_compilados con datos actualizados.
        Si no existen programas, genera programas iniciales desde el campo de gradientes."""
        recompilados = 0
        creados = 0

        with conn.cursor() as cur:
            # Check if any programs exist
            cur.execute("SELECT COUNT(*) FROM programas_compilados WHERE activo = true")
            n_activos = cur.fetchone()[0]

            if n_activos == 0:
                # --- BOOTSTRAP: crear programas iniciales desde gradientes ---
                # Extract top_gaps from most recent campo_gradientes entry (JSONB array)
                cur.execute("""
                    SELECT top_gaps FROM campo_gradientes
                    ORDER BY created_at DESC LIMIT 1
                """)
                row = cur.fetchone()
                if row and row[0]:
                    top_gaps_raw = row[0]  # JSONB array of [celda, gap]
                    top_gaps = [(g[0], float(g[1])) for g in top_gaps_raw if len(g) >= 2]
                else:
                    # Fallback: generate all 21 cells with default gap
                    cur.execute("""
                        SELECT DISTINCT funcion || 'x' || lente as celda, 1.0 as gap
                        FROM preguntas_matriz
                        WHERE nivel = 'base'
                        LIMIT 21
                    """)
                    top_gaps = [(r[0], float(r[1])) for r in cur.fetchall()]

                for modo in ['analisis', 'conversacion', 'generacion', 'confrontacion']:
                    try:
                        programa_pasos = _compilar_desde_matriz(top_gaps, conn, modo=modo)
                        if programa_pasos:
                            patron = {celda: gap for celda, gap in top_gaps[:7]}
                            cur.execute("""
                                INSERT INTO programas_compilados
                                    (consumidor, patron_gaps, programa, version, activo, compilado_at)
                                VALUES (%s, %s::jsonb, %s::jsonb, 1, true, NOW())
                            """, [
                                f'motor_vn_{modo}',
                                json.dumps(patron),
                                json.dumps({'pasos': programa_pasos, 'modo': modo}),
                            ])
                            creados += 1
                    except Exception:
                        pass

            else:
                # --- RECOMPILAR existentes con > 30 ejecuciones ---
                cur.execute("""
                    SELECT id, consumidor, patron_gaps, tasa_cierre_media, n_ejecuciones
                    FROM programas_compilados
                    WHERE activo = true AND n_ejecuciones > 30
                """)

                for row in cur.fetchall():
                    prog_id, consumidor, patron_gaps, tasa_actual, n = row
                    try:
                        top_gaps = list(patron_gaps.items()) if isinstance(patron_gaps, dict) else []
                        nuevo_programa = _compilar_desde_matriz(top_gaps, conn)

                        if nuevo_programa:
                            cur.execute("""
                                UPDATE programas_compilados
                                SET programa = %s::jsonb,
                                    version = version + 1,
                                    compilado_at = NOW()
                                WHERE id = %s
                            """, [json.dumps({'pasos': nuevo_programa}), prog_id])
                            recompilados += 1
                    except Exception:
                        pass

        conn.commit()
        return {'recompilados': recompilados, 'creados': creados}

    def _paso8_marcar_obsoletos(self, conn) -> dict:
        """Marcar preguntas obsoletas: sin datapoints en > 90 dias o referenciando patrones eliminados."""
        obsoletas = []
        with conn.cursor() as cur:
            # Preguntas sin datapoints en los ultimos 90 dias
            cur.execute("""
                SELECT pm.id, pm.inteligencia, pm.funcion, pm.lente
                FROM preguntas_matriz pm
                WHERE pm.nivel NOT IN ('podada', 'obsoleta', 'expirada')
                  AND pm.id NOT IN (
                      SELECT DISTINCT pregunta_id FROM datapoints_efectividad
                      WHERE timestamp > NOW() - INTERVAL '90 days'
                        AND calibrado = true
                  )
                  AND pm.score_efectividad IS NOT NULL
            """)
            for row in cur.fetchall():
                cur.execute("""
                    UPDATE preguntas_matriz SET nivel = 'obsoleta'
                    WHERE id = %s AND nivel NOT IN ('podada', 'obsoleta', 'expirada')
                """, [row[0]])
                if cur.rowcount > 0:
                    obsoletas.append({
                        'pregunta_id': row[0],
                        'inteligencia': row[1],
                        'razon': 'sin_datapoints_90d',
                    })

        # Lyapunov: no marcar mas del epsilon%
        if obsoletas:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM preguntas_matriz WHERE nivel NOT IN ('podada','obsoleta','expirada')")
                total = cur.fetchone()[0]
                max_obs = int(total * self.params['epsilon_estabilidad'])
                if len(obsoletas) > max_obs:
                    for o in obsoletas[max_obs:]:
                        cur.execute("UPDATE preguntas_matriz SET nivel = 'base' WHERE id = %s", [o['pregunta_id']])
                    obsoletas = obsoletas[:max_obs]

        conn.commit()
        return {'obsoletas': len(obsoletas), 'detalle': obsoletas}

    def _paso9_contradicciones(self, conn) -> dict:
        """Detectar contradicciones: misma celda+caso, hallazgos divergentes entre preguntas."""
        contradicciones = []
        with conn.cursor() as cur:
            # Preguntas en misma celda con tasas muy diferentes (una >0.5, otra <0.1)
            cur.execute("""
                SELECT a.pregunta_id as p_a, b.pregunta_id as p_b,
                       a.celda_objetivo,
                       AVG(a.tasa_cierre) as tasa_a, AVG(b.tasa_cierre) as tasa_b,
                       COUNT(*) as n_comun
                FROM datapoints_efectividad a
                JOIN datapoints_efectividad b
                    ON a.caso_id = b.caso_id
                    AND a.celda_objetivo = b.celda_objetivo
                    AND a.pregunta_id < b.pregunta_id
                WHERE a.calibrado = true AND b.calibrado = true
                GROUP BY a.pregunta_id, b.pregunta_id, a.celda_objetivo
                HAVING COUNT(*) >= 3
                    AND ABS(AVG(a.tasa_cierre) - AVG(b.tasa_cierre)) > 0.4
            """)
            for row in cur.fetchall():
                contradicciones.append({
                    'pregunta_a': row[0],
                    'pregunta_b': row[1],
                    'celda': row[2],
                    'tasa_a': round(float(row[3]), 4),
                    'tasa_b': round(float(row[4]), 4),
                    'n_comun': row[5],
                    'divergencia': round(abs(float(row[3]) - float(row[4])), 4),
                })

        # Crear marcas estigmergicas para revision
        if contradicciones:
            from .mejora_continua import crear_marca_estigmergica
            crear_marca_estigmergica('contradiccion', 'gestor_paso9', {
                'n_contradicciones': len(contradicciones),
                'detalle': contradicciones[:10],
            }, conn=conn)

        return {'contradicciones': len(contradicciones), 'detalle': contradicciones[:20]}

    def _paso10_expirar(self, conn) -> dict:
        """Expirar: candidatas sin aprobar >30d + preguntas con caduca_at pasado."""
        expiradas = []
        with conn.cursor() as cur:
            # Candidatas sin aprobar y sin actividad en > 30 dias
            cur.execute("""
                UPDATE preguntas_matriz SET nivel = 'expirada'
                WHERE nivel = 'candidata'
                  AND id NOT IN (
                      SELECT DISTINCT pregunta_id FROM datapoints_efectividad
                      WHERE timestamp > NOW() - INTERVAL '30 days'
                        AND calibrado = true
                  )
                RETURNING id
            """)
            for row in cur.fetchall():
                expiradas.append({'pregunta_id': row[0], 'razon': 'candidata_sin_aprobar_30d'})

            # Marcar datapoints muy antiguos como historicos (flag, no borrar)
            cur.execute("""
                SELECT COUNT(*) FROM datapoints_efectividad
                WHERE timestamp < NOW() - INTERVAL '180 days'
                  AND consumidor != 'historico'
                  AND calibrado = true
            """)
            antiguos = cur.fetchone()[0]

        conn.commit()
        return {
            'expiradas': len(expiradas),
            'detalle': expiradas,
            'datapoints_antiguos_180d': antiguos,
        }

    # =========================================
    # SEGUNDO ORDEN: auto-ajustar parametros
    # =========================================

    def _auto_ajustar_parametros(self, resultados_loop: dict, conn) -> dict:
        """Adaptive Control: ajusta GESTOR_PARAMS basandose en resultados.

        Patron #83759: dos loops — uno sobre el proceso, otro sobre
        los parametros del controlador.

        Reglas de adaptacion:
        1. Si poda fue excesiva (>5 preguntas) → reducir agresividad_poda
        2. Si no se podo nada pero hay muchas preguntas muertas → subir umbral
        3. Si hay muchas oscilaciones → ampliar ventana_pid
        4. gamma_adaptacion controla velocidad de cambio

        Estabilidad (Lyapunov): ||Phi'|| >= ||Phi|| * (1 - epsilon)
        """
        gamma = self.params['gamma_adaptacion']
        ajustes = {}

        # 1. Ajustar agresividad_poda
        poda = resultados_loop.get('podar', {})
        n_podadas = poda.get('podadas', 0)
        if n_podadas > 5:
            old = self.params['agresividad_poda']
            self.params['agresividad_poda'] = max(0.1, old * (1 - gamma))
            ajustes['agresividad_poda'] = {'old': old, 'new': self.params['agresividad_poda'],
                                           'razon': f'{n_podadas} preguntas podadas'}
        elif n_podadas == 0:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT pregunta_id
                        FROM datapoints_efectividad
                        WHERE calibrado = true
                        GROUP BY pregunta_id
                        HAVING COUNT(*) > %s AND AVG(tasa_cierre) < %s
                    ) sub
                """, [self.params['min_n_decision'], self.params['umbral_poda']])
                muertas_potenciales = cur.fetchone()[0]
            if muertas_potenciales > 10:
                old = self.params['agresividad_poda']
                self.params['agresividad_poda'] = min(0.9, old * (1 + gamma))
                ajustes['agresividad_poda'] = {'old': old, 'new': self.params['agresividad_poda'],
                                               'razon': f'{muertas_potenciales} muertas no podadas'}

        # 2. Ajustar umbral_poda basandose en distribucion de tasas
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT percentile_cont(0.10) WITHIN GROUP (ORDER BY avg_tasa)
                    FROM (
                        SELECT AVG(tasa_cierre) as avg_tasa
                        FROM datapoints_efectividad
                        WHERE calibrado = true
                        GROUP BY pregunta_id
                        HAVING COUNT(*) >= %s
                    ) sub
                """, [self.params['min_n_decision']])
                row = cur.fetchone()
                if row and row[0] is not None:
                    p10 = float(row[0])
                    old = self.params['umbral_poda']
                    self.params['umbral_poda'] = round(old + gamma * (p10 - old), 4)
                    if abs(self.params['umbral_poda'] - old) > 0.001:
                        ajustes['umbral_poda'] = {'old': old, 'new': self.params['umbral_poda'],
                                                  'razon': f'p10={p10:.4f}'}
        except Exception:
            pass

        # 3. Ajustar gamma propio (meta-adaptacion)
        n_ajustes = len(ajustes)
        if n_ajustes > 2:
            self.params['gamma_adaptacion'] = max(0.01, gamma * 0.9)
            ajustes['gamma'] = {'old': gamma, 'new': self.params['gamma_adaptacion'],
                                'razon': f'{n_ajustes} ajustes grandes'}
        elif n_ajustes == 0:
            self.params['gamma_adaptacion'] = min(0.5, gamma * 1.1)

        # Log ajustes
        if ajustes:
            from .mejora_continua import log_gestor
            log_gestor('auto_ajuste', {
                'ciclo': self.ciclo_n,
                'ajustes': ajustes,
                'params_actuales': dict(self.params),
            }, nivel='auto', conn=conn)

        return {
            'ajustes_realizados': len(ajustes),
            'detalle': ajustes,
            'params_actuales': dict(self.params),
        }

    def obtener_salud(self, conn=None) -> dict:
        """Estado completo de la Matriz para el endpoint GET /gestor/salud."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(DISTINCT celda_objetivo) FROM datapoints_efectividad
                    WHERE calibrado = true
                """)
                celdas_con_datos = cur.fetchone()[0]

                cur.execute("""
                    SELECT nivel, COUNT(*) FROM preguntas_matriz
                    GROUP BY nivel
                """)
                preguntas_por_nivel = {r[0] or 'sin_nivel': r[1] for r in cur.fetchall()}

                cur.execute("""
                    SELECT rol, modelo FROM config_modelos WHERE activo = true
                """)
                modelos_activos = [{'rol': r[0], 'modelo': r[1]} for r in cur.fetchall()]

                cur.execute("""
                    SELECT COUNT(*) FROM programas_compilados WHERE activo = true
                """)
                programas_activos = cur.fetchone()[0]

                cur.execute("""
                    SELECT detalle, created_at FROM log_gestor
                    WHERE accion = 'loop_completo'
                    ORDER BY created_at DESC LIMIT 1
                """)
                ultimo_loop = cur.fetchone()

                cur.execute("SELECT COUNT(*) FROM datapoints_efectividad WHERE calibrado = true")
                total_datapoints = cur.fetchone()[0]

            return {
                'celdas_totales': 21,  # 3 lentes x 7 funciones
                'celdas_con_datos': celdas_con_datos,
                'celdas_vacias': 21 - celdas_con_datos,
                'preguntas_por_nivel': preguntas_por_nivel,
                'modelos_activos': modelos_activos,
                'programas_activos': programas_activos,
                'total_datapoints': total_datapoints,
                'ultimo_loop': {
                    'detalle': ultimo_loop[0] if ultimo_loop else None,
                    'timestamp': str(ultimo_loop[1]) if ultimo_loop else None,
                },
                'parametros_gamc': dict(self.params),
                'ciclo_actual': self.ciclo_n,
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)


# Instancia global del Gestor
_gestor_gamc = None


def get_gestor() -> GestorGAMC:
    """Obtener instancia singleton del Gestor GAMC."""
    global _gestor_gamc
    if _gestor_gamc is None:
        _gestor_gamc = GestorGAMC()
    return _gestor_gamc
