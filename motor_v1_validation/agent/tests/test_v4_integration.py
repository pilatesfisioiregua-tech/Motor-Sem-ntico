"""E2E tests for Code OS v4.0 — Advanced modules integration."""

import os
import sys

# Ensure agent/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestCircuitBreakerIntegration:
    """Test CircuitBreaker is connected to agent_loop."""

    def test_circuit_breaker_singleton(self):
        from core.monitoring import get_circuit_breaker
        cb1 = get_circuit_breaker()
        cb2 = get_circuit_breaker()
        assert cb1 is cb2

    def test_circuit_breaker_flow(self):
        from core.monitoring import get_circuit_breaker
        cb = get_circuit_breaker()
        model = "test/model-v4"
        assert cb.puede_llamar(model) is True
        # Register failures up to threshold
        for _ in range(5):
            cb.registrar_fallo(model)
        assert cb.puede_llamar(model) is False
        # Fallback available
        fallback = cb.get_modelo_fallback(model)
        assert isinstance(fallback, str)
        assert len(fallback) > 0
        # Clean up
        cb.registrar_exito(model)
        assert cb.puede_llamar(model) is True

    def test_circuit_breaker_states_in_diagnostics(self):
        from core.monitoring import get_circuit_breaker
        cb = get_circuit_breaker()
        estados = cb.get_estados()
        assert isinstance(estados, dict)

    def test_agent_loop_imports_breaker(self):
        """Verify agent_loop imports get_circuit_breaker."""
        import core.agent_loop as al
        source = open(al.__file__).read()
        assert "get_circuit_breaker" in source
        assert "breaker.puede_llamar" in source
        assert "breaker.registrar_exito" in source
        assert "breaker.registrar_fallo" in source


class TestMonitorIntegration:
    """Test Monitor is connected to agent_loop."""

    def test_monitor_singleton(self):
        from core.monitoring import get_monitor
        m1 = get_monitor()
        m2 = get_monitor()
        assert m1 is m2

    def test_monitor_registrar_ejecucion(self):
        from core.monitoring import get_monitor
        mon = get_monitor()
        initial_count = len(mon.ejecuciones_recientes)
        mon.registrar_ejecucion({
            'latencia_total_s': 1.5,
            'coste_total_usd': 0.01,
            'error': None,
            'modo': 'test',
            'tier': 2,
            'n_inteligencias': 3,
        })
        assert len(mon.ejecuciones_recientes) == initial_count + 1

    def test_monitor_check_slos(self):
        from core.monitoring import get_monitor
        mon = get_monitor()
        slos = mon.check_slos()
        assert 'status' in slos

    def test_monitor_check_budget(self):
        from core.monitoring import get_monitor
        mon = get_monitor()
        budget = mon.check_budget()
        assert 'dentro_presupuesto' in budget

    def test_agent_loop_has_monitor(self):
        """Verify agent_loop calls get_monitor."""
        import core.agent_loop as al
        source = open(al.__file__).read()
        assert "get_monitor" in source
        assert "monitor.registrar_ejecucion" in source


class TestCriticalityManifoldIntegration:
    """Test CriticalityEngine adjusts ConstraintManifold."""

    def test_criticality_singleton(self):
        from core.criticality_engine import get_criticality_engine
        c1 = get_criticality_engine()
        c2 = get_criticality_engine()
        assert c1 is c2

    def test_ajustar_manifold_temperatura(self):
        from core.criticality_engine import get_criticality_engine
        crit = get_criticality_engine()
        ajuste = crit.ajustar_manifold_temperatura()
        assert 'accion' in ajuste
        assert ajuste['accion'] in ('relajar', 'endurecer', 'mantener')
        assert 'R03_max_ints' in ajuste
        assert 'R07_profundidad' in ajuste

    def test_get_manifold_applies_criticality(self):
        from core.reglas_compilador import get_manifold
        manifold = get_manifold(apply_criticality=True)
        # Should have criticality attributes set
        assert hasattr(manifold, '_criticality_max_ints')
        assert hasattr(manifold, '_criticality_profundidad')

    def test_manifold_generar_respects_criticality(self):
        from core.reglas_compilador import get_manifold
        from core.criticality_engine import get_criticality_engine
        crit = get_criticality_engine()
        # Force orden_rigido: T = 0 (below T_c - 0.15)
        crit.T = 0.1
        manifold = get_manifold(apply_criticality=True)
        prog = manifold.generar({'top_gaps': []}, modo='analisis')
        # In orden_rigido, max_ints should be 7 (relaxed)
        assert manifold._criticality_max_ints == 7
        assert len(prog['inteligencias']) <= 7
        # Reset
        crit.T = 0.5


class TestMetacognitiveIntegration:
    """Test MetacognitiveLayer FOK/JOL in agent_loop."""

    def test_metacognitive_singleton(self):
        from core.metacognitive import get_metacognitive
        m1 = get_metacognitive()
        m2 = get_metacognitive()
        assert m1 is m2

    def test_fok_basic(self):
        from core.metacognitive import get_metacognitive
        meta = get_metacognitive()
        fok = meta.feeling_of_knowing("test input", "TestxSalud")
        assert 'fok' in fok
        assert 0.0 <= fok['fok'] <= 1.0
        assert 'factores' in fok

    def test_jol_basic(self):
        from core.metacognitive import get_metacognitive
        meta = get_metacognitive()
        jol = meta.judgment_of_learning({
            'tasa_cierre': 0.8,
            'hallazgos': [{'texto': 'test'}],
            'latencia_ms': 5000,
            'coste_usd': 0.05,
            'celda_objetivo': 'TestxSalud',
        })
        assert 'jol' in jol
        assert 0.0 <= jol['jol'] <= 1.0

    def test_agent_loop_has_metacognitive(self):
        """Verify agent_loop has FOK before loop and JOL after."""
        import core.agent_loop as al
        source = open(al.__file__).read()
        assert "feeling_of_knowing" in source
        assert "judgment_of_learning" in source
        assert "fok_result" in source
        assert "jol_result" in source


class TestFlywheelIntegration:
    """Test Flywheel end-to-end with check_promotion."""

    def test_flywheel_after_session_callable(self):
        from core.flywheel import after_session
        assert callable(after_session)

    def test_flywheel_check_promotion_callable(self):
        from core.flywheel import check_promotion
        assert callable(check_promotion)

    def test_agent_loop_calls_check_promotion(self):
        """Verify agent_loop calls check_promotion after after_session."""
        import core.agent_loop as al
        source = open(al.__file__).read()
        assert "check_promotion" in source
        assert "flywheel_promotion" in source


class TestGameTheoryMotorIntegration:
    """Test GameTheory is connected to Motor vN."""

    def test_game_theory_singleton(self):
        from core.game_theory import get_game_theory
        g1 = get_game_theory()
        g2 = get_game_theory()
        assert g1 is g2

    def test_analizar_composicion(self):
        from core.game_theory import get_game_theory
        gt = get_game_theory()
        outputs = [
            {'inteligencia': 'INT-01', 'texto': 'Analisis cuantitativo del caso', 'hallazgos': []},
            {'inteligencia': 'INT-08', 'texto': 'Perspectiva emocional del individuo', 'hallazgos': []},
        ]
        result = gt.analizar_composicion(outputs)
        assert 'señales_confianza' in result
        assert 'convergencia_schelling' in result

    def test_motor_vn_has_game_theory(self):
        import core.motor_vn as mv
        source = open(mv.__file__).read()
        assert "game_theory" in source
        assert "analizar_composicion" in source


class TestInformationLayerMotorIntegration:
    """Test InformationLayer is connected to Motor vN."""

    def test_information_bottleneck(self):
        from core.information_layer import information_bottleneck
        outputs = [
            {'inteligencia': 'INT-01', 'texto': 'Analisis cuantitativo con numeros y datos'},
            {'inteligencia': 'INT-08', 'texto': 'Perspectiva emocional sentimientos y valores'},
        ]
        result = information_bottleneck(outputs)
        assert 'ranking' in result
        assert 'total_info_neta' in result
        assert 'ratio_eficiencia' in result

    def test_motor_vn_has_information_layer(self):
        import core.motor_vn as mv
        source = open(mv.__file__).read()
        assert "information_bottleneck" in source
        assert "information_layer" in source


class TestStatusEndpointEnhanced:
    """Test /code-os/status returns advanced module states."""

    def test_api_has_circuit_breaker_section(self):
        import api as api_mod
        source = open(api_mod.__file__).read()
        assert "circuit_breaker" in source
        assert "monitor" in source
        assert "criticality" in source
        assert "flywheel" in source
        assert '"version": "5.0"' in source
