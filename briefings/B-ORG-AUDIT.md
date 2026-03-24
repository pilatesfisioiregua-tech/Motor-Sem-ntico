# B-ORG-AUDIT — Auditoría Exhaustiva Post-Roadmap v4

**Para:** Claude Code (pestaña Código en Desktop)
**Cuándo:** Después de ejecutar F0→F7 del Roadmap v4
**Estimación:** ~2-3h de análisis

---

## INSTRUCCIONES PARA CLAUDE CODE

Haz una auditoría exhaustiva de todo el codebase del motor semántico. El repositorio acaba de pasar por una reestructuración masiva (Roadmap v4: auth, pizarras, motor unificado, agentes diana, presencia digital). Necesito que lo examines TODO y me des un informe honesto.

**Ruta base:** `/Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/`

---

## FASE 1: INVENTARIO (~30 min)

1. **Cuenta líneas de código por directorio:**
```bash
find src/ -name "*.py" | xargs wc -l | sort -n
find frontend/src/ -name "*.jsx" -o -name "*.js" -o -name "*.css" | xargs wc -l | sort -n
```

2. **Lista todas las migraciones SQL en orden:**
```bash
ls -la migrations/*.sql
```

3. **Lista todos los endpoints:**
```bash
grep -rn "@router\.\|@app\." src/ --include="*.py" | grep "def "
```

4. **Lista todas las tablas om_*:**
Conecta a la DB y ejecuta:
```sql
SELECT tablename FROM pg_tables WHERE tablename LIKE 'om_%' ORDER BY tablename;
```

5. **Lista todos los imports entre módulos:**
```bash
grep -rn "from src\." src/ --include="*.py" | sort
```

Guarda el inventario completo en `docs/operativo/INVENTARIO_CODEBASE.md`.

---

## FASE 2: ANÁLISIS DE SALUD (~45 min)

### 2.1 Código muerto
- Busca funciones/clases que NUNCA se importan ni se llaman desde otro archivo.
- Busca archivos .py que no se importan desde ningún sitio.
- Busca imports que no se usan dentro de cada archivo.
```bash
# Funciones definidas vs referenciadas
grep -rn "^def \|^async def " src/ --include="*.py"
# Para cada función, verificar si se referencia en otro archivo
```

### 2.2 Código duplicado
- Busca patrones repetidos: misma lógica de conexión a DB, misma extracción JSON, mismo patrón de llamada LLM.
- ¿Hay archivos que hacen lo mismo con nombres diferentes?
```bash
# Buscar patrones comunes duplicados
grep -rn "async with pool.acquire" src/ --include="*.py" | wc -l
grep -rn "httpx.AsyncClient" src/ --include="*.py"
grep -rn "OPENROUTER_API_KEY" src/ --include="*.py"
grep -rn 'TENANT = "authentic_pilates"' src/ --include="*.py" | wc -l
```

### 2.3 TENANT hardcoded
- Cuenta cuántos archivos todavía tienen `TENANT = "authentic_pilates"` hardcoded.
- Lista cada archivo y la línea.
```bash
grep -rn 'TENANT = "authentic_pilates"' src/ --include="*.py"
```

### 2.4 Dependencias no usadas
- Lee `requirements.txt` y verifica qué paquetes se importan realmente.
```bash
for pkg in $(cat requirements.txt | cut -d= -f1 | cut -d'[' -f1); do
  count=$(grep -rn "import $pkg\|from $pkg" src/ --include="*.py" | wc -l)
  echo "$pkg: $count usos"
done
```

### 2.5 Errores silenciados
- Busca `except Exception: pass` o `except: pass` — errores que se tragan sin log.
```bash
grep -rn "except.*pass" src/ --include="*.py"
grep -rn "except Exception:" src/ --include="*.py" -A1 | grep "pass"
```

### 2.6 Secrets en código
- Busca tokens, keys, passwords hardcoded.
```bash
grep -rni "api_key\|token\|password\|secret" src/ --include="*.py" | grep -v "os.getenv\|environ\|\.env"
```

---

## FASE 3: ANÁLISIS DE ARQUITECTURA (~45 min)

### 3.1 Grafo de dependencias
Para cada módulo principal (pilates/, pipeline/, motor/, tcf/, reactor/, gestor/):
- ¿Qué importa de otros módulos?
- ¿Quién lo importa?
- ¿Hay dependencias circulares?

```bash
# Dependencias entre módulos
for dir in pilates pipeline motor tcf reactor gestor utils config db; do
  echo "=== src/$dir/ imports ==="
  grep -rn "from src\." src/$dir/ --include="*.py" | grep -v "from src\.$dir" | sort -u
done
```

### 3.2 Puntos de entrada
Lista todos los puntos de entrada al sistema:
- Endpoints HTTP (router.py, redsys_router.py, portal.py, main.py)
- Cron tasks (cron.py: _tarea_diaria, _tarea_semanal, _tarea_mensual, cron_loop)
- Webhooks (WA, Redsys)
- LISTEN/NOTIFY listeners

### 3.3 Flujo de datos
Traza el flujo completo de estos escenarios:
1. **Cliente paga con tarjeta** → Redsys notificación → procesar_notificacion → conciliar → bus → feed
2. **Lunes 07:00 ciclo semanal** → escuchar → diagnosticar → enjambre → compositor → estratega → AF1-7 → mediador → ejecutor → traductor → WA
3. **WA entrante de lead nuevo** → webhook → clasificar → bus → reactivo → respuesta automática

¿Hay puntos donde el flujo se rompe o hay pasos desconectados?

### 3.4 Consistencia motor.pensar() vs llamadas directas
- ¿Todos los componentes usan motor.pensar() o quedan llamadas directas a httpx/openrouter?
```bash
grep -rn "httpx.AsyncClient\|openrouter_complete\|llm.complete" src/pilates/ --include="*.py"
```

### 3.5 Pizarras: escritores vs lectores
Para cada una de las 11 pizarras, verifica:
- ¿Quién ESCRIBE en ella? (INSERT/UPDATE)
- ¿Quién LEE? (SELECT)
- ¿Hay pizarras que nadie lee? ¿Pizarras que nadie escribe?

---

## FASE 4: CUELLOS DE BOTELLA Y RENDIMIENTO (~30 min)

### 4.1 Pool de conexiones DB
- ¿Cuántos archivos hacen `get_pool()` independientemente?
- ¿Se comparten conexiones o cada función abre la suya?
- ¿Hay leaks (acquire sin release)?

### 4.2 Llamadas LLM costosas
- Lista TODAS las llamadas a motor.pensar() o equivalentes con su complejidad (baja/media/alta).
- ¿Cuál es el coste estimado por ciclo semanal?
- ¿Hay llamadas LLM que podrían ser código puro ($0)?

### 4.3 Queries SQL lentas
- Busca queries sin índice (JOINs sin WHERE indexado).
- Busca queries con `SELECT *` que podrían ser más selectivas.
- Busca N+1 queries (loop de Python con query dentro).
```bash
grep -rn "SELECT \*" src/ --include="*.py"
grep -rn "await conn.fetch" src/ --include="*.py" -B5 | grep "for.*in"
```

### 4.4 Tamaño de cron
- ¿Cuánto tarda el ciclo semanal completo?
- ¿Hay componentes del cron que podrían ejecutarse en paralelo?
- ¿El cron tiene timeout protection?

---

## FASE 5: SEGURIDAD (~20 min)

### 5.1 Auth gaps
- ¿Todos los endpoints sensibles requieren auth?
- ¿PUBLIC_PREFIXES es correcto? ¿Hay endpoints que deberían ser públicos pero no lo son, o viceversa?
- ¿El webhook de WA verifica la firma de Meta?

### 5.2 SQL injection
- ¿Se usan parámetros ($1, $2) en TODAS las queries o hay string formatting?
```bash
grep -rn "f\".*SELECT\|f\".*INSERT\|f\".*UPDATE\|f\".*DELETE" src/ --include="*.py"
```

### 5.3 RGPD
- ¿Los datos clínicos (om_datos_clinicos) están protegidos?
- ¿El endpoint mis-datos devuelve TODO lo que debería?
- ¿solicitar-baja realmente marca para eliminación?

---

## FASE 6: TESTS (~15 min)

### 6.1 Cobertura actual
```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```
- ¿Cuántos tests hay?
- ¿Cuántos pasan?
- ¿Qué módulos NO tienen tests?

### 6.2 Tests que faltan
Lista los 10 tests más críticos que deberían existir y no existen.

---

## FASE 7: FRONTEND (~15 min)

### 7.1 Build check
```bash
cd frontend && npm run build 2>&1
```

### 7.2 Componentes huérfanos
- ¿Hay componentes .jsx que no se importan desde ningún sitio?

### 7.3 API calls sin error handling
- ¿Hay fetch calls sin .catch()?
```bash
grep -rn "\.then(" frontend/src/ --include="*.jsx" | grep -v "catch"
```

---

## OUTPUT ESPERADO

Genera un documento `docs/operativo/AUDITORIA_POST_ROADMAP_V4.md` con:

1. **Resumen ejecutivo** (1 párrafo): Estado general del codebase.

2. **Inventario** (tabla):
   - Líneas de código por módulo
   - Nº endpoints
   - Nº tablas
   - Nº tests

3. **Críticos** (bloquean producción):
   - Problemas de seguridad
   - Errores que crashean
   - Datos que se pierden

4. **Cuellos de botella** (degradan rendimiento):
   - Queries lentas
   - LLM calls innecesarias
   - Pool leaks

5. **Deuda técnica** (no urgente pero acumulable):
   - TENANT hardcoded (cuántos archivos)
   - Código muerto (cuántas funciones/archivos)
   - Duplicación
   - Imports no usados

6. **Oportunidades** (mejoras de alto impacto bajo esfuerzo):
   - Qué se puede eliminar
   - Qué se puede simplificar
   - Qué se puede cachear

7. **Score de salud** (0-10):
   - Seguridad: X/10
   - Rendimiento: X/10
   - Mantenibilidad: X/10
   - Cobertura tests: X/10
   - Arquitectura: X/10

8. **Top 10 acciones** priorizadas por impacto/esfuerzo.

---

## REGLAS

- Sé BRUTALMENTE honesto. No suavices los problemas.
- Cada hallazgo debe tener: archivo, línea, problema, impacto, fix sugerido.
- Si encuentras algo que podría causar pérdida de datos o dinero, márcalo como CRÍTICO.
- Si encuentras código que nunca se ejecuta, márcalo para eliminación.
- Guarda el informe en `docs/operativo/AUDITORIA_POST_ROADMAP_V4.md`.
- NO arregles nada. Solo diagnostica. Los fixes se harán en briefings separados.
