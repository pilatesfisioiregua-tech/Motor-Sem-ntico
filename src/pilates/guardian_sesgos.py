"""Guardián de Sesgos — Protege al enjambre de sus propios sesgos.

Se ejecuta DESPUÉS del enjambre y ANTES del Compositor.
Busca específicamente: sesgo de confirmación, anclaje, disponibilidad,
puntos ciegos, falsas certezas, unanimidad sospechosa.

Modelo: claude-sonnet-4.6 (1 call)
Frecuencia: cada ejecución de G4 (semanal)
"""
from __future__ import annotations

import json
import os
import structlog
import time

from src.db.client import get_pool

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4-6")


SYSTEM_GUARDIAN = """Eres el GUARDIÁN DE SESGOS del organismo cognitivo de OMNI-MIND.

Tu trabajo: recibir el output COMPLETO del enjambre (6 clusters)
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

7. SESGO DE SUPERVIVENCIA: ¿Los clusters solo analizan lo que EXISTE?
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
            "n_clusters": 6,
            "por_que_sospechosa": "por qué unanimidad no es señal de verdad aquí"
        }
    ],
    "confianza_ajustada": 0.0-1.0,
    "recomendacion": "aplicar|ajustar_con_cautela|reconvocar_con_datos_adicionales",
    "datos_faltantes": ["qué datos pedir para eliminar la incertidumbre"]
}"""


async def evaluar_sesgos(resultados_enjambre: dict, diagnostico_codigo: dict) -> dict:
    """Evalúa sesgos en el output del enjambre.

    Usa _call_llm del compositor para JSON parsing robusto.
    """
    if not OPENROUTER_API_KEY:
        return {"sesgos_detectados": [], "confianza_ajustada": 0.5,
                "recomendacion": "sin_modelo", "puntos_ciegos": [], "datos_faltantes": []}

    t0 = time.time()

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

OUTPUT COMPLETO DEL ENJAMBRE (6 clusters):
{enjambre_str}

ESTADÍSTICAS RÁPIDAS:
- Confirmaciones: {total_confirmaciones} ({pct_confirmacion}%)
- Contradicciones: {total_contradicciones} ({100-pct_confirmacion}%)
- Clusters ejecutados: {resultados_enjambre.get('clusters_ejecutados', 0)}

CONTEXTO: Authentic Pilates, ~{diagnostico_codigo.get('metricas_raw', {}).get('total_activos', 22)} clientes, instructor único, pueblo 4.000 hab.

Busca sesgos, puntos ciegos, unanimidades sospechosas y falsas certezas."""

    # Usar _call_llm del compositor (JSON parsing ultrarrobusto)
    from src.pilates.compositor import _call_llm
    resultado = await _call_llm(
        REASONING_MODEL, SYSTEM_GUARDIAN, user_prompt, "guardian",
        max_tokens=6000)

    if "error" in resultado:
        log.error("guardian_error", error=resultado["error"])
        return {"sesgos_detectados": [], "confianza_ajustada": 0.5,
                "recomendacion": "error", "error": resultado["error"]}

    dt = round(time.time() - t0, 1)

    # Emitir al bus si hay sesgos graves
    sesgos_graves = [s for s in resultado.get("sesgos_detectados", [])
                     if isinstance(s.get("gravedad"), (int, float)) and s["gravedad"] >= 4]
    if sesgos_graves:
        try:
            from src.pilates.bus import emitir
            await emitir("ALERTA", "GUARDIAN_SESGOS", {
                "tipo": "sesgo_grave_detectado",
                "sesgos": sesgos_graves,
                "confianza_ajustada": resultado.get("confianza_ajustada", 0),
                "recomendacion": resultado.get("recomendacion"),
            }, prioridad=2)
        except Exception as e:
            log.debug("silenced_exception", exc=str(e))

    # Pizarra
    try:
        from src.pilates.pizarra import escribir
        n_sesgos = len(resultado.get("sesgos_detectados", []))
        n_ciegos = len(resultado.get("puntos_ciegos", []))
        await escribir(
            agente="GUARDIAN",
            capa="cognitiva",
            estado="completado",
            detectando=f"{n_sesgos} sesgos, {n_ciegos} puntos ciegos",
            interpretacion=f"Confianza ajustada: {resultado.get('confianza_ajustada', 0):.0%}. "
                           f"Recomendación: {resultado.get('recomendacion', 'desconocida')}",
            accion_propuesta=f"Datos faltantes: {', '.join(resultado.get('datos_faltantes', [])[:3])}"
                             if resultado.get("datos_faltantes") else "Sin datos faltantes",
            confianza=resultado.get("confianza_ajustada", 0.5),
            prioridad=3,
        )
    except Exception as e:
        log.debug("silenced_exception", exc=str(e))

    # Feed
    try:
        from src.pilates.feed import publicar
        n_sesgos = len(resultado.get("sesgos_detectados", []))
        n_ciegos = len(resultado.get("puntos_ciegos", []))
        if n_sesgos > 0 or n_ciegos > 0:
            await publicar(
                "organismo_guardian", "shield",
                f"Guardian: {n_sesgos} sesgos, {n_ciegos} puntos ciegos",
                f"Confianza ajustada: {resultado.get('confianza_ajustada', 0):.0%}. "
                f"Recomendacion: {resultado.get('recomendacion', 'desconocida')}",
                severidad="warning" if n_sesgos > 2 else "info")
    except Exception as e:
        log.debug("silenced_exception", exc=str(e))

    log.info("guardian_ok",
             sesgos=len(resultado.get("sesgos_detectados", [])),
             puntos_ciegos=len(resultado.get("puntos_ciegos", [])),
             confianza=resultado.get("confianza_ajustada"),
             tiempo=dt)

    return resultado
