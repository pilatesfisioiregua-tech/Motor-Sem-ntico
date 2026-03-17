
=== EXP 4 — MESA REDONDA MULTI-MODELO (12 modelos, 2 rondas) ===

HALLAZGOS:
- Mesa evaluadora producción: V3.2-chat + V3.1 + R1 = 100% cobertura con prompts especializados
- Sintetizador: Cogito-671b #1 sin discusión (3.6 conexiones/output, 5/5 hallazgos no-genéricos, 47s)
- Qwen3 inflador (+0.93 vs media global). NO cerebro. 77% de convergencias hacia donde Qwen3 apuntaba en R1
- Auto-tracking inflaba +0.93 puntos. Evaluación externa Claude: media 3.06 (vs auto 3.99)
- Pizarra distribuida: 425 conexiones + 239 puntos ciegos (valor exclusivo). GPT-OSS mayor contribuidor (119), no Qwen3 (63)
- Kimi K2 INERTE (0/5 R2). GLM-4.7 marginal. Opus $75/M 0 únicos. Sonnet 0 únicos.

DECISIONES VALIDADAS:
- Mesa producción: V3.2-chat + V3.1 + R1
- Sintetizador: Cogito-671b
- Pizarra (Tier 4): 7 modelos → Cogito sintetiza → panel evaluador externo valida
- Descartados: Opus, Sonnet, Kimi K2, GLM-4.7


=== EXP 5 — CADENA DE MONTAJE (8 configs × 5 tasks = 40 runs) ===

| Config | T1(TS) | T2(SQL) | T3(Py) | T4(Orch) | T5(Asm) | Media | Coste |
|--------|--------|---------|--------|----------|---------|-------|-------|
| A Industrial (7 est.) | 0% | 94% | 100% | 0% | 83% | 56% | $0.33 |
| D Ultra-Barato (5 est.) | 0% | 80% | 90% | 0% | 86% | 51% | $0.05 |
| B Coder Puro (5 est.) | 0% | 93% | 91% | 0% | 0% | 37% | $0.14 |
| G Razonadores (7 est.) | 0% | 0% | 90% | 0% | 75% | 33% | $0.19 |
| 0 Baseline (1 est.) | 0% | 0% | 83% | 0% | 75% | 32% | $0.03 |

HALLAZGOS:
1. Pipeline lineal: techo 56%. NO reemplaza a Code
2. T4 (Orquestador async): 0% en 8/8 configs — techo ESTRUCTURAL
3. Config D Pareto: 51% a $0.05 — 7x más barato que A para -5%
4. Premium PEOR: 15% a $0.34 — pagar más NO ayuda
5. Debugger poco eficaz: 5/35 mejoras. Reviewer ROMPE código funcional (3 casos)


=== EXP 1 BIS — 6 MODELOS NUEVOS (6 × 5 tareas = 30 runs) ===

| Modelo | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Step 3.5 Flash | 1.00 | 0.89 | 1.00 | 1.00 | 1.00 | 0.98 | $0.019 |
| Nemotron Super | 1.00 | 0.88 | 1.00 | 0.90 | 1.00 | 0.96 | $0.007 |
| MiMo V2 Flash | 1.00 | 0.89 | 0.60 | 1.00 | 1.00 | 0.90 | $0.001 |
| Devstral | 1.00 | 0.50 | 0.80 | 1.00 | 1.00 | 0.86 | $0.004 |
| Kimi K2.5 | 0.81 | 0.89 | 0.80 | 0.80 | 1.00 | 0.86 | $0.038 |
| Qwen 3.5 397B | 0.59 | 0.88 | 0.80 | 1.00 | 1.00 | 0.85 | $0.033 |

HALLAZGOS:
1. Step 3.5 Flash #1 overall (0.98), MiMo ratio absurdo (0.90 a $0.001)
2. T5 Síntesis: 6/6 modelos 1.00 — TODOS sintetizan bien
3. Devstral: coding specialist (T4=1.00)
4. Todos los roles cubiertos: evaluador, debugger, pizarra, patcher, math, tier barato


=== EXP 5b — MODELOS NUEVOS EN PIPELINE ===

| Config | T1 | T4 |
|--------|:---:|:---:|
| N2_cheap (MiMo+Nemotron+Step) | 100% | 0% |
| N3_coding (Step+Devstral) | 100% | 0% |

HALLAZGOS:
1. T1 RESUELTO: 0%→100% con modelos nuevos
2. T4 SIGUE 0%: think-tag blowup + async mocking imposible
3. Regla skip-E5/E6 VALIDADA: reviewer/optimizer rompen código funcional


=== EXP 6 — AGENTE DE CODING OS (loop agéntico, 460 líneas) ===

| Approach | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Exp 5 Config A | 0% | 94% | 100% | 0% | 83% | 56% | $0.33 |
| **Agente multi-modelo** | **100%** | **100%** | **100%** | **93%** | **100%** | **99%** | $1.57 |
| Agente Devstral solo | 83% | — | — | **100%** | — | — | $0.66 |
| Agente MiMo solo | 79% | — | — | 96% | — | — | $0.92 |

HALLAZGOS:
1. T4 RESUELTO: 0% en 11 configs pipeline → 93% con agente (13/14 tests)
2. Devstral solo = 100% en T4 a $0.66
3. Step 0% en T4 como agente — piensa sin actuar
4. MiMo+loop (88%) SUPERA pipeline caro sin loop (56%)
5. 460 líneas bastan. Loop > cantidad de modelos
6. Si tests pasan 100% → finish() inmediato (reviewers rompen código)

AGENTE: 5 herramientas (read_file, write_file, run_command, list_dir, search_files) + finish
ROUTING: Devstral (genera) → Step (debugea tras 2 errores) → MiMo (fallback)
SEGURIDAD: sandbox path, command blacklist, stuck detection


=== EXP 7 — REDISEÑO CHIEF OS (5 modelos, 3 rondas) ===

DISEÑO CONSENSUADO: 8 componentes
1. Dispatcher Inteligente 2. Evaluador de Respuesta 3. Planificador Razonamiento
4. Matriz Cognitiva Adapter ($0) 5. Agente de Coding 6. Monitor Rendimiento
7. Optimizador Configuración 8. Logger & Telemetría ($0)
COSTE: $0.0013/turno (15x bajo target)
PROBLEMA: 4/10 checks vs Maestro fallan (estigmergia, 8 ops, pipeline 7 pasos, enjambre código)


=== EXP 8 — AUDITORÍA COMPLETA (5 modelos, 3 rondas) ===

CONSENSO 5/5:
1. Chief deprecado vs operativo — contradicción crítica (D1)
2. No hay corrección de errores (C5)
3. Modelo negocio no validado (C3)
4. Supabase vs fly.io insostenible (D2)
5. Sobrediseño: 17 tipos pensamiento + 6 modos (B3/B4)
6. UI/UX no especificada (C2)
7. Cross-dominio no demostrado (C4)
8. Componentes teóricos sin validación (B1)
9. MVP sobrediseñado (E6)
10. Dependencia Sonnet en 12 agentes (D3)

DECISIONES CR0: Eliminar Chief, migrar fly.io, eliminar Sonnet del MVP,
podar componentes teóricos, MVP con 6 INTs irreducibles, presupuesto realista


=== MAPA DEFINITIVO DE MODELOS OS ===

| Modelo | Score | Coste | Rol óptimo |
|--------|:---:|:---:|------------|
| Step 3.5 Flash | 0.98 | $0.019 | Debugger, Evaluador, Razonador |
| Nemotron Super | 0.96 | $0.007 | Validador numérico, Evaluador |
| MiMo V2 Flash | 0.90 | $0.001 | Workhorse, Arquitecto, Fallback |
| Devstral | 0.86 | $0.004 | Agente coding, Implementador |
| Kimi K2.5 | 0.86 | $0.038 | Pizarra, Auditor contexto largo |
| Qwen 3.5 397B | 0.85 | $0.033 | Evaluador, Implementador |
| Cogito 671B | #1 sint. | $0.125 | Sintetizador mesa redonda |
| DeepSeek V3.2 | — | $1.10/M | Diseño, Orquestación |

REGLAS EMPÍRICAS:
1. Loop > modelos: MiMo+loop (88%) supera pipeline caro sin loop (56%)
2. Barato+bueno > caro+solo: MiMo $0.001 con 0.90
3. Diversidad > calidad individual
4. Reviewers rompen código: si tests 100% → PARAR
5. Think-tag blowup: Step/Qwen gastan 16K pensando sin output
6. Devstral = agente coding ideal: rápido (4-10s), barato ($0.004), T4=100%


=== COSTES REALES ===

| Experimento | Estimado | Real | Factor |
|-------------|----------|------|--------|
| Exp 5 (40 runs) | $5-15 | $1.50 | 3-10x sobrestimado |
| Exp 1 bis (30 runs) | $1-3 | $0.10 | 10-30x sobrestimado |
| Exp 6 (agente) | $3-6 | $1.57 | 2-4x sobrestimado |
| Exp 7 (15 calls) | $3-5 | $0.15 | 20-33x sobrestimado |
| TOTAL 6 exps | $14-33 | ~$5.50 | 3-6x sobrestimado |
