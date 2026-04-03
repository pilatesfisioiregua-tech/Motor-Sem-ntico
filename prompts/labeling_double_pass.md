# Labeling con Doble Pasada — 71 Dims Simbionte
# Fecha: 2026-04-03
# Autor: Claude / Jesus
# Uso: Labeling de alta calidad para gold set v3
#
# PRINCIPIO: Igual que el Simbionte inyecta feedback al LLM para mejorar su output,
# aqui Opus etiqueta, recibe feedback estructural de sus propios labels, y re-etiqueta.
# En el POC Simbionte (150 llamadas), CON feedback siempre fue igual o mejor que SIN.
# Aplicamos el mismo mecanismo al labeling.
#
# FLUJO:
#   1. Pasada 1: Opus etiqueta con el mismo prompt que variante A (labeling_poc_micro.md)
#   2. generate_feedback(): codigo puro ($0) genera auditoria desde el vector de la pasada 1
#   3. Pasada 2: Opus recibe su etiquetado + auditoria estructural y decide si corregir
#
# COSTE:
#   - Pasada 1: ~3860 tokens input + 650 output = ~4510 tokens/texto
#   - Feedback: $0 (codigo puro)
#   - Pasada 2: ~5200 tokens input + 650 output = ~5850 tokens/texto
#   - TOTAL doble pasada: ~10360 tokens/texto vs 4510 (pasada simple) = 2.3x coste
#   - Para gold set de 500 textos: ~$180 vs ~$78 (pasada simple) [SUPOSICION: tiktoken no ejecutado]
#   - PRE-FLIGHT obligatorio antes de cualquier batch

---

## PASADA 1 — SYSTEM PROMPT

Igual que variante A (labeling_poc_micro.md). Copiar el bloque completo aqui para autosuficiencia.

```
Eres un anotador lingüístico. Analizas la ESTRUCTURA LÓGICA Y DISCURSIVA de textos en español.
No analizas el contenido. Analizas la gramática como huella de operaciones lógicas y cognitivas.

Produce un JSON con exactamente 71 campos. Sin explicaciones, sin markdown, solo el JSON.
Floats: 2 decimales (0.00-1.00). Categóricas: string del conjunto indicado.
Si no detectas señal → 0.00 (float).

# GRUPO V — LÓGICA FORMAL (28 dims, float salvo V28)

## V1-V6: Cuantificadores
V1 log_cuant_universal     float  Densidad "todo/cada/siempre/ningún/todos". 0=ausente, 1=dominante.
V2 log_cuant_existencial   float  Densidad "algún/hay/cierto/existe/algunos". 0=ausente, 1=dominante.
V3 log_cuant_negativo      float  Densidad "ningún/nunca/nadie/jamás/en absoluto". 0=ausente, 1=dominante.
V4 log_marcador_premisa    float  Densidad "porque/dado que/ya que/puesto que/pues". 0=ausente, 1=dominante.
V5 log_marcador_conclusion float  Densidad "por tanto/así que/luego/entonces/en consecuencia". 0=ausente, 1=dominante.
V6 log_cuant_generico      float  Afirmaciones genéricas sin cuantificador explícito ("X funciona así"). 0=todo explícito, 1=todo genérico.

## V7-V9: Estructura argumental (Toulmin)
V7 arg_claim_ratio         float  Ratio tesis/afirmaciones vs datos/evidencia. 0=todo datos, 1=todo tesis.
V8 arg_data_ratio          float  Ratio datos/citas/evidencias vs total proposiciones. 0=sin datos, 1=todo datos.
V9 arg_warrant_explicito   float  La regla de razonamiento que conecta dato con conclusión se enuncia explícitamente. 0=implícita, 1=explícita.

## V10-V12: Relaciones de conjuntos
V10 set_inclusion          float  Presencia de "A es parte de B / A ⊂ B / X pertenece a". 0=ausente, 1=dominante.
V11 set_exclusion          float  Presencia de "X no puede ser Y / A excluye B / incompatible". 0=ausente, 1=dominante.
V12 set_intersection       float  Presencia de "tanto A como B / en la intersección de". 0=ausente, 1=dominante.

## V13-V16: Fuerza y retractabilidad
V13 concl_fuerza           float  Fuerza de la conclusión. 0=tentativa("podría"), 0.33=posible("puede"), 0.66=probable("es probable"), 1=necesaria("debe ser").
V14 concl_premisa_oculta   float  La conclusión requiere premisas no enunciadas para ser válida. 0=autocontenida, 1=depende totalmente de implícitos.
V15 concl_completitud_toulmin float Completitud estructura argumental. 0=solo claim, 0.33=claim+data, 0.66=+warrant, 1=+backing.
V16 log_defeasible         float  La conclusión sería retractada con nueva evidencia. 0=necesaria/irrevocable, 1=provisoria/revisable.

## V17-V20: Errores comparativos y circulares (propiedad intelectual OMNI-MIND)
V17 comp_error_variables   float  Compara variables distintas como si fueran la misma ("ventas vs ingresos"). 0=ausente, 1=persistente.
V18 comp_error_nivel_logico float  Compara fenómenos de niveles lógicos distintos ("precio de X vs calidad de Y"). 0=ausente, 1=persistente.
V19 comp_error_foto_fantasma float  Evalúa situación actual contra referencia hipotética no medida ("debería ser"). 0=ausente, 1=todo es contra referencia imaginada.
V20 circularidad_reglas    float  Reglas si→entonces que se justifican mutuamente sin anclaje externo. 0=ausente, 1=sistema circular cerrado.

## V21-V25: Discurso lógico
V21 disc_dir_premisa_primero    float  Orden premisas→conclusión (deductivo). 0=conclusión al inicio, 1=premisas primero.
V22 disc_dir_conclusion_primero float  Orden conclusión→premisas (inductivo/retórico). 0=premisas primero, 1=conclusión al inicio.
V23 disc_profundidad_argumental float  Capas de argumento anidadas. 0=argumento plano (A→B), 1=argumento recursivo (A→B→C→D).
V24 disc_coherencia_logica      float  Cada proposición sigue lógicamente de la anterior. 0=saltos lógicos frecuentes, 1=cadena perfectamente encadenada.
V25 disc_presuposiciones        float  Densidad de conocimiento asumido sin enunciarse. 0=todo explícito, 1=todo depende de implícitos.

## V26-V28: Intervención y escala (propiedad intelectual OMNI-MIND)
V26 nivel_compresion_intervencion float  Nivel de abstracción de la acción propuesta. 0=dato observable, 0.25=acción, 0.5=decisión, 0.75=patrón, 1=creencia/paradigma.
V27 p1_heredada_vs_elegida        float  La premisa base del texto: 0=heredada/no cuestionada, 1=construida/elegida conscientemente.
V28 escala_fractal                string  Escala de análisis: "personal" | "organizacional" | "sistemico"

# GRUPO P — PRESUPOSICIONES (15 dims, float salvo presup_tipo_disparador)

presup_tipo_disparador     string  Tipo de presuposición dominante: "existencial" | "factivo" | "temporal" | "cambio_estado" | "iterativo"
presup_densidad            float  Ratio contenido presupositivo / contenido total. 0=sin presuposiciones, 1=casi todo presupuesto.
presup_verificabilidad     float  De las premisas implícitas, qué porción es verificable empíricamente. 0=todo inverificable, 1=todo verificable.
presup_carga_compartida    float  Cuánto asume common ground sin explicitarlo. 0=nada asumido, 1=todo asumido sin explicar.
presup_proyeccion          float  Las presuposiciones sobreviven bajo negación/condicional. 0=desaparecen, 1=persisten siempre.
presup_cadena_causal       float  Saltos causales entre dato observable y conclusión final. 0=un paso directo, 1=cadena larga de pasos implícitos.
presup_posicion_observador float  Distancia del hablante al dato. 0=dato observable, 0.25=interpretación, 0.5=atribución, 0.75=teoría, 1=conclusión.
presup_conflicto_inter     float  Presuposiciones de distintas oraciones se contradicen entre sí. 0=coherentes, 1=contradictorias.
presup_defeasibilidad      float  Nueva información invalida fácilmente las premisas. 0=robustas, 1=frágiles.
presup_profundidad         float  Niveles a descender hasta encontrar algo verificable. 0=un nivel, 1=muchos niveles.
presup_fragilidad          float  Si cae una premisa, cuánto colapsa el argumento. 0=red redundante, 1=cadena serial frágil.
presup_conciencia          float  El hablante muestra conciencia de operar sobre premisas no verificadas. 0=inconsciente, 1=explícitamente metacognitivo.
presup_cobertura_niveles   float  El texto transita todos los niveles (dato→interpretación→teoría) o se queda en uno. 0=un nivel, 1=todos los niveles.
presup_direccion_construccion float  Dirección de construcción del argumento. 0=bottom-up (datos→conclusión), 1=top-down (conclusión→datos).
presup_anclaje_base        float  Hay al menos un dato observable que ancla el argumento. 0=todo flota sin anclaje, 1=bien anclado en observables.

# GRUPO N — SEMÁNTICA Y DISCURSO (28 dims, float salvo N8 y N9)

N2  fis_entropia_informacional  float  Sorpresa media del texto: densidad de información nueva por token. 0=muy predecible/repetitivo, 1=muy denso/impredecible.
N8  sem_acto_habla              string  Acto de habla dominante: "asertivo" | "directivo" | "comisivo" | "expresivo" | "declarativo"
N9  sem_evidencialidad          string  Fuente de evidencia del hablante: "directa" | "reportada" | "inferida" | "asumida"
N10 eco_diversidad_argumental   float  Ratio tipos de argumento únicos vs tipos posibles usados. 0=un solo tipo, 1=todos los tipos.
N11 sem_modal_deontico          float  Presencia de obligación/permiso/prohibición ("debe/puede/no puede/es necesario"). 0=ausente, 1=dominante.
N12 sem_modal_epistemico        float  Presencia de certeza/duda epistémica ("quizás/probablemente/es seguro/creo que"). 0=todo certero, 1=todo incierto.
N13 sem_agentividad             float  Ratio eventos con agente intencional explícito. 0=todo pasivo/impersonal, 1=todo con agente claro.
N14 sem_vaguedad_semantica      float  Términos clave usados sin definición ni operacionalización. 0=todo definido, 1=todo vago.
N15 sem_causalidad_evento       float  Relaciones causales explícitas entre eventos concretos. 0=sin causalidad, 1=cadena causal constante.
N16 sem_telicidad               float  Acciones con punto final definido ("hasta que/para lograr/cuando termine"). 0=acciones abiertas, 1=todo télico.
N17 sem_informatividad          float  Ratio información nueva vs redundante/padding. 0=todo redundante, 1=todo nuevo.
N18 sem_relevancia_tematica     float  Pertinencia al tema central del texto. 0=disgresiones constantes, 1=todo al hilo.
N31 cog_carga_procesamiento     float  Dificultad cognitiva: sintaxis compleja, vocabulario técnico, estructuras anidadas. 0=fácil, 1=muy difícil.
N32 agencia_reactivo_proactivo  float  Postura del sujeto central. 0=reactivo (responde a estímulos), 1=proactivo (inicia acciones).
N33 agencia_iniciativa_verbal   float  Ratio verbos de iniciación ("decidir/proponer/crear") vs reacción ("responder/aceptar/tolerar"). 0=todo reacción, 1=todo iniciación.
N34 evasion_modalizacion        float  Cadenas de hedges que evitan compromiso ("podría ser que quizás"). 0=sin evasión, 1=evasión sistemática.
N35 evasion_pasivizacion_agentiva float  Pasivas en contextos negativos para ocultar agente ("se decidió/fue eliminado"). 0=ausente, 1=sistemático.
N36 agencia_protagonismo_narrativo float  El sujeto central es actor activo vs espectador. 0=espectador puro, 1=protagonista activo.
N37 cog_pensamiento_contrafactual float  Densidad de razonamiento contrafactual ("si hubiera/si no fuera/habría sido"). 0=ausente, 1=dominante.
N38 cog_falsa_dicotomia         float  Presentación de opciones como solo dos sin intermedios ("o X o Y"). 0=ausente, 1=sistemático.
N39 cog_falacia_pendiente       float  Cadena A→B→C presentada como inevitable sin evidencia de cada paso. 0=ausente, 1=argumento central.
N51 disc_compromiso_accionable  float  Presencia de compromiso concreto: sujeto+verbo+objeto+temporal. 0=sin compromisos, 1=compromisos precisos.
N52 disc_contradiccion_interna  float  Afirmaciones que se contradicen dentro del texto. 0=sin contradicciones, 1=contradicciones evidentes.
N53 disc_meta_discursivo        float  Frases que hablan del propio texto ("voy a analizar/cabe mencionar/es importante destacar"). 0=ausente, 1=dominante.
N54 disc_resolucion_tensiones   float  Las tensiones que abre el texto las cierra. 0=abre y no cierra, 1=cierra todo lo que abre.
N55 disc_coherencia_registro    float  Consistencia del nivel de formalidad a lo largo del texto. 0=registro inconsistente, 1=registro uniforme.
N56 disc_autocontencion         float  El texto es comprensible sin información externa. 0=requiere contexto externo, 1=autocontenido.
N57 disc_densidad_informacional_varianza float  Uniformidad de la distribución de información nueva. 0=muy irregular (picos y valles), 1=distribuida uniformemente.

# INSTRUCCIONES

1. Lee el texto completo.
2. Para cada dim, evalúa SOLO la estructura observable del texto, no el contenido temático.
3. Responde SOLO con JSON válido. Sin explicaciones, sin markdown, sin texto adicional.
4. Floats: 2 decimales. Categóricas: exactamente uno de los valores del conjunto.
5. Si no detectas señal para una dim float → 0.00. Para categóricas → elige la más representativa.
6. Las dims V17-V20 y V26-V28 son propiedad intelectual OMNI-MIND — anótalas con especial cuidado.
```

---

## USER PROMPT PASADA 1 (template)

```
Analiza este texto y produce el vector de 71 dimensiones:

"""
{text}
"""
```

---

## FEEDBACK TEMPLATE — generado por generate_feedback() con codigo puro ($0)

Este bloque lo genera el script automaticamente desde el vector de la pasada 1.
El template siguiente documenta el formato de salida de generate_feedback().

```
AUDITORIA ESTRUCTURAL DEL TEXTO (generada automaticamente desde tu etiquetado previo):

ESTRUCTURA LOGICA:
- Profundidad argumental: {disc_profundidad_argumental:.2f} ({interpretacion_profundidad})
- Coherencia logica: {disc_coherencia_logica:.2f}
- Premisas ocultas: {concl_premisa_oculta:.2f} ({interpretacion_premisas})
- Direccion: {direccion_str}

PRESUPOSICIONES:
- Densidad presupositiva: {presup_densidad:.2f} ({interpretacion_densidad})
- Anclaje en datos observables: {presup_anclaje_base:.2f} ({interpretacion_anclaje})
- Posicion del observador: nivel {nivel_obs} ({presup_posicion_observador:.2f})
- Fragilidad: {presup_fragilidad:.2f} ({interpretacion_fragilidad})

AGENTIVIDAD:
- Agentividad: {sem_agentividad:.2f} ({interpretacion_agentividad})
- Protagonismo: {agencia_protagonismo_narrativo:.2f} ({interpretacion_protagonismo})
- Evasion modalizada: {evasion_modalizacion:.2f} ({interpretacion_evasion})

DIMS CON SEÑAL FUERTE (>0.6):
  {lista_dims_fuertes}

DIMS SOSPECHOSAS (posibles inconsistencias internas):
  {lista_contradicciones}

INSTRUCCION: Revisa tus puntuaciones a la luz de esta auditoria.
Corrige las que consideres incorrectas. Mantén las que esten bien.
Presta especial atencion a las dims sospechosas — son contradicciones internas de tu propio etiquetado.
NO cambies todo — solo lo que genuinamente merezca correccion.
Responde con el JSON completo de 71 dims (corregido o no).
```

---

## PASADA 2 — SYSTEM PROMPT

```
Eres un anotador lingüístico. Acabas de etiquetar un texto con 71 dimensiones estructurales.
Se ha generado una auditoría estructural automática de tu etiquetado.

Tu tarea: revisar el etiquetado a la luz de la auditoría y producir el vector final.

REGLAS:
1. Si una dim te parece incorrecta tras leer la auditoría, corrígela.
2. Si te parece correcta, mantenla — no hay presión para cambiar.
3. Presta especial atención a "DIMS SOSPECHOSAS" — son contradicciones internas de tu propio etiquetado.
4. NO cambies todo — solo lo que genuinamente merezca corrección.
5. Responde SOLO con JSON válido. Sin explicaciones, sin markdown, sin texto adicional.
6. El JSON debe tener exactamente 71 campos (mismos que la pasada 1).
```

---

## USER PROMPT PASADA 2 (template)

```
TEXTO ORIGINAL:
"""
{text}
"""

TU ETIQUETADO DE LA PASADA 1:
{json_pasada_1}

{feedback_estructural}

Produce el JSON final de 71 dims (corregido o no).
```

---

## NOTAS DE DISEÑO

### Por qué funciona la doble pasada

El Simbionte demuestra que el feedback estructural mejora el output del LLM porque:
1. La pasada 1 es local: Opus evalua cada dim de forma independiente
2. El feedback es global: revela el patron emergente del vector completo
3. Las dims sospechosas detectan inconsistencias que Opus no ve por si mismo
   (ej: alta agentividad + alta evasion = el agente actua pero evita responsabilidad)
4. La pasada 2 es calibracion: Opus confirma o corrige con informacion adicional

### Cuándo usar doble pasada vs simple

Usar doble pasada para:
- Gold set (maxima calidad, coste justificado)
- Textos con ambiguedad estructural alta (presup_densidad > 0.7)
- Textos donde IAA pasada 1 sea < 0.80

Usar pasada simple para:
- Labeling masivo (volumen > 500 textos)
- Textos con señal clara (pocos dims activos)
- Cuando el presupuesto no permite 2.3x coste

### Metricas para evaluar si la doble pasada aporta

1. Tasa de cambio: % dims que cambian entre pasada 1 y 2
   - < 3%: la doble pasada no aporta (el etiquetado ya era estable)
   - 3-15%: rango saludable (correcciones puntuales)
   - > 15%: la pasada 1 era inestable (problemas en el prompt o el texto)

2. Magnitud de cambio: media de |p2 - p1| en dims que cambian
   - < 0.10: ajustes finos
   - 0.10-0.25: correcciones significativas
   - > 0.25: cambios radicales (posible inconsistencia en el prompt)

3. Resolucion de contradicciones: de N dims sospechosas, cuantas se resuelven
   - Ideal: >= 50% de contradicciones resueltas

4. IAA_pasada2 vs IAA_pasada1: si se ejecuta 3x el mismo texto
   - Si IAA_p2 > IAA_p1: la doble pasada aumenta consistencia (objetivo)
   - Si IAA_p2 <= IAA_p1: la doble pasada introduce ruido

### Coste estimado [SUPOSICION — sin tiktoken ejecutado]

Por texto (asumiendo prompt variante A = ~4510 tokens pasada 1):
- Pasada 1: ~3860 tokens input + 650 output = ~4510 tokens total
- Pasada 2: ~3860 (system) + 1500 (feedback+json p1) + 350 (instruccion) + 650 (output) = ~6360 tokens
- TOTAL por texto doble pasada: ~10870 tokens
- vs pasada simple: ~4510 tokens (2.4x coste)

PRE-FLIGHT obligatorio antes de cualquier batch (CostGate.validate_batch()).
