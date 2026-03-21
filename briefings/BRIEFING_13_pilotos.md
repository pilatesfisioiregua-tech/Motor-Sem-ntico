# BRIEFING_13: Pilotos — Ejecutar Motor vN sobre pilates y fisioterapia

Fecha: 2026-03-18
Prioridad: 3 (depende de P1 ✅ y P2 ✅)
Objetivo: Generar los primeros datapoints REALES del pipeline completo sobre los 2 casos piloto.

---

## CONTEXTO

El Motor vN tiene 7 ejecuciones históricas (todas modo=analisis, coste medio $0.18, score medio 8.7). Pero:
- Solo se probó con inputs genéricos, no con los casos piloto reales
- 4 programas compilados nunca se actualizaron con ejecuciones reales
- 0 observaciones en reactor
- 0 perfiles de gradientes por consumidor
- El Gestor no puede mejorar la Matriz sin datos de ejecución frescos

Este briefing genera datos reales para alimentar los loops que acabamos de activar.

---

## PREREQUISITO: Endpoint de ejecución del Motor

### Investigar primero
`motor_vn.py` tiene `async def ejecutar(self, input_texto, modo, consumidor)` pero puede que NO exista un endpoint HTTP para llamarlo. Buscar en `api.py`:

```
grep -n "motor.*ejecutar\|MotorVN\|motor_vn\|/motor/" api.py | head -30
```

### Si NO existe endpoint `/motor/ejecutar`:
Crear en `api.py`, cerca de los otros endpoints del Motor (`/motor/registrar`, `/motor/señales`):

```python
@app.post("/motor/ejecutar")
async def motor_ejecutar(request: Request):
    """Ejecutar el pipeline completo del Motor vN sobre un caso."""
    try:
        body = await request.json()
        input_texto = body.get("input", body.get("texto", ""))
        modo = body.get("modo", "analisis")
        consumidor = body.get("consumidor", "motor_vn")

        if not input_texto:
            return {"status": "error", "error": "input requerido"}

        from core.motor_vn import MotorVN
        motor = MotorVN()
        resultado = await motor.ejecutar(input_texto, modo=modo, consumidor=consumidor)

        return {"status": "ok", "resultado": resultado}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
```

### Si YA existe, verificar que funciona:
```bash
curl -X POST https://chief-os-omni.fly.dev/motor/ejecutar \
  -H "Content-Type: application/json" \
  -d '{"input": "test rápido", "modo": "analisis"}'
```

---

## EJECUCIÓN 1: CASO PILATES

### Input para el Motor
Este texto debe pasarse al Motor como `input_texto`. Es el resumen del caso real:

```
Estudio de Pilates terapéutico en Madrid. Dueño trabaja 50h/semana, 87% dependencia. 
Quiere delegar 20h a instructor nuevo. Sistema de gestión obsoleto (Archivex), todo manual.
F3 Continuidad es el eslabón más débil (grado 4.0/10). Invariantes críticas ausentes: 
Caja Negra (3.5/10), Homeostasis (4.2/10), Retroalimentación (3.0/10), Externalidad (4.0/10).
Marketing casi inexistente. Retención alta (7/10) pero captación baja. 
Método EEDAP propio, equipamiento completo (Gratz), espacio de 130m².
Precio grupal: 105€/3 personas = 35€/persona (igual que individual, sin incentivo).
Facturación estable pero sin crecimiento. Necesita sistema que opere sin él al 60%.
```

### Comando de ejecución
```bash
curl -X POST https://chief-os-omni.fly.dev/motor/ejecutar \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Estudio de Pilates terapéutico en Madrid. Dueño trabaja 50h/semana, 87% dependencia. Quiere delegar 20h a instructor nuevo. Sistema de gestión obsoleto (Archivex), todo manual. F3 Continuidad es el eslabón más débil (grado 4.0/10). Invariantes críticas ausentes: Caja Negra (3.5/10), Homeostasis (4.2/10), Retroalimentación (3.0/10), Externalidad (4.0/10). Marketing casi inexistente. Retención alta (7/10) pero captación baja. Método EEDAP propio, equipamiento completo (Gratz), espacio de 130m². Precio grupal: 105€/3 personas = 35€/persona (igual que individual, sin incentivo). Facturación estable pero sin crecimiento. Necesita sistema que opere sin él al 60%.",
    "modo": "analisis",
    "consumidor": "exocortex:pilates"
  }'
```

### Qué debe pasar internamente:
1. **Fase A (determinista, $0):** calcular_gradientes → generar programa via Manifold (con vector routing) → freeze
2. **Fase B (con LLM):** ejecutar con enjambre → evaluar → integrar → registrar
3. **Post-ejecución:** actualizar programas_compilados, registrar datapoints, señales PID

### Verificación Ejecución 1
```sql
-- Nuevo campo de gradientes para este caso
SELECT ejecucion_id, top_gaps FROM campo_gradientes 
ORDER BY created_at DESC LIMIT 1;

-- Nuevos datapoints calibrados
SELECT count(*) FROM datapoints_efectividad 
WHERE consumidor = 'exocortex:pilates' AND calibrado = true;

-- Programa actualizado
SELECT consumidor, n_ejecuciones, tasa_cierre_media 
FROM programas_compilados WHERE consumidor LIKE '%pilates%';

-- Efectos en la Matriz
SELECT inteligencia, lente, funcion, hallazgo 
FROM efectos_matriz ORDER BY created_at DESC LIMIT 10;

-- Ejecución registrada
SELECT id, modo, coste_usd, tiempo_s, score_calidad 
FROM ejecuciones ORDER BY created_at DESC LIMIT 1;
```

---

## EJECUCIÓN 2: CASO FISIOTERAPIA

### Input para el Motor
```
Clínica de fisioterapia familiar en Madrid. Servicio premium, clientela fidelizada. 
Operada por un familiar de los fundadores de OMNI-MIND (caso piloto Wave 2).
Retos principales: gestión de citas manual, poca presencia digital, 
dependencia alta del fisioterapeuta principal. Sin sistema de seguimiento 
post-tratamiento. Captación por boca a boca exclusivamente (sin marketing activo).
Competencia creciente de franquicias low-cost. Diferenciador: atención personalizada 
y conocimiento profundo del paciente. Sin métricas de retención ni satisfacción formales.
Necesita digitalizar sin perder el toque personal que lo diferencia.
```

### Comando de ejecución
```bash
curl -X POST https://chief-os-omni.fly.dev/motor/ejecutar \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Clínica de fisioterapia familiar en Madrid. Servicio premium, clientela fidelizada. Operada por un familiar de los fundadores de OMNI-MIND (caso piloto Wave 2). Retos principales: gestión de citas manual, poca presencia digital, dependencia alta del fisioterapeuta principal. Sin sistema de seguimiento post-tratamiento. Captación por boca a boca exclusivamente (sin marketing activo). Competencia creciente de franquicias low-cost. Diferenciador: atención personalizada y conocimiento profundo del paciente. Sin métricas de retención ni satisfacción formales. Necesita digitalizar sin perder el toque personal que lo diferencia.",
    "modo": "analisis",
    "consumidor": "exocortex:fisioterapia"
  }'
```

### Verificación Ejecución 2
Mismas queries que Ejecución 1 pero con `consumidor = 'exocortex:fisioterapia'`.

---

## EJECUCIÓN 3: Ejecutar cada caso en los 4 modos

Después de las 2 ejecuciones en modo `analisis`, ejecutar cada caso en los otros modos para generar datos de comparación:

```bash
# Pilates — conversación
curl -X POST .../motor/ejecutar -d '{"input": "[MISMO INPUT PILATES]", "modo": "conversacion", "consumidor": "exocortex:pilates"}'

# Pilates — generación
curl -X POST .../motor/ejecutar -d '{"input": "[MISMO INPUT PILATES]", "modo": "generacion", "consumidor": "exocortex:pilates"}'

# Fisioterapia — conversación
curl -X POST .../motor/ejecutar -d '{"input": "[MISMO INPUT FISIO]", "modo": "conversacion", "consumidor": "exocortex:fisioterapia"}'

# Fisioterapia — generación
curl -X POST .../motor/ejecutar -d '{"input": "[MISMO INPUT FISIO]", "modo": "generacion", "consumidor": "exocortex:fisioterapia"}'
```

Esto genera 6 ejecuciones totales (2 analisis + 2 conversacion + 2 generacion).

---

## POST-EJECUCIÓN: Disparar ciclo del Gestor

Después de las 6 ejecuciones, forzar un ciclo del Gestor para que procese los nuevos datos:

```bash
curl -X POST https://chief-os-omni.fly.dev/gestor/loop
```

Y verificar autopoiesis:
```bash
curl https://chief-os-omni.fly.dev/gestor/autopoiesis
```

---

## POST-EJECUCIÓN: Actualizar perfil_gradientes

Los perfiles de gradientes por consumidor deberían poblarse automáticamente. Verificar:
```sql
SELECT consumidor, version FROM perfil_gradientes;
-- Debería tener al menos 2 entries (pilates + fisioterapia)
-- Si está vacío, el Motor no está llamando a la función de perfil.
-- Investigar y reportar.
```

---

## VERIFICACIÓN FINAL

```sql
-- 1. Ejecuciones nuevas
SELECT modo, consumidor, coste_usd, score_calidad 
FROM ejecuciones ORDER BY created_at DESC LIMIT 10;
-- Debe haber >= 6 nuevas (2 analisis + 2 conv + 2 gen)

-- 2. Datapoints por consumidor
SELECT consumidor, count(*), avg(tasa_cierre) 
FROM datapoints_efectividad 
WHERE calibrado = true 
GROUP BY consumidor ORDER BY count DESC;
-- Debe mostrar exocortex:pilates y exocortex:fisioterapia con datos

-- 3. Programas actualizados
SELECT consumidor, n_ejecuciones, tasa_cierre_media 
FROM programas_compilados WHERE activo = true ORDER BY consumidor;
-- Debe tener n_ejecuciones > 0 para pilotos

-- 4. Señales PID por celda
SELECT * FROM (
  SELECT DISTINCT ON (celda_objetivo) celda_objetivo, gap_pre, gap_post, tasa_cierre, timestamp
  FROM datapoints_efectividad
  WHERE consumidor IN ('exocortex:pilates', 'exocortex:fisioterapia')
  ORDER BY celda_objetivo, timestamp DESC
) sub ORDER BY gap_post DESC;

-- 5. Efectos en la Matriz
SELECT inteligencia, count(*) as n, avg(gap_cerrado) as avg_gap_cerrado
FROM efectos_matriz 
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY inteligencia ORDER BY avg_gap_cerrado DESC;

-- 6. Autopoiesis — check_datapoints debe tener datos
-- (ya verificado via curl arriba)
```

---

## ERRORES ESPERADOS Y MANEJO

### Error: Motor falla por timeout
El Motor usa LLMs externos. Timeouts son esperables.
- Si falla 1 ejecución: reintentar
- Si falla consistentemente: verificar que OPENROUTER_API_KEY funciona (`curl /models/health`)
- Timeout del endpoint: puede necesitar más de 60s. Si FastAPI corta antes, aumentar timeout o hacer el endpoint async con background task.

### Error: "No inteligencias en programa"
El Manifold no encontró inteligencias para los gaps. Verificar que `inteligencias` tiene 18 rows y que `preguntas_matriz` tiene preguntas activas:
```sql
SELECT count(*) FROM inteligencias;
SELECT count(*) FROM preguntas_matriz WHERE nivel = 'base';
```

### Error: programas_compilados no se actualiza
`_persistir_programa` puede devolver None si el consumidor key no matchea. Verificar:
```sql
SELECT consumidor FROM programas_compilados;
```
Si los keys son `motor_vn_analisis` pero el Motor envía `exocortex:pilates_analisis`, hay mismatch.

### Error: datapoints calibrado = false
El registrador puede no estar marcando los nuevos datapoints como calibrados. Verificar:
```sql
SELECT calibrado, count(*) FROM datapoints_efectividad 
WHERE timestamp > NOW() - INTERVAL '1 hour' GROUP BY calibrado;
```
Si todos son false, hay que añadir `calibrado = true` en la inserción del registrador.

---

## ORDEN DE EJECUCIÓN

```
PASO 1: Verificar/crear endpoint /motor/ejecutar
PASO 2: Deploy si hubo cambios
PASO 3: Ejecutar Ejecución 1 (pilates analisis)
PASO 4: Verificar Ejecución 1 (queries SQL)
PASO 5: Ejecutar Ejecución 2 (fisio analisis)
PASO 6: Ejecutar Ejecución 3 (4 ejecuciones adicionales en otros modos)
PASO 7: Disparar ciclo Gestor
PASO 8: Verificación final (todas las queries)
PASO 9: Reportar resultados: n_ejecuciones, n_datapoints, coste total, score medio
```

---

## CRITERIO DE ÉXITO

- [ ] Endpoint /motor/ejecutar existe y responde
- [ ] >= 6 ejecuciones nuevas registradas en tabla `ejecuciones`
- [ ] Datapoints calibrados para exocortex:pilates y exocortex:fisioterapia
- [ ] programas_compilados actualizados con n_ejecuciones > 0
- [ ] Efectos en la Matriz registrados para las ejecuciones
- [ ] Ciclo Gestor ejecutado post-pilotos sin errores
- [ ] Autopoiesis: check_datapoints no vacío

## COSTE ESTIMADO
- 6 ejecuciones × ~$0.18 = ~$1.08
- Total: ~$1-1.50
