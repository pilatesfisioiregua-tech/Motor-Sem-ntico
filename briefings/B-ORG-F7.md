# B-ORG-F7 — Fase 7: Presencia Digital con Identidad

**Fecha:** 24 marzo 2026
**Estimación:** ~28h
**Prerequisito:** B-ORG-F4 (motor.pensar), B-ORG-F5 (pizarra comunicación, reactivo), B-ORG-F6 (multi-tenant, tests)
**WIP:** 2 (sensores y filtro son paralelos)
**Principios:** P67 (identidad desde dentro, no copiada), P68 (eliminar > añadir)

---

## OBJETIVO

El organismo deja de ser un sistema interno y proyecta su identidad al mundo exterior. La identidad NO se copia de la competencia — se diagnostica desde dentro (ACD + lente Sentido) y se proyecta hacia fuera. F5 es el director creativo, F3 el filtro de coherencia, F6 los ojos.

**Antes:** El sistema piensa sobre el negocio pero no actúa fuera de WA.
**Después:** Instagram, Google Business Profile, contenido, reseñas, leads — todo filtrado por identidad. Si no es coherente con quién eres, F3 lo bloquea.

---

## CIRCUITO F7 (P67)

```
ACD → F5 cristaliza identidad → F6 observa terreno externo
  → Director diseña contenido → F3 filtra (¿es coherente?)
  → Si pasa: publicar/interactuar via pizarra comunicación
  → Si no: → om_depuracion (señal F3)
  → Feedback engagement → Memoria detecta patrones
  → Anti-dilución: 4 ciclos divergentes → F3 → Director recalibra
```

---

## ARCHIVOS A LEER ANTES DE EMPEZAR

```
src/pilates/voz_identidad.py       ← Seed identidad existente
src/pilates/af5_identidad.py       ← AF5 gaps identidad
src/pilates/af3_depuracion.py      ← AF3 depuración + VETO
src/pilates/collectors.py          ← Collectors IG + GBP existentes
src/pilates/buscador.py            ← Buscadores especializados
src/motor/pensar.py                ← API pensamiento (F4)
src/pilates/pizarras.py            ← Helper pizarras (F2)
src/pilates/reactivo.py            ← Despachador comunicaciones (F5)
src/pilates/traductor.py           ← Traductor álgebra→castellano (F5)
```

---

## PASO 0: MIGRACIÓN SQL (032_identidad_presencia.sql)

Crear archivo: `migrations/032_identidad_presencia.sql`

```sql
-- 032_identidad_presencia.sql — Pizarra Identidad (#11) + contenido + presencia digital
-- Fase 7 del Roadmap v4 (P67)

-- 1. PIZARRA IDENTIDAD (#11) — ADN del exocórtex
CREATE TABLE IF NOT EXISTS om_pizarra_identidad (
    tenant_id TEXT PRIMARY KEY,
    -- Quién soy
    esencia TEXT,
    narrativa TEXT,
    valores TEXT[],
    propuesta_valor TEXT,
    metodo TEXT,
    -- Qué NO soy
    anti_identidad TEXT[],
    depuraciones_deliberadas TEXT[],
    -- Voz y estética
    tono TEXT,
    tono_ejemplos JSONB DEFAULT '[]',
    estilo_visual JSONB DEFAULT '{}',
    -- Posición desde ACD
    posicion_lentes JSONB DEFAULT '{}',
    angulo_diferencial TEXT,
    -- Configuración por canal
    canales JSONB DEFAULT '{}',
    -- Metadata
    ultima_revision TIMESTAMPTZ,
    origen TEXT DEFAULT 'seed',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Seed desde voz_identidad.py existente
INSERT INTO om_pizarra_identidad (tenant_id, esencia, narrativa, valores, propuesta_valor, metodo,
    anti_identidad, depuraciones_deliberadas, tono, angulo_diferencial, origen)
VALUES ('authentic_pilates',
    'Pilates auténtico con atención real en un pueblo de La Rioja. No somos un gimnasio.',
    'Jesús dejó su carrera anterior para dedicarse a lo que le apasiona: enseñar Pilates de verdad. En Albelda de Iregua, cada persona tiene nombre, historia y un cuerpo único.',
    ARRAY['autenticidad', 'atención_individual', 'método_original', 'cercanía', 'rigor'],
    'Pilates auténtico con atención real. Cada sesión es única porque cada persona es única.',
    'EEDAP de Fabien Menegon — Escuela de Educación del Authentic Pilates',
    ARRAY['gimnasio masivo', 'clases de 20 personas', 'entrenadores sin formación', 'descuentos agresivos', 'marketing de urgencia'],
    ARRAY['nunca publicar ofertas tipo "50% descuento"', 'nunca copiar estética de cadenas fitness', 'nunca hablar de "transformación corporal en 30 días"'],
    'cercano, profesional, sin jerga fitness. Como habla un vecino que sabe mucho de su oficio.',
    'El único estudio con método EEDAP en La Rioja. Grupos de máximo 4 personas. No vendemos abdominales, vendemos que tu cuerpo funcione bien.',
    'seed')
ON CONFLICT (tenant_id) DO NOTHING;

-- 2. CONTENIDO — Calendario + publicaciones
CREATE TABLE IF NOT EXISTS om_contenido (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    ciclo TEXT NOT NULL,
    canal TEXT NOT NULL,
    tipo TEXT NOT NULL,
    titulo TEXT,
    cuerpo TEXT NOT NULL,
    hashtags TEXT[],
    media_url TEXT,
    funcion TEXT,
    lente TEXT,
    ints TEXT[],
    -- Estado
    estado TEXT DEFAULT 'borrador',
    filtro_identidad TEXT DEFAULT 'pendiente',
    filtro_motivo TEXT,
    programado_para TIMESTAMPTZ,
    publicado_at TIMESTAMPTZ,
    -- Métricas post-publicación
    alcance INT,
    engagement INT,
    clicks INT,
    guardados INT,
    compartidos INT,
    coherencia_score FLOAT,
    -- Metadata
    origen TEXT DEFAULT 'director',
    aprobado_por TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_contenido_ciclo ON om_contenido(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_contenido_estado ON om_contenido(estado);
CREATE INDEX IF NOT EXISTS idx_contenido_canal ON om_contenido(canal);

-- 3. COMPETENCIA — Perfiles públicos monitorizados
CREATE TABLE IF NOT EXISTS om_competencia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    nombre TEXT NOT NULL,
    canal TEXT NOT NULL,
    handle TEXT,
    url TEXT,
    tipo TEXT DEFAULT 'directo',
    followers INT,
    engagement_rate FLOAT,
    ultima_recogida TIMESTAMPTZ,
    datos JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_comp_tenant ON om_competencia(tenant_id);

-- 4. LEADS EXTERNOS — Leads que llegan por canales digitales
CREATE TABLE IF NOT EXISTS om_leads_externos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    canal TEXT NOT NULL,
    nombre TEXT,
    contacto TEXT,
    mensaje TEXT,
    compatible_identidad BOOLEAN,
    score_compatibilidad FLOAT,
    estado TEXT DEFAULT 'nuevo',
    asignado_a TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_leads_ext_estado ON om_leads_externos(estado);

-- 5. Trigger: contenido publicado → señal bus
CREATE OR REPLACE FUNCTION notify_contenido_publicado() RETURNS trigger AS $$
BEGIN
    IF NEW.estado = 'publicado' AND (OLD.estado IS NULL OR OLD.estado != 'publicado') THEN
        PERFORM pg_notify('contenido_publicado', json_build_object(
            'id', NEW.id, 'canal', NEW.canal, 'tipo', NEW.tipo
        )::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_contenido_publicado ON om_contenido;
CREATE TRIGGER trg_contenido_publicado
    AFTER INSERT OR UPDATE ON om_contenido
    FOR EACH ROW EXECUTE FUNCTION notify_contenido_publicado();
```

**Test 0.1:** `SELECT esencia FROM om_pizarra_identidad WHERE tenant_id='authentic_pilates'` → texto
**Test 0.2:** `SELECT count(*) FROM om_contenido` → 0
**Test 0.3:** `SELECT count(*) FROM om_competencia` → 0

---

## PASO 1: FILTRO IDENTIDAD — F3 como guardián (~3h)

Crear archivo: `src/pilates/filtro_identidad.py`

```python
"""Filtro Identidad — F3 como guardián de coherencia (P67).

Todo contenido externo pasa por aquí ANTES de publicarse.
Compatible → pasa. Incompatible → om_depuracion + señal F3.

Reglas claras → código puro ($0).
Ambiguo → motor.pensar() con INT-15 (estética) + INT-17 (existencial).
"""
from __future__ import annotations

import json
import structlog
from typing import Optional

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def leer_identidad(tenant_id: str = TENANT) -> dict:
    """Lee pizarra identidad del tenant."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_pizarra_identidad WHERE tenant_id = $1", tenant_id)
        if row:
            return dict(row)
    return {}


async def filtrar_por_identidad(
    contenido: str,
    canal: str = "instagram",
    tenant_id: str = TENANT,
) -> dict:
    """Filtra contenido contra la identidad del tenant.

    Returns:
        {"compatible": bool, "score": 0-1, "motivo": str, "metodo": "reglas"|"llm"}
    """
    identidad = await leer_identidad(tenant_id)
    if not identidad:
        return {"compatible": True, "score": 0.5, "motivo": "Sin identidad configurada", "metodo": "default"}

    # FASE 1: Reglas claras ($0)
    anti = identidad.get("anti_identidad") or []
    depuraciones = identidad.get("depuraciones_deliberadas") or []
    texto_lower = contenido.lower()

    # Check anti-identidad
    for anti_item in anti:
        keywords = anti_item.lower().split()
        if all(kw in texto_lower for kw in keywords if len(kw) > 3):
            return {
                "compatible": False,
                "score": 0.1,
                "motivo": f"Anti-identidad detectada: '{anti_item}'",
                "metodo": "reglas",
            }

    # Check depuraciones deliberadas
    for dep in depuraciones:
        dep_keywords = [w for w in dep.lower().split() if len(w) > 3]
        if dep_keywords and sum(1 for kw in dep_keywords if kw in texto_lower) >= len(dep_keywords) * 0.6:
            return {
                "compatible": False,
                "score": 0.15,
                "motivo": f"Depuración deliberada: '{dep}'",
                "metodo": "reglas",
            }

    # Check tono incompatible
    tonos_prohibidos = ["compra ya", "últimas plazas", "oferta limitada",
                        "transforma tu cuerpo", "resultados garantizados",
                        "pierde peso", "sin esfuerzo"]
    for tono in tonos_prohibidos:
        if tono in texto_lower:
            return {
                "compatible": False,
                "score": 0.2,
                "motivo": f"Tono incompatible: '{tono}'",
                "metodo": "reglas",
            }

    # FASE 2: Si no es claramente incompatible, ¿es claramente compatible?
    valores = identidad.get("valores") or []
    score_compatible = 0.5  # base
    for valor in valores:
        if valor.lower().replace("_", " ") in texto_lower:
            score_compatible += 0.1

    if score_compatible >= 0.7:
        return {
            "compatible": True,
            "score": min(1.0, score_compatible),
            "motivo": "Coherente con valores",
            "metodo": "reglas",
        }

    # FASE 3: Ambiguo → LLM (motor.pensar)
    try:
        from src.motor.pensar import pensar, ConfigPensamiento

        system = f"""Eres el filtro de identidad de {identidad.get('esencia', 'un estudio de Pilates')}.
Valores: {', '.join(valores)}
Anti-identidad: {', '.join(anti)}
Tono: {identidad.get('tono', 'cercano y profesional')}
Ángulo: {identidad.get('angulo_diferencial', '')}

Evalúa si el siguiente contenido es COHERENTE con esta identidad.
Responde SOLO JSON: {{"compatible": true/false, "score": 0-1, "motivo": "explicación breve"}}"""

        config = ConfigPensamiento(
            funcion="F3", lente="sentido", complejidad="baja",
            usar_cache=True, ttl_cache_horas=168,
        )
        resultado = await pensar(system=system, user=f"Contenido a evaluar:\n{contenido}", config=config)
        from src.pilates.json_utils import extraer_json
        parsed = extraer_json(resultado.texto, fallback={"compatible": True, "score": 0.5})
        parsed["metodo"] = "llm"
        return parsed

    except Exception as e:
        log.warning("filtro_identidad_llm_error", error=str(e)[:80])
        return {"compatible": True, "score": 0.5, "motivo": "LLM error, permitir por defecto", "metodo": "error"}


async def filtrar_contenido_db(contenido_id, tenant_id: str = TENANT) -> dict:
    """Filtra un contenido de om_contenido y actualiza su estado."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_contenido WHERE id = $1 AND tenant_id = $2",
            contenido_id, tenant_id)
        if not row:
            return {"error": "Contenido no encontrado"}

        resultado = await filtrar_por_identidad(row["cuerpo"], row["canal"], tenant_id)

        await conn.execute("""
            UPDATE om_contenido
            SET filtro_identidad = $2, filtro_motivo = $3, updated_at = now()
            WHERE id = $1
        """, contenido_id,
            "compatible" if resultado["compatible"] else "incompatible",
            resultado.get("motivo", ""))

        # Si incompatible → registrar en om_depuracion + señal F3
        if not resultado["compatible"]:
            try:
                from src.pilates.bus import emitir
                await emitir("ALERTA", "F3_FILTRO",
                    {"tipo": "contenido_incompatible", "contenido_id": str(contenido_id),
                     "motivo": resultado["motivo"], "score": resultado["score"]},
                    destino="AF3", prioridad=3)
            except Exception:
                pass

    return resultado
```

**Test 1.1:** `python -c "from src.pilates.filtro_identidad import filtrar_por_identidad; print('ok')"` → ok
**Test 1.2:** `filtrar_por_identidad("¡Oferta limitada! 50% descuento hoy!")` → `{compatible: false}`
**Test 1.3:** `filtrar_por_identidad("Hoy hemos trabajado movilidad de cadera con María")` → `{compatible: true}`

---

## PASO 2: GENERADOR DE CONTENIDO — Director diseña desde identidad (~4h)

Crear archivo: `src/pilates/contenido.py`

```python
"""Contenido — Generación y gestión de contenido digital (P67).

El Director incluye recetas de contenido externo en la pizarra cognitiva.
La matriz 3L×7F determina el ángulo. Todo pasa por filtro identidad.

Flujo: Director receta → generar_contenido() → filtro F3 → programar en pizarra comunicación
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.db.client import get_pool
from src.motor.pensar import pensar, ConfigPensamiento
from src.pilates.json_utils import extraer_json
from src.pilates.filtro_identidad import leer_identidad, filtrar_contenido_db

log = structlog.get_logger()

TENANT = "authentic_pilates"

# Matriz 3L×7F → ángulos de contenido
ANGULOS = {
    ("S", "F1"): "Historias de clientes que se mantienen fieles. Consistencia.",
    ("S", "F2"): "Cómo el método EEDAP transforma de forma real, no mágica.",
    ("S", "F3"): "Lo que NO hacemos y por qué. Diferenciación por eliminación.",
    ("Se", "F5"): "Quiénes somos. Valores. El pueblo. La persona detrás.",
    ("Se", "F6"): "Cómo nos adaptamos sin perder esencia. Temporadas, cambios.",
    ("C", "F7"): "El método perdura. Formación EEDAP. Lo que se transfiere.",
    ("C", "F4"): "Cómo el Pilates se integra en tu vida diaria.",
}

SYSTEM_CONTENIDO = """Eres el generador de contenido de {nombre}, un estudio de Pilates en {ubicacion}.

IDENTIDAD:
{identidad_resumen}

REGLAS:
- Tono: {tono}
- Máximo 280 chars para Instagram caption (sin hashtags)
- Para GBP posts: máximo 500 chars
- Sugiere 3-5 hashtags relevantes
- NUNCA uses tono de gimnasio masivo, urgencia falsa, o promesas de transformación rápida
- Escribe como habla un profesional cercano de pueblo, no como un community manager de Barcelona

Formato JSON:
{{
  "titulo": "titulo corto",
  "cuerpo": "el contenido principal",
  "hashtags": ["tag1", "tag2"],
  "tipo_media": "foto|video|carrusel|texto",
  "sugerencia_media": "descripción de la foto/video ideal"
}}"""


async def generar_contenido_semana(ciclo: str = None) -> dict:
    """Genera el calendario de contenido de la semana.

    Lee identidad + recetas del Director + datos del negocio
    → genera 3-5 piezas de contenido → filtra con F3 → guarda en om_contenido.
    """
    if ciclo is None:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    identidad = await leer_identidad(TENANT)
    if not identidad or not identidad.get("esencia"):
        return {"status": "skip", "razon": "Sin identidad configurada"}

    # Leer contexto del negocio
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Datos frescos
        clientes_activos = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id=$1 AND estado='activo'", TENANT)
        sesiones_semana = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones
            WHERE tenant_id=$1 AND fecha >= date_trunc('week', now()) AND fecha < date_trunc('week', now()) + interval '7 days'
        """, TENANT)

    # Seleccionar 3 ángulos para la semana (rotar por ciclo)
    import hashlib
    seed = int(hashlib.md5(ciclo.encode()).hexdigest()[:8], 16)
    angulos_keys = list(ANGULOS.keys())
    seleccionados = []
    for i in range(3):
        idx = (seed + i) % len(angulos_keys)
        lente, funcion = angulos_keys[idx]
        seleccionados.append({
            "lente": lente, "funcion": funcion,
            "angulo": ANGULOS[angulos_keys[idx]],
        })

    identidad_resumen = (
        f"Esencia: {identidad.get('esencia', '')}\n"
        f"Valores: {', '.join(identidad.get('valores', []))}\n"
        f"Anti-identidad: {', '.join(identidad.get('anti_identidad', []))}\n"
        f"Ángulo diferencial: {identidad.get('angulo_diferencial', '')}"
    )

    system = SYSTEM_CONTENIDO.format(
        nombre=identidad.get("esencia", "Authentic Pilates").split(".")[0],
        ubicacion="Albelda de Iregua, La Rioja",
        identidad_resumen=identidad_resumen,
        tono=identidad.get("tono", "cercano y profesional"),
    )

    user = (
        f"Ciclo: {ciclo}\n"
        f"Clientes activos: {clientes_activos}\n"
        f"Sesiones esta semana: {sesiones_semana}\n\n"
        f"Genera 3 piezas de contenido para Instagram, una por cada ángulo:\n"
    )
    for i, a in enumerate(seleccionados):
        user += f"\n{i+1}. Lente {a['lente']}, Función {a['funcion']}: {a['angulo']}"

    user += "\n\nResponde con un JSON array de 3 objetos."

    config = ConfigPensamiento(
        funcion="F5", lente="sentido", complejidad="media",
        usar_cache=True, ttl_cache_horas=168,
    )
    resultado = await pensar(system=system, user=user, config=config)
    piezas = extraer_json(resultado.texto, fallback={"items": []})
    if isinstance(piezas, dict):
        piezas = piezas.get("items", piezas.get("contenidos", [piezas]))
    if not isinstance(piezas, list):
        piezas = [piezas]

    # Guardar en om_contenido y filtrar
    creados = 0
    filtrados = 0
    async with pool.acquire() as conn:
        for i, pieza in enumerate(piezas[:5]):
            if not isinstance(pieza, dict) or not pieza.get("cuerpo"):
                continue

            row = await conn.fetchrow("""
                INSERT INTO om_contenido
                    (tenant_id, ciclo, canal, tipo, titulo, cuerpo, hashtags,
                     funcion, lente, ints, estado, origen)
                VALUES ($1, $2, 'instagram', $3, $4, $5, $6, $7, $8, $9, 'borrador', 'director')
                RETURNING id
            """, TENANT, ciclo,
                pieza.get("tipo_media", "foto"),
                pieza.get("titulo", f"Contenido {i+1}"),
                pieza["cuerpo"],
                pieza.get("hashtags", []),
                seleccionados[i]["funcion"] if i < len(seleccionados) else None,
                seleccionados[i]["lente"] if i < len(seleccionados) else None,
                [],
            )
            creados += 1

            # Filtrar con F3
            filtro = await filtrar_contenido_db(row["id"], TENANT)
            if not filtro.get("compatible", True):
                filtrados += 1

    log.info("contenido_generado", ciclo=ciclo, creados=creados, filtrados=filtrados,
             coste=resultado.coste_usd)

    return {
        "status": "ok", "ciclo": ciclo,
        "creados": creados, "filtrados_f3": filtrados,
        "coste": resultado.coste_usd,
    }


async def aprobar_contenido(contenido_id, aprobado_por: str = "jesus") -> dict:
    """CR1: Jesús aprueba contenido para publicación."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE om_contenido
            SET estado = 'aprobado', aprobado_por = $2, updated_at = now()
            WHERE id = $1 AND filtro_identidad = 'compatible'
        """, contenido_id, aprobado_por)
    return {"status": "ok"}


async def programar_publicacion(contenido_id, programado_para: datetime = None) -> dict:
    """Programa contenido aprobado para publicación."""
    if programado_para is None:
        programado_para = datetime.now(ZoneInfo("Europe/Madrid")) + timedelta(hours=2)

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE om_contenido
            SET estado = 'programado', programado_para = $2, updated_at = now()
            WHERE id = $1 AND estado = 'aprobado'
        """, contenido_id, programado_para)
    return {"status": "ok", "programado_para": str(programado_para)}
```

**Test 2.1:** `python -c "from src.pilates.contenido import generar_contenido_semana; print('ok')"` → ok

---

## PASO 3: SENSORES EXTERNOS — Collectors mejorados (~3h)

`collectors.py` ya existe con estructura para Instagram + GBP. Mejorarlo:

### 3.1 Añadir collector de competencia

Al final de `collectors.py`, añadir:

```python
async def collect_competencia() -> dict:
    """Recoge datos públicos de competidores monitorizados.

    Lee om_competencia → para cada uno, scrape público (sin API, datos públicos).
    Frecuencia: semanal.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        competidores = await conn.fetch(
            "SELECT * FROM om_competencia WHERE tenant_id = $1", TENANT)

    if not competidores:
        return {"status": "skip", "razon": "Sin competidores configurados"}

    # Por ahora, log que están configurados pero no scrapeamos aún
    # (scraping de IG requiere sesión — usar Perplexity para análisis)
    log.info("collector_competencia", total=len(competidores))
    return {"status": "ok", "competidores": len(competidores)}
```

### 3.2 Seed competidores iniciales

En la migration 032, añadir:

```sql
-- Seeds competencia Albelda/Logroño
INSERT INTO om_competencia (tenant_id, nombre, canal, handle, tipo) VALUES
    ('authentic_pilates', 'Pilates Logroño Centro', 'instagram', NULL, 'directo'),
    ('authentic_pilates', 'Gimnasio Municipal Albelda', 'gbp', NULL, 'indirecto'),
    ('authentic_pilates', 'Fisio + Pilates Rioja', 'instagram', NULL, 'directo')
ON CONFLICT DO NOTHING;
```

### 3.3 En cron semanal, añadir generación de contenido

En `_tarea_semanal()`, DESPUÉS del traductor:

```python
        # 13. Generar contenido semanal (F7 — presencia digital)
        try:
            from src.pilates.contenido import generar_contenido_semana
            cont = await generar_contenido_semana()
            log.info("cron_semanal_contenido_ok",
                     creados=cont.get("creados", 0),
                     filtrados=cont.get("filtrados_f3", 0))
        except Exception as e:
            log.error("cron_semanal_contenido_error", error=str(e))
```

**Test 3.1:** `grep "generar_contenido_semana" src/pilates/cron.py` → match

---

## PASO 4: DETECTOR ANTI-DILUCIÓN (~2h)

Crear archivo: `src/pilates/anti_dilucion.py`

```python
"""Anti-dilución — Detecta drift de identidad en contenido publicado (P67).

Si el contenido publicado diverge de la pizarra identidad durante 4+ ciclos,
emite señal F3 para que el Director recalibre.

Se ejecuta mensualmente (en _tarea_mensual).
"""
from __future__ import annotations

import structlog
from src.db.client import get_pool
from src.pilates.filtro_identidad import leer_identidad, filtrar_por_identidad

log = structlog.get_logger()

TENANT = "authentic_pilates"
CICLOS_DRIFT_UMBRAL = 4


async def detectar_drift_identidad() -> dict:
    """Analiza contenido publicado de los últimos 4 ciclos.

    Si >30% del contenido publicado tiene coherencia_score < 0.5,
    hay drift → señal F3.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Contenido publicado últimos 4 ciclos
        publicados = await conn.fetch("""
            SELECT id, cuerpo, canal, coherencia_score, ciclo
            FROM om_contenido
            WHERE tenant_id = $1 AND estado = 'publicado'
            ORDER BY publicado_at DESC
            LIMIT 20
        """, TENANT)

    if len(publicados) < 4:
        return {"status": "skip", "razon": "datos_insuficientes"}

    # Re-evaluar coherencia de cada pieza
    incoherentes = 0
    total = len(publicados)

    for p in publicados:
        if p["coherencia_score"] is not None and p["coherencia_score"] < 0.5:
            incoherentes += 1
        elif p["coherencia_score"] is None:
            # Evaluar si no tiene score
            resultado = await filtrar_por_identidad(p["cuerpo"], p["canal"], TENANT)
            if not resultado.get("compatible", True) or resultado.get("score", 1) < 0.5:
                incoherentes += 1
            # Actualizar score
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE om_contenido SET coherencia_score = $2 WHERE id = $1
                """, p["id"], resultado.get("score", 0.5))

    ratio_incoherente = incoherentes / max(total, 1)

    if ratio_incoherente > 0.3:
        # DRIFT detectado
        try:
            from src.pilates.bus import emitir
            await emitir("ALERTA", "ANTI_DILUCION",
                {"tipo": "drift_identidad",
                 "ratio_incoherente": round(ratio_incoherente, 2),
                 "total_evaluados": total,
                 "incoherentes": incoherentes,
                 "accion": "Director debe recalibrar contenido"},
                destino="DIRECTOR", prioridad=2)
            log.warning("anti_dilucion_drift", ratio=ratio_incoherente, incoherentes=incoherentes)
        except Exception:
            pass

        return {"status": "drift", "ratio": ratio_incoherente, "incoherentes": incoherentes}

    log.info("anti_dilucion_ok", ratio=ratio_incoherente)
    return {"status": "ok", "ratio": ratio_incoherente, "incoherentes": incoherentes}
```

### 4.1 En _tarea_mensual(), añadir:

```python
    # Anti-dilución: detectar drift de identidad en contenido publicado
    try:
        from src.pilates.anti_dilucion import detectar_drift_identidad
        drift = await detectar_drift_identidad()
        log.info("cron_mensual_anti_dilucion", status=drift.get("status"))
    except Exception as e:
        log.error("cron_mensual_anti_dilucion_error", error=str(e))
```

**Test 4.1:** `python -c "from src.pilates.anti_dilucion import detectar_drift_identidad; print('ok')"` → ok

---

## PASO 5: ENDPOINTS CONTENIDO + IDENTIDAD (~2h)

Añadir en `src/pilates/router.py`:

```python
# ============================================================
# IDENTIDAD + CONTENIDO (F7)
# ============================================================

@router.get("/identidad")
async def get_identidad():
    """Lee la pizarra identidad del tenant."""
    from src.pilates.filtro_identidad import leer_identidad
    return await leer_identidad()


@router.patch("/identidad")
async def actualizar_identidad(request: Request):
    """Actualiza campos de la pizarra identidad (CR1 Jesús)."""
    body = await request.json()
    from src.db.client import get_pool
    pool = await get_pool()
    campos_permitidos = ["esencia", "narrativa", "valores", "anti_identidad",
                         "depuraciones_deliberadas", "tono", "angulo_diferencial"]
    sets = []
    params = ["authentic_pilates"]
    for campo in campos_permitidos:
        if campo in body:
            params.append(body[campo])
            sets.append(f"{campo} = ${len(params)}")
    if not sets:
        raise HTTPException(400, "Sin campos válidos")
    sets.append("updated_at = now()")
    query = f"UPDATE om_pizarra_identidad SET {', '.join(sets)} WHERE tenant_id = $1"
    async with pool.acquire() as conn:
        await conn.execute(query, *params)
    return {"status": "ok"}


@router.get("/contenido")
async def get_contenido(ciclo: str = None, estado: str = None, limit: int = 20):
    """Lista contenido generado."""
    from src.db.client import get_pool
    pool = await get_pool()
    query = "SELECT * FROM om_contenido WHERE tenant_id = 'authentic_pilates'"
    params = []
    if ciclo:
        params.append(ciclo)
        query += f" AND ciclo = ${len(params)}"
    if estado:
        params.append(estado)
        query += f" AND estado = ${len(params)}"
    query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
    params.append(limit)
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]


@router.post("/contenido/{contenido_id}/aprobar")
async def aprobar(contenido_id):
    """CR1: Jesús aprueba contenido para publicación."""
    from uuid import UUID
    from src.pilates.contenido import aprobar_contenido
    return await aprobar_contenido(UUID(contenido_id))


@router.post("/contenido/{contenido_id}/programar")
async def programar(contenido_id, request: Request):
    """Programa contenido aprobado."""
    from uuid import UUID
    from src.pilates.contenido import programar_publicacion
    body = await request.json()
    return await programar_publicacion(UUID(contenido_id))


@router.post("/contenido/filtrar")
async def filtrar_contenido_manual(request: Request):
    """Filtra texto contra identidad (para preview)."""
    body = await request.json()
    from src.pilates.filtro_identidad import filtrar_por_identidad
    return await filtrar_por_identidad(body.get("texto", ""), body.get("canal", "instagram"))


@router.get("/competencia")
async def get_competencia():
    """Lista competidores monitorizados."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM om_competencia WHERE tenant_id = 'authentic_pilates'")
    return [dict(r) for r in rows]
```

**Test 5.1:** `curl /pilates/identidad` → JSON con esencia, valores, tono
**Test 5.2:** `curl /pilates/contenido` → JSON array
**Test 5.3:** `curl -X POST /pilates/contenido/filtrar -d '{"texto":"¡50% descuento hoy!"}' ` → `{compatible: false}`

---

## PASO 6: FRONTEND — Tab Identidad + Contenido (~6h)

### 6.1 API exports (frontend/src/api.js)

```js
// IDENTIDAD + CONTENIDO (F7)
export const getIdentidad = () => request('/identidad');
export const actualizarIdentidad = (data) => request('/identidad', { method: 'PATCH', body: JSON.stringify(data) });
export const getContenido = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/contenido${qs ? `?${qs}` : ''}`);
};
export const aprobarContenido = (id) => request(`/contenido/${id}/aprobar`, { method: 'POST' });
export const programarContenido = (id) => request(`/contenido/${id}/programar`, { method: 'POST', body: '{}' });
export const filtrarContenido = (data) => request('/contenido/filtrar', { method: 'POST', body: JSON.stringify(data) });
export const getCompetencia = () => request('/competencia');
```

### 6.2 Panel Identidad en Cockpit (panels/IdentidadPanel.jsx)

Crear panel que muestra: esencia (editable), valores como badges, anti-identidad como badges rojos, tono, ángulo diferencial. Botón "Editar" que abre modal de edición inline.

### 6.3 Panel Contenido en Cockpit (panels/ContenidoPanel.jsx)

Crear panel que muestra: contenidos del ciclo actual, estado (borrador/aprobado/programado/publicado) con colores, botón "Aprobar" por pieza, filtro_identidad visible (compatible=verde, incompatible=rojo).

### 6.4 Tab Contenido en Profundo

En Profundo.jsx, añadir tab que muestra: calendario contenido semana, piezas con preview, filtro identidad, métricas post-publicación, competencia.

**Nota:** Los detalles de implementación de los componentes React siguen el mismo patrón que los paneles de F6B — usar useFetch, Card, design tokens. No duplico el JSX completo aquí porque Claude Code puede generarlo siguiendo los patrones establecidos en OrganismoPanel.jsx.

**Test 6.1:** Cockpit capa "identidad" → IdentidadPanel con esencia + valores + anti-identidad
**Test 6.2:** Panel contenido → piezas con estado + botón aprobar
**Test 6.3:** Profundo tab → calendario semanal + métricas

---

## PASO 7: LEADS FILTRADOS POR IDENTIDAD (~2h)

### 7.1 Embajador filtrado en wa_chat.py

En el flujo de respuesta a leads nuevos (primer contacto WA), añadir filtro:

```python
# En la función que procesa mensajes de leads nuevos:
from src.pilates.filtro_identidad import filtrar_por_identidad

# Evaluar si el lead es compatible con la identidad
# (ej: alguien preguntando por CrossFit → no compatible)
filtro = await filtrar_por_identidad(mensaje_texto, "whatsapp")
if not filtro.get("compatible", True):
    # Responder educadamente que no es lo que buscas
    # Registrar en om_leads_externos como incompatible
    pass
```

### 7.2 Registrar leads externos

Cuando llega un lead por IG o WA, registrar en `om_leads_externos` con score de compatibilidad.

**Test 7.1:** Lead preguntando por "clases de spinning" → marcado incompatible
**Test 7.2:** Lead preguntando por "Pilates para dolor de espalda" → marcado compatible

---

## PASO 8: PERPLEXITY PARA ANÁLISIS EXTERNO (~2h)

En `buscador.py`, el buscador Perplexity ya está preparado (aprobado como Capa A). Añadir queries específicas para F7:

```python
# En buscador.py, añadir tipo de búsqueda F7:
async def buscar_contexto_presencia(tenant_id: str = TENANT) -> dict:
    """Busca contexto externo para la presencia digital.

    Queries:
    - Tendencias Pilates en España 2026
    - Competencia estudios Pilates en Logroño/La Rioja
    - Mejores prácticas contenido para estudios pequeños
    """
    from src.pilates.filtro_identidad import leer_identidad
    identidad = await leer_identidad(tenant_id)

    queries = [
        f"tendencias pilates España {datetime.now().year}",
        f"estudios pilates {identidad.get('ubicacion', 'La Rioja')} opiniones",
        "contenido instagram pilates estudio pequeño que funciona",
    ]
    # ... usar Perplexity API si configurada ...
```

**Test 8.1:** `grep "buscar_contexto_presencia" src/pilates/buscador.py` → match

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `migrations/032_identidad_presencia.sql` | **NUEVO** — pizarra identidad + contenido + competencia + leads + trigger | 0 |
| `src/pilates/filtro_identidad.py` | **NUEVO** — F3 guardián: reglas $0 + LLM ambiguo | 1 |
| `src/pilates/contenido.py` | **NUEVO** — generación + aprobación + programación | 2 |
| `src/pilates/anti_dilucion.py` | **NUEVO** — detector drift 4 ciclos | 4 |
| `src/pilates/collectors.py` | +collector competencia | 3 |
| `src/pilates/cron.py` | +generar_contenido semanal + anti_dilucion mensual | 3, 4 |
| `src/pilates/router.py` | +8 endpoints identidad/contenido/competencia | 5 |
| `frontend/src/api.js` | +7 exports F7 | 6 |
| `frontend/src/panels/IdentidadPanel.jsx` | **NUEVO** | 6 |
| `frontend/src/panels/ContenidoPanel.jsx` | **NUEVO** | 6 |
| `frontend/src/Profundo.jsx` | +tab contenido | 6 |
| `src/pilates/wa_chat.py` | +filtro identidad en leads | 7 |
| `src/pilates/buscador.py` | +buscar_contexto_presencia | 8 |

## TESTS FINALES (PASS/FAIL)

```
T1:  SELECT esencia FROM om_pizarra_identidad → texto seed                           [PASS/FAIL]
T2:  python filtrar "50% descuento" → compatible: false                               [PASS/FAIL]
T3:  python filtrar "trabajo de cadera con María" → compatible: true                  [PASS/FAIL]
T4:  curl /pilates/identidad → JSON con esencia, valores, anti_identidad              [PASS/FAIL]
T5:  curl /pilates/contenido → JSON array                                             [PASS/FAIL]
T6:  curl -X POST /pilates/contenido/filtrar → resultado filtro                       [PASS/FAIL]
T7:  grep "generar_contenido_semana" src/pilates/cron.py → match                     [PASS/FAIL]
T8:  grep "detectar_drift_identidad" src/pilates/cron.py → match                     [PASS/FAIL]
T9:  Cockpit panel identidad → esencia + valores visibles                             [PASS/FAIL]
T10: npm run build → sin errores                                                      [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Crear `migrations/032_identidad_presencia.sql` (Paso 0)
2. Crear `src/pilates/filtro_identidad.py` (Paso 1)
3. Crear `src/pilates/contenido.py` (Paso 2)
4. Crear `src/pilates/anti_dilucion.py` (Paso 4)
5. Editar `src/pilates/collectors.py` + seeds competencia (Paso 3)
6. Editar `src/pilates/cron.py` — contenido semanal + anti-dilución mensual (Pasos 3, 4)
7. Editar `src/pilates/router.py` — 8 endpoints (Paso 5)
8. Frontend: api.js + 2 paneles + tab profundo (Paso 6)
9. Editar `wa_chat.py` — filtro leads (Paso 7)
10. Editar `buscador.py` — contexto presencia (Paso 8)
11. Deploy
12. Verificar T1-T10

## NOTAS

- **La publicación real en Instagram/GBP NO se implementa en este briefing.** Se genera contenido, se filtra, se aprueba, se programa. La publicación real via Meta Graph API requiere app review de Meta (~2-4 semanas) y se implementa como briefing separado B-ORG-PUBLISH cuando la app esté aprobada.
- **Competencia:** Por ahora solo se monitoriza con datos públicos + Perplexity. No se scrapea Instagram (ToS violation). Los handles se dejan NULL hasta que Jesús los rellene.
- **Filtro identidad es el corazón de F7.** Todo pasa por él. Las reglas cubren el 80% de los casos ($0). Solo el 20% ambiguo usa LLM (~$0.001/filtro).
- **Anti-dilución necesita ≥4 ciclos de contenido publicado.** Hasta entonces devuelve "datos_insuficientes".
- **La pizarra identidad es editable por Jesús** (PATCH /identidad). Es el ÚNICO punto donde Jesús define quién es el negocio. Todo lo demás se deriva.
