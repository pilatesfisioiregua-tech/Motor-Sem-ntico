#!/usr/bin/env python3
"""Seed ~70 deep spec patterns across 7 new domains into knowledge_base."""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import psycopg2
import anthropic

# ── Config ────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind",
)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY env var required")
MODEL = "claude-sonnet-4-6"

# ── Domains ───────────────────────────────────────────────────────

DOMAINS: dict[str, list[str]] = {
    "patrones:distributed_systems": [
        "Raft Consensus", "CRDTs", "Vector Clocks", "CAP Theorem", "Saga Pattern",
        "Circuit Breaker", "CQRS", "Event Sourcing", "Gossip Protocol", "Consistent Hashing",
    ],
    "patrones:cognitive_science": [
        "Dual Process Theory", "Bounded Rationality", "Satisficing", "Cognitive Load Theory",
        "Embodied Cognition", "Distributed Cognition", "Metacognition", "Flow States",
        "Attention Networks", "Working Memory",
    ],
    "patrones:game_theory": [
        "Nash Equilibrium", "Mechanism Design", "Schelling Points", "Evolutionary Stable Strategy",
        "Auction Theory", "Bayesian Games", "Signaling Theory", "Repeated Games",
        "Coalition Formation", "Price of Anarchy",
    ],
    "patrones:complexity_science": [
        "Self-Organized Criticality", "Power Laws", "Phase Transitions", "Attractor Landscapes",
        "Cellular Automata", "Small World Networks", "Scale-Free Networks", "Fitness Landscapes",
        "Edge of Chaos", "Stigmergy",
    ],
    "patrones:information_theory": [
        "Shannon Entropy", "Kolmogorov Complexity", "Channel Capacity", "Rate-Distortion Theory",
        "Mutual Information", "Fisher Information", "Minimum Description Length",
        "Error Correction Codes", "Lossy Compression", "Information Bottleneck",
    ],
    "patrones:control_theory": [
        "PID Control", "Kalman Filter", "Adaptive Control", "Robust Control",
        "Model Predictive Control", "Feedback Linearization", "Sliding Mode Control",
        "Optimal Control", "State Estimation", "Stability Margins",
    ],
    "patrones:category_theory": [
        "Monads", "Functors", "Natural Transformations", "Adjunctions", "Yoneda Lemma",
        "Limits and Colimits", "Kan Extensions", "Topoi", "F-Algebras", "Operads",
    ],
}


# ── Helpers ───────────────────────────────────────────────────────

def to_concepto(name: str) -> str:
    """Convert pattern name to lowercase underscored concepto key."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def get_conn() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    conn.autocommit = False
    return conn


def pattern_exists(cur, scope: str, concepto: str) -> bool:
    """Check if a pattern with this scope + concepto already exists."""
    cur.execute(
        """
        SELECT 1 FROM knowledge_base
        WHERE scope = %s AND metadata->>'concepto' = %s
        LIMIT 1
        """,
        (scope, concepto),
    )
    return cur.fetchone() is not None


# ── Prompt builder ────────────────────────────────────────────────

SPEC_PROMPT_TEMPLATE = """Generate a deep technical specification for the pattern "{name}" in the domain "{domain}".

The specification must contain exactly these 10 sections:

1. **Definicion formal**: Rigorous mathematical/conceptual definition. What IS this pattern?
2. **Mecanismo**: How does it work step-by-step? What are the moving parts?
3. **Invariantes**: What properties are always preserved? What can you rely on?
4. **Trade-offs**: What do you gain vs. what do you lose? Quantify where possible.
5. **Condiciones de activacion**: When should this pattern be applied? What triggers it?
6. **Reglas de composicion**: How does this pattern compose with others? What are valid combinations?
7. **Implementaciones canonicas**: 2-3 real-world implementations with concrete details.
8. **Isomorfismos**: What other patterns/concepts is this structurally equivalent to? Cross-domain connections.
9. **Metricas de exito**: How do you measure if this pattern is working well?
10. **Anti-patrones**: What are common misuses? What looks like this pattern but isn't?

Additionally, classify this pattern along 4 dimensions:

- **lentes**: Which analytical lenses apply? Choose 1-3 from: [salud, sentido, continuidad]
- **funciones**: Which functions does it serve? Choose 1-3 from: [conservar, captar, depurar, distribuir, frontera, adaptar, replicar]
- **thinking_types**: Which thinking types? Choose 1-3 from: [percepcion, causalidad, abstraccion, sintesis, discernimiento, metacognicion, consciencia_epistemologica, auto_diagnostico, convergencia, dialectica, analogia, contrafactual, abduccion, provocacion, reencuadre, destruccion_creativa, creacion]
- **conceptual_modes**: Which modes? Choose 1-3 from: [ANALIZAR, PERCIBIR, MOVER, SENTIR, GENERAR, ENMARCAR]

For each dimension, also indicate the PRIMARY (most relevant single value).

Requirements:
- Total spec text: 2000-5000 characters of high-quality technical content
- Be precise and technical, not generic
- Include concrete numbers, thresholds, or formulas where applicable
- Cross-reference other patterns from any domain

Format your response as:
1. The full specification text (sections 1-10, each with its header)
2. Then a JSON metadata block on its own line starting with ```json and ending with ```:

```json
{{
  "propiedades_algebraicas": {{
    "conmutativo": true/false,
    "asociativo": true/false,
    "idempotente": true/false,
    "saturacion_n": N
  }},
  "dimensiones_valor": {{
    "complejidad": "low/medium/high",
    "generalidad": "low/medium/high",
    "composabilidad": "low/medium/high"
  }},
  "lentes": ["..."],
  "funciones": ["..."],
  "thinking_types": ["..."],
  "conceptual_modes": ["..."],
  "lente_funcion_primary": "Lente x Funcion",
  "thinking_primary": "...",
  "mode_primary": "..."
}}
```"""


def build_prompt(name: str, domain: str) -> str:
    return SPEC_PROMPT_TEMPLATE.format(name=name, domain=domain.replace("patrones:", ""))


def parse_response(raw: str) -> tuple[str, dict]:
    """Parse LLM response into (spec_text, metadata_dict).

    Returns the specification text and the parsed JSON metadata.
    If JSON parsing fails, returns empty metadata.
    """
    # Find JSON block
    json_match = re.search(r"```json\s*\n(.*?)\n```", raw, re.DOTALL)
    if json_match:
        spec_text = raw[:json_match.start()].strip()
        try:
            metadata = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            print("    WARNING: Failed to parse JSON metadata block")
            metadata = {}
    else:
        # Try to find a bare JSON object at the end
        brace_idx = raw.rfind("{\n")
        if brace_idx > 0:
            spec_text = raw[:brace_idx].strip()
            try:
                metadata = json.loads(raw[brace_idx:])
            except json.JSONDecodeError:
                spec_text = raw.strip()
                metadata = {}
        else:
            spec_text = raw.strip()
            metadata = {}

    return spec_text, metadata


def insert_pattern(
    cur,
    scope: str,
    concepto: str,
    spec_text: str,
    metadata: dict,
) -> None:
    """Insert a pattern into knowledge_base with taxonomy columns."""
    # Build metadata JSONB (concepto + algebraic props + value dims + isomorfismos)
    meta = {
        "concepto": concepto,
    }
    if "propiedades_algebraicas" in metadata:
        meta["propiedades_algebraicas"] = metadata["propiedades_algebraicas"]
    if "dimensiones_valor" in metadata:
        meta["dimensiones_valor"] = metadata["dimensiones_valor"]

    # Taxonomy arrays (actual columns from migration 006)
    lentes = metadata.get("lentes", [])
    funciones = metadata.get("funciones", [])
    thinking_types = metadata.get("thinking_types", [])
    conceptual_modes = metadata.get("conceptual_modes", [])
    lente_funcion_primary = metadata.get("lente_funcion_primary", "")
    thinking_primary = metadata.get("thinking_primary", "")
    mode_primary = metadata.get("mode_primary", "")

    cur.execute(
        """
        INSERT INTO knowledge_base
            (scope, tipo, texto, metadata, lentes, funciones,
             thinking_types, conceptual_modes,
             lente_funcion_primary, thinking_primary, mode_primary)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            scope,
            "patron",
            spec_text,
            json.dumps(meta, ensure_ascii=False),
            lentes,
            funciones,
            thinking_types,
            conceptual_modes,
            lente_funcion_primary,
            thinking_primary,
            mode_primary,
        ),
    )


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Seed ~70 deep spec patterns across 7 domains into knowledge_base"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be inserted without writing to DB",
    )
    parser.add_argument(
        "--domain", type=str, default=None,
        help="Only process a single domain scope (e.g. patrones:game_theory)",
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Max total patterns to process (0 = unlimited)",
    )
    args = parser.parse_args()

    # Validate domain filter
    if args.domain:
        if args.domain not in DOMAINS:
            print(f"ERROR: Unknown domain '{args.domain}'")
            print(f"Available: {', '.join(sorted(DOMAINS.keys()))}")
            sys.exit(1)
        domains = {args.domain: DOMAINS[args.domain]}
    else:
        domains = DOMAINS

    # Connect
    if not args.dry_run:
        print(f"Connecting to DB...")
        conn = get_conn()
        cur = conn.cursor()
        print(f"  Connected.")
    else:
        conn = None
        cur = None

    # Anthropic client
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Stats
    total_inserted = 0
    total_skipped = 0
    total_errors = 0
    total_chars = 0
    stats_per_domain: dict[str, dict] = {}

    total_patterns = sum(len(pats) for pats in domains.values())
    if args.limit > 0:
        total_patterns = min(total_patterns, args.limit)
    print(f"\nProcessing {total_patterns} patterns across {len(domains)} domains")
    print(f"  Model: {MODEL}")
    print(f"  Dry-run: {args.dry_run}")
    print()

    processed = 0

    for scope, patterns in domains.items():
        domain_label = scope.replace("patrones:", "")
        stats_per_domain[scope] = {"inserted": 0, "skipped": 0, "errors": 0, "chars": 0}

        print(f"=== {domain_label.upper()} ({len(patterns)} patterns) ===")

        for pattern_name in patterns:
            if args.limit > 0 and processed >= args.limit:
                break

            concepto = to_concepto(pattern_name)
            prefix = f"  [{processed + 1}/{total_patterns}] {scope} / {pattern_name}"

            # Check existence
            if not args.dry_run:
                if pattern_exists(cur, scope, concepto):
                    print(f"{prefix} -> SKIP (already exists)")
                    total_skipped += 1
                    stats_per_domain[scope]["skipped"] += 1
                    processed += 1
                    continue

            # Generate spec via Sonnet
            prompt = build_prompt(pattern_name, scope)
            print(f"{prefix} -> generating...", end=" ", flush=True)

            try:
                t0 = time.time()
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=6000,
                    messages=[{"role": "user", "content": prompt}],
                )
                elapsed = round(time.time() - t0, 1)
                raw = response.content[0].text
            except Exception as e:
                print(f"API ERROR: {e}")
                total_errors += 1
                stats_per_domain[scope]["errors"] += 1
                processed += 1
                time.sleep(2)
                continue

            # Parse
            spec_text, metadata = parse_response(raw)
            char_count = len(spec_text)

            if char_count < 500:
                print(f"WARNING: spec too short ({char_count} chars), inserting anyway")

            if args.dry_run:
                lentes = metadata.get("lentes", [])
                thinking = metadata.get("thinking_primary", "?")
                mode = metadata.get("mode_primary", "?")
                print(
                    f"DRY-RUN OK ({char_count} chars, {elapsed}s) "
                    f"lentes={lentes} thinking={thinking} mode={mode}"
                )
            else:
                try:
                    insert_pattern(cur, scope, concepto, spec_text, metadata)
                    conn.commit()
                    print(f"OK ({char_count} chars, {elapsed}s)")
                except Exception as e:
                    conn.rollback()
                    print(f"DB ERROR: {e}")
                    total_errors += 1
                    stats_per_domain[scope]["errors"] += 1
                    processed += 1
                    time.sleep(1)
                    continue

            total_inserted += 1
            total_chars += char_count
            stats_per_domain[scope]["inserted"] += 1
            stats_per_domain[scope]["chars"] += char_count
            processed += 1

            # Rate limiting
            time.sleep(1)

        if args.limit > 0 and processed >= args.limit:
            print(f"\n  Limit of {args.limit} reached.")
            break

        print()

    # Close DB
    if conn:
        conn.close()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Domain':<35} {'Inserted':>8} {'Skipped':>8} {'Errors':>7} {'Chars':>8}")
    print("-" * 60)
    for scope, st in stats_per_domain.items():
        label = scope.replace("patrones:", "")
        print(
            f"  {label:<33} {st['inserted']:>8} {st['skipped']:>8} "
            f"{st['errors']:>7} {st['chars']:>8}"
        )
    print("-" * 60)
    print(
        f"  {'TOTAL':<33} {total_inserted:>8} {total_skipped:>8} "
        f"{total_errors:>7} {total_chars:>8}"
    )
    print()


if __name__ == "__main__":
    main()
