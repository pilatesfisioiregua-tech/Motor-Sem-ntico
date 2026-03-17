"""Seed datos de produccion validados (Experimento 4) + datapoints sinteticos.

Tablas que pobla:
  1. config_modelos — mesa de produccion (6 modelos)
  2. config_enjambre — 5 tiers
  3. datapoints_efectividad — 20 datapoints sinteticos variados

Ejecutar: python3 migrations/seed_exp4_data.py
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone, timedelta

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def seed_config_modelos(conn):
    """Seed mesa de produccion validada (Exp 4)."""
    modelos = [
        ('ejecutor', 'deepseek/deepseek-chat-v3-0324', 'openrouter', 2, 5, 0.27, 1.10, 'V3.2 chat — 89.5% cobertura individual'),
        ('ejecutor', 'deepseek/deepseek-chat', 'openrouter', 2, 5, 0.27, 1.10, 'V3.1 — segundo ejecutor'),
        ('razonador', 'deepseek/deepseek-reasoner', 'openrouter', 3, 5, 0.55, 2.19, 'R1 — razonamiento profundo'),
        ('sintetizador', 'deepcogito/cogito-v2.1-671b', 'openrouter', 3, 5, 0.50, 2.00, 'Cogito — sintesis multi-perspectiva'),
        ('pizarra', 'openai/gpt-4o-mini', 'openrouter', 4, 5, 0.60, 2.40, 'GPT-4o-mini — pizarra multi-ronda'),
        ('fontaneria', 'xiaomi/mimo-v2-flash', 'openrouter', 1, 3, 0.10, 0.40, 'MiMo — tareas rapidas/baratas'),
    ]

    with conn.cursor() as cur:
        for rol, modelo, provider, tier_min, tier_max, cost_in, cost_out, notas in modelos:
            cur.execute("""
                INSERT INTO config_modelos (rol, modelo, provider, tier_min, tier_max,
                                            coste_input_per_m, coste_output_per_m, activo, notas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true, %s)
                ON CONFLICT DO NOTHING
            """, [rol, modelo, provider, tier_min, tier_max, cost_in, cost_out, notas])
    conn.commit()
    print(f"  config_modelos: {len(modelos)} modelos insertados")


def seed_config_enjambre(conn):
    """Seed 5 tiers de enjambre (Maestro v3 §4.4)."""
    tiers = [
        (1, '{}', 'lookup', 0, None, False, 0.00),
        (2, '{deepseek/deepseek-chat-v3-0324}', 'individual', 1, None, False, 0.03),
        (3, '{deepseek/deepseek-chat-v3-0324,deepseek/deepseek-chat,deepseek/deepseek-reasoner}', 'mesa', 1, 'cogito', False, 0.30),
        (4, '{openai/gpt-4o-mini,deepseek/deepseek-reasoner,qwen/qwen3-235b-a22b,moonshotai/kimi-k2}', 'pizarra', 5, 'cogito', True, 2.00),
        (5, '{all}', 'pizarra', 10, 'cogito', True, 10.00),
    ]

    with conn.cursor() as cur:
        for tier, modelos, mecanismo, rondas, sintetizador, evaluador, coste in tiers:
            cur.execute("""
                INSERT INTO config_enjambre (tier, modelos, mecanismo, rondas,
                                             sintetizador, evaluador_externo, coste_estimado)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, [tier, modelos, mecanismo, rondas, sintetizador, evaluador, coste])
    conn.commit()
    print(f"  config_enjambre: {len(tiers)} tiers insertados")


def seed_datapoints_sinteticos(conn):
    """Seed 20 datapoints sinteticos variados para que el Gestor practique.

    4 tipos de señales:
    - 5 convergentes (D < 0): gap decreciente
    - 5 cronicos (I alto): gap constante alto
    - 5 oscilantes (D ruidoso): gap va y viene
    - 5 cerrados (gap ~ 0): celda resuelta

    NOTA: gap_cerrado y tasa_cierre son GENERATED ALWAYS columns — no se insertan.
    """
    import random
    random.seed(42)

    celdas = ['ConservarxSalud', 'CaptarxSentido', 'DepurarxContinuidad',
              'FronteraxSalud', 'AdaptarxSentido']
    preguntas = ['INT-01-Q001', 'INT-08-Q001', 'INT-16-Q001',
                 'INT-14-Q001', 'INT-06-Q001']
    modelo = 'deepseek/deepseek-chat-v3-0324'
    now = datetime.now(timezone.utc)

    datapoints = []

    # Tipo 1: Convergentes (gap decreciente)
    for i in range(5):
        gap_post = 0.8 - (i * 0.12)
        datapoints.append({
            'pregunta_id': preguntas[0],
            'celda': celdas[0],
            'gap_pre': gap_post + 0.12,
            'gap_post': gap_post,
        })

    # Tipo 2: Cronicos (gap constante alto)
    for i in range(5):
        gap = 0.85 + random.uniform(-0.03, 0.03)
        datapoints.append({
            'pregunta_id': preguntas[1],
            'celda': celdas[1],
            'gap_pre': 0.9,
            'gap_post': gap,
        })

    # Tipo 3: Oscilantes (gap va y viene)
    for i in range(5):
        gap = 0.5 + (0.2 * (1 if i % 2 == 0 else -1)) + random.uniform(-0.05, 0.05)
        datapoints.append({
            'pregunta_id': preguntas[2],
            'celda': celdas[2],
            'gap_pre': 0.6,
            'gap_post': gap,
        })

    # Tipo 4: Cerrados (gap ~ 0)
    for i in range(5):
        gap = random.uniform(0.0, 0.05)
        datapoints.append({
            'pregunta_id': preguntas[3],
            'celda': celdas[3],
            'gap_pre': 0.3,
            'gap_post': gap,
        })

    with conn.cursor() as cur:
        for i, dp in enumerate(datapoints):
            ts = now - timedelta(hours=len(datapoints) - i)
            cur.execute("""
                INSERT INTO datapoints_efectividad
                  (pregunta_id, modelo, caso_id, consumidor, celda_objetivo,
                   gap_pre, gap_post, operacion, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [dp['pregunta_id'], modelo, f"seed-{i:03d}", 'seed_exp4',
                  dp['celda'], dp['gap_pre'], dp['gap_post'],
                  'individual', ts])

    conn.commit()
    print(f"  datapoints_efectividad: {len(datapoints)} datapoints insertados")
    print(f"    - 5 convergentes (D<0), 5 cronicos (I alto), 5 oscilantes, 5 cerrados")


def main():
    """Ejecutar seed completo."""
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 no disponible. Instalar: pip install psycopg2-binary")
        sys.exit(1)

    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        db_url = "postgresql://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind"

    print(f"Conectando a DB...")
    conn = psycopg2.connect(db_url, connect_timeout=10)
    print(f"OK")

    try:
        print("\n1. Seed config_modelos:")
        seed_config_modelos(conn)

        print("\n2. Seed config_enjambre:")
        seed_config_enjambre(conn)

        print("\n3. Seed datapoints sinteticos:")
        seed_datapoints_sinteticos(conn)

        # Verificacion
        print("\n=== VERIFICACION ===")
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM config_modelos WHERE activo = true")
            print(f"  config_modelos activos: {cur.fetchone()[0]}")

            cur.execute("SELECT COUNT(*) FROM config_enjambre")
            print(f"  config_enjambre tiers: {cur.fetchone()[0]}")

            cur.execute("SELECT COUNT(*) FROM datapoints_efectividad")
            print(f"  datapoints_efectividad: {cur.fetchone()[0]}")

            cur.execute("""
                SELECT celda_objetivo, COUNT(*),
                       ROUND(AVG(tasa_cierre)::numeric, 4)
                FROM datapoints_efectividad
                WHERE consumidor = 'seed_exp4'
                GROUP BY celda_objetivo
            """)
            print(f"\n  Distribucion por celda:")
            for row in cur.fetchall():
                print(f"    {row[0]:25s} n={row[1]} tasa_media={row[2]}")

        print("\nSeed completado.")

    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
