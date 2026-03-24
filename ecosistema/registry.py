"""Registry del Ecosistema — Gestiona N organismos-tenant.

Cada tenant es un organismo independiente con su DB/schema.
Conectar un nuevo exocortex = nueva fila + seed de pizarras.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass
from typing import Optional

log = structlog.get_logger()


@dataclass
class TenantConfig:
    """Configuración de un tenant en el ecosistema."""
    tenant_id: str
    nombre: str
    sector: str                     # "wellness", "dental", "saas", etc.
    tamano: str = "micro"           # "micro", "pyme", "mediana"
    db_schema: Optional[str] = None # Schema dedicado (MVP) o DB URL (Scale)
    propietario: str = ""
    ubicacion: str = ""
    presupuesto_llm_semanal: float = 5.0
    autonomia: str = "notificar_4h" # "auto" | "notificar_4h" | "cr1"
    activo: bool = True


@dataclass
class TelemetriaOrganismo:
    """Lo que el ecosistema lee de cada organismo (NO datos del negocio).

    SÍ lee: estados ACD, gaps, recetas efectividad, patrones, costes.
    NO lee: nombres clientes, pagos, WA, reseñas, datos personales.
    """
    tenant_id: str
    sector: str
    tamano: str

    # Estado ACD anonimizado
    estado_diagnostico: str           # "E3_equilibrado_medio"
    lentes: dict                      # {"salud": 0.46, "sentido": 0.34, "continuidad": 0.40}
    gaps: list[str]                   # ["F3_baja", "F6_baja"]

    # Recetas y efectividad (el ORO del ecosistema)
    recetas_activas: list[dict]       # [{funcion, ints, tasa_cierre, n_ejecuciones}]
    recetas_fallidas: list[dict]
    patrones_aprendidos: list[dict]

    # Operativo
    coste_llm_semanal: float = 0.0
    cache_hit_rate: float = 0.0
    gomas_activas: int = 0
    agentes_silenciosos: list[str] = None
    drift_acd: float = 0.0

    def __post_init__(self):
        if self.agentes_silenciosos is None:
            self.agentes_silenciosos = []


class EcosistemaRegistry:
    """Gestiona N organismos, cada uno con su DB/schema.

    MVP: Schema por tenant en 1 Postgres.
    Scale: DB por tenant (Fly.io Postgres clusters).
    """

    def __init__(self, db_pool):
        self.pool = db_pool
        self._tenants: dict[str, TenantConfig] = {}

    async def cargar_tenants(self):
        """Carga todos los tenants activos del ecosistema."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT tenant_id, valor FROM om_pizarra
                WHERE tipo = 'dominio' AND clave = 'config'
            """)
            for row in rows:
                import json
                config = json.loads(row["valor"]) if isinstance(row["valor"], str) else row["valor"]
                self._tenants[row["tenant_id"]] = TenantConfig(
                    tenant_id=row["tenant_id"],
                    nombre=config.get("nombre", row["tenant_id"]),
                    sector=config.get("sector", "general"),
                    tamano=config.get("tamano", "micro"),
                    propietario=config.get("propietario", ""),
                    presupuesto_llm_semanal=config.get("presupuesto_semanal_llm", 5.0),
                    autonomia=config.get("autonomia", {}).get("nivel", "notificar_4h"),
                )
        log.info("ecosistema_tenants_cargados", count=len(self._tenants))

    async def registrar_tenant(self, config: TenantConfig) -> str:
        """Nuevo exocortex = nuevo schema + seed pizarras.

        Pasos:
        1. Crear schema dedicado
        2. Ejecutar migraciones base en ese schema
        3. Seed pizarra dominio con config del tenant
        4. Seed pizarra cognitiva con recetas genéricas del sector
        5. Primer diagnóstico ACD (con datos vacíos → E1 bajo)
        """
        tenant_id = config.tenant_id

        async with self.pool.acquire() as conn:
            # 1. Schema dedicado (MVP)
            schema = f"tenant_{tenant_id}"
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            log.info("ecosistema_schema_creado", tenant=tenant_id, schema=schema)

            # 3. Seed pizarra dominio
            import json
            await conn.execute("""
                INSERT INTO om_pizarra (tenant_id, tipo, clave, valor, origen)
                VALUES ($1, 'dominio', 'config', $2::jsonb, 'ecosistema')
                ON CONFLICT (tenant_id, tipo, clave, ciclo)
                DO UPDATE SET valor = $2::jsonb, updated_at = now()
            """, tenant_id, json.dumps({
                "nombre": config.nombre,
                "sector": config.sector,
                "tamano": config.tamano,
                "propietario": config.propietario,
                "ubicacion": config.ubicacion,
                "presupuesto_semanal_llm": config.presupuesto_llm_semanal,
                "autonomia": {"nivel": config.autonomia},
            }))

        self._tenants[tenant_id] = config
        log.info("ecosistema_tenant_registrado", tenant=tenant_id, sector=config.sector)
        return tenant_id

    async def obtener_telemetria(self, tenant_id: str) -> Optional[TelemetriaOrganismo]:
        """Lee telemetría anonimizada de un organismo (NO sus datos de negocio)."""
        config = self._tenants.get(tenant_id)
        if not config:
            return None

        async with self.pool.acquire() as conn:
            # Estado ACD más reciente
            estado_row = await conn.fetchrow("""
                SELECT valor FROM om_pizarra
                WHERE tenant_id = $1 AND tipo = 'estado' AND clave = 'diagnostico'
                ORDER BY updated_at DESC LIMIT 1
            """, tenant_id)

            # Recetas activas y su efectividad
            recetas_rows = await conn.fetch("""
                SELECT valor FROM om_pizarra
                WHERE tenant_id = $1 AND tipo = 'cognitiva'
                ORDER BY prioridad
            """, tenant_id)

        import json
        estado = json.loads(estado_row["valor"]) if estado_row else {}
        recetas = [json.loads(r["valor"]) if isinstance(r["valor"], str) else r["valor"]
                    for r in recetas_rows]

        return TelemetriaOrganismo(
            tenant_id=tenant_id,
            sector=config.sector,
            tamano=config.tamano,
            estado_diagnostico=estado.get("estado", "desconocido"),
            lentes=estado.get("lentes", {}),
            gaps=estado.get("gaps", []),
            recetas_activas=[r for r in recetas if r.get("tasa_cierre", 0) > 0.3],
            recetas_fallidas=[r for r in recetas if r.get("tasa_cierre", 0) <= 0.3],
            patrones_aprendidos=estado.get("patrones", []),
            coste_llm_semanal=estado.get("coste_semanal", 0),
            gomas_activas=estado.get("gomas_activas", 0),
            drift_acd=estado.get("drift", 0),
        )

    def listar_tenants(self) -> list[TenantConfig]:
        """Lista todos los tenants activos."""
        return [t for t in self._tenants.values() if t.activo]
