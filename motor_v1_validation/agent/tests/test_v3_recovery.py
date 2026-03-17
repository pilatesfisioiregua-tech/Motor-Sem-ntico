"""Test E2E Fase 2 — Error Recovery: RecoveryEngine, StuckDetector enhancements, hooks."""

import os
import sys

# Ensure agent/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================
# RecoveryEngine — decide()
# ============================================================

def test_recovery_decide_no_errors():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    result = r.decide([], "read_file", "some goal")
    assert result["action"] == "retry"
    assert result["reason"] == "no_errors"


def test_recovery_decide_unknown_tool():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    result = r.decide(["Unknown tool: foo_bar"], "foo_bar", "some goal")
    assert result["action"] == "skip"
    assert "foo_bar" in result["reason"]


def test_recovery_decide_api_retry():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    result = r.decide(["429 rate limit exceeded"], "call_llm", "some goal")
    assert result["action"] == "retry"


def test_recovery_decide_api_escalate():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    # Exhaust API retries
    for _ in range(4):
        result = r.decide(["503 service unavailable"], "call_llm", "some goal")
    assert result["action"] == "escalate"


def test_recovery_decide_syntax_retry_different():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    result = r.decide(["SyntaxError: unexpected indent"], "write_file", "fix code")
    assert result["action"] == "retry_different"
    assert result["hint"] is not None


def test_recovery_decide_syntax_rollback():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    # First syntax error → retry_different
    r.decide(["SyntaxError: unexpected indent"], "write_file", "fix code",
             last_write="/tmp/test.py")
    # Second syntax error → rollback
    result = r.decide(["SyntaxError: invalid syntax"], "write_file", "fix code",
                       last_write="/tmp/test.py")
    assert result["action"] == "rollback"


def test_recovery_decide_timeout_retry_then_skip():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    result = r.decide(["TimeoutError: timed out"], "run_command", "some goal")
    assert result["action"] == "retry"
    result = r.decide(["TimeoutError: timed out"], "run_command", "some goal")
    assert result["action"] == "skip"


def test_recovery_decide_io_skip():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    result = r.decide(["FileNotFoundError: /nonexistent"], "read_file", "read stuff")
    assert result["action"] == "skip"


def test_recovery_decide_test_failure():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    result = r.decide(["FAILED test_foo.py::test_bar"], "run_command", "run tests")
    assert result["action"] == "retry_different"
    assert "Test" in result["reason"] or "test" in result["reason"].lower()


# ============================================================
# RecoveryEngine — classify_error
# ============================================================

def test_classify_error_categories():
    from core.recovery import classify_error
    assert classify_error("SyntaxError: invalid syntax") == "syntax"
    assert classify_error("ModuleNotFoundError: No module named 'foo'") == "import"
    assert classify_error("TypeError: expected str, got int") == "type"
    assert classify_error("FileNotFoundError: /tmp/nope") == "io"
    assert classify_error("429 rate limit exceeded") == "api"
    assert classify_error("FAILED test_foo.py") == "test"
    assert classify_error("Unknown tool: bar") == "unknown_tool"
    assert classify_error("something completely different") == "unknown"


# ============================================================
# RecoveryEngine — should_decompose
# ============================================================

def test_should_decompose_diverse_errors():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    # 3+ different error types → decompose
    errors = [
        "SyntaxError: bad",
        "ModuleNotFoundError: no module",
        "TypeError: wrong type",
    ]
    assert r.should_decompose(errors, 5, 30) is True


def test_should_decompose_few_errors():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    assert r.should_decompose(["one error"], 2, 30) is False
    assert r.should_decompose([], 0, 30) is False


# ============================================================
# RecoveryEngine — decompose
# ============================================================

def test_decompose_multi_file():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    goal = "Modify @project/core/api.py and @project/core/router.py to add new endpoint"
    sub = r.decompose(goal)
    assert len(sub) >= 2
    assert any("api.py" in s for s in sub)
    assert any("router.py" in s for s in sub)


def test_decompose_default():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    goal = "Make the system faster"
    sub = r.decompose(goal)
    assert len(sub) == 3
    assert "investigate" in sub[0].lower()
    assert "implement" in sub[1].lower()
    assert "verify" in sub[2].lower()


# ============================================================
# RecoveryEngine — rollback
# ============================================================

def test_rollback_no_checkpoints():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    assert r.rollback() is None


def test_record_checkpoint():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    r.record_checkpoint("abc123")
    r.record_checkpoint("def456")
    assert len(r._git_checkpoints) == 2


def test_record_write():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    r.record_write("write_file", "/tmp/test.py")
    assert len(r.last_writes) == 1
    assert r.last_writes[0] == ("write_file", "/tmp/test.py")


def test_reset():
    from core.recovery import RecoveryEngine
    r = RecoveryEngine()
    r.record_write("write_file", "/tmp/a.py")
    r.decide(["SyntaxError"], "write_file", "goal")
    r.record_checkpoint("abc")
    r.reset()
    assert len(r.error_counts) == 0
    assert len(r.last_errors) == 0
    assert len(r.last_writes) == 0


# ============================================================
# StuckDetector — detect_loop
# ============================================================

def test_stuck_detect_loop_cycle2():
    from core.budget import StuckDetector
    s = StuckDetector()
    # Create A→B→A→B→A→B pattern (cycle of 2, repeated 3x)
    for _ in range(3):
        s.record_action("tool_a", {"x": 1}, "ok", False)
        s.record_action("tool_b", {"y": 2}, "ok", False)
    result = s.detect_loop()
    assert result is not None
    assert "Loop" in result


def test_stuck_detect_loop_no_cycle():
    from core.budget import StuckDetector
    s = StuckDetector()
    # Random actions, no cycle
    s.record_action("tool_a", {"x": 1}, "ok", False)
    s.record_action("tool_b", {"y": 2}, "ok", False)
    s.record_action("tool_c", {"z": 3}, "ok", False)
    s.record_action("tool_d", {"w": 4}, "ok", False)
    assert s.detect_loop() is None


def test_stuck_detect_loop_too_short():
    from core.budget import StuckDetector
    s = StuckDetector()
    s.record_action("tool_a", {"x": 1}, "ok", False)
    s.record_action("tool_b", {"y": 2}, "ok", False)
    assert s.detect_loop() is None


# ============================================================
# StuckDetector — detect_regression
# ============================================================

def test_stuck_detect_regression():
    from core.budget import StuckDetector
    s = StuckDetector()
    # Same tool: 2 successes then 3 errors
    s.record_action("write_file", {"p": "a"}, "ok", False)
    s.record_action("write_file", {"p": "a"}, "ok", False)
    s.record_action("write_file", {"p": "a"}, "SyntaxError", True)
    s.record_action("write_file", {"p": "a"}, "SyntaxError", True)
    s.record_action("write_file", {"p": "a"}, "SyntaxError", True)
    result = s.detect_regression()
    assert result is not None
    assert "Regression" in result


def test_stuck_detect_regression_none():
    from core.budget import StuckDetector
    s = StuckDetector()
    # All successes — no regression
    for _ in range(5):
        s.record_action("read_file", {"p": "a"}, "ok", False)
    assert s.detect_regression() is None


# ============================================================
# StuckDetector — check() integration
# ============================================================

def test_stuck_check_includes_loop():
    from core.budget import StuckDetector
    s = StuckDetector()
    # Create loop that triggers via check()
    for _ in range(3):
        s.record_action("tool_a", {"x": 1}, "ok", False)
        s.record_action("tool_b", {"y": 2}, "ok", False)
    result = s.check()
    assert result is not None
    assert "Loop" in result


# ============================================================
# Hooks — git_checkpoint_hook
# ============================================================

def test_git_checkpoint_hook_skips_non_writes():
    from hooks import git_checkpoint_hook
    ctx = {"tool": "read_file", "is_error": False}
    git_checkpoint_hook(ctx)
    assert "_checkpoint_hash" not in ctx


def test_git_checkpoint_hook_skips_errors():
    from hooks import git_checkpoint_hook
    ctx = {"tool": "write_file", "is_error": True, "args": {"path": "/tmp/a.py"}}
    git_checkpoint_hook(ctx)
    assert "_checkpoint_hash" not in ctx
