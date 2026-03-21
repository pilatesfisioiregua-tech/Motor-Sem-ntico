# B-PIL-14: ADN + Procesos + Conocimiento + Tensiones + Depuración — Capa de Inteligencia Operativa

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-12 (dashboard ACD), B-PIL-01 (tablas om_adn, om_procesos, om_conocimiento, om_tensiones, om_depuracion ya existen)
**Coste:** $0

---

## CONTEXTO

El ACD diagnostica que Authentic Pilates está en estado "genio_mortal" (S+ Se+ C-) y prescribe: TRANSFERIR — documentar método, codificar ADN, evaluar qué delegar. Pero las tablas que soportan esto (om_adn, om_procesos, om_conocimiento, om_tensiones, om_depuracion) existen en la DB sin endpoints ni UI.

Este briefing las conecta al sistema: CRUD + UI en Modo Profundo + cálculo de readiness de replicación.

**Fuente:** Exocortex v2.1 S3 (T18-T22, T29), S10, S17.3

**Lo que habilita:**
- **F5 Identidad:** om_adn — principios innegociables, filosofía, antipatrones
- **F7 Replicación:** om_procesos — pasos documentados de cada proceso del estudio
- **F2 Captación (Sentido):** om_conocimiento — aprendizajes emergentes que suben a ADN
- **F6 Adaptación:** om_tensiones — eventos externos que requieren ajuste
- **F3 Depuración:** om_depuracion — lo que dejar de hacer (diferenciador OMNI-MIND)

---

## FASE A: Backend — CRUD completo en router.py

**Archivo:** `@project/src/pilates/router.py` — LEER PRIMERO. AÑADIR schemas + endpoints.

### Schemas

```python
# ============================================================
# SCHEMAS — ADN + PROCESOS + CONOCIMIENTO + TENSIONES + DEPURACIÓN
# ============================================================

class ADNCreate(BaseModel):
    categoria: str = Field(pattern="^(principio_innegociable|principio_flexible|metodo|filosofia|antipatron|criterio_depuracion)$")
    titulo: str
    descripcion: str
    ejemplos: Optional[list[str]] = None
    contra_ejemplos: Optional[list[str]] = None
    funcion_l07: Optional[str] = None
    lente: Optional[str] = None

class ADNUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    ejemplos: Optional[list[str]] = None
    contra_ejemplos: Optional[list[str]] = None
    activo: Optional[bool] = None

class ProcesoCreate(BaseModel):
    area: str = Field(pattern="^(operativa_diaria|sesion|cliente|emergencia|administrativa|instructor)$")
    titulo: str
    descripcion: str
    pasos: list[dict]  # [{"orden": 1, "accion": "...", "detalle": "..."}]
    notas: Optional[str] = None
    funcion_l07: Optional[str] = None
    vinculado_a_adn: Optional[UUID] = None

class ConocimientoCreate(BaseModel):
    tipo: str = Field(pattern="^(tecnica|cliente|negocio|mercado|metodo)$")
    titulo: str
    descripcion: str
    evidencia: Optional[list[str]] = None
    confianza: str = Field(default="hipotesis", pattern="^(hipotesis|validado|consolidado)$")
    origen: Optional[str] = None

class TensionCreate(BaseModel):
    tipo: str = Field(pattern="^(competencia_nueva|perdida_recurso|crisis_demanda|crecimiento|regulatorio|personal|estacional|mercado)$")
    descripcion: str
    funciones_afectadas: list[str]
    severidad: str = Field(pattern="^(baja|media|alta|critica)$")
    duracion_estimada_dias: Optional[int] = None

class DepuracionCreate(BaseModel):
    tipo: str = Field(pattern="^(servicio_eliminar|cliente_toxico|gasto_innecesario|proceso_redundante|canal_inefectivo|habito_operativo|creencia_limitante)$")
    descripcion: str
    impacto_estimado: Optional[str] = None
    funcion_l07: Optional[str] = None
    lente: Optional[str] = None
    origen: str = Field(default="manual", pattern="^(diagnostico_acd|sesion_consejo|manual|automatizacion)$")
    diagnostico_id: Optional[UUID] = None
```

### Endpoints ADN (5)

```python
# ============================================================
# ADN DEL NEGOCIO (F5 Identidad)
# ============================================================

@router.get("/adn")
async def listar_adn(categoria: Optional[str] = None, activo: bool = True):
    """Lista principios ADN. Filtro por categoría y estado activo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if activo:
            conditions.append("activo = true")
        if categoria:
            conditions.append(f"categoria = ${idx}"); params.append(categoria); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_adn WHERE {where} ORDER BY categoria, titulo
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.get("/adn/{adn_id}")
async def obtener_adn(adn_id: UUID):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_adn WHERE id = $1 AND tenant_id = $2", adn_id, TENANT)
        if not row:
            raise HTTPException(404, "Principio ADN no encontrado")
    return _row_to_dict(row)


@router.post("/adn", status_code=201)
async def crear_adn(data: ADNCreate):
    """Crea un principio ADN del negocio."""
    import json
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_adn (tenant_id, categoria, titulo, descripcion,
                ejemplos, contra_ejemplos, funcion_l07, lente)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7,$8) RETURNING id
        """, TENANT, data.categoria, data.titulo, data.descripcion,
            json.dumps(data.ejemplos) if data.ejemplos else None,
            json.dumps(data.contra_ejemplos) if data.contra_ejemplos else None,
            data.funcion_l07, data.lente)
    log.info("adn_creado", titulo=data.titulo, categoria=data.categoria)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/adn/{adn_id}")
async def actualizar_adn(adn_id: UUID, data: ADNUpdate):
    import json
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "Nada que actualizar")
    pool = await _get_pool()
    # Serializar listas a JSON
    for k in ("ejemplos", "contra_ejemplos"):
        if k in updates and isinstance(updates[k], list):
            updates[k] = json.dumps(updates[k])
    set_clauses = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
    values = [adn_id] + list(updates.values())
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE om_adn SET {set_clauses}, version = version + 1, fecha_modificacion = CURRENT_DATE WHERE id = $1 AND tenant_id = '{TENANT}'",
            *values)
    return {"status": "updated"}


@router.delete("/adn/{adn_id}")
async def desactivar_adn(adn_id: UUID):
    """No borra — marca como inactivo (historial)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE om_adn SET activo = false WHERE id = $1 AND tenant_id = $2",
            adn_id, TENANT)
    return {"status": "desactivado"}
```

### Endpoints Procesos (4)

```python
# ============================================================
# PROCESOS DOCUMENTADOS (F7 Replicación)
# ============================================================

@router.get("/procesos")
async def listar_procesos(area: Optional[str] = None):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if area:
            rows = await conn.fetch("""
                SELECT * FROM om_procesos WHERE tenant_id = $1 AND area = $2 ORDER BY area, titulo
            """, TENANT, area)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_procesos WHERE tenant_id = $1 ORDER BY area, titulo
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/procesos/{proceso_id}")
async def obtener_proceso(proceso_id: UUID):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_procesos WHERE id = $1 AND tenant_id = $2", proceso_id, TENANT)
        if not row:
            raise HTTPException(404, "Proceso no encontrado")
        # Incrementar consultas
        await conn.execute("""
            UPDATE om_procesos SET veces_consultado = veces_consultado + 1, ultima_consulta = now()
            WHERE id = $1
        """, proceso_id)
    return _row_to_dict(row)


@router.post("/procesos", status_code=201)
async def crear_proceso(data: ProcesoCreate):
    import json
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_procesos (tenant_id, area, titulo, descripcion, pasos,
                notas, funcion_l07, vinculado_a_adn, documentado_por)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,'Jesus') RETURNING id
        """, TENANT, data.area, data.titulo, data.descripcion,
            json.dumps(data.pasos), data.notas, data.funcion_l07, data.vinculado_a_adn)
    log.info("proceso_creado", titulo=data.titulo, area=data.area)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/procesos/{proceso_id}")
async def actualizar_proceso(proceso_id: UUID, data: dict):
    """Actualiza proceso. Incrementa versión."""
    import json
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Leer actual
        actual = await conn.fetchrow(
            "SELECT * FROM om_procesos WHERE id = $1 AND tenant_id = $2", proceso_id, TENANT)
        if not actual:
            raise HTTPException(404, "Proceso no encontrado")
        # Actualizar campos enviados
        titulo = data.get("titulo", actual["titulo"])
        descripcion = data.get("descripcion", actual["descripcion"])
        pasos = json.dumps(data["pasos"]) if "pasos" in data else actual["pasos"]
        notas = data.get("notas", actual["notas"])
        await conn.execute("""
            UPDATE om_procesos SET titulo=$1, descripcion=$2, pasos=$3::jsonb, notas=$4,
                version = version + 1, ultima_revision = CURRENT_DATE
            WHERE id = $5
        """, titulo, descripcion, pasos if isinstance(pasos, str) else json.dumps(pasos),
            notas, proceso_id)
    return {"status": "updated"}
```

### Endpoints Conocimiento (3)

```python
# ============================================================
# CONOCIMIENTO EMERGENTE (F2 Sentido)
# ============================================================

@router.get("/conocimiento")
async def listar_conocimiento(tipo: Optional[str] = None, confianza: Optional[str] = None):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if tipo:
            conditions.append(f"tipo = ${idx}"); params.append(tipo); idx += 1
        if confianza:
            conditions.append(f"confianza = ${idx}"); params.append(confianza); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_conocimiento WHERE {where} ORDER BY fecha_descubrimiento DESC
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.post("/conocimiento", status_code=201)
async def crear_conocimiento(data: ConocimientoCreate):
    import json
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_conocimiento (tenant_id, tipo, titulo, descripcion,
                evidencia, confianza, origen)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7) RETURNING id
        """, TENANT, data.tipo, data.titulo, data.descripcion,
            json.dumps(data.evidencia) if data.evidencia else None,
            data.confianza, data.origen)
    log.info("conocimiento_creado", titulo=data.titulo, tipo=data.tipo)
    return {"id": str(row["id"]), "status": "created"}


@router.post("/conocimiento/{conocimiento_id}/promover-adn")
async def promover_a_adn(conocimiento_id: UUID, data: ADNCreate):
    """Promueve conocimiento consolidado a principio ADN.
    
    F2→F5: lo que se aprende (conocimiento) sube a lo que se es (ADN).
    """
    pool = await _get_pool()
    import json
    async with pool.acquire() as conn:
        # Verificar conocimiento
        conoc = await conn.fetchrow(
            "SELECT * FROM om_conocimiento WHERE id = $1 AND tenant_id = $2",
            conocimiento_id, TENANT)
        if not conoc:
            raise HTTPException(404, "Conocimiento no encontrado")

        # Crear ADN
        adn_row = await conn.fetchrow("""
            INSERT INTO om_adn (tenant_id, categoria, titulo, descripcion,
                ejemplos, contra_ejemplos, funcion_l07, lente)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7,$8) RETURNING id
        """, TENANT, data.categoria, data.titulo, data.descripcion,
            json.dumps(data.ejemplos) if data.ejemplos else None,
            json.dumps(data.contra_ejemplos) if data.contra_ejemplos else None,
            data.funcion_l07, data.lente)

        # Marcar conocimiento como promovido
        await conn.execute("""
            UPDATE om_conocimiento SET promovido_a_adn = $1, confianza = 'consolidado'
            WHERE id = $2
        """, adn_row["id"], conocimiento_id)

    log.info("conocimiento_promovido", conocimiento=str(conocimiento_id), adn=str(adn_row["id"]))
    return {"status": "promovido", "adn_id": str(adn_row["id"])}
```

### Endpoints Tensiones (3)

```python
# ============================================================
# TENSIONES (F6 Adaptación)
# ============================================================

@router.get("/tensiones")
async def listar_tensiones(estado: Optional[str] = "activa"):
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT * FROM om_tensiones WHERE tenant_id = $1 AND estado = $2
                ORDER BY severidad DESC, fecha_inicio DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_tensiones WHERE tenant_id = $1 ORDER BY fecha_inicio DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.post("/tensiones", status_code=201)
async def crear_tension(data: TensionCreate):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_tensiones (tenant_id, tipo, descripcion, funciones_afectadas,
                severidad, duracion_estimada_dias, detectada_por)
            VALUES ($1,$2,$3,$4,$5,$6,'manual') RETURNING id
        """, TENANT, data.tipo, data.descripcion, data.funciones_afectadas,
            data.severidad, data.duracion_estimada_dias)
    log.info("tension_creada", tipo=data.tipo, severidad=data.severidad)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/tensiones/{tension_id}")
async def actualizar_tension(tension_id: UUID, data: dict):
    """Actualiza tensión: resolver, marcar crónica, etc."""
    pool = await _get_pool()
    estado = data.get("estado")
    async with pool.acquire() as conn:
        if estado:
            updates = {"estado": estado}
            if estado == "resuelta":
                updates["fecha_fin"] = "CURRENT_DATE"
                await conn.execute("""
                    UPDATE om_tensiones SET estado = $1, fecha_fin = CURRENT_DATE
                    WHERE id = $2 AND tenant_id = $3
                """, estado, tension_id, TENANT)
            else:
                await conn.execute("""
                    UPDATE om_tensiones SET estado = $1 WHERE id = $2 AND tenant_id = $3
                """, estado, tension_id, TENANT)
    return {"status": "updated"}
```

### Endpoints Depuración (4)

```python
# ============================================================
# DEPURACIÓN (F3 — "deja de hacer esto")
# ============================================================

@router.get("/depuracion")
async def listar_depuracion(estado: Optional[str] = None):
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT d.*, dt.estado as diagnostico_estado
                FROM om_depuracion d
                LEFT JOIN om_diagnosticos_tenant dt ON dt.id = d.diagnostico_id
                WHERE d.tenant_id = $1 AND d.estado = $2
                ORDER BY d.created_at DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT d.*, dt.estado as diagnostico_estado
                FROM om_depuracion d
                LEFT JOIN om_diagnosticos_tenant dt ON dt.id = d.diagnostico_id
                WHERE d.tenant_id = $1
                ORDER BY d.created_at DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.post("/depuracion", status_code=201)
async def crear_depuracion(data: DepuracionCreate):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_depuracion (tenant_id, tipo, descripcion, impacto_estimado,
                funcion_l07, lente, origen, diagnostico_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id
        """, TENANT, data.tipo, data.descripcion, data.impacto_estimado,
            data.funcion_l07, data.lente, data.origen, data.diagnostico_id)
    log.info("depuracion_creada", tipo=data.tipo, descripcion=data.descripcion[:50])
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/depuracion/{depuracion_id}")
async def actualizar_depuracion(depuracion_id: UUID, data: dict):
    """Cambiar estado: propuesta → aprobada → ejecutada / descartada."""
    pool = await _get_pool()
    estado = data.get("estado")
    resultado = data.get("resultado")
    async with pool.acquire() as conn:
        updates = []
        params = [depuracion_id]
        idx = 2
        if estado:
            updates.append(f"estado = ${idx}"); params.append(estado); idx += 1
            if estado == "aprobada":
                updates.append("fecha_decision = CURRENT_DATE")
            elif estado == "ejecutada":
                updates.append("fecha_ejecucion = CURRENT_DATE")
        if resultado:
            updates.append(f"resultado = ${idx}"); params.append(resultado); idx += 1
        if not updates:
            raise HTTPException(400, "Nada que actualizar")
        set_clause = ", ".join(updates)
        await conn.execute(
            f"UPDATE om_depuracion SET {set_clause} WHERE id = $1 AND tenant_id = '{TENANT}'",
            *params)
    return {"status": "updated"}


@router.get("/readiness")
async def readiness_replicacion():
    """Calcula readiness de replicación del negocio.
    
    Formula: % procesos documentados × % ADN codificado × grado_absorcion × % conocimiento consolidado
    
    Exocortex v2.1 S10.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Procesos documentados vs áreas esperadas
        procesos = await conn.fetchval(
            "SELECT count(*) FROM om_procesos WHERE tenant_id = $1", TENANT)
        areas_total = 6  # operativa_diaria, sesion, cliente, emergencia, administrativa, instructor
        areas_cubiertas = await conn.fetchval("""
            SELECT count(DISTINCT area) FROM om_procesos WHERE tenant_id = $1
        """, TENANT)
        pct_procesos = round(min(areas_cubiertas / areas_total, 1) * 100, 0)

        # ADN codificado
        adn_total = await conn.fetchval(
            "SELECT count(*) FROM om_adn WHERE tenant_id = $1 AND activo = true", TENANT)
        # Mínimo esperado: al menos 1 por categoría clave (innegociable, método, filosofía)
        cats_cubiertas = await conn.fetchval("""
            SELECT count(DISTINCT categoria) FROM om_adn WHERE tenant_id = $1 AND activo = true
        """, TENANT)
        cats_total = 6
        pct_adn = round(min(cats_cubiertas / cats_total, 1) * 100, 0)

        # Grado absorción instructor
        onboarding = await conn.fetchrow("""
            SELECT grado_absorcion FROM om_onboarding_instructor
            WHERE tenant_id = $1 ORDER BY created_at DESC LIMIT 1
        """, TENANT)
        grado_absorcion = float(onboarding["grado_absorcion"]) / 10 if onboarding and onboarding["grado_absorcion"] else 0

        # Conocimiento consolidado
        total_conoc = await conn.fetchval(
            "SELECT count(*) FROM om_conocimiento WHERE tenant_id = $1", TENANT)
        consolidado = await conn.fetchval(
            "SELECT count(*) FROM om_conocimiento WHERE tenant_id = $1 AND confianza = 'consolidado'", TENANT)
        pct_conocimiento = round(consolidado / max(total_conoc, 1) * 100, 0)

        # Depuración activa
        depuraciones_ejecutadas = await conn.fetchval(
            "SELECT count(*) FROM om_depuracion WHERE tenant_id = $1 AND estado = 'ejecutada'", TENANT)
        depuraciones_propuestas = await conn.fetchval(
            "SELECT count(*) FROM om_depuracion WHERE tenant_id = $1", TENANT)

    # Readiness compuesto
    readiness = round(
        (pct_procesos / 100) * (pct_adn / 100) * max(grado_absorcion, 0.1) * max(pct_conocimiento / 100, 0.1) * 100, 1
    )

    return {
        "readiness_pct": readiness,
        "componentes": {
            "procesos": {"pct": pct_procesos, "total": procesos, "areas_cubiertas": areas_cubiertas, "areas_total": areas_total},
            "adn": {"pct": pct_adn, "total": adn_total, "categorias_cubiertas": cats_cubiertas, "categorias_total": cats_total},
            "absorcion_instructor": {"valor": round(grado_absorcion * 100, 0), "tiene_onboarding": onboarding is not None},
            "conocimiento": {"pct": pct_conocimiento, "total": total_conoc, "consolidado": consolidado},
            "depuracion": {"ejecutadas": depuraciones_ejecutadas, "propuestas": depuraciones_propuestas},
        },
        "prescripcion_c": "Documentar procesos y codificar ADN para subir Continuidad (C)" if readiness < 50
            else "Readiness aceptable — foco en absorción instructor" if readiness < 80
            else "Readiness alto — listo para replicar",
    }
```

---

## FASE B: Frontend — Pestañas ADN y Procesos en Modo Profundo

### B1. Actualizar api.js

```javascript
// ADN
export const getADN = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/adn${qs ? `?${qs}` : ''}`);
};
export const crearADN = (data) => request('/adn', { method: 'POST', body: JSON.stringify(data) });
export const actualizarADN = (id, data) => request(`/adn/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

// Procesos
export const getProcesos = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/procesos${qs ? `?${qs}` : ''}`);
};
export const crearProceso = (data) => request('/procesos', { method: 'POST', body: JSON.stringify(data) });

// Conocimiento
export const getConocimiento = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/conocimiento${qs ? `?${qs}` : ''}`);
};
export const crearConocimiento = (data) => request('/conocimiento', { method: 'POST', body: JSON.stringify(data) });
export const promoverADN = (id, data) => request(`/conocimiento/${id}/promover-adn`, { method: 'POST', body: JSON.stringify(data) });

// Tensiones
export const getTensiones = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/tensiones${qs ? `?${qs}` : ''}`);
};
export const crearTension = (data) => request('/tensiones', { method: 'POST', body: JSON.stringify(data) });

// Depuración
export const getDepuracion = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/depuracion${qs ? `?${qs}` : ''}`);
};
export const crearDepuracion = (data) => request('/depuracion', { method: 'POST', body: JSON.stringify(data) });
export const actualizarDepuracion = (id, data) => request(`/depuracion/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

// Readiness
export const getReadiness = () => request('/readiness');
```

### B2. Añadir pestañas en Profundo.jsx

**Archivo:** `@project/frontend/src/Profundo.jsx` — LEER PRIMERO.

Añadir 'adn' y 'depuracion' al array de tabs. Añadir contenido para cada pestaña:

**Pestaña ADN:**
- Lista principios agrupados por categoría (innegociable, flexible, método, filosofía, antipatrón)
- Formulario para crear nuevo principio
- Indicador de readiness prominente

**Pestaña Depuración (F3):**
- Lista depuraciones por estado (propuesta → aprobada → ejecutada)
- Botones para cambiar estado
- Formulario para crear nueva depuración
- Enlace a tensiones activas

El código JSX sigue el mismo patrón que las pestañas existentes (grupos, contabilidad) con formularios inline y listas con acciones.

---

## FASE C: Integrar readiness en Dashboard

**Archivo:** `@project/src/pilates/router.py` — En el endpoint `dashboard_profundo` (GET /dashboard), AÑADIR al final antes del return:

```python
    # Readiness de replicación
    from src.pilates.router import readiness_replicacion
    # Llamar directamente la lógica, no el endpoint
    # (copiar la lógica inline o importar como función)
```

Alternativa más limpia: extraer la lógica de readiness a una función async en un módulo separado o como función privada en router.py, y llamarla desde dashboard.

---

## Pass/fail

- 5 endpoints ADN (CRUD + desactivar)
- 4 endpoints Procesos (CRUD con versionado)
- 3 endpoints Conocimiento (CRUD + promover a ADN)
- 3 endpoints Tensiones (CRUD + resolver/crónica)
- 4 endpoints Depuración (CRUD + cambio estado + resultado)
- GET /pilates/readiness calcula readiness de replicación con 5 componentes
- POST /pilates/conocimiento/{id}/promover-adn convierte aprendizaje en principio ADN
- Procesos incrementan veces_consultado al ser leídos
- ADN desactivado (no borrado) para historial
- Depuración con flujo propuesta → aprobada → ejecutada + resultado
- Frontend: pestañas ADN y Depuración en Modo Profundo
- api.js con todas las funciones CRUD

---

## IMPACTO EN PRESCRIPCIÓN ACD

Cuando el ACD prescribe "TRANSFERIR" para cerrar el gap de Continuidad (C):

| Prescripción | Acción en el sistema | Tabla |
|---|---|---|
| "Documentar método EEDAP" | POST /procesos con pasos | om_procesos |
| "Codificar filosofía Pilates" | POST /adn con categoria='filosofia' | om_adn |
| "Eliminar seguimiento manual recuperaciones" | POST /depuracion con tipo='proceso_redundante' | om_depuracion |
| "Registrar aprendizaje: clientes >55 necesitan calentamiento extra" | POST /conocimiento | om_conocimiento |
| "Promover a principio: siempre calentar >55" | POST /conocimiento/{id}/promover-adn | om_conocimiento → om_adn |
| "Competencia nueva: estudio reformer abre en centro" | POST /tensiones | om_tensiones |

El readiness sube con cada acción. El briefing del lunes muestra el progreso. El Séquito usa estos datos para sus respuestas.
