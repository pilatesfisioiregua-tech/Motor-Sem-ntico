"""Model Observatory — DB-driven model registry with auto-discovery and A/B testing."""

import os
import json
import time
import subprocess
import tempfile
from typing import Optional
from datetime import datetime, timezone


# Hardcoded fallback (used if DB unavailable)
FALLBACK_TIER_CONFIG = {
    "cerebro":       "mistralai/devstral-2512",
    "worker":        "stepfun/step-3.5-flash",
    "worker_budget": "xiaomi/mimo-v2-flash",
    "evaluador":     "deepcogito/cogito-v2.1-671b",
    "swarm":         "openai/gpt-4o-mini",
    "compress":      "xiaomi/mimo-v2-flash",
    "fast":          "moonshotai/kimi-k2.5",
    # Legacy aliases
    "orchestrator":  "mistralai/devstral-2512",
    "synthesis":     "deepcogito/cogito-v2.1-671b",
}

FALLBACK_PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
    "minimax/minimax-m2.5": {"input": 0.27, "output": 0.95},
    "google/gemini-3.1-pro": {"input": 2.00, "output": 12.00},
    "google/gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "openai/gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "openai/gpt-5.4": {"input": 2.50, "output": 15.00},
    "qwen/qwen3-coder-next": {"input": 0.00, "output": 0.00},
    "deepseek/deepseek-v3.2": {"input": 0.28, "output": 0.42},
    "mistralai/devstral-small": {"input": 0.10, "output": 0.30},
    "mistralai/devstral-2512": {"input": 0.50, "output": 2.00},
    "z-ai/glm-4.7": {"input": 0.38, "output": 1.98},
    "moonshotai/kimi-k2.5": {"input": 0.45, "output": 2.20},
}

# Models that use Anthropic API directly (not OpenRouter)
ANTHROPIC_MODELS = {"claude-sonnet-4-6", "claude-opus-4-6"}


def _get_conn():
    """Get DB connection from shared pool."""
    from .db_pool import get_conn
    return get_conn()


def _put_conn(conn):
    """Return connection to pool."""
    from .db_pool import put_conn
    put_conn(conn)


class ModelObservatory:
    """DB-driven model registry with auto-discovery and A/B testing."""

    def __init__(self):
        self._cache = {}
        self._cache_ts = 0
        self._cache_ttl = 300  # 5 min

    def _load_from_db(self) -> bool:
        """Load active models from DB into cache."""
        now = time.time()
        if self._cache and (now - self._cache_ts) < self._cache_ttl:
            return True

        conn = _get_conn()
        if not conn:
            return False

        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT model_id, provider, display_name, tier, status,
                           cost_input_per_m, cost_output_per_m,
                           supports_tools, supports_vision, supports_streaming,
                           quality_score, speed_score, cost_score, roi_score,
                           context_window, health_status, metadata
                    FROM model_registry
                    WHERE status = 'active'
                    ORDER BY roi_score DESC
                """)
                rows = cur.fetchall()

            self._cache = {
                "models": {r["model_id"]: dict(r) for r in rows},
                "tier_config": {},
                "pricing": {},
            }
            for r in rows:
                if r["tier"]:
                    self._cache["tier_config"][r["tier"]] = r["model_id"]
                self._cache["pricing"][r["model_id"]] = {
                    "input": r["cost_input_per_m"] or 0.0,
                    "output": r["cost_output_per_m"] or 0.0,
                }
            self._cache_ts = now
            return True
        except Exception:
            return False
        finally:
            _put_conn(conn)

    def get_tier_config(self) -> dict:
        """Get current tier config (DB-driven with fallback)."""
        if self._load_from_db() and self._cache.get("tier_config"):
            return self._cache["tier_config"]
        return FALLBACK_TIER_CONFIG.copy()

    def get_model_for_tier(self, tier: str) -> str:
        """Get model ID for a specific tier."""
        config = self.get_tier_config()
        return config.get(tier, config.get("fallback", "qwen/qwen3-coder-next"))

    def get_pricing(self, model_id: str) -> dict:
        """Get pricing for a model (DB-driven with fallback)."""
        if self._load_from_db() and model_id in self._cache.get("pricing", {}):
            return self._cache["pricing"][model_id]
        return FALLBACK_PRICING.get(model_id, {"input": 1.0, "output": 1.0})

    def get_output_price(self, model_id: str) -> float:
        """Get output price per M tokens."""
        return self.get_pricing(model_id).get("output", 1.0)

    def is_anthropic_model(self, model_id: str) -> bool:
        """Check if model should use Anthropic API directly."""
        return model_id in ANTHROPIC_MODELS

    def get_all_models(self) -> dict:
        """Get all models from registry."""
        if self._load_from_db():
            return self._cache.get("models", {})
        return {}

    def get_best_for_task(self, task_type: str, max_cost: float = None) -> str:
        """Select best model for task type considering ROI."""
        task_to_tier = {
            "code_gen": "code_gen",
            "debugging": "code_gen",
            "refactoring": "code_gen",
            "testing": "code_gen",
            "architecture": "reasoning",
            "security": "reasoning",
            "documentation": "fast",
            "devops": "fast",
            "synthesis": "synthesis",
            "vision": "vision",
            "compress": "compress",
            "routing": "fast",
        }
        tier = task_to_tier.get(task_type, "code_gen")
        model = self.get_model_for_tier(tier)

        if max_cost is not None:
            price = self.get_output_price(model)
            if price > max_cost:
                model = self.get_model_for_tier("fallback")

        return model

    def discover_models(self) -> dict:
        """Query OpenRouter API for available models, update registry with candidates."""
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not openrouter_key:
            return {"error": "No OPENROUTER_API_KEY", "discovered": 0}

        try:
            cmd = [
                'curl', '-s', '--max-time', '30',
                '-H', f'Authorization: Bearer {openrouter_key}',
                'https://openrouter.ai/api/v1/models'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if result.returncode != 0:
                return {"error": f"curl failed: {result.stderr[:200]}", "discovered": 0}

            data = json.loads(result.stdout)
            models = data.get("data", [])
        except Exception as e:
            return {"error": str(e), "discovered": 0}

        # Filter relevant models
        candidates = []
        for m in models:
            ctx = m.get("context_length", 0) or 0
            if ctx < 32000:
                continue

            pricing = m.get("pricing", {})
            cost_out = float(pricing.get("completion", 0) or 0) * 1_000_000
            cost_in = float(pricing.get("prompt", 0) or 0) * 1_000_000

            candidates.append({
                "model_id": m["id"],
                "display_name": m.get("name", m["id"]),
                "context_window": ctx,
                "cost_input_per_m": round(cost_in, 4),
                "cost_output_per_m": round(cost_out, 4),
            })

        # Persist new candidates to DB
        conn = _get_conn()
        if not conn:
            return {"discovered": len(candidates), "persisted": 0, "error": "No DB connection"}

        new_count = 0
        try:
            with conn.cursor() as cur:
                for c in candidates:
                    cur.execute("""
                        INSERT INTO model_registry
                            (model_id, provider, display_name, context_window,
                             cost_input_per_m, cost_output_per_m, status)
                        VALUES (%s, 'openrouter', %s, %s, %s, %s, 'candidate')
                        ON CONFLICT (model_id) DO UPDATE SET
                            cost_input_per_m = EXCLUDED.cost_input_per_m,
                            cost_output_per_m = EXCLUDED.cost_output_per_m,
                            context_window = EXCLUDED.context_window,
                            updated_at = NOW()
                    """, [c["model_id"], c["display_name"], c["context_window"],
                          c["cost_input_per_m"], c["cost_output_per_m"]])
                    if cur.statusmessage.endswith("INSERT 0 1"):
                        new_count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            return {"discovered": len(candidates), "persisted": 0, "error": str(e)}
        finally:
            _put_conn(conn)

        self._cache_ts = 0  # Invalidate cache
        return {"discovered": len(candidates), "new": new_count}

    def health_check(self, model_id: str) -> dict:
        """Ping model with trivial prompt, measure latency."""
        from .api import call_openrouter, OPENROUTER_KEY
        from .costes import set_call_context
        set_call_context(componente='model_observatory', operacion='health_check')

        messages = [{"role": "user", "content": "Reply with exactly: OK"}]
        start = time.time()

        try:
            if self.is_anthropic_model(model_id):
                return self._health_check_anthropic(model_id)

            resp = call_openrouter(messages, model_id, max_tokens=10)
            latency_ms = int((time.time() - start) * 1000)
            content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            healthy = len(content) > 0

            self._update_health(model_id, "healthy" if healthy else "degraded", latency_ms)
            return {"model_id": model_id, "status": "healthy" if healthy else "degraded",
                    "latency_ms": latency_ms, "response": content[:50]}
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            self._update_health(model_id, "down", latency_ms)
            return {"model_id": model_id, "status": "down", "latency_ms": latency_ms,
                    "error": str(e)[:200]}

    def _health_check_anthropic(self, model_id: str) -> dict:
        """Health check for Anthropic models."""
        try:
            import anthropic
            client = anthropic.Anthropic()
            start = time.time()
            resp = client.messages.create(
                model=model_id,
                max_tokens=10,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            )
            latency_ms = int((time.time() - start) * 1000)
            content = resp.content[0].text if resp.content else ""
            self._update_health(model_id, "healthy", latency_ms)
            return {"model_id": model_id, "status": "healthy",
                    "latency_ms": latency_ms, "response": content[:50]}
        except Exception as e:
            self._update_health(model_id, "down", 0)
            return {"model_id": model_id, "status": "down", "error": str(e)[:200]}

    def _update_health(self, model_id: str, status: str, latency_ms: int = 0) -> None:
        """Update health status in DB."""
        conn = _get_conn()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE model_registry
                    SET health_status = %s, last_health_check = NOW(), updated_at = NOW()
                    WHERE model_id = %s
                """, [status, model_id])
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            _put_conn(conn)

    def health_check_all(self) -> dict:
        """Health check all active models."""
        models = self.get_all_models()
        if not models:
            config = self.get_tier_config()
            models = {mid: {"model_id": mid} for mid in set(config.values())}

        results = {}
        for model_id in models:
            results[model_id] = self.health_check(model_id)
        return results

    def promote_model(self, model_id: str, tier: str) -> dict:
        """Promote a model to active for a tier."""
        conn = _get_conn()
        if not conn:
            return {"error": "No DB connection"}

        try:
            with conn.cursor() as cur:
                # Demote current tier holder
                cur.execute("""
                    UPDATE model_registry SET tier = NULL, status = 'candidate'
                    WHERE tier = %s AND status = 'active'
                """, [tier])
                # Promote new model
                cur.execute("""
                    UPDATE model_registry SET tier = %s, status = 'active', updated_at = NOW()
                    WHERE model_id = %s
                """, [tier, model_id])
            conn.commit()
            self._cache_ts = 0  # Invalidate cache
            return {"promoted": model_id, "tier": tier}
        except Exception as e:
            conn.rollback()
            return {"error": str(e)}
        finally:
            _put_conn(conn)

    def get_market_report(self) -> dict:
        """Summary: active models, candidates, health, costs."""
        conn = _get_conn()
        if not conn:
            return {"error": "No DB connection"}

        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT model_id, display_name, tier, status,
                           cost_output_per_m, quality_score, roi_score,
                           health_status, last_health_check
                    FROM model_registry
                    ORDER BY status, roi_score DESC
                """)
                all_models = cur.fetchall()

                cur.execute("""
                    SELECT count(*) FILTER (WHERE status = 'active') as active,
                           count(*) FILTER (WHERE status = 'candidate') as candidates,
                           count(*) FILTER (WHERE health_status = 'down') as down
                    FROM model_registry
                """)
                summary = cur.fetchone()

            return {
                "summary": dict(summary),
                "models": [dict(m) for m in all_models],
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            _put_conn(conn)

    def run_benchmark(self, model_id: str, benchmark: str = "tool_use") -> dict:
        """Run internal benchmark against a model."""
        from .costes import set_call_context
        set_call_context(componente='model_observatory', operacion='benchmark')
        benchmarks = {
            "tool_use": self._benchmark_tool_use,
            "code_gen": self._benchmark_code_gen,
            "reasoning": self._benchmark_reasoning,
        }
        fn = benchmarks.get(benchmark)
        if not fn:
            return {"error": f"Unknown benchmark: {benchmark}"}
        return fn(model_id)

    def _benchmark_tool_use(self, model_id: str) -> dict:
        """Benchmark: can the model correctly call tools?"""
        from .api import call_openrouter

        tools = [{
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        }]
        messages = [{"role": "user", "content": "Read the file /tmp/test.py"}]

        start = time.time()
        try:
            if self.is_anthropic_model(model_id):
                return {"model_id": model_id, "benchmark": "tool_use",
                        "note": "Anthropic tool_use benchmark not yet implemented"}

            resp = call_openrouter(messages, model_id, tools=tools, max_tokens=200)
            latency_ms = int((time.time() - start) * 1000)
            msg = resp.get("choices", [{}])[0].get("message", {})
            tool_calls = msg.get("tool_calls", [])

            score = 0.0
            if tool_calls:
                tc = tool_calls[0]
                if tc.get("function", {}).get("name") == "read_file":
                    score = 0.5
                    args = json.loads(tc["function"].get("arguments", "{}"))
                    if args.get("path") == "/tmp/test.py":
                        score = 1.0

            self._persist_benchmark(model_id, "tool_use", score, 1.0, latency_ms)
            return {"model_id": model_id, "benchmark": "tool_use",
                    "score": score, "max_score": 1.0, "latency_ms": latency_ms}
        except Exception as e:
            return {"model_id": model_id, "benchmark": "tool_use",
                    "score": 0.0, "error": str(e)[:200]}

    def _benchmark_code_gen(self, model_id: str) -> dict:
        """Benchmark: generate a simple Python function."""
        from .api import call_openrouter, extract_response

        messages = [{"role": "user", "content":
            "Write a Python function `is_palindrome(s: str) -> bool` that checks if a string "
            "is a palindrome. Return ONLY the function, no explanation."}]

        start = time.time()
        try:
            if self.is_anthropic_model(model_id):
                return {"model_id": model_id, "benchmark": "code_gen",
                        "note": "Anthropic code_gen benchmark not yet implemented"}

            resp = call_openrouter(messages, model_id, max_tokens=300)
            latency_ms = int((time.time() - start) * 1000)
            content, _, _ = extract_response(resp)

            score = 0.0
            if "def is_palindrome" in content:
                score = 0.5
                if "return" in content and ("[::-1]" in content or "reversed" in content):
                    score = 1.0

            self._persist_benchmark(model_id, "code_gen", score, 1.0, latency_ms)
            return {"model_id": model_id, "benchmark": "code_gen",
                    "score": score, "max_score": 1.0, "latency_ms": latency_ms}
        except Exception as e:
            return {"model_id": model_id, "benchmark": "code_gen",
                    "score": 0.0, "error": str(e)[:200]}

    def _benchmark_reasoning(self, model_id: str) -> dict:
        """Benchmark: simple reasoning task."""
        from .api import call_openrouter, extract_response

        messages = [{"role": "user", "content":
            "If all roses are flowers and some flowers fade quickly, can we conclude "
            "that some roses fade quickly? Answer with ONLY 'Yes' or 'No' and one sentence explaining."}]

        start = time.time()
        try:
            if self.is_anthropic_model(model_id):
                return {"model_id": model_id, "benchmark": "reasoning",
                        "note": "Anthropic reasoning benchmark not yet implemented"}

            resp = call_openrouter(messages, model_id, max_tokens=100)
            latency_ms = int((time.time() - start) * 1000)
            content, _, _ = extract_response(resp)

            score = 0.0
            lower = content.lower()
            if "no" in lower.split()[:3]:
                score = 1.0
            elif "cannot" in lower or "not necessarily" in lower:
                score = 0.8

            self._persist_benchmark(model_id, "reasoning", score, 1.0, latency_ms)
            return {"model_id": model_id, "benchmark": "reasoning",
                    "score": score, "max_score": 1.0, "latency_ms": latency_ms}
        except Exception as e:
            return {"model_id": model_id, "benchmark": "reasoning",
                    "score": 0.0, "error": str(e)[:200]}

    def _persist_benchmark(self, model_id: str, benchmark_name: str,
                           score: float, max_score: float, latency_ms: int) -> None:
        """Save benchmark result to DB."""
        conn = _get_conn()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO model_benchmarks (model_id, benchmark_name, score, max_score, latency_p50_ms)
                    VALUES (%s, %s, %s, %s, %s)
                """, [model_id, benchmark_name, score, max_score, latency_ms])
                cur.execute("""
                    UPDATE model_registry SET last_benchmarked = NOW(), updated_at = NOW()
                    WHERE model_id = %s
                """, [model_id])
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            _put_conn(conn)

    def start_ab_test(self, tier: str, model_b: str, test_name: str = None) -> dict:
        """Start A/B test between current tier champion and challenger."""
        config = self.get_tier_config()
        model_a = config.get(tier)
        if not model_a:
            return {"error": f"Unknown tier: {tier}"}

        if not test_name:
            test_name = f"{tier}_{model_a}_vs_{model_b}"

        conn = _get_conn()
        if not conn:
            return {"error": "No DB connection"}

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO model_ab_tests (test_name, model_a, model_b, tier, status)
                    VALUES (%s, %s, %s, %s, 'running')
                    RETURNING id
                """, [test_name, model_a, model_b, tier])
                test_id = cur.fetchone()[0]
            conn.commit()
            return {"test_id": test_id, "model_a": model_a, "model_b": model_b, "tier": tier}
        except Exception as e:
            conn.rollback()
            return {"error": str(e)}
        finally:
            _put_conn(conn)


# Singleton instance
_observatory = None

def get_observatory() -> ModelObservatory:
    """Get or create singleton observatory."""
    global _observatory
    if _observatory is None:
        _observatory = ModelObservatory()
    return _observatory
