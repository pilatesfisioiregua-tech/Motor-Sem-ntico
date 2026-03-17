"""Registrador PID — feedback loop del Motor al Gestor.

Patron aplicado: PID Control (knowledge_base #83757)
Cada registro computa 3 señales de control por celda:
  P = gap_post (error actual)
  I = SUM(gap_post) over last N (error acumulado, cronico)
  D = gap_post - gap_pre (tendencia, mejorando o empeorando)

Anti-patrones evitados:
  - Anti-windup: I clamped a [-10, 10]
  - Derivative filter: D suavizado con media movil 5 puntos
  - Config ajustable: Kp/Ki/Kd no hardcoded

Fase 3 Fix 2: Evaluador real de hallazgos — score calidad 0-1 via LLM.
"""

import json
import re
import uuid
import time
from datetime import datetime, timezone
from typing import Optional


# Config PID ajustable (el Gestor GAMC puede modificar estos en SN-07)
PID_CONFIG = {
    'Kp': 1.0,            # ganancia proporcional
    'Ki': 0.1,            # ganancia integral
    'Kd': 0.05,           # ganancia derivativa
    'ventana': 50,        # ultimos N datapoints para I y D
    'I_clamp': 10.0,      # anti-windup: |I| <= I_clamp
    'D_filter_n': 5,      # media movil para suavizar D
}


def _evaluar_hallazgo(hallazgo: str, celda: str, input_texto: str) -> float:
    """Evalua calidad REAL de un hallazgo via LLM (Fase 3 Fix 2).

    Score 0-1:
      0.0 = generico, aplicable a cualquier negocio
      0.3 = relevante al dominio pero obvio
      0.6 = especifico al caso con insight real
      0.9 = accionable, no obvio, cambia una decision

    Coste: ~$0.0005 por hallazgo (MiMo, ~200 tokens)
    """
    prompt = f"""Evalúa la calidad de este hallazgo para un caso concreto.

Caso (resumen): {input_texto[:300]}
Celda de la Matriz: {celda}
Hallazgo: {hallazgo[:500]}

Puntúa de 0.0 a 1.0:
- 0.0 = genérico, podría aplicar a cualquier negocio ("es importante tener clientes")
- 0.3 = relevante pero obvio ("un estudio de pilates necesita retener clientes")
- 0.6 = específico al caso con insight real ("las cancelaciones de último momento sugieren problema de compromiso, no de precio")
- 0.9 = accionable y no obvio ("implementar lista de espera que auto-rellena cancelaciones reduce pérdida de ingreso a 0")

Responde SOLO con un número decimal entre 0.0 y 1.0. Nada más."""

    try:
        from .api import call_openrouter

        # Modelo de fontanería
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
                finally:
                    put_conn(c)
        except Exception:
            pass

        from .costes import set_call_context
        set_call_context(componente='evaluador', operacion='evaluacion', celda=celda)
        response = call_openrouter(
            messages=[{"role": "user", "content": prompt}],
            model=modelo,
            max_tokens=10,
            temperature=0.0,
        )
        texto = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        match = re.search(r'(\d+\.?\d*)', texto)
        if match:
            return min(1.0, max(0.0, float(match.group(1))))
        return 0.5
    except Exception:
        return 0.5


def registrar_ejecucion(resultado: dict, conn=None) -> dict:
    """Registra datapoint + computa señales PID para la celda.

    Args:
        resultado: dict con campos:
            - pregunta_id: str (id de preguntas_matriz)
            - modelo: str (modelo LLM usado)
            - caso_id: str (id del caso/input)
            - consumidor: str (quien pidio la ejecucion)
            - celda_objetivo: str (formato "FuncionxLente")
            - gap_pre: float (gap antes de la ejecucion)
            - gap_post: float (gap despues) — IGNORED if hallazgos present (Fase 3)
            - hallazgos: list[str] (hallazgos encontrados, opcional)
            - input_texto: str (caso original para evaluador, opcional)
            - latencia_ms: int (tiempo de ejecucion, opcional)
            - tokens: int (tokens consumidos, opcional)
            - coste_usd: float (coste en USD, opcional)
            - operacion: str (tipo de operacion algebraica, opcional)

    Returns:
        dict con señales PID: {P, I, D, I_anti_windup, D_filtrado,
                               tasa_cierre, n_total}
    """
    own_conn = conn is None
    if own_conn:
        from .db_pool import get_conn
        conn = get_conn()
        if not conn:
            return {'error': 'no_db_connection'}

    try:
        pregunta_id = resultado.get('pregunta_id', '')
        modelo = resultado.get('modelo', '')
        caso_id = resultado.get('caso_id', str(uuid.uuid4())[:8])
        consumidor = resultado.get('consumidor', 'motor_vn')
        celda = resultado.get('celda_objetivo', '')
        gap_pre = resultado.get('gap_pre', 0.0)
        operacion = resultado.get('operacion', 'individual')
        hallazgos = resultado.get('hallazgos', [])
        input_texto = resultado.get('input_texto', '')
        latencia_ms = resultado.get('latencia_ms', 0)
        tokens = resultado.get('tokens', 0)
        coste_usd = resultado.get('coste_usd', 0.0)

        # === Fase 3 Fix 2: Evaluar calidad REAL de hallazgos ===
        if hallazgos and input_texto:
            scores = []
            for h in hallazgos[:3]:  # max 3 por celda (controlar coste)
                h_texto = h if isinstance(h, str) else json.dumps(h, default=str)
                score = _evaluar_hallazgo(h_texto, celda, input_texto)
                scores.append(score)

            score_calidad = sum(scores) / len(scores) if scores else 0.5

            # gap_post calibrado por calidad real
            gap_post = round(gap_pre * (1.0 - score_calidad), 4)
            gap_cerrado = max(0, gap_pre - gap_post)
            tasa_cierre = gap_cerrado / gap_pre if gap_pre > 0 else 0.0

            # Telemetria de evaluacion
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO metricas (componente, evento, datos)
                        VALUES ('registrador', 'evaluacion_calidad', %s::jsonb)
                    """, [json.dumps({
                        'celda': celda,
                        'n_hallazgos': len(hallazgos),
                        'n_evaluados': len(scores),
                        'scores': [round(s, 4) for s in scores],
                        'score_medio': round(score_calidad, 4),
                        'gap_pre': gap_pre,
                        'gap_post_calibrado': gap_post,
                        'tasa_cierre_calibrada': round(tasa_cierre, 4),
                    })])
            except Exception:
                pass
        else:
            # Sin hallazgos o sin input_texto — gap no cerrado
            gap_post = resultado.get('gap_post', gap_pre)
            gap_cerrado = max(0, gap_pre - gap_post)
            tasa_cierre = gap_cerrado / gap_pre if gap_pre > 0 else 0.0

        with conn.cursor() as cur:
            # 1. INSERT datapoints_efectividad (calibrado=true for Fase 3 data)
            cur.execute("""
                INSERT INTO datapoints_efectividad
                  (pregunta_id, modelo, caso_id, consumidor, celda_objetivo,
                   gap_pre, gap_post, operacion, calibrado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
            """, [pregunta_id, modelo, caso_id, consumidor, celda,
                  gap_pre, gap_post, operacion])

            # 2. INSERT efectos_matriz (si hay hallazgos)
            ejecucion_id = caso_id
            for hallazgo in hallazgos:
                parts = celda.split('x')
                funcion = parts[0] if len(parts) > 0 else ''
                lente = parts[1] if len(parts) > 1 else ''
                inteligencia = pregunta_id.split('-')[0] + '-' + pregunta_id.split('-')[1] if '-' in pregunta_id else ''

                cur.execute("""
                    INSERT INTO efectos_matriz
                      (ejecucion_id, inteligencia, lente, funcion,
                       hallazgo, grado_antes, grado_despues, gap_cerrado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [ejecucion_id, inteligencia, lente, funcion,
                      hallazgo if isinstance(hallazgo, str) else json.dumps(hallazgo),
                      gap_pre, gap_post, gap_cerrado])

            # 3. INSERT metricas (latencia, tokens, coste)
            if latencia_ms or tokens or coste_usd:
                cur.execute("""
                    INSERT INTO metricas (componente, evento, datos)
                    VALUES ('registrador', 'ejecucion', %s::jsonb)
                """, [json.dumps({
                    'pregunta_id': pregunta_id,
                    'modelo': modelo,
                    'celda': celda,
                    'latencia_ms': latencia_ms,
                    'tokens': tokens,
                    'coste_usd': coste_usd,
                    'tasa_cierre': round(tasa_cierre, 4),
                })])

        conn.commit()

        # 4b. B3: UPDATE incremental celdas_matriz
        try:
            if celda:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE celdas_matriz SET
                            n_datapoints = COALESCE((
                                SELECT COUNT(*) FROM datapoints_efectividad
                                WHERE celda_objetivo = %s
                            ), 0),
                            tasa_media = COALESCE((
                                SELECT AVG(tasa_cierre) FROM datapoints_efectividad
                                WHERE celda_objetivo = %s
                            ), 0.0),
                            grado_actual = LEAST(1.0, 1.0 - COALESCE((
                                SELECT AVG(gap_post) FROM datapoints_efectividad
                                WHERE celda_objetivo = %s
                            ), 0.0)),
                            updated_at = NOW()
                        WHERE id = %s
                    """, [celda, celda, celda, celda])
                conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        # 4. Computar señales PID para la celda
        señales = computar_señales_pid(celda, conn=conn)
        señales['tasa_cierre'] = round(tasa_cierre, 4)

        return señales

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


def registrar_batch(resultados: list, conn=None) -> list:
    """Registra multiples datapoints en una sola transaccion.

    Args:
        resultados: lista de dicts (mismo formato que registrar_ejecucion)

    Returns:
        lista de señales PID por cada registro
    """
    own_conn = conn is None
    if own_conn:
        from .db_pool import get_conn
        conn = get_conn()
        if not conn:
            return [{'error': 'no_db_connection'}]

    señales_list = []
    try:
        for resultado in resultados:
            señales = registrar_ejecucion(resultado, conn=conn)
            señales_list.append(señales)
        return señales_list
    finally:
        if own_conn:
            from .db_pool import put_conn
            put_conn(conn)


def computar_señales_pid(celda: str, ventana: int = None,
                          conn=None) -> dict:
    """Computa señales PID para una celda sobre los ultimos N datapoints.

    Señales:
      P = gap_post del ultimo datapoint (error actual)
      I = SUM(gap_post) over last N, clamped [-I_clamp, I_clamp] (anti-windup)
      D = pendiente de gap_post sobre last N, filtrado con media movil (anti derivative kick)

    Args:
        celda: formato "FuncionxLente"
        ventana: ultimos N datapoints (default: PID_CONFIG['ventana'])

    Returns:
        {P, I, D, I_anti_windup, D_filtrado, n_total, señal_control}
    """
    if ventana is None:
        ventana = PID_CONFIG['ventana']

    own_conn = conn is None
    if own_conn:
        from .db_pool import get_conn
        conn = get_conn()
        if not conn:
            return {'P': 0, 'I': 0, 'D': 0, 'n_total': 0}

    try:
        with conn.cursor() as cur:
            # Obtener ultimos N datapoints ordenados por timestamp
            cur.execute("""
                SELECT gap_pre, gap_post, tasa_cierre
                FROM datapoints_efectividad
                WHERE celda_objetivo = %s AND calibrado = true
                ORDER BY timestamp DESC
                LIMIT %s
            """, [celda, ventana])
            rows = cur.fetchall()

        if not rows:
            return {'P': 0.0, 'I': 0.0, 'D': 0.0,
                    'I_anti_windup': 0.0, 'D_filtrado': 0.0,
                    'n_total': 0, 'señal_control': 0.0}

        n_total = len(rows)
        gaps_post = [r[1] for r in rows]
        gaps_pre = [r[0] for r in rows]

        # P = error actual (ultimo gap_post)
        P = gaps_post[0]

        # I = error acumulado (suma de gaps_post)
        I_raw = sum(gaps_post)
        I_clamp = PID_CONFIG['I_clamp']
        I_anti_windup = max(-I_clamp, min(I_clamp, I_raw))

        # D = tendencia (diferencias gap_post - gap_pre, suavizadas)
        diffs = [post - pre for pre, post in zip(gaps_pre, gaps_post)]
        filter_n = min(PID_CONFIG['D_filter_n'], len(diffs))
        if filter_n > 0:
            D_filtrado = sum(diffs[:filter_n]) / filter_n
        else:
            D_filtrado = 0.0
        D_raw = diffs[0] if diffs else 0.0

        # Señal de control compuesta
        Kp = PID_CONFIG['Kp']
        Ki = PID_CONFIG['Ki']
        Kd = PID_CONFIG['Kd']
        señal_control = Kp * P + Ki * I_anti_windup + Kd * D_filtrado

        return {
            'P': round(P, 4),
            'I': round(I_raw, 4),
            'I_anti_windup': round(I_anti_windup, 4),
            'D': round(D_raw, 4),
            'D_filtrado': round(D_filtrado, 4),
            'n_total': n_total,
            'señal_control': round(señal_control, 4),
        }

    except Exception as e:
        return {'P': 0, 'I': 0, 'D': 0, 'n_total': 0, 'error': str(e)}
    finally:
        if own_conn:
            from .db_pool import put_conn
            put_conn(conn)


def obtener_señales_todas_celdas(conn=None) -> dict:
    """Computa señales PID para todas las celdas con datos.

    Returns:
        dict {celda: {P, I, D, ...}} para cada celda activa
    """
    own_conn = conn is None
    if own_conn:
        from .db_pool import get_conn
        conn = get_conn()
        if not conn:
            return {}

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT celda_objetivo
                FROM datapoints_efectividad
                WHERE celda_objetivo IS NOT NULL AND celda_objetivo != ''
                  AND calibrado = true
            """)
            celdas = [r[0] for r in cur.fetchall()]

        resultado = {}
        for celda in celdas:
            resultado[celda] = computar_señales_pid(celda, conn=conn)
        return resultado

    except Exception:
        return {}
    finally:
        if own_conn:
            from .db_pool import put_conn
            put_conn(conn)