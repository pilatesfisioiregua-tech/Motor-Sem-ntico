# CHECKLIST IMPLEMENTACIÓN ACD

**Creado:** 2026-03-19
**Última actualización:** 2026-03-20

---

## ESTADO GLOBAL

| Fase | Briefings | Estado | Notas |
|------|-----------|--------|-------|
| 0: Code OS | B-ACD-00 | ✅ HECHO | 5/5 pasos pass |
| 1: Datos | B-ACD-01, 02, 03, 04 | ✅ COMPLETA | 4/4 PASS |
| 2: Diagnóstico | B-ACD-05, 06, 07, 08 | ✅ COMPLETA | 4/4 PASS. Pipeline end-to-end funcional |
| 3: Prescripción | B-ACD-09, 10, 11 | ✅ COMPLETA | 09 ✅ 10 ✅ 11 ✅ |
| 4: Ejecución | B-ACD-12, 13 | ✅ COMPLETA | 12 ✅ 13 ✅ |
| 5: Verificación | B-ACD-14, 15 | ✅ COMPLETA | 14 ✅ 15 ✅ — pipeline ACD cerrado |
| 6: Deploy+Prod | B-ACD-16 | ✅ COMPLETA | deploy + migration + persistencia + test e2e |
| 7: DB V4 | B-ACD-17 | ✅ PASS (local) | ALTER inteligencias + seed P/R/estados + aristas P↔P R↔R. Pendiente deploy para DB |
| 8: Auditoría | B-ACD-18 | ✅ PASS | Informe en results/AUDITORIA_MOTORES.md. 7/8 hipótesis correctas |

---

## DETALLE POR BRIEFING

### Fase 0: Code OS

- [x] **B-ACD-00** — Rediseño loop agentic Code OS ✅ 5/5

### Fase 1: Datos

- [x] **B-ACD-01** — pensamientos.json ✅ 15P, 3/3
- [x] **B-ACD-02** — razonamientos.json ✅ 12R, 3/3
- [x] **B-ACD-03** — estados.json + flags ✅ 10 estados, 3 flags
- [x] **B-ACD-04** — Migración DB ✅ 4 tablas SQL

### Fase 2: Diagnóstico

- [x] **B-ACD-05** — Evaluador funcional (V3.2 OpenRouter) ✅ 4/4. Pilates: F5=0.633 F7=0.167
- [x] **B-ACD-06** — Clasificador 10 estados ✅ 10/10. Pilates=E2 Latencia (gap=0.014, grad=0.394)
- [x] **B-ACD-07** — Repertorio INT×P×R (V3.2 OpenRouter) ✅ 4/4. Pilates: 3 activas, 2 atrofiadas, 13 ausentes
- [x] **B-ACD-08** — Diagnóstico end-to-end ✅ 6/6. Pilates=E3 Funcional (gap=0.067, grad=0.496). ~$0.002/caso

### Fase 3: Prescripción

- [x] **B-ACD-09** — Selección cognitiva INT×P×R ✅ 10/10. operador_ciego: 7 INTs, P05/P03/P08, R03/R09/R08, PRH-01+03 detectados
- [x] **B-ACD-10** — Mapeo lente faltante → nivel lógico → modo ✅ 5/5
- [x] **B-ACD-11** — Secuenciación con prohibiciones formales ✅ 8/8. 4 PRH, prefijos SUBIR_/FRENAR_ limpios

### Fase 4: Ejecución

- [x] **B-ACD-12** — Integrar P y R en generador de prompts ✅ 5/5. _generar_bloque_pr + format_individual + generar_prompts extendidos
- [x] **B-ACD-13** — Integrar prescripción en orchestrator ✅ 2/2. _run_acd() + pipeline integrado, Pilates=E3 MANTENER, 8 INTs

### Fase 5: Verificación

- [x] **B-ACD-14** — Métricas ACD en evaluador ✅ 6/6. evaluador_acd.py + integrado en evaluador.py + orchestrator
- [x] **B-ACD-15** — Decisión ternaria (cierre/inerte/tóxico) ✅ 8/8. decidir() en evaluador_acd.py, integrado en evaluador.py + orchestrator response

### Fase 6: Deploy + Producción

- [x] **B-ACD-16** — Deploy + migration + persistencia + test integración e2e ✅ 6/6

### Fase 7: DB V4

- [x] **B-ACD-17** — Migración DB → Maestro V4 ✅ PASS local (7/7)
  - ALTER inteligencias + lente_primaria
  - Seed tipos_pensamiento (15), tipos_razonamiento (12), estados_diagnosticos (10)
  - Aristas P↔P (IC5) y R↔R (IC6) — Opción A (DROP FK)
  - Correcciones: rutas JSON src/meta_red/, iteración dict .values()
  - Pendiente: ejecutar migrations contra DB en próximo `fly deploy`

### Fase 8: Auditoría Funcional

- [x] **B-ACD-18** — Smoke test todos los motores ✅ PASS
  - Motor vN: FUNCIONAL | Gestor compilador: FUNCIONAL | Code OS: FUNCIONAL | Reactor v1: FUNCIONAL
  - Gestor loop lento: NO EXISTE | Reactor v5: SOLO OUTPUTS | Reactor v4: NO EXISTE | Models: STUB
  - Output: results/AUDITORIA_MOTORES.md

### Fase 9: Consolidado Post-ACD

- [ ] **B-ACD-19** — Deploy + Models + Gestor loop lento + Reactores v4/v5 📝 briefing escrito
  - Fase A: Deploy con migrations V4 (SQL + seeds Python en startup)
  - Fase B: Models desbloquear sklearn
  - Fase C: Gestor analizador.py (loop lento v0) + endpoint /gestor/analizar
  - Fase D: Reactor v4 telemtría v0 + endpoint /reactor/telemetria
  - Fase E: Reactor v5 como código (5 casos semilla) + endpoint /reactor/v5

---

## LOG DE EJECUCIÓN

| Fecha | Briefing | Resultado | Notas |
|-------|----------|-----------|-------|
| 2026-03-19 | B-ACD-00 | ✅ PASS (5/5) | mochila 4 secciones, system prompt 311ch |
| 2026-03-19 | B-ACD-01 | ✅ PASS (3/3) | 15 pensamientos P01-P15 |
| 2026-03-19 | B-ACD-02 | ✅ PASS (3/3) | 12 razonamientos R01-R12 |
| 2026-03-19 | B-ACD-03 | ✅ PASS | 10 estados, 3 flags |
| 2026-03-19 | B-ACD-04 | ✅ PASS | 4 tablas SQL |
| 2026-03-20 | B-ACD-05 | ✅ PASS (4/4) | openrouter_client.py + evaluador_funcional.py. V3.2 Pilates F5=0.633 F7=0.167 |
| 2026-03-20 | B-ACD-06 | ✅ PASS (10/10) | diagnostico.py clasificador. Pilates=E2 (gap=0.014, grad=0.394). Fix flags.py >= |
| 2026-03-20 | B-ACD-07 | ✅ PASS (4/4) | repertorio.py. V3.2: 3 activas (INT-10,15,08), 1574/250 tokens, 4 advertencias IC |
| 2026-03-20 | B-ACD-08 | ✅ PASS (6/6) | diagnosticar() end-to-end. Pilates=E3 Funcional (gap=0.067, grad=0.496). coalición=salud_sentido, perfil=S+Se+C-, atractor=rigidez. ~$0.002, ~24s |
| 2026-03-20 | B-ACD-11 | ✅ PASS (8/8) | verificar_prohibiciones() en recetas.py. 4 PRH: F7 sin Se, F2 sin F3, F7 gap>0.30, F6 sin F5. Prefijos limpios. 147 tests sin regresión |
| 2026-03-20 | B-ACD-09 | ✅ PASS (10/10) | prescriptor.py. operador_ciego: 7 INTs (base+refuerzo Se), Ps=[P05,P03,P08], Rs=[R03,R09,R08], nivel 3-5, modos ENMARCAR+PERCIBIR, PRH-01+03 detectados, 1 advertencia IC4 |
| 2026-03-20 | B-ACD-12 | ✅ PASS (5/5) | generador.py: _generar_bloque_pr(), format_individual+bloque_pr, generar_prompts+ps/rs. Backward compatible. 147 tests sin regresión |
| 2026-03-20 | B-ACD-13 | ✅ PASS (2/2) | orchestrator.py: _run_acd(), ACD en pipeline, INTs→forzadas, Ps/Rs→generador, ACD en response. Pilates=E3 MANTENER, 8 INTs, ~17s. 147 tests sin regresión |
| 2026-03-20 | B-ACD-15 | ✅ PASS (8/8) | DecisionTernaria + decidir() en evaluador_acd.py. 3 veredictos: tóxico/inerte/cierre. Integrado en evaluador.py + orchestrator response. 147 tests sin regresión |
| 2026-03-20 | B-ACD-16 | ✅ PASS (6/6) | Deploy fly.io + fix mount Code OS (/code-os) + DB password reset + log_diagnostico() + ACD persistencia. E2E: Pilates=E3 cierre (confianza=0.45), Score=8.3, $0.22, ~180s. diag_id=48d86e0e persistido en DB |

---

## NOTA: VARIABILIDAD ENTRE TESTS INDIVIDUALES Y END-TO-END

B-ACD-05 solo → Pilates F5=0.633 F7=0.167 → clasificado E2 (grad=0.394)
B-ACD-08 e2e → Pilates F5=0.833 F7=0.20 → clasificado E3 (grad=0.496)

Diferencia normal: V3.2 no es determinista al 100% con temperature=0.1. La segunda ejecución evaluó F5 más alto (0.833 vs 0.633) y varias funciones algo más altas, subiendo el gradiente a E3. Ambos resultados son coherentes con el caso real. Esto refuerza que el diagnóstico debe capturar el vector completo (no solo el estado) para análisis posteriores.

---

## ORDEN DE EJECUCIÓN FASE 4

```
B-ACD-12 (P/R en generador) ──→ B-ACD-13 (ACD en orchestrator)
```

**Secuencial:** B-ACD-12 primero, luego B-ACD-13.

## ORDEN DE EJECUCIÓN FASE 5

```
B-ACD-14 (métricas ACD) ──→ B-ACD-15 (decisión ternaria, extiende B-ACD-14)
```

**Secuencial:** B-ACD-14 primero (crea evaluador_acd.py), luego B-ACD-15 (extiende con decidir()).
**Todo código puro, $0.**
