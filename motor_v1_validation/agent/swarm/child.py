"""Child Agent — isolated worker agent for swarm execution."""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ChildAgent:
    """A child agent that runs an isolated task within the swarm."""
    name: str = "child"
    goal: str = ""
    sandbox_dir: str = ""
    strategy: str = "tiered"
    max_iterations: int = 15
    max_cost: float = 0.5
    context: str = ""
    verbose: bool = False

    def run(self) -> dict:
        """Execute the child's goal. Returns result dict."""
        from core.agent_loop import run_agent_loop
        from tools import create_default_registry

        registry = create_default_registry(self.sandbox_dir)

        result = run_agent_loop(
            goal=self.goal,
            mode="goal",
            project_dir=self.sandbox_dir,
            strategy=self.strategy,
            max_iterations=self.max_iterations,
            max_cost=self.max_cost,
            sandbox_dir=self.sandbox_dir,
            verbose=self.verbose,
            autonomous=True,
            context_prompt=self.context,
            session_id=f"child-{self.name}",
            registry=registry,
        )

        return {
            "name": self.name,
            "result": result.get("result"),
            "stop_reason": result.get("stop_reason"),
            "iterations": result.get("iterations", 0),
            "cost_usd": result.get("cost_usd", 0),
            "files_changed": result.get("files_changed", []),
        }
