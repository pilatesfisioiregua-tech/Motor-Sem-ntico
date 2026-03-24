"""Organismo Pilates — wiring completo de la app en el OS.

Conecta todas las piezas:
  - Sensores F1-F7 (percepcion)
  - Prompts AF1-AF7 (procesamiento)
  - Director + Enjambre (cognitiva)
  - CircuitoGomas G1-G6 (meta)
  - CronOrganismo (ejecutiva)

Entry point: crear_organismo_pilates() → CronOrganismo listo para ejecutar.
"""
from __future__ import annotations

import structlog

from organismo.cognitiva.director import Director
from organismo.cognitiva.enjambre import Enjambre
from organismo.meta.circuito_gomas import CircuitoGomas
from organismo.ejecutiva.cron_organismo import CronOrganismo
from organismo.pizarras.pizarra import PizarraUnificada
from tenant.pilates.prompts import PROMPTS_AF
from tenant.pilates.sensores import TENANT_ID

log = structlog.get_logger()


# Sensor queries por funcion para inyectar en AF
SENSOR_QUERIES_AF = {
    "F1": {
        "fantasmas": """
            SELECT c.id, c.nombre, c.apellidos,
                   CURRENT_DATE - MAX(a.fecha) as dias_sin_venir
            FROM om_clientes c
            JOIN om_contratos ct ON ct.cliente_id = c.id AND ct.estado = 'activo'
            LEFT JOIN om_asistencias a ON a.cliente_id = c.id
            WHERE ct.tenant_id = $1
            GROUP BY c.id HAVING MAX(a.fecha) < CURRENT_DATE - 21 OR MAX(a.fecha) IS NULL
        """,
    },
    "F2": {
        "ocupacion": """
            SELECT g.nombre, g.capacidad_max,
                   COUNT(DISTINCT ct.cliente_id) as inscritos
            FROM om_grupos g
            LEFT JOIN om_contratos ct ON ct.grupo_id = g.id AND ct.estado = 'activo'
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            GROUP BY g.id
        """,
    },
    "F3": {
        "infrautilizados": """
            SELECT g.nombre, g.capacidad_max,
                   COUNT(DISTINCT ct.cliente_id) as inscritos
            FROM om_grupos g
            LEFT JOIN om_contratos ct ON ct.grupo_id = g.id AND ct.estado = 'activo'
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            GROUP BY g.id HAVING COUNT(DISTINCT ct.cliente_id) <= 2
        """,
    },
    "F4": {
        "revenue": """
            SELECT date_trunc('week', co.fecha_pago) as semana,
                   SUM(co.importe) as revenue
            FROM om_cobros co
            WHERE co.tenant_id = $1 AND co.estado = 'pagado'
              AND co.fecha_pago >= CURRENT_DATE - 56
            GROUP BY 1 ORDER BY 1 DESC
        """,
    },
    "F5": {
        "asistencia": """
            SELECT ROUND(AVG(CASE WHEN asistio THEN 1 ELSE 0 END) * 100, 1) as pct
            FROM om_asistencias
            WHERE tenant_id = $1 AND fecha >= CURRENT_DATE - 28
        """,
    },
    "F6": {
        "evoluciones": """
            SELECT ec.cliente_id, c.nombre, ec.tipo_evaluacion, ec.resultado
            FROM om_evoluciones_cliente ec
            JOIN om_clientes c ON c.id = ec.cliente_id
            WHERE ec.tenant_id = $1 AND ec.fecha >= CURRENT_DATE - 90
            ORDER BY ec.fecha DESC LIMIT 10
        """,
    },
    "F7": {
        "decisiones_instructor": """
            SELECT COUNT(*) FILTER (WHERE autor != 'Jesus') as autonomas,
                   COUNT(*) FILTER (WHERE autor = 'Jesus') as consultadas
            FROM om_decisiones
            WHERE tenant_id = $1 AND fecha >= CURRENT_DATE - 28
        """,
    },
}


def crear_organismo_pilates() -> CronOrganismo:
    """Crea el organismo completo de Authentic Pilates.

    Returns:
        CronOrganismo listo para ejecutar ciclos semanales.
    """
    cron = CronOrganismo(
        tenant_id=TENANT_ID,
        system_prompts=PROMPTS_AF,
        sensor_queries=SENSOR_QUERIES_AF,
    )

    log.info("pilates.organismo_creado",
             tenant=TENANT_ID,
             funciones=list(PROMPTS_AF.keys()),
             sensores=sum(len(v) for v in SENSOR_QUERIES_AF.values()))

    return cron


async def instalar_pilates_en_os():
    """Instala Pilates como app en el OS OMNI-MIND.

    Ejecuta:
      1. Onboarding (seeds pizarras)
      2. Registrar en ecosistema
      3. Seed recetas especificas
    """
    from tenant.onboarding import onboarding_tenant
    from tenant.pilates.app import MANIFIESTO
    from tenant.pilates.recetas import RECETAS_PILATES

    # 1. Onboarding base
    resultado = await onboarding_tenant(
        tenant_id=TENANT_ID,
        nombre=MANIFIESTO.nombre,
        sector=MANIFIESTO.sector,
        propietario=MANIFIESTO.propietario,
        ubicacion=MANIFIESTO.ubicacion,
        telefono=MANIFIESTO.telefono,
        email=MANIFIESTO.email,
        presupuesto_llm_semanal=MANIFIESTO.presupuesto_semanal,
        autonomia=MANIFIESTO.autonomia,
    )

    # 2. Seed recetas especificas Pilates
    pizarra = PizarraUnificada(TENANT_ID)
    for clave, receta in RECETAS_PILATES.items():
        await pizarra.escribir("cognitiva", f"receta_{clave}", receta)

    # 3. Seed identidad F5
    await pizarra.escribir("identidad", "esencia", {
        "nombre": "Authentic Pilates",
        "metodo": "EEDAP",
        "diferenciador": "Fisio + Pilates, visión terapéutica, no fitness",
        "valores": ["cercanía", "rigor_terapéutico", "personalización", "comunidad"],
        "anti_identidad": ["gimnasio", "fitness_genérico", "franquicia", "precio_bajo"],
        "ubicacion": "Albelda de Iregua, La Rioja",
        "tono": "coloquial, tuteo, vecino",
    })

    # 4. Seed diagnostico actual
    await pizarra.escribir("cognitiva", "ultimo_diagnostico", {
        "estado": "E3_desequilibrado",
        "scores": {
            "F1": {"score": 6.7, "objetivo": 8.0, "lente": "salud"},
            "F2": {"score": 9.0, "objetivo": 9.0, "lente": "salud"},
            "F3": {"score": 4.0, "objetivo": 7.0, "lente": "continuidad"},
            "F4": {"score": 4.0, "objetivo": 7.0, "lente": "continuidad"},
            "F5": {"score": 5.3, "objetivo": 7.0, "lente": "sentido"},
            "F6": {"score": 8.5, "objetivo": 8.5, "lente": "salud"},
            "F7": {"score": 7.5, "objetivo": 8.0, "lente": "continuidad"},
        },
        "gap_critico": "F3",
        "nota": "E3 desequilibrado: F3/F4/F5 criticas vs F2/F6 excelentes",
    })

    log.info("pilates.instalado_en_os",
             recetas=len(RECETAS_PILATES),
             resultado=resultado)

    return resultado
