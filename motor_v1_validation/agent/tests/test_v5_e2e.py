"""E2E tests for Code OS v5.0 — full flow verification."""

import os
import sys

# Ensure agent/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestChiefE2EFlow:
    """E2E: Chief analyzes → designs → generates → verifies."""

    def test_full_design_flow(self):
        """Chief full flow without DB: analyze → design → briefing → verify."""
        from core.chief import Chief
        from core.verifier import Verifier

        chief = Chief()
        v = Verifier("fast")

        # Step 1: Analyze
        analysis = chief.analyze_domain("estudio de pilates premium")
        assert 'top_celdas' in analysis

        # Step 2: Design
        design = chief.design_exocortex("estudio de pilates premium", focus="retencion")
        assert 'consumidor_id' in design
        assert 'inteligencias' in design
        # INTs may be empty without DB/LLM, but key must exist
        assert isinstance(design['inteligencias'], list)

        # Step 3: Generate briefing
        briefing = chief.generate_briefing(design)
        assert '# BRIEFING:' in briefing
        assert '### PASO 1:' in briefing

        # Step 4: Verify design (fast tier)
        verification = v.verify_design(briefing, design)
        assert verification['approved'] is True
        assert verification['reviewer'] == 'fast'

    def test_conversation_flow_e2e(self):
        """ChiefConversation processes domain message."""
        from core.chief import Chief, ChiefConversation

        chief = Chief()
        conv = ChiefConversation(chief)

        # User sends domain
        result = conv.process_message("cadena de restaurantes")
        assert 'response' in result
        assert len(result['response']) > 0


class TestVerifierE2EMultiTier:
    """E2E: Verifier works across all tiers for deterministic checks."""

    def test_fast_tier_full_check(self):
        from core.verifier import Verifier
        v = Verifier("fast")
        briefing = """# BRIEFING: Test E2E
## REPO: .
### PASO 1: Create file
ARCHIVOS: test.py
INSTRUCCION:
Create a Python file
CRITERIO: python3 -c "print('OK')"

### PASO 2: Verify
ARCHIVOS: test.py
INSTRUCCION:
Run tests
CRITERIO: echo OK
"""
        result = v.verify_design(briefing, {})
        assert result['approved'] is True
        assert result['confidence'] == 1.0

    def test_invalid_briefing_rejected(self):
        from core.verifier import Verifier
        v = Verifier("fast")
        briefing = "This is not a valid briefing"
        result = v.verify_design(briefing, {})
        assert result['approved'] is False
        assert len(result['form_issues']) > 0


class TestSelfHealingE2E:
    """E2E: Self-healing classifies and processes mixed alerts."""

    def test_mixed_alerts_classification(self):
        from core.self_healing import SelfHealingLoop

        sh = SelfHealingLoop()
        alerts = [
            {
                'nivel': 'warning',
                'tipo': 'presupuesto',
                'mensaje': 'Budget warning: 85% used',
                'accion_sugerida': 'Reduce model tier temporarily',
            },
            {
                'nivel': 'alert',
                'tipo': 'modelo',
                'mensaje': 'Model quality below threshold',
                'accion_sugerida': 'Switch to different model',
            },
        ]
        result = sh.run_cycle(health_alerts=alerts)
        assert result['total_alerts'] == 2
        # First alert (budget) should be fontaneria
        # Second alert (model = protected) should be queued (or error without DB)
        total_processed = (len(result['fixes_applied']) +
                          len(result['queued']) +
                          len(result['errors']))
        assert total_processed == 2


class TestAPIEndpointsExist:
    """E2E: Verify API endpoints are registered."""

    def test_chief_endpoints_registered(self):
        import api as api_mod
        source = open(api_mod.__file__).read()
        assert '/chief/execute' in source
        assert '/chief/status/' in source
        assert '/chief/suggest/' in source
        assert '/chief/designs' in source

    def test_self_healing_endpoints_registered(self):
        import api as api_mod
        source = open(api_mod.__file__).read()
        assert '/self-healing/run' in source
        assert '/self-healing/queue' in source
        assert '/self-healing/approve/' in source
        assert '/self-healing/reject/' in source

    def test_version_5(self):
        import api as api_mod
        source = open(api_mod.__file__).read()
        assert '"version": "5.0"' in source


class TestCLIFlags:
    """E2E: Verify CLI flags exist."""

    def test_cli_has_verify_flag(self):
        source = open('cli.py').read()
        assert '--verify' in source
        assert 'verify_tier' in source

    def test_code_os_has_verify_flag(self):
        source = open('code_os.py').read()
        assert '--verify' in source
        assert 'verify_tier' in source
