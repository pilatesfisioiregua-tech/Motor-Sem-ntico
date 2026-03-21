"""Tests Reactor v4 — Telemetry to Observations.

Tests:
  1. test_observar_detects_gap_persistente
  2. test_observar_detects_coste_anomalo
  3. test_observar_detects_patron_exitoso
  4. test_generar_preguntas_creates_candidatas
  5. test_estado_returns_breakdown
"""

import os
import sys
import json
import uuid
import pytest
from datetime import datetime, timezone, timedelta

# Add agent/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _get_conn():
    """Get a DB connection for tests."""
    from core.db_pool import get_conn
    conn = get_conn()
    if not conn:
        pytest.skip("No DB connection available")
    return conn


def _cleanup(conn, test_consumidor):
    """Clean up test data."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM observaciones_reactor WHERE consumidor = %s",
                [test_consumidor])
            cur.execute(
                "DELETE FROM observaciones_reactor WHERE consumidor = 'sistema' "
                "AND tipo_dato LIKE 'rv4:%%' AND dato::text LIKE %s",
                [f'%{test_consumidor}%'])
            cur.execute(
                "DELETE FROM datapoints_efectividad WHERE consumidor = %s",
                [test_consumidor])
            cur.execute(
                "DELETE FROM ejecuciones WHERE contexto = %s",
                [test_consumidor])
            cur.execute(
                "DELETE FROM preguntas_matriz WHERE id LIKE %s",
                [f'%rv4test%'])
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass


class TestReactorV4Observar:
    """Tests para observar()."""

    def test_observar_detects_gap_persistente(self):
        """Insert 3+ datapoints con gap_post > 0.5 para misma celda → detecta gap."""
        conn = _get_conn()
        test_id = f"rv4test_{uuid.uuid4().hex[:8]}"
        try:
            _cleanup(conn, test_id)

            # Insert 3 datapoints con gap alto
            with conn.cursor() as cur:
                for i in range(3):
                    cur.execute("""
                        INSERT INTO datapoints_efectividad
                            (pregunta_id, consumidor, celda_objetivo,
                             gap_pre, gap_post, tasa_cierre, calibrado, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, true, NOW() - INTERVAL '5 minutes')
                    """, [f"p_{test_id}_{i}", test_id, 'CaptarxSalud',
                          0.9, 0.7, 0.22])
            conn.commit()

            from core.reactor_v4 import ReactorV4
            rv4 = ReactorV4()
            rv4.last_run = datetime.now(timezone.utc) - timedelta(hours=1)
            result = rv4.observar(conn=conn)

            assert 'error' not in result, f"Error: {result.get('error')}"
            assert result['observaciones_generadas'] > 0
            assert 'rv4:gap_persistente' in result.get('por_tipo', {})

        finally:
            _cleanup(conn, test_id)
            from core.db_pool import put_conn
            put_conn(conn)

    def test_observar_detects_coste_anomalo(self):
        """Insert ejecucion con coste > 2x mean → detecta anomalía."""
        conn = _get_conn()
        test_id = f"rv4test_{uuid.uuid4().hex[:8]}"
        try:
            _cleanup(conn, test_id)

            with conn.cursor() as cur:
                # 3 ejecuciones normales
                for i in range(3):
                    cur.execute("""
                        INSERT INTO ejecuciones
                            (input, contexto, modo, algoritmo_usado, resultado,
                             coste_usd, tiempo_s, score_calidad)
                        VALUES (%s, %s, 'analisis', %s::jsonb, %s::jsonb,
                                %s, 1.0, 0.7)
                    """, [f"test input {i}", test_id,
                          json.dumps({'inteligencias': ['INT-01']}),
                          json.dumps({'n_hallazgos': 1}),
                          0.10])

                # 1 ejecucion cara (10x)
                cur.execute("""
                    INSERT INTO ejecuciones
                        (input, contexto, modo, algoritmo_usado, resultado,
                         coste_usd, tiempo_s, score_calidad)
                    VALUES (%s, %s, 'analisis', %s::jsonb, %s::jsonb,
                            %s, 5.0, 0.5)
                """, [f"test input costly", test_id,
                      json.dumps({'inteligencias': ['INT-01']}),
                      json.dumps({'n_hallazgos': 1}),
                      1.50])
            conn.commit()

            from core.reactor_v4 import ReactorV4
            rv4 = ReactorV4()
            rv4.last_run = datetime.now(timezone.utc) - timedelta(hours=1)
            result = rv4.observar(conn=conn)

            assert 'error' not in result, f"Error: {result.get('error')}"
            assert result['observaciones_generadas'] > 0
            assert 'rv4:coste_anomalo' in result.get('por_tipo', {})

        finally:
            _cleanup(conn, test_id)
            from core.db_pool import put_conn
            put_conn(conn)

    def test_observar_detects_patron_exitoso(self):
        """Insert datapoint con alta tasa_cierre → detecta patrón exitoso."""
        conn = _get_conn()
        test_id = f"rv4test_{uuid.uuid4().hex[:8]}"
        try:
            _cleanup(conn, test_id)

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO datapoints_efectividad
                        (pregunta_id, consumidor, celda_objetivo,
                         gap_pre, gap_post, tasa_cierre, calibrado, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, true, NOW() - INTERVAL '5 minutes')
                """, [f"p_{test_id}_exit", test_id, 'DepurarxSentido',
                      0.8, 0.2, 0.75])
            conn.commit()

            from core.reactor_v4 import ReactorV4
            rv4 = ReactorV4()
            rv4.last_run = datetime.now(timezone.utc) - timedelta(hours=1)
            result = rv4.observar(conn=conn)

            assert 'error' not in result, f"Error: {result.get('error')}"
            assert result['observaciones_generadas'] > 0
            assert 'rv4:patron_exitoso' in result.get('por_tipo', {})

        finally:
            _cleanup(conn, test_id)
            from core.db_pool import put_conn
            put_conn(conn)


class TestReactorV4Generar:
    """Tests para generar_preguntas()."""

    def test_generar_preguntas_creates_candidatas(self):
        """Observar + generar → crea preguntas candidatas."""
        conn = _get_conn()
        test_id = f"rv4test_{uuid.uuid4().hex[:8]}"
        try:
            _cleanup(conn, test_id)

            # Insert datapoints para trigger gap_persistente
            with conn.cursor() as cur:
                for i in range(3):
                    cur.execute("""
                        INSERT INTO datapoints_efectividad
                            (pregunta_id, consumidor, celda_objetivo,
                             gap_pre, gap_post, tasa_cierre, calibrado, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, true, NOW() - INTERVAL '5 minutes')
                    """, [f"p_{test_id}_{i}", test_id, 'ConservarxSalud',
                          0.9, 0.7, 0.22])
            conn.commit()

            from core.reactor_v4 import ReactorV4
            rv4 = ReactorV4()
            rv4.last_run = datetime.now(timezone.utc) - timedelta(hours=1)

            # Observar primero
            obs_result = rv4.observar(conn=conn)
            assert obs_result.get('observaciones_generadas', 0) > 0

            # Generar preguntas
            gen_result = rv4.generar_preguntas(conn=conn)
            assert 'error' not in gen_result, f"Error: {gen_result.get('error')}"
            assert gen_result['preguntas_generadas'] > 0
            assert gen_result['observaciones_procesadas'] > 0

            # Verificar que se crearon en preguntas_matriz
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM preguntas_matriz
                    WHERE nivel = 'candidata' AND funcion = 'Conservar'
                      AND lente = 'Salud'
                      AND created_at > NOW() - INTERVAL '1 minute'
                """)
                n = cur.fetchone()[0]
                assert n > 0, "No se crearon preguntas candidatas"

        finally:
            _cleanup(conn, test_id)
            from core.db_pool import put_conn
            put_conn(conn)


class TestReactorV4Estado:
    """Tests para estado()."""

    def test_estado_returns_breakdown(self):
        """estado() devuelve estructura correcta."""
        conn = _get_conn()
        try:
            from core.reactor_v4 import ReactorV4
            rv4 = ReactorV4()
            result = rv4.estado(conn=conn)

            assert 'error' not in result or 'total_observaciones' in result
            assert 'total_observaciones' in result
            assert 'breakdown' in result
            assert isinstance(result['breakdown'], list)

        finally:
            from core.db_pool import put_conn
            put_conn(conn)
