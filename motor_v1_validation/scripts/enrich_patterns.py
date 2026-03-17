#!/usr/bin/env python3
"""Enrich all patterns in knowledge_base from ~140 chars to 2000-5000 chars with deep technical specs and 4-dimension taxonomy classification."""

import os
import sys
import json
import time
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, List

import psycopg2
from psycopg2.extras import Json
import anthropic

# ============================================================
# PATHS & ENV
# ============================================================

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

DB_URL_DEFAULT = "postgresql://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind"


def load_env():
    """Load .env from ../../.env relative to script, or ../.env as fallback."""
    candidates = [
        SCRIPT_DIR / ".." / ".." / ".env",   # ../../.env as specified
        SCRIPT_DIR / ".." / ".env",           # ../.env (motor_v1_validation/.env)
    ]
    for env_path in candidates:
        env_path = env_path.resolve()
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
            print(f"  Loaded env from {env_path}")
            return
    print("  WARNING: No .env file found")


load_env()


def get_db_connection():
    """Connect to PostgreSQL."""
    url = os.environ.get("DATABASE_URL", DB_URL_DEFAULT)
    print(f"  Connecting to DB: {url[:40]}...")
    conn = psycopg2.connect(url, connect_timeout=15)
    conn.autocommit = False
    return conn


def get_anthropic_client():
    """Create Anthropic client."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in env or .env file")
    return anthropic.Anthropic(api_key=api_key)


# ============================================================
# TAXONOMY DIMENSIONS (valid values)
# ============================================================

VALID_LENTES = ["salud", "sentido", "continuidad"]

VALID_FUNCIONES = [
    "conservar", "captar", "depurar", "distribuir",
    "frontera", "adaptar", "replicar"
]

VALID_THINKING_TYPES = [
    "percepcion", "causalidad", "abstraccion", "sintesis",
    "discernimiento", "metacognicion", "consciencia_epistemologica",
    "auto_diagnostico", "convergencia", "dialectica", "analogia",
    "contrafactual", "abduccion", "provocacion", "reencuadre",
    "destruccion_creativa", "creacion"
]

VALID_CONCEPTUAL_MODES = [
    "ANALIZAR", "PERCIBIR", "MOVER", "SENTIR", "GENERAR", "ENMARCAR"
]


# ============================================================
# PROMPT TEMPLATE
# ============================================================

ENRICHMENT_PROMPT = """Eres un experto en patrones de sistemas complejos, algebra de inteligencias y taxonomia cognitiva.

Se te da un patron del repositorio de conocimiento de OMNI-MIND. Tu tarea es generar una especificacion tecnica profunda (2000-5000 caracteres) y clasificarlo en 4 dimensiones taxonomicas.

## PATRON ACTUAL

- **Scope:** {scope}
- **Tipo:** {tipo}
- **Nivel:** {nivel}
- **Concepto(s):** {conceptos}
- **Texto actual:** {texto}

## INSTRUCCIONES

Genera una especificacion tecnica profunda con estas 10 secciones:

1. **Definicion formal** — 2-3 oraciones precisas que definan el patron sin ambiguedad
2. **Mecanismo** — Paso a paso como funciona, con causa-efecto explicito
3. **Invariantes** — Que SIEMPRE se cumple cuando este patron esta activo
4. **Trade-offs** — Que ganas vs que pierdes al aplicarlo
5. **Condiciones de activacion** — Cuando usar, cuando NO usar
6. **Reglas de composicion** — Como se combina con otros patrones (conmutatividad, asociatividad, factorizabilidad)
7. **Implementaciones canonicas** — 3 ejemplos de dominios diferentes (tecnologia, biologia, organizaciones, economia, etc.)
8. **Isomorfismos** — Patrones equivalentes en otros dominios (al menos 3)
9. **Metricas de exito** — Como medir si funciona (cuantitativo cuando sea posible)
10. **Anti-patrones** — Errores comunes al aplicarlo (al menos 2)

## CLASIFICACION MULTIDIMENSIONAL

Clasifica el patron en estas 4 dimensiones (selecciona TODOS los valores que apliquen, y marca el PRIMARY de cada dimension):

### Lentes (perspectiva de valor):
Valores validos: {lentes_validos}

### Funciones (rol funcional):
Valores validos: {funciones_validas}

### Thinking Types (tipo de pensamiento requerido):
Valores validos: {thinking_types_validos}

### Conceptual Modes (modo conceptual dominante):
Valores validos: {conceptual_modes_validos}

## FORMATO DE RESPUESTA

Primero, escribe la especificacion tecnica completa en markdown (las 10 secciones).
Despues, escribe un bloque JSON delimitado por ```json y ``` con EXACTAMENTE esta estructura:

```json
{{
  "propiedades_algebraicas": {{
    "conmutativo": true/false,
    "asociativo": true/false,
    "idempotente": true/false,
    "factorizable": true/false,
    "invariantes": ["invariante 1", "invariante 2"],
    "trade_offs": ["trade-off 1", "trade-off 2"]
  }},
  "dimensiones_valor": {{
    "metrica_1": "descripcion cuantitativa",
    "metrica_2": "descripcion cuantitativa"
  }},
  "isomorfismos": ["patron equivalente 1", "patron equivalente 2", "patron equivalente 3"],
  "lentes": ["valor1", "valor2"],
  "funciones": ["valor1", "valor2"],
  "thinking_types": ["valor1", "valor2", "valor3"],
  "conceptual_modes": ["VALOR1", "VALOR2"],
  "lente_funcion_primary": "lente:funcion",
  "thinking_primary": "valor",
  "mode_primary": "VALOR"
}}
```

IMPORTANTE:
- Los valores de lentes, funciones, thinking_types y conceptual_modes DEBEN ser de las listas validas proporcionadas.
- lente_funcion_primary debe ser formato "lente:funcion" (ej: "salud:depurar")
- thinking_primary debe ser UN valor de thinking_types
- mode_primary debe ser UN valor de conceptual_modes
- La especificacion tecnica debe tener entre 2000 y 5000 caracteres
- Escribe en espanol tecnico"""


# ============================================================
# CORE LOGIC
# ============================================================

def fetch_patterns(conn, limit=None, offset=0):
    """Fetch all patterns from knowledge_base."""
    cur = conn.cursor()
    query = """
        SELECT id, scope, tipo, nivel, texto, metadata,
               lentes, funciones, thinking_types, conceptual_modes,
               lente_funcion_primary, thinking_primary, mode_primary
        FROM knowledge_base
        WHERE scope LIKE 'patrones:%%'
        ORDER BY id
    """
    if limit:
        query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    elif offset > 0:
        query += f" OFFSET {int(offset)}"

    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    return rows


def build_prompt(pattern: dict) -> str:
    """Build the enrichment prompt for a single pattern."""
    metadata = pattern.get("metadata") or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    conceptos = metadata.get("conceptos", [])
    conceptos_str = ", ".join(conceptos) if conceptos else "(no definidos)"

    return ENRICHMENT_PROMPT.format(
        scope=pattern["scope"],
        tipo=pattern["tipo"],
        nivel=pattern.get("nivel", ""),
        conceptos=conceptos_str,
        texto=pattern["texto"],
        lentes_validos=", ".join(VALID_LENTES),
        funciones_validas=", ".join(VALID_FUNCIONES),
        thinking_types_validos=", ".join(VALID_THINKING_TYPES),
        conceptual_modes_validos=", ".join(VALID_CONCEPTUAL_MODES),
    )


def parse_response(response_text: str) -> Tuple[str, dict]:
    """Parse Sonnet response into spec text and JSON metadata.

    Returns:
        (spec_text, metadata_dict)
    """
    # Find the JSON block
    json_match = re.search(r'```json\s*\n(.*?)\n\s*```', response_text, re.DOTALL)

    if json_match:
        json_str = json_match.group(1).strip()
        # The spec text is everything before the JSON block
        spec_text = response_text[:json_match.start()].strip()
        try:
            metadata = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"    WARNING: Failed to parse JSON block: {e}")
            print(f"    JSON snippet: {json_str[:200]}...")
            metadata = {}
    else:
        # No JSON block found — try to find any JSON-like structure
        print("    WARNING: No ```json block found in response")
        spec_text = response_text.strip()
        metadata = {}

    return spec_text, metadata


def validate_taxonomy(metadata: dict) -> dict:
    """Validate and filter taxonomy values to only valid options."""
    result = dict(metadata)

    # Validate lentes
    if "lentes" in result:
        result["lentes"] = [v for v in result["lentes"] if v in VALID_LENTES]

    # Validate funciones
    if "funciones" in result:
        result["funciones"] = [v for v in result["funciones"] if v in VALID_FUNCIONES]

    # Validate thinking_types
    if "thinking_types" in result:
        result["thinking_types"] = [v for v in result["thinking_types"] if v in VALID_THINKING_TYPES]

    # Validate conceptual_modes
    if "conceptual_modes" in result:
        result["conceptual_modes"] = [v for v in result["conceptual_modes"] if v in VALID_CONCEPTUAL_MODES]

    # Validate primary values
    if "lente_funcion_primary" in result:
        parts = result["lente_funcion_primary"].split(":")
        if len(parts) == 2:
            if parts[0] not in VALID_LENTES or parts[1] not in VALID_FUNCIONES:
                # Try to pick from what we have
                lentes = result.get("lentes", [])
                funciones = result.get("funciones", [])
                if lentes and funciones:
                    result["lente_funcion_primary"] = f"{lentes[0]}:{funciones[0]}"

    if "thinking_primary" in result:
        if result["thinking_primary"] not in VALID_THINKING_TYPES:
            types = result.get("thinking_types", [])
            result["thinking_primary"] = types[0] if types else None

    if "mode_primary" in result:
        if result["mode_primary"] not in VALID_CONCEPTUAL_MODES:
            modes = result.get("conceptual_modes", [])
            result["mode_primary"] = modes[0] if modes else None

    return result


def update_pattern(conn, pattern_id: int, spec_text: str, metadata: dict, dry_run: bool = False):
    """Update a pattern in the DB with enriched text and taxonomy."""
    if dry_run:
        print(f"    [DRY RUN] Would update pattern {pattern_id}")
        return

    cur = conn.cursor()

    # Build the metadata JSONB update — merge with existing
    cur.execute("SELECT metadata FROM knowledge_base WHERE id = %s", [pattern_id])
    row = cur.fetchone()
    existing_metadata = row[0] if row and row[0] else {}
    if isinstance(existing_metadata, str):
        existing_metadata = json.loads(existing_metadata)

    # Merge propiedades_algebraicas and dimensiones_valor into metadata
    if "propiedades_algebraicas" in metadata:
        existing_metadata["propiedades_algebraicas"] = metadata["propiedades_algebraicas"]
    if "dimensiones_valor" in metadata:
        existing_metadata["dimensiones_valor"] = metadata["dimensiones_valor"]
    if "isomorfismos" in metadata:
        existing_metadata["isomorfismos"] = metadata["isomorfismos"]

    # Extract taxonomy arrays
    lentes = metadata.get("lentes", [])
    funciones = metadata.get("funciones", [])
    thinking_types = metadata.get("thinking_types", [])
    conceptual_modes = metadata.get("conceptual_modes", [])
    lente_funcion_primary = metadata.get("lente_funcion_primary")
    thinking_primary = metadata.get("thinking_primary")
    mode_primary = metadata.get("mode_primary")

    cur.execute("""
        UPDATE knowledge_base SET
            texto = %s,
            metadata = %s,
            lentes = %s,
            funciones = %s,
            thinking_types = %s,
            conceptual_modes = %s,
            lente_funcion_primary = %s,
            thinking_primary = %s,
            mode_primary = %s,
            updated_at = NOW()
        WHERE id = %s
    """, [
        spec_text,
        Json(existing_metadata),
        lentes,
        funciones,
        thinking_types,
        conceptual_modes,
        lente_funcion_primary,
        thinking_primary,
        mode_primary,
        pattern_id,
    ])

    conn.commit()
    cur.close()


def enrich_pattern(client: anthropic.Anthropic, pattern: dict) -> Optional[Tuple[str, dict]]:
    """Call Sonnet to enrich a single pattern. Returns (spec_text, metadata) or None on failure."""
    prompt = build_prompt(pattern)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text
        spec_text, metadata = parse_response(response_text)
        metadata = validate_taxonomy(metadata)
        return spec_text, metadata
    except anthropic.APIError as e:
        print(f"    ERROR (API): {e}")
        return None
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {e}")
        return None


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Enrich patterns in knowledge_base with deep specs and taxonomy classification"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be updated without writing to DB")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only process first N patterns")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip first N patterns (for resuming)")
    args = parser.parse_args()

    print("=" * 60)
    print("ENRICH PATTERNS — Deep Specs + 4-Dimension Taxonomy")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Dry run: {args.dry_run}")
    print(f"  Limit: {args.limit or 'ALL'}")
    print(f"  Offset: {args.offset}")
    print("=" * 60)

    # Connect
    conn = get_db_connection()
    client = get_anthropic_client()

    # Fetch patterns
    patterns = fetch_patterns(conn, limit=args.limit, offset=args.offset)
    total = len(patterns)
    print(f"\n  Found {total} patterns to enrich\n")

    if total == 0:
        print("  Nothing to do.")
        conn.close()
        return

    # Process
    updated = 0
    failed = 0
    total_chars_before = 0
    total_chars_after = 0

    for i, pattern in enumerate(patterns, 1):
        pid = pattern["id"]
        scope = pattern["scope"]
        old_len = len(pattern["texto"]) if pattern["texto"] else 0
        total_chars_before += old_len

        # Skip already-enriched patterns (resumable)
        if old_len > 1000 and pattern.get("thinking_primary"):
            print(f"[{i}/{total}] id={pid} scope={scope} ({old_len} chars) -> SKIP (already enriched)")
            updated += 1
            total_chars_after += old_len
            continue

        print(f"[{i}/{total}] id={pid} scope={scope} ({old_len} chars)")

        result = enrich_pattern(client, pattern)
        if result is None:
            print(f"    FAILED — skipping")
            failed += 1
            time.sleep(1)
            continue

        spec_text, metadata = result
        new_len = len(spec_text)
        total_chars_after += new_len

        # Validate we got a meaningful enrichment
        if new_len < 500:
            print(f"    WARNING: Spec too short ({new_len} chars) — skipping")
            failed += 1
            time.sleep(1)
            continue

        taxonomy_summary = (
            f"lentes={metadata.get('lentes', [])}, "
            f"funciones={metadata.get('funciones', [])}, "
            f"thinking={metadata.get('thinking_primary', '?')}, "
            f"mode={metadata.get('mode_primary', '?')}"
        )

        print(f"    {old_len} -> {new_len} chars (+{new_len - old_len})")
        print(f"    Taxonomy: {taxonomy_summary}")

        update_pattern(conn, pid, spec_text, metadata, dry_run=args.dry_run)
        updated += 1

        # Rate limiting
        time.sleep(1)

    # Summary
    avg_increase = (total_chars_after - total_chars_before) / max(updated, 1)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total patterns:  {total}")
    print(f"  Updated:         {updated}")
    print(f"  Failed:          {failed}")
    print(f"  Skipped (limit): {total - updated - failed}")
    print(f"  Avg chars before: {total_chars_before / max(total, 1):.0f}")
    print(f"  Avg chars after:  {total_chars_after / max(updated, 1):.0f}")
    print(f"  Avg increase:    +{avg_increase:.0f} chars")
    print(f"  Finished: {datetime.now().isoformat()}")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
