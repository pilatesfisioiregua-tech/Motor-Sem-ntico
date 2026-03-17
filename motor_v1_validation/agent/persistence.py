"""Code OS — Supabase Persistence Layer.
Registers everything: sessions, visions, briefings, iterations, files, results.
Uses Supabase REST API via subprocess+curl (same pattern as OpenRouter).
"""

import os
import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


def _load_env():
    """Load .env.staging from project root."""
    for env_path in [
        Path(__file__).parent.parent.parent.parent / ".env.staging",
        Path(__file__).parent.parent / ".env.staging",
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))
            break

_load_env()


@dataclass
class SupabaseClient:
    """Persists Code OS data to Supabase via REST API."""
    url: str = ""
    key: str = ""  # service_role key
    enabled: bool = True

    def __post_init__(self):
        if not self.url:
            self.url = os.environ.get("STAGING_URL", "").rstrip("/")
        if not self.key:
            self.key = os.environ.get("STAGING_SERVICE_KEY", "")
        if not self.url or not self.key:
            self.enabled = False

    def _request(self, method: str, path: str, data: dict = None,
                 params: str = "") -> Optional[dict]:
        """Make HTTP request to Supabase REST API via curl."""
        if not self.enabled:
            return None

        url = f"{self.url}/rest/v1/{path}"
        if params:
            url += f"?{params}"

        cmd = ['curl', '-s', '--max-time', '10', '-X', method, url,
               '-H', f'apikey: {self.key}',
               '-H', f'Authorization: Bearer {self.key}',
               '-H', 'Content-Type: application/json']

        if method == "POST":
            cmd.extend(['-H', 'Prefer: return=representation'])

        if data is not None:
            tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(data, tmp)
            tmp.close()
            cmd.extend(['-d', f'@{tmp.name}'])
        else:
            tmp = None

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                return None
            resp = json.loads(result.stdout) if result.stdout.strip() else None
            return resp
        except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception):
            return None
        finally:
            if tmp:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass

    # ================================================================
    # HIGH-LEVEL LOGGING METHODS
    # ================================================================

    def log_session_start(self, mode: str, input_raw: str,
                          project_name: str = "", project_dir: str = "",
                          model_primary: str = "", strategy: str = "solo") -> str:
        """Start a new session. Returns session_id (UUID)."""
        session_id = str(uuid.uuid4())
        self._request("POST", "code_os_sessions", {
            "id": session_id,
            "mode": mode,
            "input_raw": input_raw[:5000],
            "project_dir": project_dir,
            "project_name": project_name or os.path.basename(project_dir),
            "model_primary": model_primary,
            "strategy": strategy,
            "status": "running",
        })
        return session_id

    def log_session_end(self, session_id: str, status: str = "completed"):
        """Mark session as finished."""
        self._request("PATCH", f"code_os_sessions",
                       {"status": status, "finished_at": "now()"},
                       params=f"id=eq.{session_id}")

    def log_vision(self, session_id: str, vision_raw: str,
                   spec_generated: dict = None, questions: list = None,
                   clarifications: list = None):
        """Log a vision translation."""
        self._request("POST", "code_os_visions", {
            "session_id": session_id,
            "vision_raw": vision_raw[:5000],
            "spec_generated": spec_generated,
            "questions_asked": questions,
            "clarifications": clarifications,
        })

    def log_briefing(self, session_id: str, title: str, content_md: str,
                     approved: bool = False, feedback: str = None, version: int = 1):
        """Log a generated briefing."""
        self._request("POST", "code_os_briefings", {
            "session_id": session_id,
            "title": title,
            "content_md": content_md[:50000],
            "approved": approved,
            "user_feedback": feedback,
            "version": version,
        })

    def log_iteration(self, session_id: str, iter_n: int, model_used: str,
                      tool_called: str = None, tool_args: dict = None,
                      tool_result: str = None, is_error: bool = False,
                      tokens_in: int = 0, tokens_out: int = 0,
                      cost_usd: float = 0, duration_ms: int = 0):
        """Log a single iteration of the agent loop."""
        self._request("POST", "code_os_iterations", {
            "session_id": session_id,
            "iteration_n": iter_n,
            "model_used": model_used,
            "tool_called": tool_called,
            "tool_args": tool_args,
            "tool_result": (tool_result[:5000] if tool_result else None),
            "is_error": is_error,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms,
        })

    def log_file_change(self, session_id: str, file_path: str, action: str,
                        content_before: str = None, content_after: str = None,
                        iter_n: int = 0):
        """Log a file creation/edit/delete."""
        self._request("POST", "code_os_files", {
            "session_id": session_id,
            "file_path": file_path,
            "action": action,
            "content_before": (content_before[:10000] if content_before else None),
            "content_after": (content_after[:10000] if content_after else None),
            "iteration_n": iter_n,
        })

    def log_result(self, session_id: str, pass_rate: float = 0,
                   tests_passed: int = 0, tests_total: int = 0,
                   total_cost_usd: float = 0, total_time_s: float = 0,
                   total_tokens: int = 0, total_iterations: int = 0,
                   stop_reason: str = "", files_changed: list = None,
                   error_summary: str = None):
        """Log final result of a session."""
        self._request("POST", "code_os_results", {
            "session_id": session_id,
            "pass_rate": pass_rate,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "total_cost_usd": total_cost_usd,
            "total_time_s": total_time_s,
            "total_tokens": total_tokens,
            "total_iterations": total_iterations,
            "stop_reason": stop_reason,
            "files_changed": files_changed,
            "error_summary": error_summary[:2000] if error_summary else None,
        })

    # ================================================================
    # CONTEXT QUERIES
    # ================================================================

    def get_project_history(self, project_name: str, limit: int = 5) -> list:
        """Get recent sessions for a project."""
        result = self._request("GET", "code_os_sessions",
            params=f"project_name=eq.{project_name}&order=created_at.desc&limit={limit}&select=id,mode,input_raw,status,model_primary,created_at")
        return result if isinstance(result, list) else []

    def get_past_briefings(self, project_name: str) -> list:
        """Get briefings generated for a project."""
        # Join through sessions
        sessions = self.get_project_history(project_name, limit=20)
        if not sessions:
            return []
        session_ids = ",".join(f'"{s["id"]}"' for s in sessions)
        result = self._request("GET", "code_os_briefings",
            params=f"session_id=in.({session_ids})&order=created_at.desc&limit=10&select=title,content_md,approved,version,created_at")
        return result if isinstance(result, list) else []

    def get_common_errors(self, project_name: str) -> list:
        """Get common errors from past sessions."""
        sessions = self.get_project_history(project_name, limit=10)
        if not sessions:
            return []
        session_ids = ",".join(f'"{s["id"]}"' for s in sessions)
        result = self._request("GET", "code_os_iterations",
            params=f"session_id=in.({session_ids})&is_error=eq.true&order=created_at.desc&limit=20&select=tool_called,tool_result")
        return result if isinstance(result, list) else []

    def get_best_models(self, project_name: str) -> dict:
        """Get model performance stats for a project."""
        results = self._request("GET", "code_os_results",
            params=f"order=created_at.desc&limit=50&select=session_id,pass_rate,total_cost_usd,stop_reason")
        if not results or not isinstance(results, list):
            return {}

        # Cross-reference with sessions to get model info
        sessions = self.get_project_history(project_name, limit=50)
        session_models = {s["id"]: s.get("model_primary", "unknown") for s in sessions}

        model_stats = {}
        for r in results:
            model = session_models.get(r.get("session_id"), "unknown")
            if model not in model_stats:
                model_stats[model] = {"runs": 0, "total_pass": 0, "total_cost": 0}
            model_stats[model]["runs"] += 1
            model_stats[model]["total_pass"] += r.get("pass_rate", 0)
            model_stats[model]["total_cost"] += r.get("total_cost_usd", 0)

        for model, stats in model_stats.items():
            if stats["runs"] > 0:
                stats["avg_pass_rate"] = stats["total_pass"] / stats["runs"]
                stats["avg_cost"] = stats["total_cost"] / stats["runs"]

        return model_stats

    # ================================================================
    # SESSION STATE (v2 — resume + learning)
    # ================================================================

    def save_session_state(self, session_id: str, state: dict) -> None:
        """Save session state for resume capability."""
        self._request("PATCH", "code_os_sessions",
                       {"session_state": state},
                       params=f"id=eq.{session_id}")

    def get_session_state(self, session_id: str) -> Optional[dict]:
        """Get saved session state for resume."""
        result = self._request("GET", "code_os_sessions",
            params=f"id=eq.{session_id}&select=session_state,mode,input_raw,project_name,strategy")
        if isinstance(result, list) and result:
            return result[0]
        return None

    # ================================================================
    # CROSS-SESSION LEARNING (v2)
    # ================================================================

    def log_knowledge(self, project_name: str, goal_text: str,
                      approach_summary: str = "", model_used: str = "",
                      pass_rate: float = 0, cost_usd: float = 0,
                      session_id: str = None) -> None:
        """Record a successful approach for future learning."""
        self._request("POST", "code_os_knowledge", {
            "project_name": project_name,
            "goal_text": goal_text[:2000],
            "approach_summary": approach_summary[:5000],
            "model_used": model_used,
            "pass_rate": pass_rate,
            "cost_usd": cost_usd,
            "session_id": session_id,
        })

    def get_similar_solutions(self, project_name: str, goal_text: str,
                              limit: int = 3) -> list:
        """Find similar past solutions for learning hints."""
        # Simple keyword matching (not semantic — would need embeddings)
        result = self._request("GET", "code_os_knowledge",
            params=f"project_name=eq.{project_name}&pass_rate=gte.0.8"
                   f"&order=pass_rate.desc,created_at.desc&limit={limit}"
                   f"&select=goal_text,approach_summary,model_used,pass_rate,cost_usd")
        return result if isinstance(result, list) else []

    def save_custom_tool(self, name: str, description: str, code: str,
                         parameters_schema: dict, test_code: str = "",
                         project_name: str = "", session_id: str = None) -> None:
        """Save a custom tool to Supabase for cross-project sharing."""
        self._request("POST", "code_os_custom_tools", {
            "name": name,
            "description": description,
            "code": code,
            "parameters_schema": parameters_schema,
            "test_code": test_code,
            "project_name": project_name,
            "created_by_session": session_id,
        })

    def get_custom_tools(self, project_name: str = "") -> list:
        """Get custom tools, optionally filtered by project."""
        params = "order=use_count.desc&limit=50&select=name,description,code,parameters_schema"
        if project_name:
            params = f"project_name=eq.{project_name}&" + params
        result = self._request("GET", "code_os_custom_tools", params=params)
        return result if isinstance(result, list) else []
