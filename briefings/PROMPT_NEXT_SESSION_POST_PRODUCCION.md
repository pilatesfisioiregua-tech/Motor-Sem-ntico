# PROMPT CONTINUACIÓN — POST B-ORG-PRODUCCION

**Fecha:** 24 marzo 2026
**Sesión anterior:** Escritura de B-ORG-PRODUCCION (F0 Blindaje + F1 Valor Inmediato)

---

## QUÉ SE HIZO ESTA SESIÓN

Escritura del briefing B-ORG-PRODUCCION con 10 pasos detallados, código before/after, 12 tests PASS/FAIL.

Cubre: auth middleware, CORS restrictivo, docs off, cron state en DB, ZoneInfo, cobros Redsys en cron, confirmaciones pre-sesión, cumpleaños WA, briefing semanal WA, rate limiting, RGPD mínimo, health profundo, fix stripe→redsys en automatismos.

**Briefing:** `motor-semantico/briefings/B-ORG-PRODUCCION.md`

## QUÉ HACER EN LA PRÓXIMA SESIÓN

**Opción A (recomendada): Ejecutar B-ORG-PRODUCCION con Claude Code**
1. Leer el briefing: `motor-semantico/briefings/B-ORG-PRODUCCION.md`
2. Ejecutar los 10 pasos en orden
3. Deploy a fly.io
4. Jesús setea secrets (OMNI_API_KEY, JESUS_TELEFONO)
5. Verificar 12 tests

**Opción B: Ejecutar Fase 2 (Cimientos pizarras + CQRS)**
Si F0+F1 ya se ejecutaron.

**Opción C: Otra prioridad**
Jesús decide.

## DOCUMENTOS CLAVE

| Documento | Ruta |
|-----------|------|
| Briefing F0+F1 | `motor-semantico/briefings/B-ORG-PRODUCCION.md` |
| Roadmap v4 (CR1) | `docs/operativo/ROADMAP_CONSOLIDADO_23MAR.md` |
| Ficha Redsys | Adjunta en proyecto Claude (Ficha_Tecnica_Caja_Rural_Redsys.docx) |

## CONTEXTO RÁPIDO

```
query_conocimiento("roadmap v4 127h 11 pizarras score 10")
query_conocimiento("auditoria profunda seguridad produccion oportunidades")
query_conocimiento("fase 0 blindaje auth cron cobros rate limit RGPD health")
```

## NOTAS

- `automatismos.py` todavía importa `stripe_pagos` en ejecutar_cron('diario') — el briefing lo corrige
- Credenciales Redsys sandbox NO disponibles aún — esperando respuesta de Caja Rural
- `is_configured()` en redsys_pagos.py protege contra ejecución sin credenciales
- Jesús debe proporcionar JESUS_TELEFONO para los secrets de fly.io
- Ficha técnica Redsys lista para enviar — falta email y teléfono en sección 8
