"""Propagador de cambios — cascade updates cross-table.

Patron Cascade (#60679): cuando una tabla cambia, propagar a dependientes.
Patron Event Propagation (#83761): notificar componentes afectados.

Grafo de dependencias:
  preguntas_matriz → programas_compilados (recompilar si pregunta cambia)
  config_modelos → config_enjambre (actualizar modelos en tiers)
  datapoints_efectividad → pregunta_efectividad (refrescar vista)
"""

import json
from datetime import datetime, timezone


DEPENDENCIAS = {
    'preguntas_matriz': ['programas_compilados', 'aristas_grafo'],
    'config_modelos': ['config_enjambre'],
    'datapoints_efectividad': ['pregunta_efectividad'],
}


class Propagador:
    """Propaga cambios entre tablas manteniendo consistencia."""

    def propagar(self, tabla_origen: str, cambios: list, conn=None) -> dict:
        """Propagar cambios de tabla_origen a todas las dependientes.

        Args:
            tabla_origen: nombre de la tabla que cambio
            cambios: lista de {tipo: 'update'|'delete', ids: [...]}
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            resultado = {'origen': tabla_origen, 'propagaciones': {}}
            dependientes = DEPENDENCIAS.get(tabla_origen, [])

            for dep in dependientes:
                if dep == 'programas_compilados':
                    n = self._recompilar_programas_afectados(cambios, conn)
                    resultado['propagaciones'][dep] = n
                elif dep == 'aristas_grafo':
                    n = self._actualizar_aristas(cambios, conn)
                    resultado['propagaciones'][dep] = n
                elif dep == 'config_enjambre':
                    n = self._actualizar_enjambre(cambios, conn)
                    resultado['propagaciones'][dep] = n
                elif dep == 'pregunta_efectividad':
                    self._refrescar_vista(conn)
                    resultado['propagaciones'][dep] = 'refreshed'

            # Log
            from .mejora_continua import log_gestor
            log_gestor('propagacion', {
                'tabla_origen': tabla_origen,
                'n_cambios': len(cambios),
                'propagaciones': resultado['propagaciones'],
            }, nivel='auto', conn=conn)

            return resultado

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

    def verificar_consistencia(self, conn=None) -> dict:
        """Verificar que todas las tablas estan sincronizadas."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection'}

        try:
            checks = {}
            with conn.cursor() as cur:
                # Check 1: Programas que referencian preguntas podadas/obsoletas
                cur.execute("""
                    SELECT COUNT(*) FROM programas_compilados pc
                    WHERE pc.activo = true
                      AND EXISTS (
                          SELECT 1 FROM preguntas_matriz pm
                          WHERE pm.nivel IN ('podada', 'obsoleta', 'expirada')
                            AND pc.programa::text LIKE '%%' || pm.id || '%%'
                      )
                """)
                checks['programas_con_preguntas_inactivas'] = cur.fetchone()[0]

                # Check 2: Config enjambre con modelos inactivos
                cur.execute("""
                    SELECT tier, modelos FROM config_enjambre
                """)
                modelos_inactivos = 0
                for row in cur.fetchall():
                    modelos_raw = row[1] if row[1] else []
                    # modelos puede ser list (psycopg2 array) o string
                    if isinstance(modelos_raw, list):
                        modelos = [m for m in modelos_raw if m]
                    elif isinstance(modelos_raw, str):
                        modelos = [m.strip() for m in modelos_raw.strip('{}').split(',') if m.strip()]
                    else:
                        modelos = []
                    for m in modelos:
                        if m == 'all':
                            continue
                        cur.execute("""
                            SELECT COUNT(*) FROM config_modelos
                            WHERE modelo = %s AND activo = true
                        """, [m])
                        if cur.fetchone()[0] == 0:
                            modelos_inactivos += 1
                checks['enjambre_modelos_inactivos'] = modelos_inactivos

                # Check 3: Datapoints huerfanos (pregunta_id no existe)
                cur.execute("""
                    SELECT COUNT(*) FROM datapoints_efectividad de
                    WHERE NOT EXISTS (
                        SELECT 1 FROM preguntas_matriz pm WHERE pm.id = de.pregunta_id
                    )
                """)
                checks['datapoints_huerfanos'] = cur.fetchone()[0]

            checks['consistente'] = all(v == 0 for v in checks.values())
            return checks

        except Exception as e:
            return {'error': str(e)}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def _recompilar_programas_afectados(self, cambios: list, conn) -> int:
        """Recompilar programas que usan preguntas modificadas."""
        ids_afectados = []
        for c in cambios:
            ids_afectados.extend(c.get('ids', []))

        if not ids_afectados:
            return 0

        recompilados = 0
        with conn.cursor() as cur:
            for pid in ids_afectados:
                cur.execute("""
                    UPDATE programas_compilados
                    SET compilado_at = NOW(), version = version + 1
                    WHERE activo = true AND programa::text LIKE %s
                """, [f'%{pid}%'])
                recompilados += cur.rowcount

        conn.commit()
        return recompilados

    def _actualizar_aristas(self, cambios: list, conn) -> int:
        """Recalcular pesos de aristas para preguntas modificadas."""
        # Las aristas se recalculan implicitamente en el proximo ciclo del Gestor
        return 0

    def _actualizar_enjambre(self, cambios: list, conn) -> int:
        """Actualizar config_enjambre cuando cambian modelos."""
        # Los tiers se actualizan en paso 6 del Gestor
        return 0

    def _refrescar_vista(self, conn):
        """Refrescar vista materializada pregunta_efectividad."""
        try:
            with conn.cursor() as cur:
                cur.execute("REFRESH MATERIALIZED VIEW pregunta_efectividad")
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass


# Singleton
_propagador = None

def get_propagador() -> Propagador:
    global _propagador
    if _propagador is None:
        _propagador = Propagador()
    return _propagador
