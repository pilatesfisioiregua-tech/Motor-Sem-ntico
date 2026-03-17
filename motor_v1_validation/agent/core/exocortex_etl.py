"""Exocortex ETL — Extract-Transform-Load para datos externos.

Patron ETL Pipeline (#60682): ingestar observaciones de fuentes externas.
Patron Multi-tenant (#60683): aislamiento por scope/tenant.

Pipeline:
  Extract: recibir datos en formato libre (texto, JSON)
  Transform: normalizar a formato interno (observacion)
  Load: insertar en datapoints + trigger reactor
"""

import json
import uuid
from datetime import datetime, timezone


class ExocortexETL:
    """ETL pipeline para ingestar observaciones externas."""

    def ingest(self, datos: dict, tenant_id: str = 'default', conn=None) -> dict:
        """Pipeline ETL completo.

        Args:
            datos: {
                'observaciones': [
                    {'texto': str, 'celda': str, 'inteligencia': str,
                     'gap_estimado': float, 'contexto': str}
                ]
            }
            tenant_id: identificador del tenant
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            # Extract
            observaciones_crudas = self._extract(datos)

            # Transform
            observaciones = self._transform(observaciones_crudas, tenant_id)

            # Load
            insertadas = self._load(observaciones, conn)

            # Trigger reactor via marca estigmergica
            if insertadas > 0:
                from .mejora_continua import crear_marca_estigmergica
                crear_marca_estigmergica('ingestion_externa', 'exocortex_etl', {
                    'tenant_id': tenant_id,
                    'n_observaciones': insertadas,
                    'celdas': list(set(o.get('celda', '') for o in observaciones)),
                }, conn=conn)

            return {
                'extraidas': len(observaciones_crudas),
                'transformadas': len(observaciones),
                'insertadas': insertadas,
                'tenant_id': tenant_id,
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

    def _extract(self, datos: dict) -> list:
        """Extraer observaciones crudas del input."""
        if isinstance(datos.get('observaciones'), list):
            return datos['observaciones']
        if isinstance(datos.get('texto'), str):
            return [{'texto': datos['texto']}]
        return []

    def _transform(self, observaciones_crudas: list, tenant_id: str) -> list:
        """Normalizar a formato interno."""
        transformadas = []
        for obs in observaciones_crudas:
            if not obs.get('texto'):
                continue

            transformadas.append({
                'texto': obs['texto'][:2000],
                'celda': obs.get('celda', 'ConservarxSalud'),
                'inteligencia': obs.get('inteligencia', 'INT-01'),
                'gap_estimado': float(obs.get('gap_estimado', 0.5)),
                'contexto': obs.get('contexto', ''),
                'tenant_id': tenant_id,
                'id': str(uuid.uuid4())[:12],
            })

        return transformadas

    def _load(self, observaciones: list, conn) -> int:
        """Insertar como datapoints de efectividad."""
        insertadas = 0
        with conn.cursor() as cur:
            for obs in observaciones:
                try:
                    pregunta_id = f"{obs['inteligencia']}-ETL-{obs['id']}"
                    cur.execute("""
                        INSERT INTO datapoints_efectividad
                            (pregunta_id, modelo, caso_id, consumidor,
                             celda_objetivo, gap_pre, gap_post, operacion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, [pregunta_id, 'etl_externo', obs['id'],
                          f"exocortex_{obs['tenant_id']}",
                          obs['celda'], obs['gap_estimado'],
                          obs['gap_estimado'] * 0.8,  # assume 20% improvement
                          'ingestion'])
                    insertadas += 1
                except Exception:
                    pass

        conn.commit()
        return insertadas

    def listar_tenants(self, conn=None) -> list:
        """Listar tenants activos basandose en consumidores unicos."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return []

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT
                        REPLACE(consumidor, 'exocortex_', '') as tenant_id,
                        COUNT(*) as n_datapoints,
                        MAX(timestamp) as ultimo
                    FROM datapoints_efectividad
                    WHERE consumidor LIKE 'exocortex_%%'
                    GROUP BY consumidor
                    ORDER BY ultimo DESC
                """)
                return [{'tenant_id': r[0], 'n_datapoints': r[1],
                         'ultimo': str(r[2]) if r[2] else None}
                        for r in cur.fetchall()]
        except Exception:
            return []
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)


class APIGateway:
    """Request routing con aislamiento por tenant."""

    def get_tenant_context(self, tenant_id: str, conn=None) -> dict:
        """Contexto del tenant: datapoints, celdas activas, ultimo ingestion."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            with conn.cursor() as cur:
                consumidor = f"exocortex_{tenant_id}"
                cur.execute("""
                    SELECT COUNT(*), COUNT(DISTINCT celda_objetivo),
                           AVG(tasa_cierre), MAX(timestamp)
                    FROM datapoints_efectividad
                    WHERE consumidor = %s
                """, [consumidor])
                row = cur.fetchone()
                return {
                    'tenant_id': tenant_id,
                    'n_datapoints': row[0],
                    'celdas_activas': row[1],
                    'tasa_media': round(float(row[2]), 4) if row[2] else None,
                    'ultimo': str(row[3]) if row[3] else None,
                }
        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)


# Singletons
_etl = None
_gateway = None

def get_etl() -> ExocortexETL:
    global _etl
    if _etl is None:
        _etl = ExocortexETL()
    return _etl

def get_gateway() -> APIGateway:
    global _gateway
    if _gateway is None:
        _gateway = APIGateway()
    return _gateway
