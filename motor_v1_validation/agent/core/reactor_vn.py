"""Reactor vN — genera preguntas nuevas desde gaps y observaciones.

Patron Generator (#60671): sintesis sistematica de preguntas.
Patron Feedback Loop (#60670): reactor↔gestor bidireccional.

Ciclo: gaps → observaciones → preguntas candidatas → scoring → preguntas_matriz
"""

import json
import uuid
import random
from datetime import datetime, timezone


# Templates de preguntas por funcion
TEMPLATES_FUNCION = {
    'Conservar': [
        "¿Qué mecanismos mantienen estable {contexto}?",
        "¿Qué se perdería si {contexto} dejara de funcionar?",
        "¿Cuál es el coste de NO conservar {contexto}?",
    ],
    'Captar': [
        "¿Qué recursos necesita captar {contexto} para sobrevivir?",
        "¿De dónde viene la energía que alimenta {contexto}?",
        "¿Qué oportunidades no se están captando en {contexto}?",
    ],
    'Depurar': [
        "¿Qué sobra en {contexto} que consume sin aportar?",
        "¿Qué procesos en {contexto} podrían eliminarse sin consecuencias?",
        "¿Cuánto cuesta mantener lo que no funciona en {contexto}?",
    ],
    'Distribuir': [
        "¿Cómo se reparten los recursos en {contexto}?",
        "¿Hay concentración excesiva de {recurso} en algún punto?",
        "¿Qué partes de {contexto} están infrafinanciadas?",
    ],
    'Frontera': [
        "¿Dónde termina {contexto} y empieza lo externo?",
        "¿Qué decisiones de {contexto} son internas vs externas?",
        "¿Quién define los límites de {contexto}?",
    ],
    'Adaptar': [
        "¿Cómo responde {contexto} a cambios inesperados?",
        "¿Qué pasaría si el entorno de {contexto} cambiara radicalmente?",
        "¿Cuánto tarda {contexto} en adaptarse a nuevas condiciones?",
    ],
    'Replicar': [
        "¿Puede {contexto} funcionar sin la persona clave?",
        "¿Es replicable el modelo de {contexto} en otro lugar?",
        "¿Qué impide que {contexto} escale?",
    ],
}

TEMPLATES_LENTE = {
    'Salud': "desde la perspectiva de si funciona operativamente",
    'Sentido': "desde la perspectiva de si tiene propósito y dirección",
    'Continuidad': "desde la perspectiva de si puede sobrevivir en el tiempo",
}


class ReactorVN:
    """Genera preguntas nuevas para celdas con gap alto."""

    def ejecutar(self, max_candidatas: int = 20, conn=None) -> dict:
        """Pipeline completo del reactor.

        1. Identificar celdas con gap alto (señales PID: I alto, D >= 0)
        2. Consumir peticiones estigmergicas del Gestor
        3. Para cada celda, generar preguntas candidatas
        4. Scoring: priorizar por gap * novedad
        5. Insertar top-N en preguntas_matriz con nivel='candidata'
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            # 1. Identificar gaps prioritarios
            gaps = self._identificar_gaps_prioritarios(conn)

            # 2. Consumir peticiones del Gestor + tool_gaps
            from .mejora_continua import consumir_marcas
            peticiones = consumir_marcas('peticion_reactor', conn=conn)
            tool_gap_marks = consumir_marcas('tool_gap', conn=conn)

            # Merge: gaps + peticiones + tool_gaps
            celdas_target = set()
            for g in gaps:
                celdas_target.add(g['celda'])
            for p in peticiones:
                contenido = p.get('contenido', {})
                if isinstance(contenido, dict) and 'celda' in contenido:
                    celdas_target.add(contenido['celda'])
            # tool_gaps don't have a specific celda — map to generic gap targets
            for tg in tool_gap_marks:
                contenido = tg.get('contenido', {})
                desc = contenido.get('description', '') if isinstance(contenido, dict) else ''
                if desc:
                    # Map tool gap to nearest functional cell
                    celdas_target.add('AdaptarxSalud')  # default: adaptation gaps

            if not celdas_target and not gaps:
                return {'candidatas_generadas': 0, 'msg': 'no gaps prioritarios'}

            # 3. Generar candidatas
            todas_candidatas = []
            for celda in celdas_target:
                parts = celda.split('x')
                funcion = parts[0] if len(parts) > 0 else 'Conservar'
                lente = parts[1] if len(parts) > 1 else 'Salud'

                # Determinar inteligencias relevantes para esta celda
                ints = self._inteligencias_para_celda(funcion, lente)
                for int_id in ints[:2]:  # max 2 inteligencias por celda
                    candidatas = self._generar_candidatas(celda, int_id, funcion, lente, conn)
                    todas_candidatas.extend(candidatas)

            # 4. Scoring
            scored = self._scoring_candidatas(todas_candidatas, gaps, conn)

            # 5. Insertar top-N
            top = scored[:max_candidatas]
            insertadas = self._insertar_aprobadas(top, conn)

            # Log
            from .mejora_continua import log_gestor
            log_gestor('reactor_ejecutado', {
                'gaps_detectados': len(gaps),
                'peticiones_consumidas': len(peticiones),
                'tool_gaps_consumidos': len(tool_gap_marks),
                'candidatas_generadas': len(todas_candidatas),
                'insertadas': insertadas,
            }, nivel='auto', conn=conn)

            return {
                'gaps_analizados': len(gaps),
                'peticiones_consumidas': len(peticiones),
                'tool_gaps_consumidos': len(tool_gap_marks),
                'candidatas_generadas': len(todas_candidatas),
                'insertadas': insertadas,
                'top_candidatas': top[:5],
            }

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

    def _identificar_gaps_prioritarios(self, conn) -> list:
        """Top celdas donde hay gap alto o cronico."""
        from .registrador import obtener_señales_todas_celdas

        señales = obtener_señales_todas_celdas(conn=conn)
        gaps = []

        for celda, s in señales.items():
            P = s.get('P', 0)
            I = s.get('I_anti_windup', 0)
            D = s.get('D_filtrado', 0)

            # Gap prioritario: P alto (gap actual alto) O I alto Y D >= 0 (cronico, no mejorando)
            if P > 0.5 or (I > 1.0 and D >= 0):
                gaps.append({
                    'celda': celda,
                    'P': P, 'I': I, 'D': D,
                    'prioridad': P + abs(I) * 0.5,
                })

        gaps.sort(key=lambda x: x['prioridad'], reverse=True)
        return gaps[:10]

    def _inteligencias_para_celda(self, funcion: str, lente: str) -> list:
        """Mapear celda a inteligencias relevantes."""
        mapa_funcion = {
            'Conservar': ['INT-01', 'INT-16'],
            'Captar': ['INT-06', 'INT-14'],
            'Depurar': ['INT-02', 'INT-07'],
            'Distribuir': ['INT-05', 'INT-16'],
            'Frontera': ['INT-09', 'INT-17'],
            'Adaptar': ['INT-08', 'INT-10'],
            'Replicar': ['INT-13', 'INT-12'],
        }
        return mapa_funcion.get(funcion, ['INT-01', 'INT-08'])

    def _generar_candidatas(self, celda: str, int_id: str,
                            funcion: str, lente: str, conn) -> list:
        """Generar preguntas candidatas por recombinacion de templates + exitosas.

        NO usa LLM — genera por recombinacion determinista.
        """
        candidatas = []
        templates = TEMPLATES_FUNCION.get(funcion, [])
        lente_perspectiva = TEMPLATES_LENTE.get(lente, '')

        # Obtener preguntas exitosas existentes para esta inteligencia
        exitosas = []
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT texto FROM preguntas_matriz
                    WHERE inteligencia = %s AND score_efectividad > 0.3
                    ORDER BY score_efectividad DESC
                    LIMIT 5
                """, [int_id])
                exitosas = [r[0] for r in cur.fetchall()]
        except Exception:
            pass

        # Generar desde templates
        contextos = ['este sistema', 'la situación', 'este proyecto', 'este negocio']
        for template in templates:
            for ctx in contextos[:2]:
                texto = template.format(contexto=ctx, recurso='atención')
                texto_full = f"{texto} ({lente_perspectiva})"
                candidatas.append({
                    'texto': texto_full,
                    'inteligencia': int_id,
                    'celda': celda,
                    'funcion': funcion,
                    'lente': lente,
                    'origen': 'template',
                })

        # Generar variaciones de exitosas
        for exitosa in exitosas[:3]:
            # Variacion: cambiar perspectiva
            variacion = f"{exitosa.rstrip('?')} — {lente_perspectiva}?"
            candidatas.append({
                'texto': variacion,
                'inteligencia': int_id,
                'celda': celda,
                'funcion': funcion,
                'lente': lente,
                'origen': 'variacion_exitosa',
            })

        return candidatas

    def _scoring_candidatas(self, candidatas: list, gaps: list, conn) -> list:
        """Score = gap_celda * novedad.

        Novedad: penalizar si texto muy similar a preguntas existentes.
        """
        gap_por_celda = {g['celda']: g['prioridad'] for g in gaps}

        # Obtener textos existentes para calcular novedad
        textos_existentes = set()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT texto FROM preguntas_matriz LIMIT 1000")
                textos_existentes = {r[0].lower()[:50] for r in cur.fetchall()}
        except Exception:
            pass

        for c in candidatas:
            gap_score = gap_por_celda.get(c['celda'], 0.5)
            # Novedad: 1.0 si nueva, 0.1 si ya existe algo parecido
            prefix = c['texto'].lower()[:50]
            novedad = 0.1 if prefix in textos_existentes else 1.0
            c['score'] = round(gap_score * novedad, 4)

        candidatas.sort(key=lambda x: x['score'], reverse=True)
        return candidatas

    def _insertar_aprobadas(self, candidatas: list, conn) -> int:
        """Insertar en preguntas_matriz con nivel='candidata'."""
        insertadas = 0
        with conn.cursor() as cur:
            for c in candidatas:
                pregunta_id = f"{c['inteligencia']}_{c['funcion'][0]}_{c['lente'][0]}_{uuid.uuid4().hex[:6]}"
                try:
                    cur.execute("""
                        INSERT INTO preguntas_matriz
                            (id, inteligencia, lente, funcion, texto, nivel)
                        VALUES (%s, %s, %s, %s, %s, 'candidata')
                        ON CONFLICT (id) DO NOTHING
                    """, [pregunta_id, c['inteligencia'], c['lente'],
                          c['funcion'], c['texto']])
                    if cur.rowcount > 0:
                        insertadas += 1
                except Exception:
                    pass

        conn.commit()
        return insertadas

    def listar_candidatas(self, conn=None) -> list:
        """Listar preguntas candidatas pendientes de aprobacion."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return []

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, inteligencia, lente, funcion, texto, created_at
                    FROM preguntas_matriz
                    WHERE nivel = 'candidata'
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                cols = ['id', 'inteligencia', 'lente', 'funcion', 'texto', 'created_at']
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception:
            return []
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def aprobar_candidata(self, pregunta_id: str, conn=None) -> dict:
        """Promover candidata a nivel 'base'."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE preguntas_matriz SET nivel = 'base'
                    WHERE id = %s AND nivel = 'candidata'
                """, [pregunta_id])
                ok = cur.rowcount > 0
            conn.commit()
            return {'aprobada': ok, 'pregunta_id': pregunta_id}
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


# Singleton
_reactor = None

def get_reactor() -> ReactorVN:
    global _reactor
    if _reactor is None:
        _reactor = ReactorVN()
    return _reactor
