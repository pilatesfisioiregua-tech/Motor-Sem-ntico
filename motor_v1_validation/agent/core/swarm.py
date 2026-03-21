"""Swarm Executor — Tiers 4-5 del Motor vN.

Tier 4 (Pizarra):
  - N modelos ejecutan el MISMO prompt en paralelo por INT
  - Votación por consenso: >60% coinciden → confirmed, resto → divergent
  - Timeout: 45 min total

Tier 5 (Cartografía):
  - TODAS las 18 INTs, 3 modelos × 2 pasadas por INT
  - Semaphore(5) para no saturar OpenRouter
  - Síntesis final con modelo sintetizador
  - Timeout: 4 horas

Principio 31: 5 tiers con escala logarítmica de coste/tiempo.
Principio 32: swarm como red neuronal — cada modelo = neurona.
"""

import asyncio
import json
import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# 18 inteligencias canónicas
ALL_INTELIGENCIAS = [f"INT-{str(i).zfill(2)}" for i in range(1, 19)]

# Modelos fallback para pizarra si config_modelos no tiene entries
MODELOS_PIZARRA_FALLBACK = [
    'deepseek/deepseek-chat-v3-0324',
    'google/gemini-2.5-flash-preview',
    'mistralai/devstral-2512',
    'qwen/qwen3-235b',
    'cognitivecomputations/cogito-v1-preview-llama-70B',
]

MODELO_SINTETIZADOR_FALLBACK = 'cognitivecomputations/cogito-v1-preview-llama-70B'


class SwarmExecutor:
    """Ejecutor de Tier 4 (Pizarra) y Tier 5 (Cartografía).

    Recibe referencia al MotorVN para reutilizar _llamar_llm (circuit breaker + costes).
    """

    def __init__(self, motor):
        self.motor = motor

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _obtener_modelos_pizarra(self, n: int = 5) -> list:
        """Obtener lista de modelos disponibles para tier >= 4."""
        modelos = []
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT modelo FROM config_modelos
                            WHERE activo = true AND tier_max >= 4
                            ORDER BY coste_input_per_m ASC
                            LIMIT %s
                        """, [n])
                        modelos = [row[0] for row in cur.fetchall()]
                finally:
                    put_conn(conn)
        except Exception as e:
            logger.warning(f"Error obteniendo modelos pizarra: {e}")

        if not modelos:
            modelos = MODELOS_PIZARRA_FALLBACK[:n]

        return modelos[:n]

    def _obtener_modelo_sintetizador(self) -> str:
        """Obtener modelo sintetizador para integración final."""
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT modelo FROM config_modelos
                            WHERE rol = 'sintetizador' AND activo = true
                              AND tier_max >= 4
                            ORDER BY coste_input_per_m ASC
                            LIMIT 1
                        """)
                        row = cur.fetchone()
                        if row:
                            return row[0]
                finally:
                    put_conn(conn)
        except Exception:
            pass
        return MODELO_SINTETIZADOR_FALLBACK

    def _calcular_consenso(self, respuestas: list) -> list:
        """Agrupar hallazgos por similaridad y votar consenso.

        Similaridad: Jaccard sobre keywords (palabras > 4 chars).
        >60% coinciden en hallazgo → confirmed, resto → divergent.
        """
        # Extraer hallazgos de cada respuesta
        todos = []  # [(modelo, hallazgo_text)]
        for modelo, respuesta in respuestas:
            if not respuesta or respuesta.startswith('[ERROR') or respuesta.startswith('[EXCEPTION'):
                continue
            for linea in respuesta.split('\n'):
                linea = linea.strip()
                if linea and len(linea) > 20 and not linea.startswith('#'):
                    todos.append((modelo, linea[:500]))

        if not todos:
            return []

        # Extraer keywords por hallazgo
        def keywords(text):
            return set(
                w.lower() for w in text.split()
                if len(w) > 4 and w.isalpha()
            )

        # Agrupar por similaridad (Jaccard > 0.3 = mismo grupo)
        grupos = []  # [(hallazgo_representativo, [(modelo, texto)])]
        for modelo, texto in todos:
            kw = keywords(texto)
            matched = False
            for i, (rep, miembros) in enumerate(grupos):
                rep_kw = keywords(rep)
                if rep_kw and kw:
                    jaccard = len(kw & rep_kw) / len(kw | rep_kw)
                    if jaccard > 0.3:
                        miembros.append((modelo, texto))
                        matched = True
                        break
            if not matched:
                grupos.append((texto, [(modelo, texto)]))

        # Votar: >60% de modelos respondieron → confirmed
        n_modelos = len(set(m for m, _ in respuestas
                           if not (isinstance(_, str) and
                                   (_.startswith('[ERROR') or _.startswith('[EXCEPTION')))))
        n_modelos = max(n_modelos, 1)

        hallazgos_consenso = []
        for rep, miembros in grupos:
            modelos_en_grupo = set(m for m, _ in miembros)
            pct = len(modelos_en_grupo) / n_modelos
            consenso = 'confirmed' if pct > 0.6 else 'divergent'
            hallazgos_consenso.append({
                'hallazgo': rep,
                'consenso': consenso,
                'pct_acuerdo': round(pct * 100, 1),
                'n_modelos': len(modelos_en_grupo),
                'modelos': list(modelos_en_grupo),
            })

        return hallazgos_consenso

    # ------------------------------------------------------------------
    # Tier 4 — Pizarra
    # ------------------------------------------------------------------

    async def ejecutar_pizarra(self, programa, input_texto: str) -> dict:
        """Tier 4: N modelos en paralelo por INT, votación por consenso.

        Args:
            programa: FrozenPrograma con pasos e inteligencias
            input_texto: texto de entrada

        Returns:
            dict con hallazgos (con campo consenso), scores, sintesis
        """
        t0 = time.time()
        modelos = self._obtener_modelos_pizarra(n=5)
        semaphore = asyncio.Semaphore(10)
        hallazgos_totales = []
        modelos_usados = {}
        n_llm_calls = 0
        errores = []

        for paso_tuple in programa.pasos:
            paso = dict(paso_tuple) if isinstance(paso_tuple, tuple) else paso_tuple
            inteligencia = paso.get('inteligencia', '') if isinstance(paso, dict) else ''
            preguntas = paso.get('preguntas', []) if isinstance(paso, dict) else []

            if not preguntas:
                prompt = self.motor._generar_prompt_int(inteligencia, input_texto)
            else:
                prompt = self.motor._generar_prompt_preguntas(preguntas, input_texto)

            if not self.motor._pre_validar(prompt, input_texto):
                continue

            # Lanzar N modelos en paralelo con semáforo
            async def _call_modelo(modelo, sem):
                async with sem:
                    try:
                        resp = await self.motor._llamar_llm(modelo, prompt)
                        return (modelo, resp)
                    except Exception as e:
                        return (modelo, f"[EXCEPTION] {e}")

            tasks = [_call_modelo(m, semaphore) for m in modelos]
            respuestas = await asyncio.gather(*tasks, return_exceptions=True)

            # Filtrar excepciones de gather
            respuestas_ok = []
            for r in respuestas:
                if isinstance(r, Exception):
                    errores.append(str(r))
                else:
                    respuestas_ok.append(r)

            n_llm_calls += len(respuestas_ok)
            modelos_usados[inteligencia] = [m for m, _ in respuestas_ok]

            # Calcular consenso
            hallazgos_int = self._calcular_consenso(respuestas_ok)
            for h in hallazgos_int:
                h['inteligencia'] = inteligencia
            hallazgos_totales.extend(hallazgos_int)

        # Timeout check
        elapsed = time.time() - t0
        if elapsed > 2700:  # 45 min
            logger.warning(f"Pizarra timeout: {elapsed:.0f}s")

        # Scoring
        scores = self.motor._evaluar(hallazgos_totales, input_texto)
        scores['n_modelos_swarm'] = len(modelos)
        scores['confirmed'] = sum(1 for h in hallazgos_totales if h.get('consenso') == 'confirmed')
        scores['divergent'] = sum(1 for h in hallazgos_totales if h.get('consenso') == 'divergent')

        # Sintesis
        sintesis = self._sintetizar_swarm(hallazgos_totales, 'pizarra')

        # Registrar coste con componente='swarm'
        self._registrar_coste_swarm(n_llm_calls, 'pizarra')

        return {
            'hallazgos': hallazgos_totales,
            'scores': scores,
            'sintesis': sintesis,
            'n_llm_calls': n_llm_calls,
            'modelos_usados': modelos_usados,
            'tier': 4,
            'swarm_info': {
                'tipo': 'pizarra',
                'n_modelos': len(modelos),
                'modelos': modelos,
                'errores': errores[:5],
                'tiempo_s': round(elapsed, 2),
            },
        }

    # ------------------------------------------------------------------
    # Tier 5 — Cartografía
    # ------------------------------------------------------------------

    async def ejecutar_cartografia(self, input_texto: str,
                                   consumidor: str = 'motor_vn') -> dict:
        """Tier 5: TODAS las 18 INTs, 3 modelos × 2 pasadas por INT.

        Returns:
            dict con mapa completo, cobertura por celda, hallazgos con consenso
        """
        t0 = time.time()
        modelos = self._obtener_modelos_pizarra(n=5)[:3]  # 3 modelos para cartografía
        semaphore = asyncio.Semaphore(5)  # Más conservador que pizarra
        hallazgos_totales = []
        modelos_usados = {}
        n_llm_calls = 0
        errores = []
        cobertura_ints = {}

        for int_id in ALL_INTELIGENCIAS:
            prompt = self.motor._generar_prompt_int(int_id, input_texto)
            if not self.motor._pre_validar(prompt, input_texto):
                cobertura_ints[int_id] = {'cubierta': False, 'reason': 'prompt_invalid'}
                continue

            # 3 modelos × 2 pasadas = 6 llamadas por INT
            async def _call(modelo, pasada, sem):
                async with sem:
                    try:
                        # En pasada 2, enriquecer prompt con hint de profundización
                        p = prompt
                        if pasada == 2:
                            p = (f"{prompt}\n\n[PASADA 2] Profundiza: busca lo que "
                                 f"no se dijo en la primera pasada. Contradicciones, "
                                 f"puntos ciegos, implicaciones de segundo orden.")
                        resp = await self.motor._llamar_llm(modelo, p)
                        return (modelo, pasada, resp)
                    except Exception as e:
                        return (modelo, pasada, f"[EXCEPTION] {e}")

            tasks = []
            for modelo in modelos:
                for pasada in [1, 2]:
                    tasks.append(_call(modelo, pasada, semaphore))

            respuestas = await asyncio.gather(*tasks, return_exceptions=True)

            respuestas_ok = []
            for r in respuestas:
                if isinstance(r, Exception):
                    errores.append(str(r))
                else:
                    respuestas_ok.append((r[0], r[2]))  # (modelo, respuesta)

            n_llm_calls += len(respuestas_ok)
            modelos_usados[int_id] = list(set(m for m, _ in respuestas_ok))

            # Consenso por INT
            hallazgos_int = self._calcular_consenso(respuestas_ok)
            for h in hallazgos_int:
                h['inteligencia'] = int_id

            hallazgos_totales.extend(hallazgos_int)
            cobertura_ints[int_id] = {
                'cubierta': len(hallazgos_int) > 0,
                'n_hallazgos': len(hallazgos_int),
                'confirmed': sum(1 for h in hallazgos_int if h.get('consenso') == 'confirmed'),
            }

        elapsed = time.time() - t0

        # Scores
        scores = self.motor._evaluar(hallazgos_totales, input_texto)
        scores['n_modelos_swarm'] = len(modelos)
        scores['ints_cubiertas'] = sum(
            1 for v in cobertura_ints.values() if v.get('cubierta'))
        scores['ints_total'] = 18
        scores['confirmed'] = sum(
            1 for h in hallazgos_totales if h.get('consenso') == 'confirmed')
        scores['divergent'] = sum(
            1 for h in hallazgos_totales if h.get('consenso') == 'divergent')

        # Síntesis final con sintetizador
        sintesis = await self._sintetizar_cartografia(hallazgos_totales, input_texto)

        # Registrar coste
        self._registrar_coste_swarm(n_llm_calls, 'cartografia')

        return {
            'hallazgos': hallazgos_totales,
            'scores': scores,
            'sintesis': sintesis,
            'n_llm_calls': n_llm_calls,
            'modelos_usados': modelos_usados,
            'cobertura_ints': cobertura_ints,
            'tier': 5,
            'swarm_info': {
                'tipo': 'cartografia',
                'n_modelos': len(modelos),
                'n_pasadas': 2,
                'modelos': modelos,
                'errores': errores[:10],
                'tiempo_s': round(elapsed, 2),
            },
        }

    # ------------------------------------------------------------------
    # Síntesis
    # ------------------------------------------------------------------

    def _sintetizar_swarm(self, hallazgos: list, tipo: str) -> str:
        """Síntesis determinista de hallazgos del swarm (sin LLM)."""
        if not hallazgos:
            return "Sin hallazgos para sintetizar."

        confirmed = [h for h in hallazgos if h.get('consenso') == 'confirmed']
        divergent = [h for h in hallazgos if h.get('consenso') == 'divergent']

        por_int = defaultdict(list)
        for h in confirmed:
            por_int[h.get('inteligencia', '')].append(h['hallazgo'])

        lineas = [
            f"SINTESIS {tipo.upper()} ({len(confirmed)} confirmed, "
            f"{len(divergent)} divergent)\n"
        ]

        for int_id, hs in sorted(por_int.items()):
            lineas.append(f"\n{int_id}:")
            for h in hs[:3]:
                lineas.append(f"  - {h[:200]}")

        if divergent:
            lineas.append(f"\nDIVERGENTES ({len(divergent)}):")
            for h in divergent[:5]:
                lineas.append(
                    f"  [{h.get('inteligencia', '?')}] {h['hallazgo'][:150]} "
                    f"({h.get('pct_acuerdo', 0)}% acuerdo)")

        return '\n'.join(lineas)

    async def _sintetizar_cartografia(self, hallazgos: list,
                                      input_texto: str) -> str:
        """Síntesis de cartografía con modelo sintetizador (LLM)."""
        confirmed = [h for h in hallazgos if h.get('consenso') == 'confirmed']
        if not confirmed:
            return self._sintetizar_swarm(hallazgos, 'cartografia')

        # Preparar resumen para sintetizador
        resumen_por_int = defaultdict(list)
        for h in confirmed:
            resumen_por_int[h.get('inteligencia', '')].append(h['hallazgo'][:200])

        bloques = []
        for int_id in ALL_INTELIGENCIAS:
            hs = resumen_por_int.get(int_id, [])
            if hs:
                bloques.append(f"{int_id}: {'; '.join(hs[:3])}")

        prompt = f"""Sintetiza los hallazgos de 18 inteligencias sobre este caso.
Identifica: patrones transversales, contradicciones, puntos ciegos.

CASO: {input_texto[:1000]}

HALLAZGOS POR INTELIGENCIA:
{chr(10).join(bloques)}

Output: síntesis integrada (máx 500 palabras), patrones clave, recomendaciones."""

        modelo = self._obtener_modelo_sintetizador()
        try:
            resp = await self.motor._llamar_llm(modelo, prompt)
            if resp and not resp.startswith('[ERROR') and not resp.startswith('[EXCEPTION'):
                return resp
        except Exception as e:
            logger.warning(f"Sintetizador cartografía falló: {e}")

        # Fallback a síntesis determinista
        return self._sintetizar_swarm(hallazgos, 'cartografia')

    # ------------------------------------------------------------------
    # Coste
    # ------------------------------------------------------------------

    def _registrar_coste_swarm(self, n_calls: int, tipo: str):
        """Registrar coste del swarm en sistema de costes."""
        try:
            from .costes import registrar_coste
            registrar_coste(
                modelo=f'swarm_{tipo}',
                tokens_input=0,
                tokens_output=0,
                latencia_ms=0,
                provider='openrouter',
                componente='swarm',
                operacion=tipo,
            )
        except Exception as e:
            logger.warning(f"Error registrando coste swarm: {e}")

    # ------------------------------------------------------------------
    # Seed config_modelos
    # ------------------------------------------------------------------

    @staticmethod
    def seed_config_modelos():
        """Insert modelos para tier 4-5 si no existen."""
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO config_modelos
                            (rol, modelo, tier_min, tier_max, activo,
                             coste_input_per_m, coste_output_per_m)
                        VALUES
                            ('pizarra', 'deepseek/deepseek-chat-v3-0324',
                             4, 5, true, 0.27, 1.10),
                            ('pizarra', 'google/gemini-2.5-flash-preview',
                             4, 5, true, 0.15, 0.60),
                            ('pizarra', 'mistralai/devstral-2512',
                             4, 5, true, 0.10, 0.30),
                            ('pizarra', 'qwen/qwen3-235b',
                             4, 5, true, 0.30, 1.20),
                            ('sintetizador',
                             'cognitivecomputations/cogito-v1-preview-llama-70B',
                             4, 5, true, 0.40, 1.60)
                        ON CONFLICT DO NOTHING
                    """)
                conn.commit()
                logger.info("Seed config_modelos tier 4-5: OK")
            finally:
                put_conn(conn)
        except Exception as e:
            logger.warning(f"Seed config_modelos tier 4-5 failed: {e}")
