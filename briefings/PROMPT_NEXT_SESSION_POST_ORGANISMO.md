# PROMPT SIGUIENTE SESION — Post L0_8 + L0_9 + MCP

**Fecha:** 22 marzo 2026
**Contexto:** Sesion de diseño arquitectonico + primer briefing ejecutable (MCP)

---

## ESTADO ACTUAL

### Documentos nuevos en repo (22-mar-2026)

| Documento | Ruta | Estado | Que es |
|---|---|---|---|
| L0_8 | `docs/L0/L0_8_ARQUITECTURA_UNIVERSAL_AGENTES.md` | CR0 | Meta-Red de Agentes: 7 AF con 5 ciclos, 3 capas, bus de señales, 6 tipos de señal |
| L0_9 | `docs/L0/L0_9_ORGANISMO_COGNITIVO_3_CAPAS.md` | CR0 | Organismo completo: Sensorial + Cognitiva + Ejecutiva. Busqueda dirigida por gap/gradiente. Enjambre ACD. P41 + pgvector integrados |
| 77 Herramientas | `docs/biblioteca/77_HERRAMIENTAS_COGNITIVAS_AGENTES_8_CAPAS_CR0.md` | CR0 | PENDIENTE copiar al repo (Jesus debe copiar manualmente desde uploads) |
| B-MCP-01 | `motor-semantico/briefings/B-MCP-01.md` | Listo para ejecutar | MCP server de conocimiento: migration + endpoints + deploy + tests |

### INDICE_VIVO actualizado con L0_8, L0_9, cadena de lectura 1→10.

### B-PIL-20e: COMPLETADO (confirmado por Jesus al inicio de sesion)

---

## ACCION INMEDIATA

**Ejecutar B-MCP-01 con Claude Code.** Briefing en `motor-semantico/briefings/B-MCP-01.md`.
6 fases: A (migration) → B (conocimiento.py) → C (main.py) → D (deploy) → E (tests V1-V6) → F (config MCP).

---

## IDEAS DISEÑADAS PERO NO FORMALIZADAS

Estas ideas se discutieron en la sesion pero NO tienen documento ni briefing aun:

### 1. Capa propioceptiva del organismo
Agentes que monitorizan al propio sistema: calidad diagnostica, coste, drift, cobertura.
El sistema se aplica ACD a si mismo. Propiocepcion + mejora continua + telemetria → busqueda externa mas quirurgica.

### 2. Code OS como agente gestionado por chatbot
Un chatbot orquestador que traduce prescripciones del Estratega en briefings ejecutables y lanza Code OS automaticamente. Cierra el gap prescripcion→codigo.

### 3. Agente de Sesgos Cognitivos (77 herramientas)
Opera en modo dual: INTERNO (proteger calidad del enjambre) + EXTERNO (comunicacion persuasiva por segmento PCA).
Basado en `77_HERRAMIENTAS_COGNITIVAS_AGENTES_8_CAPAS_CR0.md`.
Se integra en el Eje 3 (Consumo) del Motor Tridimensional de Voz.

### 4. Aprendizaje sobre personas/audiencia
Tres niveles: sobre Jesus (sin limite), sobre clientes (RGPD con consentimiento), sobre desconocidos en redes (solo agregado por segmento PCA, nunca individual).
Los sesgos se aplican a SEGMENTOS, no a individuos identificables.

### 5. Maestro V4 → V5
El documento esta desactualizado (no tiene L0_8, L0_9, organismo 6 capas, MCP).
CR0 propuesto: extension rapida (§17-§20) sin reescribir todo.

### 6. Enjambre cognitivo completo
El ACD como enjambre real de chatbots (3L + 7F + clusters INT + P + R + Compositor + Estratega + Orquestador).
Detallado en L0_9 pero sin briefing de implementacion.

---

## PRIORIDAD DE IMPLEMENTACION (CR0)

1. **B-MCP-01** — MCP server de conocimiento (esta sesion o siguiente)
2. **Ingestar chats historicos** — Script batch para los ~20 chats del proyecto
3. **Config MCP en Claude Desktop** — Conectar y verificar que funciona
4. **77 Herramientas al repo** — Jesus copia manualmente
5. **Maestro V5 extension** — Añadir §17-§20
6. **AF1 (Conservacion)** — Siguiente agente ejecutivo despues de AF5 (Voz)
7. **Sensorial basica** — Generador de queries + Perplexity dirigido por gaps (requiere ACD Fase 2)

---

## ARCHIVOS CLAVE

```
# Nuevos documentos L0
docs/L0/L0_8_ARQUITECTURA_UNIVERSAL_AGENTES.md
docs/L0/L0_9_ORGANISMO_COGNITIVO_3_CAPAS.md

# Briefing pendiente de ejecutar
motor-semantico/briefings/B-MCP-01.md

# Contexto del Bloque Voz (completado)
motor-semantico/src/pilates/voz_identidad.py
motor-semantico/src/pilates/voz_estrategia.py
motor-semantico/src/pilates/voz_arquitecto.py
motor-semantico/src/pilates/voz_ciclos.py

# Main app
motor-semantico/src/main.py

# 77 Herramientas (PENDIENTE copiar al repo)
docs/biblioteca/77_HERRAMIENTAS_COGNITIVAS_AGENTES_8_CAPAS_CR0.md
```

---

## QUE HACER EN LA SIGUIENTE SESION

**Opcion A (si MCP no ejecutado aun):**
→ Ejecutar B-MCP-01. Verificar V1-V6. Configurar MCP en Claude Desktop.

**Opcion B (si MCP ejecutado y funcionando):**
→ Ingestar chats historicos del proyecto. Verificar que query funciona.
→ Empezar Maestro V5 extension.

**Opcion C (si Jesus quiere avanzar en otra cosa):**
→ AF1 (Conservacion) como segundo agente ejecutivo.
→ O ACD Fase 2 (B-ACD-05 a B-ACD-08).
