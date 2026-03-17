# Roadmap Realista para OMNI-MIND: De Sistema de Investigación a Producto Vendible

**Advertencia previa:** Este roadmap es brutalmente honesto. La documentación de OMNI-MIND describe un sistema de **investigación avanzada**, no un producto. Tiene 157 componentes, 62 agentes, múltiples enjambres, una matriz abstracta de 378 celdas, y dependencias de 10+ modelos LLM. Esto es **sobrediseño puro** para cualquier caso de uso comercial viable.

## Diagnóstico Crítico

### Lo que SÍ funciona (validado empíricamente):
1. **Pipeline conversacional con memoria inter-sesiones** - Probado en producción con 5+ turnos
2. **Comunicación por estigmergia** - Patrón robusto para agentes autónomos
3. **Migración a modelos OS** - Coste reducido de $14/mes a $0.50-1/mes
4. **Gateway API con multi-tenancy** - Permite vender a múltiples clientes
5. **Compresor de memoria y perfil de usuario** - Funciona y genera valor

### Lo que es HUMO (eliminar inmediatamente):
1. **Matriz 3L×7F×18INT** - Concepto abstracto sin valor comercial. Nadie pagará por "378 celdas con gradientes".
2. **Álgebra del cálculo semántico** - Matemáticas innecesarias. El "compilador de prompts" es solo un selector de preguntas.
3. **Mecanismos multi-modelo complejos** (Exp 4): pizarra distribuida, mesa redonda, sintetizador. Coste $2-5 por análisis. Inviable comercialmente.
4. **Fábrica de exocortex autónoma** - Ciencia ficción. "El sistema se diseña a sí mismo" no funciona en producción.
5. **Auto-evolución via semillas dormidas** - Riesgo catastrófico. Un sistema que se modifica solo es inseguro para clientes.
6. **18 inteligencias irreducibles** - Pseudociencia. Reducir a 3-4 capacidades medibles.

### El problema fundamental:
**OMNI-MIND es un cerebro buscando un problema.** Tiene soluciones técnicas brillantes (estigmergia,管道, memoria) pero no un **producto-market fit** claro. Los casos de uso propuestos (Pilates, fisioterapia) son nichos pequeños que no justifican esta complejidad.

---

## Roadmap de 12 Meses: Del Prototipo al Producto

### FASE 0: DECISIÓN ESTRATÉGICA (Semana 1-2)

**Objetivo:** Elegir UN dominio vertical y simplificar radicalmente.

**Opción A (RECOMENDADA): Asistente para Consultoría de Negocios**
- Mercado: $10B+ (consultores independientes, pequeñas empresas)
- Problema real: "Necesito análisis estructurado de mi negocio pero no tengo un consultor"
- Valor percibido: Alto ($50-200/mes)
- Datos disponibles: Métricas, finanzas, operaciones (ya digitalizadas)

**Opción B: Asistente para Clínicas de Salud Mental**
- Mercado: $5B+ (terapeutas, psicólogos)
- Problema: "Necesito seguimiento estructurado de pacientes entre sesiones"
- Valor: $30-100/mes
- Problema: Sensibilidad de datos (HIPAA), regulación

**Opción C: Asistente para Estudios de Yoga/Pilates** (propuesto en docs)
- Mercado: Pequeño (<$500M global)
- Problema: "Gestión de clientes y progreso"
- Valor: $20-50/mes
- **DESCARTAR**: Mercado pequeño, software de gestión existente (MindBody) ya cubre necesidades básicas.

**Decisión CR0:** **Opción A - Consultoría de Negocios**. Mayor mercado, datos estructurados disponibles, precio just