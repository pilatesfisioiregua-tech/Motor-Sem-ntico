"""Watchdog — Periodic system health check that auto-routes failures to Code OS.

Runs every N minutes. Checks all subsystems. When failures are detected,
creates self-healing tasks and optionally triggers Code OS to fix them.
"""

import asyncio
import time
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Check interval: 10 minutes
CHECK_INTERVAL_S = 600
# Only auto-fix issues with severity >= this threshold
AUTO_FIX_SEVERITY = "high"


class HealthCheck:
    """Single health check result."""
    def __init__(self, subsystem: str, status: str, message: str = "",
                 severity: str = "low", auto_fixable: bool = False,
                 fix_instruction: str = ""):
        self.subsystem = subsystem
        self.status = status  # "ok", "warning", "error"
        self.message = message
        self.severity = severity  # "low", "medium", "high", "critical"
        self.auto_fixable = auto_fixable
        self.fix_instruction = fix_instruction

    def to_dict(self):
        return {
            "subsystem": self.subsystem,
            "status": self.status,
            "message": self.message,
            "severity": self.severity,
            "auto_fixable": self.auto_fixable,
        }


class Watchdog:
    """System watchdog that checks health and triggers auto-remediation."""

    def __init__(self):
        self.last_check_ts = None
        self.last_results: List[Dict] = []
        self.issues_found = 0
        self.issues_fixed = 0
        self.running = False
        self._task = None

    def run_checks(self) -> List[HealthCheck]:
        """Run all health checks. Returns list of HealthCheck results."""
        checks = []

        # 1. Database connectivity
        checks.append(self._check_db())

        # 2. API endpoints responding
        checks.extend(self._check_endpoints())

        # 3. Autopoiesis cycle
        checks.append(self._check_autopoiesis())

        # 4. LLM API connectivity (OpenRouter)
        checks.append(self._check_llm_api())

        # 5. Cost budget
        checks.append(self._check_costs())

        # 6. Stale alerts accumulation
        checks.append(self._check_stale_alerts())

        # 7. Activity (datapoints in last 24h)
        checks.append(self._check_activity())

        self.last_check_ts = time.time()
        self.last_results = [c.to_dict() for c in checks]
        return checks

    def _check_db(self) -> HealthCheck:
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return HealthCheck("database", "error", "No DB connection",
                                   severity="critical", auto_fixable=False)
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                return HealthCheck("database", "ok", "Connected")
            finally:
                put_conn(conn)
        except Exception as e:
            return HealthCheck("database", "error", str(e),
                               severity="critical", auto_fixable=False)

    def _check_endpoints(self) -> List[HealthCheck]:
        """Quick internal check of critical endpoint handlers."""
        results = []
        critical_modules = [
            ("agent_loop", "core.agent_loop", "run_agent_loop"),
            ("intent", "core.intent", "translate_intent"),
            ("tools", "tools", "create_default_registry"),
        ]
        for name, module, func in critical_modules:
            try:
                import importlib
                mod = importlib.import_module(module)
                if hasattr(mod, func):
                    results.append(HealthCheck(name, "ok", f"{func} available"))
                else:
                    results.append(HealthCheck(name, "error",
                                               f"{func} not found in {module}",
                                               severity="high", auto_fixable=False))
            except Exception as e:
                results.append(HealthCheck(name, "error",
                                           f"Import failed: {e}",
                                           severity="high", auto_fixable=False))
        return results

    def _check_autopoiesis(self) -> HealthCheck:
        try:
            from .gestor_scheduler import get_scheduler
            auto = get_scheduler().check_autopoiesis()
            if auto.get("error"):
                return HealthCheck("autopoiesis", "error", auto["error"],
                                   severity="high", auto_fixable=True,
                                   fix_instruction="Verificar conexion DB y ejecutar /gestor/autopoiesis/reset-alertas")
            if auto.get("ciclo_roto"):
                failing = [k for k, v in auto.items()
                           if k.startswith("check_") and v is False]
                return HealthCheck("autopoiesis", "warning",
                                   f"Ciclo roto: {', '.join(failing)}",
                                   severity="medium", auto_fixable=True,
                                   fix_instruction="Consumir alertas stale y verificar actividad del Motor")
            return HealthCheck("autopoiesis", "ok", "Ciclo sano")
        except Exception as e:
            return HealthCheck("autopoiesis", "error", str(e), severity="medium")

    def _check_llm_api(self) -> HealthCheck:
        try:
            from .api import OPENROUTER_KEY
            if not OPENROUTER_KEY:
                return HealthCheck("llm_api", "error",
                                   "OPENROUTER_API_KEY not set",
                                   severity="critical", auto_fixable=False)
            # Quick connectivity test (no actual LLM call)
            import httpx
            resp = httpx.get("https://openrouter.ai/api/v1/models",
                             headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
                             timeout=10)
            if resp.status_code == 200:
                return HealthCheck("llm_api", "ok", "OpenRouter reachable")
            elif resp.status_code == 401:
                return HealthCheck("llm_api", "error", "API key invalid (401)",
                                   severity="critical", auto_fixable=False)
            else:
                return HealthCheck("llm_api", "warning",
                                   f"OpenRouter returned {resp.status_code}",
                                   severity="medium")
        except Exception as e:
            return HealthCheck("llm_api", "warning", f"Connectivity: {e}",
                               severity="medium")

    def _check_costs(self) -> HealthCheck:
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return HealthCheck("costs", "warning", "No DB", severity="low")
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(SUM(coste_input_usd + coste_output_usd), 0)
                        FROM costes_llm
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                    """)
                    cost_24h = float(cur.fetchone()[0])
                if cost_24h > 5.0:
                    return HealthCheck("costs", "warning",
                                       f"${cost_24h:.2f} en 24h (umbral: $5)",
                                       severity="medium")
                return HealthCheck("costs", "ok", f"${cost_24h:.2f} en 24h")
            finally:
                put_conn(conn)
        except Exception as e:
            return HealthCheck("costs", "warning", str(e), severity="low")

    def _check_stale_alerts(self) -> HealthCheck:
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return HealthCheck("alerts", "warning", "No DB", severity="low")
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM marcas_estigmergicas
                        WHERE consumida = false AND tipo = 'alerta'
                          AND created_at < NOW() - INTERVAL '1 hour'
                    """)
                    stale = cur.fetchone()[0]
                if stale > 5:
                    return HealthCheck("alerts", "warning",
                                       f"{stale} alertas sin consumir (>1h)",
                                       severity="medium", auto_fixable=True,
                                       fix_instruction="Consumir alertas stale via /gestor/autopoiesis/reset-alertas")
                return HealthCheck("alerts", "ok", f"{stale} alertas pendientes")
            finally:
                put_conn(conn)
        except Exception as e:
            return HealthCheck("alerts", "warning", str(e), severity="low")

    def _check_activity(self) -> HealthCheck:
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return HealthCheck("activity", "warning", "No DB", severity="low")
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM metricas
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                    """)
                    count = cur.fetchone()[0]
                if count == 0:
                    return HealthCheck("activity", "warning",
                                       "0 metricas en 24h — sistema inactivo",
                                       severity="low")
                return HealthCheck("activity", "ok", f"{count} metricas en 24h")
            finally:
                put_conn(conn)
        except Exception as e:
            return HealthCheck("activity", "warning", str(e), severity="low")

    def auto_remediate(self, checks: List[HealthCheck]) -> List[Dict]:
        """Auto-fix issues that are auto_fixable. Returns list of actions taken."""
        actions = []
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        fixable = [c for c in checks
                   if c.status in ("error", "warning")
                   and c.auto_fixable
                   and severity_order.get(c.severity, 0) >= severity_order.get(AUTO_FIX_SEVERITY, 3)]

        for check in fixable:
            action = self._try_fix(check)
            if action:
                actions.append(action)
                self.issues_fixed += 1

        return actions

    def _try_fix(self, check: HealthCheck) -> Dict:
        """Attempt to fix a specific issue."""
        if check.subsystem == "autopoiesis" and "alertas" in check.fix_instruction.lower():
            return self._fix_stale_alerts(check)
        elif check.subsystem == "alerts":
            return self._fix_stale_alerts(check)
        return None

    def _fix_stale_alerts(self, check: HealthCheck) -> Dict:
        """Consume stale autopoiesis alerts."""
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return {"action": "consume_stale_alerts", "result": "no_db"}
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE marcas_estigmergicas
                        SET consumida = true
                        WHERE consumida = false AND tipo = 'alerta'
                          AND created_at < NOW() - INTERVAL '1 hour'
                        RETURNING id
                    """)
                    consumed = cur.fetchall()
                conn.commit()
                logger.info(f"Watchdog: consumed {len(consumed)} stale alerts")
                return {"action": "consume_stale_alerts", "result": "ok",
                        "count": len(consumed)}
            finally:
                put_conn(conn)
        except Exception as e:
            return {"action": "consume_stale_alerts", "result": "error",
                    "error": str(e)}

    def route_to_codeos(self, checks: List[HealthCheck]) -> Dict:
        """Route unresolved issues to Code OS for deeper investigation."""
        unresolved = [c for c in checks if c.status == "error" and not c.auto_fixable]
        if not unresolved:
            return {"routed": 0}

        # Build a diagnostic prompt for Code OS
        issues_text = "\n".join(
            f"- [{c.severity.upper()}] {c.subsystem}: {c.message}"
            for c in unresolved
        )

        diagnostic_goal = (
            f"WATCHDOG AUTO-CHECK detectó {len(unresolved)} problemas:\n"
            f"{issues_text}\n\n"
            "Investiga cada problema. Para cada uno:\n"
            "1. db_query() para verificar estado actual\n"
            "2. Identifica root cause\n"
            "3. Si puedes arreglar (SQL, config) → hazlo\n"
            "4. Si no → documenta el problema y sugiere acción manual\n"
        )

        # Store for Code OS to pick up
        try:
            from .db_pool import get_conn, put_conn
            from .mejora_continua import crear_marca_estigmergica
            crear_marca_estigmergica('señal', 'watchdog', {
                'tipo': 'autocheck_issues',
                'issues': [c.to_dict() for c in unresolved],
                'diagnostic_goal': diagnostic_goal,
            })
            logger.info(f"Watchdog: routed {len(unresolved)} issues to Code OS")
        except Exception as e:
            logger.error(f"Watchdog: failed to route issues: {e}")

        return {"routed": len(unresolved), "goal": diagnostic_goal}

    def get_status(self) -> Dict:
        return {
            "running": self.running,
            "last_check": self.last_check_ts,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "last_results": self.last_results,
            "check_interval_s": CHECK_INTERVAL_S,
        }

    async def loop(self, delay_inicial_s: int = 120):
        """Periodic watchdog loop."""
        self.running = True
        logger.info(f"Watchdog iniciado (primer check en {delay_inicial_s}s)")

        await asyncio.sleep(delay_inicial_s)

        while self.running:
            try:
                checks = self.run_checks()
                errors = [c for c in checks if c.status in ("error", "warning")]
                self.issues_found += len(errors)

                if errors:
                    logger.warning(
                        f"Watchdog: {len(errors)} issues detected: "
                        + ", ".join(f"{c.subsystem}={c.status}" for c in errors)
                    )
                    # Auto-fix what we can
                    fixes = self.auto_remediate(checks)
                    if fixes:
                        logger.info(f"Watchdog: auto-fixed {len(fixes)} issues")

                    # Route remaining to Code OS
                    self.route_to_codeos(checks)
                else:
                    logger.info("Watchdog: all checks passed")

                await asyncio.sleep(CHECK_INTERVAL_S)

            except asyncio.CancelledError:
                self.running = False
                break
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                await asyncio.sleep(CHECK_INTERVAL_S)

    def stop(self):
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()


# Singleton
_watchdog = None

def get_watchdog() -> Watchdog:
    global _watchdog
    if _watchdog is None:
        _watchdog = Watchdog()
    return _watchdog
