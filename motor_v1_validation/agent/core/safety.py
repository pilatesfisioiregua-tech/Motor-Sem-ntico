"""Safety module — protecciones para usuario no tecnico."""

import re
from typing import Optional


PROTECTED_TABLES = [
    "inteligencias",
    "config_modelos",
    "config_enjambre",
    "presupuestos",
]


def validate_mutation(sql: str) -> Optional[str]:
    """Check if SQL modifies a protected table. Returns warning or None if OK."""
    if not sql:
        return None

    sql_upper = sql.strip().upper()

    # Only check mutations
    if not any(sql_upper.startswith(kw) for kw in ["UPDATE", "DELETE", "INSERT", "ALTER", "TRUNCATE"]):
        return None

    sql_lower = sql.lower()
    for table in PROTECTED_TABLES:
        # Match table name as word boundary (not substring)
        if re.search(r'\b' + re.escape(table) + r'\b', sql_lower):
            action = sql_upper.split()[0]
            return (
                f"Esta accion ({action}) modifica '{table}' que es una tabla critica. "
                f"Confirmar antes de ejecutar."
            )

    return None


def validate_deploy() -> Optional[str]:
    """Before fly deploy, verify tests pass. Returns warning or None if OK."""
    import subprocess
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-x", "--tb=no", "-q"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            failed_lines = [l for l in result.stdout.splitlines() if "FAILED" in l]
            summary = failed_lines[0] if failed_lines else result.stdout[-200:]
            return f"Tests fallando — deploy bloqueado. {summary}"
    except FileNotFoundError:
        return "pytest no encontrado — no se puede verificar antes de deploy."
    except subprocess.TimeoutExpired:
        return "Tests tardaron >60s — deploy bloqueado por timeout."
    except Exception as e:
        return f"Error verificando tests: {e}"

    return None


def validate_cost(estimated_cost: float, budget_remaining: float) -> Optional[str]:
    """Warn if estimated cost exceeds 20% of remaining budget."""
    if budget_remaining <= 0:
        return f"Presupuesto agotado (${budget_remaining:.2f}). Esta accion costaria ${estimated_cost:.2f}."

    pct = (estimated_cost / budget_remaining) * 100
    if pct > 20:
        return (
            f"Esta accion costaria ~${estimated_cost:.2f}, "
            f"que es el {pct:.0f}% del presupuesto restante (${budget_remaining:.2f}). "
            f"Confirmar antes de ejecutar."
        )

    return None
