# TEST DE VALIDACIÓN DE MODELOS — Post BRIEFING_06

> Ejecutar con Claude Code después de que BRIEFING_06 esté desplegado.
> Objetivo: determinar si los modelos OS actuales son capaces con la infraestructura arreglada.
> NO arreglar nada durante los tests. Solo ejecutar y reportar resultados.

---

## INSTRUCCIONES PARA CLAUDE CODE

Ejecuta los 4 tests en orden. Para cada test:
1. Ejecuta EXACTAMENTE lo que dice
2. Mide: iteraciones usadas, tiempo, errores, resultado correcto sí/no
3. NO arregles bugs que encuentres — solo reporta
4. Al final genera un RESUMEN con tabla de resultados

Usa Code OS via la API local: `http://localhost:8080` o `https://chief-os-omni.fly.dev`

---

## TEST 1: QUICK — Tarea trivial

**Objetivo:** Verificar que el modelo puede hacer una edición simple sin perderse.

**Ejecución:**
```bash
# Crear archivo de prueba
cat > /tmp/test_model_validation.py << 'EOF'
def get_gestor():
    """Obtener instancia del gestor."""
    return GestorGAMC()

def calcular_total(items):
    """Calcula el total de una lista."""
    total = 0
    for item in items:
        total += item
    return total

class MiClase:
    def get_gestor(self):
        return self._gestor
EOF
```

Ahora llama a Code OS con esta tarea:
```
POST /code-os/execute
{
  "input": "En el archivo /tmp/test_model_validation.py, renombra la función get_gestor a obtener_gestor (las 2 ocurrencias: la función standalone y el método de MiClase). No toques calcular_total.",
  "mode": "auto"
}
```

**Criterio de éxito:**
- Completar en ≤ 8 iteraciones
- Las 2 ocurrencias de `get_gestor` renombradas a `obtener_gestor`
- `calcular_total` intacta
- Sin errores

---

## TEST 2: ANÁLISIS — Leer y extraer info

**Objetivo:** Verificar que el modelo puede leer un archivo y extraer información correcta.

**Ejecución:**
```
POST /code-os/execute
{
  "input": "Lee el archivo @project/core/motor_vn.py y lista TODOS los métodos de la clase MotorVN (solo los nombres, como lista). No modifiques nada.",
  "mode": "auto"
}
```

**Criterio de éxito:**
- Completar en ≤ 12 iteraciones
- Debe listar al menos estos métodos: `ejecutar`, `_seleccionar_modelo`, `_fase_compilacion`, `_fase_ejecucion`, `_pre_validar`, `_post_validar`, `_generar_prompt_int`, `_generar_prompt_preguntas`, `_llamar_llm`, `_evaluar`, `_integrar`, `_persistir_programa`, `_calcular_tasa_cierre`, `_actualizar_programa_post_ejecucion`, `_registrar`, `_preflight_fok`, `_ajustar_tier_criticality`, `_postflight_jol`, `_flywheel_update`
- Sin modificar ningún archivo
- Sin errores

---

## TEST 3: EXECUTE — Crear algo nuevo

**Objetivo:** Verificar que el modelo puede crear código funcional.

**Ejecución:**
```
POST /code-os/execute
{
  "input": "Añade un endpoint GET /test/ping en @project/api.py que devuelva {\"status\": \"pong\", \"timestamp\": <timestamp ISO actual>, \"version\": \"3.4.0\"}. Usa datetime.datetime.now(datetime.timezone.utc).isoformat() para el timestamp. Añádelo junto a los otros endpoints GET simples (cerca de /health). Verifica que el código es sintácticamente correcto.",
  "mode": "auto"
}
```

**Criterio de éxito:**
- Completar en ≤ 20 iteraciones
- Endpoint añadido en api.py
- Código sintácticamente correcto (python -c "import ast; ast.parse(open('api.py').read())")
- Devuelve los 3 campos esperados
- Sin romper endpoints existentes

---

## TEST 4: DEEP — Diagnosticar y arreglar

**Objetivo:** Verificar que el modelo puede razonar sobre un problema complejo y aplicar un fix.

**Ejecución:**
```
POST /code-os/execute
{
  "input": "Diagnostica por qué el endpoint GET /gestor/consistencia reporta consistente=false. Usa http_request para llamar al endpoint, analiza la respuesta, identifica las causas específicas (programas con preguntas inactivas, modelos inactivos, datapoints huérfanos), y propón qué acciones concretas tomarías para resolver cada una. NO apliques cambios — solo diagnostica y reporta.",
  "mode": "auto"
}
```

**Criterio de éxito:**
- Completar en ≤ 30 iteraciones
- Llama al endpoint real
- Identifica las 3 categorías de inconsistencia
- Propone acciones concretas (no genéricas)
- Sin modificar archivos ni DB

---

## RESUMEN — Generar al final

Después de los 4 tests, genera una tabla así:

```
| Test | Resultado | Iteraciones | Tiempo | Errores | Notas |
|------|-----------|-------------|--------|---------|-------|
| T1 Quick (rename) | PASS/FAIL | X/8 | Xs | N | ... |
| T2 Análisis (listar métodos) | PASS/FAIL | X/12 | Xs | N | ... |
| T3 Execute (crear endpoint) | PASS/FAIL | X/20 | Xs | N | ... |
| T4 Deep (diagnóstico) | PASS/FAIL | X/30 | Xs | N | ... |
```

Y una conclusión:
- Si T1-T2 fallan → el cerebro no sirve ni para tareas básicas → cambiar modelo
- Si T1-T2 pasan pero T3-T4 fallan → capacidad parcial → evaluar cambio de cerebro
- Si T1-T4 pasan → los modelos son capaces, el problema era la infraestructura

Guardar el resumen en: `motor-semantico/results/test_modelos_post_b06.md`
