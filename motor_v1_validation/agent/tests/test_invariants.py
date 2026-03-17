"""Test de invariantes del sistema — SN-17.

Patron Property-Based Testing (#60688): tests de propiedades, no de valores.
Patron Invariant Checking (#60689): verificar invariantes del sistema.

Invariantes:
1. Todo programa generado satisface las 13 reglas
2. PID anti-windup: I nunca supera [-10, 10]
3. Lyapunov: repertorio no encoge > 10% por ciclo
4. FrozenPrograma es inmutable
5. Scheduler adapta intervalos correctamente
6. Consistencia cross-table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_manifold_genera_valido() -> dict:
    """Invariante 1: Todo programa generado por Manifold satisface 13 reglas."""
    from core.reglas_compilador import get_manifold

    manifold = get_manifold()
    modos = ['analisis', 'conversacion', 'generacion', 'confrontacion']

    resultados = []
    for modo in modos:
        gradientes = {'top_gaps': [('ConservarxSalud', 0.8), ('CaptarxSentido', 0.7)]}
        programa = manifold.generar(gradientes, modo=modo)
        valido, violaciones = manifold.validar(programa)
        resultados.append({
            'modo': modo,
            'valido': valido,
            'violaciones': len(violaciones),
        })

    all_valid = all(r['valido'] for r in resultados)
    return {
        'invariante': 'manifold_genera_valido',
        'pasa': all_valid,
        'detalle': resultados,
    }


def test_pid_anti_windup() -> dict:
    """Invariante 2: I_anti_windup nunca supera [-10, 10]."""
    from core.registrador import computar_señales_pid, obtener_señales_todas_celdas

    señales = obtener_señales_todas_celdas()
    violaciones = []

    for celda, s in señales.items():
        I = s.get('I_anti_windup', 0)
        if abs(I) > 10:
            violaciones.append({'celda': celda, 'I': I})

    return {
        'invariante': 'pid_anti_windup',
        'pasa': len(violaciones) == 0,
        'celdas_verificadas': len(señales),
        'violaciones': violaciones,
    }


def test_lyapunov_estabilidad() -> dict:
    """Invariante 3: Repertorio no encoge > 10% por ciclo."""
    from core.db_pool import get_conn, put_conn

    conn = get_conn()
    if not conn:
        return {'invariante': 'lyapunov', 'pasa': None, 'error': 'no_db'}

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM preguntas_matriz
                WHERE nivel NOT IN ('podada', 'obsoleta', 'expirada')
            """)
            activas = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM preguntas_matriz")
            total = cur.fetchone()[0]

        ratio = activas / total if total > 0 else 1.0

        return {
            'invariante': 'lyapunov_estabilidad',
            'pasa': ratio >= 0.90,
            'activas': activas,
            'total': total,
            'ratio': round(ratio, 4),
        }
    finally:
        put_conn(conn)


def test_frozen_programa_inmutable() -> dict:
    """Invariante 4: FrozenPrograma es inmutable."""
    from core.motor_vn import FrozenPrograma
    import time as t

    programa = FrozenPrograma(
        pasos=(('test', 'paso'),),
        inteligencias=frozenset(['INT-01']),
        modo='test',
        tier=1,
        profundidad=1,
        alpha=1.0,
        timestamp=t.time(),
    )

    try:
        programa.modo = 'modificado'
        inmutable = False
    except (AttributeError, TypeError, Exception):
        inmutable = True

    return {
        'invariante': 'frozen_programa_inmutable',
        'pasa': inmutable,
    }


def test_scheduler_adapta_intervalo() -> dict:
    """Invariante 5: Scheduler calcula intervalos correctos."""
    from core.gestor_scheduler import GestorScheduler

    scheduler = GestorScheduler()

    # Sin datos -> 24h
    assert scheduler.calcular_proximo_intervalo() == 24.0

    # Delta negativo -> 1h
    scheduler.flywheel_history = [(0, 0.1, -0.1)]
    intervalo_neg = scheduler.calcular_proximo_intervalo()

    # Delta positivo alto -> < 24h
    scheduler.flywheel_history = [(0, 0.1, 0.15)]
    intervalo_pos = scheduler.calcular_proximo_intervalo()

    return {
        'invariante': 'scheduler_intervalos',
        'pasa': intervalo_neg == 1.0 and intervalo_pos < 24.0,
        'delta_negativo_intervalo': intervalo_neg,
        'delta_positivo_intervalo': intervalo_pos,
    }


def test_consistencia_cross_table() -> dict:
    """Invariante 6: Tablas estan sincronizadas."""
    from core.propagador import get_propagador

    propagador = get_propagador()
    checks = propagador.verificar_consistencia()

    return {
        'invariante': 'consistencia_cross_table',
        'pasa': checks.get('consistente', False),
        'checks': checks,
    }


def test_circuit_breaker() -> dict:
    """Invariante 7: Circuit breaker se abre tras N fallos."""
    from core.monitoring import CircuitBreaker

    cb = CircuitBreaker(umbral_fallos=3, timeout_s=1)

    # 3 fallos -> OPEN
    for _ in range(3):
        cb.registrar_fallo('test_modelo')

    estado = cb._get_estado('test_modelo')
    abierto = estado['estado'] == 'OPEN'
    no_puede = not cb.puede_llamar('test_modelo')

    return {
        'invariante': 'circuit_breaker',
        'pasa': abierto and no_puede,
        'estado_tras_3_fallos': estado['estado'],
    }


def run_all_invariants() -> dict:
    """Ejecutar todos los invariantes y retornar resumen."""
    tests = [
        test_manifold_genera_valido,
        test_pid_anti_windup,
        test_lyapunov_estabilidad,
        test_frozen_programa_inmutable,
        test_scheduler_adapta_intervalo,
        test_consistencia_cross_table,
        test_circuit_breaker,
    ]

    resultados = []
    for test_fn in tests:
        try:
            r = test_fn()
            resultados.append(r)
        except Exception as e:
            resultados.append({
                'invariante': test_fn.__name__.replace('test_', ''),
                'pasa': False,
                'error': str(e),
            })

    n_pass = sum(1 for r in resultados if r.get('pasa') is True)
    n_fail = sum(1 for r in resultados if r.get('pasa') is False)
    n_skip = sum(1 for r in resultados if r.get('pasa') is None)

    return {
        'total': len(resultados),
        'pass': n_pass,
        'fail': n_fail,
        'skip': n_skip,
        'all_pass': n_fail == 0,
        'resultados': resultados,
    }


if __name__ == '__main__':
    result = run_all_invariants()
    import json
    print(json.dumps(result, indent=2, default=str))
