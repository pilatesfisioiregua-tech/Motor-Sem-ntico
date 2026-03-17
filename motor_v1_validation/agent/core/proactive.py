"""Proactive health check — 5 checks rapidos al inicio de sesion. $0, sin LLM."""


def health_check(conn=None) -> list:
    """Run 5 quick health checks. Returns list of issues needing attention.

    Each item: {nivel: "info"|"warning"|"alert", mensaje: str, accion_sugerida: str}
    Empty list = everything OK.
    """
    own_conn = conn is None
    if own_conn:
        try:
            from .db_pool import get_conn
            conn = get_conn()
        except Exception:
            return []
        if not conn:
            return []

    alerts = []
    try:
        with conn.cursor() as cur:
            # 1. Presupuesto: gastado > 80% del limite?
            try:
                cur.execute("""
                    SELECT p.consumidor, p.limite_mensual_usd,
                           COALESCE(SUM(c.coste_total_usd), 0) as gastado
                    FROM presupuestos p
                    LEFT JOIN costes_llm c ON c.consumidor = p.consumidor
                        AND date_trunc('month', c.created_at) = date_trunc('month', now())
                    WHERE p.activo = true
                    GROUP BY p.consumidor, p.limite_mensual_usd
                """)
                for consumidor, limite, gastado in cur.fetchall():
                    if limite and limite > 0:
                        pct = gastado / limite * 100
                        if pct >= 100:
                            alerts.append({
                                "nivel": "alert",
                                "mensaje": f"Presupuesto EXCEDIDO para {consumidor}: ${gastado:.2f} de ${limite:.2f}",
                                "accion_sugerida": "Revisar costes y pausar ejecuciones no criticas",
                            })
                        elif pct >= 80:
                            alerts.append({
                                "nivel": "warning",
                                "mensaje": f"Presupuesto al {pct:.0f}% para {consumidor}: ${gastado:.2f} de ${limite:.2f}",
                                "accion_sugerida": "Monitorizar gasto y considerar modelos mas baratos",
                            })
            except Exception:
                pass

            # 2. Señales critical sin resolver > 24h
            try:
                cur.execute("""
                    SELECT tipo, mensaje FROM señales
                    WHERE resuelta = false AND severidad = 'critical'
                      AND created_at < now() - interval '24 hours'
                    ORDER BY created_at ASC LIMIT 3
                """)
                rows = cur.fetchall()
                if rows:
                    for tipo, mensaje in rows:
                        alerts.append({
                            "nivel": "alert",
                            "mensaje": f"Alerta critica sin resolver (>24h): {mensaje[:100]}",
                            "accion_sugerida": "Investigar y resolver la alerta",
                        })
            except Exception:
                pass

            # 3. Datapoints creciendo? (24h vs 48h)
            try:
                cur.execute("""
                    SELECT
                        COUNT(CASE WHEN timestamp > now() - interval '24 hours' THEN 1 END) as recientes,
                        COUNT(CASE WHEN timestamp BETWEEN now() - interval '48 hours'
                              AND now() - interval '24 hours' THEN 1 END) as anteriores
                    FROM datapoints_efectividad
                    WHERE consumidor NOT LIKE 'test%%'
                """)
                row = cur.fetchone()
                recientes, anteriores = row[0], row[1]
                if anteriores > 0 and recientes == 0:
                    alerts.append({
                        "nivel": "warning",
                        "mensaje": f"0 datapoints en las ultimas 24h (ayer hubo {anteriores})",
                        "accion_sugerida": "Verificar que el Motor esta ejecutando",
                    })
                elif anteriores > 0 and recientes > 0:
                    growth = recientes / anteriores
                    if growth > 1.5:
                        alerts.append({
                            "nivel": "info",
                            "mensaje": f"Datapoints creciendo: {recientes} hoy vs {anteriores} ayer",
                            "accion_sugerida": "Buen ritmo, nada que hacer",
                        })
            except Exception:
                pass

            # 4. Modelos con quality_score bajo
            try:
                cur.execute("""
                    SELECT modelo, quality_score FROM config_modelos
                    WHERE activo = true AND quality_score IS NOT NULL AND quality_score < 50
                """)
                for modelo, score in cur.fetchall():
                    alerts.append({
                        "nivel": "warning",
                        "mensaje": f"Modelo {modelo} con calidad baja ({score}/100)",
                        "accion_sugerida": "Considerar reemplazar por un modelo mejor",
                    })
            except Exception:
                pass

            # 5. Exocortex sin datos > 7 dias
            try:
                cur.execute("""
                    SELECT e.nombre
                    FROM exocortex_estado e
                    WHERE e.activo = true
                      AND NOT EXISTS (
                          SELECT 1 FROM datapoints_efectividad d
                          WHERE d.consumidor LIKE '%%' || LOWER(e.nombre) || '%%'
                            AND d.timestamp > now() - interval '7 days'
                      )
                """)
                rows = cur.fetchall()
                if rows:
                    nombres = ", ".join(r[0] for r in rows[:3])
                    alerts.append({
                        "nivel": "alert",
                        "mensaje": f"Pilotos sin datos en 7 dias: {nombres}",
                        "accion_sugerida": "Verificar conexion y configuracion de los pilotos",
                    })
            except Exception:
                pass

    except Exception:
        pass
    finally:
        if own_conn:
            try:
                from .db_pool import put_conn
                put_conn(conn)
            except Exception:
                pass

    return alerts
