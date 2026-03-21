"""Gestor Scheduler — Flywheel + Autopoiesis.

Patrones aplicados:
  Flywheel (#60668): f(n+1) = f(n) * (1 + Delta(n))
  Autopoiesis (#60847): verificar que el sistema se auto-mantiene
"""

import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class GestorScheduler:
    """Scheduler adaptativo basado en Flywheel con check autopoietico."""

    def __init__(self):
        self.intervalo_actual_h = 24.0
        self.flywheel_history = []
        self.ultimo_loop_ts = None
        self.running = False
        self._task = None

    def calcular_proximo_intervalo(self) -> float:
        """Intervalo adaptativo en horas basado en Delta(n)."""
        if not self.flywheel_history:
            return 24.0

        _, _, delta = self.flywheel_history[-1]

        if delta is None:
            return 24.0

        if delta < -0.05:
            return 1.0
        elif delta > 0.10:
            return max(4.0, self.intervalo_actual_h * 0.7)
        elif delta > 0.02:
            return max(8.0, self.intervalo_actual_h * 0.85)
        else:
            return min(48.0, self.intervalo_actual_h * 1.2)

    def _calcular_delta(self, f_n: float) -> Optional[float]:
        """Calcular Delta(n) = (f(n) - f(n-1)) / f(n-1)."""
        if not self.flywheel_history:
            return None

        _, f_prev, _ = self.flywheel_history[-1]
        if f_prev and f_prev > 0:
            return round((f_n - f_prev) / f_prev, 6)
        return None

    def check_autopoiesis(self, conn=None) -> dict:
        """Verificar que el sistema se auto-mantiene (patron #60847).

        4 checks del ciclo autopoietico:
        1. Preguntas nuevas: hay preguntas activas en la Matriz?
        2. Gaps decrecientes: la media de gap_post esta bajando?
        3. Tasa subiendo: la tasa_cierre_media esta subiendo?
        4. Datapoints creciendo: hay mas datapoints que antes?
        """
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return {'error': 'no_db_connection', 'ciclo_roto': True}

        try:
            checks = {}
            with conn.cursor() as cur:
                # Check 1: Preguntas activas
                cur.execute("""
                    SELECT COUNT(*) FROM preguntas_matriz
                    WHERE nivel != 'podada'
                """)
                checks['preguntas_activas'] = cur.fetchone()[0]
                checks['check_preguntas'] = checks['preguntas_activas'] > 0

                # Check 2: Gaps decrecientes (ultimos 24h vs 24-48h)
                # Filter out seeds/test data to avoid false signals
                cur.execute("""
                    SELECT
                        AVG(CASE WHEN timestamp > NOW() - INTERVAL '24 hours' THEN gap_post END) as gap_reciente,
                        AVG(CASE WHEN timestamp BETWEEN NOW() - INTERVAL '48 hours' AND NOW() - INTERVAL '24 hours' THEN gap_post END) as gap_anterior
                    FROM datapoints_efectividad
                    WHERE consumidor NOT IN ('seed_exp4') AND consumidor NOT LIKE 'test%%'
                      AND calibrado = true
                """)
                row = cur.fetchone()
                gap_reciente = float(row[0]) if row[0] else None
                gap_anterior = float(row[1]) if row[1] else None
                if gap_reciente is not None and gap_anterior is not None:
                    checks['check_gaps'] = gap_reciente < gap_anterior
                    checks['gap_reciente'] = round(gap_reciente, 4)
                    checks['gap_anterior'] = round(gap_anterior, 4)
                else:
                    checks['check_gaps'] = None
                    checks['gap_reciente'] = gap_reciente
                    checks['gap_anterior'] = gap_anterior

                # Check 3: Tasa subiendo
                cur.execute("""
                    SELECT
                        AVG(CASE WHEN timestamp > NOW() - INTERVAL '24 hours' THEN tasa_cierre END) as tasa_reciente,
                        AVG(CASE WHEN timestamp BETWEEN NOW() - INTERVAL '48 hours' AND NOW() - INTERVAL '24 hours' THEN tasa_cierre END) as tasa_anterior
                    FROM datapoints_efectividad
                    WHERE consumidor NOT IN ('seed_exp4') AND consumidor NOT LIKE 'test%%'
                      AND calibrado = true
                """)
                row = cur.fetchone()
                tasa_reciente = float(row[0]) if row[0] else None
                tasa_anterior = float(row[1]) if row[1] else None
                if tasa_reciente is not None and tasa_anterior is not None:
                    checks['check_tasa'] = tasa_reciente > tasa_anterior
                    checks['tasa_reciente'] = round(tasa_reciente, 4)
                    checks['tasa_anterior'] = round(tasa_anterior, 4)
                else:
                    checks['check_tasa'] = None
                    checks['tasa_reciente'] = tasa_reciente
                    checks['tasa_anterior'] = tasa_anterior

                # Check 4: Datapoints creciendo (filter seeds/tests)
                cur.execute("""
                    SELECT
                        COUNT(CASE WHEN timestamp > NOW() - INTERVAL '24 hours' THEN 1 END) as dp_recientes,
                        COUNT(CASE WHEN timestamp BETWEEN NOW() - INTERVAL '48 hours' AND NOW() - INTERVAL '24 hours' THEN 1 END) as dp_anteriores
                    FROM datapoints_efectividad
                    WHERE consumidor NOT IN ('seed_exp4') AND consumidor NOT LIKE 'test%%'
                      AND calibrado = true
                """)
                row = cur.fetchone()
                checks['dp_recientes'] = row[0]
                checks['dp_anteriores'] = row[1]
                # 0 recientes = sin actividad (indeterminado), no declive
                if row[0] == 0:
                    checks['check_datapoints'] = None
                elif row[1] > 0:
                    checks['check_datapoints'] = row[0] >= row[1]
                else:
                    checks['check_datapoints'] = None

                # Check 5: Alertas estigmergicas pendientes
                cur.execute("""
                    SELECT COUNT(*) FROM marcas_estigmergicas
                    WHERE consumida = false AND tipo = 'alerta'
                      AND contenido->>'tipo' = 'autopoiesis_roto'
                """)
                alertas_pendientes = cur.fetchone()[0]
                checks['alertas_autopoiesis_pendientes'] = alertas_pendientes
                checks['check_alertas'] = alertas_pendientes == 0

            # Ciclo roto si alguno de los checks falla definitivamente
            active_checks = [v for k, v in checks.items()
                           if k.startswith('check_') and v is not None]
            checks['ciclo_roto'] = any(v is False for v in active_checks) if active_checks else False

            return checks

        except Exception as e:
            return {'error': str(e), 'ciclo_roto': True}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    async def ejecutar_ciclo(self) -> dict:
        """Ejecutar un ciclo del Gestor + metricas Flywheel."""
        from .gestor import get_gestor
        from .mejora_continua import crear_marca_estigmergica

        gestor = get_gestor()

        resultado = gestor.ejecutar_loop()

        # Evaluar reglas de detección (genera señales si hay umbrales cruzados)
        try:
            from .telemetria import evaluar_reglas
            señales_generadas = evaluar_reglas()
            if señales_generadas:
                logger.info(f"Reglas evaluadas: {len(señales_generadas)} señales generadas")
        except Exception as e:
            logger.warning(f"evaluar_reglas failed: {e}")

        # Reactor v4: generate observations from telemetry
        reactor_v4_result = None
        try:
            from .reactor_v4 import get_reactor_v4
            rv4 = get_reactor_v4()
            reactor_v4_result = rv4.observar()
            if reactor_v4_result.get('observaciones_generadas', 0) > 0:
                reactor_v4_result['preguntas'] = rv4.generar_preguntas()
                logger.info(f"Reactor v4: {reactor_v4_result['observaciones_generadas']} observaciones")
        except Exception as e:
            logger.warning(f"Reactor v4 failed: {e}")

        f_n = resultado.get('tasa_media_global', 0)
        delta_n = self._calcular_delta(f_n)

        ts = time.time()
        self.flywheel_history.append((ts, f_n, delta_n))
        self.ultimo_loop_ts = ts

        auto = self.check_autopoiesis()
        if auto.get('ciclo_roto'):
            # Check if data checks pass but stale alerts cause ciclo_roto
            data_checks = [v for k, v in auto.items()
                           if k.startswith('check_') and k != 'check_alertas' and v is not None]
            data_ok = all(v is not False for v in data_checks) if data_checks else False
            stale_alerts = auto.get('alertas_autopoiesis_pendientes', 0) > 0

            if data_ok and stale_alerts:
                # System self-healed: consume stale marks
                try:
                    from .db_pool import get_conn, put_conn
                    conn = get_conn()
                    if conn:
                        try:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    UPDATE marcas_estigmergicas
                                    SET consumida = true
                                    WHERE consumida = false AND tipo = 'alerta'
                                      AND contenido->>'tipo' = 'autopoiesis_roto'
                                """)
                            conn.commit()
                            logger.info("Alertas autopoiesis_roto consumidas (sistema auto-reparado)")
                            # Re-check autopoiesis to reflect clean state
                            auto = self.check_autopoiesis()
                        finally:
                            put_conn(conn)
                except Exception as e:
                    logger.error(f"Error consumiendo alertas stale: {e}")

            if auto.get('ciclo_roto'):
                logger.warning(f"Ciclo autopoietico ROTO: {auto}")
                # Solo crear alerta si no hay ya una pendiente (evitar acumulacion)
                if auto.get('alertas_autopoiesis_pendientes', 0) == 0:
                    crear_marca_estigmergica('alerta', 'gestor_scheduler', {
                        'tipo': 'autopoiesis_roto',
                        'checks': auto,
                        'ciclo': len(self.flywheel_history),
                    })

        self.intervalo_actual_h = self.calcular_proximo_intervalo()

        # Self-healing cycle after each Gestor cycle (Step 19)
        self_healing_result = None
        try:
            from .self_healing import get_self_healing
            sh = get_self_healing()
            self_healing_result = sh.run_cycle()
            if self_healing_result.get('fixes_applied'):
                logger.info(
                    f"Self-healing: {len(self_healing_result['fixes_applied'])} fixes applied, "
                    f"{len(self_healing_result.get('queued', []))} queued"
                )
        except Exception as e:
            logger.warning(f"Self-healing cycle failed: {e}")

        logger.info(
            f"Ciclo {len(self.flywheel_history)}: "
            f"f(n)={f_n:.4f}, Delta={delta_n}, "
            f"proximo_intervalo={self.intervalo_actual_h:.1f}h, "
            f"autopoiesis={'OK' if not auto.get('ciclo_roto') else 'ROTO'}"
        )

        return {
            'ciclo': len(self.flywheel_history),
            'f_n': f_n,
            'delta_n': delta_n,
            'intervalo_proximo_h': self.intervalo_actual_h,
            'autopoiesis': auto,
            'resultado_gestor': resultado,
            'self_healing': self_healing_result,
            'reactor_v4': reactor_v4_result,
        }

    async def loop_infinito(self, delay_inicial_s: int = 60):
        """Loop infinito con intervalos adaptativos."""
        self.running = True
        logger.info(f"Gestor Scheduler iniciado (primer ciclo en {delay_inicial_s}s)")

        # Esperar antes del primer ciclo para que la app arranque completamente
        if delay_inicial_s > 0:
            await asyncio.sleep(delay_inicial_s)

        while self.running:
            try:
                await self.ejecutar_ciclo()
                intervalo_s = self.intervalo_actual_h * 3600

                logger.info(f"Proximo ciclo en {self.intervalo_actual_h:.1f}h ({intervalo_s:.0f}s)")
                await asyncio.sleep(intervalo_s)

            except asyncio.CancelledError:
                logger.info("Gestor Scheduler cancelado")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error en ciclo del scheduler: {e}")
                await asyncio.sleep(3600)

    def stop(self):
        """Detener el scheduler."""
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()

    def get_estado(self) -> dict:
        """Estado actual del scheduler."""
        return {
            'running': self.running,
            'intervalo_actual_h': self.intervalo_actual_h,
            'ultimo_loop': datetime.fromtimestamp(self.ultimo_loop_ts, tz=timezone.utc).isoformat() if self.ultimo_loop_ts else None,
            'proximo_loop_en_h': self.intervalo_actual_h if self.running else None,
            'ciclos_completados': len(self.flywheel_history),
            'flywheel': [
                {
                    'timestamp': datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                    'f_n': round(f_n, 4) if f_n else 0,
                    'delta_n': round(delta_n, 6) if delta_n else None,
                }
                for ts, f_n, delta_n in self.flywheel_history[-20:]
            ],
        }


# Singleton
_scheduler = None

def get_scheduler() -> GestorScheduler:
    """Obtener instancia singleton del scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = GestorScheduler()
    return _scheduler
