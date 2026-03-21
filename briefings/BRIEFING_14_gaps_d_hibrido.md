# BRIEFING_14: Cerrar gaps + Integrar D_híbrido en Motor

Fecha: 2026-03-18
Prioridad: 3B (post-pilotos, pre-P4)
Objetivo: Cerrar 2 gaps del piloto + integrar formato de prompt validado para máxima calidad

---

## CONTEXTO

Los pilotos (BRIEFING_13) funcionaron: 270 hallazgos, $0.02, 27/27 señales PID OK. Pero revelaron 2 gaps de fontanería y el Motor usa prompts genéricos en vez del formato D_híbrido validado en Exp-11 (91% cobertura vs 61% con prosa pura).

---

## FIX 1: Registrar ejecuciones en tabla `ejecuciones`

### Problema
Motor vN registra datapoints en `datapoints_efectividad` y `efectos_matriz` via el Registrador, pero NUNCA escribe en la tabla `ejecuciones`. Las 7 rows históricas son de tests antiguos. El Monitoring y CEO Advisor consultan `ejecuciones` para métricas y dashboard.

### Solución
En `core/motor_vn.py`, dentro del método `ejecutar()`, DESPUÉS de la línea:

```python
        resultado = await self._fase_ejecucion(programa, input_texto)
```

Y ANTES de:

```python
        # ===== ACTUALIZAR PROGRAMA POST-EJECUCION =====
```

Añadir:

```python
        # ===== REGISTRAR EN TABLA EJECUCIONES =====
        try:
            from .db_pool import get_conn, put_conn
            conn_ej = get_conn()
            if conn_ej:
                try:
                    with conn_ej.cursor() as cur:
                        cur.execute("""
                            INSERT INTO ejecuciones
                                (input, contexto, modo, huecos_detectados,
                                 algoritmo_usado, resultado, coste_usd, tiempo_s, score_calidad)
                            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)
                        """, [
                            input_texto[:2000],
                            consumidor,
                            modo,
                            json.dumps(gradientes.get('top_gaps', [])[:10], default=str),
                            json.dumps({
                                'inteligencias': sorted(programa.inteligencias),
                                'tier': programa.tier,
                                'alpha': programa.alpha,
                                'profundidad': programa.profundidad,
                            }, default=str),
                            json.dumps({
                                'n_hallazgos': len(resultado.get('hallazgos', [])),
                                'sintesis': resultado.get('sintesis', '')[:1000],
                                'n_llm_calls': resultado.get('n_llm_calls', 0),
                            }, default=str),
                            round(self.coste_acumulado, 6),
                            round(time.time() - t0, 2),
                            resultado.get('scores', {}).get('score_calidad', 0),
                        ])
                    conn_ej.commit()
                finally:
                    put_conn(conn_ej)
        except Exception as _e:
            print(f"[WARN:motor_vn.ejecutar.ejecuciones] {type(_e).__name__}: {_e}")
```

### Verificación
Después de una ejecución del Motor:
```sql
SELECT id, modo, contexto, coste_usd, tiempo_s, score_calidad 
FROM ejecuciones ORDER BY created_at DESC LIMIT 3;
-- Debe mostrar la ejecución reciente con consumidor en contexto
```

---

## FIX 2: Poblar `perfil_gradientes` por consumidor

### Problema
`perfil_gradientes` tiene 0 rows. Nadie escribe ahí. Esta tabla debería acumular un perfil de gaps por consumidor (exocortex:pilates, exocortex:fisioterapia) que evoluciona con cada ejecución.

### Solución
En `core/motor_vn.py`, dentro de `ejecutar()`, DESPUÉS del bloque de registrar en `ejecuciones` (Fix 1), añadir:

```python
        # ===== ACTUALIZAR PERFIL DE GRADIENTES POR CONSUMIDOR =====
        try:
            from .db_pool import get_conn, put_conn
            conn_pg = get_conn()
            if conn_pg:
                try:
                    with conn_pg.cursor() as cur:
                        # Upsert: incrementar versión si existe, crear si no
                        cur.execute("""
                            INSERT INTO perfil_gradientes (consumidor, gradientes, version)
                            VALUES (%s, %s::jsonb, 1)
                            ON CONFLICT (consumidor, usuario_id) DO UPDATE SET
                                gradientes = %s::jsonb,
                                version = perfil_gradientes.version + 1,
                                updated_at = NOW()
                        """, [
                            consumidor,
                            json.dumps(gradientes.get('gradientes', {}), default=str),
                            json.dumps(gradientes.get('gradientes', {}), default=str),
                        ])
                    conn_pg.commit()
                finally:
                    put_conn(conn_pg)
        except Exception as _e:
            print(f"[WARN:motor_vn.ejecutar.perfil_gradientes] {type(_e).__name__}: {_e}")
```

**NOTA IMPORTANTE:** La tabla `perfil_gradientes` tiene `consumidor` + `usuario_id` sin UNIQUE constraint combinado. Verificar antes:
```sql
\d perfil_gradientes
```
Si no hay UNIQUE en (consumidor, usuario_id), el ON CONFLICT fallará. En ese caso:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_perfil_gradientes_consumidor_usuario 
ON perfil_gradientes (consumidor, COALESCE(usuario_id, ''));
```

### Verificación
```sql
SELECT consumidor, version, updated_at FROM perfil_gradientes;
-- Debe tener entries para cada consumidor ejecutado
```

---

## FIX 3: Integrar formato D_híbrido en el Generador del Motor

### Problema
`_generar_prompt_int()` genera un prompt genérico ("Analiza el siguiente caso desde la perspectiva de INT-XX...") con 61% de cobertura. El formato D_híbrido validado en Exp-11 logra 91% cobertura, 100% adherencia, y -35% tokens.

### Referencia canónica
`docs/L0/FORMATO_CANONICO_PROMPT.md` — leer primero.

### Solución
Reescribir `_generar_prompt_int()` y `_generar_prompt_preguntas()` en `core/motor_vn.py`.

**Reemplazar `_generar_prompt_int()`** (actualmente en ~línea 674) con:

```python
    def _generar_prompt_int(self, inteligencia: str, input_texto: str) -> str:
        """Generar prompt en formato D_híbrido (P35) para una inteligencia.

        Formato canónico: pipeline como código Python + preguntas en lenguaje natural.
        Validado: 91% cobertura, 100% adherencia, -35% tokens vs prosa pura.
        Ref: docs/L0/FORMATO_CANONICO_PROMPT.md
        """
        # Cargar firma y punto_ciego de la inteligencia desde DB
        firma, punto_ciego, lentes_naturales = self._cargar_metadata_int(inteligencia)

        # Cargar preguntas de la Matriz para esta inteligencia
        preguntas_por_paso = self._cargar_preguntas_int(inteligencia)

        # Determinar si necesita provocaciones (INT-17, INT-18 = frontera)
        usa_provocaciones = inteligencia in ('INT-17', 'INT-18')

        # Determinar lentes
        lentes = lentes_naturales if lentes_naturales else ['Salud', 'Sentido', 'Continuidad']
        lentes_str = ', '.join(f'"{l}"' for l in lentes)

        # --- Bloque código (estructura) ---
        bloque_codigo = f'''```python
pipeline = [
    {{"op": "EXTRAER", "target": caso, "output": "datos_formalizados"}},
    {{"op": "CRUZAR", "input": "datos_formalizados", "output": "estructura_problema"}},
    {{"op": "LENTES", "input": "estructura_problema", "lenses": [{lentes_str}], "output": "perspectivas"}},
    {{"op": "INTEGRAR", "input": "perspectivas", "output": "sintesis"}},
    {{"op": "ABSTRAER", "input": "sintesis", "output": "patron"}},
    {{"op": "FRONTERA", "input": "patron", "output": "limites"}},
]

agent = {{"id": "{inteligencia}", "signature": "{firma}", "blind_spot": "{punto_ciego}"}}
```'''

        # --- Bloque natural (preguntas) ---
        pasos = ['EXTRAER', 'CRUZAR', 'LENTES', 'INTEGRAR', 'ABSTRAER', 'FRONTERA']
        bloque_preguntas = "Ejecuta este pipeline sobre el caso. Preguntas por paso:\n\n"

        for paso in pasos:
            qs = preguntas_por_paso.get(paso, [])
            if qs:
                preguntas_texto = ' '.join(qs[:3])  # Max 3 preguntas por paso
            else:
                preguntas_texto = self._pregunta_default(paso, inteligencia)

            bloque_preguntas += f"**{paso}**: {preguntas_texto}\n"

            # Provocación para inteligencias de frontera (D+G)
            if usa_provocaciones and paso in ('FRONTERA', 'INTEGRAR', 'EXTRAER'):
                provoc = self._generar_provocacion(paso, inteligencia, punto_ciego)
                if provoc:
                    bloque_preguntas += f"↳ Provoca: {provoc}\n"

            bloque_preguntas += "\n"

        # --- Output schema ---
        output_schema = "Output: hallazgos (uno por línea, concreto y accionable), firma_combinada, puntos_ciegos."

        return f"""{bloque_codigo}

{bloque_preguntas}
{output_schema}

CASO:
{input_texto}"""

    def _cargar_metadata_int(self, inteligencia: str) -> tuple:
        """Cargar firma, punto_ciego y modos de una inteligencia desde DB."""
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return ('', '', [])
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT firma, punto_ciego, modos_naturales
                        FROM inteligencias WHERE id = %s
                    """, [inteligencia])
                    row = cur.fetchone()
                    if row:
                        return (row[0] or '', row[1] or '', row[2] or [])
                return ('', '', [])
            finally:
                put_conn(conn)
        except Exception:
            return ('', '', [])

    def _cargar_preguntas_int(self, inteligencia: str) -> dict:
        """Cargar preguntas de la Matriz agrupadas por paso del pipeline.

        Mapea lente/funcion a pasos del pipeline:
        - Funciones de percepción → EXTRAER
        - Funciones de análisis → CRUZAR
        - Lentes → LENTES
        - Funciones de integración → INTEGRAR
        - Funciones de abstracción → ABSTRAER
        - Funciones de frontera → FRONTERA
        """
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return {}
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT lente, funcion, texto FROM preguntas_matriz
                        WHERE inteligencia = %s AND nivel = 'base'
                        ORDER BY lente, funcion
                        LIMIT 30
                    """, [inteligencia])
                    rows = cur.fetchall()

                # Mapear funciones a pasos del pipeline
                paso_mapping = {
                    'Conservar': 'EXTRAER',
                    'Captar': 'EXTRAER',
                    'Depurar': 'CRUZAR',
                    'Distribuir': 'CRUZAR',
                    'Frontera': 'FRONTERA',
                    'Adaptar': 'ABSTRAER',
                    'Replicar': 'INTEGRAR',
                }
                lente_paso = 'LENTES'

                preguntas = {}
                for lente, funcion, texto in rows:
                    paso = paso_mapping.get(funcion, 'CRUZAR')
                    preguntas.setdefault(paso, []).append(texto)
                    # También añadir a LENTES si es una lente explícita
                    preguntas.setdefault(lente_paso, []).append(f"{lente}: {texto}")

                return preguntas
            finally:
                put_conn(conn)
        except Exception:
            return {}

    def _pregunta_default(self, paso: str, inteligencia: str) -> str:
        """Pregunta default cuando no hay preguntas en la Matriz para un paso."""
        defaults = {
            'EXTRAER': f'¿Qué datos clave se pueden identificar desde la perspectiva de {inteligencia}?',
            'CRUZAR': '¿Qué relaciones o tensiones emergen entre los datos extraídos?',
            'LENTES': '¿Cómo se ve el caso desde cada lente (Salud, Sentido, Continuidad)?',
            'INTEGRAR': '¿Qué patrón emerge al cruzar todas las perspectivas?',
            'ABSTRAER': '¿Este patrón es transferible a otros contextos? ¿Qué lo hace universal?',
            'FRONTERA': '¿Qué asume este análisis que no ha examinado? ¿Dónde están los límites?',
        }
        return defaults.get(paso, f'¿Qué revela {paso} desde {inteligencia}?')

    def _generar_provocacion(self, paso: str, inteligencia: str, punto_ciego: str) -> str:
        """Generar provocación para inteligencias de frontera (D+G format)."""
        provocaciones = {
            'EXTRAER': {
                'INT-17': f'Si esta persona se mirara al espejo dentro de 10 años habiendo elegido NO actuar — ¿qué vería?',
                'INT-18': '¿Qué es lo que este caso intenta decir que nadie ha escuchado todavía?',
            },
            'INTEGRAR': {
                'INT-17': 'Si las tres lentes fueran tres versiones de esta persona — pasada, presente, futura — ¿estarían de acuerdo?',
                'INT-18': '¿Qué sucede si dejamos de intentar resolver y simplemente observamos?',
            },
            'FRONTERA': {
                'INT-17': f'{inteligencia} puede {punto_ciego.lower()}. ¿Este análisis está ayudando a decidir, o a posponer?',
                'INT-18': f'¿Qué ha quedado sin decir que este análisis no puede capturar?',
            },
        }
        return provocaciones.get(paso, {}).get(inteligencia, '')
```

**Reemplazar `_generar_prompt_preguntas()`** con:

```python
    def _generar_prompt_preguntas(self, preguntas: list, input_texto: str) -> str:
        """Generar prompt D_híbrido desde preguntas específicas compiladas."""
        # Formato D_híbrido simplificado para preguntas pre-compiladas
        preguntas_texto = "\n".join(
            f"- {p.get('texto', p) if isinstance(p, dict) else p}"
            for p in preguntas[:8]
        )

        return f'''```python
pipeline = [
    {{"op": "ANALIZAR", "target": caso, "questions": "ver_abajo", "output": "hallazgos"}},
]
```

Responde cada pregunta con un hallazgo concreto y accionable.

Preguntas:
{preguntas_texto}

Output: hallazgos (uno por línea), puntos_ciegos.

CASO:
{input_texto}'''
```

### Verificación
Ejecutar una ejecución del Motor y verificar que el prompt usa el formato D_híbrido:
```bash
# Añadir un print temporal en _generar_prompt_int para ver el prompt generado
# O ejecutar y verificar que la calidad/cobertura mejora
curl -X POST https://chief-os-omni.fly.dev/motor/ejecutar-vn \
  -H "Content-Type: application/json" \
  -d '{"input": "Estudio de pilates con problemas de retención", "modo": "analisis", "consumidor": "test_d_hibrido"}'
```

Comparar hallazgos con las ejecuciones de BRIEFING_13 (que usaron prompts genéricos):
```sql
-- Ejecuciones con prompt genérico (BRIEFING_13)
SELECT count(*) as n_hallazgos FROM efectos_matriz 
WHERE ejecucion_id IN (SELECT ejecucion_id FROM campo_gradientes 
WHERE input_texto LIKE '%Pilates%' ORDER BY created_at ASC LIMIT 1);

-- Ejecución con D_híbrido (nueva)
SELECT count(*) as n_hallazgos FROM efectos_matriz 
WHERE ejecucion_id IN (SELECT ejecucion_id FROM campo_gradientes 
WHERE input_texto LIKE '%pilates%' ORDER BY created_at DESC LIMIT 1);
```

---

## ORDEN DE EJECUCIÓN

```
PASO 1: Leer docs/L0/FORMATO_CANONICO_PROMPT.md completo (referencia)
PASO 2: Aplicar FIX 1 (registrar en ejecuciones)
PASO 3: Aplicar FIX 2 (perfil_gradientes) — verificar/crear UNIQUE index primero
PASO 4: Aplicar FIX 3 (D_híbrido) — reemplazar _generar_prompt_int + _generar_prompt_preguntas + añadir métodos auxiliares
PASO 5: Deploy
PASO 6: Ejecutar una ejecución de test para verificar los 3 fixes
PASO 7: Verificar (queries SQL)
```

---

## CRITERIO DE ÉXITO

- [ ] Tabla `ejecuciones` recibe datos de cada ejecución del Motor
- [ ] Tabla `perfil_gradientes` se puebla por consumidor
- [ ] Motor genera prompts en formato D_híbrido (pipeline como código + preguntas naturales)
- [ ] Inteligencias de frontera (INT-17, INT-18) incluyen provocaciones (D+G)
- [ ] Prompts cargan firma + punto_ciego desde DB (no hardcoded)
- [ ] Prompts cargan preguntas desde preguntas_matriz (no genéricas)

## COSTE
- Deploy: $0
- Ejecución de test: ~$0.005
- Total: ~$0.005
