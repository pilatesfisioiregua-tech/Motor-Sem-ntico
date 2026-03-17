# 1. PRODUCTO

**Producto concreto:**  
**OMNI-MIND Exocortex para Pequeños Negocios de Servicios** — un sistema SaaS que actúa como "cerebro externo" para dueños de estudios de Pilates, clínicas de fisioterapia, dentistas, etc. No es un chatbot: es un diagnóstico cognitivo estructurado que, conectándose a los datos del negocio (agenda, clientes, ingresos), genera preguntas que revelan gaps estructurales, contradicciones y oportunidades invisibles.

**Usuario:**  
Dueño de un pequeño negocio de servicios (1-5 empleados, facturación €10k-50k/mes) que toma decisiones basadas en intuición o datos superficiales. No tiene acceso a consultoría estratégica de alto nivel.

**Problema que resuelve:**  
Falta de diagnóstico profundo. El usuario ve sus números pero no percibe patrones sistémicos (ej: "el sillón 3 está vacío el 40% del tiempo, eso son €6k/mes perdidos" — Exp 8, INT-02). OMNI-MIND identifica estos gaps mediante 18 inteligencias especializadas (lógica, ecológica, política, existencial, etc.) que ningún ChatGPT puede replicar.

**Wow moment:**  
El usuario recibe, tras conectar sus datos de agenda, una pregunta como:  
*"¿Por qué sigues trabajando 60h/semana cuando tu modelo de negocio ya no requiere tu presencia física en cada sesión? El sistema identifica que tu esposa está cerca del burnout (INT-08, Social) y que tu padre murió de un infarto por estrés (INT-12, Narrativa). La expansión a 5 sillones (que planeas) aumentaría el burn rate un 40% sin resolver el cuello de botella humano. En cambio, podrías entrenar a un asistente para que gestione el sillón 3, liberando 15h/semana tuyas en 3 meses."*  
Eso es un insight que un consultor de 20 años tardaría semanas en descubrir.

**Diferenciación vs ChatGPT/Claude/Gemini:**  
- **No es un asistente conversacional:** No responde preguntas, las *genera* para dirigir tu atención a lo que importa.  
- **Matriz 3L×7F:** Estructura de diagnóstico que ningún competidor tiene. Mapea gaps en 21 celdas (Salud/Sentido/Continuidad × 7 funciones).  
- **Multi-modelo especializado:** Usa 3-5 modelos OS en paralelo porque cada uno domina diferentes celdas (DeepSeek V3.1 en Frontera, GPT-OSS en Depurar, R1 en Continuidad — Tabla 3, Exp 4). Un solo modelo no cubre todo.  
- **Flywheel cross-dominio:** Cada cliente nuevo enriquece la Matriz para todos los demás. Lo que un estudio de Pilates descubre sobre gestión de turnos, una clínica de fisio lo recibe si su patrón de gaps es similar.  
- **Costo operativo ultra-bajo:** $0.08-0.35 por diagnóstico completo (Exp 6) vs $1-2 de consultoría humana.  

---

# 2. VALOR

**Valor real basado en datos experimentales:**  
- **Cobertura diagnóstica:** Exp 4 demuestra que 3 modelos OS (V3.1, R1, GPT-OSS) superan a Claude (2.19 vs 1.79 score medio) y cubren 20/21 celdas vs 15/21 de Claude.  
- **Resolución de problemas estructurales:** Exp 6 resolvió T4 (orquestador asíncrono) que 11 pipelines lineales no pudieron (0% → 93%). Esto demuestra que el enfoque de agente con loop (observe→think→act) rompe techos estructurales.  
- **Costo-efectividad:** Exp 1bis muestra MiMo V2 Flash ($0.001) con score 0.90, Nemotron Super ($0.007) con 0.96. Step 3.5 Flash ($0.019) es el mejor debugger (100% en T4). El costo real por diagnóstico completo (Motor vN) es $0.10-0.35 (Exp 6), no los $0.50-1.50 inicialmente estimados.  
- **Aprendizaje continuo:** Cada ejecución registra gap_pre/gap_post por celda (datapoints_efectividad). El Gestor de la Matriz usa esto para asignar modelos óptimos y podar preguntas inefectivas (tasa<0.05).  

**¿Qué pueden hacer los modelos OS que NO pueden los chatbots genéricos?**  
- **Especialización por celda:** Un modelo generalista (GPT-4) tiene score ~1.5 en la Matriz. Los modelos OS especializados (V3.1, R1, GPT-OSS) tienen scores 2.15-2.19 porque están optimizados para ciertos tipos de razonamiento (Frontera, Depurar, Continuidad).  
- **Diversidad como dimensión algebraica:** La combinación de modelos diferentes genera conexiones cross-lente que un solo modelo no ve (425 conexiones en Exp 4.3).  
- **Costo marginal bajo:** MiMo V2 Flash ($0.001) permite ejecución masiva para poblar la Matriz, algo inviable con modelos premium.  

**¿La Matriz 3L×7F aporta valor perceptible al usuario o es infraestructura invisible?**  
Aporta valor **perceptible** porque estructura el diagnóstico en 21 celdas concretas. El usuario ve un mapa de "qué áreas están débiles" (ej: "Frontera×Salud: 0.3, necesitas límites humanos"). No es un detalle técnico; es el interfaz de diagnóstico. Las preguntas generadas tienen coordenadas exactas (INT-04 × Frontera × Salud) y eso permite aprendizaje transferible entre dominios.  

**¿El multi-modelo (enjambre) aporta valor vs un solo modelo bueno?**  
**Sí, empíricamente:** Exp 4.3 (mente distribuida) generó 425 conexiones cross-lente y 239 puntos ciegos que la mesa redonda (modelo único) no detectó. Además, ningún modelo domina todas las celdas: V3.1 es mejor en 7 celdas, R1 en 7, GPT-OSS en 4. El enjambre siempre gana. El costo adicional de usar 3-5 modelos en paralelo se justifica por la calidad superior (nivel medio 3.99 vs 3.27 de mesa redonda).  

---

# 3. ARQUITECTURA MÍNIMA VIABLE

**Con los datos de Exp 6 (agente 460 líneas, 99%), la arquitectura mínima es:**

1. **Motor vN (pipeline 7 pasos):**  
   - Paso 0: Detector de huecos (7 primitivas + 8 operaciones sintácticas) — código puro.  
   - Paso 1: Campo de gradientes (21 celdas) — código + Haiku ligero ($0.01).  
   - Paso 2: Routing por gradiente — asigna modelos por celda usando **Tabla 3 de Exp 4** (asignación fija inicial).  
   - Paso 3: Composición (NetworkX, 13 reglas) — código puro.  
   - Paso 4: Ensamblaje del prompt — código puro.  
   - Paso 5: Ejecución multi-modelo — usa modelos OS según celda (ej: V3.1 para Conservar×Frontera).  
   - Paso 6: Verificación de cierre — código + Haiku ($0.01).  
   - Paso 7: Integración + registro — Sonnet solo si es necesario, sino V3.1 ($0.005).  

2. **Gestor de la Matriz (v0.1):**  
   - No need full learning loop inicial. Usa **asignación fija por celda** (Tabla 3) y actualiza `gap_medio_cerrado` tras cada ejecución (código puro).  
   - Compila "programa de preguntas" para cada caso: para cada celda con gap>0.3, incluye las 3-5 preguntas más efectivas de esa coordenada (de la DB).  

3. **Base de datos:**  
   - `preguntas_matriz`: id, inteligencia, lente, función, texto, score_efectividad.  
   - `datapoints_efectividad`: pregunta_id, modelo, gap_pre, gap_post, tasa_cierre.  
   - `sesiones_chief`: sesion_id, input, contexto, modo.  
   - `marcas_estigmergicas`: comunicación entre componentes.  

4. **Agente de Coding (reutilizado de Exp 6):**  
   - 460 líneas con loop observe→think→act, 5 herramientas (read_file, write_file, run_command, list_dir, search_files) + finish.  
   - Routing: Devstral (genera) → Step (debuggea tras 2 errores) → MiMo (fallback).  
   - Se usa para auto-mejora nivel 1: aplicar patches pequeños (<20 líneas) sin intervención humana.  

5. **Frontend chat simple:**  
   - Interfaz de chat que muestra preguntas generadas y permite al usuario responder.  
   - Dashboard mínimo con mapa de 21 celdas (gradientes coloreados) para que el usuario vea "dónde está el problema".  

**Componentes realmente necesarios (solo 5):**  
1. Motor vN (ejecuta Matriz).  
2. Gestor v0.1 (asigna modelos, compila preguntas).  
3. DB (Matriz, sesiones, marcas).  
4. Agente de coding (auto-mejora).  
5. Frontend (chat + dashboard).  

**Qué se elimina del diseño actual sin perder valor:**  
- Chief of Staff completo (24 agentes, pipeline dual, 9 modos).  
- 17 tipos de pensamiento (sobrediseño, solo 6-7 usados).  
- Reactor v3 (12% utilidad).  
- Meta-motor (no validado).  
- Dependencia de Sonnet (reemplazado por OS).  

**Qué se añade que no está diseñado:**  
- **Dashboard de gradientes:** Visualización de las 21 celdas con colores según gap (rojo=crítico, amarillo=medio, verde=ok). Esto es crucial para el wow moment.  
- **Mecanismo de rollback:** Snapshots de la Matriz antes de auto-mejoras (porque Exp 5 mostró que reviewers rompen código funcional en 44% de casos).  
- **Conexión a datos reales:** Conector que lee CSV o API de software de gestión (ej: Books, Calendly) para alimentar Reactor v4.  

---

# 4. IMPLEMENTACIÓN

**¿Qué se puede construir en 1 semana?**  
- Motor vN con 6 INT irreducibles (01, 02, 06, 08, 14, 16) y asignación fija de modelos (usar Tabla 3).  
- DB con tablas mínimas (preguntas_matriz, datapoints_efectividad, sesiones_chief, marcas_estigmergicas).  
- Frontend chat simple (sin dashboard).  
- **Resultado:** Sistema que funciona con casos de cartografía pre-construidos. No hay datos reales ni auto-mejora.  

**¿En 1 mes?**  
- Añadir Gestor v0.1 (actualiza scores, asigna modelos probabilísticamente tras 10+ ejecuciones por celda).  
- Reactor v4 básico: genera preguntas desde datos de telemetría (ej: "cancelaciones >20% → pregunta INT-04 sobre ecosistema").  
- Piloto 1 con Jesús (Pilates): conectar manualmente a sus datos (CSV de reservas/clientes).  
- Agente de coding integrado para auto-mejoras nivel 1 (fontanería).  
- **Resultado:** Primer piloto operativo con datos reales, validación de Reactor v4.  

**¿En 3 meses?**  
- Piloto 2 con mujer de Jesús (Fisioterapia) → validar cross-dominio.  
- Integración API con software de gestión del amigo informático (ej: TPV, calendario).  
- Dashboard de gradientes (21 celdas visualizadas).  
- Mecanismo de rollback (snapshots cada 10 ejecuciones).  
- Auto-mejora nivel 1 funcionando (patches automáticos <20 líneas).  
- **Resultado:** Dos pilotos reales, flywheel validado (o no), producto listo para escalar vía partner de software.  

**Secuencia que maximiza aprendizaje con mínimo esfuerzo:**  
1. **Semana 1-2:** Motor vN MVP + DB + chat. Probar con 10 casos de cartografía existentes.  
2. **Semana 3-4:** Añadir Gestor v0.1 (feedback loop básico). Medir: ¿las preguntas generadas son útiles?  
3. **Mes 2:** Piloto 1 (Jesús). Conectar a sus datos (CSV). Activar Reactor v4. Medir: ¿detecta gaps que Jesús no veía? (encuesta post-diagnóstico).  
4. **Mes 2.5:** Analizar datos de Piloto 1. Si Reactor v4 generó preguntas útiles (utilidad >70%), proceder a Piloto 2. Si no, ajustar Reactor v4.  
5. **Mes 3:** Piloto 2 (Fisio). Validar transferencia cross-dominio: ¿preguntas de Pilotes aplican a fisio? Comparar utilidad percibida.  
6. **Mes 3.5:** Presentar resultados a amigo informático con datos concretos (ej: "detectamos 5 gaps en 3 clientes, uno valía €2k/mes").  

**¿Qué del agente de Exp 6 se reutiliza directamente?**  
- **Loop observe→think→act** (460 líneas).  
- **5 herramientas** (read_file, write_file, run_command, list_dir, search_files).  
- **Stuck detection** (5 patrones: acción repetida×4, error×3, monólogo, ciclo largo, context window).  
- **Budget enforcement** (max $0.015 por ejecución).  
- **Routing multi-modelo** (Devstral genera, Step debuggea, MiMo fallback).  
Se adapta como "Agente de Coding" para auto-mejora nivel 1 (aplicar patches) y para tareas específicas (ej: generar scripts de integración con API).  

**Coste realista por mes de operación (con 10 clientes piloto):**  
- **Consultas:** 10 clientes × 10 consultas/día × 30 días = 3000 consultas/mes.  
- **Costo por consulta:** $0.10 (promedio, con evaluador OS).  
- **Total tokens:** 3000 × $0.10 = **$300/mes**.  
- **Infraestructura fly.io:** ~$100/mes (Postgres, compute).  
- **Total:** **$400/mes**.  
- **Ingresos (10 clientes × €100/mes):** €1000 ≈ $1100.  
- **Margen:** ~65%.  
*(Nota: Exp 7 logró $0.0013/turno, pero eso era sin Motor vN completo. Con Motor completo, $0.10 es realista basado en Exp 6.)*  

---

# 5. NEGOCIO

**¿€50-200/mes es el precio correcto? ¿Para quién?**  
- **Sí, para negocios de servicios que facturan €10k-50k/mes.** €100/mes es 0.2-1% de facturación. Si el sistema detecta una oportunidad de €2k/mes o ahorra 2h/semana del dueño (valor €200/mes), el ROI es claro.  
- **Segmento inicial:** Estudios de Pilates/Yoga, clínicas de fisioterapia, dentistas pequeños (como el caso del briefing). Son negocios con datos estructurados (agenda, clientes) pero sin análisis estratégico.  
- **Precio por volumen:** Escalar a €200/mes para negocios con más empleados (10-20) o que quieran integración API completa.  

**Modelo:** SaaS por negocio/mes. Acceso via web (dashboard + chat). Incluye:  
- Conexión a datos (API/CSV).  
- Diagnósticos ilimitados.  
- Actualizaciones de la Matriz (flywheel).  
- Soporte por email.  

**Competidores reales y diferenciación:**  
| Competidor | Qué hace | Diferenciación OMNI-MIND |
|------------|----------|------------------------|
| **Glean** | Búsqueda empresarial (documentos) | OMNI-MIND no busca, *diagnostica* con Matriz 3L×7F. |
| **Adept** | Agentes de software (automatizan tareas) | OMNI-MIND no automatiza, *piensa* y hace preguntas. |
| **AutoGPT** | Agentes autónomos generales | OMNI-MIND es específico para negocios de servicios, con inteligencias especializadas (política, existencial, etc.). |
| **ChatGPT Plus** | Asistente conversacional | OMNI-MIND usa multi-modelo OS (diversidad > calidad individual) y flywheel cross-dominio. |

**Pilotos propios → amigo informático → escala es la ruta correcta?**  
**Sí, por tres razones:**  
1. **Validación con bajo costo:** Jesús y su mujer son usuarios reales (no teóricos). Sus datos reales validan el Reactor v4 y el flywheel.  
2. **Caso de negocio concreto:** El amigo informático tiene software de gestión existente. Integrar OMNI-MIND como "capa inteligente" es un upsell para sus clientes (ej: "tu software de agenda ahora piensa por ti").  
3. **Escalabilidad through partners:** Vender a miles de pequeños negocios directamente es costoso. Vender a 10 partners de software (que ya tienen 100 clientes cada uno) escala 100x más rápido.  

---

# 6. RIESGOS

**Riesgo #1 que mata el proyecto:**  
**El Gestor de la Matriz es un SPOF (Single Point of Failure).**  
Si el Gestor (que asigna modelos y compila programas) falla, todo el sistema colapsa porque el Motor no sabe qué preguntas ejecutar. En el diseño actual, el Gestor es un servicio externo no implementado.  
**Mitigación:** Implementar fallback en el Motor: si el Gestor no responde en 2s, usar **asignación fija por celda** (Tabla 3) y programa de preguntas genérico (las 50 preguntas base de cada INT). Esto garantiza operación degradada (calidad 80% pero funcional).  

**Asunción no validada más peligrosa:**  
**El flywheel cross-dominio funciona** (que preguntas generadas en Pilates apliquen a Fisioterapia).  
Esto asume que patrones de gaps son transferibles entre dominios (ej: "proveedor único" en restaurante = "único instructor especializado" en Pilates). Exp 8 lo marca como "bloqueante" sin validar.  
**Validación:** En Piloto 2 (Fisio), comparar utilidad de preguntas generadas desde datos de Pilates vs preguntas generadas desde datos de Fisio. Si >60% de las preguntas de Pilates son útiles en Fisio, el flywheel funciona. Si no, necesitamos Reactor v4 por dominio (crecimiento lineal, no exponencial).  

**Qué pasa si el flywheel no funciona?**  
- Cada nuevo dominio requiere su propio Reactor v4 (generar preguntas desde sus datos específicos).  
- El crecimiento de la Matriz es lineal por dominio, no exponencial.  
- Aún así, el producto funciona: cada dominio tiene su propio exocortex con preguntas adaptadas.  
- El modelo de negocio se ralentiza (más trabajo por cliente), pero sigue siendo viable porque el costo por consulta sigue siendo bajo ($0.10).  

**Otros riesgos menores:**  
- **Coste real vs estimado:** Si el volumen de consultas escala a 1000/día, el costo tokens podría ser $1000/mes (no $300). Mitigar: optimizar a evaluador OS (bajar a $0.02/turno).  
- **Competencia:** Si un jugador grande (OpenAI, Anthropic) lanza un producto similar con marca, adoption se dificulta. Diferenciación clave: flywheel y multi-modelo especializado.  
- **Regulaciones datos:** Conectar a datos de negocio requiere consentimiento y compliance GDPR. Usar anonimización en telemetría.  

---

**Conclusión:**  
El producto concreto es un **exocortex SaaS para pequeños negocios de servicios** que usa una Matriz 3L×7F×18INT para generar preguntas de diagnóstico profundo. El MVP se construye en 1 mes (Motor vN + Gestor v0.1 + Reactor v4 básico) y se valida en 3 meses con dos pilotos reales. La arquitectura mínima son 5 componentes (Motor, Gestor, DB, Agente coding, Frontend). El costo operativo es $400/mes para 10 clientes, con margen >60% a €100/mes. El riesgo principal es el SPOF del Gestor (fallback con asignación fija lo mitiga). La apuesta crítica es el flywheel cross-dominio (validar en Piloto 2).