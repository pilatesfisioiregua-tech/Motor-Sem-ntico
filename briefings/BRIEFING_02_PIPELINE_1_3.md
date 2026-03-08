# BRIEFING_02 — PIPELINE CAPAS 0-3 (COMPILACIÓN)

**Objetivo:** Detector de Huecos (código puro), Router (Sonnet), Compositor (NetworkX), Generador (templates). Las capas que "compilan" el algoritmo antes de ejecutar.
**Pre-requisito:** BRIEFING_00 y BRIEFING_01 completados.
**Output:** Dado un input en lenguaje natural, se detectan huecos, seleccionan inteligencias, y se genera un plan de ejecución.

---

## CAPA 0: DETECTOR DE HUECOS (src/pipeline/detector_huecos.py)

### Qué hace
Analiza el input en lenguaje natural ANTES del router. Detecta qué falta (verbos sin objeto, creencias sin evidencia, etc.) usando las 8 operaciones sintácticas del Marco Lingüístico. Output: lista tipificada de huecos que informa al router sobre qué inteligencias priorizar.

### Lógica (código puro, $0, ~200ms)

```python
"""Capa 0: Detector de huecos sintácticos. Código puro, $0."""
import re
import json
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class Hueco:
    tipo: str           # 'verbo_sin_objeto', 'creencia_sin_evidencia', etc.
    operacion: str      # qué operación sintáctica falta
    fragmento: str      # el fragmento del input que lo evidencia
    capa: str           # a qué capa del sistema afecta
    inteligencia_sugerida: str | None = None  # qué INT activar

@dataclass
class DetectorResult:
    huecos: list[Hueco]
    perfil_acoples: dict[str, int]  # {Y: 3, PERO: 2, ...}
    diagnostico_acople: str         # "dominado por condicionales = rígido"
    inteligencias_sugeridas: list[str]  # INTs sugeridas por los huecos


# Mapeo operación → inteligencias relevantes
OPERACION_TO_INT = {
    'transitividad': ['INT-03', 'INT-05'],      # verbo sin objeto → estructural/estratégica
    'subordinacion_causal': ['INT-01', 'INT-02'], # sin porque → cuantitativa
    'subordinacion_condicional': ['INT-07', 'INT-13'],  # sin si → financiera/prospectiva
    'cuantificacion': ['INT-01', 'INT-07'],       # sin cuánto → cuantitativa
    'modificacion': ['INT-15', 'INT-09'],         # sin cualificación → estética/lingüística
    'conexion': ['INT-08', 'INT-06'],             # acoples ocultos → social/política
    'predicacion': ['INT-16', 'INT-05'],          # estado sin acción → constructiva/estratégica
    'transformacion': ['INT-14', 'INT-12'],       # categorías fijas → divergente/narrativa
}

# Conjunciones y sus patrones
CONJUNCIONES = {
    'y': 'Y', 'e': 'Y',
    'pero': 'PERO', 'sin embargo': 'PERO', 'no obstante': 'PERO',
    'aunque': 'AUNQUE', 'a pesar de': 'AUNQUE',
    'porque': 'PORQUE', 'ya que': 'PORQUE', 'dado que': 'PORQUE',
    'si': 'SI', 'en caso de': 'SI',
    'para': 'PARA', 'con el fin de': 'PARA', 'a fin de': 'PARA',
}


def detectar_huecos(input_text: str, marco: dict) -> DetectorResult:
    """Detecta huecos sintácticos en el input. Código puro."""
    huecos = []
    
    oraciones = re.split(r'[.!?]+', input_text)
    oraciones = [o.strip() for o in oraciones if o.strip()]
    
    for oracion in oraciones:
        palabras = oracion.lower().split()
        
        # 1. Transitividad: verbos sin objeto claro
        verbos_transitivos = ['quiere', 'busca', 'necesita', 'planea', 'considera',
                              'piensa', 'decide', 'elige', 'lidera', 'gestiona', 'dirige']
        for verbo in verbos_transitivos:
            if verbo in palabras:
                idx = palabras.index(verbo)
                # Si el verbo está al final o seguido de punto/conjunción
                if idx >= len(palabras) - 2:
                    huecos.append(Hueco(
                        tipo='verbo_sin_objeto',
                        operacion='transitividad',
                        fragmento=oracion,
                        capa='funciones',
                        inteligencia_sugerida='INT-03'
                    ))
        
        # 2. Cuantificación ausente: magnitudes sin número
        cuant_vagas = ['mucho', 'poco', 'bastante', 'algo', 'varios', 'algunos']
        for vago in cuant_vagas:
            if vago in palabras:
                huecos.append(Hueco(
                    tipo='cuantificacion_vaga',
                    operacion='cuantificacion',
                    fragmento=oracion,
                    capa='lentes',
                    inteligencia_sugerida='INT-01'
                ))
                break
        
        # 3. Predicación sin causa: afirmaciones sin subordinación causal
        # (se detecta a nivel global, no por oración)
    
    # 4. Perfil de acoples (análisis global del input)
    text_lower = input_text.lower()
    perfil = {}
    for patron, tipo in CONJUNCIONES.items():
        count = text_lower.count(patron)
        if count > 0:
            perfil[tipo] = perfil.get(tipo, 0) + count
    
    # 5. Diagnóstico por perfil de acoples
    diagnostico = diagnosticar_perfil(perfil)
    
    # 6. Subordinación causal ausente
    tiene_porque = any(c in text_lower for c in ['porque', 'ya que', 'dado que', 'debido a'])
    if not tiene_porque and len(oraciones) > 2:
        huecos.append(Hueco(
            tipo='sin_causalidad',
            operacion='subordinacion_causal',
            fragmento='(input completo)',
            capa='creencias',
            inteligencia_sugerida='INT-01'
        ))
    
    # 7. Finalidad ausente
    tiene_para = any(c in text_lower for c in ['para', 'con el fin de', 'a fin de'])
    if not tiene_para and len(oraciones) > 1:
        huecos.append(Hueco(
            tipo='sin_finalidad',
            operacion='subordinacion_final',
            fragmento='(input completo)',
            capa='reglas',
            inteligencia_sugerida='INT-17'
        ))
    
    # 8. Recoger inteligencias sugeridas (dedup, ordenadas por frecuencia)
    sugeridas = {}
    for h in huecos:
        if h.inteligencia_sugerida:
            sugeridas[h.inteligencia_sugerida] = sugeridas.get(h.inteligencia_sugerida, 0) + 1
        if h.operacion in OPERACION_TO_INT:
            for int_id in OPERACION_TO_INT[h.operacion]:
                sugeridas[int_id] = sugeridas.get(int_id, 0) + 1
    
    inteligencias_sugeridas = sorted(sugeridas.keys(), key=lambda k: sugeridas[k], reverse=True)
    
    return DetectorResult(
        huecos=huecos,
        perfil_acoples=perfil,
        diagnostico_acople=diagnostico,
        inteligencias_sugeridas=inteligencias_sugeridas[:5]
    )


def diagnosticar_perfil(perfil: dict[str, int]) -> str:
    """Diagnóstico basado en el perfil de acoples."""
    total = sum(perfil.values())
    if total == 0:
        return "Sin acoples explícitos — relaciones implícitas no verificadas"
    
    dominante = max(perfil, key=perfil.get) if perfil else None
    
    diagnosticos = {
        'SI': 'Dominado por condicionales — sistema rígido/frágil',
        'AUNQUE': 'Dominado por concesivas — fugas toleradas',
        'PERO': 'Dominado por tensiones — fricción activa',
        'PORQUE': 'Dominado por causales — cadena causal explícita',
        'Y': 'Dominado por sinergias — puede ocultar tensiones',
        'PARA': 'Dominado por finalidad — orientado pero puede ser rígido',
    }
    
    return diagnosticos.get(dominante, "Perfil mixto")
```

### Interfaz

```python
async def detect(input_text: str) -> DetectorResult:
    """Ejecuta detección de huecos. Síncrono envuelto en async para consistencia."""
    from src.meta_red import load_marco_linguistico
    marco = load_marco_linguistico()
    return detectar_huecos(input_text, marco)
```

---

## CAPA 1: ROUTER (src/pipeline/router.py)

### Qué hace
Recibe el input del usuario y selecciona las 4-5 inteligencias más relevantes usando Sonnet.

### Lógica

1. Construye un prompt con: el input del usuario + el catálogo de firmas de las 18 inteligencias + las reglas de selección
2. Sonnet devuelve un JSON con las inteligencias seleccionadas, ordenadas por relevancia
3. Se aplican las reglas obligatorias post-selección (núcleo irreducible, etc.)

### Prompt del Router

```python
ROUTER_SYSTEM = """Eres un router de inteligencias. Tu trabajo es seleccionar las 4-5 inteligencias más relevantes para analizar el input del usuario.

CATÁLOGO DE INTELIGENCIAS:
{catalogo}

REGLAS OBLIGATORIAS:
1. SIEMPRE incluir al menos 1 de {{INT-01, INT-02}} (cuantitativa) + 1 de {{INT-08, INT-17}} (humana) + INT-16 (constructiva). Sin este triángulo, el análisis está incompleto.
2. Priorizar pares de máximo diferencial: INT-01×INT-08 (0.95), INT-07×INT-17 (0.93), INT-02×INT-15 (0.90).
3. Sweet spot: 4-5 inteligencias. Nunca menos de 3. Nunca más de 6.
4. Evitar pares redundantes del mismo cluster: INT-03+INT-04 (sistémicas), INT-08+INT-12 (interpretativas), INT-17+INT-18 (existenciales).

MODO: {modo}
- análisis: 4-5 inteligencias, máximo diferencial
- generación: priorizar INT-14, INT-15, INT-09 (creativas)
- conversación: 2-3 inteligencias, las más directamente relevantes
- confrontación: incluir INT-17 y/o INT-18 (frontera)

Responde SOLO con un JSON válido, sin markdown, sin explicación:
{{
  "inteligencias": ["INT-XX", "INT-YY", ...],
  "razon": "explicación breve de la selección",
  "pares_complementarios": [["INT-XX", "INT-YY"], ...],
  "descartadas": ["INT-ZZ", ...]
}}"""
```

### Formato del catálogo (se genera dinámicamente desde inteligencias.json)

```
INT-01 | Lógico-Matemática | Firma: Contradicción formal demostrable entre premisas | Punto ciego: Lo ambiguo
INT-02 | Computacional | Firma: Dato trivializador ausente + atajo algorítmico | Punto ciego: Lo no-computable
...
```

### Post-procesamiento (código puro, reglas obligatorias)

```python
def enforce_rules(selected: list[str], modo: str) -> list[str]:
    """Aplica reglas obligatorias sobre la selección del LLM."""
    
    # Regla 1: Núcleo irreducible
    has_quant = any(i in selected for i in ['INT-01', 'INT-02'])
    has_human = any(i in selected for i in ['INT-08', 'INT-17'])
    has_constructive = 'INT-16' in selected
    
    if not has_quant:
        selected.append('INT-01')  # Default cuantitativa
    if not has_human:
        selected.append('INT-08')  # Default humana
    if not has_constructive and modo != 'conversacion':
        selected.append('INT-16')
    
    # Regla 3: Límites
    if len(selected) > 6:
        # Quitar las de menor relevancia (las añadidas al final)
        selected = selected[:6]
    if len(selected) < 3:
        # Esto no debería pasar con las reglas anteriores
        pass
    
    # Regla: Confrontación requiere existenciales
    if modo == 'confrontacion':
        if 'INT-17' not in selected and 'INT-18' not in selected:
            selected.append('INT-17')
    
    return selected
```

### Configuración por modo

| Modo | K inteligencias | Temperature | Forzar |
|------|----------------|-------------|--------|
| análisis | 5 | 0.2 | Núcleo irreducible |
| generación | 4 | 0.4 | INT-14 o INT-15 |
| conversación | 3 | 0.1 | Solo cuantitativa + humana |
| confrontación | 5 | 0.3 | INT-17 o INT-18 |

### Interfaz

```python
async def route(input_text: str, contexto: str | None, modo: str, 
                forzadas: list[str], excluidas: list[str],
                huecos: DetectorResult | None = None) -> RouterResult:
    """Selecciona inteligencias para el input dado. Usa huecos de Capa 0 si disponibles."""
    # Si hay huecos, inyectar las inteligencias sugeridas como señal al LLM
    # y como candidatas forzadas blandas (se incluyen si no contradicen reglas)
    # Returns RouterResult con: inteligencias, pares_complementarios, descartadas, cost, time
```

---

## CAPA 2: COMPOSITOR (src/pipeline/compositor.py)

### Qué hace
Recibe la lista de inteligencias seleccionadas y genera el algoritmo óptimo de operaciones (composiciones, fusiones, orden).

### Lógica (código puro, NetworkX, $0)

1. Carga el grafo de aristas (diferencial, composición, fusión) desde DB o memoria
2. Extrae el subgrafo relevante (solo las inteligencias seleccionadas)
3. Aplica las 13 reglas del compilador para determinar:
   - Qué pares componer (A→B)
   - Qué pares fusionar (A|B)
   - En qué orden ejecutar
   - Cuántas pasadas por inteligencia

### Estructura de datos

```python
from dataclasses import dataclass, field

@dataclass
class Operacion:
    tipo: str  # 'individual', 'composicion', 'fusion'
    inteligencias: list[str]  # 1 para individual, 2 para composición/fusión
    orden: int  # secuencia de ejecución
    pasadas: int  # 1 o 2
    direccion: str | None = None  # 'INT-01→INT-08' para composiciones

@dataclass  
class Algoritmo:
    inteligencias: list[str]
    operaciones: list[Operacion]
    loops: dict[str, int]  # {INT-XX: num_pasadas}
    paralelizable: list[list[str]]  # grupos ejecutables en paralelo
```

### Algoritmo del compositor

```python
import networkx as nx

def componer(inteligencias: list[str], aristas: list[dict], modo: str) -> Algoritmo:
    """Genera algoritmo óptimo desde inteligencias + grafo de aristas."""
    
    G = nx.DiGraph()
    
    # 1. Construir subgrafo con inteligencias seleccionadas
    for a in aristas:
        if a['origen'] in inteligencias and a['destino'] in inteligencias:
            G.add_edge(a['origen'], a['destino'], 
                       tipo=a['tipo'], peso=a['peso'],
                       direccion=a.get('direccion_optima'),
                       emergente=a.get('hallazgo_emergente'))
    
    operaciones = []
    orden = 0
    
    # 2. Identificar pares de alto diferencial para componer
    composiciones = [
        (a['origen'], a['destino'], a['peso'], a.get('direccion_optima'))
        for a in aristas
        if a['tipo'] in ('composicion', 'diferencial')
        and a['origen'] in inteligencias 
        and a['destino'] in inteligencias
        and a['peso'] >= 0.85
    ]
    composiciones.sort(key=lambda x: x[2], reverse=True)
    
    # 3. Identificar pares para fusionar
    fusiones = [
        (a['origen'], a['destino'], a['peso'])
        for a in aristas
        if a['tipo'] == 'fusion'
        and a['origen'] in inteligencias 
        and a['destino'] in inteligencias
    ]
    
    usadas = set()
    
    # 4. Regla 4: Formal primero en composiciones
    for origen, destino, peso, direccion in composiciones[:2]:  # Max 2 composiciones
        if origen in usadas and destino in usadas:
            continue
        operaciones.append(Operacion(
            tipo='composicion',
            inteligencias=[origen, destino],
            orden=orden,
            pasadas=2 if modo in ('analisis', 'confrontacion') else 1,
            direccion=direccion or f'{origen}→{destino}'
        ))
        usadas.add(origen)
        usadas.add(destino)
        orden += 1
    
    # 5. Fusiones para pares no usados en composición
    for origen, destino, peso in fusiones:
        if origen in usadas or destino in usadas:
            continue
        operaciones.append(Operacion(
            tipo='fusion',
            inteligencias=[origen, destino],
            orden=orden,
            pasadas=1
        ))
        usadas.add(origen)
        usadas.add(destino)
        orden += 1
    
    # 6. Individuales para las que sobran
    for intel in inteligencias:
        if intel not in usadas:
            operaciones.append(Operacion(
                tipo='individual',
                inteligencias=[intel],
                orden=orden,
                pasadas=2 if modo in ('analisis', 'confrontacion') else 1
            ))
            usadas.add(intel)
            orden += 1
    
    # 7. Loops
    loops = {}
    for op in operaciones:
        for intel in op.inteligencias:
            loops[intel] = op.pasadas
    
    # 8. Paralelización (Regla 9: fusiones paralelizables ~70%)
    paralelos = []
    independientes = [op for op in operaciones if op.tipo == 'individual']
    if len(independientes) >= 2:
        paralelos.append([op.inteligencias[0] for op in independientes])
    
    return Algoritmo(
        inteligencias=inteligencias,
        operaciones=operaciones,
        loops=loops,
        paralelizable=paralelos
    )
```

### Interfaz

```python
async def compose(inteligencias: list[str], modo: str) -> Algoritmo:
    """Genera algoritmo óptimo para las inteligencias dadas."""
    aristas = await fetch_aristas()  # o desde caché en memoria
    return componer(inteligencias, aristas, modo)
```

---

## CAPA 3: GENERADOR (src/pipeline/generador.py)

### Qué hace
Recibe el algoritmo del compositor y genera los prompts exactos que se enviarán a los LLMs.

### Lógica (código puro, templates, $0)

1. Carga inteligencias.json en memoria (al arrancar)
2. Para cada operación del algoritmo, genera el prompt correspondiente
3. El prompt incluye: las preguntas de la inteligencia + el input del usuario + contexto

### Templates

```python
TEMPLATE_INDIVIDUAL = """Eres la inteligencia {nombre} ({id}).

Tu firma: {firma}
Tu punto ciego: {punto_ciego}

Aplica tu red de preguntas al siguiente caso. Sigue EXACTAMENTE esta secuencia:

1. EXTRAER — {extraer_nombre}:
{extraer_preguntas}

2. CRUZAR — {cruzar_nombre}:
{cruzar_preguntas}

3. LENTES:
{lentes_preguntas}

4. INTEGRAR: {integrar}

5. ABSTRAER: {abstraer}

6. FRONTERA: {frontera}

CASO:
{input}

{contexto_extra}

Responde de forma estructurada. Para cada paso, contesta CADA pregunta. No saltes ninguna.
Al final, genera un JSON con:
{{
  "firma_caso": "la firma específica de este caso en 1-2 frases",
  "hallazgos": ["hallazgo 1", "hallazgo 2", ...],
  "puntos_ciegos": ["lo que esta inteligencia NO puede ver"],
  "accion_prioritaria": "la acción más importante que sugiere este análisis",
  "confianza": 0.0-1.0
}}"""

TEMPLATE_COMPOSICION = """Eres la inteligencia {nombre_b} ({id_b}).

Tu firma: {firma_b}
Tu punto ciego: {punto_ciego_b}

Se te proporciona el ANÁLISIS PREVIO realizado por {nombre_a} ({id_a}).
Tu trabajo es aplicar tus preguntas SOBRE ESE ANÁLISIS, no sobre el caso original directamente.

ANÁLISIS PREVIO ({id_a}):
{output_a}

CASO ORIGINAL (para referencia):
{input}

Aplica tu red de preguntas al análisis previo:
{preguntas_b}

Presta especial atención a:
- Lo que {id_a} NO pudo ver (sus puntos ciegos: {punto_ciego_a})
- Lo que EMERGE al cruzar su análisis con tu lente
- Contradicciones entre lo que {id_a} encontró y lo que tú ves

Responde con el mismo formato JSON que el análisis previo, más:
{{
  "hallazgo_emergente": "lo que SOLO aparece al cruzar {id_a} con {id_b}",
  "contradicciones": ["contradicción encontrada con el análisis previo"]
}}"""

TEMPLATE_FUSION = """Tienes dos análisis del MISMO caso, realizados por dos inteligencias diferentes.

ANÁLISIS 1 ({id_a} — {nombre_a}):
{output_a}

ANÁLISIS 2 ({id_b} — {nombre_b}):
{output_b}

Tu trabajo es FUSIONAR ambos análisis:
1. ¿Qué dicen los dos que coincide?
2. ¿Dónde se contradicen?
3. ¿Qué emerge SOLO al juntar ambos que ninguno veía solo?
4. ¿Cuál es la síntesis que respeta lo mejor de ambos?

CASO ORIGINAL:
{input}

Responde con:
{{
  "convergencias": ["punto donde ambos coinciden"],
  "divergencias": ["punto donde se contradicen"],
  "emergente": "lo que SOLO aparece al fusionar",
  "sintesis": "la síntesis integradora",
  "firma_combinada": "firma del par fusionado en 1-2 frases"
}}"""

TEMPLATE_LOOP = """Eres la inteligencia {nombre} ({id}).

Se te proporciona tu PROPIO ANÁLISIS PREVIO de este caso.
Tu trabajo es re-examinar tu análisis con ojos frescos.

TU ANÁLISIS PREVIO:
{output_previo}

Preguntas de meta-diagnóstico:
- ¿Tu análisis tiene sesgos propios de tu forma de pensar?
- ¿Hay algo que diste por hecho sin verificar?
- ¿Tu punto ciego ({punto_ciego}) afectó lo que encontraste?
- ¿Hay hallazgos genuinamente nuevos que emergen al re-examinar?

Responde SOLO con lo NUEVO. No repitas lo anterior.
{{
  "hallazgos_nuevos": ["genuinamente nuevo, no repetido"],
  "sesgos_detectados": ["sesgo de tu propio análisis"],
  "correccion": "si algo del análisis previo era erróneo"
}}"""
```

### Función principal

```python
def generar_prompts(algoritmo: Algoritmo, input_text: str, 
                    contexto: str | None, inteligencias_data: dict) -> list[PromptPlan]:
    """Genera los prompts exactos para cada operación del algoritmo."""
    prompts = []
    for operacion in sorted(algoritmo.operaciones, key=lambda o: o.orden):
        if operacion.tipo == 'individual':
            intel = inteligencias_data[operacion.inteligencias[0]]
            prompt = format_individual(intel, input_text, contexto)
            prompts.append(PromptPlan(
                operacion=operacion,
                prompt_system="",
                prompt_user=prompt,
                modelo=MODEL_EXTRACTOR,  # Haiku para extracción
                depende_de=[]
            ))
        elif operacion.tipo == 'composicion':
            # El segundo depende del output del primero
            id_a, id_b = operacion.inteligencias
            prompts.append(PromptPlan(
                operacion=operacion,
                prompt_system="",
                prompt_user=None,  # Se genera dinámicamente con output_a
                modelo=MODEL_EXTRACTOR,
                depende_de=[id_a],
                template='composicion',
                intel_a=inteligencias_data[id_a],
                intel_b=inteligencias_data[id_b]
            ))
        elif operacion.tipo == 'fusion':
            id_a, id_b = operacion.inteligencias
            prompts.append(PromptPlan(
                operacion=operacion,
                prompt_system="",
                prompt_user=None,  # Se genera con ambos outputs
                modelo=MODEL_INTEGRATOR,  # Sonnet para fusión
                depende_de=[id_a, id_b],
                template='fusion',
                intel_a=inteligencias_data[id_a],
                intel_b=inteligencias_data[id_b]
            ))
    
    # Añadir loop tests (pasada 2) si procede
    for intel_id, pasadas in algoritmo.loops.items():
        if pasadas >= 2:
            intel = inteligencias_data[intel_id]
            prompts.append(PromptPlan(
                operacion=Operacion(tipo='loop', inteligencias=[intel_id],
                                   orden=999, pasadas=1),
                prompt_system="",
                prompt_user=None,  # Se genera con output de pasada 1
                modelo=MODEL_EXTRACTOR,
                depende_de=[intel_id],
                template='loop',
                intel_data=intel
            ))
    
    return prompts
```

---

## VERIFICACIÓN

1. Test unitario detector: dado "Quiero expandir mi negocio", debe detectar al menos 1 hueco (sin_finalidad y/o cuantificacion_vaga) y sugerir inteligencias
2. Test unitario router: dado un input tipo "Mi socio quiere vender su parte", el router debe devolver ≥4 inteligencias incluyendo al menos 1 cuantitativa, 1 humana y INT-16
3. Test unitario compositor: dadas [INT-01, INT-08, INT-07, INT-16, INT-17], debe generar un algoritmo con al menos 1 composición (INT-01→INT-08 o similar)
4. Test unitario generador: dado un algoritmo con 3 operaciones, debe generar 3+ prompts con todas las preguntas de cada inteligencia
5. Detector y compositor son código puro (sin LLM). Router se puede testear con mock.
