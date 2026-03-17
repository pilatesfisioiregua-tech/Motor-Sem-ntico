"""Migration 003: Neural Index — tsvector + hybrid_search + Hebbian activation.

Adds full-text search to knowledge_base and creates the hybrid_search() SQL function
that combines text ranking + scope filtering + Hebbian graph boost.

Run: python3 migrations/003_neural_index.py
Requires: fly proxy 15432:5433 -a motor-semantico-db
"""

import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 15432,
    "dbname": "omni_mind",
    "user": "chief_os_omni",
    "password": "77qJGeKtMTgCYhz",
}


def run_migration():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    print("=== Migration 003: Neural Index ===\n")

    # ── Step 1: Add tsvector column ──────────────────────────────────────
    print("[1/5] Adding tsv column to knowledge_base...")
    cur.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'knowledge_base' AND column_name = 'tsv'
            ) THEN
                ALTER TABLE knowledge_base ADD COLUMN tsv tsvector;
            END IF;
        END $$;
    """)
    conn.commit()
    print("  ✓ tsv column ready")

    # ── Step 2: Populate tsvector from existing data ─────────────────────
    print("[2/5] Populating tsv from texto + tipo + scope...")
    cur.execute("""
        UPDATE knowledge_base
        SET tsv = to_tsvector('spanish',
            COALESCE(tipo, '') || ' ' ||
            COALESCE(scope, '') || ' ' ||
            COALESCE(LEFT(texto, 5000), '')
        )
        WHERE tsv IS NULL
    """)
    updated = cur.rowcount
    conn.commit()
    print(f"  ✓ {updated} rows populated")

    # ── Step 3: GIN index on tsvector ────────────────────────────────────
    print("[3/5] Creating GIN index on tsv...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_kb_tsv
        ON knowledge_base USING gin(tsv)
    """)
    conn.commit()
    print("  ✓ GIN index created")

    # ── Step 4: Auto-update trigger ──────────────────────────────────────
    print("[4/5] Creating auto-update trigger...")
    cur.execute("""
        CREATE OR REPLACE FUNCTION kb_tsv_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.tsv := to_tsvector('spanish',
                COALESCE(NEW.tipo, '') || ' ' ||
                COALESCE(NEW.scope, '') || ' ' ||
                COALESCE(LEFT(NEW.texto, 5000), '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trg_kb_tsv'
            ) THEN
                CREATE TRIGGER trg_kb_tsv
                BEFORE INSERT OR UPDATE OF texto, tipo, scope
                ON knowledge_base
                FOR EACH ROW EXECUTE FUNCTION kb_tsv_trigger();
            END IF;
        END $$;
    """)
    conn.commit()
    print("  ✓ Trigger created")

    # ── Step 5: hybrid_search() SQL function ─────────────────────────────
    # AND→OR fallback + scope supports both ':' and '/' separators
    print("[5/5] Creating hybrid_search() function...")
    cur.execute("""
        CREATE OR REPLACE FUNCTION hybrid_search(
            search_query text,
            scope_filter text DEFAULT NULL,
            session_id_param text DEFAULT NULL,
            result_limit int DEFAULT 10
        )
        RETURNS TABLE (
            id int,
            scope text,
            tipo text,
            texto text,
            fts_rank real,
            hebbian_boost float,
            combined_score float
        )
        LANGUAGE plpgsql STABLE AS $$
        DECLARE
            tsq_and tsquery;
            tsq_or tsquery;
            tsq_final tsquery;
            and_count int;
        BEGIN
            -- Try strict AND match first
            tsq_and := plainto_tsquery('spanish', search_query);

            -- Build OR query: split on spaces, join with |
            tsq_or := to_tsquery('spanish',
                array_to_string(
                    array(
                        SELECT lexeme FROM unnest(
                            tsvector_to_array(to_tsvector('spanish', search_query))
                        ) AS lexeme
                        WHERE length(lexeme) > 1
                    ),
                    ' | '
                )
            );

            -- Check if AND query returns results
            SELECT count(*) INTO and_count
            FROM knowledge_base kb
            WHERE kb.tsv @@ tsq_and
              AND (scope_filter IS NULL OR kb.scope = scope_filter
                   OR kb.scope LIKE scope_filter || ':%'
                   OR kb.scope LIKE scope_filter || '/%')
            LIMIT 1;

            -- Use AND if it has results, otherwise OR for broader recall
            IF and_count > 0 THEN
                tsq_final := tsq_and;
            ELSE
                tsq_final := tsq_or;
            END IF;

            RETURN QUERY
            WITH fts AS (
                SELECT
                    kb.id, kb.scope, kb.tipo, kb.texto,
                    ts_rank_cd(kb.tsv, tsq_final, 32) AS fts_rank
                FROM knowledge_base kb
                WHERE kb.tsv @@ tsq_final
                  AND (scope_filter IS NULL OR kb.scope = scope_filter
                       OR kb.scope LIKE scope_filter || ':%'
                       OR kb.scope LIKE scope_filter || '/%')
                ORDER BY fts_rank DESC
                LIMIT result_limit * 3
            ),
            ilike_fallback AS (
                SELECT
                    kb.id, kb.scope, kb.tipo, kb.texto,
                    0.1::real AS fts_rank
                FROM knowledge_base kb
                WHERE NOT EXISTS (SELECT 1 FROM fts)
                  AND (kb.texto ILIKE '%' || search_query || '%'
                       OR kb.tipo ILIKE '%' || search_query || '%')
                  AND (scope_filter IS NULL OR kb.scope = scope_filter
                       OR kb.scope LIKE scope_filter || ':%'
                       OR kb.scope LIKE scope_filter || '/%')
                LIMIT result_limit * 3
            ),
            combined AS (
                SELECT * FROM fts
                UNION ALL
                SELECT * FROM ilike_fallback
            ),
            with_hebbian AS (
                SELECT
                    c.id, c.scope, c.tipo, c.texto, c.fts_rank,
                    COALESCE(heb.total_strength, 0.0) AS hebbian_boost,
                    c.fts_rank::float + COALESCE(heb.total_strength, 0.0) * 0.3 AS combined_score
                FROM combined c
                LEFT JOIN LATERAL (
                    SELECT SUM(kc.strength) AS total_strength
                    FROM knowledge_connections kc
                    WHERE (kc.source_id = c.id OR kc.target_id = c.id)
                      AND session_id_param IS NOT NULL
                      AND (kc.source_id IN (
                              SELECT kal.knowledge_id FROM knowledge_access_log kal
                              WHERE kal.session_id = session_id_param
                              AND kal.created_at > NOW() - INTERVAL '1 hour'
                           )
                           OR kc.target_id IN (
                              SELECT kal.knowledge_id FROM knowledge_access_log kal
                              WHERE kal.session_id = session_id_param
                              AND kal.created_at > NOW() - INTERVAL '1 hour'
                           ))
                ) heb ON true
            )
            SELECT wh.id, wh.scope, wh.tipo, wh.texto,
                   wh.fts_rank, wh.hebbian_boost, wh.combined_score
            FROM with_hebbian wh
            ORDER BY wh.combined_score DESC
            LIMIT result_limit;
        END;
        $$;
    """)
    conn.commit()
    print("  ✓ hybrid_search() function created")

    # ── Verify ───────────────────────────────────────────────────────────
    print("\n=== Verification ===")

    # Test hybrid_search
    cur.execute("SELECT id, scope, tipo, fts_rank, combined_score FROM hybrid_search('database indexing', NULL, NULL, 5)")
    rows = cur.fetchall()
    print(f"\nhybrid_search('database indexing'): {len(rows)} results")
    for r in rows:
        print(f"  [{r[0]}] {r[1]}/{r[2]} rank={r[3]:.3f} score={r[4]:.3f}")

    cur.execute("SELECT id, scope, tipo, fts_rank, combined_score FROM hybrid_search('maestro sistema cognitivo', NULL, NULL, 5)")
    rows = cur.fetchall()
    print(f"\nhybrid_search('maestro sistema cognitivo'): {len(rows)} results")
    for r in rows:
        print(f"  [{r[0]}] {r[1]}/{r[2]} rank={r[3]:.3f} score={r[4]:.3f}")

    cur.execute("SELECT id, scope, tipo, fts_rank, combined_score FROM hybrid_search('PostgreSQL', 'patrones', NULL, 5)")
    rows = cur.fetchall()
    print(f"\nhybrid_search('PostgreSQL', scope='patrones'): {len(rows)} results")
    for r in rows:
        print(f"  [{r[0]}] {r[1]}/{r[2]} rank={r[3]:.3f} score={r[4]:.3f}")

    # Stats
    cur.execute("SELECT COUNT(*) FROM knowledge_base WHERE tsv IS NOT NULL")
    print(f"\nEntries with tsvector: {cur.fetchone()[0]}")

    cur.close()
    conn.close()
    print("\n=== Migration 003 complete ===")


if __name__ == "__main__":
    run_migration()
