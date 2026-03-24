# B-ORG-COG-PR: Clusters de Pensamiento y Razonamiento — Los agentes que evalúan CÓMO piensa el negocio

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — sin esto el enjambre solo ve QUÉ inteligencias tiene, no CÓMO las procesa
**Modelo:** `anthropic/claude-sonnet-4.6` (7 clusters en paralelo con los 6 INT existentes)
**Dependencia:** B-ORG-UNIFY-01 ejecutado (enjambre v3 funcional)

---

## POR QUÉ FALTAN

Los 6 clusters INT evalúan QUÉ inteligencias usa el negocio. Pero las reglas IC3 (desacople INT-P) e IC5 (pares complementarios P) demuestran que la inteligencia SIN el pensamiento correcto se ABORTA. Y las reglas IC4 (desacople INT-R) e IC6 (validación cruzada R) demuestran que la inteligencia con el razonamiento INCORRECTO concluye MAL.

Ejemplo: el cluster INT detecta que INT-17 (Existencial) está activa. Pero sin un cluster P que verifique que se procesa con P05 (Primeros principios) y NO con P07 (Convergente), no sabemos si INT-17 realmente genera Se o se trivializa.

El diagnóstico de `tcf/repertorio.py` infiere P y R activos, pero con una sola LLM call. Los clusters P y R enriquecen con evidencia del negocio real.

## ARQUITECTURA

Los 7 nuevos clusters se ejecutan EN PARALELO con los 6 clusters INT existentes. No son secuenciales. Todos reciben el mismo input (diagnóstico tcf/ + datos reales) y producen evaluaciones independientes.

```
DIAGNÓSTICO tcf/ + DATOS REALES
         |
    ┌────┴────────────────────────┐
    |                             |
    v                             v
6 Clusters INT (existentes)    7 Clusters P+R (NUEVOS)
    |                             |
    └────────┬────────────────────┘
             v
        COMPOSITOR (integra todo)
```

## CAMBIOS EN enjambre.py

Añadir 7 clusters al dict CLUSTERS existente y ejecutarlos en paralelo con los 6 INT:

```python
# ============================================================
# CLUSTERS DE PENSAMIENTO (4)
# ============================================================

CLUSTERS_P = {
    "p_accion": {
        "ps": "P07(Convergente), P11(Encarnado), P13(Computacional)",
        "lente": "S",
        "angulo": """Evalúa si el negocio EJECUTA con método.
¿Las decisiones se cierran con criterio (P07) o quedan abiertas?
¿Hay acción física/operativa (P11) o solo planificación?
¿Los problemas se descomponen en pasos (P13) o se afrontan en bloque?
Si P07 domina SIN P06 → cierre prematuro (IC5). Señálalo.""",
    },
    "p_cuestionamiento": {
        "ps": "P03(Crítico), P05(Primeros principios), P08(Metacognición)",
        "lente": "Se",
        "angulo": """Evalúa si el negocio CUESTIONA sus premisas.
¿Se evalúa la evidencia antes de decidir (P03) o se actúa por inercia?
¿Se descomponen las premisas hasta lo fundamental (P05) o se aceptan como dadas?
¿El dueño observa su propio proceso de decisión (P08) o está dentro sin ver?
Si NINGUNO de estos P está activo → el negocio es ciego a sus propios sesgos.
Si P08 domina SIN P11 → piensa sobre pensar sin actuar (IC5).""",
    },
    "p_exploracion": {
        "ps": "P01(Lateral), P02(Sistémico), P06(Divergente), P15(Integrativo)",
        "lente": "Se",
        "angulo": """Evalúa si el negocio EXPLORA alternativas.
¿Se buscan soluciones fuera del marco habitual (P01)?
¿Se ven las conexiones entre partes (P02) o se tratan por separado?
¿Se generan muchas opciones antes de elegir (P06) o se va a la primera?
¿Se mantienen opuestos sin elegir hasta que emerge síntesis (P15)?
Si P06 activo SIN P07 → generación infinita sin cierre (IC5).""",
    },
    "p_transferencia": {
        "ps": "P04(Diseño), P09(Prospectivo), P10(Reflexivo), P12(Narrativo), P14(Estratégico)",
        "lente": "Se+C",
        "angulo": """Evalúa si el negocio TRANSFIERE y PROYECTA.
¿Hay ciclo de empatizar→prototipar→testear (P04)?
¿Se piensan escenarios futuros (P09) o solo el presente?
¿Se revisa la experiencia para extraer principios (P10)?
¿Se cuenta la historia del negocio de forma que otros la entiendan (P12)?
¿Se piensa en movimientos y secuencias (P14)?
Si P09 activo SIN P03 → proyección sin cuestionar premisas (extrapolación ciega).""",
    },
}

# ============================================================
# CLUSTERS DE RAZONAMIENTO (3)
# ============================================================

CLUSTERS_R = {
    "r_operativo": {
        "rs": "R01(Deducción), R07(Bayesiano), R09(Eliminación), R12(Transductivo)",
        "lente": "S",
        "angulo": """Evalúa CÓMO el negocio llega a conclusiones OPERATIVAS.
¿Deduce correctamente de premisas (R01) o deduce de premisas falsas (Maginot)?
¿Actualiza creencias con evidencia nueva (R07) o mantiene priors fijos?
¿Descarta opciones sistemáticamente (R09) o elige al azar?
¿Transfiere de casos anteriores (R12) o cada problema es nuevo?
R01 SOLA sin R02/R03 = certeza desde premisas no validadas (IC6).
R07 con priors fijos sin R08 = echo chamber (IC6).""",
    },
    "r_comprension": {
        "rs": "R02(Inducción), R03(Abducción), R05(Causal), R08(Dialéctico), R10(Retroductivo)",
        "lente": "Se",
        "angulo": """Evalúa CÓMO el negocio COMPRENDE lo que pasa.
¿Generaliza desde observaciones (R02) o asume sin datos?
¿Busca la MEJOR explicación para lo observado (R03) o acepta la primera?
¿Establece causas reales (R05) o confunde correlación con causa?
¿Confronta posiciones opuestas para generar síntesis (R08)?
¿Descubre la estructura necesaria detrás de los fenómenos (R10)?
R03 es el razonamiento CENTRAL del diagnóstico ACD. Si está ausente,
el negocio no puede diagnosticar sus propios problemas.
R02 SOLA sin R06 = generalización sin testear excepciones (IC6).""",
    },
    "r_transferencia": {
        "rs": "R04(Analogía), R06(Contrafactual), R11(Modal)",
        "lente": "Se+C",
        "angulo": """Evalúa CÓMO el negocio TRANSFIERE y ANTICIPA.
¿Transfiere conocimiento entre dominios (R04) o cada área es un silo?
¿Evalúa qué pasaría SI... (R06) o solo reacciona a lo que ya pasó?
¿Distingue lo necesario de lo contingente (R11) o trata todo como inevitable?
R04 SOLA sin R09 = transferencia superficial sin depurar diferencias (IC6).
Si R06 está ausente, el negocio es CIEGO al riesgo futuro.
Estas son las herramientas de CONTINUIDAD — sin ellas, el método muere con el fundador.""",
    },
}


# SYSTEM PROMPT para clusters P
SYSTEM_CLUSTER_P = """Eres el cluster de pensamiento {nombre} del enjambre cognitivo.

DIAGNÓSTICO DE CÓDIGO (tcf/):
{diagnostico_resumen}

Tus tipos de pensamiento: {ps}
Lente primaria: {lente}
Tu ángulo: {angulo}

EVALÚA:
1. ¿Estos P están ACTIVOS en este negocio? ¿Hay evidencia en las decisiones observables?
2. ¿Hay PARES COMPLEMENTARIOS (IC5) activos? ¿O un P domina sin su complemento?
3. ¿Hay DESACOPLES INT-P (IC3)? ¿Alguna INT detectada se procesa con un P incompatible?
4. ¿Qué EFECTO tienen estos P (o su ausencia) en las lentes/funciones?

Responde en JSON:
{{
    "cluster": "{nombre}",
    "ps_evaluados": [
        {{"id": "PXX", "activo": true/false, "evidencia": "dato concreto",
          "par_complementario": "PYY presente/ausente",
          "desacople_ic3": "INT-XX procesada con este P es compatible/incompatible"}}
    ],
    "efecto_lentes": {{
        "S": "cómo estos P impulsan o frenan S",
        "Se": "cómo estos P impulsan o frenan Se",
        "C": "cómo estos P impulsan o frenan C"
    }},
    "disfunciones_detectadas": ["ICX: descripción concreta"],
    "insights": ["algo que solo evaluando P se puede ver"]
}}"""


# SYSTEM PROMPT para clusters R
SYSTEM_CLUSTER_R = """Eres el cluster de razonamiento {nombre} del enjambre cognitivo.

DIAGNÓSTICO DE CÓDIGO (tcf/):
{diagnostico_resumen}

Tus tipos de razonamiento: {rs}
Lente primaria: {lente}
Tu ángulo: {angulo}

EVALÚA:
1. ¿Estos R están ACTIVOS en este negocio? ¿Cómo llega a conclusiones?
2. ¿Hay VALIDACIÓN CRUZADA (IC6)? ¿O un R opera aislado amplificando sesgos?
3. ¿Hay DESACOPLES INT-R (IC4)? ¿Alguna INT detectada usa un R incompatible?
4. ¿Qué EFECTO tienen estos R (o su ausencia) en las lentes/funciones?

Responde en JSON:
{{
    "cluster": "{nombre}",
    "rs_evaluados": [
        {{"id": "RXX", "activo": true/false, "evidencia": "dato concreto",
          "validacion_cruzada": "RYY lo valida / opera aislado",
          "desacople_ic4": "INT-XX con este R es compatible/incompatible"}}
    ],
    "efecto_lentes": {{
        "S": "cómo estos R impulsan o frenan S",
        "Se": "cómo estos R impulsan o frenan Se",
        "C": "cómo estos R impulsan o frenan C"
    }},
    "disfunciones_detectadas": ["ICX: descripción concreta"],
    "insights": ["algo que solo evaluando R se puede ver"]
}}"""
```

## INTEGRACIÓN EN ejecutar_enjambre()

En la sección donde se lanzan los 6 clusters INT en paralelo, AÑADIR los 7 P+R:

```python
    # 6 clusters INT (existentes) + 4 clusters P + 3 clusters R = 13 en paralelo
    tareas = []

    # Clusters INT (existentes)
    for cl_id, cl_def in CLUSTERS.items():
        prompt = SYSTEM_CLUSTER.format(...)
        tareas.append(_call_cluster(prompt, contexto, f"Cluster-INT-{cl_id}"))

    # Clusters P (NUEVOS)
    for cl_id, cl_def in CLUSTERS_P.items():
        prompt = SYSTEM_CLUSTER_P.format(
            nombre=cl_id, diagnostico_resumen=diagnostico_resumen,
            ps=cl_def["ps"], lente=cl_def["lente"], angulo=cl_def["angulo"])
        tareas.append(_call_cluster(prompt, contexto, f"Cluster-P-{cl_id}"))

    # Clusters R (NUEVOS)
    for cl_id, cl_def in CLUSTERS_R.items():
        prompt = SYSTEM_CLUSTER_R.format(
            nombre=cl_id, diagnostico_resumen=diagnostico_resumen,
            rs=cl_def["rs"], lente=cl_def["lente"], angulo=cl_def["angulo"])
        tareas.append(_call_cluster(prompt, contexto, f"Cluster-R-{cl_id}"))

    resp_all = await asyncio.gather(*tareas)
    # Separar resultados en 3 dicts
    resultados["clusters_int"] = {k: v for k, v in zip(CLUSTERS.keys(), resp_all[:6])}
    resultados["clusters_p"] = {k: v for k, v in zip(CLUSTERS_P.keys(), resp_all[6:10])}
    resultados["clusters_r"] = {k: v for k, v in zip(CLUSTERS_R.keys(), resp_all[10:])}
```

## COSTE ADICIONAL

7 clusters × claude-sonnet-4.6 (~$0.05/call) = ~$0.35/ejecución
Total enjambre: $0.30 (INT) + $0.35 (P+R) = **$0.65/ejecución** (~$2.60/mes)

## TESTS

### T1: Clusters P detectan pares complementarios (IC5)
```python
result = await ejecutar_enjambre()
for cl_id, cl_resp in result["resultados"]["clusters_p"].items():
    if "error" not in cl_resp:
        for p_eval in cl_resp.get("ps_evaluados", []):
            assert "par_complementario" in p_eval
```

### T2: Clusters R detectan validación cruzada (IC6)
```python
for cl_id, cl_resp in result["resultados"]["clusters_r"].items():
    if "error" not in cl_resp:
        for r_eval in cl_resp.get("rs_evaluados", []):
            assert "validacion_cruzada" in r_eval
```

### T3: 13 clusters ejecutan en paralelo
```python
assert result["clusters_ejecutados"] >= 10  # Al menos 10 de 13 OK
assert result["tiempo_total_s"] < 90  # Paralelo, no secuencial
```
