"""Fix 004: Reset tasa_cierre_media inflada a 1.0 en programas pre-calibracion.

Root cause: 10 programas llevan tasa_cierre_media=1.0 de datos pre-calibracion.
La tasa calibrada real es ~0.52. Reseteamos a NULL y n_ejecuciones=0 para que
_actualizar_programa_post_ejecucion() recalcule desde cero con datos reales.
"""

import os
import sys
import psycopg2

def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Try loading from .env
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('DATABASE_URL='):
                        database_url = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break

    if not database_url:
        print("ERROR: DATABASE_URL not found in environment or .env")
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            # Check current state
            cur.execute("""
                SELECT id, consumidor, tasa_cierre_media, n_ejecuciones
                FROM programas_compilados
                WHERE activo = true AND tasa_cierre_media IS NOT NULL
            """)
            rows = cur.fetchall()
            print(f"Programas activos con tasa_cierre_media: {len(rows)}")
            for r in rows:
                print(f"  id={r[0]} consumidor={r[1]} tasa={r[2]} n_ejec={r[3]}")

            # Reset
            cur.execute("""
                UPDATE programas_compilados
                SET tasa_cierre_media = NULL, n_ejecuciones = 0
                WHERE activo = true
            """)
            updated = cur.rowcount
            conn.commit()
            print(f"\nReset {updated} programas: tasa_cierre_media=NULL, n_ejecuciones=0")

    finally:
        conn.close()

if __name__ == '__main__':
    main()
