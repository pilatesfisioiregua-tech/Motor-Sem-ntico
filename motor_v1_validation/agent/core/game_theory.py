"""SN-23: Game-Theoretic Composition — Mechanism Design, Schelling Points, Signaling.

Patrones aplicados:
  Mechanism Design (#83728): disenar reglas para outcome global optimo
  Schelling Points (#83729): puntos focales de convergencia natural
  Signaling Theory (#83733): formalizar comunicacion de confianza

Capacidades:
  1. Schelling detection: encontrar programas donde multiples señales convergen
  2. Mechanism design: incentivos para que INTs cooperen (no compitan)
  3. Confidence signaling: formalizar cuanta confianza tiene cada output
  4. Nash equilibria: detectar combinaciones estables de INTs
"""

import math
from collections import defaultdict, Counter
from typing import Optional


class ConfidenceSignal:
    """Signal de confianza formalizado (Signaling Theory #83733).

    Cada output de una INT emite señales de confianza:
    - Coste de la señal (costlier signals are more credible)
    - Verificabilidad (falsifiable claims > unfalsifiable)
    - Especificidad (concrete > vague)
    """

    @staticmethod
    def evaluar_señal(output: dict) -> dict:
        """Evaluar credibilidad de las señales en un output."""
        texto = output.get('texto', '')
        hallazgos = output.get('hallazgos', [])

        señales = {}

        # 1. Especificidad: ratio de datos concretos vs afirmaciones vagas
        palabras = texto.split()
        n_palabras = len(palabras)
        # Indicadores de especificidad: numeros, porcentajes, nombres propios
        concretos = sum(1 for w in palabras if any(c.isdigit() for c in w))
        señales['especificidad'] = round(concretos / n_palabras, 4) if n_palabras > 0 else 0

        # 2. Verificabilidad: hallazgos con evidencia vs opiniones
        n_hallazgos = len(hallazgos) if isinstance(hallazgos, list) else 0
        señales['n_hallazgos'] = n_hallazgos
        señales['verificabilidad'] = min(1.0, n_hallazgos / 5) if n_hallazgos > 0 else 0

        # 3. Longitud como proxy de coste (more effort = more credible, diminishing returns)
        señales['coste_señal'] = round(min(1.0, math.log(n_palabras + 1) / math.log(500)), 4)

        # 4. Cobertura: cuantas dimensiones cubre
        dimensiones = set()
        keywords_dim = {
            'salud': ['salud', 'bienestar', 'cuerpo', 'energia'],
            'sentido': ['sentido', 'proposito', 'significado', 'valor'],
            'continuidad': ['continuidad', 'tiempo', 'futuro', 'plan'],
        }
        texto_lower = texto.lower()
        for dim, kws in keywords_dim.items():
            if any(kw in texto_lower for kw in kws):
                dimensiones.add(dim)
        señales['cobertura_dimensional'] = round(len(dimensiones) / 3, 4)

        # Credibilidad compuesta
        credibilidad = (
            0.30 * señales['especificidad'] +
            0.30 * señales['verificabilidad'] +
            0.20 * señales['coste_señal'] +
            0.20 * señales['cobertura_dimensional']
        )
        señales['credibilidad'] = round(credibilidad, 4)

        return señales


class SchellingDetector:
    """Detector de Schelling Points — convergencia focal.

    Un Schelling Point ocurre cuando multiples INTs independientemente
    convergen en la misma conclusion/recomendacion. Esto es muy valioso
    porque sugiere alta confianza sin coordinacion explicita.
    """

    @staticmethod
    def detectar_convergencia(outputs: list) -> dict:
        """Detectar puntos de convergencia entre outputs de multiples INTs.

        Busca:
        1. Hallazgos compartidos por 2+ INTs (consensus)
        2. Recomendaciones convergentes
        3. Patrones tematicos comunes
        """
        if len(outputs) < 2:
            return {'convergencias': [], 'score': 0}

        # 1. Extraer keywords de cada output
        keywords_por_int = {}
        for o in outputs:
            int_id = o.get('inteligencia', '?')
            texto = o.get('texto', '')
            # Keywords: palabras de >4 chars, normalizadas
            kws = set(
                w.lower().strip('.,;:!?()[]{}')
                for w in texto.split()
                if len(w) > 4
            )
            keywords_por_int[int_id] = kws

        # 2. Encontrar keywords compartidas por 2+ INTs
        all_keywords = Counter()
        for kws in keywords_por_int.values():
            for kw in kws:
                all_keywords[kw] += 1

        convergencias = []
        shared = {kw: count for kw, count in all_keywords.items() if count >= 2}

        if shared:
            # Top keywords compartidas
            top_shared = sorted(shared.items(), key=lambda x: x[1], reverse=True)[:20]
            for kw, count in top_shared:
                ints_que_comparten = [
                    int_id for int_id, kws in keywords_por_int.items()
                    if kw in kws
                ]
                convergencias.append({
                    'keyword': kw,
                    'n_inteligencias': count,
                    'inteligencias': ints_que_comparten,
                })

        # 3. Score de convergencia: ratio keywords compartidas / total
        total_unique = len(all_keywords)
        n_shared = len(shared)
        score = round(n_shared / total_unique, 4) if total_unique > 0 else 0

        # 4. Pares con mayor overlap (Jaccard similarity)
        pares_similares = []
        ints = list(keywords_por_int.keys())
        for i in range(len(ints)):
            for j in range(i + 1, len(ints)):
                kws_i = keywords_por_int[ints[i]]
                kws_j = keywords_por_int[ints[j]]
                intersection = len(kws_i & kws_j)
                union = len(kws_i | kws_j)
                jaccard = intersection / union if union > 0 else 0
                if jaccard > 0.1:
                    pares_similares.append({
                        'par': f"{ints[i]}-{ints[j]}",
                        'jaccard': round(jaccard, 4),
                        'n_compartidos': intersection,
                    })

        pares_similares.sort(key=lambda x: x['jaccard'], reverse=True)

        # Interpretacion
        if score > 0.3:
            interpretacion = 'schelling_fuerte'
            desc = 'Alta convergencia focal — multiples INTs llegan a las mismas conclusiones independientemente'
        elif score > 0.15:
            interpretacion = 'schelling_moderado'
            desc = 'Convergencia parcial — algunas conclusiones compartidas'
        else:
            interpretacion = 'sin_schelling'
            desc = 'Baja convergencia — INTs producen perspectivas complementarias (no es malo)'

        return {
            'convergencias': convergencias[:15],
            'pares_similares': pares_similares[:10],
            'score': score,
            'interpretacion': interpretacion,
            'descripcion': desc,
        }


class MechanismDesigner:
    """Mechanism Design — disenar incentivos para cooperacion optima entre INTs.

    Reverse game theory: en vez de predecir comportamiento dado las reglas,
    disenar las reglas para obtener el comportamiento deseado.

    Objetivo: que cada INT contribuya informacion UNICA y COMPLEMENTARIA,
    no que compitan por dar la "mejor" respuesta.
    """

    def analizar_incentivos(self, conn=None) -> dict:
        """Analizar si los incentivos actuales promueven cooperacion o competencia."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                # 1. Concentracion: si pocas INTs acaparan todo = competencia
                cur.execute("""
                    SELECT SPLIT_PART(pregunta_id, '_', 1) as int_id,
                           COUNT(*) as n,
                           AVG(tasa_cierre) as tasa
                    FROM datapoints_efectividad
                    GROUP BY SPLIT_PART(pregunta_id, '_', 1)
                    ORDER BY n DESC
                """)
                distribucion = []
                total_n = 0
                for row in cur.fetchall():
                    n = row[1]
                    distribucion.append({
                        'inteligencia': row[0],
                        'n': n,
                        'tasa': round(float(row[2]), 4) if row[2] else 0,
                    })
                    total_n += n

                # Herfindahl index (concentracion)
                hhi = 0
                for d in distribucion:
                    share = d['n'] / total_n if total_n > 0 else 0
                    hhi += share * share
                hhi = round(hhi, 4)

                # 2. Cooperacion: pares que funcionan mejor juntos que solos
                cur.execute("""
                    SELECT a.int_id, b.int_id,
                           AVG(a.tasa + b.tasa) / 2 as tasa_conjunta,
                           COUNT(*) as n_conjuntas
                    FROM (
                        SELECT SPLIT_PART(pregunta_id, '_', 1) as int_id,
                               celda_objetivo, tasa_cierre as tasa
                        FROM datapoints_efectividad
                    ) a
                    JOIN (
                        SELECT SPLIT_PART(pregunta_id, '_', 1) as int_id,
                               celda_objetivo, tasa_cierre as tasa
                        FROM datapoints_efectividad
                    ) b ON a.celda_objetivo = b.celda_objetivo AND a.int_id < b.int_id
                    GROUP BY a.int_id, b.int_id
                    HAVING COUNT(*) >= 3
                    ORDER BY tasa_conjunta DESC
                    LIMIT 10
                """)
                cooperaciones = []
                for row in cur.fetchall():
                    cooperaciones.append({
                        'par': f"{row[0]}-{row[1]}",
                        'tasa_conjunta': round(float(row[2]), 4) if row[2] else 0,
                        'n': row[3],
                    })

            # Diagnostico
            if hhi > 0.25:
                diagnostico = 'concentrada'
                recomendacion = 'Diversificar: pocas INTs dominan. Incentivar uso de INTs subrepresentadas'
            elif hhi < 0.10:
                diagnostico = 'dispersa'
                recomendacion = 'Bien distribuido. Verificar que la dispersion no sea por falta de datos'
            else:
                diagnostico = 'equilibrada'
                recomendacion = 'Distribucion saludable. Mantener incentivos actuales'

            return {
                'distribucion': distribucion[:15],
                'hhi': hhi,
                'diagnostico': diagnostico,
                'recomendacion': recomendacion,
                'cooperaciones_top': cooperaciones,
                'n_inteligencias_activas': len(distribucion),
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def detectar_equilibrios(self, conn=None) -> dict:
        """Detectar Nash equilibria: combinaciones estables de INTs.

        Un equilibrio Nash ocurre cuando ninguna INT individual
        mejoraria el resultado si se sustituyera por otra.
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                # Encontrar combinaciones INT con tasa alta y estable
                cur.execute("""
                    SELECT celda_objetivo,
                           array_agg(DISTINCT SPLIT_PART(pregunta_id, '_', 1)) as ints,
                           AVG(tasa_cierre) as tasa_media,
                           STDDEV(tasa_cierre) as tasa_std,
                           COUNT(*) as n
                    FROM datapoints_efectividad
                    GROUP BY celda_objetivo
                    HAVING COUNT(*) >= 5
                    ORDER BY tasa_media DESC
                """)
                equilibrios = []
                for row in cur.fetchall():
                    tasa = float(row[2]) if row[2] else 0
                    std = float(row[3]) if row[3] else 1
                    # Equilibrio = alta tasa + baja varianza
                    estabilidad = tasa / (std + 0.01)  # Sharpe-like ratio
                    ints_list = row[1] if isinstance(row[1], list) else []

                    if tasa > 0.2 and estabilidad > 2.0:
                        equilibrios.append({
                            'celda': row[0],
                            'inteligencias': ints_list,
                            'tasa_media': round(tasa, 4),
                            'tasa_std': round(std, 4),
                            'estabilidad': round(estabilidad, 2),
                            'n': row[4],
                        })

            equilibrios.sort(key=lambda x: x['estabilidad'], reverse=True)

            return {
                'equilibrios': equilibrios[:10],
                'n_equilibrios': len(equilibrios),
                'interpretacion': (
                    'Sistema con equilibrios estables' if len(equilibrios) >= 3
                    else 'Pocos equilibrios — sistema aun explorando'
                ),
            }

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)


class GameTheoryEngine:
    """Motor de teoria de juegos unificado."""

    def __init__(self):
        self.signal = ConfidenceSignal()
        self.schelling = SchellingDetector()
        self.mechanism = MechanismDesigner()

    def analizar_composicion(self, outputs: list) -> dict:
        """Analisis game-theoretic completo de una composicion de outputs."""
        # Señales de confianza por output
        señales = []
        for o in outputs:
            s = self.signal.evaluar_señal(o)
            s['inteligencia'] = o.get('inteligencia', '?')
            señales.append(s)

        # Convergencia Schelling
        convergencia = self.schelling.detectar_convergencia(outputs)

        return {
            'señales_confianza': señales,
            'convergencia_schelling': convergencia,
            'credibilidad_media': round(
                sum(s['credibilidad'] for s in señales) / len(señales), 4
            ) if señales else 0,
        }

    def get_estado_completo(self, conn=None) -> dict:
        """Estado completo del motor game-theoretic."""
        incentivos = self.mechanism.analizar_incentivos(conn)
        equilibrios = self.mechanism.detectar_equilibrios(conn)

        return {
            'incentivos': incentivos,
            'equilibrios': equilibrios,
        }


# Singleton
_engine = None

def get_game_theory() -> GameTheoryEngine:
    global _engine
    if _engine is None:
        _engine = GameTheoryEngine()
    return _engine
