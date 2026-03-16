"""Control financiero — cada llamada LLM registrada con coste real.

Principio: ninguna llamada a un LLM ocurre sin pasar por aqui.
Si no se registra, no existe.
"""

import json

# Precios por modelo ($/1M tokens) — fuente: OpenRouter marzo 2026
PRECIOS = {
    'xiaomi/mimo-v2-flash': {'input': 0.10, 'output': 0.40},
    'xiaomi/mimo-vl-7b-sft': {'input': 0.10, 'output': 0.40},
    'deepseek/deepseek-chat-v3-0324': {'input': 0.27, 'output': 1.10},
    'deepseek/deepseek-chat': {'input': 0.27, 'output': 1.10},
    'deepseek/deepseek-reasoner': {'input': 0.55, 'output': 2.19},
    'cognitivecomputations/cogito-v2-671b': {'input': 0.50, 'output': 1.00},
    'deepcogito/cogito-v2.1-671b': {'input': 0.50, 'output': 1.00},
    'openai/gpt-4o-mini': {'input': 0.15, 'output': 0.60},
    'mistralai/devstral-2512': {'input': 0.20, 'output': 0.60},
    'stepfun/step-3.5-flash': {'input': 1.00, 'output': 3.80},
    'moonshotai/kimi-k2.5': {'input': 2.50, 'output': 7.50},
    'qwen/qwen3-235b': {'input': 0.30, 'output': 1.20},
    'qwen/qwen3-coder-next': {'input': 0.00, 'output': 0.00},
    'minimax/minimax-m2.5': {'input': 0.30, 'output': 0.95},
    'google/gemini-2.5-flash': {'input': 0.15, 'output': 0.60},
    'nvidia/llama-3.3-nemotron-super-49b-v1.5': {'input': 0.12, 'output': 0.30},
    'claude-sonnet-4-6': {'input': 3.00, 'output': 15.00},
    'claude-opus-4-6': {'input': 15.00, 'output': 75.00},
}

PRECIO_DEFAULT = {'input': 1.00, 'output': 3.00}

# Thread-local context for component/consumer tracking
_call_context = {}


def set_call_context(componente: str = None, consumidor: str = None,
                     operacion: str = None, caso_id: str = None, celda: str = None):
    """Set context for the next LLM call(s). Called before LLM calls."""
    if componente:
        _call_context['componente'] = componente
    if consumidor:
        _call_context['consumidor'] = consumidor
    if operacion:
        _call_context['operacion'] = operacion
    if caso_id:
        _call_context['caso_id'] = caso_id
    if celda:
        _call_context['celda'] = celda


def clear_call_context():
    """Clear call context."""
    _call_context.clear()


def get_call_context() -> dict:
    """Get current call context."""
    return dict(_call_context)


def registrar_coste(
    modelo: str,
    tokens_input: int,
    tokens_output: int,
    componente: str = None,
    consumidor: str = None,
    operacion: str = None,
    caso_id: str = None,
    celda: str = None,
    latencia_ms: int = None,
    provider: str = 'openrouter',
    conn=None
) -> dict:
    """Registra el coste de una llamada LLM.

    Returns:
        dict con coste calculado y estado del presupuesto
    """
    # Use context if not explicitly provided
    ctx = get_call_context()
    componente = componente or ctx.get('componente', 'desconocido')
    consumidor = consumidor or ctx.get('consumidor', 'sistema')
    operacion = operacion or ctx.get('operacion')
    caso_id = caso_id or ctx.get('caso_id')
    celda = celda or ctx.get('celda')

    own_conn = conn is None
    if own_conn:
        try:
            from core.db_pool import get_conn
            conn = get_conn()
        except ImportError:
            from .db_pool import get_conn
            conn = get_conn()
        if not conn:
            # Calculate cost even without DB
            precios = PRECIOS.get(modelo, PRECIO_DEFAULT)
            coste_total = (tokens_input / 1_000_000) * precios['input'] + \
                          (tokens_output / 1_000_000) * precios['output']
            return {'coste_total_usd': round(coste_total, 6), 'error': 'no_db'}

    try:
        precios = PRECIOS.get(modelo, PRECIO_DEFAULT)
        coste_input = (tokens_input / 1_000_000) * precios['input']
        coste_output = (tokens_output / 1_000_000) * precios['output']
        coste_total = coste_input + coste_output

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO costes_llm
                    (modelo, provider, componente, consumidor,
                     tokens_input, tokens_output, coste_input_usd, coste_output_usd,
                     operacion, caso_id, celda, latencia_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [modelo, provider, componente, consumidor,
                  tokens_input, tokens_output, coste_input, coste_output,
                  operacion, caso_id, celda, latencia_ms])

            # Check budget
            cur.execute("""
                SELECT p.limite_mensual_usd, p.alerta_al_pct,
                       COALESCE(SUM(c.coste_total_usd), 0) as gastado_mes
                FROM presupuestos p
                LEFT JOIN costes_llm c ON c.consumidor = p.consumidor
                    AND date_trunc('month', c.created_at) = date_trunc('month', now())
                WHERE p.consumidor = %s AND p.activo = true
                GROUP BY p.limite_mensual_usd, p.alerta_al_pct
            """, [consumidor])
            row = cur.fetchone()

            alerta_presupuesto = None
            if row:
                limite, alerta_pct, gastado = row
                pct_usado = (gastado / limite * 100) if limite > 0 else 0
                if pct_usado >= 100:
                    alerta_presupuesto = 'EXCEDIDO'
                elif pct_usado >= alerta_pct:
                    alerta_presupuesto = 'ALERTA'

                if alerta_presupuesto == 'EXCEDIDO':
                    try:
                        from core.telemetria import crear_señal
                        crear_señal('presupuesto', 'critical',
                            f'Presupuesto excedido para {consumidor}: ${gastado:.2f} de ${limite:.2f}',
                            {'consumidor': consumidor, 'gastado': gastado, 'limite': limite},
                            conn)
                    except Exception:
                        pass

        conn.commit()

        return {
            'coste_total_usd': round(coste_total, 6),
            'coste_input_usd': round(coste_input, 6),
            'coste_output_usd': round(coste_output, 6),
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'modelo': modelo,
            'alerta_presupuesto': alerta_presupuesto,
        }

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {'error': str(e), 'coste_total_usd': 0}
    finally:
        if own_conn:
            try:
                from core.db_pool import put_conn
            except ImportError:
                from .db_pool import put_conn
            put_conn(conn)


def resumen_costes(consumidor: str = None, meses: int = 3, conn=None) -> dict:
    """Resumen de costes para el dashboard."""
    own_conn = conn is None
    if own_conn:
        try:
            from core.db_pool import get_conn
            conn = get_conn()
        except ImportError:
            from .db_pool import get_conn
            conn = get_conn()
        if not conn:
            return {'error': 'no_db'}

    try:
        with conn.cursor() as cur:
            resultado = {}

            # Por modelo y mes
            if consumidor:
                cur.execute("""
                    SELECT modelo, date_trunc('month', created_at) as mes,
                           COUNT(*) as llamadas,
                           ROUND(SUM(coste_total_usd)::numeric, 4) as total
                    FROM costes_llm
                    WHERE consumidor = %s
                      AND created_at > now() - make_interval(months => %s)
                    GROUP BY modelo, date_trunc('month', created_at)
                    ORDER BY mes DESC, total DESC
                """, [consumidor, meses])
            else:
                cur.execute("""
                    SELECT modelo, date_trunc('month', created_at) as mes,
                           COUNT(*) as llamadas,
                           ROUND(SUM(coste_total_usd)::numeric, 4) as total
                    FROM costes_llm
                    WHERE created_at > now() - make_interval(months => %s)
                    GROUP BY modelo, date_trunc('month', created_at)
                    ORDER BY mes DESC, total DESC
                """, [meses])

            resultado['por_modelo_mes'] = [
                {'modelo': r[0], 'mes': str(r[1])[:7], 'llamadas': r[2], 'coste': float(r[3])}
                for r in cur.fetchall()
            ]

            # Por consumidor y mes
            cur.execute("""
                SELECT consumidor, date_trunc('month', created_at) as mes,
                       COUNT(*) as llamadas,
                       ROUND(SUM(coste_total_usd)::numeric, 4) as total
                FROM costes_llm
                WHERE created_at > now() - make_interval(months => %s)
                GROUP BY consumidor, date_trunc('month', created_at)
                ORDER BY mes DESC, total DESC
            """, [meses])
            resultado['por_consumidor_mes'] = [
                {'consumidor': r[0], 'mes': str(r[1])[:7], 'llamadas': r[2], 'coste': float(r[3])}
                for r in cur.fetchall()
            ]

            # Por componente y mes
            cur.execute("""
                SELECT componente, date_trunc('month', created_at) as mes,
                       COUNT(*) as llamadas,
                       ROUND(SUM(coste_total_usd)::numeric, 4) as total
                FROM costes_llm
                WHERE created_at > now() - make_interval(months => %s)
                GROUP BY componente, date_trunc('month', created_at)
                ORDER BY mes DESC, total DESC
            """, [meses])
            resultado['por_componente_mes'] = [
                {'componente': r[0], 'mes': str(r[1])[:7], 'llamadas': r[2], 'coste': float(r[3])}
                for r in cur.fetchall()
            ]

            # Resumen 30d
            cur.execute("SELECT * FROM costes_resumen_30d")
            row = cur.fetchone()
            if row:
                resultado['resumen_30d'] = {
                    'total_llamadas': row[0],
                    'modelos_usados': row[1],
                    'consumidores_activos': row[2],
                    'coste_total': float(row[3]) if row[3] else 0,
                    'coste_medio_diario': float(row[4]) if row[4] else 0,
                    'proyeccion_mensual': float(row[5]) if row[5] else 0,
                }
            else:
                resultado['resumen_30d'] = {
                    'total_llamadas': 0, 'modelos_usados': 0,
                    'consumidores_activos': 0, 'coste_total': 0,
                    'coste_medio_diario': 0, 'proyeccion_mensual': 0,
                }

            # Estado presupuestos
            cur.execute("""
                SELECT p.consumidor, p.limite_mensual_usd,
                       COALESCE(SUM(c.coste_total_usd), 0) as gastado
                FROM presupuestos p
                LEFT JOIN costes_llm c ON c.consumidor = p.consumidor
                    AND date_trunc('month', c.created_at) = date_trunc('month', now())
                WHERE p.activo = true
                GROUP BY p.consumidor, p.limite_mensual_usd
                ORDER BY p.consumidor
            """)
            resultado['presupuestos'] = [
                {
                    'consumidor': r[0],
                    'limite': float(r[1]),
                    'gastado': round(float(r[2]), 4),
                    'pct_usado': round(float(r[2]) / float(r[1]) * 100, 1) if r[1] > 0 else 0,
                    'restante': round(float(r[1]) - float(r[2]), 4),
                }
                for r in cur.fetchall()
            ]

            return resultado
    except Exception as e:
        return {'error': str(e)}
    finally:
        if own_conn:
            try:
                from core.db_pool import put_conn
            except ImportError:
                from .db_pool import put_conn
            put_conn(conn)
