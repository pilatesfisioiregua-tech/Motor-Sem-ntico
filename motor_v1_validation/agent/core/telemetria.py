"""Telemetria del sistema nervioso — registro de metricas y señales."""

import json
from datetime import datetime, timezone
from typing import Optional


def registrar_metrica(componente: str, evento: str, datos: dict, conn=None):
    """Registra una metrica en la tabla metricas.

    Args:
        componente: Quien genera la metrica (motor_vn, gestor, reactor_v4, code_os)
        evento: Tipo de evento (ejecucion, compilacion, poda, health_check)
        datos: Dict con datos del evento (latencia_ms, tokens_in, coste_usd, error, etc.)
        conn: Conexion DB (crea una si no se pasa)
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
                INSERT INTO metricas (componente, evento, datos)
                VALUES (%s, %s, %s::jsonb)
            """, [componente, evento, json.dumps(datos, default=str)])
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


def crear_señal(tipo: str, severidad: str, mensaje: str,
                datos: dict = None, conn=None):
    """Crea una señal (alerta, umbral, anomalia).

    Args:
        tipo: alerta | umbral | anomalia
        severidad: info | warning | critical
        mensaje: Descripcion humana
        datos: Contexto adicional
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
                INSERT INTO señales (tipo, severidad, mensaje, datos)
                VALUES (%s, %s, %s, %s::jsonb)
            """, [tipo, severidad, mensaje,
                  json.dumps(datos, default=str) if datos else None])
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


def evaluar_reglas(conn=None):
    """Evalua todas las reglas de deteccion activas.

    Lee metricas recientes y compara contra umbrales.
    Genera señales o mejoras segun la accion de cada regla.

    Returns:
        list de señales generadas
    """
    own_conn = conn is None
    if own_conn:
        from core.db_pool import get_conn
        conn = get_conn()
        if not conn:
            return []

    señales_generadas = []
    try:
        with conn.cursor() as cur:
            # Leer reglas activas
            cur.execute("SELECT id, nombre, condicion, accion FROM reglas_deteccion WHERE activa = true")
            reglas = cur.fetchall()

            for regla_id, nombre, condicion, accion in reglas:
                metrica_nombre = condicion.get('metrica', '')
                operador = condicion.get('operador', '>')
                umbral = condicion.get('umbral', 0)

                # Buscar metrica mas reciente
                cur.execute("""
                    SELECT datos FROM metricas
                    WHERE datos ? %s
                    ORDER BY created_at DESC LIMIT 1
                """, [metrica_nombre])
                row = cur.fetchone()
                if not row:
                    continue

                valor = row[0].get(metrica_nombre)
                if valor is None:
                    continue

                # Evaluar condicion
                triggered = False
                if operador == '>' and valor > umbral:
                    triggered = True
                elif operador == '<' and valor < umbral:
                    triggered = True
                elif operador == '=' and valor == umbral:
                    triggered = True

                if triggered:
                    msg = f"Regla '{nombre}' activada: {metrica_nombre}={valor} {operador} {umbral}"
                    if accion == 'señal':
                        crear_señal('umbral', 'warning', msg,
                                   {'regla': nombre, 'valor': valor, 'umbral': umbral}, conn)
                    elif accion == 'escalar':
                        crear_señal('alerta', 'critical', msg,
                                   {'regla': nombre, 'valor': valor, 'umbral': umbral}, conn)
                    elif accion == 'crear_mejora':
                        cur.execute("""
                            INSERT INTO cola_mejoras (tipo, descripcion, prioridad)
                            VALUES ('fontaneria', %s, 5)
                        """, [msg])
                    señales_generadas.append(msg)

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

    return señales_generadas


def propiocepcion(conn=None):
    """Estado completo del sistema nervioso.

    Returns:
        dict con estado de todos los componentes
    """
    own_conn = conn is None
    if own_conn:
        from core.db_pool import get_conn
        conn = get_conn()
        if not conn:
            return {"error": "No DB connection"}

    try:
        with conn.cursor() as cur:
            estado = {}

            # Matriz
            cur.execute("SELECT COUNT(*) FROM inteligencias")
            estado['inteligencias'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM preguntas_matriz")
            estado['preguntas_matriz'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM aristas_grafo")
            estado['aristas_grafo'] = cur.fetchone()[0]

            # Knowledge base
            cur.execute("SELECT COUNT(*) FROM knowledge_base")
            estado['knowledge_base_entries'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM knowledge_connections")
            estado['knowledge_connections'] = cur.fetchone()[0]

            # Gestor
            cur.execute("SELECT COUNT(*) FROM programas_compilados WHERE activo = true")
            estado['programas_activos'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM datapoints_efectividad")
            estado['datapoints_efectividad'] = cur.fetchone()[0]

            # Modelos
            cur.execute("SELECT COUNT(*) FROM config_modelos WHERE activo = true")
            estado['modelos_activos'] = cur.fetchone()[0]

            # Exocortex
            cur.execute("SELECT id, nombre, config->>'fase' as fase FROM exocortex_estado WHERE activo = true")
            estado['exocortex'] = [{'id': r[0], 'nombre': r[1], 'fase': r[2]} for r in cur.fetchall()]

            # Señales sin resolver
            cur.execute("SELECT COUNT(*) FROM señales WHERE resuelta = false")
            estado['señales_pendientes'] = cur.fetchone()[0]

            # Mejoras pendientes
            cur.execute("SELECT COUNT(*) FROM cola_mejoras WHERE estado = 'pendiente'")
            estado['mejoras_pendientes'] = cur.fetchone()[0]

            # Metricas recientes (ultima hora)
            cur.execute("""
                SELECT componente, COUNT(*) FROM metricas
                WHERE created_at > NOW() - INTERVAL '1 hour'
                GROUP BY componente
            """)
            estado['metricas_ultima_hora'] = {r[0]: r[1] for r in cur.fetchall()}

            # Ejecuciones recientes
            cur.execute("SELECT COUNT(*) FROM metricas WHERE componente = 'motor_vn' AND evento = 'ejecucion_completa' AND created_at > NOW() - INTERVAL '24 hours'")
            estado['ejecuciones_24h'] = cur.fetchone()[0]

            # Cobertura de la Matriz
            cur.execute("""
                SELECT
                    COUNT(DISTINCT inteligencia) as ints,
                    COUNT(DISTINCT lente) as lentes,
                    COUNT(DISTINCT funcion) as funciones,
                    COUNT(*) as total_preguntas
                FROM preguntas_matriz
            """)
            row = cur.fetchone()
            estado['cobertura_matriz'] = {
                'inteligencias': row[0],
                'lentes': row[1],
                'funciones': row[2],
                'total_preguntas': row[3]
            }

            return estado
    except Exception as e:
        return {"error": str(e)}
    finally:
        if own_conn:
            from core.db_pool import put_conn
            put_conn(conn)
