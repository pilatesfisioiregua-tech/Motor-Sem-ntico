# B-PIL-18 — Fases D, E, F (Addendum)

**Fecha:** 2026-03-20
**Complementa:** B-PIL-18.md (Fases A, B, C = portal conversacional base)
**Ejecutor:** Claude Code

---

## FASE D: Cobros proactivos + Pago recurrente con tarjeta (Stripe)

### Concepto

El portal detecta saldo pendiente al entrar y lo menciona conversacionalmente.
Opción de tokenizar tarjeta vía Stripe para cobro recurrente automático.
Si un cobro falla → aviso por WA + alerta en feed del estudio.

### D1. Migración SQL

```sql
-- Pago recurrente con tarjeta (Stripe)
CREATE TABLE IF NOT EXISTS om_pago_recurrente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL REFERENCES om_clientes(id),
    stripe_customer_id TEXT,
    stripe_payment_method_id TEXT,
    dia_cobro INTEGER DEFAULT 5,
    importe NUMERIC(10,2),
    estado TEXT DEFAULT 'activo',  -- activo, pausado, cancelado, fallido
    ultimo_cobro DATE,
    ultimo_resultado TEXT,
    intentos_fallidos INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pago_recurrente_activo
    ON om_pago_recurrente(tenant_id, estado, dia_cobro) WHERE estado = 'activo';

CREATE TABLE IF NOT EXISTS om_cobros_automaticos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL,
    pago_recurrente_id UUID REFERENCES om_pago_recurrente(id),
    stripe_payment_intent_id TEXT,
    importe NUMERIC(10,2),
    estado TEXT NOT NULL,
    error_mensaje TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### D2. Backend — src/pilates/stripe_pagos.py

Funciones:
- `crear_checkout_session(cliente_id, importe, dia_cobro)` → URL Stripe Checkout (mode=setup, solo tokeniza)
- `cobrar_recurrente(pago_recurrente_id)` → PaymentIntent off_session con tarjeta tokenizada
- `procesar_webhook_stripe(payload, sig)` → checkout.session.completed → guarda om_pago_recurrente
- `cron_cobros_recurrentes()` → ejecuta todos los cobros del día

Flujo cobro fallido:
1. Intento 1 falla → WA al cliente: "No hemos podido cobrar, paga por Bizum o actualiza tarjeta"
2. Intento 2 falla → repite WA
3. Intento 3 falla → pausa automática + alerta feed a Jesús

### D3. Tools nuevas para portal_chat.py

```python
# Añadir a TOOLS_SPEC:
{
    "type": "function",
    "function": {
        "name": "iniciar_pago_tarjeta",
        "description": "Genera enlace para pagar con tarjeta o configurar cobro recurrente.",
        "parameters": {
            "type": "object",
            "properties": {
                "recurrente": {"type": "boolean", "default": false},
                "dia_cobro": {"type": "integer", "default": 5}
            }
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "estado_pago_recurrente",
        "description": "Consulta si tiene pago recurrente y su estado.",
        "parameters": {"type": "object", "properties": {}}
    }
}
```

### D4. Comportamiento proactivo

En `chat()`, antes de enviar al LLM, inyectar en system prompt:

```python
if saldo_pendiente > 0 and not tiene_recurrente:
    system += f"\n{nombre} tiene {saldo_pendiente:.2f}EUR pendientes. "
    system += "Si el contexto lo permite, menciona el saldo y ofrece configurar pago automático."
```

### D5. Endpoints

```python
@router.post("/stripe/webhook")        # Webhook Stripe
@router.post("/stripe/checkout/{token}") # Crear checkout session
@router.get("/cobros-recurrentes")      # Listar cobros recurrentes
```

**Secrets fly.io:** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
**Coste Stripe:** 1.4% + 0.25EUR/tx (~1.72EUR sobre 105EUR)

---

## FASE E: Sistema de aprendizaje del cliente (engagement social)

### Concepto

El sistema aprende de cada cliente usando mecánicas de redes sociales.
El bot SABE cosas sobre el cliente y adapta su tono y sugerencias.

### Mecánicas implementadas

| Mecánica red social | Implementación |
|---|---|
| **Tracking comportamental** | Cada interacción → om_cliente_eventos (portal, WA, asistencia, pago) |
| **Engagement score (0-100)** | 5 componentes: asistencia (40pts), uso portal (20), pago al día (20), recencia (10), antigüedad (10) |
| **Rachas** | Semanas consecutivas sin falta. Se celebra a las 4, 8, 12 semanas |
| **Nudging predictivo** | Si engagement baja → bot es más amable y motivador. Si racha alta → lo reconoce |
| **Detección de churn** | Score <20=crítico, <40=alto, <60+bajando=medio. Alerta a Jesús + mensaje proactivo |
| **Milestone celebrations** | 1/3/6/12 meses, 25/50/100 clases, rachas. Notificación automática por WA |
| **Preferencias aprendidas** | Hora portal, canal pago, franja horaria, patrones cancelación — deducidos del comportamiento |
| **Cross-sell inteligente** | Solo grupo + engagement >70 → susceptible de ofrecer sesión individual |
| **Cohort intelligence** | (Futuro) Comparar con clientes similares para sugerir servicios |
| **FOMO controlado** | (Futuro) "Solo quedan 2 plazas en tu grupo" |

### E1. Migración SQL

```sql
CREATE TABLE IF NOT EXISTS om_cliente_perfil (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL REFERENCES om_clientes(id) UNIQUE,
    engagement_score INTEGER DEFAULT 50,
    engagement_tendencia TEXT DEFAULT 'estable',    -- subiendo, estable, bajando
    riesgo_churn TEXT DEFAULT 'bajo',               -- bajo, medio, alto, critico
    racha_actual INTEGER DEFAULT 0,
    racha_maxima INTEGER DEFAULT 0,
    hora_preferida_portal TIME,
    franja_preferida TEXT,
    dia_preferido_contacto INTEGER,
    canal_pago_preferido TEXT,
    patron_cancelacion JSONB DEFAULT '{}',
    patron_asistencia JSONB DEFAULT '{}',
    intereses_detectados JSONB DEFAULT '[]',
    total_interacciones_portal INTEGER DEFAULT 0,
    total_mensajes_wa INTEGER DEFAULT 0,
    ultimo_acceso_portal TIMESTAMPTZ,
    promedio_mensajes_por_visita NUMERIC(4,1) DEFAULT 0,
    milestones_celebrados JSONB DEFAULT '[]',
    proximo_milestone TEXT,
    susceptible_individual BOOLEAN DEFAULT FALSE,
    susceptible_upgrade BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_cliente_eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL,
    tipo TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_eventos_cliente ON om_cliente_eventos(cliente_id, tipo, created_at DESC);
```

### E2. Backend — src/pilates/engagement.py

Funciones principales:
- `registrar_evento(cliente_id, tipo, metadata)` — llamar desde cada punto de contacto
- `recalcular_engagement_todos()` — cron semanal, recalcula score de todos
- `_recalcular_engagement_cliente(cliente_id)` — score + racha + preferencias + milestones + churn
- `obtener_contexto_engagement(cliente_id)` — genera texto para inyectar en system prompt del bot

### E3. Milestones definidos

```python
MILESTONES = [
    {"id": "1_mes",     "label": "1 mes en el estudio"},
    {"id": "3_meses",   "label": "3 meses en el estudio"},
    {"id": "6_meses",   "label": "6 meses en el estudio"},
    {"id": "1_anio",    "label": "1 año en el estudio"},
    {"id": "25_clases", "label": "25 clases completadas"},
    {"id": "50_clases", "label": "50 clases completadas"},
    {"id": "100_clases","label": "100 clases completadas"},
    {"id": "racha_4",   "label": "4 semanas sin faltar"},
    {"id": "racha_8",   "label": "8 semanas sin faltar"},
    {"id": "racha_12",  "label": "12 semanas sin faltar"},
    {"id": "pago_al_dia","label": "Siempre al día con pagos (3+ meses)"},
]
```

### E4. Integración en portal_chat.py

```python
# En chat(), tras verificar token:
from src.pilates.engagement import registrar_evento, obtener_contexto_engagement
await registrar_evento(cliente_id, "portal_chat", {"mensaje": mensaje[:100]})

contexto_eng = await obtener_contexto_engagement(cliente_id)
if contexto_eng:
    system += f"\n\nCONTEXTO SOBRE ESTE CLIENTE (usa discretamente):\n{contexto_eng}"
```

El contexto inyectado incluye:
- Si tiene racha larga → "Reconócelo si viene a cuento"
- Si riesgo churn alto → "Sé especialmente amable y proactivo"
- Si engagement bajando → "Que la interacción sea positiva y motivadora"
- Si susceptible cross-sell → "Buen candidato para ofrecer sesión individual"
- Canal pago preferido → para ofrecer el correcto

### E5. Cron — en automatismos.py inicio_semana

```python
from src.pilates.engagement import recalcular_engagement_todos
resultados["engagement"] = await recalcular_engagement_todos()
```

---

## FASE F: Panel de noticias del estudio (Feed en tiempo real)

### Concepto

Feed tipo timeline en el Modo Estudio. Cada evento genera una noticia.
Jesús abre el estudio y ve qué ha pasado sin buscar nada.

### Eventos que generan noticias

| Evento | Icono | Severidad |
|---|---|---|
| Cliente cancela clase | 🔴 | warning |
| Pago recibido | 💰 | success |
| Solicitud del portal | 📋 | warning |
| Alerta retención | ⚠️ | danger |
| Milestone logrado | 🏆 | success |
| Cobro automático fallido | 🔴 | danger |
| Nuevo onboarding completado | 🆕 | success |
| Lista espera → hueco notificado | 🔔 | info |
| Engagement cayendo fuerte | 📉 | warning |
| Propuestas Voz pendientes | 💬 | info |

### F1. Migración SQL

```sql
CREATE TABLE IF NOT EXISTS om_feed_estudio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    tipo TEXT NOT NULL,
    icono TEXT NOT NULL,
    titulo TEXT NOT NULL,
    detalle TEXT,
    cliente_id UUID,
    severidad TEXT DEFAULT 'info',  -- info, warning, success, danger
    leido BOOLEAN DEFAULT FALSE,
    accion_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_feed_reciente ON om_feed_estudio(tenant_id, created_at DESC);
CREATE INDEX idx_feed_no_leido ON om_feed_estudio(tenant_id, leido) WHERE leido = FALSE;
```

### F2. Backend — src/pilates/feed.py

```python
async def publicar(tipo, icono, titulo, detalle=None, cliente_id=None, severidad="info", accion_url=None)

# Helpers:
async def feed_cancelacion(nombre, fecha, hora, cliente_id)
async def feed_pago(nombre, metodo, monto, cliente_id)
async def feed_solicitud(nombre, tipo, descripcion, cliente_id)
async def feed_alerta(nombre, tipo_alerta, detalle, cliente_id)
async def feed_milestone(nombre, milestone, cliente_id)
async def feed_cobro_fallido(nombre, monto, cliente_id)
async def feed_onboarding(nombre, grupo, cliente_id)
async def feed_lista_espera(nombre, detalle, cliente_id)
async def feed_engagement(nombre, de_score, a_score, cliente_id)
```

### F3. Endpoints

```python
@router.get("/feed")                    # Timeline (limit, solo_no_leidos)
@router.post("/feed/marcar-leido")      # {ids: [...]} o {todos: true}
@router.get("/feed/count")              # Badge: {"no_leidos": N}
```

### F4. Integración — llamar feed.publicar() desde:

- `portal_chat.py` → tras cancelación, pago, solicitud
- `automatismos.py` → tras alertas retención
- `engagement.py` → tras milestones y caídas de engagement
- `stripe_pagos.py` → tras cobro ok o fallido
- `router.py` completar_onboarding → feed_onboarding
- `check_lista_espera` → feed_lista_espera

### F5. Frontend — FeedEstudio.jsx

- Badge rojo con contador no leídos (esquina superior)
- Panel lateral slide-in con timeline
- Cada noticia: icono + título + detalle + timestamp + color severidad
- Click → deep link a sección relevante
- Botón "marcar todas como leídas"
- Polling cada 30s a `/feed/count`, carga completa al abrir panel

---

## ORDEN DE IMPLEMENTACIÓN RECOMENDADO

| Fase | Qué | Complejidad | Dependencia |
|---|---|---|---|
| A | Motor conversacional + lista espera | Alta | — |
| B | Frontend chat | Media | A |
| C | Verificación base | — | A+B |
| F | Feed estudio | Baja | — (independiente) |
| E | Engagement + aprendizaje | Media | A (para tracking) |
| D | Stripe pagos | Media | Cuenta Stripe |

**F antes de E** porque el feed es rápido de implementar y da visibilidad inmediata.
**D al final** porque requiere cuenta Stripe configurada.

---

## VERIFICACIÓN COMPLETA

```bash
# Tests originales C1-C6 (portal base)

# C7. Stripe checkout
curl -X POST .../stripe/checkout/{TOKEN} -d '{"importe":105,"dia_cobro":5}'
# PASS: devuelve checkout_url

# C8. Engagement recalculado
curl -X POST .../cron/inicio_semana
# PASS: engagement recalculado para todos

# C9. Feed
curl .../feed?limit=10
# PASS: lista noticias con icono, titulo, severidad

# C10. Feed count
curl .../feed/count
# PASS: {"no_leidos": N}

# C11. Bot usa contexto engagement
# Escribir algo en portal → verificar que usa racha/preferencias en respuesta

# C12. Milestone WA
# Forzar milestone → verificar WA enviado + feed publicado
```
