# Especificacion de Agente OMNI-MIND

## Que es un agente en este ecosistema

Un agente es un proceso autonomo que:
1. Lee su tarea de una fuente (DB tabla `tareas_agente` o archivo en `tasks/`)
2. Ejecuta usando codigo puro + LLM cuando necesita juicio
3. Reporta resultado (DB + marcas estigmergicas)
4. Se detiene o continua al siguiente ciclo

## Ciclo de vida

```
IDLE → LEER_TAREA → EJECUTAR → REPORTAR → IDLE
                       ↓
                    ESCALAR (si no sabe que hacer)
```

## Interfaz comun (todo agente implementa)

```python
class AgenteBase:
    nombre: str           # Identificador unico
    tipo: str             # fabrica | producto | meta
    sensor: Sensor        # De donde lee
    actuador: Actuador    # Donde escribe

    async def leer_tarea(self) -> Tarea | None
    async def ejecutar(self, tarea: Tarea) -> Resultado
    async def reportar(self, resultado: Resultado)
    async def escalar(self, problema: str)
```

## Fuentes de tareas

### Opcion A: Tabla `tareas_agente`
```sql
CREATE TABLE tareas_agente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agente TEXT NOT NULL,           -- nombre del agente destino
    tipo TEXT NOT NULL,             -- fix | analisis | comunicacion | mejora
    prioridad INT DEFAULT 5,       -- 1=critico, 10=nice-to-have
    payload JSONB NOT NULL,        -- datos especificos de la tarea
    estado TEXT DEFAULT 'pendiente', -- pendiente | en_progreso | completada | fallida
    resultado JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
```

### Opcion B: Archivos en `tasks/`
```
tasks/
  builder/
    001_fix_predicciones.yaml
    002_add_endpoint.yaml
  verificador/
    daily_run.yaml
  investigador/
    scan_competidores.yaml
```

### Opcion C: Marcas estigmergicas (reactivo)
Un agente deja una marca → otro la detecta y actua.
```sql
INSERT INTO marcas_estigmergicas (tipo, agente, contenido)
VALUES ('hallazgo', 'verificador', '{"endpoint": "/predicciones", "error": 500}');
-- El Builder detecta marcas tipo='hallazgo' y genera fixes
```

## Comunicacion: SOLO estigmergia

```
Verificador                          Builder
    |                                   |
    |-- marca: hallazgo ──────────────→ |
    |                                   |-- lee hallazgo
    |                                   |-- genera fix
    |                                   |-- aplica + deploy
    |                                   |-- marca: fix_aplicado ──→
    |                                   |
    |←── detecta fix_aplicado ──────────|
    |-- re-verifica endpoint            |
    |-- marca: verificado ──────────────→
```

## Agentes actuales

### Verificador (scripts/verificador.py)
- **Sensor**: Llama a todos los endpoints de produccion
- **Procesador**: Compara respuestas vs expectativas
- **Actuador**: Genera informe JSON con hallazgos
- **Trigger**: Manual o post-deploy

### Builder (scripts/builder.py)
- **Sensor**: Lee hallazgos del Verificador + logs de fly.io
- **Procesador**: Claude Sonnet genera fix minimo
- **Actuador**: Edita archivos + `fly deploy`
- **Safety**: git stash antes, rollback si falla
- **Trigger**: Manual o loop automatico

## Como anadir un agente nuevo

1. Crear `scripts/<nombre>.py`
2. Implementar: leer_tarea → ejecutar → reportar
3. Definir sensor (de donde lee) y actuador (donde escribe)
4. Registrar en `docs/VISION_NEGOCIO.md` tabla de agentes
5. Test: `python3 scripts/<nombre>.py --dry-run`
