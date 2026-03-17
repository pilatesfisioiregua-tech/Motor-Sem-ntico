"""Unit tests for Code OS v5.0 — Chief + Verifier + Self-Healing."""

import os
import sys

# Ensure agent/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# =========================================================
# Chief unit tests (Steps 1-4)
# =========================================================

class TestChiefAnalyzeDomain:
    """Test Chief.analyze_domain returns structured analysis."""

    def test_analyze_returns_top_celdas(self):
        from core.chief import Chief
        chief = Chief()
        result = chief.analyze_domain("estudio de pilates")
        assert 'top_celdas' in result
        assert 'programa_sugerido' in result
        assert 'domain' in result

    def test_analyze_returns_ints(self):
        from core.chief import Chief
        chief = Chief()
        result = chief.analyze_domain("restaurante")
        prog = result.get('programa_sugerido', {})
        assert 'inteligencias' in prog

    def test_get_ints_for_cell(self):
        from core.chief import Chief
        chief = Chief()
        ints = chief._get_ints_for_cell('ConservarxSalud')
        assert isinstance(ints, list)
        assert len(ints) > 0


class TestChiefDesignExocortex:
    """Test Chief.design_exocortex returns full design."""

    def test_design_has_required_keys(self):
        from core.chief import Chief
        chief = Chief()
        design = chief.design_exocortex("estudio de pilates", focus="retencion")
        assert 'consumidor_id' in design
        assert 'celdas_target' in design
        assert 'inteligencias' in design
        assert 'datos_necesarios' in design

    def test_design_consumidor_format(self):
        from core.chief import Chief
        chief = Chief()
        design = chief.design_exocortex("test domain")
        assert design['consumidor_id'].startswith('exocortex_')


class TestChiefGenerateBriefing:
    """Test Chief.generate_briefing produces valid briefing format."""

    def test_briefing_has_header(self):
        from core.chief import Chief
        chief = Chief()
        design = chief.design_exocortex("test domain")
        briefing = chief.generate_briefing(design)
        assert '# BRIEFING:' in briefing

    def test_briefing_has_steps(self):
        from core.chief import Chief
        chief = Chief()
        design = chief.design_exocortex("test domain")
        briefing = chief.generate_briefing(design)
        assert '### PASO 1:' in briefing
        assert '### PASO 6:' in briefing
        assert 'ARCHIVOS:' in briefing
        assert 'INSTRUCCION:' in briefing
        assert 'CRITERIO:' in briefing


# =========================================================
# Verifier unit tests (Steps 5-7, 9)
# =========================================================

class TestVerifierInit:
    """Test Verifier initialization."""

    def test_valid_tiers(self):
        from core.verifier import Verifier
        for tier in ('fast', 'standard', 'deep'):
            v = Verifier(tier)
            assert v.tier == tier

    def test_invalid_tier_raises(self):
        from core.verifier import Verifier
        try:
            Verifier("invalid")
            assert False, "Should have raised"
        except AssertionError:
            pass


class TestVerifierFormatCheck:
    """Test Verifier._check_briefing_format."""

    def test_valid_format_no_issues(self):
        from core.verifier import Verifier
        v = Verifier("fast")
        briefing = """# BRIEFING: Test
## REPO: .
### PASO 1: Test step
ARCHIVOS: test.py
INSTRUCCION:
Do something
CRITERIO: python3 -c "print('OK')"
"""
        issues = v._check_briefing_format(briefing)
        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_missing_header(self):
        from core.verifier import Verifier
        v = Verifier("fast")
        briefing = """## REPO: .
### PASO 1: Test step
ARCHIVOS: test.py
INSTRUCCION:
Do something
CRITERIO: echo OK
"""
        issues = v._check_briefing_format(briefing)
        assert any('header' in str(i).lower() for i in issues)

    def test_missing_criterio(self):
        from core.verifier import Verifier
        v = Verifier("fast")
        briefing = """# BRIEFING: Test
### PASO 1: Missing criterion
ARCHIVOS: test.py
INSTRUCCION:
Do something
"""
        issues = v._check_briefing_format(briefing)
        assert any('CRITERIO' in str(i) for i in issues)


class TestVerifierCodeChange:
    """Test Verifier.verify_code_change."""

    def test_valid_python(self):
        from core.verifier import Verifier
        v = Verifier("fast")
        result = v.verify_code_change(
            "test.py",
            "x = 1",
            "x = 2\ny = 3\n",
        )
        assert result['syntax_ok'] is True
        assert result['passed'] is True

    def test_invalid_python(self):
        from core.verifier import Verifier
        v = Verifier("fast")
        result = v.verify_code_change(
            "test.py",
            "x = 1",
            "def f(\n  broken syntax",
        )
        assert result['syntax_ok'] is False
        assert result['passed'] is False


class TestVerifierDesignDegradation:
    """Test verify_design degrades from deep to standard without conversation."""

    def test_deep_without_conversation_degrades(self):
        from core.verifier import Verifier
        v = Verifier("deep")
        briefing = """# BRIEFING: Test
### PASO 1: Step
ARCHIVOS: test.py
INSTRUCCION:
Do it
CRITERIO: echo OK
"""
        result = v.verify_design(briefing, {}, conversation=None)
        assert result['reviewer'] == 'standard'

    def test_fast_no_degradation(self):
        from core.verifier import Verifier
        v = Verifier("fast")
        briefing = """# BRIEFING: Test
### PASO 1: Step
ARCHIVOS: test.py
INSTRUCCION:
Do it
CRITERIO: echo OK
"""
        result = v.verify_design(briefing, {})
        assert result['reviewer'] == 'fast'


# =========================================================
# Self-Healing unit tests (Steps 16-18)
# =========================================================

class TestSelfHealingClassify:
    """Test SelfHealingLoop.classify_improvement."""

    def test_single_file_low_risk_fontaneria(self):
        from core.self_healing import SelfHealingLoop
        sh = SelfHealingLoop()
        result = sh.classify_improvement({
            'files': ['core/budget.py'],
            'lines_changed': 5,
            'risk_level': 'low',
        })
        assert result == 'FONTANERIA'

    def test_protected_component_arquitectural(self):
        from core.self_healing import SelfHealingLoop
        sh = SelfHealingLoop()
        result = sh.classify_improvement({
            'files': ['core/motor_vn.py'],
            'lines_changed': 3,
            'risk_level': 'low',
        })
        assert result == 'ARQUITECTURAL'

    def test_multiple_files_arquitectural(self):
        from core.self_healing import SelfHealingLoop
        sh = SelfHealingLoop()
        result = sh.classify_improvement({
            'files': ['a.py', 'b.py'],
            'lines_changed': 5,
            'risk_level': 'low',
        })
        assert result == 'ARQUITECTURAL'

    def test_too_many_lines_arquitectural(self):
        from core.self_healing import SelfHealingLoop
        sh = SelfHealingLoop()
        result = sh.classify_improvement({
            'files': ['core/budget.py'],
            'lines_changed': 50,
            'risk_level': 'low',
        })
        assert result == 'ARQUITECTURAL'

    def test_high_risk_arquitectural(self):
        from core.self_healing import SelfHealingLoop
        sh = SelfHealingLoop()
        result = sh.classify_improvement({
            'files': ['core/budget.py'],
            'lines_changed': 5,
            'risk_level': 'high',
        })
        assert result == 'ARQUITECTURAL'


class TestSelfHealingSingleton:
    """Test get_self_healing singleton."""

    def test_singleton(self):
        from core.self_healing import get_self_healing
        sh1 = get_self_healing()
        sh2 = get_self_healing()
        assert sh1 is sh2
