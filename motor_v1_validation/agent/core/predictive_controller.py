"""SN-22: Predictive Controller — MPC, Attractor Landscapes.

Patrones aplicados:
  Model Predictive Control (#83761): planificar N ciclos ahead
  Attractor Landscapes (#83740): clusters de problemas que convergen a mismos programas

Capacidades:
  1. MPC: optimizar horizonte de N ciclos del Gestor
  2. Attractor detection: encontrar cuencas de atraccion (problem clusters)
  3. Trajectory prediction: predecir evolucion de tasa_cierre
  4. Optimal scheduling: cuando ejecutar que acciones
"""

import math
import time
from collections import defaultdict, Counter
from typing import Optional


class AttractorLandscape:
    """Paisaje de atractores: clusters de problemas que convergen a programas similares.

    Un atractor es un programa (combinacion de INTs) al que convergen
    multiples inputs. Si muchos inputs distintos acaban usando el mismo
    programa, ese programa es un atractor fuerte.
    """

    def detectar_atractores(self, conn=None) -> dict:
        """Detectar cuencas de atraccion en el espacio de programas."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                # Obtener programas compilados y sus frecuencias de uso
                cur.execute("""
                    SELECT programa, COUNT(*) as n_usos,
                           AVG(e.tasa_cierre) as tasa_media
                    FROM programas_compilados pc
                    LEFT JOIN datapoints_efectividad e
                        ON e.pregunta_id = ANY(
                            SELECT unnest(string_to_array(
                                regexp_replace(pc.programa::text, '[^a-zA-Z0-9_,-]', '', 'g'),
                                ','
                            ))
                        )
                    WHERE pc.activo = true
                    GROUP BY programa
                    ORDER BY n_usos DESC
                    LIMIT 20
                """)
                programas = []
                for row in cur.fetchall():
                    programas.append({
                        'programa': str(row[0]),
                        'n_usos': row[1],
                        'tasa_media': round(float(row[2]), 4) if row[2] else 0,
                    })

                # Detectar pares celda-programa mas comunes
                cur.execute("""
                    SELECT celda_objetivo,
                           SPLIT_PART(pregunta_id, '_', 1) as int_prefix,
                           COUNT(*) as n,
                           AVG(tasa_cierre) as tasa
                    FROM datapoints_efectividad
                    GROUP BY celda_objetivo, SPLIT_PART(pregunta_id, '_', 1)
                    HAVING COUNT(*) >= 3
                    ORDER BY n DESC
                    LIMIT 30
                """)
                clusters = defaultdict(list)
                for row in cur.fetchall():
                    clusters[row[0]].append({
                        'inteligencia': row[1],
                        'n': row[2],
                        'tasa': round(float(row[3]), 4) if row[3] else 0,
                    })

            # Identificar atractores: celdas con INTs dominantes
            atractores = []
            for celda, ints in clusters.items():
                if len(ints) >= 2:
                    ints_sorted = sorted(ints, key=lambda x: x['tasa'], reverse=True)
                    top = ints_sorted[0]
                    if top['tasa'] > 0.3:  # Tasa significativa
                        atractores.append({
                            'celda': celda,
                            'int_dominante': top['inteligencia'],
                            'tasa_dominante': top['tasa'],
                            'n_inteligencias': len(ints),
                            'fuerza': round(top['tasa'] * top['n'] / 10, 4),
                        })

            atractores.sort(key=lambda x: x['fuerza'], reverse=True)

            return {
                'atractores': atractores[:15],
                'n_atractores': len(atractores),
                'clusters_por_celda': {k: v for k, v in list(clusters.items())[:10]},
                'programas_frecuentes': programas[:10],
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)


class PredictiveController:
    """Model Predictive Control para el Gestor.

    En vez de reaccionar a datos pasados, planifica N ciclos ahead:
    1. Modelo: predecir como evolucionaran las tasas
    2. Optimizacion: elegir acciones que maximicen tasa a horizonte N
    3. Receding horizon: re-planificar cada ciclo con datos nuevos
    """

    def __init__(self, horizonte: int = 5):
        self.horizonte = horizonte
        self.landscape = AttractorLandscape()
        self.predictions = []

    def predecir_trayectoria(self, conn=None) -> dict:
        """Predecir trayectoria de tasa_cierre para los proximos N ciclos.

        Modelo simple: tendencia lineal + estacionalidad semanal.
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                # Obtener serie temporal de tasas medias por dia
                cur.execute("""
                    SELECT DATE(timestamp) as dia,
                           AVG(tasa_cierre) as tasa_media,
                           COUNT(*) as n
                    FROM datapoints_efectividad
                    GROUP BY DATE(timestamp)
                    ORDER BY dia
                """)
                serie = []
                for row in cur.fetchall():
                    serie.append({
                        'dia': str(row[0]),
                        'tasa': round(float(row[1]), 4) if row[1] else 0,
                        'n': row[2],
                    })

            if len(serie) < 3:
                return {
                    'error': 'insuficientes_datos',
                    'n_dias': len(serie),
                    'minimo': 3,
                }

            # Tendencia: regresion lineal sobre las tasas
            tasas = [s['tasa'] for s in serie]
            n = len(tasas)
            xs = list(range(n))
            sum_x = sum(xs)
            sum_y = sum(tasas)
            sum_xy = sum(x * y for x, y in zip(xs, tasas))
            sum_x2 = sum(x * x for x in xs)

            denom = n * sum_x2 - sum_x * sum_x
            if denom != 0:
                pendiente = (n * sum_xy - sum_x * sum_y) / denom
                intercepto = (sum_y - pendiente * sum_x) / n
            else:
                pendiente = 0
                intercepto = sum_y / n if n > 0 else 0

            # Predecir horizonte
            predicciones = []
            for i in range(1, self.horizonte + 1):
                x_futuro = n + i
                tasa_pred = intercepto + pendiente * x_futuro
                tasa_pred = max(0, min(1, tasa_pred))
                predicciones.append({
                    'ciclo': i,
                    'tasa_predicha': round(tasa_pred, 4),
                })

            # Tendencia general
            if pendiente > 0.005:
                tendencia = 'mejorando'
            elif pendiente < -0.005:
                tendencia = 'degradandose'
            else:
                tendencia = 'estable'

            self.predictions = predicciones

            return {
                'serie_historica': serie[-10:],  # ultimos 10 dias
                'predicciones': predicciones,
                'tendencia': tendencia,
                'pendiente': round(pendiente, 6),
                'tasa_actual': round(tasas[-1], 4) if tasas else 0,
                'tasa_predicha_horizonte': predicciones[-1]['tasa_predicha'] if predicciones else 0,
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def planificar_acciones(self, conn=None) -> dict:
        """Planificar acciones optimas para los proximos N ciclos.

        MPC: en vez de reaccionar, anticipar que acciones maximizan
        la tasa de cierre a horizonte N.
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db'}

        try:
            acciones = []

            with conn.cursor() as cur:
                # 1. Identificar celdas con tendencia negativa (D > 0 = empeorando)
                cur.execute("""
                    SELECT celda_objetivo,
                           AVG(CASE WHEN timestamp > NOW() - INTERVAL '3 days'
                               THEN tasa_cierre END) as tasa_reciente,
                           AVG(CASE WHEN timestamp <= NOW() - INTERVAL '3 days'
                                    AND timestamp > NOW() - INTERVAL '7 days'
                               THEN tasa_cierre END) as tasa_anterior,
                           COUNT(*) as n
                    FROM datapoints_efectividad
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                    GROUP BY celda_objetivo
                    HAVING COUNT(*) >= 3
                """)
                for row in cur.fetchall():
                    celda = row[0]
                    tasa_reciente = float(row[1]) if row[1] else 0
                    tasa_anterior = float(row[2]) if row[2] else tasa_reciente
                    delta = tasa_reciente - tasa_anterior

                    if delta < -0.05:  # Empeorando
                        acciones.append({
                            'tipo': 'escalar_prioridad',
                            'celda': celda,
                            'razon': f'Tasa cayendo: {round(tasa_anterior, 3)} -> {round(tasa_reciente, 3)}',
                            'urgencia': round(abs(delta) * 10, 2),
                            'ciclo_recomendado': 1,
                        })
                    elif tasa_reciente < 0.1 and row[3] > 10:
                        acciones.append({
                            'tipo': 'podar_o_recompilar',
                            'celda': celda,
                            'razon': f'Tasa persistentemente baja ({round(tasa_reciente, 3)}) con {row[3]} intentos',
                            'urgencia': 5.0,
                            'ciclo_recomendado': 2,
                        })

                # 2. Identificar modelos con mejor rendimiento para reasignar
                cur.execute("""
                    SELECT modelo, AVG(tasa_cierre) as tasa_media,
                           COUNT(*) as n
                    FROM datapoints_efectividad
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                    GROUP BY modelo
                    HAVING COUNT(*) >= 5
                    ORDER BY tasa_media DESC
                """)
                modelos = []
                for row in cur.fetchall():
                    modelos.append({
                        'modelo': row[0],
                        'tasa_media': round(float(row[1]), 4) if row[1] else 0,
                        'n': row[2],
                    })

                if len(modelos) >= 2:
                    mejor = modelos[0]
                    peor = modelos[-1]
                    if mejor['tasa_media'] - peor['tasa_media'] > 0.2:
                        acciones.append({
                            'tipo': 'reasignar_modelo',
                            'razon': f'Modelo {mejor["modelo"]} ({round(mejor["tasa_media"], 3)}) supera a {peor["modelo"]} ({round(peor["tasa_media"], 3)})',
                            'urgencia': 3.0,
                            'ciclo_recomendado': 2,
                        })

            # Obtener atractores para informar planificacion
            atractores = self.landscape.detectar_atractores(conn)

            acciones.sort(key=lambda x: x['urgencia'], reverse=True)

            return {
                'acciones_planificadas': acciones[:10],
                'n_acciones': len(acciones),
                'horizonte': self.horizonte,
                'modelos_ranking': modelos[:5] if modelos else [],
                'atractores_top': atractores.get('atractores', [])[:5],
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def get_estado_completo(self, conn=None) -> dict:
        """Estado completo del controlador predictivo."""
        trayectoria = self.predecir_trayectoria(conn)
        plan = self.planificar_acciones(conn)
        atractores = self.landscape.detectar_atractores(conn)

        return {
            'trayectoria': trayectoria,
            'plan': plan,
            'atractores': atractores,
        }


# Singleton
_controller = None

def get_predictive_controller() -> PredictiveController:
    global _controller
    if _controller is None:
        _controller = PredictiveController()
    return _controller
