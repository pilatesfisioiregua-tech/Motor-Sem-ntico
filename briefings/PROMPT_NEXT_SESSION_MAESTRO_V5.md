# PROMPT SIGUIENTE SESION — Maestro V5: Las Gomas como Principio Organizador

**Fecha:** 22 marzo 2026
**Objetivo:** Reescribir la vision de conjunto del sistema como Maestro V5 donde los CHATBOTS son el sistema circulatorio que conecta todos los organos y las GOMAS son el principio de transmision.

---

## CONTEXTO CRITICO

### La idea central (de Jesus, 22-mar-2026)

El sistema cognitivo es como un circuito cerrado de gomas elasticas alrededor de levas y ruedas. Una palanca inicial → la energia se transmite por todas las gomas → movimiento perpetuo → solo se detiene con freno externo (Jesus CR1).

**Los chatbots son la pieza que hace posible la vision de conjunto.** Son la sangre, el sistema circulatorio que conecta cada organo con el siguiente. Sin chatbots, los componentes son piezas en una mesa. Con chatbots, el motor arranca y gira solo.

### Lo que tenemos HOY (documentos separados que no se conectan)

| Documento | Describe | Falta |
|---|---|---|
| Maestro V4 | PIEZAS (Motor, Gestor, Reactores, ACD) | Como fluye la energia entre ellas |
| L0_8 | MANOS (AF1-AF7, bus, senales) | Que las impulsa y las conecta |
| L0_9 | ANATOMIA (Sensorial, Cognitiva, Ejecutiva) | Que hace circular la informacion |
| L0_10 (borrador) | GOMAS + CHATBOTS (primer diseno) | Necesita integrarse en Maestro, no ser documento separado |

### Lo que el Maestro V5 debe ser

NO es "V4 + seccion nueva". Es la **reescritura donde cada componente se define por su posicion en el circuito**:
- Que goma lo impulsa
- Que chatbot lo conecta al siguiente
- Que pasa si esa conexion se rompe

### Decisiones CR0 ya tomadas esta sesion

1. **ELIMINADO:** enjambre de codigo, fabrica exocortex, migracion Supabase. Claude Code + Claude Desktop + MCP cubren todo eso.
2. **CHATBOTS = correas de transmision.** 6 chatbots (Vigia, Mecanico, Diagnosticador, Buscador, Gestor, Ejecutor) son sesiones de Claude Code lanzadas automaticamente con system prompt especifico.
3. **GOMAS = principio dinamico.** 6 gomas (datos→senales→diagnostico→busqueda→prescripcion→accion→aprendizaje) + goma META (rotura→auto-reparacion).
4. **FRENO = Jesus (CR1).** Todo lo demas es autonomo.
5. **Gap encontrado:** Falta Director Global. El Orquestador solo gestiona capa cognitiva. CR0: extender para coordinar 5 capas.

---

## INVENTARIO IMPLEMENTADO (para referencia)

| Componente | Estado | Endpoints/Tablas |
|---|---|---|
| Exocortex Pilates | IMPL | 111 endpoints, 29 tablas, 22 clientes |
| ACD Fase 1 | IMPL | 15P+12R+10 estados+detectors |
| Pipeline ACD basico | IMPL | /acd/diagnosticar ~$0.005/caso |
| Sequito 24 asesores | IMPL | /consejo, $0.003/consulta |
| Bloque Voz completo | IMPL | 25+ endpoints, 9 tablas, IRC+PCA+5 ciclos |
| WhatsApp bidireccional | IMPL | webhook + envio + confirmaciones |
| Portales (cliente+publico) | IMPL | /portal/{token} + /publico/chat |
| Cockpit generativo | IMPL | /cockpit + chat LLM |
| Motor Semantico v1 | IMPL | /motor/ejecutar, 3 casos >8.5/10 |
| Code OS | IMPL | 4/4 PASS, devstral/deepseek/glm-5 |
| MCP Conocimiento | IMPL | 694+ piezas pgvector, loop verificado |
| Cron | IMPL | Diaria 06:00 + Semanal lun 07:00 |

---

## ARCHIVOS A LEER

| Que | Ruta | Por que |
|---|---|---|
| Maestro V4 actual | docs/maestro/MAESTRO_V4.md | Base a reescribir (1307 lineas) |
| L0_8 Agentes | docs/L0/L0_8_ARQUITECTURA_UNIVERSAL_AGENTES.md | Capa ejecutiva |
| L0_9 Organismo | docs/L0/L0_9_ORGANISMO_COGNITIVO_3_CAPAS.md | 3 capas completas |
| L0_10 Gomas | docs/L0/L0_10_MOTOR_PERPETUO_GOMAS_Y_PALANCAS.md | Primer borrador gomas+chatbots |
| Checklist completo | docs/operativo/CHECKLIST_ORGANISMO_IMPLEMENTACION.md | Inventario de ~170 componentes |
| 77 Herramientas | docs/biblioteca/77_HERRAMIENTAS_COGNITIVAS_AGENTES_8_CAPAS_CR0.md | Guardian de sesgos |

**TAMBIEN consultar corpus MCP** para contexto denso:
- query: "chatbots gomas motor perpetuo circuito"
- query: "organismo cognitivo tres capas"  
- query: "checklist definitivo 170 componentes"
- query: "propiedades algebraicas empiricas compilador"
- query: "P41 gradientes duales"

---

## ESTRUCTURA PROPUESTA MAESTRO V5

```
§0. POR QUE V5 — las gomas como principio organizador
§1. QUE ES OMNI-MIND (reescrito: un organismo que gira solo)
§2. EL CIRCUITO DE GOMAS — el flujo de energia
    §2.1 Las 6 gomas + goma META
    §2.2 Que impulsa cada goma (tension elastica)
    §2.3 Frecuencia de rotacion (cron, eventos, umbrales)
§3. LOS CHATBOTS — el sistema circulatorio
    §3.1 Los 6 chatbots (Vigia, Mecanico, Diagnosticador, Buscador, Gestor, Ejecutor)
    §3.2 Anatomia de un chatbot (rol, trigger, herramientas, output, freno)
    §3.3 Como se conectan chatbots + gomas
§4. EL ALGEBRA — compilador de preguntas (preservado de V4 §3-§4)
§5. EL ENJAMBRE COGNITIVO — agentes de percepcion y composicion (de L0_9)
§6. LA CAPA EJECUTIVA — Meta-Red AF1-AF7 (de L0_8)
§7. LA CAPA SENSORIAL — busqueda dirigida (de L0_9)
§8. EL MOTOR vN — pipeline de ejecucion (preservado+ACD pasos 3-5)
§9. EL GESTOR — mantenimiento de la Matriz (preservado+extensiones)
§10. REACTORES — fabrica de preguntas (preservado, sin fabrica exocortex)
§11. GUARDIAN DE SESGOS — 77 herramientas modo dual
§12. PROPIOCEPCION — el organismo se diagnostica a si mismo
§13. GENERATIVA — el organismo crea herramientas nuevas
§14. INFRAESTRUCTURA — fly.io + pgvector + MCP + Claude Code (simplificado)
§15. RESULTADOS EMPIRICOS (preservado de V4 §10)
§16. CHECKLIST — estado actual + fases implementacion
§17. PRINCIPIOS DE DISENO (preservado+nuevos: P50 gomas, P51 chatbots)
§18. HORIZONTE
```

---

## QUE HACER

1. Leer Maestro V4 completo (1307 lineas) 
2. Leer L0_8, L0_9, L0_10
3. Consultar corpus MCP para contexto denso
4. Escribir Maestro V5 seccion por seccion, guardando en repo
5. Cada seccion: definir posicion en el circuito, que chatbot la conecta, que goma la impulsa

**Estimacion:** ~1-2 sesiones para el Maestro V5 completo.
