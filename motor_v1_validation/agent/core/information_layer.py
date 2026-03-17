"""SN-19: Information Layer — Mutual Information, Entropy, Information Bottleneck.

Patrones aplicados:
  Information Bottleneck (#83756): compresion optima preservando relevancia
  Mutual Information (#83751): I(X;Y) = H(X) + H(Y) - H(X,Y)
  Shannon Entropy (#83747): H(X) = -SUM p(x) * log2 p(x)

Capacidades:
  1. Medir redundancia entre inteligencias (MI)
  2. Medir informacion anadida por cada output (Entropy)
  3. Compresion optima en integracion (IB)
  4. Detectar puntos ciegos informativos
"""

import math
import json
from collections import Counter, defaultdict
from typing import Optional


def _tokenize(text: str) -> list:
    """Tokenizar texto en palabras normalizadas."""
    return [w.lower().strip('.,;:!?()[]{}') for w in text.split() if len(w) > 2]


def shannon_entropy(text: str) -> float:
    """H(X) = -SUM p(x) * log2 p(x)

    Mide la incertidumbre/informacion del texto.
    Alto = mucha informacion diversa. Bajo = repetitivo.
    """
    tokens = _tokenize(text)
    if not tokens:
        return 0.0

    n = len(tokens)
    counts = Counter(tokens)
    entropy = 0.0

    for count in counts.values():
        p = count / n
        if p > 0:
            entropy -= p * math.log2(p)

    return round(entropy, 4)


def conditional_entropy(text_x: str, text_y: str) -> float:
    """H(X|Y) — entropia de X dado Y.

    Aproximacion: cuantos tokens de X NO aparecen en Y.
    """
    tokens_x = set(_tokenize(text_x))
    tokens_y = set(_tokenize(text_y))

    if not tokens_x:
        return 0.0

    # Tokens de X que no estan en Y = informacion nueva de X dado Y
    nuevos = tokens_x - tokens_y
    ratio_nuevos = len(nuevos) / len(tokens_x) if tokens_x else 0

    # H(X|Y) proporcional a la ratio de tokens nuevos
    return round(shannon_entropy(' '.join(nuevos)) * ratio_nuevos, 4)


def mutual_information(text_a: str, text_b: str) -> dict:
    """I(A;B) = H(A) + H(B) - H(A,B)

    Mide cuanta informacion comparten dos textos.
    Alto = redundantes. Bajo = complementarios.
    """
    h_a = shannon_entropy(text_a)
    h_b = shannon_entropy(text_b)
    h_ab = shannon_entropy(text_a + ' ' + text_b)

    mi = max(0, h_a + h_b - h_ab)
    # Normalizar: NMI = 2*I(A;B) / (H(A) + H(B))
    nmi = (2 * mi / (h_a + h_b)) if (h_a + h_b) > 0 else 0

    return {
        'H_A': h_a,
        'H_B': h_b,
        'H_AB': h_ab,
        'MI': round(mi, 4),
        'NMI': round(nmi, 4),  # 0=independientes, 1=identicos
        'complementariedad': round(1.0 - nmi, 4),  # 1=totalmente complementarios
    }


def information_bottleneck(outputs: list, target_bits: float = None) -> dict:
    """Compresion optima de multiples outputs preservando informacion relevante.

    Implementacion simplificada del IB:
    1. Calcular entropia de cada output
    2. Calcular MI entre pares
    3. Seleccionar subset que maximiza informacion total con minima redundancia

    Args:
        outputs: lista de {'inteligencia': str, 'texto': str}
        target_bits: bits objetivo de compresion (None = auto)

    Returns:
        dict con ranking de outputs por contribucion informativa
    """
    if not outputs:
        return {'ranking': [], 'total_info': 0}

    n = len(outputs)

    # 1. Entropia individual de cada output
    entropias = []
    for o in outputs:
        h = shannon_entropy(o.get('texto', ''))
        entropias.append({
            'inteligencia': o.get('inteligencia', '?'),
            'H': h,
            'n_tokens': len(_tokenize(o.get('texto', ''))),
        })

    # 2. MI entre todos los pares
    mi_matrix = {}
    for i in range(n):
        for j in range(i + 1, n):
            key = f"{outputs[i].get('inteligencia', i)}-{outputs[j].get('inteligencia', j)}"
            mi = mutual_information(
                outputs[i].get('texto', ''),
                outputs[j].get('texto', '')
            )
            mi_matrix[key] = mi

    # 3. Contribucion marginal de cada output
    # Info_marginal(i) = H(i) - AVG(MI(i,j)) para todo j != i
    for i, e in enumerate(entropias):
        mi_sum = 0
        mi_count = 0
        int_i = outputs[i].get('inteligencia', str(i))
        for j in range(n):
            if i == j:
                continue
            int_j = outputs[j].get('inteligencia', str(j))
            key = f"{int_i}-{int_j}" if int_i < int_j else f"{int_j}-{int_i}"
            if key in mi_matrix:
                mi_sum += mi_matrix[key]['MI']
                mi_count += 1

        redundancia_media = mi_sum / mi_count if mi_count > 0 else 0
        e['redundancia_media'] = round(redundancia_media, 4)
        e['info_marginal'] = round(e['H'] - redundancia_media, 4)

    # Ranking por contribucion marginal
    ranking = sorted(entropias, key=lambda x: x['info_marginal'], reverse=True)

    # Detectar puntos ciegos: pares con MI muy baja = informacion independiente
    puntos_ciegos = []
    for key, mi in mi_matrix.items():
        if mi['NMI'] < 0.1:
            puntos_ciegos.append({
                'par': key,
                'NMI': mi['NMI'],
                'interpretacion': 'informacion completamente independiente — posible punto ciego entre estas inteligencias',
            })

    # Total info unica (no redundante)
    total_bruta = sum(e['H'] for e in entropias)
    total_redundancia = sum(mi['MI'] for mi in mi_matrix.values())
    total_neta = max(0, total_bruta - total_redundancia)

    return {
        'ranking': ranking,
        'mi_matrix': mi_matrix,
        'puntos_ciegos': puntos_ciegos,
        'total_info_bruta': round(total_bruta, 4),
        'total_redundancia': round(total_redundancia, 4),
        'total_info_neta': round(total_neta, 4),
        'ratio_eficiencia': round(total_neta / total_bruta, 4) if total_bruta > 0 else 0,
    }


def analizar_inteligencias_db(conn=None) -> dict:
    """Analizar redundancia/complementariedad entre inteligencias usando datos reales.

    Calcula MI entre outputs de diferentes inteligencias para los mismos casos.
    """
    own_conn = conn is None
    if own_conn:
        from .db_pool import get_conn
        conn = get_conn()
        if not conn:
            return {'error': 'no_db_connection'}

    try:
        with conn.cursor() as cur:
            # Obtener inteligencias con mas datos
            cur.execute("""
                SELECT DISTINCT SPLIT_PART(pregunta_id, '_', 1) as int_id,
                       COUNT(*) as n,
                       AVG(tasa_cierre) as tasa_media
                FROM datapoints_efectividad
                GROUP BY SPLIT_PART(pregunta_id, '_', 1)
                HAVING COUNT(*) >= 3
                ORDER BY n DESC
            """)
            stats = [{'inteligencia': r[0], 'n': r[1],
                      'tasa_media': round(float(r[2]), 4) if r[2] else 0}
                     for r in cur.fetchall()]

            # MI proxy: dos INTs que cierran los mismos gaps son redundantes
            cur.execute("""
                SELECT a.int_id, b.int_id,
                       COUNT(*) as n_comun,
                       CORR(a.tasa, b.tasa) as correlacion
                FROM (
                    SELECT SPLIT_PART(pregunta_id, '_', 1) as int_id,
                           celda_objetivo, AVG(tasa_cierre) as tasa
                    FROM datapoints_efectividad
                    GROUP BY SPLIT_PART(pregunta_id, '_', 1), celda_objetivo
                ) a
                JOIN (
                    SELECT SPLIT_PART(pregunta_id, '_', 1) as int_id,
                           celda_objetivo, AVG(tasa_cierre) as tasa
                    FROM datapoints_efectividad
                    GROUP BY SPLIT_PART(pregunta_id, '_', 1), celda_objetivo
                ) b ON a.celda_objetivo = b.celda_objetivo AND a.int_id < b.int_id
                GROUP BY a.int_id, b.int_id
                HAVING COUNT(*) >= 2
            """)
            pares = []
            for r in cur.fetchall():
                corr = float(r[3]) if r[3] is not None else 0
                pares.append({
                    'par': f"{r[0]}-{r[1]}",
                    'n_celdas_comunes': r[2],
                    'correlacion': round(corr, 4),
                    'tipo': 'redundante' if corr > 0.7 else ('complementario' if corr < 0.3 else 'parcial'),
                })

        pares.sort(key=lambda x: x['correlacion'])
        return {
            'inteligencias': stats,
            'pares': pares,
            'mas_complementarios': pares[:5] if pares else [],
            'mas_redundantes': pares[-5:] if pares else [],
        }

    except Exception as e:
        return {'error': str(e)}
    finally:
        if own_conn:
            from .db_pool import put_conn
            put_conn(conn)
