"""Sensores Pilates — queries SQL para percepcion F1-F7.

Cada sensor es una query que lee datos del negocio y los convierte
en senales para el bus de percepcion del organismo.

Datos reales: om_clientes, om_grupos, om_contratos, om_sesiones,
om_asistencias, om_cobros, om_cancelaciones.
"""
from __future__ import annotations

from organismo.percepcion.bus import SensorSQL, SensorPizarra, BusPercepcion

TENANT_ID = "authentic_pilates"


# ============================================================
# SENSORES F1 — CONSERVACION (proteger lo que hay)
# ============================================================

SENSOR_FANTASMAS = SensorSQL(
    nombre="clientes_fantasma",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT c.id, c.nombre, c.apellidos,
               MAX(a.fecha) as ultima_asistencia,
               CURRENT_DATE - MAX(a.fecha) as dias_sin_venir
        FROM om_clientes c
        JOIN om_contratos ct ON ct.cliente_id = c.id AND ct.estado = 'activo'
        LEFT JOIN om_asistencias a ON a.cliente_id = c.id
        WHERE ct.tenant_id = $1
        GROUP BY c.id, c.nombre, c.apellidos
        HAVING MAX(a.fecha) < CURRENT_DATE - INTERVAL '21 days'
           OR MAX(a.fecha) IS NULL
        ORDER BY dias_sin_venir DESC NULLS FIRST
    """,
    tipo_senal="ALERTA",
    modo="estado",
    prioridad=2,
)

SENSOR_ENGAGEMENT_CAIDA = SensorSQL(
    nombre="engagement_caida",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        WITH asistencia_semanal AS (
            SELECT cliente_id,
                   date_trunc('week', fecha) as semana,
                   COUNT(*) as sesiones
            FROM om_asistencias
            WHERE tenant_id = $1
              AND fecha >= CURRENT_DATE - INTERVAL '4 weeks'
            GROUP BY cliente_id, date_trunc('week', fecha)
        ),
        tendencia AS (
            SELECT cliente_id,
                   MAX(CASE WHEN semana = date_trunc('week', CURRENT_DATE) THEN sesiones ELSE 0 END) as esta_semana,
                   MAX(CASE WHEN semana = date_trunc('week', CURRENT_DATE - INTERVAL '1 week') THEN sesiones ELSE 0 END) as semana_pasada
            FROM asistencia_semanal
            GROUP BY cliente_id
        )
        SELECT t.cliente_id, c.nombre, c.apellidos,
               t.esta_semana, t.semana_pasada,
               t.semana_pasada - t.esta_semana as caida
        FROM tendencia t
        JOIN om_clientes c ON c.id = t.cliente_id
        WHERE t.semana_pasada > 0
          AND t.esta_semana < t.semana_pasada
        ORDER BY caida DESC
    """,
    tipo_senal="ALERTA",
    modo="proceso",
    prioridad=3,
)

SENSOR_DEUDA = SensorSQL(
    nombre="deuda_silenciosa",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT c.id as cliente_id, c.nombre, c.apellidos,
               SUM(co.importe) as deuda_total,
               MIN(co.fecha_vencimiento) as primera_deuda,
               CURRENT_DATE - MIN(co.fecha_vencimiento) as dias_deuda
        FROM om_cobros co
        JOIN om_clientes c ON c.id = co.cliente_id
        WHERE co.tenant_id = $1
          AND co.estado = 'pendiente'
          AND co.fecha_vencimiento < CURRENT_DATE - INTERVAL '14 days'
        GROUP BY c.id, c.nombre, c.apellidos
        HAVING SUM(co.importe) > 60
        ORDER BY deuda_total DESC
    """,
    tipo_senal="ALERTA",
    modo="ley",
    prioridad=2,
)


# ============================================================
# SENSORES F2 — CAPTACION (atraer nuevos)
# ============================================================

SENSOR_NUEVOS_MES = SensorSQL(
    nombre="nuevos_clientes_mes",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT COUNT(*) as nuevos,
               date_trunc('month', ct.fecha_inicio) as mes
        FROM om_contratos ct
        WHERE ct.tenant_id = $1
          AND ct.fecha_inicio >= CURRENT_DATE - INTERVAL '3 months'
        GROUP BY date_trunc('month', ct.fecha_inicio)
        ORDER BY mes DESC
    """,
    tipo_senal="RESUMEN",
    modo="proceso",
    prioridad=5,
)

SENSOR_OCUPACION = SensorSQL(
    nombre="ocupacion_grupos",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT g.id, g.nombre, g.capacidad_max,
               COUNT(DISTINCT ct.cliente_id) as inscritos,
               ROUND(COUNT(DISTINCT ct.cliente_id)::numeric / NULLIF(g.capacidad_max, 0) * 100, 1) as pct_ocupacion
        FROM om_grupos g
        LEFT JOIN om_contratos ct ON ct.grupo_id = g.id AND ct.estado = 'activo'
        WHERE g.tenant_id = $1 AND g.estado = 'activo'
        GROUP BY g.id, g.nombre, g.capacidad_max
        ORDER BY pct_ocupacion ASC
    """,
    tipo_senal="RESUMEN",
    modo="propiedad",
    prioridad=4,
)


# ============================================================
# SENSORES F3 — DEPURACION (eliminar lo que sobra)
# ============================================================

SENSOR_GRUPOS_INFRAUTILIZADOS = SensorSQL(
    nombre="grupos_infrautilizados",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT g.id, g.nombre, g.capacidad_max, g.precio_mensual,
               COUNT(DISTINCT ct.cliente_id) as inscritos,
               g.precio_mensual * COUNT(DISTINCT ct.cliente_id) as ingreso_real,
               CASE WHEN COUNT(DISTINCT ct.cliente_id) <= 1 THEN 'critico'
                    WHEN COUNT(DISTINCT ct.cliente_id) <= 2 THEN 'bajo'
                    ELSE 'ok' END as estado_ocupacion
        FROM om_grupos g
        LEFT JOIN om_contratos ct ON ct.grupo_id = g.id AND ct.estado = 'activo'
        WHERE g.tenant_id = $1 AND g.estado = 'activo'
        GROUP BY g.id, g.nombre, g.capacidad_max, g.precio_mensual
        HAVING COUNT(DISTINCT ct.cliente_id) <= 2
        ORDER BY ingreso_real ASC
    """,
    tipo_senal="OPORTUNIDAD",
    modo="proceso",
    prioridad=3,
)

SENSOR_CANCELACIONES_RECIENTES = SensorSQL(
    nombre="cancelaciones_recientes",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT ca.id, c.nombre, c.apellidos, ca.motivo,
               ca.fecha_cancelacion, ca.reactivable
        FROM om_cancelaciones ca
        JOIN om_clientes c ON c.id = ca.cliente_id
        WHERE ca.tenant_id = $1
          AND ca.fecha_cancelacion >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY ca.fecha_cancelacion DESC
    """,
    tipo_senal="ALERTA",
    modo="evento",
    prioridad=3,
)


# ============================================================
# SENSORES F4 — ESTRATEGIA (decidir rumbo)
# ============================================================

SENSOR_REVENUE_SEMANAL = SensorSQL(
    nombre="revenue_semanal",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT date_trunc('week', co.fecha_pago) as semana,
               SUM(co.importe) as revenue,
               COUNT(*) as n_cobros,
               SUM(CASE WHEN co.metodo = 'tpv' THEN co.importe ELSE 0 END) as tpv,
               SUM(CASE WHEN co.metodo = 'bizum' THEN co.importe ELSE 0 END) as bizum,
               SUM(CASE WHEN co.metodo = 'efectivo' THEN co.importe ELSE 0 END) as efectivo
        FROM om_cobros co
        WHERE co.tenant_id = $1
          AND co.estado = 'pagado'
          AND co.fecha_pago >= CURRENT_DATE - INTERVAL '8 weeks'
        GROUP BY date_trunc('week', co.fecha_pago)
        ORDER BY semana DESC
    """,
    tipo_senal="RESUMEN",
    modo="propiedad",
    prioridad=4,
)


# ============================================================
# SENSORES F5 — IDENTIDAD (que nos hace unicos)
# ============================================================

SENSOR_ASISTENCIA_GLOBAL = SensorSQL(
    nombre="asistencia_global",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT COUNT(*) as total_asistencias,
               COUNT(DISTINCT cliente_id) as clientes_unicos,
               ROUND(AVG(CASE WHEN asistio THEN 1 ELSE 0 END) * 100, 1) as pct_asistencia,
               COUNT(*) FILTER (WHERE NOT asistio) as ausencias
        FROM om_asistencias
        WHERE tenant_id = $1
          AND fecha >= CURRENT_DATE - INTERVAL '4 weeks'
    """,
    tipo_senal="RESUMEN",
    modo="propiedad",
    prioridad=5,
)


# ============================================================
# SENSORES F6 — ADAPTACION (evolucionar)
# ============================================================

SENSOR_EVOLUCIONES = SensorSQL(
    nombre="evoluciones_cliente",
    fuente="exterocepcion",
    tenant_id=TENANT_ID,
    query="""
        SELECT ec.cliente_id, c.nombre, c.apellidos,
               ec.tipo_evaluacion, ec.fecha, ec.resultado,
               ec.notas
        FROM om_evoluciones_cliente ec
        JOIN om_clientes c ON c.id = ec.cliente_id
        WHERE ec.tenant_id = $1
          AND ec.fecha >= CURRENT_DATE - INTERVAL '3 months'
        ORDER BY ec.fecha DESC
        LIMIT 20
    """,
    tipo_senal="RESUMEN",
    modo="proceso",
    prioridad=5,
)


# ============================================================
# SENSORES INTERNOS (pizarras)
# ============================================================

SENSOR_ESTADO_GOMAS = SensorPizarra(
    nombre="estado_gomas",
    fuente="interocepcion",
    tenant_id=TENANT_ID,
    tipo_pizarra="estado",
)

SENSOR_DIAGNOSTICO = SensorPizarra(
    nombre="ultimo_diagnostico",
    fuente="interocepcion",
    tenant_id=TENANT_ID,
    tipo_pizarra="cognitiva",
    claves=["ultimo_diagnostico"],
)

SENSOR_IDENTIDAD = SensorPizarra(
    nombre="identidad_f5",
    fuente="propiocepcion_motora",
    tenant_id=TENANT_ID,
    tipo_pizarra="identidad",
)


# ============================================================
# BUS COMPLETO
# ============================================================

def crear_bus_pilates() -> BusPercepcion:
    """Crea el bus de percepcion completo para Pilates."""
    bus = BusPercepcion(tenant_id=TENANT_ID)

    # F1 Conservacion
    bus.registrar(SENSOR_FANTASMAS)
    bus.registrar(SENSOR_ENGAGEMENT_CAIDA)
    bus.registrar(SENSOR_DEUDA)

    # F2 Captacion
    bus.registrar(SENSOR_NUEVOS_MES)
    bus.registrar(SENSOR_OCUPACION)

    # F3 Depuracion
    bus.registrar(SENSOR_GRUPOS_INFRAUTILIZADOS)
    bus.registrar(SENSOR_CANCELACIONES_RECIENTES)

    # F4 Estrategia
    bus.registrar(SENSOR_REVENUE_SEMANAL)

    # F5 Identidad
    bus.registrar(SENSOR_ASISTENCIA_GLOBAL)

    # F6 Adaptacion
    bus.registrar(SENSOR_EVOLUCIONES)

    # Internos
    bus.registrar(SENSOR_ESTADO_GOMAS)
    bus.registrar(SENSOR_DIAGNOSTICO)
    bus.registrar(SENSOR_IDENTIDAD)

    return bus
