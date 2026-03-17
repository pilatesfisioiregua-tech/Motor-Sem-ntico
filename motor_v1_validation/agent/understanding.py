"""Code OS — Understanding Layer.
Loads project context, translates non-technical vision to specs, generates briefings.
"""

import os
import json
import glob as glob_module
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ProjectContext:
    """Complete context about a project."""
    project_dir: str = ""
    project_name: str = ""
    claude_md: str = ""
    structure: str = ""
    stack: str = ""
    briefings: List[str] = field(default_factory=list)
    design_docs: List[str] = field(default_factory=list)
    session_history: List[dict] = field(default_factory=list)
    past_errors: List[str] = field(default_factory=list)
    best_models: Dict[str, Any] = field(default_factory=dict)

    def to_prompt(self, max_chars: int = 8000) -> str:
        """Render context as a prompt section for the LLM."""
        parts = []
        if self.claude_md:
            parts.append(f"## Project Instructions (CLAUDE.md)\n{self.claude_md[:2000]}")
        if self.structure:
            parts.append(f"## Project Structure\n{self.structure[:1500]}")
        if self.stack:
            parts.append(f"## Stack: {self.stack}")
        if self.briefings:
            briefs = "\n".join(f"- {b}" for b in self.briefings[:10])
            parts.append(f"## Existing Briefings\n{briefs}")
        if self.design_docs:
            docs = "\n".join(f"- {d}" for d in self.design_docs[:5])
            parts.append(f"## Design Documents\n{docs}")
        if self.session_history:
            hist = "\n".join(
                f"- [{s.get('mode','?')}] {s.get('input_raw','')[:100]} → {s.get('status','?')}"
                for s in self.session_history[:5]
            )
            parts.append(f"## Recent Sessions\n{hist}")
        if self.past_errors:
            errs = "\n".join(f"- {e[:150]}" for e in self.past_errors[:5])
            parts.append(f"## Common Errors (avoid these)\n{errs}")

        result = "\n\n".join(parts)
        if len(result) > max_chars:
            result = result[:max_chars] + "\n... [truncated]"
        return result


@dataclass
class TechnicalSpec:
    """Technical specification generated from a vision."""
    objective: str = ""
    modules: List[dict] = field(default_factory=list)
    implementation_order: List[str] = field(default_factory=list)
    expected_failures: List[dict] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)


class ContextLoader:
    """Loads project context from local files + Supabase history."""

    def load(self, project_dir: str, supabase_client=None) -> ProjectContext:
        ctx = ProjectContext(
            project_dir=project_dir,
            project_name=os.path.basename(os.path.abspath(project_dir)),
        )

        # 1. CLAUDE.md
        for name in ["CLAUDE.md", "claude.md", ".claude.md"]:
            path = os.path.join(project_dir, name)
            if os.path.isfile(path):
                ctx.claude_md = Path(path).read_text(errors='replace')[:4000]
                break
            # Check parent dirs (up to 3 levels)
            for parent in [os.path.dirname(project_dir),
                          os.path.dirname(os.path.dirname(project_dir))]:
                ppath = os.path.join(parent, name)
                if os.path.isfile(ppath):
                    ctx.claude_md = Path(ppath).read_text(errors='replace')[:4000]
                    break

        # 2. Directory structure (2 levels deep)
        ctx.structure = self._list_tree(project_dir, max_depth=2)

        # 3. Detect stack
        ctx.stack = self._detect_stack(project_dir)

        # 4. Existing briefings
        briefing_dirs = [
            os.path.join(project_dir, "briefings"),
            os.path.join(project_dir, "docs", "briefings"),
        ]
        for bdir in briefing_dirs:
            if os.path.isdir(bdir):
                for f in sorted(os.listdir(bdir)):
                    if f.endswith(".md"):
                        ctx.briefings.append(f)

        # 5. Design docs
        for pattern in ["DISENO*.md", "DESIGN*.md", "ARCHITECTURE*.md", "docs/design*.md"]:
            for f in glob_module.glob(os.path.join(project_dir, pattern)):
                ctx.design_docs.append(os.path.basename(f))
            # Check parent
            parent = os.path.dirname(project_dir)
            for f in glob_module.glob(os.path.join(parent, pattern)):
                ctx.design_docs.append(os.path.basename(f))

        # 6. Supabase history (if available)
        if supabase_client and supabase_client.enabled:
            ctx.session_history = supabase_client.get_project_history(
                ctx.project_name, limit=5)
            errors = supabase_client.get_common_errors(ctx.project_name)
            ctx.past_errors = [e.get("tool_result", "")[:200] for e in errors[:10]]
            ctx.best_models = supabase_client.get_best_models(ctx.project_name)

        return ctx

    def _list_tree(self, root: str, max_depth: int = 2, prefix: str = "") -> str:
        """List directory tree up to max_depth."""
        lines = []
        try:
            entries = sorted(os.listdir(root))
        except PermissionError:
            return "(permission denied)"

        # Filter out common noise
        skip = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
                '.DS_Store', '.mypy_cache', '.pytest_cache', 'dist', 'build'}
        entries = [e for e in entries if e not in skip]

        for i, entry in enumerate(entries[:30]):  # Max 30 entries per level
            full = os.path.join(root, entry)
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry}")

            if os.path.isdir(full) and max_depth > 0:
                extension = "    " if is_last else "│   "
                subtree = self._list_tree(full, max_depth - 1, prefix + extension)
                if subtree:
                    lines.append(subtree)

        return "\n".join(lines)

    def _detect_stack(self, project_dir: str) -> str:
        """Detect project stack from marker files."""
        markers = {
            "package.json": "Node.js/TypeScript",
            "requirements.txt": "Python",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "pom.xml": "Java (Maven)",
            "build.gradle": "Java (Gradle)",
            "Gemfile": "Ruby",
            "composer.json": "PHP",
            "deno.json": "Deno/TypeScript",
            "fly.toml": "+fly.io",
            "Dockerfile": "+Docker",
            "docker-compose.yml": "+Docker Compose",
        }
        detected = []
        for marker, stack in markers.items():
            if os.path.isfile(os.path.join(project_dir, marker)):
                detected.append(stack)
        return ", ".join(detected) if detected else "Unknown"


class VisionTranslator:
    """Translates non-technical vision into a technical specification.
    Uses LLM via the agent's call_openrouter function.
    """

    TRANSLATE_PROMPT = """You are a senior software architect. A non-technical user is describing their vision for a feature or product. Your job:

1. UNDERSTAND what they want (focus on the WHAT, not the HOW)
2. If anything is ambiguous, list specific questions (max 3)
3. Translate their vision into a structured technical specification

PROJECT CONTEXT:
{context}

USER'S VISION:
{vision}

Respond in JSON format:
{{
    "objective": "One clear sentence describing what needs to be built",
    "modules": [
        {{"name": "module_name", "purpose": "what it does", "dependencies": ["other_module"]}}
    ],
    "implementation_order": ["Step 1: ...", "Step 2: ..."],
    "expected_failures": [
        {{"scenario": "what might go wrong", "recovery": "how to handle it"}}
    ],
    "constraints": ["constraint 1", "constraint 2"],
    "tests": ["test description 1", "test description 2"],
    "questions": ["question if ambiguous (or empty list if clear)"]
}}

IMPORTANT: Use the project's existing stack, patterns, and conventions. Do NOT introduce new frameworks or languages unless absolutely necessary."""

    def translate(self, vision: str, context: ProjectContext,
                  call_llm_fn=None) -> TechnicalSpec:
        """Translate vision to spec using LLM.

        Args:
            vision: Non-technical description from user
            context: Project context
            call_llm_fn: Function(messages, model) -> response dict
        """
        prompt = self.TRANSLATE_PROMPT.format(
            context=context.to_prompt(max_chars=4000),
            vision=vision,
        )

        if call_llm_fn is None:
            # Return a placeholder spec if no LLM available
            return TechnicalSpec(objective=vision)

        messages = [
            {"role": "system", "content": "You are a software architect. Respond only in valid JSON."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = call_llm_fn(messages, model=None)  # Uses default model
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            # Extract JSON from response (handle markdown code blocks)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            data = json.loads(content)
            return TechnicalSpec(
                objective=data.get("objective", vision),
                modules=data.get("modules", []),
                implementation_order=data.get("implementation_order", []),
                expected_failures=data.get("expected_failures", []),
                constraints=data.get("constraints", []),
                tests=data.get("tests", []),
            )
        except (json.JSONDecodeError, KeyError, IndexError):
            return TechnicalSpec(objective=vision)


class BriefingGenerator:
    """Generates briefings in the project's standard BRIEFING_XX format."""

    BRIEFING_TEMPLATE = """# BRIEFING_{number:02d} — {title}

**Objetivo:** {objective}
**Pre-requisito:** {prerequisites}
**Output:** {outputs}

## TAREA

{task_checklist}

## IMPLEMENTACIÓN

{implementation}

## VERIFICACIÓN

{verification}
"""

    GENERATE_PROMPT = """You are an expert technical writer generating implementation briefings.

PROJECT CONTEXT:
{context}

TECHNICAL SPECIFICATION:
{spec}

Generate a complete briefing following this exact format:

# BRIEFING_{number:02d} — [TITLE]

**Objetivo:** [Clear objective in 1-2 sentences]
**Pre-requisito:** [What must be done before this briefing]
**Output:** [What this briefing produces]

## TAREA
[Numbered checklist of 5-7 major implementation steps]

## IMPLEMENTACIÓN
[For each task, provide:
- What it does ("Qué hace")
- Complete, copy-paste ready code with type hints
- Data structures and models]

## VERIFICACIÓN
[Exact commands to verify the implementation works. Example:
```bash
python3 -c "from src.module import Class; print('OK')"
pytest tests/test_module.py -v
```]

RULES:
- Code must be COMPLETE and COPY-PASTE READY
- Use the project's existing stack ({stack})
- Follow existing conventions from CLAUDE.md
- Type hints are mandatory for Python
- Each module gets a 1-line docstring
- Tests use pytest + pytest-asyncio for async code
- Do NOT introduce new dependencies unless essential"""

    def generate(self, spec: TechnicalSpec, context: ProjectContext,
                 briefing_number: int = 5, call_llm_fn=None) -> str:
        """Generate a complete briefing from a technical spec.

        Args:
            spec: Technical specification
            context: Project context
            briefing_number: Sequential number for this briefing
            call_llm_fn: Function(messages, model) -> response dict
        """
        spec_text = json.dumps({
            "objective": spec.objective,
            "modules": spec.modules,
            "implementation_order": spec.implementation_order,
            "expected_failures": spec.expected_failures,
            "constraints": spec.constraints,
            "tests": spec.tests,
        }, indent=2, ensure_ascii=False)

        prompt = self.GENERATE_PROMPT.format(
            context=context.to_prompt(max_chars=4000),
            spec=spec_text,
            number=briefing_number,
            stack=context.stack,
        )

        if call_llm_fn is None:
            # Return a basic template if no LLM available
            return self.BRIEFING_TEMPLATE.format(
                number=briefing_number,
                title=spec.objective[:50].upper(),
                objective=spec.objective,
                prerequisites="Briefings anteriores completados",
                outputs="Módulos implementados + tests pasando",
                task_checklist="\n".join(f"{i+1}. [ ] {step}"
                                       for i, step in enumerate(spec.implementation_order)),
                implementation="[Pendiente de generación con LLM]",
                verification="```bash\npytest tests/ -v\n```",
            )

        messages = [
            {"role": "system", "content": "You are a technical writer. Generate complete, production-ready briefings."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = call_llm_fn(messages, model=None)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip()
        except Exception:
            return self.BRIEFING_TEMPLATE.format(
                number=briefing_number,
                title=spec.objective[:50].upper(),
                objective=spec.objective,
                prerequisites="Briefings anteriores completados",
                outputs="Módulos implementados + tests pasando",
                task_checklist="\n".join(f"{i+1}. [ ] {step}"
                                       for i, step in enumerate(spec.implementation_order)),
                implementation="[Error generating — retry with --verbose]",
                verification="```bash\npytest tests/ -v\n```",
            )
