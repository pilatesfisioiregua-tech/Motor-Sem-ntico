"""Reactor v4 — Telemetry to Observations.

Lee telemetria real (ejecuciones, datapoints, señales) y genera observaciones
estructuradas en observaciones_reactor. Luego genera preguntas candidatas
desde templates (zero LLM cost).
"""

import json
import uuid
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# 18 inteligencias canónicas
ALL_INTELIGENCIAS = [f"INT-{str(i).zfill(2)}" for i in range(1, 19)]


class ReactorV4:
    """Genera observaciones desde telemetría y preguntas desde templates."""

    def __init__(self):
        self.last_run = datetime.now(timezone.utc) - timedelta(hours=1)

    # ------------------------------------------------------------------
    # observar: lee telemetría, detecta patrones, inserta observaciones
    # ------------------------------------------------------------------

    def observar(self, conn=None) -> dict:
        """Pure code, zero LLM calls. Detecta patrones en telemetría."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            with conn.cursor() as cur:
                # 1. Ejecuciones recientes
                cur.execute("""
                    SELECT id, contexto, modo, algoritmo_usado, coste_usd,
                           score_calidad, created_at
                    FROM ejecuciones
                    WHERE created_at > %s
                    ORDER BY created_at DESC
                """, [self.last_run])
                cols_ej = ['id', 'contexto', 'modo', 'algoritmo_usado',
                           'coste_usd', 'score_calidad', 'created_at']
                ejecuciones = [dict(zip(cols_ej, r)) for r in cur.fetchall()]

                # 2. Datapoints calibrados recientes
                cur.execute("""
                    SELECT pregunta_id, consumidor, celda_objetivo,
                           gap_pre, gap_post, tasa_cierre, timestamp
                    FROM datapoints_efectividad
                    WHERE calibrado = true AND timestamp > %s
                    ORDER BY timestamp DESC
                """, [self.last_run])
                cols_dp = ['pregunta_id', 'consumidor', 'celda_objetivo',
                           'gap_pre', 'gap_post', 'tasa_cierre', 'timestamp']
                datapoints = [dict(zip(cols_dp, r)) for r in cur.fetchall()]

                # 3. Señales no resueltas
                cur.execute("""
                    SELECT id, tipo, severidad, mensaje, datos, created_at
                    FROM señales
                    WHERE resuelta = false
                    ORDER BY created_at DESC
                """)
                cols_s = ['id', 'tipo', 'severidad', 'mensaje', 'datos', 'created_at']
                señales = [dict(zip(cols_s, r)) for r in cur.fetchall()]

            # 4. Ejecutar 5 detecciones
            obs_gap = self._detectar_gap_persistente(datapoints)
            obs_int = self._detectar_int_infrautilizada(ejecuciones)
            obs_coste = self._detectar_coste_anomalo(ejecuciones)
            obs_score = self._detectar_score_bajo(ejecuciones)
            obs_exito = self._detectar_patron_exitoso(datapoints)

            todas = obs_gap + obs_int + obs_coste + obs_score + obs_exito

            # 5. INSERT observaciones
            insertadas = 0
            with conn.cursor() as cur:
                for obs in todas:
                    obs_id = f"rv4_{uuid.uuid4().hex[:12]}"
                    cur.execute("""
                        INSERT INTO observaciones_reactor
                            (id, consumidor, tipo_dato, dato, celdas_detectadas,
                             celdas_gap, procesado)
                        VALUES (%s, %s, %s, %s::jsonb, %s, %s, false)
                    """, [
                        obs_id,
                        obs.get('consumidor', 'sistema'),
                        obs['tipo_dato'],
                        json.dumps(obs.get('dato', {}), default=str),
                        obs.get('celdas_detectadas'),
                        obs.get('celdas_gap'),
                    ])
                    insertadas += 1
            conn.commit()

            # 6. Actualizar last_run
            self.last_run = datetime.now(timezone.utc)

            por_tipo = {}
            for obs in todas:
                t = obs['tipo_dato']
                por_tipo[t] = por_tipo.get(t, 0) + 1

            return {
                'observaciones_generadas': insertadas,
                'por_tipo': por_tipo,
                'telemetria': {
                    'ejecuciones': len(ejecuciones),
                    'datapoints': len(datapoints),
                    'señales': len(señales),
                },
            }

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"ReactorV4.observar error: {e}")
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    # ------------------------------------------------------------------
    # Detecciones
    # ------------------------------------------------------------------

    def _detectar_gap_persistente(self, datapoints: list) -> list:
        """Celda con avg gap_post > 0.5 en 3+ datapoints."""
        from collections import defaultdict
        por_celda = defaultdict(list)
        for dp in datapoints:
            celda = dp.get('celda_objetivo')
            if celda and dp.get('gap_post') is not None:
                por_celda[(dp.get('consumidor', 'sistema'), celda)].append(
                    float(dp['gap_post']))

        obs = []
        for (consumidor, celda), gaps in por_celda.items():
            if len(gaps) >= 3:
                avg = sum(gaps) / len(gaps)
                if avg > 0.5:
                    obs.append({
                        'tipo_dato': 'rv4:gap_persistente',
                        'consumidor': consumidor,
                        'dato': {
                            'celda': celda,
                            'avg_gap_post': round(avg, 4),
                            'n_datapoints': len(gaps),
                        },
                        'celdas_detectadas': [celda],
                        'celdas_gap': [celda],
                    })
        return obs

    def _detectar_int_infrautilizada(self, ejecuciones: list) -> list:
        """Inteligencia no presente en últimas 10 ejecuciones."""
        usadas = set()
        ultimas = ejecuciones[:10]
        for ej in ultimas:
            algo = ej.get('algoritmo_usado')
            if isinstance(algo, str):
                try:
                    algo = json.loads(algo)
                except Exception:
                    algo = {}
            if isinstance(algo, dict):
                for int_id in algo.get('inteligencias', []):
                    usadas.add(int_id)

        no_usadas = [i for i in ALL_INTELIGENCIAS if i not in usadas]
        obs = []
        if no_usadas and len(ultimas) >= 5:
            obs.append({
                'tipo_dato': 'rv4:int_infrautilizada',
                'consumidor': 'sistema',
                'dato': {
                    'inteligencias_no_usadas': no_usadas,
                    'n_ejecuciones_analizadas': len(ultimas),
                },
                'celdas_detectadas': None,
                'celdas_gap': None,
            })
        return obs

    def _detectar_coste_anomalo(self, ejecuciones: list) -> list:
        """Ejecución con coste_usd > 2x promedio."""
        costes = [float(ej['coste_usd']) for ej in ejecuciones
                  if ej.get('coste_usd') and float(ej['coste_usd']) > 0]
        if len(costes) < 2:
            return []

        avg = sum(costes) / len(costes)
        obs = []
        for ej in ejecuciones:
            c = float(ej['coste_usd']) if ej.get('coste_usd') else 0
            if c > avg * 2 and avg > 0:
                obs.append({
                    'tipo_dato': 'rv4:coste_anomalo',
                    'consumidor': 'sistema',
                    'dato': {
                        'ejecucion_id': str(ej['id']),
                        'coste_usd': round(c, 6),
                        'avg_coste': round(avg, 6),
                        'ratio': round(c / avg, 2),
                    },
                    'celdas_detectadas': None,
                    'celdas_gap': None,
                })
        return obs

    def _detectar_score_bajo(self, ejecuciones: list) -> list:
        """Ejecución con score_calidad < 0.3."""
        obs = []
        for ej in ejecuciones:
            score = ej.get('score_calidad')
            if score is not None and float(score) < 0.3:
                obs.append({
                    'tipo_dato': 'rv4:score_bajo',
                    'consumidor': 'sistema',
                    'dato': {
                        'ejecucion_id': str(ej['id']),
                        'score_calidad': round(float(score), 4),
                        'modo': ej.get('modo'),
                    },
                    'celdas_detectadas': None,
                    'celdas_gap': None,
                })
        return obs

    def _detectar_patron_exitoso(self, datapoints: list) -> list:
        """Datapoint con tasa_cierre > 0.6 (gap cerrado > 0.3)."""
        obs = []
        for dp in datapoints:
            tasa = dp.get('tasa_cierre')
            gap_pre = dp.get('gap_pre')
            gap_post = dp.get('gap_post')
            if (tasa is not None and float(tasa) > 0.6
                    and gap_pre is not None and gap_post is not None
                    and (float(gap_pre) - float(gap_post)) > 0.3):
                celda = dp.get('celda_objetivo')
                obs.append({
                    'tipo_dato': 'rv4:patron_exitoso',
                    'consumidor': dp.get('consumidor', 'sistema'),
                    'dato': {
                        'celda': celda,
                        'tasa_cierre': round(float(tasa), 4),
                        'gap_pre': round(float(gap_pre), 4),
                        'gap_post': round(float(gap_post), 4),
                        'pregunta_id': dp.get('pregunta_id'),
                    },
                    'celdas_detectadas': [celda] if celda else None,
                    'celdas_gap': [celda] if celda else None,
                })
        return obs

    # ------------------------------------------------------------------
    # generar_preguntas: template-based, zero LLM
    # ------------------------------------------------------------------

    def generar_preguntas(self, conn=None) -> dict:
        """Genera preguntas candidatas desde observaciones no procesadas."""
        from .reactor_vn import TEMPLATES_FUNCION, TEMPLATES_LENTE

        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            with conn.cursor() as cur:
                # 1. Observaciones no procesadas de rv4
                cur.execute("""
                    SELECT id, consumidor, tipo_dato, dato, celdas_detectadas,
                           celdas_gap
                    FROM observaciones_reactor
                    WHERE procesado = false AND tipo_dato LIKE 'rv4:%%'
                    ORDER BY created_at ASC
                """)
                cols = ['id', 'consumidor', 'tipo_dato', 'dato',
                        'celdas_detectadas', 'celdas_gap']
                observaciones = [dict(zip(cols, r)) for r in cur.fetchall()]

            preguntas_generadas = 0
            obs_procesadas = 0

            for obs in observaciones:
                dato = obs['dato']
                if isinstance(dato, str):
                    try:
                        dato = json.loads(dato)
                    except Exception:
                        dato = {}

                # Extraer celda
                celdas = obs.get('celdas_gap') or obs.get('celdas_detectadas') or []
                if isinstance(dato, dict) and 'celda' in dato:
                    celdas = [dato['celda']]

                if not celdas:
                    # Sin celda: marcar procesada sin generar pregunta
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE observaciones_reactor
                            SET procesado = true
                            WHERE id = %s
                        """, [obs['id']])
                    obs_procesadas += 1
                    continue

                celda = celdas[0]
                parts = celda.split('x') if celda else []
                funcion = parts[0] if len(parts) > 0 else 'Conservar'
                lente = parts[1] if len(parts) > 1 else 'Salud'

                # Elegir inteligencia desde contexto o mapping
                int_id = self._inteligencia_para_obs(obs, funcion, lente, conn)

                # Generar 1-3 preguntas desde templates
                templates = TEMPLATES_FUNCION.get(funcion, [])
                perspectiva = TEMPLATES_LENTE.get(lente, '')
                n_gen = min(len(templates), 3)

                pregunta_ids = []
                with conn.cursor() as cur:
                    for tmpl in templates[:n_gen]:
                        texto = tmpl.format(
                            contexto='este sistema',
                            recurso='atención',
                        )
                        texto_full = f"{texto} ({perspectiva})"
                        pregunta_id = (
                            f"{int_id}_{funcion[0]}_{lente[0]}_"
                            f"{uuid.uuid4().hex[:6]}"
                        )
                        try:
                            cur.execute("""
                                INSERT INTO preguntas_matriz
                                    (id, inteligencia, lente, funcion, texto, nivel)
                                VALUES (%s, %s, %s, %s, %s, 'candidata')
                                ON CONFLICT (id) DO NOTHING
                            """, [pregunta_id, int_id, lente, funcion, texto_full])
                            if cur.rowcount > 0:
                                preguntas_generadas += 1
                                pregunta_ids.append(pregunta_id)
                        except Exception:
                            pass

                    # Marcar observación procesada
                    first_pid = pregunta_ids[0] if pregunta_ids else None
                    cur.execute("""
                        UPDATE observaciones_reactor
                        SET procesado = true, pregunta_generada_id = %s
                        WHERE id = %s
                    """, [first_pid, obs['id']])
                    obs_procesadas += 1

            conn.commit()
            return {
                'preguntas_generadas': preguntas_generadas,
                'observaciones_procesadas': obs_procesadas,
            }

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"ReactorV4.generar_preguntas error: {e}")
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def _inteligencia_para_obs(self, obs: dict, funcion: str, lente: str,
                               conn) -> str:
        """Elige inteligencia relevante para la observación."""
        # Mapeo función → inteligencia principal
        mapa = {
            'Conservar': 'INT-01',
            'Captar': 'INT-06',
            'Depurar': 'INT-02',
            'Distribuir': 'INT-05',
            'Frontera': 'INT-09',
            'Adaptar': 'INT-08',
            'Replicar': 'INT-13',
        }

        # Si la observación tiene inteligencias infrautilizadas, usar la primera
        dato = obs.get('dato', {})
        if isinstance(dato, str):
            try:
                dato = json.loads(dato)
            except Exception:
                dato = {}
        if isinstance(dato, dict):
            no_usadas = dato.get('inteligencias_no_usadas', [])
            if no_usadas:
                return no_usadas[0]

        return mapa.get(funcion, 'INT-01')

    # ------------------------------------------------------------------
    # estado: read-only breakdown
    # ------------------------------------------------------------------

    def estado(self, conn=None) -> dict:
        """Breakdown de observaciones por tipo_dato y procesado."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT tipo_dato,
                           COUNT(*) as total,
                           COUNT(*) FILTER (WHERE procesado) as procesadas,
                           COUNT(*) FILTER (WHERE NOT procesado) as pendientes
                    FROM observaciones_reactor
                    GROUP BY tipo_dato
                    ORDER BY tipo_dato
                """)
                breakdown = []
                for row in cur.fetchall():
                    breakdown.append({
                        'tipo_dato': row[0],
                        'total': row[1],
                        'procesadas': row[2],
                        'pendientes': row[3],
                    })

                cur.execute("SELECT COUNT(*) FROM observaciones_reactor")
                total = cur.fetchone()[0]

            return {
                'total_observaciones': total,
                'breakdown': breakdown,
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)


# Singleton
_reactor_v4 = None


def get_reactor_v4() -> ReactorV4:
    global _reactor_v4
    if _reactor_v4 is None:
        _reactor_v4 = ReactorV4()
    return _reactor_v4
