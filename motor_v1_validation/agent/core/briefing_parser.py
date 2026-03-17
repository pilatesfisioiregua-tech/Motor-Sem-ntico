"""Briefing parser — .md con estructura fija → lista de pasos atomicos."""

import re
from dataclasses import dataclass, field
from pathlib import Path


MAX_INSTRUCTION_LINES = 15


@dataclass
class BriefingStep:
    number: int
    description: str
    files: list
    instruction: str
    success_criteria: str
    repo_dir: str


@dataclass
class Briefing:
    title: str
    repo_dir: str
    context: str
    steps: list


def parse_briefing(path: str) -> Briefing:
    """Parse .md briefing into structured steps.

    Expected format:
        # BRIEFING: [titulo]
        ## REPO: [directorio base]
        ## CONTEXTO: [2-3 lineas]

        ### PASO N: [descripcion]
        ARCHIVOS: a.py, b.py
        INSTRUCCION:
        [4-15 lineas]
        CRITERIO: [1 linea]

    Raises ValueError if format is invalid or instruction exceeds 15 lines.
    """
    text = Path(path).read_text(encoding='utf-8')

    # Parse header
    title_match = re.search(r'^#\s+BRIEFING:\s*(.+)$', text, re.MULTILINE)
    if not title_match:
        raise ValueError("Briefing must start with '# BRIEFING: [titulo]'")
    title = title_match.group(1).strip()

    repo_match = re.search(r'^##\s+REPO:\s*(.+)$', text, re.MULTILINE)
    if not repo_match:
        raise ValueError("Briefing must have '## REPO: [directorio]'")
    repo_dir = repo_match.group(1).strip()

    context_match = re.search(r'^##\s+CONTEXTO:\s*(.+?)(?=\n###|\Z)', text, re.MULTILINE | re.DOTALL)
    context = context_match.group(1).strip() if context_match else ""

    # Split into step blocks
    step_blocks = re.split(r'(?=^###\s+PASO\s+\d+)', text, flags=re.MULTILINE)
    step_blocks = [b for b in step_blocks if re.match(r'^###\s+PASO\s+\d+', b)]

    if not step_blocks:
        raise ValueError("Briefing must have at least one '### PASO N: ...' section")

    steps = []
    for block in step_blocks:
        step = _parse_step_block(block, repo_dir)
        steps.append(step)

    return Briefing(title=title, repo_dir=repo_dir, context=context, steps=steps)


def _parse_step_block(block: str, repo_dir: str) -> BriefingStep:
    """Parse a single ### PASO block."""
    # Number + description
    header = re.match(r'^###\s+PASO\s+(\d+):\s*(.+)$', block, re.MULTILINE)
    if not header:
        raise ValueError(f"Invalid step header: {block[:80]}")
    number = int(header.group(1))
    description = header.group(2).strip()

    # ARCHIVOS
    files_match = re.search(r'^ARCHIVOS:\s*(.+)$', block, re.MULTILINE)
    if not files_match:
        raise ValueError(f"PASO {number}: missing ARCHIVOS line")
    files = [f.strip() for f in files_match.group(1).split(',') if f.strip()]

    # INSTRUCCION (multiline block until CRITERIO)
    instr_match = re.search(
        r'^INSTRUCCI[OÓ]N:\s*\n(.*?)(?=^CRITERIO:)',
        block, re.MULTILINE | re.DOTALL
    )
    if not instr_match:
        raise ValueError(f"PASO {number}: missing INSTRUCCION block")
    instruction = instr_match.group(1).strip()

    # Hard limit
    line_count = len(instruction.splitlines())
    if line_count > MAX_INSTRUCTION_LINES:
        raise ValueError(
            f"PASO {number}: instruction has {line_count} lines (max {MAX_INSTRUCTION_LINES}). "
            f"Rewrite the briefing with shorter steps."
        )

    # CRITERIO
    criterio_match = re.search(r'^CRITERIO:\s*(.+)$', block, re.MULTILINE)
    if not criterio_match:
        raise ValueError(f"PASO {number}: missing CRITERIO line")
    success_criteria = criterio_match.group(1).strip()

    return BriefingStep(
        number=number,
        description=description,
        files=files,
        instruction=instruction,
        success_criteria=success_criteria,
        repo_dir=repo_dir,
    )
