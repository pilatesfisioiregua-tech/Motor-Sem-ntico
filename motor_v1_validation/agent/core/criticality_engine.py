"""SN-20: Criticality Engine — SOC, Phase Transitions, Edge of Chaos.

Patrones aplicados:
  Self-Organized Criticality (#83737): auto-tuning al punto critico
  Phase Transitions (#83739): saltos cualitativos en calidad
  Edge of Chaos (#83745): operar donde la capacidad computacional es maxima

El sistema busca operar en el borde del caos: ni tan rigido que siempre
use el mismo programa, ni tan caotico que seleccione al azar. En el borde,
la capacidad de generar insights emergentes es maxima.
"""

import math
import time
import random
from collections import defaultdict, Counter
from typing import Optional


class CriticalityEngine:
    """Motor de criticalidad: auto-tune al borde del caos.

    Metricas clave:
    - Temperatura T: control parameter (0=orden, 1=caos)
    - Lyapunov exponent L: sensibilidad a condiciones iniciales
    - Correlation length xi: alcance de las interacciones
    - Avalanche distribution: P(s) ~ s^(-tau) si esta en criticalidad
    """

    def __init__(self):
        self.T = 0.5  # temperatura inicial (borde)
        self.T_c = 0.5  # temperatura critica estimada
        self.tau = 2.0  # exponente de ley de potencias
        self.history = []  # [(timestamp, T, L, resultado)]
        self.avalanchas = []  # tamaños de "avalanchas" de mejora

    def calcular_temperatura(self, conn=None) -> dict:
        """Calcular temperatura actual del sistema.

        T = varianza(tasa_cierre) / media(tasa_cierre)
        - T bajo: sistema rigido (siempre mismos resultados)
        - T alto: sistema caotico (resultados impredecibles)
        - T ~ T_c: borde del caos (maximo potencial)
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'T': self.T, 'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT AVG(tasa_cierre) as media,
                           STDDEV(tasa_cierre) as stddev,
                           COUNT(*) as n
                    FROM datapoints_efectividad
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                      AND calibrado = true
                """)
                row = cur.fetchone()
                media = float(row[0]) if row[0] else 0.5
                stddev = float(row[1]) if row[1] else 0.1
                n = row[2]

            # T = coeficiente de variacion
            T = stddev / media if media > 0 else 0.5
            self.T = round(min(1.0, max(0.0, T)), 4)

            # Distancia al punto critico
            distancia_critica = abs(self.T - self.T_c)

            # Regimen
            if self.T < self.T_c - 0.15:
                regimen = 'orden_rigido'
                recomendacion = 'Relajar restricciones del Manifold — sistema demasiado predecible'
            elif self.T > self.T_c + 0.15:
                regimen = 'caos'
                recomendacion = 'Endurecer restricciones — sistema demasiado impredecible'
            else:
                regimen = 'borde_del_caos'
                recomendacion = 'Optimo — sistema opera con maxima capacidad computacional'

            return {
                'T': self.T,
                'T_c': self.T_c,
                'distancia_critica': round(distancia_critica, 4),
                'regimen': regimen,
                'recomendacion': recomendacion,
                'media_tasa': round(media, 4),
                'stddev_tasa': round(stddev, 4),
                'n_datapoints': n,
            }

        except Exception as e:
            return {'T': self.T, 'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def detectar_transiciones_fase(self, conn=None) -> dict:
        """Detectar phase transitions: saltos cualitativos en calidad.

        Una transicion de fase ocurre cuando añadir/quitar una inteligencia
        causa un cambio discontinuo en la tasa de cierre.
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'transiciones': []}

        try:
            transiciones = []
            with conn.cursor() as cur:
                # Buscar inteligencias cuya presencia/ausencia causa salto >30%
                cur.execute("""
                    SELECT SPLIT_PART(pregunta_id, '_', 1) as int_id,
                           celda_objetivo,
                           AVG(tasa_cierre) as tasa_con,
                           COUNT(*) as n
                    FROM datapoints_efectividad
                    WHERE calibrado = true
                    GROUP BY SPLIT_PART(pregunta_id, '_', 1), celda_objetivo
                    HAVING COUNT(*) >= 3
                """)
                datos_por_int = defaultdict(list)
                for row in cur.fetchall():
                    datos_por_int[row[0]].append({
                        'celda': row[1],
                        'tasa': float(row[2]),
                        'n': row[3],
                    })

                # Tasa global por celda (sin filtrar por INT)
                cur.execute("""
                    SELECT celda_objetivo, AVG(tasa_cierre) as tasa_global
                    FROM datapoints_efectividad
                    WHERE calibrado = true
                    GROUP BY celda_objetivo
                """)
                tasa_global = {r[0]: float(r[1]) for r in cur.fetchall()}

                # Detectar saltos
                for int_id, datos in datos_por_int.items():
                    for d in datos:
                        global_tasa = tasa_global.get(d['celda'], 0)
                        if global_tasa > 0:
                            salto = (d['tasa'] - global_tasa) / global_tasa
                            if abs(salto) > 0.30:  # >30% de diferencia
                                transiciones.append({
                                    'inteligencia': int_id,
                                    'celda': d['celda'],
                                    'tasa_con_int': round(d['tasa'], 4),
                                    'tasa_global': round(global_tasa, 4),
                                    'salto_pct': round(salto * 100, 1),
                                    'tipo': 'positiva' if salto > 0 else 'negativa',
                                    'n': d['n'],
                                })

            transiciones.sort(key=lambda x: abs(x['salto_pct']), reverse=True)

            return {
                'transiciones': transiciones[:20],
                'n_transiciones': len(transiciones),
                'inteligencias_criticas': list(set(t['inteligencia'] for t in transiciones[:5])),
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def medir_avalanchas(self, conn=None) -> dict:
        """Medir distribucion de avalanchas (patron SOC).

        Si P(s) ~ s^(-tau), el sistema esta en criticalidad.
        - tau ~ 1.5: criticalidad fuerte
        - tau > 3: subcritico (orden)
        - tau < 1: supercritico (caos)
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                # Medir "avalanchas" = racha de mejoras consecutivas
                cur.execute("""
                    SELECT tasa_cierre FROM datapoints_efectividad
                    WHERE calibrado = true
                    ORDER BY timestamp
                """)
                tasas = [float(r[0]) for r in cur.fetchall()]

            if len(tasas) < 10:
                return {'error': 'insuficientes_datos', 'n': len(tasas)}

            # Detectar avalanchas: secuencias donde tasa > media
            media = sum(tasas) / len(tasas)
            avalanchas = []
            current = 0

            for t in tasas:
                if t > media:
                    current += 1
                else:
                    if current > 0:
                        avalanchas.append(current)
                    current = 0
            if current > 0:
                avalanchas.append(current)

            self.avalanchas = avalanchas

            if not avalanchas:
                return {'avalanchas': 0, 'tau': None}

            # Estimar tau: log-log regression
            size_counts = Counter(avalanchas)
            sizes = sorted(size_counts.keys())
            if len(sizes) >= 2:
                # Simple power-law fit: log P(s) = -tau * log(s) + c
                total = sum(size_counts.values())
                log_s = [math.log(s) for s in sizes if s > 0]
                log_p = [math.log(size_counts[s] / total) for s in sizes if s > 0]

                if len(log_s) >= 2:
                    # Linear regression
                    n = len(log_s)
                    sum_x = sum(log_s)
                    sum_y = sum(log_p)
                    sum_xy = sum(x * y for x, y in zip(log_s, log_p))
                    sum_x2 = sum(x * x for x in log_s)

                    denom = n * sum_x2 - sum_x * sum_x
                    if denom != 0:
                        tau = -(n * sum_xy - sum_x * sum_y) / denom
                    else:
                        tau = 2.0
                else:
                    tau = 2.0
            else:
                tau = 2.0

            self.tau = round(tau, 2)

            # Interpretacion
            if 1.3 < tau < 2.5:
                regimen = 'criticalidad'
                desc = 'Sistema en criticalidad auto-organizada — maxima adaptabilidad'
            elif tau > 2.5:
                regimen = 'subcritico'
                desc = 'Sistema demasiado ordenado — pocas avalanchas grandes'
            else:
                regimen = 'supercritico'
                desc = 'Sistema demasiado caotico — avalanchas excesivas'

            return {
                'n_avalanchas': len(avalanchas),
                'max_avalancha': max(avalanchas),
                'media_avalancha': round(sum(avalanchas) / len(avalanchas), 2),
                'tau': self.tau,
                'regimen': regimen,
                'descripcion': desc,
                'distribucion': dict(size_counts),
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def ajustar_manifold_temperatura(self) -> dict:
        """Ajustar restricciones del Manifold segun temperatura.

        En borde del caos: mantener invariantes, relajar heuristicas.
        En orden: relajar mas heuristicas.
        En caos: endurecer heuristicas.
        """
        if self.T < self.T_c - 0.15:
            # Demasiado orden -> relajar
            return {
                'accion': 'relajar',
                'R03_max_ints': 7,  # ampliar de 6 a 7
                'R04_orden_flexible': True,
                'R07_profundidad': 1,
            }
        elif self.T > self.T_c + 0.15:
            # Demasiado caos -> endurecer
            return {
                'accion': 'endurecer',
                'R03_max_ints': 4,  # reducir de 6 a 4
                'R04_orden_flexible': False,
                'R07_profundidad': 2,
            }
        else:
            # Borde del caos -> optimo
            return {
                'accion': 'mantener',
                'R03_max_ints': 5,
                'R04_orden_flexible': False,
                'R07_profundidad': 2,
            }

    def get_estado_completo(self, conn=None) -> dict:
        """Estado completo del motor de criticalidad."""
        temp = self.calcular_temperatura(conn)
        avalanchas = self.medir_avalanchas(conn)
        transiciones = self.detectar_transiciones_fase(conn)
        ajuste = self.ajustar_manifold_temperatura()

        return {
            'temperatura': temp,
            'avalanchas': avalanchas,
            'transiciones': transiciones,
            'ajuste_manifold': ajuste,
        }


# Singleton
_engine = None

def get_criticality_engine() -> CriticalityEngine:
    global _engine
    if _engine is None:
        _engine = CriticalityEngine()
    return _engine
