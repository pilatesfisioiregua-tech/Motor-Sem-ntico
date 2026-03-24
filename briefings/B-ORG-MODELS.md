# B-ORG-MODELS: Migrar TODOS los modelos LLM a los adecuados por tarea

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — ejecutar junto con B-ORG-BRAIN
**Esfuerzo:** 1 briefing
**Impacto:** Todo el sistema pasa de modelos inadecuados a modelos óptimos

---

## PROBLEMA

TODOS los componentes LLM del sistema usan modelos equivocados:

| Componente | Modelo ACTUAL (MAL) | Problema |
|---|---|---|
| Séquito 24 asesores | `devstral-2512` | Modelo de código. No entiende álgebra cognitiva ni razonamiento semántico. |
| Séquito síntesis | `glm-5` | No es capaz de integrar 5-8 perspectivas divergentes con coherencia. |
| Cockpit chat | `deepseek-chat` | Malo en español peninsular. Tool calling poco fiable. |
| Portal cliente | `deepseek-chat` | Idem. Los clientes reciben respuestas en español robótico. |
| WA chat | `deepseek-chat` | Idem. Mensajes WA suenan a traducción automática, no a Albelda. |
| Estrategia voz | `deepseek-chat` | Creatividad en español limitada. Marketing genérico. |
| Arquitecto perfiles | `deepseek-chat` | Idem. Perfiles de canales sin matices culturales. |

## SOLUCIÓN

Cambiar env vars y actualizar código donde el modelo está hardcodeado.

## ENV VARS NUEVAS (fly.io secrets)

```bash
# Cerebro organismo — AF1-AF7, Gestor, narrativa
BRAIN_MODEL=openai/gpt-4o

# Razonamiento complejo — Ejecutor, Convergencia
REASONING_MODEL=anthropic/claude-sonnet-4.6

# Séquito — asesores individuales (álgebra cognitiva)
SEQUITO_MODEL=anthropic/claude-sonnet-4.6

# Séquito — síntesis (integrar perspectivas)
SEQUITO_SYNTH_MODEL=anthropic/claude-sonnet-4.6

# Interfaz conversacional — cockpit, portal, WA
CHAT_MODEL=openai/gpt-4o

# Estrategia y contenido — voz, perfiles
STRATEGY_MODEL=openai/gpt-4o
```

## CAMBIOS EN CÓDIGO

### 1. sequito.py

Línea actual:
```python
model = os.getenv("SEQUITO_MODEL", "mistralai/devstral-2512")
```

Cambiar a:
```python
model = os.getenv("SEQUITO_MODEL", "anthropic/claude-sonnet-4.6")
```

Línea actual (síntesis):
```python
model = os.getenv("SEQUITO_SYNTH_MODEL", "z-ai/glm-5")
```

Cambiar a:
```python
model = os.getenv("SEQUITO_SYNTH_MODEL", "anthropic/claude-sonnet-4.6")
```

**IMPORTANTE — Actualizar system prompt del séquito:**

El system prompt de cada asesor debe incluir referencia al framework ACD para que Claude lo entienda y lo use. Añadir al prompt de cada asesor:

```python
prompt = f"""Eres {asesor['nombre']} ({int_id}), asesor de un estudio de Pilates.
Tu ángulo: {asesor['angulo']}
Tu pensamiento asignado: {p_id} — {p_desc}
Tu razonamiento asignado: {r_id} — {r_desc}

FRAMEWORK COGNITIVO (Álgebra Cognitiva Diagnóstica):
- El negocio se diagnostica en 3 LENTES: Salud (S), Sentido (Se), Continuidad (C)
- Cada lente se evalúa a través de 7 FUNCIONES: F1 Conservación, F2 Captación, F3 Depuración, F4 Distribución, F5 Identidad, F6 Adaptación, F7 Replicación
- Tu perspectiva como {int_id} debe cruzar tu PENSAMIENTO ({p_id}) con tu RAZONAMIENTO ({r_id}) para producir un análisis que ningún otro asesor puede dar
- La composición INT×P×R no es conmutativa: el orden importa. Tu ángulo primero, tu pensamiento después, tu razonamiento como método

DATOS REALES DEL NEGOCIO:
{contexto}

PREGUNTA DEL DUEÑO:
{pregunta}

Responde desde tu ángulo específico, usando el tipo de pensamiento y razonamiento asignados.
Sé directo, concreto, con datos. Máximo 200 palabras. Sin preámbulos."""
```

### 2. cockpit.py

Línea actual:
```python
CHAT_MODEL = os.getenv("PORTAL_CHAT_MODEL", "deepseek/deepseek-chat")
```

Cambiar a:
```python
CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-4o")
```

### 3. portal_chat.py

Línea actual:
```python
CHAT_MODEL = os.getenv("PORTAL_CHAT_MODEL", "deepseek/deepseek-chat")
```

Cambiar a:
```python
CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-4o")
```

### 4. wa_chat.py

Si wa_chat.py reutiliza portal_chat.py, el cambio se hereda.
Si tiene su propia referencia al modelo, cambiar igual.

Verificar: `grep -n "model\|MODEL\|deepseek" src/pilates/wa_chat.py`

### 5. voz_estrategia.py

Línea actual:
```python
"model": "deepseek/deepseek-chat",
```

Cambiar a:
```python
STRATEGY_MODEL = os.getenv("STRATEGY_MODEL", "openai/gpt-4o")
# ... en la llamada:
"model": STRATEGY_MODEL,
```

### 6. voz_arquitecto.py

Mismo cambio que voz_estrategia.py — buscar `deepseek/deepseek-chat` y reemplazar por `STRATEGY_MODEL`.

## TESTS

### TEST 1: Séquito usa claude-sonnet-4.6
```python
# Convocar consejo con 1 asesor
result = await convocar_consejo("¿Debería subir precios?", profundidad="rapida")
# Verificar que la respuesta demuestra comprensión del framework ACD
# (menciona lentes, funciones, o cruza P×R)
assert result.asesores[0].respuesta  # No vacío
assert len(result.sintesis) > 100  # Síntesis sustancial
```

### TEST 2: Cockpit responde en español peninsular natural
```python
result = await chat_cockpit("Ponme la agenda", [])
# Debe tutear, sin formalismos, tono Albelda
assert "usted" not in result["respuesta"].lower()
```

### TEST 3: Portal cliente tool calling funciona
```python
# Simular mensaje de cliente
result = await portal_chat("¿Cuándo es mi próxima clase?", cliente_id=UUID)
# Debe llamar herramienta ver_proximas_clases y devolver resultado
assert result  # No crash
```

### TEST 4: Estrategia genera contenido natural en español
```python
result = await calcular_estrategia()
# Verificar que el calendario tiene contenido en español natural
cal = result.get("calendario", [])
if cal:
    # No debe sonar a traducción
    assert "fitness" not in cal[0].get("contenido", "").lower()  # Palabra prohibida
```

---

## COSTE COMPARATIVO

| Antes (todo deepseek/devstral) | Después (modelos correctos) |
|---|---|
| ~$1-2/mes | ~$5.80/mes |
| Español robótico | Español peninsular natural |
| Séquito no entiende ACD | Séquito razona con álgebra cognitiva |
| Cockpit pierde tool calls | Cockpit fiable |
| Organismo = termómetros | Organismo = cerebro vivo |

**Diferencia: $4/mes por un producto que funciona de verdad.**

---

## EJECUCIÓN

```bash
# 1. Actualizar código (Claude Code ejecuta este briefing)
# 2. Añadir env vars a fly.io:
fly secrets set BRAIN_MODEL="openai/gpt-4o" \
  REASONING_MODEL="anthropic/claude-sonnet-4.6" \
  SEQUITO_MODEL="anthropic/claude-sonnet-4.6" \
  SEQUITO_SYNTH_MODEL="anthropic/claude-sonnet-4.6" \
  CHAT_MODEL="openai/gpt-4o" \
  STRATEGY_MODEL="openai/gpt-4o"

# 3. Deploy
fly deploy
```
