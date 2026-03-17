"""Mejora continua — sistema inmune del sistema nervioso.

3 niveles (Maestro v3 §8.5):
  Nivel 1 — Fontaneria (auto-aprobable): retry, latencia, patches < 20 lineas
  Nivel 2 — Arquitectural (CR1 siempre): nuevas preguntas, cambios de modelo
  Nivel 3 — Auto-evolucion (semillas dormidas + CR1): el sistema crece solo

Este modulo implementa Nivel 1 y prepara Nivel 2.
"""

import json
from datetime import datetime, timezone


def detectar_mejoras(conn=None):
    """Analiza metricas y señales para detectar mejoras necesarias.

    Revisa:
    1. Metricas de las ultimas 24h
    2. Señales sin resolver
    3. Datapoints de efectividad (preguntas debiles)
    4. Patrones repetidos de error

    Returns:
        list de mejoras detectadas
    """
    own_conn = conn is None
    if own_conn:
        from core.db_pool import get_conn
        conn = get_conn()
        if not conn:
            return []

    mejoras = []
    try:
        with conn.cursor() as cur:
            # 1. Preguntas muertas (n>10, tasa<0.05)
            cur.execute("""
                SELECT pregunta_id, modelo, celda_objetivo,
                       COUNT(*) as n, AVG(tasa_cierre) as tasa
                FROM datapoints_efectividad
                GROUP BY pregunta_id, modelo, celda_objetivo
                HAVING COUNT(*) > 10 AND AVG(tasa_cierre) < 0.05
            """)
            for row in cur.fetchall():
                mejoras.append({
                    'tipo': 'fontaneria',
                    'descripcion': f"Pregunta muerta: {row[0]} con modelo {row[1]} en {row[2]} (n={row[3]}, tasa={row[4]:.3f})",
                    'prioridad': 3,
                    'accion': 'poda_pregunta',
                    'datos': {'pregunta_id': row[0], 'modelo': row[1], 'celda': row[2]},
                })

            # 2. Preguntas potentes (n>10, tasa>0.40)
            cur.execute("""
                SELECT pregunta_id, modelo, celda_objetivo,
                       COUNT(*) as n, AVG(tasa_cierre) as tasa
                FROM datapoints_efectividad
                GROUP BY pregunta_id, modelo, celda_objetivo
                HAVING COUNT(*) > 10 AND AVG(tasa_cierre) > 0.40
            """)
            for row in cur.fetchall():
                mejoras.append({
                    'tipo': 'fontaneria',
                    'descripcion': f"Pregunta potente: {row[0]} con {row[1]} en {row[2]} (n={row[3]}, tasa={row[4]:.3f}). Promover a Tier 1.",
                    'prioridad': 7,
                    'accion': 'promocion_pregunta',
                    'datos': {'pregunta_id': row[0], 'modelo': row[1], 'celda': row[2]},
                })

            # 3. Señales criticas sin resolver >24h
            cur.execute("""
                SELECT id, mensaje FROM señales
                WHERE resuelta = false
                  AND severidad = 'critical'
                  AND created_at < NOW() - INTERVAL '24 hours'
            """)
            for row in cur.fetchall():
                mejoras.append({
                    'tipo': 'arquitectural',
                    'descripcion': f"Señal critica sin resolver >24h: {row[1]}",
                    'prioridad': 9,
                    'accion': 'escalar',
                    'datos': {'señal_id': row[0]},
                })

            # 4. Celdas debiles (ninguna pregunta > 0.20 tasa)
            cur.execute("""
                SELECT celda_objetivo, MAX(AVG_tasa) as mejor_tasa
                FROM (
                    SELECT celda_objetivo, AVG(tasa_cierre) as AVG_tasa
                    FROM datapoints_efectividad
                    GROUP BY celda_objetivo, pregunta_id
                ) sub
                GROUP BY celda_objetivo
                HAVING MAX(AVG_tasa) < 0.20
            """)
            for row in cur.fetchall():
                mejoras.append({
                    'tipo': 'arquitectural',
                    'descripcion': f"Celda debil: {row[0]} (mejor tasa={row[1]:.3f}). Necesita preguntas nuevas o modelo diferente.",
                    'prioridad': 6,
                    'accion': 'investigar_celda',
                    'datos': {'celda': row[0]},
                })

            # Insertar mejoras detectadas en cola_mejoras
            for mejora in mejoras:
                cur.execute("""
                    INSERT INTO cola_mejoras (tipo, descripcion, prioridad)
                    VALUES (%s, %s, %s)
                """, [mejora['tipo'], mejora['descripcion'], mejora['prioridad']])

        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        if own_conn:
            from core.db_pool import put_conn
            put_conn(conn)

    return mejoras


def crear_marca_estigmergica(tipo: str, origen: str, contenido: dict, conn=None):
    """Crea una marca estigmergica para comunicacion entre componentes.

    Tipos: hallazgo, sintesis, alerta, señal
    Origen: gestor, motor_vn, reactor_v4, code_os, etc.
    """
    own_conn = conn is None
    if own_conn:
        from core.db_pool import get_conn
        conn = get_conn()
        if not conn:
            return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO marcas_estigmergicas (tipo, origen, contenido)
                VALUES (%s, %s, %s::jsonb)
            """, [tipo, origen, json.dumps(contenido, default=str)])
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        if own_conn:
            from core.db_pool import put_conn
            put_conn(conn)


def consumir_marcas(tipo: str = None, limit: int = 10, conn=None) -> list:
    """Lee y consume marcas estigmergicas no consumidas.

    Returns:
        list de marcas consumidas
    """
    own_conn = conn is None
    if own_conn:
        from core.db_pool import get_conn
        conn = get_conn()
        if not conn:
            return []

    try:
        with conn.cursor() as cur:
            if tipo:
                cur.execute("""
                    UPDATE marcas_estigmergicas SET consumida = true
                    WHERE consumida = false AND tipo = %s
                    RETURNING id, tipo, origen, contenido, created_at
                """, [tipo])
            else:
                cur.execute("""
                    UPDATE marcas_estigmergicas SET consumida = true
                    WHERE consumida = false
                    RETURNING id, tipo, origen, contenido, created_at
                """)
            marcas = [{'id': r[0], 'tipo': r[1], 'origen': r[2],
                       'contenido': r[3], 'created_at': r[4]}
                      for r in cur.fetchall()]
        conn.commit()
        return marcas
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return []
    finally:
        if own_conn:
            from core.db_pool import put_conn
            put_conn(conn)


def log_gestor(accion: str, detalle: dict, nivel: str = 'auto', conn=None):
    """Registra accion del Gestor en log de auditoria."""
    own_conn = conn is None
    if own_conn:
        from core.db_pool import get_conn
        conn = get_conn()
        if not conn:
            return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO log_gestor (accion, detalle, nivel)
                VALUES (%s, %s::jsonb, %s)
            """, [accion, json.dumps(detalle, default=str), nivel])
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        if own_conn:
            from core.db_pool import put_conn
            put_conn(conn)
