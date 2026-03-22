# B-ORG-D1: Deploy + Smoke Test del Organismo Completo

**Fecha:** 23 marzo 2026
**Prioridad:** Crítica (sin deploy, todo gira solo en local)
**Dependencia:** B-ORG-R1 y B-ORG-C1 ejecutados
**Esfuerzo:** 1 briefing, ~30 min

---

## CONTEXTO

Hay 13 archivos nuevos del organismo (B-ORG-01 a B-ORG-08 + R1 + C1) que deben estar desplegados en fly.io. Algunos ya tienen commits, otros están pendientes.

Este briefing:
1. Verifica que TODO el código del organismo está en el repo y desplegado
2. Ejecuta migraciones pendientes (018, 019, 020)
3. Añade endpoints y routers faltantes al main.py
4. Smoke test de producción: verificar que cada goma gira

## PASO 1: Verificar archivos en el repo

```bash
# Todos estos archivos deben existir:
ls -la src/pilates/bus.py
ls -la src/pilates/observador.py
ls -la src/pilates/diagnosticador.py
ls -la src/pilates/buscador.py
ls -la src/pilates/vigia.py
ls -la src/pilates/mecanico.py
ls -la src/pilates/autofago.py
ls -la src/pilates/propiocepcion.py
ls -la src/pilates/af1_conservacion.py
ls -la src/pilates/af3_depuracion.py
ls -la src/pilates/voz_reactivo.py
ls -la src/pilates/af_restantes.py
ls -la src/pilates/ejecutor_convergencia.py
ls -la src/pilates/redsys_pagos.py       # B-ORG-R1
ls -la src/pilates/collectors.py          # B-ORG-C1
```

Si alguno falta → ejecutar el briefing correspondiente primero.

## PASO 2: Verificar imports en main.py

Abrir `src/main.py` y verificar que:

1. El router de Redsys está montado:
```python
from src.pilates.redsys_pagos import redsys_router  # o el equivalente
app.include_router(redsys_router)
```

Si los endpoints de Redsys no están en router.py ni en un router separado, CREARLOS según B-ORG-R1.

2. El cron arranca en el lifespan:
```python
from src.pilates.cron import cron_loop
# En el lifespan:
asyncio.create_task(cron_loop())
```

## PASO 3: Migraciones pendientes

Ejecutar en orden contra la DB de fly.io:

```bash
# Conectar a la DB de fly.io
fly postgres connect -a chief-os-omni-db

# Verificar qué migraciones ya están aplicadas:
\dt om_*

# Aplicar las pendientes:
# 018_bus_senales.sql (si no está)
# 019_telemetria_sistema.sql (si no está)
# 020_redsys.sql (nueva)
```

Si no es posible conectar directamente, crear un endpoint temporal `/admin/migrate` que ejecute las migraciones, o usar `fly ssh console`.

## PASO 4: Dependencias

```bash
# En requirements.txt, verificar que incluye:
pycryptodome    # Redsys (DES3)
PyJWT           # Google service account (collectors)
# Ya deberían estar: httpx, structlog, asyncpg, etc.

pip install pycryptodome PyJWT --break-system-packages
```

## PASO 5: Deploy

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
git add -A
git commit -m "Organismo completo: FASE 0+1 + Redsys + Collectors"
fly deploy
```

## PASO 6: Smoke test en producción

Ejecutar CADA endpoint para verificar que funciona:

### G1 — Datos→Señales (Observador)
```bash
# Crear un cliente de test (si no hay datos)
curl -X POST https://motor-semantico-omni.fly.dev/pilates/clientes \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Test","apellidos":"Organismo","telefono":"600000000"}'
# → Debe devolver 200 + ID
# → El Observador debe emitir señal DATO al bus automáticamente
```

### G2 — Señales→Diagnóstico
```bash
curl -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/diagnostico
# → Debe devolver estado ACD (E1-E4 o desequilibrado) + lentes S/Se/C
```

### G3 — Diagnóstico→Búsqueda
```bash
curl -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/buscador
# → Sin PERPLEXITY_API_KEY: debe devolver error gracioso, no crash
# → Con key: debe devolver gaps + queries + resultados
```

### G5 — Prescripción→Acción (AF)
```bash
# AF1
curl -X POST https://motor-semantico-omni.fly.dev/pilates/af/conservacion
# → fantasmas, engagement

# AF3
curl -X POST https://motor-semantico-omni.fly.dev/pilates/af/depuracion
# → grupos infrautilizados, zombis, VETOs

# AF restantes
curl -X POST https://motor-semantico-omni.fly.dev/pilates/af/todos
# → AF2+AF4+AF6+AF7
```

### G6 — Acción→Aprendizaje
```bash
# Propiocepción
curl -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/propiocepcion
# → snapshot con señales, agentes, ACD

# Collectors
curl -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/collectors
# → Sin credenciales Meta/GBP: skip gracioso. WA: métricas de DB.
```

### META — Rotura→Reparación
```bash
# Vigía
curl -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/vigia
# → health checks, alertas

# Mecánico
curl -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/mecanico
# → fixes aplicados (o 0 si todo OK)
```

### Ejecutor + Convergencia + Gestor
```bash
curl -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/circuito
# → ejecutor + convergencia + gestor en secuencia
```

### Voz
```bash
# Estrategia activa
curl https://motor-semantico-omni.fly.dev/pilates/voz/estrategia
# → foco + narrativa + calendario (o error si no hay estrategia)

# Ciclo completo
curl -X POST https://motor-semantico-omni.fly.dev/pilates/voz/ciclo
# → escuchar + priorizar + IRC + ISP
```

### Redsys (sin credenciales = error gracioso)
```bash
curl https://motor-semantico-omni.fly.dev/pilates/redsys/retorno-ok
# → HTML "Pago realizado correctamente"

curl https://motor-semantico-omni.fly.dev/pilates/redsys/retorno-ko
# → HTML "El pago no se ha completado"
```

### Cockpit
```bash
curl -X POST https://motor-semantico-omni.fly.dev/pilates/cockpit/contexto
# → saludo + datos del día + módulos sugeridos
```

## TESTS: Criterio PASS

| Test | PASS si |
|---|---|
| T1: Deploy | `fly deploy` sin errores |
| T2: Migraciones | Tablas om_bus_senales, om_telemetria_sistema, om_redsys_pedidos existen |
| T3: Diagnóstico ACD | Devuelve estado + lentes (no crash) |
| T4: AF1+AF3 | Devuelven datos operativos (fantasmas, grupos, VETOs) |
| T5: Vigía | Devuelve health checks (no crash) |
| T6: Circuito completo | Ejecutor + Convergencia + Gestor en secuencia |
| T7: Collectors | Skip gracioso sin credenciales (no crash) |
| T8: Redsys endpoints | Retorno OK/KO devuelven HTML |
| T9: Cockpit contexto | Devuelve saludo + datos + módulos |
| T10: Cron arranca | Logs confirman "cron_iniciado" |

**10/10 = PASS. Organismo en producción.**

---

## NOTA POST-DEPLOY

Una vez el smoke test pase, el organismo está girando autónomamente:
- **Cada 15 min:** Vigía + Mecánico
- **Diario 06:00:** Escuchar señales + collectors + propiocepción
- **Lunes 07:00:** Ciclo completo (ACD + búsqueda + AF1-AF7 + estrategia + convergencia + gestor)
- **Día 1 mes 08:00:** Autofagia

Lo único que falta para producción real: **cargar los 90 clientes** (B-ORG-C2, cuando Jesús pase el Excel) y **añadir credenciales** (Meta, GBP, Perplexity, Redsys cuando lleguen).
