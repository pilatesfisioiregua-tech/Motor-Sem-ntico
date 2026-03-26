# OMNI-MIND — Vision de Negocio

## Que es
Una plataforma de agentes IA especializados que operan negocios de forma autonoma.
No es un SaaS. No es un chatbot. Es un **equipo de IA completo** que gestiona un negocio.

## El insight
Las empresas que ya facturan miles de millones con IA tienen:
- Un CEO humano con vision
- Todo lo demas son agentes IA

OMNI-MIND es la fabrica que produce esos agentes para cualquier negocio.

## Producto: Exocortex Agentico
Un cerebro externo para tu negocio compuesto por agentes especializados que:
1. **Leen tareas** del repositorio o base de datos
2. **Ejecutan** de forma autonoma (diagnosticar, predecir, operar, comunicar)
3. **Aprenden** de los resultados y mejoran

### Para el usuario final (dueno de negocio)
- "Conecta tus datos → tu equipo de IA empieza a trabajar"
- No necesita saber de IA, APIs, o programacion
- Ve resultados: clientes contactados, cobros gestionados, predicciones cumplidas

### Para la fabrica interna (nosotros)
- Agentes que construyen agentes
- Pipeline: Verificador → Builder → Deploy → Verificar → Loop
- Autonomo 24/7

## Arquitectura: Enjambre de Agentes Especializados

### Agentes de Fabrica (construyen el producto)
| # | Agente | Funcion | Estado |
|---|--------|---------|--------|
| 1 | Verificador | Testea todo E2E, encuentra fallos | OPERATIVO |
| 2 | Builder | Lee hallazgos, genera fixes, deploya | OPERATIVO |
| 3 | Investigador | Escanea mercado, competidores, oportunidades | PENDIENTE |
| 4 | Disenador | UX/UI, flujos, estetica | PENDIENTE |
| 5 | Arquitecto | Specs tecnicas, briefings | PENDIENTE |
| 6 | Operador | Monitoring, alertas, auto-healing | PARCIAL (mecanico.py) |
| 7 | Pulidor | Copy, micro-UX, coherencia | PENDIENTE |
| 8 | Monitor CEO | Resumen diario, prioridades | PENDIENTE |

### Agentes de Producto (operan el negocio del cliente)
| # | Agente | Funcion |
|---|--------|---------|
| 1 | Diagnosticador | Analiza salud del negocio (7 funciones vitales) |
| 2 | Predictor | Abandonos, demanda, cashflow |
| 3 | Comunicador | WhatsApp, email, notificaciones |
| 4 | Cobrador | Cargos, recordatorios, planes de pago |
| 5 | Optimizador | Horarios, precios, recursos |
| 6 | Captador | Leads, seguimiento, conversion |
| 7 | Retenedor | Detecta riesgo de baja, actua |

## Como funciona un agente

Un agente es:
```
SENSOR → PROCESADOR → ACTUADOR
  (lee)    (decide)     (hace)
```

En la practica:
1. **Sensor**: Lee de la DB, del repo, de APIs externas, o de marcas estigmergicas
2. **Procesador**: Codigo puro ($0) para lo determinista + LLM para lo que requiere juicio
3. **Actuador**: Escribe en DB, envia WhatsApp, modifica codigo, deploya, crea marcas

### Comunicacion entre agentes
- **NO** llamadas directas entre agentes
- **SI** estigmergia: escriben marcas en `marcas_estigmergicas` que otros leen
- Un agente deja una marca → otro la detecta → actua
- Como hormigas con feromonas: escala sin coordinacion central

## Modelo de negocio

### Fase 1: Verticales (0-12 meses)
- Pilates/Yoga/Fitness → ya funcional
- Clinicas dentales/fisio → mismo modelo
- Precio: 149-299 EUR/mes
- Meta: 100 clientes = 15-30K MRR

### Fase 2: Plataforma (12-24 meses)
- API publica para que otros construyan agentes
- Marketplace de agentes especializados
- Precio: revenue share + suscripcion

### Fase 3: Fabrica (24+ meses)
- Cualquier negocio puede tener su equipo de IA
- Self-service: sube tus datos → equipo operativo en horas
- El moat: datos cruzados entre negocios del mismo vertical

## Metricas que importan
- Score vendible del Verificador (hoy: 2/10, objetivo: 8/10)
- Endpoints funcionando sin error (hoy: 39/39)
- Tiempo de onboarding nuevo tenant (hoy: dias, objetivo: minutos)
- Coste por cliente por mes en LLM (hoy: ~15 EUR)
- Clientes pagando (hoy: 0, objetivo 30d: 5)

## Siguiente paso inmediato
1. Subir score vendible de 2/10 a 8/10 con la fabrica (Verificador+Builder)
2. Landing page + flujo de registro
3. Onboarding automatico (1 agente)
4. 5 clientes beta gratis → feedback → iterar
5. Cobrar
