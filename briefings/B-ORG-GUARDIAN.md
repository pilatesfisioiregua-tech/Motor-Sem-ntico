# B-ORG-GUARDIAN: Guardián de Sesgos Interno — El sistema que protege al enjambre de sí mismo

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — sin esto el enjambre tiene sesgo de confirmación y nadie lo detecta
**Modelo:** `anthropic/claude-sonnet-4.6` (1 agente post-enjambre)
**Dependencia:** B-ORG-UNIFY-01+02 ejecutados, B-ORG-COG-PR ejecutado

---

## EL PROBLEMA

El enjambre tiene 13 clusters que evalúan el diagnóstico de `tcf/`. Si todos confirman, ¿es porque es correcto o porque comparten los mismos sesgos? Si el Compositor recibe 13 confirmaciones y 0 contradicciones, puede tener falsa confianza.

Sesgos conocidos del enjambre:
1. **Sesgo de confirmación**: los clusters tienden a confirmar el diagnóstico de código porque lo reciben como "base de verdad"
2. **Sesgo de anclaje**: el primer cluster que responde ancla la interpretación de los siguientes (mitigado por paralelismo, pero no eliminado en el Compositor)
3. **Sesgo de disponibilidad**: los clusters solo ven los datos que se les pasan — no ven lo que NO se les pasó
4. **Sesgo cultural**: todos usan claude-sonnet-4.6, que tiene sus propios sesgos de razonamiento
5. **Sesgo de supervivencia**: solo ven los clientes activos, no los que ya se fueron y por qué

## LA SOLUCIÓN

Un agente GUARDIÁN que se ejecuta DESPUÉS del enjambre y ANTES del Compositor. Recibe TODO el output del enjambre y busca específicamente sesgos, puntos ciegos y falsas certezas.

```
tcf/ diagnóstico
      |
      v
13 clusters (paralelo)
      |
      v
GUARDIÁN DE SESGOS ← ★ NUEVO ★
      |
      v
COMPOSITOR (integra)
```

## ARCHIVO A CREAR

`src/pilates/guardian_sesgos.py`

## CÓDIGO

```python
"""Guardián de Sesgos — Protege al enjambre de sus propios sesgos.

Se ejecuta DESPUÉS del enjambre y ANTES del Compositor.
Busca específicamente: sesgo de confirmación, anclaje, disponibilidad,
puntos ciegos, falsas certezas, unanimidad sospechosa.

Las 77 herramientas cognitivas del catálogo definen 5 sesgos por herramienta.
El Guardián verifica si alguno de esos sesgos está operando en el enjambre.

Modelo: claude-sonnet-4.6 (1 call)
Frecuencia: cada ejecución de G4 (semanal)
"""
from __future__ import annotations

import json
import os
import structlog
import httpx

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4.6")


SYSTEM_GUARDIAN = """Eres el GUARDIÁN DE SESGOS del organismo cognitivo de OMNI-MIND.

Tu trabajo: recibir el output COMPLETO del enjambre (13 clusters: 6 INT + 4 P + 3 R)
y buscar SESGOS, PUNTOS CIEGOS y FALSAS CERTEZAS.

NO eres un validador. Eres un ABOGADO DEL DIABLO. Tu trabajo es encontrar lo que está MAL,
no confirmar lo que está bien.

SESGOS A BUSCAR:

1. SESGO DE CONFIRMACIÓN: ¿Todos los clusters confirman el diagnóstico de código?
   Si >80% confirman y <10% contradicen → SOSPECHOSO. La realidad rara vez confirma
   un modelo tan limpiamente. Busca qué evidencia podría contradecir y nadie la mencionó.

2. SESGO DE ANCLAJE: ¿Los clusters repiten las mismas palabras/framing del diagnóstico
   de código? Si sí, están anclados al input y no pensando independientemente.

3. SESGO DE DISPONIBILIDAD: ¿Los clusters solo mencionan datos que recibieron?
   ¿Hay datos AUSENTES que deberían haberse considerado? Ejemplo: si ningún cluster
   menciona la estacionalidad del negocio, eso es un punto ciego.

4. UNANIMIDAD SOSPECHOSA: Si TODOS los clusters dicen lo mismo, probablemente
   están viendo lo mismo desde el mismo ángulo. La diversidad de perspectivas
   debería producir ALGUNA divergencia. Unanimidad = señal de sesgo compartido.

5. FALSA CERTEZA: ¿Algún cluster afirma algo con mucha confianza basándose en
   poca evidencia? "CONFIRMADO" con 1 dato no es confirmación.

6. PUNTO CIEGO SISTÉMICO: ¿Hay algo que NINGÚN cluster mencionó que debería
   ser obvio? Ejemplo: si hay 90 clientes pero ningún cluster pregunta por
   la satisfacción real (no solo asistencia), eso es un punto ciego.

7. SESGO DE SUPERVIVENCIA: ¿Los clusters solo analizan lo que EXISTS?
   ¿Qué pasa con los clientes que se fueron? ¿Los servicios que se eliminaron?
   ¿Las ideas que se descartaron? Lo que no existe puede ser más revelador
   que lo que existe.

8. SESGO CULTURAL DEL MODELO: claude-sonnet-4.6 tiende a ser optimista
   y a buscar soluciones constructivas. ¿Hay algún caso donde la respuesta
   correcta es "esto no tiene solución" o "esto debería morir" y ningún
   cluster lo dijo?

REGLAS:
- Sé ESPECÍFICO. No digas "hay sesgo de confirmación" — di "el cluster
  comprension_profunda confirma que INT-17 está ausente, pero la única
  evidencia es que 'Jesús no cuestiona' — eso podría ser también que
  cuestiona en privado y los datos no lo captan."
- Cada sesgo detectado debe tener: tipo, evidencia, impacto potencial,
  y qué hacer para verificar.
- Si NO encuentras sesgos significativos, di "sin sesgos críticos detectados"
  — pero eso debería ser raro.

Responde en JSON:
{
    "sesgos_detectados": [
        {
            "tipo": "confirmacion|anclaje|disponibilidad|unanimidad|falsa_certeza|punto_ciego|supervivencia|cultural",
            "descripcion": "qué sesgo hay y dónde",
            "evidencia": "qué en el output del enjambre lo demuestra",
            "clusters_afectados": ["cluster_id"],
            "impacto_potencial": "qué consecuencia tiene si no se corrige",
            "verificacion": "qué dato/acción verificaría si es sesgo real o no",
            "gravedad": 1-5
        }
    ],
    "puntos_ciegos": [
        {
            "aspecto": "qué nadie mencionó",
            "por_que_importa": "por qué debería haberse mencionado",
            "clusters_que_deberian_verlo": ["cluster_id"]
        }
    ],
    "unanimidades_sospechosas": [
        {
            "afirmacion": "qué todos dicen igual",
            "n_clusters": 13,
            "por_que_sospechosa": "por qué unanimidad no es señal de verdad aquí"
        }
    ],
    "confianza_ajustada": 0.0-1.0,
    "recomendacion": "aplicar|ajustar_con_cautela|reconvocar_con_datos_adicionales",
    "datos_faltantes": ["qué datos pedir para eliminar la incertidumbre"]
}"""


async def evaluar_sesgos(resultados_enjambre: dict, diagnostico_codigo: dict) -> dict:
    """Evalúa sesgos en el output del enjambre.

    Args:
        resultados_enjambre: Output completo de ejecutar_enjambre()
        diagnostico_codigo: Diagnóstico de tcf/ (repertorio + prescripción)

    Returns:
        Evaluación de sesgos con recomendaciones.
    """
    if not OPENROUTER_API_KEY:
        return {"sesgos_detectados": [], "confianza_ajustada": 0.5,
                "recomendacion": "sin_modelo", "puntos_ciegos": [], "datos_faltantes": []}

    # Serializar inputs para el Guardián
    enjambre_str = json.dumps(resultados_enjambre, ensure_ascii=False, indent=2, default=str)[:6000]
    codigo_str = json.dumps(diagnostico_codigo, ensure_ascii=False, indent=2, default=str)[:2000]

    # Calcular estadísticas rápidas del enjambre
    total_confirmaciones = resultados_enjambre.get("confirmaciones", 0)
    total_contradicciones = resultados_enjambre.get("contradicciones", 0)
    total = total_confirmaciones + total_contradicciones
    pct_confirmacion = round(total_confirmaciones / max(total, 1) * 100)

    user_prompt = f"""DIAGNÓSTICO DE CÓDIGO (lo que los clusters recibieron como input):
{codigo_str}

OUTPUT COMPLETO DEL ENJAMBRE (13 clusters):
{enjambre_str}

ESTADÍSTICAS RÁPIDAS:
- Confirmaciones: {total_confirmaciones} ({pct_confirmacion}%)
- Contradicciones: {total_contradicciones} ({100-pct_confirmacion}%)
- Clusters ejecutados: {resultados_enjambre.get('clusters_ejecutados', 0)}

CONTEXTO: Authentic Pilates, ~90 clientes, instructor único, pueblo 4.000 hab.

Busca sesgos, puntos ciegos, unanimidades sospechosas y falsas certezas."""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                json={
                    "model": REASONING_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_GUARDIAN},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]

        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        resultado = json.loads(clean.strip())

    except Exception as e:
        log.error("guardian_error", error=str(e))
        return {"sesgos_detectados": [], "confianza_ajustada": 0.5,
                "recomendacion": "error", "error": str(e)[:200]}

    # Emitir al bus si hay sesgos graves
    sesgos_graves = [s for s in resultado.get("sesgos_detectados", []) if s.get("gravedad", 0) >= 4]
    if sesgos_graves:
        try:
            from src.pilates.bus import emitir
            await emitir("ALERTA", "GUARDIAN_SESGOS", {
                "tipo": "sesgo_grave_detectado",
                "sesgos": sesgos_graves,
                "confianza_ajustada": resultado.get("confianza_ajustada", 0),
                "recomendacion": resultado.get("recomendacion"),
            }, prioridad=2)
        except Exception:
            pass

    # Feed
    try:
        from src.pilates.feed import publicar
        n_sesgos = len(resultado.get("sesgos_detectados", []))
        n_ciegos = len(resultado.get("puntos_ciegos", []))
        if n_sesgos > 0 or n_ciegos > 0:
            await publicar(
                "organismo_guardian", "🛡️",
                f"Guardián: {n_sesgos} sesgos, {n_ciegos} puntos ciegos",
                f"Confianza ajustada: {resultado.get('confianza_ajustada', 0):.0%}. "
                f"Recomendación: {resultado.get('recomendacion', 'desconocida')}",
                severidad="warning" if n_sesgos > 2 else "info")
    except Exception:
        pass

    log.info("guardian_ok",
             sesgos=len(resultado.get("sesgos_detectados", [])),
             puntos_ciegos=len(resultado.get("puntos_ciegos", [])),
             confianza=resultado.get("confianza_ajustada"))

    return resultado
```

## INTEGRACIÓN EN compositor.py (ejecutar_g4)

Después del enjambre y ANTES del compositor, añadir:

```python
    # 2b. GUARDIÁN DE SESGOS (post-enjambre, pre-compositor)
    from src.pilates.guardian_sesgos import evaluar_sesgos
    guardian = await evaluar_sesgos(enjambre, {
        "estado": diag_result.get("estado"),
        "repertorio": diag_result.get("repertorio"),
        "prescripcion": diag_result.get("prescripcion"),
    })

    # Inyectar resultado del guardián en el input del compositor
    compositor_input += f"\n\nEVALUACIÓN DEL GUARDIÁN DE SESGOS:\n{json.dumps(guardian, ensure_ascii=False, indent=2, default=str)[:1500]}"
```

Y en el return:

```python
    return {
        ...
        "guardian_sesgos": guardian,
        ...
    }
```

## COSTE

1 call claude-sonnet-4.6 = ~$0.05/ejecución, ~$0.20/mes

## TESTS

### T1: Guardián detecta al menos 1 sesgo o punto ciego
```python
result = await evaluar_sesgos(enjambre_output, diagnostico_codigo)
total = len(result.get("sesgos_detectados", [])) + len(result.get("puntos_ciegos", []))
assert total >= 1  # Un enjambre perfecto sin sesgos es sospechoso
```

### T2: Confianza ajustada es razonable
```python
assert 0.1 <= result.get("confianza_ajustada", 0) <= 1.0
```

### T3: Recomendación es válida
```python
assert result.get("recomendacion") in ("aplicar", "ajustar_con_cautela", "reconvocar_con_datos_adicionales")
```
