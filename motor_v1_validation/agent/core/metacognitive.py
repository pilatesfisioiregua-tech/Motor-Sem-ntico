"""SN-21: Metacognitive Layer — FOK, JOL, Kalman Filter, Distributed Cognition.

Patrones aplicados:
  Metacognition (#83723): monitoring + control of cognition itself
  Kalman Filter (#83758): optimal recursive estimator, filtering noise
  Distributed Cognition (#83722): intelligence as emergent property of interactions

Capacidades:
  1. FOK (Feeling of Knowing): estimar confianza ANTES de ejecutar
  2. JOL (Judgment of Learning): evaluar calidad DESPUES de ejecutar
  3. Kalman-filtered effectiveness: estimar tasa real filtrando ruido
  4. Emergent insight detection: detectar cuando el todo > suma de partes
"""

import math
import time
from collections import defaultdict
from typing import Optional


class KalmanEstimator:
    """Kalman Filter para estimar tasa de efectividad real.

    Estado: x = tasa_cierre_real (latente)
    Medicion: z = tasa_cierre_observada (ruidosa)

    x_k = x_{k-1}                    (modelo: tasa no cambia rapido)
    z_k = x_k + v_k                  (medicion = real + ruido)

    Kalman gain: K = P / (P + R)
    Update: x = x + K * (z - x)
    P = (1 - K) * P + Q
    """

    def __init__(self, initial_estimate: float = 0.5,
                 process_noise: float = 0.01,
                 measurement_noise: float = 0.1):
        self.x = initial_estimate  # estado estimado
        self.P = 1.0               # incertidumbre del estado
        self.Q = process_noise     # ruido del proceso (cuanto cambia la tasa real)
        self.R = measurement_noise # ruido de medicion (cuanto varia cada datapoint)
        self.history = []

    def update(self, measurement: float) -> dict:
        """Actualizar estimacion con nueva medicion."""
        # Predict
        x_pred = self.x
        P_pred = self.P + self.Q

        # Kalman gain
        K = P_pred / (P_pred + self.R) if (P_pred + self.R) > 0 else 0.5

        # Update
        innovation = measurement - x_pred
        self.x = x_pred + K * innovation
        self.P = (1 - K) * P_pred

        self.history.append({
            'z': round(measurement, 4),
            'x': round(self.x, 4),
            'K': round(K, 4),
            'P': round(self.P, 4),
            'innovation': round(innovation, 4),
        })

        return {
            'estimacion': round(self.x, 4),
            'incertidumbre': round(self.P, 4),
            'gain': round(K, 4),
            'innovation': round(innovation, 4),
        }

    def get_confidence_interval(self, sigma: float = 2.0) -> tuple:
        """Intervalo de confianza [x - sigma*sqrt(P), x + sigma*sqrt(P)]."""
        margin = sigma * math.sqrt(self.P) if self.P > 0 else 0
        return (
            round(max(0, self.x - margin), 4),
            round(min(1, self.x + margin), 4),
        )


class MetacognitiveLayer:
    """Capa metacognitiva: monitoreo y control de la cognicion.

    FOK: antes de ejecutar, estimar si vamos a poder responder bien.
    JOL: despues de ejecutar, evaluar si la respuesta fue buena.
    """

    def __init__(self):
        self.kalman_estimators = {}  # celda -> KalmanEstimator
        self.fok_history = []
        self.jol_history = []

    def feeling_of_knowing(self, input_texto: str, celda: str,
                           programa: dict = None, conn=None) -> dict:
        """FOK: estimar confianza ANTES de ejecutar.

        Factores:
        1. Tasa historica de la celda (Kalman-filtered)
        2. Complejidad del input (longitud, ambiguedad)
        3. Cobertura del programa (cuantas INTs cubren la celda)
        4. Novedad del input (similitud con casos previos — Fase 3 Fix 3)

        Returns:
            {fok: float 0-1, factores: dict, recomendacion: str}
        """
        factores = {}

        # Factor 1: Tasa historica filtrada
        estimator = self._get_estimator(celda, conn)
        tasa_estimada = estimator.x if estimator else 0.5
        factores['tasa_kalman'] = round(tasa_estimada, 4)

        # Factor 2: Complejidad del input
        palabras = len(input_texto.split())
        complejidad = min(1.0, palabras / 200)  # >200 palabras = max complejidad
        factores['complejidad_input'] = round(complejidad, 4)

        # Factor 3: Cobertura del programa
        if programa:
            ints = programa.get('inteligencias', set())
            cobertura = min(1.0, len(ints) / 5)  # 5 INTs = cobertura completa
        else:
            cobertura = 0.5
        factores['cobertura_programa'] = round(cobertura, 4)

        # Factor 4: Novedad del input (Fase 3 Fix 3)
        # Busca si inputs similares ya se ejecutaron antes
        novedad = self._calcular_novedad(input_texto, conn)
        familiaridad = 1.0 - novedad
        factores['novedad'] = round(novedad, 4)
        factores['familiaridad'] = round(familiaridad, 4)

        # FOK = media ponderada (novedad REDUCE confianza)
        fok = (
            0.35 * tasa_estimada +
            0.15 * (1.0 - complejidad) +
            0.20 * cobertura +
            0.30 * familiaridad  # Fase 3: peso mayor a familiaridad
        )
        fok = round(min(1.0, max(0.0, fok)), 4)

        # Recomendacion
        if fok > 0.7:
            recomendacion = 'Alta confianza — proceder con tier normal'
        elif fok > 0.4:
            recomendacion = 'Confianza media — considerar tier superior'
        else:
            recomendacion = 'Baja confianza — escalar a tier maximo o alertar'

        result = {
            'fok': fok,
            'factores': factores,
            'recomendacion': recomendacion,
            'celda': celda,
        }
        self.fok_history.append(result)
        return result

    def judgment_of_learning(self, resultado: dict, programa: dict = None) -> dict:
        """JOL: evaluar calidad DESPUES de ejecutar.

        Factores:
        1. Tasa de cierre obtenida
        2. Consenso entre modelos (si enjambre)
        3. Cobertura de hallazgos
        4. Latencia relativa al SLO
        5. Calibracion FOK vs resultado real

        Returns:
            {jol: float 0-1, factores: dict, calibracion: dict}
        """
        factores = {}

        # Factor 1: Tasa de cierre
        tasa = resultado.get('tasa_cierre', 0)
        factores['tasa_cierre'] = round(tasa, 4)

        # Factor 2: Numero de hallazgos
        hallazgos = resultado.get('hallazgos', [])
        n_hallazgos = len(hallazgos) if isinstance(hallazgos, list) else 0
        factores['n_hallazgos'] = n_hallazgos
        factor_hallazgos = min(1.0, n_hallazgos / 5)

        # Factor 3: Latencia vs SLO
        latencia_ms = resultado.get('latencia_ms', 0)
        slo_ms = 150000  # 150s SLO
        factor_latencia = max(0, 1.0 - (latencia_ms / slo_ms)) if slo_ms > 0 else 0.5
        factores['factor_latencia'] = round(factor_latencia, 4)

        # Factor 4: Coste vs presupuesto
        coste = resultado.get('coste_usd', 0)
        factor_coste = max(0, 1.0 - (coste / 1.50))  # $1.50 max
        factores['factor_coste'] = round(factor_coste, 4)

        # JOL = media ponderada
        jol = (
            0.50 * tasa +
            0.20 * factor_hallazgos +
            0.15 * factor_latencia +
            0.15 * factor_coste
        )
        jol = round(min(1.0, max(0.0, jol)), 4)

        # Calibracion: comparar FOK previo con JOL
        calibracion = {}
        if self.fok_history:
            celda = resultado.get('celda_objetivo', '')
            fok_previo = None
            for fh in reversed(self.fok_history):
                if fh.get('celda') == celda:
                    fok_previo = fh['fok']
                    break
            if fok_previo is not None:
                calibracion = {
                    'fok_predicho': fok_previo,
                    'jol_real': jol,
                    'error': round(abs(fok_previo - jol), 4),
                    'bien_calibrado': abs(fok_previo - jol) < 0.2,
                }

        # Actualizar Kalman con la medicion real
        celda = resultado.get('celda_objetivo', '')
        if celda:
            estimator = self._get_or_create_estimator(celda)
            estimator.update(tasa)

        result = {
            'jol': jol,
            'factores': factores,
            'calibracion': calibracion,
        }
        self.jol_history.append(result)
        return result

    def detectar_emergencia(self, outputs: list, resultado_integrado: dict) -> dict:
        """Detectar insights emergentes: cuando el todo > suma de partes.

        Patron Distributed Cognition (#83722): la inteligencia emerge
        de las interacciones, no esta en los nodos individuales.

        Indicadores de emergencia:
        1. Hallazgo integrado que ningun output individual contenia
        2. Contradiccion resuelta entre outputs (sintesis dialectica)
        3. Patron detectado solo visible en la interseccion
        """
        if not outputs or not resultado_integrado:
            return {'emergencia': 0, 'indicadores': []}

        indicadores = []

        # 1. Hallazgos nuevos en integracion
        hallazgos_individuales = set()
        for o in outputs:
            for h in o.get('hallazgos', []):
                if isinstance(h, str):
                    hallazgos_individuales.add(h.lower()[:50])
                elif isinstance(h, dict):
                    hallazgos_individuales.add(str(h.get('texto', ''))[:50].lower())

        hallazgos_integrados = resultado_integrado.get('hallazgos', [])
        nuevos = 0
        for h in hallazgos_integrados:
            texto = h.lower()[:50] if isinstance(h, str) else str(h.get('texto', ''))[:50].lower()
            if texto not in hallazgos_individuales:
                nuevos += 1

        if nuevos > 0:
            indicadores.append({
                'tipo': 'hallazgo_emergente',
                'n': nuevos,
                'descripcion': f'{nuevos} hallazgos en integracion no presentes en outputs individuales',
            })

        # 2. Tasa integrada vs media individual
        tasas_individuales = [o.get('tasa_cierre', 0) for o in outputs if 'tasa_cierre' in o]
        tasa_integrada = resultado_integrado.get('tasa_cierre', 0)
        if tasas_individuales:
            media_individual = sum(tasas_individuales) / len(tasas_individuales)
            if tasa_integrada > media_individual * 1.2:  # >20% mejor
                indicadores.append({
                    'tipo': 'sinergia',
                    'tasa_integrada': round(tasa_integrada, 4),
                    'media_individual': round(media_individual, 4),
                    'boost': round((tasa_integrada - media_individual) / media_individual * 100, 1),
                    'descripcion': f'Tasa integrada {round((tasa_integrada/media_individual - 1)*100, 1)}% superior a media individual',
                })

        # 3. Diversidad de perspectivas
        ints_usadas = set()
        for o in outputs:
            if 'inteligencia' in o:
                ints_usadas.add(o['inteligencia'])
        if len(ints_usadas) >= 4:
            indicadores.append({
                'tipo': 'diversidad_alta',
                'n_inteligencias': len(ints_usadas),
                'descripcion': f'{len(ints_usadas)} inteligencias diversas — mayor potencial emergente',
            })

        # Score de emergencia
        emergencia = min(1.0, len(indicadores) * 0.3 + nuevos * 0.1)

        return {
            'emergencia': round(emergencia, 4),
            'indicadores': indicadores,
            'n_indicadores': len(indicadores),
            'interpretacion': 'emergencia_fuerte' if emergencia > 0.5 else (
                'emergencia_debil' if emergencia > 0.2 else 'sin_emergencia'
            ),
        }

    def get_kalman_estado(self, conn=None) -> dict:
        """Estado de todos los estimadores Kalman por celda."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db'}

        try:
            estados = {}
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT celda_objetivo, AVG(tasa_cierre) as media, COUNT(*) as n
                    FROM datapoints_efectividad
                    WHERE calibrado = true
                    GROUP BY celda_objetivo
                """)
                for row in cur.fetchall():
                    celda = row[0]
                    media = float(row[1]) if row[1] else 0
                    n = row[2]

                    estimator = self._get_or_create_estimator(celda)
                    # Initialize from DB if no history
                    if not estimator.history:
                        estimator.x = media

                    ci = estimator.get_confidence_interval()
                    estados[celda] = {
                        'estimacion': estimator.x,
                        'incertidumbre': round(estimator.P, 4),
                        'intervalo_confianza': ci,
                        'n_datapoints': n,
                        'media_cruda': round(media, 4),
                    }

            return {
                'estimadores': estados,
                'n_celdas': len(estados),
            }
        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def _calcular_novedad(self, input_texto: str, conn=None) -> float:
        """Novedad del input respecto a casos anteriores (Fase 3 Fix 3).

        1.0 = totalmente nuevo (nunca visto algo parecido)
        0.0 = ya ejecutado exacto o muy similar
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return 0.5

        try:
            with conn.cursor() as cur:
                # Buscar inputs similares por keywords (top 5 palabras)
                palabras = [w for w in input_texto.lower().split() if len(w) > 3][:5]
                if not palabras:
                    return 0.8

                # Use LIKE for compatibility (no FTS dependency)
                like_pattern = f'%{palabras[0]}%'
                cur.execute("""
                    SELECT COUNT(*) FROM campo_gradientes
                    WHERE input_texto ILIKE %s
                """, [like_pattern])
                similares = cur.fetchone()[0]

                if similares == 0:
                    return 1.0  # Totalmente nuevo
                elif similares <= 2:
                    return 0.7  # Poco visto
                elif similares <= 5:
                    return 0.4  # Familiar
                else:
                    return 0.1  # Muy visto

        except Exception:
            return 0.5
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def reset_kalman(self):
        """Reset todos los estimadores Kalman (Fase 3 Fix 3).

        Llamar tras recalibración de señales para que el Kalman
        se recalibre con datos reales post-Fix 2.
        """
        self.kalman_estimators = {}
        self.fok_history = []
        self.jol_history = []

    def _get_estimator(self, celda: str, conn=None) -> Optional[KalmanEstimator]:
        """Obtener estimador existente o crear uno desde DB."""
        if celda in self.kalman_estimators:
            return self.kalman_estimators[celda]

        # Intentar inicializar desde DB
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return None

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT AVG(tasa_cierre), COUNT(*)
                    FROM datapoints_efectividad
                    WHERE celda_objetivo = %s AND calibrado = true
                """, [celda])
                row = cur.fetchone()
                if row and row[1] > 0:
                    est = KalmanEstimator(initial_estimate=float(row[0]))
                    self.kalman_estimators[celda] = est
                    return est
            return None
        except Exception:
            return None
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def _get_or_create_estimator(self, celda: str) -> KalmanEstimator:
        """Obtener o crear estimador para celda."""
        if celda not in self.kalman_estimators:
            self.kalman_estimators[celda] = KalmanEstimator()
        return self.kalman_estimators[celda]

    def _contar_previos(self, celda: str, conn=None) -> int:
        """Contar datapoints previos para una celda."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return 0

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM datapoints_efectividad
                    WHERE celda_objetivo = %s AND calibrado = true
                """, [celda])
                return cur.fetchone()[0]
        except Exception:
            return 0
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)


# Singleton
_metacognitive = None

def get_metacognitive() -> MetacognitiveLayer:
    global _metacognitive
    if _metacognitive is None:
        _metacognitive = MetacognitiveLayer()
    return _metacognitive
