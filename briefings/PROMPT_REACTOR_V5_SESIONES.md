# PROMPT REACTOR v5 — Mapeo de Pares Problema-Solución a Vectores Funcionales

## INSTRUCCIONES DE USO

**Qué es esto:** Un prompt autocontenido para mapear pares problema-solución a vectores funcionales (7F×3L). Se pega al inicio de una sesión nueva de Claude. Claude ELIGE los casos de su conocimiento. Cada sesión procesa 10 pares. 5 sesiones = 50 pares.

**Cómo usar:**
1. Abre sesión nueva con Claude Opus
2. Pega este prompt completo como primer mensaje
3. Claude confirma que entiende
4. Dile: "Sesión N: [DOMINIO]" — Claude elige 10 casos y los mapea
5. Guarda el output en `results/reactor_v5/`

**Distribución de los 50 pares (5 sesiones):**
- Sesión 1: "Sesión 1: NEGOCIO" — 10 pares de empresas/negocios reales
- Sesión 2: "Sesión 2: SALUD" — 10 pares de medicina/rehabilitación/salud
- Sesión 3: "Sesión 3: STEM" — 10 pares de matemáticas/ingeniería/ciencia
- Sesión 4: "Sesión 4: MIXTO" — 10 pares de dominios variados (deporte, educación, derecho, personal)
- Sesión 5: "Sesión 5: FALLIDAS" — 10 pares cross-dominio donde la solución FALLÓ o EMPEORÓ (Tipo 2 y 3)

---

## ───── COPIAR DESDE AQUÍ ─────

Eres un analista del sistema cognitivo OMNI-MIND. Tu tarea es ELEGIR casos reales de tu conocimiento y mapear pares problema-solución a vectores funcionales usando la Teoría del Campo Funcional (TCF).

### LAS 7 FUNCIONES NUCLEARES

Cada sistema (negocio, organismo, problema matemático, proyecto) tiene 7 funciones vitales. Cada una se mide de 0.0 (ausente) a 1.0 (óptima).

```
F1 CONSERVAR    Mantener lo que funciona. Proteger la estructura. Memoria operativa.
                En negocio: mantener clientes, procesos, capital.
                En salud: mantener tejido, función, homeostasis.
                En STEM: conservar invariantes, identidades, restricciones válidas.

F2 CAPTAR       Absorber recursos del entorno. Buscar, atraer, incorporar.
                En negocio: marketing, ventas, contratación.
                En salud: nutrición, oxigenación, absorción de carga.
                En STEM: incorporar datos, variables, técnicas nuevas.

F3 DEPURAR      Eliminar lo que sobra o daña. Filtrar. Soltar. Simplificar.
                En negocio: despedir, cerrar líneas, eliminar desperdicio.
                En salud: eliminar toxinas, inflamación, patrones dañinos.
                En STEM: simplificar, reducir, eliminar complejidad innecesaria.

F4 DISTRIBUIR   Repartir recursos donde más falta. Asignar. Priorizar.
                En negocio: asignar presupuesto, tiempo, personas.
                En salud: distribuir carga, irrigación, atención.
                En STEM: distribuir esfuerzo computacional, balancear ecuaciones.

F5 FRONTERA     Saber qué soy y qué no soy. Identidad. Límites. Definición.
                En negocio: propuesta de valor, target, qué NO hacemos.
                En salud: sistema inmune, diferenciación celular, diagnóstico.
                En STEM: definir dominio, restricciones, tipo de problema.

F6 ADAPTAR      Cambiar ante cambios del entorno. Flexibilidad. Evolución.
                En negocio: pivotar, ajustar precios, innovar.
                En salud: neuroplasticidad, adaptación a carga, rehabilitación.
                En STEM: cambiar de método, reformular, generalizar.

F7 REPLICAR     Transmitir lo esencial para que funcione sin ti. Documentar. Escalar.
                En negocio: manuales, franquicia, onboarding, delegar.
                En salud: regeneración, cicatrización, enseñar ejercicios al paciente.
                En STEM: formalizar prueba, generalizar teorema, crear algoritmo reusable.
```

### LAS 3 LENTES

Cada función se puede mirar desde 3 perspectivas:
- **Salud:** ¿funciona HOY? ¿aguanta la presión actual?
- **Sentido:** ¿tiene dirección? ¿sabe POR QUÉ funciona?
- **Continuidad:** ¿sobrevive sin ti? ¿se puede transmitir?

### DEPENDENCIAS ENTRE FUNCIONES (leyes TCF)

```
BLOQUEANTES (B) — Fi NO PUEDE operar sin Fj:
  F2 → F3 (B)   Captar sin depurar = acumular basura
  F4 → F5 (B)   Distribuir sin frontera = fugas
  F7 → F5 (B)   Replicar sin frontera = replicar ruido

DEGRADANTES (D) — Fi opera PEOR sin Fj:
  F1 → F6 (D)   Conservar sin adaptar = rigidez
  F6 → F5 (D)   Adaptar sin frontera = perder identidad
  F7 → F1 (D)   Replicar sin conservar = copias degradadas
  F3 → F5 (D)   Depurar sin frontera = no saber qué es residuo
  F2 → F5 (D)   Captar sin frontera = captar cualquier cosa
  F4 → F1 (D)   Distribuir sin conservar = descapitalizarse
  F7 → F3 (D)   Replicar sin depurar = amplificar defectos
  F6 → F1 (D)   Adaptar sin conservar = destruir lo esencial
```

### 12 ARQUETIPOS

```
intoxicado:              F2↑ F3↓ — "Muy ocupados pero no avanzamos"
rigido:                  F1↑ F6↓ — "Siempre hemos hecho así"
sin_rumbo:               F5↓     — "No sé decir no"
hemorragico:             F4↓ F5↓ — "Facturamos mucho pero no queda nada"
parasito_interno:        F3↓ F5↓ — "Es parte de cómo somos" (sobre algo dañino)
maquina_sin_alma:        F7↓     — "¿Qué pasa si mañana no estoy?"
semilla_dormida:         F2↓ F4↓ — "Lo que hago es bueno, pero nadie lo sabe"
expansion_sin_cimientos: F7↑ F1↓ — "Estamos creciendo muy rápido"
aislado:                 F5↑↑ F2↓ — "No necesitamos nada de fuera"
copia_sin_esencia:       F7↑ F5↓ — "Ya no es lo que era"
quemado:                 TODO↓   — "Ya da igual"
equilibrado:             TODO↑   — "Sé lo que soy, funciono, podría transmitirlo"
```

### TRES TIPOS DE RESULTADO

```
TIPO 1 — CIERRE:   La solución cerró el gap. Delta neto positivo.
TIPO 2 — INERTE:   La solución no movió nada. Delta ≈ 0.
TIPO 3 — TÓXICO:   La solución empeoró el problema. Delta negativo.
```

### TU TAREA: ELEGIR CASOS Y MAPEAR

Cuando te diga "Sesión N: DOMINIO", tú:

1. **ELIGES 10 casos reales** de tu conocimiento sobre ese dominio
2. **Mapeas** cada caso como par problema-solución

**CRITERIOS PARA ELEGIR CASOS:**
- **Reales y verificables.** Casos públicos, documentados, conocidos. Nada inventado. Incluye nombre real (empresa, persona, evento, teorema) para que sea verificable.
- **Diversidad de resultado.** De los 10 casos, incluye al menos: 5-6 Tipo 1 (cierre), 2-3 Tipo 2 (inerte), 1-2 Tipo 3 (tóxico). Excepción: Sesión 5 (FALLIDAS) donde TODOS son Tipo 2 o 3.
- **Diversidad de arquetipo.** No repitas el mismo arquetipo más de 2 veces en una sesión. Busca cubrir al menos 5-6 arquetipos diferentes.
- **Diversidad de escala.** Mezcla micro (individuo/equipo), meso (empresa/organización), macro (industria/país).
- **Casos con datos concretos** tienen prioridad sobre narrativos vagos.
- **Selecciona para TESTEAR las leyes**, no para confirmarlas. Incluye casos donde la TCF podría fallar — eso es más valioso que 10 confirmaciones fáciles.
- **NO optimices para quedar bien.** Si un caso refuta una ley, repórtalo. La honestidad del mapeo es más importante que la tasa de confirmación.

**FORMATO DE OUTPUT por caso:**

```json
{
  "id": "N01",
  "dominio": "negocio|salud|matematicas|ingenieria|deporte|educacion|derecho|ciencia|personal",
  "escala": "micro|meso|macro",
  "caso_real": "Nombre real del caso/empresa/persona/evento para verificabilidad",

  "problema_resumen": "1-2 líneas con hechos concretos",
  "vector_pre": {"F1": 0.00, "F2": 0.00, "F3": 0.00, "F4": 0.00, "F5": 0.00, "F6": 0.00, "F7": 0.00},
  "arquetipo_estimado": "nombre (score%)",
  "arquetipo_secundario": "nombre (score%) o null",
  "eslabon_debil": "Fx",

  "solucion_resumen": "1-2 líneas con hechos concretos",
  "delta": {"F1": 0.00, "F2": 0.00, "F3": 0.00, "F4": 0.00, "F5": 0.00, "F6": 0.00, "F7": 0.00},
  "vector_post": {"F1": 0.00, "F2": 0.00, "F3": 0.00, "F4": 0.00, "F5": 0.00, "F6": 0.00, "F7": 0.00},

  "tipo_resultado": "cierre|inerte|toxico",
  "funciones_movidas": ["F3: +0.30", "F5: +0.20"],
  "funciones_no_movidas": ["F7: 0.00"],

  "leyes_tcf": [
    {"ley": "ley_2_FX_FY", "status": "confirmada|refutada|no_aplica", "detalle": "..."}
  ],
  "dependencias_violadas": ["F2→F3 (B): F2 subió sin F3"],
  "prediccion_tcf": "La TCF habría predicho: cierre|inerte|toxico porque...",
  "prediccion_correcta": true,

  "confianza_mapeo": 0.7,
  "notas": "cualquier observación relevante"
}
```

### REGLAS DE MAPEO

1. **Sé honesto con los grados.** No infles ni deflactes. 0.50 es "funciona a medias". 0.80 es "funciona bien". 0.20 es "casi no existe".
2. **El delta puede ser negativo.** Si la solución BAJA una función, pon delta negativo.
3. **Valida TODAS las dependencias relevantes.** Para cada par, revisa las 11 dependencias y reporta las que se activan (violadas o satisfechas). No es necesario listar las 11 si no son relevantes — solo las que el caso toca.
4. **La predicción TCF es CLAVE.** Antes de mirar el resultado real, pregúntate: "dado el vector_pre y el delta, ¿qué predicen las leyes TCF?" Luego compara con el resultado real. Reporta si la predicción fue correcta.
5. **Confianza del mapeo:** 0.9 si el caso tiene datos concretos (números, hechos verificables). 0.6-0.7 si es bien documentado pero cualitativo. 0.4-0.5 si es narrativo/parcial.
6. **No fuerces arquetipos.** Si el caso no encaja limpiamente, pon "mixto" o el más cercano con score bajo.
7. **vector_post = vector_pre + delta.** Verifica que la suma es correcta y que todos los valores están en [0.0, 1.0]. Si vector_pre + delta > 1.0, cap a 1.0. Si < 0.0, cap a 0.0.

### EJEMPLO COMPLETO

**CASO:** "Estudio de Pilates Authentic Pilates donde todo depende del dueño. Solución: documentó su método EEDAP en un manual y contrató un instructor."

```json
{
  "id": "EJEMPLO",
  "dominio": "negocio",
  "escala": "micro",
  "caso_real": "Authentic Pilates (estudio en Madrid)",

  "problema_resumen": "Estudio de Pilates sostenido por 1 persona, método propio EEDAP no documentado, sin delegación ni marketing",
  "vector_pre": {"F1": 0.50, "F2": 0.30, "F3": 0.25, "F4": 0.35, "F5": 0.65, "F6": 0.35, "F7": 0.20},
  "arquetipo_estimado": "maquina_sin_alma (75%)",
  "arquetipo_secundario": "semilla_dormida (20%)",
  "eslabon_debil": "F7",

  "solucion_resumen": "Documentó método EEDAP en manual + contrató primer instructor formado en el método",
  "delta": {"F1": 0.05, "F2": 0.05, "F3": 0.00, "F4": 0.10, "F5": 0.00, "F6": 0.05, "F7": 0.30},
  "vector_post": {"F1": 0.55, "F2": 0.35, "F3": 0.25, "F4": 0.45, "F5": 0.65, "F6": 0.40, "F7": 0.50},

  "tipo_resultado": "cierre",
  "funciones_movidas": ["F7: +0.30", "F4: +0.10"],
  "funciones_no_movidas": ["F3: 0.00", "F5: 0.00"],

  "leyes_tcf": [
    {"ley": "ley_2_F7_F5", "status": "confirmada", "detalle": "F7↑ con F5 ya alta (0.65) → dependencia F7→F5(B) satisfecha, replicación viable"},
    {"ley": "ley_2_F7_F3", "status": "no_aplica", "detalle": "F7→F3(D) degradante, F3=0.25 baja pero F7 subió desde 0.20 → riesgo menor de amplificar defectos"}
  ],
  "dependencias_violadas": [],
  "prediccion_tcf": "La TCF predice CIERRE: F7 era el eslabón débil, F5 ya era alta (0.65, dependencia F7→F5 satisfecha), documentar ataca directamente el gap principal",
  "prediccion_correcta": true,

  "confianza_mapeo": 0.85,
  "notas": "Caso real validado empíricamente. F3 sigue baja — siguiente intervención debería ser depuración."
}
```

### PROTOCOLO DE SESIÓN

Cuando recibas "Sesión N: DOMINIO":

1. **Elige 10 casos** reales del dominio indicado siguiendo los criterios de selección
2. **Presenta primero la lista** de los 10 casos elegidos (1 línea cada uno) para que el usuario confirme
3. Tras confirmación (o "adelante"), **mapea los 10 casos** en formato JSON
4. Al final de los 10, devuelve un **RESUMEN**:

```
RESUMEN SESIÓN [N] — [DOMINIO]:
- Pares procesados: 10
- Distribución tipos: X cierre, Y inerte, Z tóxico
- Arquetipos cubiertos: [lista]
- Leyes TCF confirmadas: [lista con conteo]
- Leyes TCF refutadas: [lista con detalle]
- Predicción correcta: X/10 (Y%)
- Confianza media: 0.XX
- Hallazgo principal: [la observación más interesante de la sesión]
- Hallazgo secundario: [otra observación]
- ¿Alguna ley necesita revisión?: [sí/no + detalle]
```

Responde con "Entendido. Listo para sesiones." para confirmar.

## ───── FIN DEL PROMPT ─────

---

## NOTAS PARA JESÚS (no copiar)

**Flujo por sesión:**
1. Pega el prompt → Claude dice "Entendido"
2. Dices "Sesión 1: NEGOCIO" → Claude propone 10 casos
3. Dices "adelante" → Claude mapea los 10 + resumen
4. Copias el output y lo guardas

**Si quieres intervenir:** Puedes vetar/cambiar casos de la lista antes de decir "adelante". Pero la idea es dejar que Opus elija para evitar sesgo.

**Dónde guardar los resultados:**
```
motor-semantico/results/reactor_v5/
  sesion_1_negocio.json
  sesion_2_salud.json
  sesion_3_stem.json
  sesion_4_mixto.json
  sesion_5_fallidas.json
  resumen_50_pares.md
```

**Qué esperar:**
- Si la TCF predice correctamente >70% de los pares → Teorema 5 avanza a ✅
- Si las mismas dependencias (F2→F3, F7→F5) aparecen cross-dominio → universalidad real
- Si algo falla consistentemente → la ley necesita ajuste (dato valioso también)
- Los casos Tipo 3 (tóxicos) son los más interesantes — ahí se validan las leyes de dependencia
