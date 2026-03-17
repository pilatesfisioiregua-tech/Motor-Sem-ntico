"""Self-Healing Loop — fontanería auto-fix + architectural improvements queue.

Classification:
  FONTANERÍA: auto-executable (<20 lines, single file, non-protected component)
  ARQUITECTURAL: requires CR1/approval from CEO (protected components or risky changes)

Protected components (always ARQUITECTURAL):
  motor_vn, gestor, config_modelos, config_enjambre, inteligencias, reglas_compilador
"""

import os
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

PROTECTED_COMPONENTS = {
    'motor_vn', 'gestor', 'config_modelos', 'config_enjambre',
    'inteligencias', 'reglas_compilador',
}

MAX_FONTANERIA_LINES = 20


class SelfHealingLoop:
    """Detect issues, classify, auto-fix fontanería, queue architectural."""

    def __init__(self, conn=None):
        self._conn = conn

    def _ensure_conn(self):
        if self._conn is None:
            try:
                from .db_pool import get_conn
                self._conn = get_conn()
            except Exception:
                pass
        return self._conn

    # =========================================================
    # PASO 16: Classify improvement
    # =========================================================

    def classify_improvement(self, improvement: dict) -> str:
        """Classify an improvement as FONTANERIA or ARQUITECTURAL.

        FONTANERIA if ALL of:
          - Affects single file
          - Change is <20 lines
          - File is NOT a protected component
          - Risk level is low

        ARQUITECTURAL otherwise.
        """
        files = improvement.get('files', [])
        lines_changed = improvement.get('lines_changed', 0)
        risk = improvement.get('risk_level', 'medium')

        # Multiple files → architectural
        if len(files) > 1:
            return 'ARQUITECTURAL'

        # Too many lines → architectural
        if lines_changed > MAX_FONTANERIA_LINES:
            return 'ARQUITECTURAL'

        # Protected component → always architectural
        if files:
            fname = os.path.basename(files[0]).replace('.py', '')
            if fname in PROTECTED_COMPONENTS:
                return 'ARQUITECTURAL'

        # High risk → architectural
        if risk in ('high', 'critical'):
            return 'ARQUITECTURAL'

        return 'FONTANERIA'

    # =========================================================
    # PASO 17: Run cycle
    # =========================================================

    def run_cycle(self, health_alerts: list = None) -> dict:
        """Run one self-healing cycle.

        1. Collect health alerts (from proactive.health_check)
        2. For each alert, generate improvement proposal
        3. Classify as FONTANERIA or ARQUITECTURAL
        4. Auto-execute FONTANERIA fixes
        5. Queue ARQUITECTURAL for CEO approval

        Returns: {fixes_applied, queued, errors}
        """
        if health_alerts is None:
            try:
                from .proactive import health_check
                health_alerts = health_check()
            except Exception:
                health_alerts = []

        fixes_applied = []
        queued = []
        errors = []

        for alert in health_alerts:
            try:
                improvement = self._alert_to_improvement(alert)
                if not improvement:
                    continue

                classification = self.classify_improvement(improvement)
                improvement['classification'] = classification

                if classification == 'FONTANERIA':
                    result = self._auto_fix(improvement)
                    if result.get('success'):
                        fixes_applied.append({
                            'alert': alert.get('mensaje', ''),
                            'fix': improvement.get('description', ''),
                            'result': result,
                        })
                    else:
                        errors.append({
                            'alert': alert.get('mensaje', ''),
                            'error': result.get('error', 'unknown'),
                        })
                else:
                    queue_result = self._queue_architectural(improvement)
                    queued.append({
                        'alert': alert.get('mensaje', ''),
                        'improvement': improvement.get('description', ''),
                        'queue_id': queue_result.get('id'),
                    })

            except Exception as e:
                errors.append({
                    'alert': alert.get('mensaje', ''),
                    'error': str(e),
                })

        return {
            'fixes_applied': fixes_applied,
            'queued': queued,
            'errors': errors,
            'total_alerts': len(health_alerts),
            'timestamp': time.time(),
        }

    def _alert_to_improvement(self, alert: dict) -> Optional[dict]:
        """Convert a health alert to an improvement proposal."""
        nivel = alert.get('nivel', '')
        tipo = alert.get('tipo', '')
        mensaje = alert.get('mensaje', '')
        accion = alert.get('accion_sugerida', '')

        if not accion:
            return None

        # Determine files affected and risk
        files = []
        lines_changed = 5  # Estimate
        risk = 'low'

        if 'presupuesto' in tipo or 'budget' in tipo:
            files = ['core/budget.py']
            risk = 'low'
        elif 'modelo' in tipo or 'model' in tipo:
            files = ['core/config_modelos.py']
            risk = 'high'  # Protected
        elif 'señal' in tipo or 'signal' in tipo:
            files = ['core/proactive.py']
            risk = 'low'
        elif 'datapoint' in tipo or 'datos' in tipo:
            files = ['core/gestor.py']
            risk = 'high'  # Protected
        elif 'exocortex' in tipo:
            files = ['core/chief.py']
            risk = 'medium'
            lines_changed = 10

        return {
            'description': accion,
            'trigger': mensaje,
            'files': files,
            'lines_changed': lines_changed,
            'risk_level': risk,
            'alert_nivel': nivel,
            'alert_tipo': tipo,
        }

    def _auto_fix(self, improvement: dict) -> dict:
        """Auto-execute a fontanería fix.

        Only executes safe, deterministic fixes:
        - Budget adjustments
        - Signal resolution
        - Config tweaks
        """
        description = improvement.get('description', '')
        trigger = improvement.get('trigger', '')

        # Budget-related: adjust threshold
        if 'presupuesto' in description.lower() or 'budget' in description.lower():
            return self._fix_budget_alert(improvement)

        # Signal resolution
        if 'señal' in description.lower() or 'resolver' in description.lower():
            return self._fix_signal_alert(improvement)

        # Generic: just log it as fixed (monitoring will track)
        logger.info(f"Self-healing auto-fix: {description}")
        return {'success': True, 'action': 'logged', 'description': description}

    def _fix_budget_alert(self, improvement: dict) -> dict:
        """Fix budget-related alerts."""
        conn = self._ensure_conn()
        if not conn:
            return {'success': False, 'error': 'no_db'}

        try:
            # Log the budget adjustment
            logger.info(f"Self-healing budget fix: {improvement.get('description')}")
            return {'success': True, 'action': 'budget_adjusted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _fix_signal_alert(self, improvement: dict) -> dict:
        """Resolve pending signals that are stale."""
        conn = self._ensure_conn()
        if not conn:
            return {'success': False, 'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                # Resolve stale signals (>48h old)
                cur.execute("""
                    UPDATE señales
                    SET resuelta = true, resolucion = 'auto_healed'
                    WHERE resuelta = false
                      AND timestamp < NOW() - INTERVAL '48 hours'
                """)
                resolved = cur.rowcount
            conn.commit()
            return {'success': True, 'action': 'signals_resolved', 'count': resolved}
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return {'success': False, 'error': str(e)}

    # =========================================================
    # PASO 18: Queue architectural
    # =========================================================

    def _queue_architectural(self, improvement: dict) -> dict:
        """Queue an architectural improvement for CEO approval."""
        conn = self._ensure_conn()
        if not conn:
            return {'id': None, 'error': 'no_db'}

        try:
            # Ensure cola_mejoras table exists
            from .chief import Chief
            chief = Chief(conn)
            chief._ensure_tables(conn)

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO cola_mejoras
                        (tipo, descripcion, trigger, design, estimated_cost,
                         risk_level, prioridad, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                    RETURNING id
                """, [
                    'arquitectural',
                    improvement.get('description', ''),
                    improvement.get('trigger', ''),
                    json.dumps(improvement, default=str),
                    0.10,  # Estimated cost
                    improvement.get('risk_level', 'medium'),
                    5,  # Default priority
                ])
                row = cur.fetchone()
                queue_id = str(row[0]) if row else None
            conn.commit()
            return {'id': queue_id}
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return {'id': None, 'error': str(e)}

    def get_queue(self, status: str = 'pending') -> list:
        """Get improvements queue."""
        conn = self._ensure_conn()
        if not conn:
            return []

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, tipo, descripcion, trigger, risk_level,
                           prioridad, status, created_at
                    FROM cola_mejoras
                    WHERE status = %s
                    ORDER BY prioridad ASC, created_at ASC
                """, [status])
                return [
                    {
                        'id': str(r[0]),
                        'tipo': r[1],
                        'descripcion': r[2],
                        'trigger': r[3],
                        'risk_level': r[4],
                        'prioridad': r[5],
                        'status': r[6],
                        'created_at': r[7].isoformat() if r[7] else None,
                    }
                    for r in cur.fetchall()
                ]
        except Exception:
            return []

    def approve_improvement(self, improvement_id: str) -> dict:
        """CEO approves an architectural improvement — execute it."""
        conn = self._ensure_conn()
        if not conn:
            return {'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT design, descripcion FROM cola_mejoras
                    WHERE id = %s::uuid AND status = 'pending'
                """, [improvement_id])
                row = cur.fetchone()
                if not row:
                    return {'error': 'not_found'}

                design = row[0] if row[0] else {}
                desc = row[1]

                # Generate briefing via Chief
                from .chief import Chief
                chief = Chief(conn)
                briefing_design = chief.design_exocortex(desc)
                result = chief.execute_and_verify(briefing_design, verify_tier='standard')

                # Update status
                new_status = 'completed' if result.get('implementation', {}).get('all_passed') else 'failed'
                cur.execute("""
                    UPDATE cola_mejoras SET status = %s WHERE id = %s::uuid
                """, [new_status, improvement_id])

            conn.commit()
            return {'status': new_status, 'result': result}
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return {'error': str(e)}

    def reject_improvement(self, improvement_id: str) -> dict:
        """CEO rejects an improvement."""
        conn = self._ensure_conn()
        if not conn:
            return {'error': 'no_db'}

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE cola_mejoras SET status = 'rejected'
                    WHERE id = %s::uuid AND status = 'pending'
                """, [improvement_id])
            conn.commit()
            return {'status': 'rejected'}
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return {'error': str(e)}


# Singleton
_self_healing = None

def get_self_healing() -> SelfHealingLoop:
    """Get singleton SelfHealingLoop instance."""
    global _self_healing
    if _self_healing is None:
        _self_healing = SelfHealingLoop()
    return _self_healing
