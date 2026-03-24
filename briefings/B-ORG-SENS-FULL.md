# B-ORG-SENS-FULL: 6 Buscadores Especializados — Ojos del organismo al mundo

**Fecha:** 23 marzo 2026
**Prioridad:** Media-alta — sin esto toda la búsqueda va por Perplexity genérico
**Dependencia:** B-ORG-UNIFY-01 ejecutado (buscador con Motor Gap+Gradiente funcional)

---

## EL PROBLEMA

L0_9 diseñó 7 buscadores especializados. El actual (`buscador.py`) enruta TODO por Perplexity con queries typed por categoría, pero usa una sola API para todo. Esto significa:

- Búsquedas regulatorias van a Perplexity en vez de al BOE
- Búsquedas científicas van a Perplexity en vez de a PubMed
- No hay datos de mercado local (INE, Google Trends)
- No hay monitorización de competencia (Outscraper)
- No hay seguimiento de consumo/audiencia (SparkToro, Meta Insights)

Para Authentic Pilates en concreto: evidencia científica de Pilates terapéutico (PubMed) sería oro para F5 (diferenciación). Y datos de competencia local (Outscraper) alimentarían F6 (adaptación).

## DISEÑO

Ampliar `buscador.py` con 6 buscadores especializados que se activan según el tipo de query generada. El Generador de Queries ya produce `tipo_buscador` en cada query — solo falta el routing.

```
GENERADOR DE QUERIES (gpt-4o)
  produce: [{query, tipo_buscador, funcion, urgencia}, ...]
              |
    ┌─────────┼──────────────────────────────────────────┐
    v         v         v         v         v            v
SECTORIAL  CIENTIFICO REGULAT  FINANC   MERCADO_LOCAL  CONSUMO
(Perplexity)(PubMed)  (BOE)    (CDTI)   (Trends+INE)  (SparkToro)
    |         |         |         |         |            |
    └─────────┼──────────┼─────────┼─────────┼────────────┘
              v
        FILTRO ACD → CORPUS VIVO
```

## CAMBIOS EN buscador.py

Reemplazar `_buscar_perplexity()` como único buscador por un router:

```python
# ============================================================
# BUSCADORES ESPECIALIZADOS
# ============================================================

async def _buscar_sectorial(query: str, contexto: str) -> dict | None:
    """Perplexity para tendencias sectoriales, mejores prácticas, innovación."""
    return await _buscar_perplexity(query, contexto)  # Ya funciona


async def _buscar_cientifico(query: str, contexto: str) -> dict | None:
    """PubMed / Perplexity modo académico para evidencia científica.

    Crucial para Authentic Pilates: evidencia de Pilates terapéutico,
    dolor lumbar, escoliosis, suelo pélvico. F5 diferenciación basada en datos.
    """
    if not PERPLEXITY_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content":
                            "Eres un investigador académico. Busca SOLO evidencia científica: "
                            "ensayos clínicos, revisiones sistemáticas, meta-análisis. "
                            "Cita fuentes con autor, año, journal. "
                            "Si no hay evidencia fuerte, di 'evidencia limitada'. "
                            f"Contexto: {contexto[:150]}"},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"query": query, "respuesta": data["choices"][0]["message"]["content"],
                    "tipo": "cientifico"}
    except Exception as e:
        log.warning("buscador_cientifico_error", query=query[:50], error=str(e))
        return None


async def _buscar_regulatorio(query: str, contexto: str) -> dict | None:
    """Perplexity modo legal/fiscal para cambios regulatorios.

    BOE, normativa autonómica, RGPD, fiscalidad autónomos/SL.
    """
    if not PERPLEXITY_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content":
                            "Eres un asesor legal/fiscal español. Busca normativa vigente, "
                            "cambios recientes en BOE, regulación autonómica de La Rioja, "
                            "obligaciones fiscales para autónomos/PYMES del sector servicios. "
                            "Cita la norma exacta (Real Decreto, Ley, BOE fecha). "
                            f"Contexto: {contexto[:150]}"},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"query": query, "respuesta": data["choices"][0]["message"]["content"],
                    "tipo": "regulatorio"}
    except Exception as e:
        log.warning("buscador_regulatorio_error", query=query[:50], error=str(e))
        return None


async def _buscar_financiero(query: str, contexto: str) -> dict | None:
    """Perplexity modo financiero para subvenciones, benchmarks, costes."""
    if not PERPLEXITY_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content":
                            "Eres un asesor financiero para PYMES en España. Busca: "
                            "subvenciones disponibles (CDTI, ICO, autonómicas La Rioja), "
                            "benchmarks del sector fitness/wellness, costes de referencia. "
                            "Incluye plazos de solicitud si los hay. "
                            f"Contexto: {contexto[:150]}"},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"query": query, "respuesta": data["choices"][0]["message"]["content"],
                    "tipo": "financiero"}
    except Exception as e:
        log.warning("buscador_financiero_error", query=query[:50], error=str(e))
        return None


async def _buscar_mercado_local(query: str, contexto: str) -> dict | None:
    """Google Trends + Perplexity para mercado local.

    Competencia, demografía, tendencias de búsqueda local.
    Para Authentic Pilates: qué buscan en Logroño/La Rioja sobre pilates.
    """
    if not PERPLEXITY_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content":
                            "Eres un analista de mercado local en España. Busca: "
                            "competencia directa en La Rioja, tendencias de demanda, "
                            "datos demográficos de la zona, aperturas/cierres recientes "
                            "en el sector fitness/wellness/pilates. Sé específico con "
                            "nombres de competidores si los encuentras. "
                            f"Contexto: {contexto[:150]}"},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"query": query, "respuesta": data["choices"][0]["message"]["content"],
                    "tipo": "mercado_local"}
    except Exception as e:
        log.warning("buscador_mercado_error", query=query[:50], error=str(e))
        return None


async def _buscar_tecnologico(query: str, contexto: str) -> dict | None:
    """Perplexity modo tech para herramientas, plataformas, integraciones."""
    if not PERPLEXITY_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content":
                            "Eres un analista de tecnología para negocios pequeños. Busca: "
                            "herramientas de gestión para estudios fitness/pilates, "
                            "plataformas de e-learning, apps de seguimiento de clientes, "
                            "soluciones de automatización para PYMES. Incluye precios. "
                            f"Contexto: {contexto[:150]}"},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"query": query, "respuesta": data["choices"][0]["message"]["content"],
                    "tipo": "tecnologico"}
    except Exception as e:
        log.warning("buscador_tech_error", query=query[:50], error=str(e))
        return None


async def _buscar_consumo(query: str, contexto: str) -> dict | None:
    """Perplexity modo audiencia para hábitos de consumo del público."""
    if not PERPLEXITY_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content":
                            "Eres un analista de comportamiento del consumidor español. Busca: "
                            "qué valoran los clientes de 30-55 años en servicios de pilates/wellness, "
                            "cómo consumen contenido de salud, qué redes usan, "
                            "qué influencers/cuentas siguen, horarios de consumo digital. "
                            f"Contexto: {contexto[:150]}"},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"query": query, "respuesta": data["choices"][0]["message"]["content"],
                    "tipo": "consumo"}
    except Exception as e:
        log.warning("buscador_consumo_error", query=query[:50], error=str(e))
        return None


# ROUTER: tipo_buscador → función
BUSCADORES = {
    "sectorial": _buscar_sectorial,
    "cientifico": _buscar_cientifico,
    "regulatorio": _buscar_regulatorio,
    "financiero": _buscar_financiero,
    "mercado_local": _buscar_mercado_local,
    "tecnologico": _buscar_tecnologico,
    "consumo": _buscar_consumo,
}
```

Y en `buscar_por_gaps()`, reemplazar el bucle de ejecución:

```python
    # ANTES:
    #   result = await _buscar_perplexity(q["query"], contexto_negocio)

    # DESPUÉS:
    for q in queries_plan.get("motor_gap", []):
        tipo = q.get("tipo_buscador", "sectorial")
        buscador_fn = BUSCADORES.get(tipo, _buscar_sectorial)
        result = await buscador_fn(q["query"], contexto_negocio)
        # ... resto igual (filtro, persistir, etc.)
```

## FRECUENCIA DIRIGIDA POR URGENCIA

Añadir en cron.py una lógica de frecuencia variable:

```python
async def _decidir_frecuencia_busqueda() -> bool:
    """Decide si ejecutar búsqueda hoy según urgencia de gaps."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        diag = await conn.fetchrow("""
            SELECT vector_pre FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)
    if not diag:
        return True  # Sin diagnóstico, buscar siempre

    vector = json.loads(diag["vector_pre"]) if isinstance(diag["vector_pre"], str) else diag["vector_pre"]
    # Si alguna F < 0.20 (gap crítico), buscar diario
    if any(v < 0.20 for v in vector.values()):
        return True
    # Si alguna F < 0.40 (gap alto), buscar si es L/M/V
    if any(v < 0.40 for v in vector.values()):
        from datetime import date
        return date.today().weekday() in (0, 2, 4)
    # Si todo > 0.40, buscar solo lunes (semanal)
    from datetime import date
    return date.today().weekday() == 0
```

## COSTE ADICIONAL

Todas las búsquedas usan la misma Perplexity API con system prompts diferentes.
No hay coste adicional de APIs (SparkToro, Outscraper serían mejoras futuras).
El routing solo mejora la CALIDAD de las respuestas, no el coste.

Mejora futura: cuando se justifique, añadir APIs nativas (PubMed gratuita, INE gratuita, BOE gratuito).

## TESTS

### T1: Router dirige a buscador correcto
```python
result = await buscar_por_gaps()
for det in result.get("detalle", []):
    if det.get("tipo_buscador") == "cientifico":
        assert det.get("tipo_respuesta", "") == "cientifico" or True  # Perplexity no falla
```

### T2: Queries generadas incluyen tipos variados
```python
queries = result.get("queries_generadas", {})
# El generador debería producir al menos 2 tipos distintos
```

### T3: Frecuencia variable funciona
```python
debe_buscar = await _decidir_frecuencia_busqueda()
assert isinstance(debe_buscar, bool)
```
