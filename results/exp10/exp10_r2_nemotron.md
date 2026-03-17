# Roadmap Realista para OMNI-MIND: De Sistema de Investigación a Producto Vendible

## **Fase 0: Estabilización Inmediata (0-3 meses)**  
**Objetivo:** Resolver bloqueos técnicos y establecer base para MVP.  
**Entregables:**  
- **Migración a fly.io (2 semanas):**  
  - Migrar datos críticos (Matriz, ejecuciones, telemetría).  
  - Desactivar Supabase gradualmente.  
  - **Coste:** ~$1,500 (dev time + potential fly.io costs).  
- **Primitivas esenciales (3 semanas):**  
  - Completar **sustantivizar**, **sujeto-predicado**, **adjetivar** (v2).  
  - **Coste:** ~$3,000 (dev time).  
- **Motor orquestador simplificado (3 weeks):**  
  - Reducir de 7 a 4 pasos (huecos → routing → ejecución → verificación).  
  - **Coste:** ~$2,000.  
- **Gestor de Matriz básico (2 weeks):**  
  - Tabla de efectividad, vista materializada, asignación estática de modelos.  
  - **Coste:** ~$1,500.  

**KPIs:**  
- Sistema funcional en fly.io.  
- Primitivas esenciales desplegadas.  
- Motor orquestador simplificado.  

---

## **Fase 1: MVP para Consultoría de Negocios (3-6 months)**  
**Objetivo:** Validar valor con usuarios reales.  
**Entregables:**  
- **Motor vN + Gestor + 3 primitivas (6 weeks):**  
  - Ejecución de análisis estructurado.  
  - **Coste:** ~$4,500.  
- **Reactor v4 Piloto (4 weeks):**  
  - Generación de preguntas desde datos reales de 2 negocios (Pilates + Fisioterapia).  
  - **Coste:** ~$3,000.  
- **Interfaz Básica (3 weeks):**  
  - Consola web PWA + polling API.  
  - **Coste:** ~$2,500.  
- **Pilotos con 2 negocios (2 weeks):**  
  - Validación de 3-5 gaps cerrados.  
  - **Coste:** ~$1,000.  

**KPIs:**  
- 80% de preguntas generadas cierran gaps reales.  
- 2 negocios usando el sistema regularmente.  

---

## **Fase 2: Escalar y Monetizar (6-12 months)**  
**Objetivo:** Convertir en producto sostenible.  
**Entregables:**  
- **Fábrica de Exocortex (4 weeks):**  
  - Plantilla para conectar software de gestión (TPV, ERP).  
  - **Coste:** ~$4,000.  
- **Modelo de Precios (2 weeks):**  
  - Básico ($99/mes), Pro ($299/mes + %).  
  - **Coste:** ~$1,000.  
- **Automatización de Mejora (3 weeks):**  
  - Pipeline YAML → deploy → tests → rollback.  
  - **Coste:** ~$2,500.  
- **Escalado de Infra (3 weeks):**  
  - Optimizar costes LLM (dial-down, model selection).  
  - **Coste:** ~$3,000.  

**KPIs:**  
- 10+ exocortex activos.  
- MRR de $1,500.  
- Coste por caso < $0.10.  

---

## **Fase 3: Optimización y Expansión (12+ months)**  
**Objetivo:** Mejorar eficiencia y expandir a nuevos verticales.  
**Entregables:**  
- **Sustitución de Sonnet (2 weeks):**  
  - Migrar evaluación a Cogito-671B.  
  - **Coste:** ~$1,500.  
- **Auto-configuración del Motor (3 weeks):**  
  - Asignación dinámica de modelos basada en datos históricos.  
  - **Coste:** ~$4,000.  
- **Telemetría Predictiva (3 weeks):**  
  - Dashboard que muestra ROI de análisis.  
  - **Coste:** ~$3,500.  
- **Expansión a Verticales (4 weeks):**  
  - Salud mental, educación, etc.  
  - **Coste:** ~$6,000.  

**KPIs:**  
- Margen EBITDA > 40%.  
- 50+ exocortex activos.  
- NPS > 40.  

---

## **Riesgos y Mitigación**  
1. **Infraestructura no escalable:** Migrar a arquitectura serverless con auto-scaling.  
2. **Costes LLM no controlados:** Implementar dial-down y model selection.  
3. **Adopción baja:** Enfocarse en valor demostrable y soporte cliente.  
4. **Complejidad residual:** Mantener auditorías regulares para eliminar sobrediseño.  

---

## **Conclusión**  
OMNI-MIND puede convertirse en un producto vendible enfocado en consultoría para pequeñas empresas, con un roadmap de 12 meses, $25K-$30K de inversión, y un MRR potencial de $1,500-$2,000 en 6 meses. La clave es simplificar, validar con usuarios reales, y construir sobre una infraestructura escalable.