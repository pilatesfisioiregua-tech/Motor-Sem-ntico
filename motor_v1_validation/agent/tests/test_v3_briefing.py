"""E2E tests for Code OS v3 briefing execution pipeline."""

import os
import sys
import tempfile
import pytest

# Ensure agent/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _write_briefing(content: str) -> str:
    """Write briefing content to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestBriefingParser:
    """Test briefing_parser.py parsing."""

    def test_parse_valid_briefing(self):
        from core.briefing_parser import parse_briefing

        path = _write_briefing("""# BRIEFING: Test Briefing
## REPO: /tmp/test
## CONTEXTO: Testing context

### PASO 1: First step
ARCHIVOS: a.py
INSTRUCCION:
Do something simple.
CRITERIO: echo OK

### PASO 2: Second step
ARCHIVOS: b.py, c.py
INSTRUCCION:
Do another thing.
CRITERIO: echo OK
""")
        try:
            b = parse_briefing(path)
            assert b.title == "Test Briefing"
            assert b.repo_dir == "/tmp/test"
            assert len(b.steps) == 2
            assert b.steps[0].number == 1
            assert b.steps[0].files == ["a.py"]
            assert b.steps[1].number == 2
            assert b.steps[1].files == ["b.py", "c.py"]
        finally:
            os.unlink(path)

    def test_parse_missing_header_raises(self):
        from core.briefing_parser import parse_briefing

        path = _write_briefing("no header here\n")
        try:
            with pytest.raises(ValueError, match="BRIEFING"):
                parse_briefing(path)
        finally:
            os.unlink(path)


class TestDriftGuard:
    """Test drift_guard.py."""

    def test_check_drift_off_topic(self):
        from core.drift_guard import check_drift
        reason = check_drift("Let's implement blockchain consensus", ".")
        assert reason is not None
        assert "blockchain" in reason

    def test_check_drift_with_anchor(self):
        from core.drift_guard import check_drift
        reason = check_drift("blockchain integration for motor semantico", ".")
        assert reason is None

    def test_check_drift_clean(self):
        from core.drift_guard import check_drift
        reason = check_drift("implement the gestor scheduler flywheel", ".")
        assert reason is None

    def test_check_file_drift(self):
        from core.drift_guard import check_file_drift
        reason = check_file_drift("/etc/passwd", "/home/user/project")
        assert reason is not None

    def test_check_file_drift_ok(self):
        from core.drift_guard import check_file_drift
        reason = check_file_drift("@project/core/new.py", "/home/user/project")
        assert reason is None

    def test_reset_drift_state(self):
        from core.drift_guard import reset_drift_state, _consecutive_drifts
        reset_drift_state()
        from core.drift_guard import _consecutive_drifts as after
        assert after == 0

    def test_register_drift_hooks(self):
        from core.drift_guard import register_drift_hooks
        from hooks import HookRegistry
        registry = HookRegistry()
        register_drift_hooks(registry)
        hooks = registry.list_hooks()
        assert "drift_post_tool" in hooks.get("post_tool", [])
        assert "drift_pre_iteration" in hooks.get("pre_iteration", [])


class TestRouter:
    """Test detect_mode with new modes."""

    def test_execute_mode_paso(self):
        from core.router import detect_mode
        assert detect_mode("PASO 1: crear archivo") == "execute"

    def test_execute_mode_instruccion(self):
        from core.router import detect_mode
        assert detect_mode("Task with instrucción: do something") == "execute"

    def test_execute_mode_keywords(self):
        from core.router import detect_mode
        assert detect_mode("crear nuevo componente") == "execute"
        assert detect_mode("añadir funcionalidad") == "execute"

    def test_analyze_mode(self):
        from core.router import detect_mode
        assert detect_mode("diagnosticar estado DB") == "analyze"
        assert detect_mode("listar todos los endpoints") == "analyze"
        assert detect_mode("mostrar estructura del proyecto") == "analyze"

    def test_mode_configs_exist(self):
        from core.router import MODE_CONFIGS
        assert "execute" in MODE_CONFIGS
        assert "analyze" in MODE_CONFIGS
        assert MODE_CONFIGS["execute"].max_iterations == 20
        assert MODE_CONFIGS["analyze"].max_iterations == 30


class TestProgressTracker:
    """Test ProgressTracker."""

    def test_basic_signal(self):
        from core.budget import ProgressTracker
        p = ProgressTracker("test goal")
        p.record_action("read_file", "content here", False)
        sig = p.get_signal()
        assert sig["tools_ok"] == 1
        assert sig["tools_error"] == 0

    def test_progressing_trend(self):
        from core.budget import ProgressTracker
        p = ProgressTracker("test")
        for i in range(3):
            p.record_action("write_file", f"ok{i}", False)
        assert p.get_signal()["trend"] == "progressing"

    def test_stuck_trend(self):
        from core.budget import ProgressTracker
        p = ProgressTracker("test")
        for _ in range(3):
            p.record_action("read_file", "error", True)
        assert p.get_signal()["trend"] == "stuck"

    def test_stagnant(self):
        from core.budget import ProgressTracker
        p = ProgressTracker("test")
        for _ in range(5):
            p.record_action("read_file", "same content", False)
        assert p.stagnant() is True

    def test_not_stagnant(self):
        from core.budget import ProgressTracker
        p = ProgressTracker("test")
        for i in range(5):
            p.record_action("read_file", f"different {i}", False)
        assert p.stagnant() is False


class TestHooks:
    """Test hook system."""

    def test_default_hooks_include_drift(self):
        from hooks import create_default_hooks
        h = create_default_hooks()
        hooks = h.list_hooks()
        assert "drift_post_tool" in hooks.get("post_tool", [])
        assert "drift_pre_iteration" in hooks.get("pre_iteration", [])

    def test_auto_test_in_hooks(self):
        from hooks import create_default_hooks
        h = create_default_hooks()
        hooks = h.list_hooks()
        assert "auto_test" in hooks.get("post_tool", [])


class TestRunBriefingImport:
    """Verify run_briefing is importable."""

    def test_import(self):
        from core.agent_loop import run_briefing
        assert callable(run_briefing)
