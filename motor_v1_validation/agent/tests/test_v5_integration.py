"""Integration tests for Code OS v5.0 — Chief + Verifier + Self-Healing."""

import os
import sys

# Ensure agent/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestChiefVerifierIntegration:
    """Test Chief generates briefings that pass Verifier format checks."""

    def test_generated_briefing_passes_format_check(self):
        from core.chief import Chief
        from core.verifier import Verifier
        chief = Chief()
        v = Verifier("fast")

        design = chief.design_exocortex("estudio de pilates")
        briefing = chief.generate_briefing(design)
        issues = v._check_briefing_format(briefing)
        assert len(issues) == 0, f"Format issues: {issues}"

    def test_verify_design_fast_approves_valid(self):
        from core.chief import Chief
        from core.verifier import Verifier
        chief = Chief()
        v = Verifier("fast")

        design = chief.design_exocortex("restaurante")
        briefing = chief.generate_briefing(design)
        result = v.verify_design(briefing, design)
        assert result['approved'] is True
        assert result['reviewer'] == 'fast'


class TestChiefConversationFlow:
    """Test ChiefConversation state machine."""

    def test_initial_state(self):
        from core.chief import Chief, ChiefConversation
        chief = Chief()
        conv = ChiefConversation(chief)
        assert conv.state == 'initial'

    def test_process_message_returns_response(self):
        from core.chief import Chief, ChiefConversation
        chief = Chief()
        conv = ChiefConversation(chief)
        result = conv.process_message("estudio de pilates")
        assert 'response' in result
        assert 'state' in result

    def test_conversation_has_id(self):
        from core.chief import Chief, ChiefConversation
        chief = Chief()
        conv = ChiefConversation(chief)
        assert conv.conversation_id is not None
        assert len(conv.conversation_id) > 0


class TestVerifierStepIntegration:
    """Test Verifier.verify_step with mock step objects."""

    def test_verify_step_no_criterion(self):
        from core.verifier import Verifier
        from dataclasses import dataclass

        @dataclass
        class MockStep:
            number: int = 1
            description: str = "Test step"
            files: list = None
            success_criteria: str = ""
            repo_dir: str = "."

            def __post_init__(self):
                if self.files is None:
                    self.files = []

        v = Verifier("fast")
        step = MockStep()
        result = v.verify_step(step, {'stop_reason': 'DONE'})
        assert result['passed'] is True
        assert len(result['layers']) >= 2


class TestSelfHealingIntegration:
    """Test SelfHealingLoop classify + alert conversion."""

    def test_alert_to_improvement(self):
        from core.self_healing import SelfHealingLoop
        sh = SelfHealingLoop()
        alert = {
            'nivel': 'warning',
            'tipo': 'presupuesto',
            'mensaje': 'Budget almost exceeded',
            'accion_sugerida': 'Reduce model tier',
        }
        imp = sh._alert_to_improvement(alert)
        assert imp is not None
        assert 'files' in imp
        assert 'risk_level' in imp

    def test_run_cycle_with_empty_alerts(self):
        from core.self_healing import SelfHealingLoop
        sh = SelfHealingLoop()
        result = sh.run_cycle(health_alerts=[])
        assert result['fixes_applied'] == []
        assert result['queued'] == []
        assert result['total_alerts'] == 0

    def test_run_cycle_fontaneria_fix(self):
        from core.self_healing import SelfHealingLoop
        sh = SelfHealingLoop()
        alerts = [{
            'nivel': 'warning',
            'tipo': 'presupuesto',
            'mensaje': 'Budget warning',
            'accion_sugerida': 'Adjust budget threshold',
        }]
        result = sh.run_cycle(health_alerts=alerts)
        assert result['total_alerts'] == 1
        # Should be fontaneria (budget.py, low risk)
        assert len(result['fixes_applied']) > 0 or len(result['errors']) > 0


class TestAgentLoopVerifierIntegration:
    """Test run_briefing has verify_tier parameter."""

    def test_run_briefing_has_verify_tier(self):
        import inspect
        from core.agent_loop import run_briefing
        sig = inspect.signature(run_briefing)
        assert 'verify_tier' in sig.parameters

    def test_run_briefing_default_fast(self):
        import inspect
        from core.agent_loop import run_briefing
        sig = inspect.signature(run_briefing)
        assert sig.parameters['verify_tier'].default == 'fast'


class TestHooksVerifierIntegration:
    """Test hooks include post_briefing_step hook."""

    def test_default_hooks_include_briefing_step(self):
        from hooks import create_default_hooks
        registry = create_default_hooks()
        all_hooks = registry.list_hooks()
        assert 'post_briefing_step' in all_hooks

    def test_post_briefing_step_hook_callable(self):
        from hooks import post_briefing_step_hook
        assert callable(post_briefing_step_hook)
