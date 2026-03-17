"""B3 — Reorganizar Matriz en DB por 3L x 7F.

Hace de las 21 celdas (3 Lentes x 7 Funciones) entidades de primer nivel
con FK, contadores materializados, y vistas para visualizacion.

Migracion aditiva — zero datos perdidos. Todos los DDL son idempotentes
(IF NOT EXISTS / ON CONFLICT DO NOTHING).

Pasos:
  1. CREATE TABLE celdas_matriz
  2. Seed 21 celdas
  3. FK datapoints_efectividad
  4. FK preguntas_matriz
  5. FK efectos_matriz
  6. refresh_celdas_stats() function
  7. 3 vistas: matriz_por_lente, matriz_por_funcion, matriz_completa

Ejecutar: python3 migrations/b3_celdas_matriz.py
"""

import os
import sys

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


LENTES = ['Salud', 'Sentido', 'Continuidad']
FUNCIONES = ['Conservar', 'Captar', 'Depurar', 'Distribuir', 'Frontera', 'Adaptar', 'Replicar']


def step1_create_table(conn):
    """CREATE TABLE celdas_matriz."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS celdas_matriz (
                id              TEXT PRIMARY KEY,
                lente           TEXT NOT NULL CHECK (lente IN ('Salud', 'Sentido', 'Continuidad')),
                funcion         TEXT NOT NULL CHECK (funcion IN ('Conservar', 'Captar', 'Depurar', 'Distribuir', 'Frontera', 'Adaptar', 'Replicar')),
                grado_actual    REAL NOT NULL DEFAULT 0.0,
                grado_objetivo  REAL NOT NULL DEFAULT 1.0,
                gap             REAL GENERATED ALWAYS AS (grado_objetivo - grado_actual) STORED,
                n_preguntas     INTEGER NOT NULL DEFAULT 0,
                n_datapoints    INTEGER NOT NULL DEFAULT 0,
                tasa_media      REAL NOT NULL DEFAULT 0.0,
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
    conn.commit()
    print("  1. CREATE TABLE celdas_matriz: OK")


def step2_seed_celdas(conn):
    """Seed 21 celdas (3 lentes x 7 funciones)."""
    count = 0
    with conn.cursor() as cur:
        for funcion in FUNCIONES:
            for lente in LENTES:
                celda_id = f"{funcion}x{lente}"
                cur.execute("""
                    INSERT INTO celdas_matriz (id, lente, funcion)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, [celda_id, lente, funcion])
                count += 1
    conn.commit()
    print(f"  2. Seed {count} celdas: OK")


def step3_fk_datapoints(conn):
    """FK datapoints_efectividad -> celdas_matriz."""
    with conn.cursor() as cur:
        # Fix orphan celda_objetivo values that don't match any celda
        cur.execute("""
            UPDATE datapoints_efectividad
            SET celda_objetivo = NULL
            WHERE celda_objetivo IS NOT NULL
              AND celda_objetivo != ''
              AND celda_objetivo NOT IN (SELECT id FROM celdas_matriz)
        """)
        orphans = cur.rowcount
        if orphans > 0:
            print(f"    Fixed {orphans} orphan datapoints (celda_objetivo -> NULL)")

        # Add FK constraint if not exists
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'fk_datapoints_celda'
                      AND table_name = 'datapoints_efectividad'
                ) THEN
                    ALTER TABLE datapoints_efectividad
                        ADD CONSTRAINT fk_datapoints_celda
                        FOREIGN KEY (celda_objetivo) REFERENCES celdas_matriz(id)
                        ON DELETE SET NULL;
                END IF;
            END $$
        """)
    conn.commit()
    print("  3. FK datapoints_efectividad -> celdas_matriz: OK")


def step4_fk_preguntas(conn):
    """FK preguntas_matriz -> celdas_matriz."""
    with conn.cursor() as cur:
        # Add celda_id column if not exists
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'preguntas_matriz' AND column_name = 'celda_id'
                ) THEN
                    ALTER TABLE preguntas_matriz ADD COLUMN celda_id TEXT;
                END IF;
            END $$
        """)

        # Populate celda_id from funcion + lente
        cur.execute("""
            UPDATE preguntas_matriz
            SET celda_id = funcion || 'x' || lente
            WHERE celda_id IS NULL
              AND funcion IS NOT NULL AND funcion != ''
              AND lente IS NOT NULL AND lente != ''
        """)
        updated = cur.rowcount
        if updated > 0:
            print(f"    Updated {updated} preguntas with celda_id")

        # Fix orphans
        cur.execute("""
            UPDATE preguntas_matriz
            SET celda_id = NULL
            WHERE celda_id IS NOT NULL
              AND celda_id NOT IN (SELECT id FROM celdas_matriz)
        """)
        orphans = cur.rowcount
        if orphans > 0:
            print(f"    Fixed {orphans} orphan preguntas (celda_id -> NULL)")

        # Add FK constraint if not exists
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'fk_preguntas_celda'
                      AND table_name = 'preguntas_matriz'
                ) THEN
                    ALTER TABLE preguntas_matriz
                        ADD CONSTRAINT fk_preguntas_celda
                        FOREIGN KEY (celda_id) REFERENCES celdas_matriz(id)
                        ON DELETE SET NULL;
                END IF;
            END $$
        """)
    conn.commit()
    print("  4. FK preguntas_matriz -> celdas_matriz: OK")


def step5_fk_efectos(conn):
    """FK efectos_matriz -> celdas_matriz."""
    with conn.cursor() as cur:
        # Add celda_id column if not exists
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'efectos_matriz' AND column_name = 'celda_id'
                ) THEN
                    ALTER TABLE efectos_matriz ADD COLUMN celda_id TEXT;
                END IF;
            END $$
        """)

        # Populate celda_id from funcion + lente
        cur.execute("""
            UPDATE efectos_matriz
            SET celda_id = funcion || 'x' || lente
            WHERE celda_id IS NULL
              AND funcion IS NOT NULL AND funcion != ''
              AND lente IS NOT NULL AND lente != ''
        """)
        updated = cur.rowcount
        if updated > 0:
            print(f"    Updated {updated} efectos with celda_id")

        # Fix orphans
        cur.execute("""
            UPDATE efectos_matriz
            SET celda_id = NULL
            WHERE celda_id IS NOT NULL
              AND celda_id NOT IN (SELECT id FROM celdas_matriz)
        """)
        orphans = cur.rowcount
        if orphans > 0:
            print(f"    Fixed {orphans} orphan efectos (celda_id -> NULL)")

        # Add FK constraint if not exists
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'fk_efectos_celda'
                      AND table_name = 'efectos_matriz'
                ) THEN
                    ALTER TABLE efectos_matriz
                        ADD CONSTRAINT fk_efectos_celda
                        FOREIGN KEY (celda_id) REFERENCES celdas_matriz(id)
                        ON DELETE SET NULL;
                END IF;
            END $$
        """)
    conn.commit()
    print("  5. FK efectos_matriz -> celdas_matriz: OK")


def step6_refresh_function(conn):
    """CREATE FUNCTION refresh_celdas_stats() + execute."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE OR REPLACE FUNCTION refresh_celdas_stats()
            RETURNS void AS $$
            BEGIN
                UPDATE celdas_matriz cm SET
                    n_preguntas = COALESCE(pq.cnt, 0),
                    n_datapoints = COALESCE(dp.cnt, 0),
                    tasa_media = COALESCE(dp.tasa, 0.0),
                    grado_actual = CASE
                        WHEN COALESCE(dp.cnt, 0) > 0
                        THEN LEAST(1.0, 1.0 - COALESCE(dp.avg_gap, 0.0))
                        ELSE 0.0
                    END,
                    updated_at = NOW()
                FROM celdas_matriz base
                LEFT JOIN (
                    SELECT celda_id, COUNT(*) AS cnt
                    FROM preguntas_matriz
                    WHERE celda_id IS NOT NULL
                    GROUP BY celda_id
                ) pq ON pq.celda_id = base.id
                LEFT JOIN (
                    SELECT celda_objetivo,
                           COUNT(*) AS cnt,
                           AVG(tasa_cierre) AS tasa,
                           AVG(gap_post) AS avg_gap
                    FROM datapoints_efectividad
                    WHERE celda_objetivo IS NOT NULL
                    GROUP BY celda_objetivo
                ) dp ON dp.celda_objetivo = base.id
                WHERE cm.id = base.id;
            END;
            $$ LANGUAGE plpgsql
        """)

        # Execute the refresh
        cur.execute("SELECT refresh_celdas_stats()")
    conn.commit()
    print("  6. refresh_celdas_stats(): OK")


def step7_views(conn):
    """Create 3 views: matriz_por_lente, matriz_por_funcion, matriz_completa."""
    with conn.cursor() as cur:
        # View 1: agregado por lente
        cur.execute("""
            CREATE OR REPLACE VIEW matriz_por_lente AS
            SELECT
                lente,
                COUNT(*) AS n_celdas,
                SUM(n_preguntas) AS total_preguntas,
                SUM(n_datapoints) AS total_datapoints,
                ROUND(AVG(grado_actual)::numeric, 4) AS grado_medio,
                ROUND(AVG(gap)::numeric, 4) AS gap_medio,
                ROUND(AVG(tasa_media)::numeric, 4) AS tasa_media
            FROM celdas_matriz
            GROUP BY lente
            ORDER BY lente
        """)

        # View 2: agregado por funcion
        cur.execute("""
            CREATE OR REPLACE VIEW matriz_por_funcion AS
            SELECT
                funcion,
                COUNT(*) AS n_celdas,
                SUM(n_preguntas) AS total_preguntas,
                SUM(n_datapoints) AS total_datapoints,
                ROUND(AVG(grado_actual)::numeric, 4) AS grado_medio,
                ROUND(AVG(gap)::numeric, 4) AS gap_medio,
                ROUND(AVG(tasa_media)::numeric, 4) AS tasa_media
            FROM celdas_matriz
            GROUP BY funcion
            ORDER BY funcion
        """)

        # View 3: matriz completa con campo color_termometro
        cur.execute("""
            CREATE OR REPLACE VIEW matriz_completa AS
            SELECT
                id, lente, funcion,
                grado_actual, grado_objetivo, gap,
                n_preguntas, n_datapoints, tasa_media,
                updated_at,
                CASE
                    WHEN gap >= 0.6 THEN 'rojo'
                    WHEN gap >= 0.3 THEN 'naranja'
                    WHEN gap >= 0.1 THEN 'amarillo'
                    ELSE 'verde'
                END AS color_termometro
            FROM celdas_matriz
            ORDER BY funcion, lente
        """)
    conn.commit()
    print("  7. Views (matriz_por_lente, matriz_por_funcion, matriz_completa): OK")


def main():
    """Ejecutar migracion B3 completa."""
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 no disponible. Instalar: pip install psycopg2-binary")
        sys.exit(1)

    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        db_url = "postgresql://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind"

    print("Conectando a DB...")
    conn = psycopg2.connect(db_url, connect_timeout=10)
    print("OK\n")

    try:
        print("=== B3: Migracion celdas_matriz (3L x 7F) ===\n")

        step1_create_table(conn)
        step2_seed_celdas(conn)
        step3_fk_datapoints(conn)
        step4_fk_preguntas(conn)
        step5_fk_efectos(conn)
        step6_refresh_function(conn)
        step7_views(conn)

        # Verificacion
        print("\n=== VERIFICACION ===")
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM celdas_matriz")
            print(f"  celdas_matriz: {cur.fetchone()[0]} celdas")

            cur.execute("SELECT COUNT(*) FROM celdas_matriz WHERE n_datapoints > 0")
            print(f"  celdas con datos: {cur.fetchone()[0]}")

            cur.execute("SELECT * FROM matriz_por_lente")
            print("\n  Por lente:")
            for row in cur.fetchall():
                print(f"    {row[0]:15s} celdas={row[1]} preguntas={row[2]} datapoints={row[3]} gap_medio={row[5]}")

            cur.execute("SELECT * FROM matriz_por_funcion")
            print("\n  Por funcion:")
            for row in cur.fetchall():
                print(f"    {row[0]:15s} celdas={row[1]} preguntas={row[2]} datapoints={row[3]} gap_medio={row[5]}")

            cur.execute("SELECT id, gap, color_termometro FROM matriz_completa ORDER BY gap DESC LIMIT 5")
            print("\n  Top 5 gaps:")
            for row in cur.fetchall():
                print(f"    {row[0]:25s} gap={row[1]:.4f} color={row[2]}")

        print("\nMigracion B3 completada.")

    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
