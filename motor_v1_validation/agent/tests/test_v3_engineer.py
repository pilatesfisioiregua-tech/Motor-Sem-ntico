"""Test E2E Fase 0 — Ingeniero Experto: intent, reporter, safety, proactive."""

import os
import sys

# Ensure agent/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================
# Intent translator
# ============================================================

def test_intent_coste():
    from core.intent import translate_intent
    r = translate_intent("cuánto he gastado este mes", {})
    assert r["category"] == "coste", f"Expected 'coste', got {r['category']}"
    assert r["technical_goal"], "Missing technical_goal"
    assert r["explanation_for_user"], "Missing explanation"


def test_intent_rendimiento():
    from core.intent import translate_intent
    r = translate_intent("el sistema va lento", {})
    assert r["category"] == "rendimiento", f"Expected 'rendimiento', got {r['category']}"


def test_intent_datos():
    from core.intent import translate_intent
    r = translate_intent("los pilotos no tienen datos", {})
    assert r["category"] == "datos", f"Expected 'datos', got {r['category']}"


def test_intent_feature():
    from core.intent import translate_intent
    r = translate_intent("quiero crear un endpoint nuevo", {})
    assert r["category"] == "feature", f"Expected 'feature', got {r['category']}"


def test_intent_error():
    from core.intent import translate_intent
    r = translate_intent("el motor no funciona, da error", {})
    assert r["category"] == "error", f"Expected 'error', got {r['category']}"


def test_intent_estado():
    from core.intent import translate_intent
    r = translate_intent("cómo está el sistema", {})
    assert r["category"] == "estado", f"Expected 'estado', got {r['category']}"


def test_intent_diagnostico():
    from core.intent import translate_intent
    r = translate_intent("por qué falla el autopoiesis", {})
    assert r["category"] == "diagnostico", f"Expected 'diagnostico', got {r['category']}"


def test_intent_passthrough_technical():
    from core.intent import translate_intent
    r = translate_intent("SELECT * FROM metricas LIMIT 5", {})
    assert r["category"] is None, "Technical input should pass through without category"
    assert r["technical_goal"] == "SELECT * FROM metricas LIMIT 5"


# ============================================================
# Reporter
# ============================================================

def test_reporter_summarize_done():
    from core.reporter import Reporter
    r = Reporter()
    summary = r.summarize_session({
        "stop_reason": "DONE",
        "iterations": 5,
        "cost_usd": 0.03,
        "files_changed": ["core/api.py"],
        "result": "Task completed successfully",
    })
    assert isinstance(summary, str)
    assert len(summary) > 10
    assert "jerga" not in summary.lower()
    assert "$0.03" in summary or "0.0300" in summary


def test_reporter_summarize_timeout():
    from core.reporter import Reporter
    r = Reporter()
    summary = r.summarize_session({"stop_reason": "TIMEOUT (600s)", "iterations": 80, "cost_usd": 1.5})
    assert "tiempo" in summary.lower() or "agoto" in summary.lower()


def test_reporter_diagnostics_coste():
    from core.reporter import Reporter
    r = Reporter()
    summary = r.summarize_diagnostics({
        "category": "coste",
        "gastado": 1.5,
        "limite": 200,
        "modelo_mas_caro": "DeepSeek V3.2",
        "pct_modelo": 60,
    })
    assert "$1.50" in summary
    assert "DeepSeek" in summary


def test_reporter_answer_question():
    from core.reporter import Reporter
    r = Reporter()
    answer = r.answer_question("cuánto he gastado?", {
        "gastado": 3.50,
        "limite": 200,
        "modelo_top": "DeepSeek",
        "pct_modelo": 75,
    })
    assert "$3.50" in answer
    assert "DeepSeek" in answer


# ============================================================
# Safety
# ============================================================

def test_safety_protected_table():
    from core.safety import validate_mutation
    warning = validate_mutation("DELETE FROM inteligencias WHERE id = 1")
    assert warning is not None
    assert "critica" in warning.lower() or "inteligencias" in warning


def test_safety_protected_update():
    from core.safety import validate_mutation
    warning = validate_mutation("UPDATE config_modelos SET activo = false")
    assert warning is not None
    assert "config_modelos" in warning


def test_safety_normal_table():
    from core.safety import validate_mutation
    warning = validate_mutation("INSERT INTO metricas (componente, evento, datos) VALUES ('test', 'test', '{}')")
    assert warning is None, f"Normal table should be OK, got: {warning}"


def test_safety_select_ok():
    from core.safety import validate_mutation
    warning = validate_mutation("SELECT * FROM inteligencias")
    assert warning is None, "SELECT should never trigger safety"


def test_safety_cost_validation():
    from core.safety import validate_cost
    # Low cost, plenty of budget
    assert validate_cost(0.01, 10.0) is None
    # High cost relative to budget
    warning = validate_cost(5.0, 10.0)
    assert warning is not None
    assert "50%" in warning or "presupuesto" in warning.lower()


# ============================================================
# Proactive health check
# ============================================================

def test_health_check_returns_list():
    from core.proactive import health_check
    result = health_check()
    assert isinstance(result, list)
    # Each item should have the right structure
    for item in result:
        assert "nivel" in item
        assert "mensaje" in item
        assert "accion_sugerida" in item
        assert item["nivel"] in ("info", "warning", "alert")
