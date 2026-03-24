# PROMPT SIGUIENTE SESIÓN — Maestro V5 como Sistema Modular de Bloques

**Fecha:** 22 marzo 2026
**Objetivo:** Reestructurar V5 de documento monolítico a sistema modular de bloques especializados. Cada bloque con desarrollo óptimo completo.

---

## CONTEXTO CRÍTICO

### Por qué modular

Un documento monolítico de 1500 líneas tiene el mismo problema que V4 diagnosticó sobre sí mismo: "genio mortal" — no puede transferir conocimiento. Nadie navega 1500 líneas. Cada bloque debe poder leerse independientemente, con profundidad total en su área, y conectarse con los demás vía el índice maestro.

Es exactamente lo que el propio sistema prescribiría (P30: come tu propia comida).

### Lo que hay HOY

| Documento | Líneas | Estado |
|---|---|---|
| docs/maestro/MAESTRO_V5.md | 423 | Resumen ejecutivo — sirve como base del ÍNDICE |
| docs/producto/B2_9_BLOQUE_VOZ_GOMAS.md | 794 | Completo — se convierte en V5-06 |
| docs/maestro/MAESTRO_V4.md | 1307 | Fuente para V5-01 (álgebra) |
| docs/L0/L0_8*.md | ~600 | Fuente para V5-05 (ejecutiva) |
| docs/L0/L0_9*.md | ~800 | Fuente para V5-04 (capas cognitivas) |
| docs/L0/L0_10*.md | ~500 | Fuente para V5-02 (organismo) |
| docs/producto/B2_8*.md | 1336 | Fuente para V5-06 (AF5 blueprint) |

### Decisiones de la sesión 22-mar que aplican

- "Chatbot" → "Agente IA autónomo" en TODO
- Estigmergia superseded (bus + corpus)
- Circuito cerrado: G5→G1, G6→G2 paralelo
- G1 necesita OBSERVADOR (listener)
- ACL/ACF (cognitivos) vs AF (ejecutivos)
- Motor vN es transversal (G2, G4, G6)
- P50-P58 definidos (gomas, agentes, veto, emergencia, herramienta×agente, canal×CM)

---

## ESTRUCTURA DE BLOQUES

```
docs/maestro/
├── MAESTRO_V5.md                ← ÍNDICE EJECUTIVO (~300 líneas)
│   Visión, propuesta de valor, circuito de gomas,
│   punteros a cada bloque, ecuaciones de cierre
│
├── V5-01_ALGEBRA.md             ← EL CEREBRO MATEMÁTICO (~300 líneas)
│   8 operaciones, ~55 leyes en 8 grupos, propiedades
│   empíricas, compilador, formato canónico P35, Matriz
│
├── V5-02_ORGANISMO_GOMAS.md     ← EL CIRCUITO DE GOMAS (~250 líneas)
│   6 gomas + META, frecuencias, moduladores,
│   qué pasa si se rompe, OBSERVADOR de G1,
│   los 6 agentes IA del organismo con detalle completo
│
├── V5-03_MOTORES.md             ← LA MAQUINARIA (~200 líneas)
│   Motor vN (7 capas + 11 pasos ACD), 4 modos, 2 fases,
│   Séquito 24 asesores, Gestor (10 pasos), Reactores
│
├── V5-04_CAPAS_COGNITIVAS.md    ← EL CEREBRO (~300 líneas)
│   Capa Sensorial (7 buscadores, corpus vivo, filtro ACD),
│   Enjambre Cognitivo (3 niveles, clusters, Compositor,
│   Estratega, Orquestador), Guardián sesgos (77 herramientas)
│
├── V5-05_EJECUTIVA_META_RED.md  ← LAS MANOS (~300 líneas)
│   Meta-Red AF1-AF7 con equipos de agentes IA por AF,
│   mapa 7×7 inter-agente, protocolo señales,
│   detector convergencia, 3 capas por agente, cascada María
│
├── V5-06_AF5_BLUEPRINT.md       ← EL CASO DE REFERENCIA (~400 líneas)
│   Motor Tridimensional (IRC×Matriz×PCA),
│   8 agentes IA (CAZADOR, EMBAJADOR, ANALISTA, 5 CM),
│   coordinación cross-canal, caso B2B completo,
│   implementado vs pendiente, coste vs valor
│   (Integra B2.9 completo)
│
├── V5-07_PROPIOCEPCION.md       ← EL SISTEMA INMUNE COGNITIVO (~150 líneas)
│   P30 come tu propia comida, auto-diagnóstico,
│   detector drift, generativa (cristalización L2→L1),
│   evolución de herramientas, mejora continua
│
├── V5-08_INFRA_DB.md            ← LA FONTANERÍA (~250 líneas)
│   Stack completo, schema DB (~65+ tablas con detalle),
│   pgvector, modelos validados, WhatsApp como infra,
│   mapa herramienta×agente×uso al 100%, costes
│
├── V5-09_EXOCORTEX.md           ← EL PRODUCTO (~200 líneas)
│   Qué es un exocortex, cómo se construye por tenant,
│   relación con AF1-AF7, Authentic Pilates como primer
│   tenant (111 EP, 29 tablas), blueprint segundo tenant
│   (fisioterapia), RGPD, shared vs dedicated
│
├── MAESTRO_V4.md                ← HISTÓRICO
└── MAESTRO_V3.md                ← HISTÓRICO
```

**Total estimado: ~2450 líneas** distribuidas en 10 documentos.
Cada documento legible independientemente. El ÍNDICE los conecta.

---

## DETALLE POR BLOQUE

### MAESTRO_V5.md — ÍNDICE EJECUTIVO (~300 líneas)

El V5 actual (423 líneas) se convierte en el índice. Se MANTIENE casi todo lo que tiene, pero:
- Se aligera lo que está desarrollado en bloques (§4 álgebra deja de ser 8 líneas para ser un puntero a V5-01)
- Se expande §1.4 (propuesta de valor €9.500 vs €15-30)
- Se expande §2 (gomas con ejemplo real)
- Se añade §0.5 "Mapa de bloques" con tabla de qué leer según necesidad
- Cada sección tiene: resumen ejecutivo + "Detalle completo: V5-XX"

### V5-01_ALGEBRA.md (~300 líneas)

FUENTE: V4 §3-§4 (~300 líneas)

Contenido:
- §1 La Matriz 3L×7F×18INT×15P×12R con niveles L0/L1/L2
- §2 Las 8 operaciones del álgebra (fusión, composición, integración, diferencial, loop, contribución marginal, factorización, cruce derecho) con propiedades de cada una
- §3 Las ~55 leyes en 8 grupos (con 3-5 líneas por grupo explicando las leyes clave)
- §4 Propiedades empíricas confirmadas (tabla completa)
- §5 Las 14 reglas del compilador
- §6 Formato canónico P35
- §7 Dependencias TCF entre funciones
- §8 Posición en el circuito de gomas (G2 + G4)

### V5-02_ORGANISMO_GOMAS.md (~250 líneas)

FUENTE: L0_10 + V5 actual §2-§3

Contenido:
- §1 El circuito de 6 gomas + META (diagrama)
- §2 Qué impulsa cada goma (tensión elástica)
- §3 Frecuencia de rotación y moduladores
- §4 OBSERVADOR — componente de G1 (listener DB/webhooks que clasifica datos en señales)
- §5 Los 6 agentes IA del organismo — CADA UNO con:
  - Trigger concreto
  - Herramientas que exprime al 100% (con APIs)
  - Lo que un humano haría al 5%
  - Output concreto
  - Freno
  - Ejemplo de una acción típica
- §6 Cómo se conectan agentes + gomas (diagrama)
- §7 Qué pasa si una conexión se rompe (tabla)
- §8 El circuito completo en un ejemplo real con herramientas y costes
- §9 Reglas de auto-ejecución vs CR1

### V5-03_MOTORES.md (~200 líneas)

FUENTE: V4 §5-§6 + V5 actual §8-§10

Contenido:
- §1 Motor vN — Pipeline técnico 7 capas (tabla con Estado/Tiempo/Coste)
- §2 Pipeline lógico ACD 11 pasos (detallado, qué hace cada paso)
- §3 4 modos de operación con ejemplos
- §4 2 fases (A exploración, B lookup) con criterio de transición
- §5 Séquito 24 asesores (implementado, /consejo, $0.003/consulta)
- §6 Gestor de la Matriz — 10 pasos con estado implementación
- §7 Tabla programas_compilados y transferencia cross-dominio
- §8 Reactores — generación dirigida por gaps
- §9 Motor como componente TRANSVERSAL (G2, G4, G6)

### V5-04_CAPAS_COGNITIVAS.md (~300 líneas)

FUENTE: L0_9 Capa Sensorial + Capa Cognitiva + V4 §11

Contenido:
- §1 Capa Sensorial — principio P53 (diagnóstico dirige búsqueda)
- §2 Dos motores de búsqueda (por gap + por gradiente) con ejemplo
- §3 Los 7 buscadores especializados (tabla con fuentes y triggers)
- §4 Generador de Queries — ejemplo completo Authentic Pilates
- §5 Filtro ACD — las 3 preguntas
- §6 Corpus Vivo — pgvector, TTL, reorganización por cambio ACD
- §7 Frecuencia por urgencia del gap (tabla)
- §8 Enjambre Cognitivo — por qué (LLM monolítico se satura)
- §9 Nivel 1: Agentes de Percepción (3 ACL + 7 ACF + 6 clusters INT + 4P + 3R)
- §10 Nivel 2: Compositor + Estratega (qué hace cada uno)
- §11 Nivel 3: Orquestador — 3 modos con ejemplo de cuándo
- §12 Generación de preguntas nuevas y cristalización
- §13 Gradientes Duales P41 — ejemplo numérico + semántico
- §14 Guardián de Sesgos — 77 herramientas, modo dual, ejemplo veneno/antídoto
- §15 Costes estimados por capa

### V5-05_EJECUTIVA_META_RED.md (~300 líneas)

FUENTE: L0_8 completo + V5 actual §7

Contenido:
- §1 El vacío que resuelve (diagnostica pero no actúa)
- §2 Ciclo universal 5 fases (ESCUCHAR→...→APRENDER)
- §3 Los 7 AF con equipos de agentes IA — tabla por AF:
  - Qué escucha, qué emite, equipo de agentes, herramientas al 100%
- §4 Las 3 capas de profundidad por agente (ejecución, enriquecimiento, expansión) con ejemplo por AF
- §5 Tipos de señales inter-agente (6 tipos)
- §6 Bus de señales — cómo funciona, detector convergencia
- §7 Mapa 7×7 de señales (tabla de L0_8)
- §8 Protocolo de señal (formato estándar)
- §9 ACD como modulador global — tabla estado→efecto
- §10 Ejemplo cascada María (completo)
- §11 Propiedades de la Meta-Red (isomorfismo, no-conmutatividad, degradación, emergencia, veto)
- §12 Blueprint: cada AF necesita su B2.X

### V5-06_AF5_BLUEPRINT.md (~400 líneas)

FUENTE: B2.9 completo (794 líneas destiladas) + B2.8 detalle técnico

Contenido:
- §1 Por qué AF5 es el caso de referencia (primer AF completo, en producción)
- §2 Motor Tridimensional (IRC×Matriz×PCA) con fórmula IRC, ejemplo PCA completo
- §3 Arquitecto de Presencia — qué configura por canal
- §4 Los 3 agentes de investigación:
  - CAZADOR — inteligencia audiencia (SparkToro 50 queries, targets ocultos)
  - EMBAJADOR — captación B2B (caso completo 4 semanas con clínicas)
  - ANALISTA — cruces de datos (clima×cancelaciones, trends×conversiones)
- §5 Los 5 agentes CM por canal:
  - CM-WA (diseña, gestiona, responde, se adapta)
  - CM-GOOGLE (ficha, reseñas, Q&A, SEO local)
  - CM-IG (bio, contenido, DMs, limitaciones honestas)
  - CM-FB (complementario, activación/desactivación por IRC)
  - CM-WEB (SEO, si existe)
- §6 Coordinación cross-canal vía bus (3 ejemplos)
- §7 De batch a gomas — qué cambia de B2.8 a B2.9
- §8 Contenido del NO (F3+F5) como diferencial de producto
- §9 Implementado HOY vs pendiente
- §10 Coste vs valor (€10-15 vs €5.500)
- §11 Blueprint para replicar en AF1-AF7

### V5-07_PROPIOCEPCION.md (~150 líneas)

FUENTE: V4 §12 + L0_9 propiedades + sesión 22-mar

Contenido:
- §1 P30: Come tu propia comida — el sistema se diagnostica a sí mismo
- §2 V4 diagnosticado como "genio mortal" (gap=0.37) — ejemplo real
- §3 Los 4 componentes propioceptivos:
  - ACD sobre sí mismo
  - Detector preguntas huérfanas
  - Telemetría inter-agente (salud Meta-Red)
  - Detector de drift (sistema se aleja de principios)
- §4 Dimensión Generativa — cristalización L2→L1
  - Criterios numéricos (n>10, tasa>0.40, 2+ dominios)
  - Ejemplo concreto de pregunta que cristalizó
  - Nuevas herramientas cognitivas de patrones INT×P×R
- §5 Mejora continua como propiedad emergente
  - Cada goma mejora la siguiente
  - Cross-tenant por similaridad semántica (pgvector)
  - El Gestor como jardinero de la Matriz
- §6 Riesgos de auto-referencia y cómo acotarlos

### V5-08_INFRA_DB.md (~250 líneas)

FUENTE: V3 §8 (schema DB completo) + V5 actual §14 + sesión pilates

Contenido:
- §1 Stack tecnológico completo
- §2 Stack de modelos validado (devstral, deepseek, glm-5, nomic)
- §3 Schema DB — las ~65+ tablas organizadas por grupo:
  - Grupo 1: Exocortex Pilates (29 tablas — listado con descripción)
  - Grupo 2: Bloque Voz (9 tablas — con campos clave)
  - Grupo 3: ACD (4 tablas)
  - Grupo 4: Sistema (motor, gestor, pipeline, conocimiento)
  - Grupo 5: Bus de señales (nueva)
  - Grupo 6: MCP Conocimiento
- §4 pgvector — embeddings, similaridad coseno, cross-tenant
- §5 WhatsApp como infraestructura transversal
- §6 Mapa global: Herramienta × Agente IA × Uso al 100% (tabla 13 herramientas)
- §7 Costes estimados por componente y por tenant
- §8 Integración Redsys (Caja Rural) — pagos recurrentes, PayGold, Bizum

### V5-09_EXOCORTEX.md (~200 líneas)

FUENTE: B2.8 + EXOCORTEX_PILATES_DEFINITIVO_v2.1 + EXOCORTEX_ESTRUCTURA_MAESTRO_v2.1

Contenido:
- §1 Qué es un exocortex (cerebro externo operativo del negocio)
- §2 Estructura genérica — qué tiene todo exocortex:
  - CRUD operativo (clientes, contratos, sesiones, pagos)
  - 7 bloques funcionales alineados con F1-F7
  - Conexión con ACD para diagnóstico
  - Interfaz: Modo Estudio (keyboard-first) + Modo Profundo (24 asesores)
- §3 Authentic Pilates como primer tenant:
  - 111 endpoints, 29 tablas, 22 clientes reales
  - Facturación VeriFactu
  - 16 grupos horarios
  - Portal cliente + público
  - Cockpit generativo
- §4 Blueprint para segundo tenant (clínica fisioterapia de la mujer de Jesús):
  - Shared DB design con datos clínicos cifrados (RGPD Art. 9)
  - Cross-domain learning Pilates↔Fisioterapia
  - Qué se comparte vs qué es dedicado
- §5 Cómo construir un exocortex nuevo (Claude Code + briefings)
- §6 Relación exocortex ↔ AF1-AF7 ↔ agentes IA

---

## ORDEN DE ESCRITURA (próximas sesiones)

### Sesión 1: Estructura + V5-01 + V5-02

1. Crear la estructura de archivos en docs/maestro/
2. Reescribir MAESTRO_V5.md como ÍNDICE (~300 líneas)
3. Escribir V5-01_ALGEBRA.md (~300 líneas) — fuente: V4 §3-§4
4. Escribir V5-02_ORGANISMO_GOMAS.md (~250 líneas) — fuente: L0_10 + V5 §2-§3

### Sesión 2: V5-03 + V5-04

5. Escribir V5-03_MOTORES.md (~200 líneas) — fuente: V4 §5-§6
6. Escribir V5-04_CAPAS_COGNITIVAS.md (~300 líneas) — fuente: L0_9

### Sesión 3: V5-05 + V5-06

7. Escribir V5-05_EJECUTIVA_META_RED.md (~300 líneas) — fuente: L0_8
8. Escribir V5-06_AF5_BLUEPRINT.md (~400 líneas) — fuente: B2.9 + B2.8

### Sesión 4: V5-07 + V5-08 + V5-09

9. Escribir V5-07_PROPIOCEPCION.md (~150 líneas)
10. Escribir V5-08_INFRA_DB.md (~250 líneas) — fuente: V3 §8, Ficha Redsys
11. Escribir V5-09_EXOCORTEX.md (~200 líneas) — fuente: EXOCORTEX_DEFINITIVO

### Post-escritura

12. Actualizar INDICE_VIVO con todos los V5-XX
13. Find-replace "chatbot" → "agente IA" en B2.9
14. Ingestar todo en corpus MCP
15. Guardar prompt F0 (bus de señales + Vigía + ACD P3-5)

---

## REGLAS DE ESCRITURA

1. **Terminología:** "Agente IA autónomo" SIEMPRE. Nunca "chatbot". ACL/ACF (cognitivos) vs AF (ejecutivos).

2. **Cada bloque independiente:** Debe poder leerse sin haber leído ningún otro. Incluir contexto mínimo necesario al inicio.

3. **Cada bloque referencia a otros:** "Para detalle del álgebra ver V5-01_ALGEBRA.md". No duplicar contenido — referenciar.

4. **Filosofía B2.9 en CADA bloque:** "Lo que un humano haría al 5% vs lo que el agente IA hace al 100%". Herramientas concretas, APIs, costes.

5. **Ejemplos concretos con Authentic Pilates** en cada bloque — no teoría abstracta.

6. **Posición en el circuito de gomas** al inicio de cada bloque.

7. **El ÍNDICE es el HUB:** Si alguien lee SOLO el índice, entiende el sistema completo a nivel ejecutivo. Si necesita profundizar, sigue el puntero al bloque.

---

## ARCHIVOS FUENTE

| Bloque | Fuente principal | Fuentes secundarias |
|---|---|---|
| ÍNDICE | V5 actual (423 líneas) | Todos los demás |
| V5-01 | V4 §3-§4 | Cartografía propiedades algebraicas |
| V5-02 | L0_10 completo | V5 §2-§3 |
| V5-03 | V4 §5-§6-§7 | V3 §5 (pipeline detallado) |
| V5-04 | L0_9 completo | V4 §11 (guardián) |
| V5-05 | L0_8 completo | V5 §7 |
| V5-06 | B2.9 + B2.8 | V5 §7.10 |
| V5-07 | V4 §12-§13 | Sesión auto-diagnóstico V4 |
| V5-08 | V3 §8 (schema) | Ficha Redsys, sesión pilates |
| V5-09 | EXOCORTEX_DEFINITIVO_v2.1 | EXOCORTEX_ESTRUCTURA_MAESTRO |

---

## CONSULTAR CORPUS MCP al inicio de cada sesión

- query: "agente IA autónomo" → terminología correcta
- query: "maestro v5.1 reescrito" → estado actual
- query: "error compresión maestro" → no repetir
- query: tema específico del bloque que toque
