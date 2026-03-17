"""Swarm Coordinator — decomposes tasks, delegates to child agents, aggregates results."""

import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from .child import ChildAgent


class SwarmCoordinator:
    """Coordinates multiple child agents working in parallel."""

    def __init__(self, max_workers: int = 3, sandbox_dir: str = "",
                 strategy: str = "tiered", max_cost_per_child: float = 0.5,
                 max_iter_per_child: int = 15, verbose: bool = False):
        self.max_workers = max_workers
        self.sandbox_dir = sandbox_dir
        self.strategy = strategy
        self.max_cost_per_child = max_cost_per_child
        self.max_iter_per_child = max_iter_per_child
        self.verbose = verbose

    def validate_independence(self, subtasks: List[dict]) -> Optional[str]:
        """Check that subtasks don't operate on the same files.
        Returns error message if conflict detected, None if OK."""
        all_files = {}
        for task in subtasks:
            files = task.get("files", [])
            for f in files:
                if f in all_files:
                    return (f"Conflict: '{f}' is used by both "
                            f"'{all_files[f]}' and '{task.get('name', '?')}'")
                all_files[f] = task.get("name", "unknown")
        return None

    def execute(self, subtasks: List[dict], context: str = "") -> dict:
        """Execute subtasks in parallel using child agents.

        Each subtask dict should have:
            - name: str — task name
            - goal: str — what to do
            - files: list[str] — files this task will touch (for conflict detection)
        """
        if not subtasks:
            return {"error": "No subtasks provided"}

        # Validate independence
        conflict = self.validate_independence(subtasks)
        if conflict:
            return {"error": f"Cannot parallelize: {conflict}"}

        if self.verbose:
            print(f"  [Swarm] Launching {len(subtasks)} children (max {self.max_workers} parallel)")

        results = {}
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for task in subtasks:
                child = ChildAgent(
                    name=task.get("name", "child"),
                    goal=task["goal"],
                    sandbox_dir=self.sandbox_dir,
                    strategy=self.strategy,
                    max_iterations=self.max_iter_per_child,
                    max_cost=self.max_cost_per_child,
                    context=context,
                    verbose=self.verbose,
                )
                future = executor.submit(child.run)
                futures[future] = task.get("name", "unknown")

            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result(timeout=300)
                    results[name] = result
                    if self.verbose:
                        status = result.get("stop_reason", "?")
                        print(f"  [Swarm] {name}: {status} ({result.get('iterations', 0)} iters, "
                              f"${result.get('cost_usd', 0):.4f})")
                except Exception as e:
                    results[name] = {"error": str(e), "stop_reason": "CHILD_ERROR"}

        total_time = time.time() - start_time
        total_cost = sum(r.get("cost_usd", 0) for r in results.values() if isinstance(r, dict))
        all_done = all(r.get("stop_reason") == "DONE" for r in results.values() if isinstance(r, dict))

        return {
            "subtask_results": results,
            "total_time_s": round(total_time, 1),
            "total_cost_usd": round(total_cost, 4),
            "all_succeeded": all_done,
            "children_count": len(subtasks),
        }
