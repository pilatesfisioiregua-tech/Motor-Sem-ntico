# B-PIL-20: Bloque Voz Estratégico — Fiel a B2.8 v3.0

**Fecha:** 2026-03-21 (actualizado 2026-03-21)
**Ejecutor:** Claude Code
**Base de diseño:** docs/producto/B2_8_BLOQUE_VOZ_PRESENCIA_INTELIGENTE_v3.md
**Dependencia crítica:** B-PIL-15 (crea om_voz_propuestas, om_voz_telemetria, om_voz_isp, om_voz_capa_a)
**Reemplaza:** B-PIL-20 anterior

---

## ESTRUCTURA: 5 SUB-BRIEFINGS

El Bloque Voz de B2.8 es demasiado grande para un solo briefing.
Solo **20a es ejecutable ahora**. Los demás son roadmap — se convierten
en briefings detallados cuando toque ejecutarlos.

| Sub-briefing | Qué implementa | Dependencia | Estado |
|---|---|---|---|
| **B-PIL-20a** | Modelo de datos + Identidad + Seed AP + Diagnóstico inicial | — | **EJECUTABLE** |
| B-PIL-20b | Motor Tridimensional (IRC × Matriz × PCA) + Estrategia | 20a | ROADMAP |
| B-PIL-20c | Arquitecto de Presencia (configurar perfiles por canal) | 20a + 20b | ROADMAP |
| B-PIL-20d | 5 Ciclos + ISP automático + Telemetría | 20a + 20b + 20c | ROADMAP |
| B-PIL-20e | Integración cockpit + cron + briefing semanal + 3 modos | Todo | ROADMAP |

---

# B-PIL-20a: Modelo de datos + Identidad + Seed + Diagnóstico

## FASE A1: Migración SQL completa

**Archivo:** `migrations/017_voz_estrategico.sql`

### Verificación de dependencias

La migración 017 depende de tablas creadas en B-PIL-01 / B-PIL-15:
- `om_voz_propuestas` — ya debe existir
- `om_voz_telemetria` — ya debe existir
- `om_voz_isp` — ya debe existir (se extiende con ALTER TABLE)
- `om_voz_capa_a` — ya debe existir

Si alguna no existe, la migración falla con mensaje claro.

```sql
-- ============================================================
-- B-PIL-20a: BLOQUE VOZ ESTRATÉGICO — MODELO DE DATOS
-- Basado en B2.8 v3.0
-- REQUIERE: migrations previas que crean om_voz_isp,
--           om_voz_propuestas, om_voz_telemetria, om_voz_capa_a
-- ============================================================

BEGIN;

-- ── Verificar dependencias ──────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'om_voz_isp') THEN
        RAISE EXCEPTION 'Tabla om_voz_isp no existe. Ejecutar migración de B-PIL-15 primero.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'om_voz_propuestas') THEN
        RAISE EXCEPTION 'Tabla om_voz_propuestas no existe. Ejecutar migración de B-PIL-01 primero.';
    END IF;
END $$;

-- ── 1. Identidad de comunicación (B2.8 §2 — Capa 1) ───────
CREATE TABLE IF NOT EXISTS om_voz_identidad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',

    -- Estudio
    nombre_estudio TEXT,
    ubicacion TEXT,
    ubicacion_contexto TEXT,
    metodo_escuela TEXT,
    propuesta_valor TEXT,
    diferenciadores JSONB DEFAULT '[]',
    tono TEXT,
    personalidad TEXT,

    -- Target (3 niveles como define B2.8)
    target_primario JSONB DEFAULT '{}',
    target_secundario JSONB DEFAULT '{}',
    target_terciario JSONB DEFAULT '{}',

    -- Mercado
    nivel_conocimiento TEXT,
    confusiones_comunes JSONB DEFAULT '[]',
    competencia_percibida JSONB DEFAULT '[]',
    barreras_entrada JSONB DEFAULT '[]',

    -- Filosofía de comunicación
    principios_comunicacion JSONB DEFAULT '[]',
    lo_que_nunca_decir JSONB DEFAULT '[]',
    palabras_clave JSONB DEFAULT '[]',
    palabras_prohibidas JSONB DEFAULT '[]',

    -- Perfiles actuales (estado real)
    perfil_maps JSONB DEFAULT '{}',
    perfil_instagram JSONB DEFAULT '{}',
    perfil_whatsapp JSONB DEFAULT '{}',
    perfil_web JSONB DEFAULT '{}',
    perfil_facebook JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Un solo registro de identidad por tenant
    CONSTRAINT uq_voz_identidad_tenant UNIQUE (tenant_id)
);

-- ── 2. IRC por canal (B2.8 §4.2 — Eje 1 del Motor) ────────
-- Se recalcula semanalmente con 6 factores
CREATE TABLE IF NOT EXISTS om_voz_irc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    canal TEXT NOT NULL,

    -- 6 factores del IRC (B2.8 §4.2)
    demanda_busqueda_local NUMERIC(4,2) DEFAULT 0,
    audiencia_objetivo_presente NUMERIC(4,2) DEFAULT 0,
    tasa_conversion_historica NUMERIC(4,2) DEFAULT 0,
    coste_tiempo_dueno NUMERIC(4,2) DEFAULT 0,
    capacidad_disponible NUMERIC(4,2) DEFAULT 0,
    afinidad_consumo_audiencia NUMERIC(4,2) DEFAULT 0,

    irc_score NUMERIC(4,2) DEFAULT 0,

    -- Pesos (ajustables por madurez del negocio)
    pesos JSONB DEFAULT '{"w1":0.2,"w2":0.2,"w3":0.2,"w4":0.1,"w5":0.1,"w6":0.2}',

    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Un IRC por canal por tenant
    CONSTRAINT uq_voz_irc_canal UNIQUE (tenant_id, canal)
);

CREATE INDEX IF NOT EXISTS idx_voz_irc_activo
    ON om_voz_irc(tenant_id, activo) WHERE activo = TRUE;

-- ── 3. PCA — Perfil de Consumo de Audiencia (B2.8 §4.4) ────
CREATE TABLE IF NOT EXISTS om_voz_pca (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    segmento TEXT NOT NULL,

    -- Dimensiones del PCA
    formato_preferido JSONB DEFAULT '[]',
    tono_que_resuena TEXT,
    temas_que_enganchan JSONB DEFAULT '[]',
    temas_que_no JSONB DEFAULT '[]',
    cuentas_referencia JSONB DEFAULT '[]',
    lenguaje_real JSONB DEFAULT '[]',
    horarios_consumo JSONB DEFAULT '{}',
    canal_interaccion_profunda TEXT,

    -- Fuentes de datos
    fuentes JSONB DEFAULT '[]',

    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Un PCA por segmento por tenant
    CONSTRAINT uq_voz_pca_segmento UNIQUE (tenant_id, segmento)
);

-- ── 4. Estrategia activa de comunicación (B2.8 §3.1) ───────
-- Derivada del cruce: Identidad × ACD × IRC × PCA × Estacionalidad
CREATE TABLE IF NOT EXISTS om_voz_estrategia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',

    -- Inputs
    estado_acd TEXT CHECK (estado_acd IN (
        'E1', 'E2', 'E3', 'E4',
        'operador_ciego', 'genio_mortal', 'automata_eterno',
        'piloto_sin_mapa', 'hiperactivo_fragil', 'equilibrio_esteril'
    )),
    lentes JSONB DEFAULT '{}',
    contexto_mercado TEXT,
    contexto_estacional TEXT,
    ocupacion_pct NUMERIC(5,2),
    irc_snapshot JSONB DEFAULT '{}',
    pca_snapshot JSONB DEFAULT '{}',

    -- Outputs (lo que genera el motor estratégico)
    foco_principal TEXT CHECK (foco_principal IN (
        'educar', 'captar', 'retener', 'fidelizar', 'activar', 'depurar'
    )),
    foco_secundario TEXT,
    narrativa TEXT,
    canales_prioridad JSONB DEFAULT '[]',
    tipos_contenido_prioridad JSONB DEFAULT '[]',
    frecuencia_recomendada JSONB DEFAULT '{}',
    evitar JSONB DEFAULT '[]',
    prescripciones JSONB DEFAULT '[]',

    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_voz_estrategia_activa
    ON om_voz_estrategia(tenant_id, activa) WHERE activa = TRUE;

-- ── 5. Plantillas de perfiles (Arquitecto de Presencia §3.2) ─
CREATE TABLE IF NOT EXISTS om_voz_perfil_plantilla (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    canal TEXT NOT NULL,
    tipo TEXT NOT NULL,
    contenido TEXT NOT NULL,
    instrucciones TEXT,
    posicion_matricial TEXT,
    estado TEXT DEFAULT 'borrador'
        CHECK (estado IN ('borrador', 'aprobado', 'aplicado')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── 6. Telemetría por canal (ciclo APRENDER de B2.8) ────────
CREATE TABLE IF NOT EXISTS om_voz_telemetria_canal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    canal TEXT NOT NULL,
    periodo TEXT NOT NULL,

    -- Métricas de negocio (NO vanidad)
    leads_generados INTEGER DEFAULT 0,
    reservas_directas INTEGER DEFAULT 0,
    conversiones_cliente INTEGER DEFAULT 0,
    mensajes_respondidos INTEGER DEFAULT 0,
    tasa_respuesta NUMERIC(5,2),
    tasa_apertura NUMERIC(5,2),
    resenas_recibidas INTEGER DEFAULT 0,
    resenas_respondidas INTEGER DEFAULT 0,

    -- Métricas de contenido (para calibrar PCA)
    contenido_publicado INTEGER DEFAULT 0,
    mejor_formato TEXT,
    mejor_tema TEXT,
    engagement_medio NUMERIC(5,2),

    -- Atribución
    primer_contacto_pct NUMERIC(5,2),

    created_at TIMESTAMPTZ DEFAULT now(),

    -- Un registro por canal por periodo
    CONSTRAINT uq_telemetria_canal_periodo UNIQUE (tenant_id, canal, periodo)
);

CREATE INDEX IF NOT EXISTS idx_telemetria_canal
    ON om_voz_telemetria_canal(tenant_id, canal, periodo);

-- ── 7. Inteligencia de competidores (Outscraper data) ───────
-- NUEVO: Estructura para almacenar datos de competencia local
-- de forma consultable, no solo como JSONB opaco en capa_a
CREATE TABLE IF NOT EXISTS om_voz_competidor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    nombre TEXT NOT NULL,
    plataforma TEXT NOT NULL DEFAULT 'google_maps',
    place_id TEXT,

    -- Datos del competidor
    puntuacion NUMERIC(3,2),
    total_resenas INTEGER DEFAULT 0,
    categorias JSONB DEFAULT '[]',
    servicios JSONB DEFAULT '[]',
    precio_rango TEXT,
    horarios JSONB DEFAULT '{}',
    atributos JSONB DEFAULT '[]',

    -- Análisis cualitativo (generado por LLM sobre reseñas)
    fortalezas JSONB DEFAULT '[]',
    debilidades JSONB DEFAULT '[]',
    quejas_frecuentes JSONB DEFAULT '[]',
    lo_que_valoran JSONB DEFAULT '[]',
    oportunidad_para_nosotros TEXT,

    -- Fuente y frescura
    fuente TEXT DEFAULT 'outscraper',
    fecha_ultima_actualizacion DATE,
    activo BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_competidor UNIQUE (tenant_id, nombre, plataforma)
);

-- ── 8. Señales detectadas (ciclo ESCUCHAR de B2.8) ─────────
CREATE TABLE IF NOT EXISTS om_voz_senales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    origen TEXT NOT NULL,
    capa TEXT NOT NULL CHECK (capa IN ('A', 'B', 'C')),
    urgencia TEXT DEFAULT 'baja'
        CHECK (urgencia IN ('baja', 'media', 'alta', 'critica')),
    contenido JSONB NOT NULL,
    procesada BOOLEAN DEFAULT FALSE,
    -- Referencia a propuesta generada (si se convirtió en propuesta)
    -- FK semántica: om_voz_propuestas.id (creada en B-PIL-01/15)
    propuesta_generada_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_senales_pendientes
    ON om_voz_senales(tenant_id, procesada) WHERE procesada = FALSE;

-- ── 9. Extender om_voz_isp con campos estratégicos ─────────
ALTER TABLE om_voz_isp ADD COLUMN IF NOT EXISTS elementos_evaluados JSONB DEFAULT '[]';
ALTER TABLE om_voz_isp ADD COLUMN IF NOT EXISTS acciones_generadas JSONB DEFAULT '[]';
ALTER TABLE om_voz_isp ADD COLUMN IF NOT EXISTS posicion_matricial TEXT;
ALTER TABLE om_voz_isp ADD COLUMN IF NOT EXISTS automatico BOOLEAN DEFAULT FALSE;

-- ── 10. Calendario de contenido (planificación semanal) ─────
-- NUEVO: El Motor Tridimensional genera un plan semanal.
-- Cada fila = 1 pieza de contenido planificada.
CREATE TABLE IF NOT EXISTS om_voz_calendario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',

    -- Planificación
    semana TEXT NOT NULL,             -- "2026-W13"
    canal TEXT NOT NULL,
    tipo_contenido TEXT NOT NULL,     -- "carrusel", "broadcast_wa", "post_google", "estado_wa", "respuesta_resena"
    dia_publicacion DATE,
    hora_publicacion TIME,

    -- Contenido (puede estar vacío si es solo plan)
    titulo TEXT,
    contenido TEXT,
    visual_sugerido TEXT,
    cta TEXT,

    -- Justificación (los 3 ejes)
    eje1_irc NUMERIC(4,2),
    eje2_posicion TEXT,               -- "salud_potenciar", "sentido_conservar", etc.
    eje3_formato_pca TEXT,            -- por qué este formato
    justificacion TEXT,               -- texto libre con el porqué cruzado

    -- Estado
    estado TEXT DEFAULT 'planificado'
        CHECK (estado IN ('planificado', 'aprobado', 'publicado', 'descartado')),
    aprobado_por TEXT,
    publicado_at TIMESTAMPTZ,

    -- Resultado (retroalimentación)
    resultado JSONB DEFAULT '{}',     -- métricas post-publicación

    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_calendario_semana
    ON om_voz_calendario(tenant_id, semana, estado);

COMMIT;
```

## FASE A2: Seed Identidad Authentic Pilates

**Archivo:** Crear `src/pilates/voz_identidad.py`

```python
"""Voz Identidad — Capa 1 del Bloque Voz Estratégico.

Gestiona la identidad de comunicación del tenant:
quién eres, a quién hablas, cómo hablas, qué nunca dices.

Basado en B2.8 v3.0 — Bloque Voz: Presencia Inteligente.
"""
from __future__ import annotations
import json, structlog
from datetime import date

log = structlog.get_logger()
TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# SEED — Identidad
# ============================================================

async def seed_identidad() -> dict:
    """Seed completo de la identidad de Authentic Pilates.

    Basado en B2.8 §2 — Triple Capa de Inteligencia, Capa 1.
    Incluye: estudio, target (3 niveles), mercado, filosofía.

    Idempotente: ON CONFLICT DO NOTHING.
    """
    pool = await _get_pool()

    # Preparar datos como dict para claridad y mantenibilidad
    data = {
        "tenant_id": TENANT,
        "nombre_estudio": "Authentic Pilates",
        "ubicacion": "Albelda de Iregua, La Rioja",
        "ubicacion_contexto": (
            "Pueblo de ~1.000 hab a 8km de Logroño. "
            "Zona rural bien conectada. Aquí nos conocemos todos."
        ),
        "metodo_escuela": "EEDAP de Fabien Menegon — Escuela de Educación del Authentic Pilates",
        "propuesta_valor": (
            "Pilates auténtico con atención real. No somos un gimnasio. "
            "Cada sesión es única porque cada persona es única."
        ),
        "diferenciadores": [
            "Grupos reducidos: máximo 4-6 personas",
            "Instructor formado en el método original (EEDAP)",
            "Reformer, mat, accesorios — todo el repertorio auténtico",
            "Cada sesión adaptada: lesiones, cuerpo, momento",
            "No es ejercicio por ejercicio: es un sistema completo de movimiento",
            "Trabajo profundo: postura, respiración, consciencia corporal",
        ],
        "tono": "Cercano, de pueblo, sin formalismos. Como hablar con un vecino.",
        "personalidad": (
            "Hablamos como en Albelda: directo, cercano, sin palabras raras. "
            "Tuteamos siempre. No somos una empresa, somos Jesús que tiene un "
            "estudio y le apasiona lo que hace. Usamos 'nosotros' como comunidad, "
            "no como corporación. Si algo es bueno lo decimos con entusiasmo "
            "natural, no con marketing. Nunca forzamos, nunca presionamos. "
            "La curiosidad hace el trabajo."
        ),
        "target_primario": {
            "perfil": "Mujeres 35-60 años",
            "zona": "Albelda + pueblos cercanos (Nalda, Viguera, Islallana) + Logroño",
            "motivacion": "Dolencias de espalda, postura, bienestar general, recomendación médica/fisio",
            "freno": "No saben qué es Pilates real, creen que no es para ellas",
        },
        "target_secundario": {
            "perfil": "Hombres 40-65 con lesiones",
            "motivacion": "Derivados por fisioterapeuta o médico",
            "freno": "Creen que es 'cosa de mujeres'",
        },
        "target_terciario": {
            "perfil": "Jóvenes 25-35 que buscan algo diferente",
            "motivacion": "Hartos del gimnasio, buscan algo con más sentido",
            "freno": "No saben que existe, creen que Pilates es aburrido",
        },
        "nivel_conocimiento": "muy_bajo",
        "confusiones_comunes": [
            "Es como yoga", "Es estiramientos", "Es para señoras mayores",
            "Es cosa de mujeres", "Es como en el gimnasio pero más tranquilo",
            "Es solo para gente flexible",
        ],
        "competencia_percibida": [
            "Gimnasios con 'clases de Pilates' de 20 personas (no es Pilates real)",
            "Franquicias low-cost tipo Reformer Box (volumen, no calidad)",
            "Fisioterapeutas que ofrecen 'ejercicios de Pilates'",
        ],
        "barreras_entrada": [
            "No sé si es para mí", "Me da vergüenza, no estoy en forma",
            "Es caro (sin saber el valor)", "No tengo tiempo",
            "Ya hago ejercicio en el gimnasio",
            "No sé la diferencia con lo que ofrecen en el gym",
        ],
        "principios_comunicacion": [
            "Educar ANTES de vender — si no saben qué es, no pueden querer venir",
            "Nunca comparar con gimnasios — posicionar en categoría propia",
            "Mostrar transformación real, no ejercicios bonitos",
            "Comunicar profundidad sin asustar — accesible pero serio",
            "Persuadir por curiosidad, no por presión",
            "Testimonios y resultados > características técnicas",
            "El método tiene historia y fundamento — usar como autoridad",
            "Cada persona es una historia — personalizar siempre que se pueda",
        ],
        "lo_que_nunca_decir": [
            "Nunca comparar directamente con gimnasios",
            "Nunca usar lenguaje fitness (quemar, definir, tonificar, cardio)",
            "Nunca dar precios en redes — invitar a probar primero",
            "Nunca dar horarios en redes — que contacten",
            "Nunca stock photos — solo fotos reales del estudio",
            "Nunca prometer resultados milagrosos",
            "Nunca hablar mal de otras disciplinas",
        ],
        "palabras_clave": [
            "transformación", "profundidad", "cuidado", "atención",
            "movimiento", "consciencia", "equilibrio", "bienestar",
            "personalizado", "auténtico", "método original", "Joseph Pilates",
        ],
        "palabras_prohibidas": [
            "fitness", "quemar calorías", "ponerse en forma", "definir",
            "cardio", "entrenamiento", "rutina", "repeticiones",
            "gym", "gimnasio", "low cost", "oferta", "descuento",
        ],
    }

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_voz_identidad (
                tenant_id, nombre_estudio, ubicacion, ubicacion_contexto,
                metodo_escuela, propuesta_valor, diferenciadores, tono, personalidad,
                target_primario, target_secundario, target_terciario,
                nivel_conocimiento, confusiones_comunes, competencia_percibida,
                barreras_entrada, principios_comunicacion, lo_que_nunca_decir,
                palabras_clave, palabras_prohibidas
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9,
                $10::jsonb, $11::jsonb, $12::jsonb,
                $13, $14::jsonb, $15::jsonb, $16::jsonb,
                $17::jsonb, $18::jsonb, $19::jsonb, $20::jsonb
            )
            ON CONFLICT ON CONSTRAINT uq_voz_identidad_tenant DO NOTHING
        """,
            data["tenant_id"],             # $1
            data["nombre_estudio"],        # $2
            data["ubicacion"],             # $3
            data["ubicacion_contexto"],    # $4
            data["metodo_escuela"],        # $5
            data["propuesta_valor"],       # $6
            json.dumps(data["diferenciadores"]),       # $7
            data["tono"],                  # $8
            data["personalidad"],          # $9
            json.dumps(data["target_primario"]),        # $10
            json.dumps(data["target_secundario"]),      # $11
            json.dumps(data["target_terciario"]),       # $12
            data["nivel_conocimiento"],    # $13
            json.dumps(data["confusiones_comunes"]),    # $14
            json.dumps(data["competencia_percibida"]),  # $15
            json.dumps(data["barreras_entrada"]),       # $16
            json.dumps(data["principios_comunicacion"]),# $17
            json.dumps(data["lo_que_nunca_decir"]),     # $18
            json.dumps(data["palabras_clave"]),         # $19
            json.dumps(data["palabras_prohibidas"]),    # $20
        )

    log.info("voz_identidad_seed_ok")
    return {"status": "ok"}


# ============================================================
# SEED — IRC
# ============================================================

async def seed_irc_inicial() -> dict:
    """Seed IRC inicial para Authentic Pilates.

    Basado en B2.8 §4.2 — ejemplo concreto.
    Valores estimados a falta de datos históricos (mes 0).

    Idempotente: ON CONFLICT DO NOTHING.
    """
    pool = await _get_pool()

    canales = [
        {
            "canal": "whatsapp",
            # demanda 0.8: canal dominante en España para SMBs
            # audiencia 0.9: el 90%+ de clientas actuales usa WA
            # conversion 0.8: ~80% de reservas llegan por WA (estimación Jesús)
            # coste 0.8: bajo esfuerzo relativo (ya lo usa a diario)
            # capacidad 0.6: hay huecos pero no ilimitados (~66 plazas, ~50 ocupadas)
            # afinidad 0.9: canal #1 de interacción profunda para mujeres 35-60 en España
            "demanda": 0.8, "audiencia": 0.9, "conversion": 0.8,
            "coste": 0.8, "capacidad": 0.6, "afinidad": 0.9,
        },
        {
            "canal": "google_business",
            # demanda 0.9: "pilates logroño/albelda" tiene búsquedas reales
            # audiencia 0.8: mujeres 35-60 buscan en Google antes de WA
            # conversion 0.7: ficha genera llamadas/rutas pero no se mide bien aún
            # coste 0.9: casi cero esfuerzo de mantenimiento una vez optimizado
            # capacidad 0.6: misma capacidad que en todos los canales
            # afinidad 0.7: buscan info pero no "consumen contenido" en Google
            "demanda": 0.9, "audiencia": 0.8, "conversion": 0.7,
            "coste": 0.9, "capacidad": 0.6, "afinidad": 0.7,
        },
        {
            "canal": "instagram",
            # demanda 0.5: la gente no busca pilates en IG, lo descubre
            # audiencia 0.6: presente pero pasiva para nuestro perfil
            # conversion 0.3: nunca ha generado una reserva directa medible
            # coste 0.3: alto esfuerzo (crear contenido visual, constancia)
            # capacidad 0.6: misma
            # afinidad 0.5: miran stories pero no interactúan con profundidad
            "demanda": 0.5, "audiencia": 0.6, "conversion": 0.3,
            "coste": 0.3, "capacidad": 0.6, "afinidad": 0.5,
        },
        {
            "canal": "facebook",
            # demanda 0.3: bajo para este sector
            # audiencia 0.5: presente pero decreciendo en relevancia
            # conversion 0.2: casi nula
            # coste 0.5: medio (se puede crosspostar con IG)
            # capacidad 0.6: misma
            # afinidad 0.4: audiencia 50+ aún consume contenido aquí
            "demanda": 0.3, "audiencia": 0.5, "conversion": 0.2,
            "coste": 0.5, "capacidad": 0.6, "afinidad": 0.4,
        },
        {
            "canal": "web",
            # demanda 0.4: la web existe pero no genera tráfico propio
            # audiencia 0.3: muy pocos visitan directamente
            # conversion 0.1: casi todo se redirige a WA de todas formas
            # coste 0.7: bajo si es estática, se mantiene sola
            # capacidad 0.6: misma
            # afinidad 0.3: nadie "consume contenido" en webs de estudios pequeños
            "demanda": 0.4, "audiencia": 0.3, "conversion": 0.1,
            "coste": 0.7, "capacidad": 0.6, "afinidad": 0.3,
        },
    ]

    pesos = {"w1": 0.2, "w2": 0.2, "w3": 0.2, "w4": 0.1, "w5": 0.1, "w6": 0.2}

    async with pool.acquire() as conn:
        for c in canales:
            irc = (
                pesos["w1"] * c["demanda"] +
                pesos["w2"] * c["audiencia"] +
                pesos["w3"] * c["conversion"] +
                pesos["w4"] * c["coste"] +
                pesos["w5"] * c["capacidad"] +
                pesos["w6"] * c["afinidad"]
            )
            await conn.execute("""
                INSERT INTO om_voz_irc (tenant_id, canal,
                    demanda_busqueda_local, audiencia_objetivo_presente,
                    tasa_conversion_historica, coste_tiempo_dueno,
                    capacidad_disponible, afinidad_consumo_audiencia,
                    irc_score, pesos)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb)
                ON CONFLICT ON CONSTRAINT uq_voz_irc_canal DO NOTHING
            """, TENANT, c["canal"],
                c["demanda"], c["audiencia"], c["conversion"],
                c["coste"], c["capacidad"], c["afinidad"],
                round(irc, 2), json.dumps(pesos))

    log.info("voz_irc_seed_ok")
    return {"status": "ok", "canales": len(canales)}


# ============================================================
# SEED — PCA
# ============================================================

async def seed_pca_inicial() -> dict:
    """Seed PCA inicial — Perfil de Consumo de Audiencia.

    Basado en B2.8 §4.4. Valores estimados para zona Rioja.
    Se refina con datos reales en los primeros 3 meses (ciclo APRENDER).

    Idempotente: ON CONFLICT DO NOTHING.
    """
    pool = await _get_pool()

    segmentos = [
        {
            "segmento": "mujeres_35_60",
            "formato_preferido": [
                "carrusel_educativo",
                "texto_corto_wa_con_pregunta",
                "ficha_google_completa",
            ],
            "tono_que_resuena": "Calmado, experto, cercano. NO motivacional-fitness.",
            "temas_que_enganchan": [
                "dolor de espalda", "estrés", "sueño",
                "menopausia", "bienestar integral", "postura",
            ],
            "temas_que_no": [
                "estética", "pérdida de peso", "cuerpo de verano", "tonificar",
            ],
            "cuentas_referencia": [
                "cuentas de bienestar integral",
                "podcasts salud femenina",
                "blogs fisioterapia",
            ],
            "lenguaje_real": [
                "me duele la espalda",
                "necesito desconectar",
                "algo suave pero que sirva",
                "no estoy en forma",
            ],
            "horarios_consumo": {
                "whatsapp": "8:30-9:00 y 21:00-22:00",
                "instagram": "13:00-14:00 y 21:00-22:30",
                "google": "domingos noche",
            },
            "canal_interaccion_profunda": "whatsapp",
            "fuentes": [
                "estimacion_sector",
                "meta_insights_general",
                "wa_conversaciones_piloto",
            ],
        },
        {
            "segmento": "hombres_40_65_lesiones",
            "formato_preferido": ["texto_wa_directo", "ficha_google"],
            "tono_que_resuena": "Directo, técnico pero accesible. Sin adornos.",
            "temas_que_enganchan": [
                "rehabilitación", "lesión espalda", "movilidad",
                "recomendación fisio",
            ],
            "temas_que_no": ["mindfulness", "emocional", "comunidad"],
            "cuentas_referencia": [
                "fisioterapeutas", "traumatólogos divulgativos",
            ],
            "lenguaje_real": [
                "me lo ha dicho el fisio",
                "tengo hernia",
                "necesito algo para la espalda",
            ],
            "horarios_consumo": {
                "whatsapp": "19:00-20:00",
                "google": "laborables mediodía",
            },
            "canal_interaccion_profunda": "whatsapp",
            "fuentes": ["estimacion_sector"],
        },
        {
            "segmento": "jovenes_25_35",
            "formato_preferido": [
                "reels_cortos", "stories_behind_scenes", "texto_wa",
            ],
            "tono_que_resuena": "Auténtico, sin postureo. Que se note que es real.",
            "temas_que_enganchan": [
                "alternativa al gym", "algo diferente",
                "salud mental", "consciencia corporal",
            ],
            "temas_que_no": ["fitness agresivo", "resultados rápidos"],
            "cuentas_referencia": [
                "cuentas wellness", "yoga moderno", "salud mental",
            ],
            "lenguaje_real": [
                "estoy harto del gym",
                "quiero algo con más sentido",
                "¿qué es exactamente?",
            ],
            "horarios_consumo": {
                "instagram": "22:00-23:30",
                "whatsapp": "todo el día",
            },
            "canal_interaccion_profunda": "instagram",
            "fuentes": ["estimacion_sector"],
        },
    ]

    async with pool.acquire() as conn:
        for s in segmentos:
            await conn.execute("""
                INSERT INTO om_voz_pca (tenant_id, segmento,
                    formato_preferido, tono_que_resuena, temas_que_enganchan,
                    temas_que_no, cuentas_referencia, lenguaje_real,
                    horarios_consumo, canal_interaccion_profunda, fuentes)
                VALUES ($1,$2,$3::jsonb,$4,$5::jsonb,$6::jsonb,$7::jsonb,
                    $8::jsonb,$9::jsonb,$10,$11::jsonb)
                ON CONFLICT ON CONSTRAINT uq_voz_pca_segmento DO NOTHING
            """, TENANT, s["segmento"],
                json.dumps(s["formato_preferido"]),
                s["tono_que_resuena"],
                json.dumps(s["temas_que_enganchan"]),
                json.dumps(s["temas_que_no"]),
                json.dumps(s["cuentas_referencia"]),
                json.dumps(s["lenguaje_real"]),
                json.dumps(s["horarios_consumo"]),
                s["canal_interaccion_profunda"],
                json.dumps(s["fuentes"]),
            )

    log.info("voz_pca_seed_ok", segmentos=len(segmentos))
    return {"status": "ok", "segmentos": len(segmentos)}


# ============================================================
# SEED — Competidores iniciales (Outscraper data)
# ============================================================

async def seed_competidores() -> dict:
    """Seed de competidores conocidos en la zona de Logroño/La Rioja.

    Datos estimados. Se actualizan con Outscraper cuando se conecte.
    """
    pool = await _get_pool()

    competidores = [
        {
            "nombre": "Gimnasio con clases de Pilates tipo 1",
            "categorias": ["gimnasio", "fitness"],
            "fortalezas": ["precio bajo", "muchos horarios", "ubicación centro"],
            "debilidades": ["grupos de 20+", "instructores no especializados", "rotación de personal"],
            "quejas_frecuentes": ["masificado", "poca atención individual", "ruido"],
            "lo_que_valoran": ["precio", "horarios flexibles", "parking"],
            "oportunidad_para_nosotros": (
                "Sus clientes que buscan atención personalizada están desatendidos. "
                "Nuestro diferencial de grupos reducidos (4-6) es exactamente lo que les falta."
            ),
        },
        {
            "nombre": "Franquicia Reformer low-cost",
            "categorias": ["pilates", "reformer"],
            "fortalezas": ["marketing profesional", "instalaciones nuevas", "marca conocida"],
            "debilidades": ["método no auténtico", "volumen sobre calidad", "instructores junior"],
            "quejas_frecuentes": ["no personalizado", "se siente fábrica", "lesiones por mala supervisión"],
            "lo_que_valoran": ["estética del espacio", "moda/tendencia", "redes sociales"],
            "oportunidad_para_nosotros": (
                "Captar a quienes se lesionan o decepcionan por la falta de profundidad. "
                "Nuestro método EEDAP y atención real es la respuesta directa a sus quejas."
            ),
        },
    ]

    async with pool.acquire() as conn:
        for c in competidores:
            await conn.execute("""
                INSERT INTO om_voz_competidor (
                    tenant_id, nombre, categorias, fortalezas, debilidades,
                    quejas_frecuentes, lo_que_valoran, oportunidad_para_nosotros,
                    fuente, fecha_ultima_actualizacion
                ) VALUES ($1,$2,$3::jsonb,$4::jsonb,$5::jsonb,
                    $6::jsonb,$7::jsonb,$8,$9,$10)
                ON CONFLICT ON CONSTRAINT uq_competidor DO NOTHING
            """, TENANT, c["nombre"],
                json.dumps(c["categorias"]),
                json.dumps(c["fortalezas"]),
                json.dumps(c["debilidades"]),
                json.dumps(c["quejas_frecuentes"]),
                json.dumps(c["lo_que_valoran"]),
                c["oportunidad_para_nosotros"],
                "estimacion_manual",
                date.today(),
            )

    log.info("voz_competidores_seed_ok")
    return {"status": "ok", "competidores": len(competidores)}


# ============================================================
# CONSULTAS
# ============================================================

async def obtener_identidad() -> dict:
    """Devuelve la identidad completa del tenant."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_voz_identidad WHERE tenant_id=$1", TENANT)
        if not row:
            return {"error": "Identidad no configurada. Ejecutar seed."}
        return dict(row)


async def obtener_irc() -> list[dict]:
    """Devuelve IRC de todos los canales, ordenado por score."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_voz_irc
            WHERE tenant_id=$1 AND activo=true
            ORDER BY irc_score DESC
        """, TENANT)
    return [dict(r) for r in rows]


async def obtener_pca(segmento: str = None) -> list[dict]:
    """Devuelve PCA de todos los segmentos o uno específico."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if segmento:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_pca
                WHERE tenant_id=$1 AND segmento=$2 AND activo=true
            """, TENANT, segmento)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_pca
                WHERE tenant_id=$1 AND activo=true
            """, TENANT)
    return [dict(r) for r in rows]


async def obtener_competidores() -> list[dict]:
    """Devuelve competidores activos."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_voz_competidor
            WHERE tenant_id=$1 AND activo=true
            ORDER BY puntuacion DESC NULLS LAST
        """, TENANT)
    return [dict(r) for r in rows]


# ============================================================
# DIAGNÓSTICO INICIAL — Arquitecto de Presencia
# ============================================================

async def diagnosticar_presencia() -> dict:
    """Genera un diagnóstico cruzado de la presencia digital.

    Cruza: Identidad × IRC × PCA × Competidores para producir
    un informe accionable de qué canales priorizar y qué cambiar.

    Es el output principal de 20a — la base sobre la que
    20b construirá el Motor Tridimensional.
    """
    identidad = await obtener_identidad()
    if "error" in identidad:
        return identidad

    irc = await obtener_irc()
    pca = await obtener_pca()
    competidores = await obtener_competidores()

    # Canal prioritario por IRC
    canal_top = irc[0]["canal"] if irc else "desconocido"
    canal_top_score = irc[0]["irc_score"] if irc else 0

    # Canal con peor ROI de esfuerzo (más coste, menos conversión)
    canal_peor_roi = None
    peor_ratio = float("inf")
    for c in irc:
        if c["tasa_conversion_historica"] > 0:
            ratio = float(c["coste_tiempo_dueno"]) / float(c["tasa_conversion_historica"])
        else:
            ratio = float("inf") if float(c["coste_tiempo_dueno"]) > 0.3 else 0
        if 0 < ratio < peor_ratio and c["canal"] != canal_top:
            peor_ratio = ratio
            canal_peor_roi = c["canal"]

    # Segmento principal
    seg_principal = pca[0] if pca else {}

    # Oportunidades de competidores
    oportunidades = [
        c["oportunidad_para_nosotros"]
        for c in competidores
        if c.get("oportunidad_para_nosotros")
    ]

    diagnostico = {
        "resumen": {
            "canal_prioritario": canal_top,
            "canal_prioritario_score": canal_top_score,
            "canal_a_reducir": canal_peor_roi,
            "segmento_principal": seg_principal.get("segmento", "desconocido"),
            "tono_recomendado": seg_principal.get("tono_que_resuena", ""),
            "formato_recomendado": seg_principal.get("formato_preferido", []),
        },
        "acciones_inmediatas": [],
        "oportunidades_competencia": oportunidades,
        "datos_base": {
            "identidad_ok": "error" not in identidad,
            "canales_irc": len(irc),
            "segmentos_pca": len(pca),
            "competidores": len(competidores),
        },
    }

    # Generar acciones inmediatas
    if canal_top == "whatsapp":
        diagnostico["acciones_inmediatas"].append(
            "Configurar WhatsApp Business: catálogo, mensaje bienvenida, respuestas rápidas"
        )
    if canal_peor_roi:
        diagnostico["acciones_inmediatas"].append(
            f"Reducir esfuerzo en {canal_peor_roi} — baja conversión vs alto coste de tiempo"
        )
    if seg_principal.get("temas_que_enganchan"):
        temas = ", ".join(seg_principal["temas_que_enganchan"][:3])
        diagnostico["acciones_inmediatas"].append(
            f"Centrar contenido en: {temas} (temas que enganchan a tu audiencia principal)"
        )

    return diagnostico
```

## FASE A3: Endpoints

**Archivo:** `src/pilates/router.py` — AÑADIR al final, dentro del router existente.

Las rutas van bajo el prefijo `/pilates/` que ya tiene el router.
Las rutas completas serán `/pilates/voz/identidad/seed`, etc.

```python
# ============================================================
# VOZ ESTRATÉGICO — Identidad + IRC + PCA + Diagnóstico
# B-PIL-20a
# ============================================================

@router.post("/voz/seed")
async def seed_voz_completo():
    """Seed completo: identidad + IRC + PCA + competidores.
    Idempotente — se puede ejecutar múltiples veces sin duplicar datos.
    """
    from src.pilates.voz_identidad import (
        seed_identidad, seed_irc_inicial,
        seed_pca_inicial, seed_competidores,
    )
    r1 = await seed_identidad()
    r2 = await seed_irc_inicial()
    r3 = await seed_pca_inicial()
    r4 = await seed_competidores()
    return {"identidad": r1, "irc": r2, "pca": r3, "competidores": r4}

@router.get("/voz/identidad")
async def get_identidad():
    from src.pilates.voz_identidad import obtener_identidad
    return await obtener_identidad()

@router.get("/voz/irc")
async def get_irc():
    from src.pilates.voz_identidad import obtener_irc
    return await obtener_irc()

@router.get("/voz/pca")
async def get_pca(segmento: Optional[str] = None):
    from src.pilates.voz_identidad import obtener_pca
    return await obtener_pca(segmento)

@router.get("/voz/competidores")
async def get_competidores():
    from src.pilates.voz_identidad import obtener_competidores
    return await obtener_competidores()

@router.get("/voz/diagnostico")
async def get_diagnostico():
    """Diagnóstico cruzado de presencia digital.
    Cruza Identidad × IRC × PCA × Competidores.
    """
    from src.pilates.voz_identidad import diagnosticar_presencia
    return await diagnosticar_presencia()
```

## VERIFICACIÓN

```bash
# ── V1. Migración ────────────────────────────────────────────
psql $DATABASE_URL -f migrations/017_voz_estrategico.sql
# PASS: "COMMIT" sin errores
# PASS: \dt om_voz_* muestra 8+ tablas nuevas

# ── V2. Seed (primera vez) ───────────────────────────────────
curl -X POST .../pilates/voz/seed
# PASS: identidad.status="ok", irc.canales=5, pca.segmentos=3, competidores.status="ok"

# ── V3. Seed (segunda vez — idempotencia) ────────────────────
curl -X POST .../pilates/voz/seed
# PASS: misma respuesta, sin errores, sin datos duplicados
# PASS: SELECT count(*) FROM om_voz_identidad = 1
# PASS: SELECT count(*) FROM om_voz_irc = 5
# PASS: SELECT count(*) FROM om_voz_pca = 3

# ── V4. Leer identidad ──────────────────────────────────────
curl .../pilates/voz/identidad
# PASS: nombre_estudio="Authentic Pilates"
# PASS: target_primario contiene perfil, zona, motivacion, freno
# PASS: palabras_prohibidas contiene "fitness", "gym"

# ── V5. Leer IRC ────────────────────────────────────────────
curl .../pilates/voz/irc
# PASS: 5 canales, ordenados por irc_score DESC
# PASS: whatsapp primero (score ~0.82)
# PASS: web último (score ~0.38)

# ── V6. Leer PCA ────────────────────────────────────────────
curl .../pilates/voz/pca
# PASS: 3 segmentos con formato_preferido, temas, horarios, lenguaje_real

# ── V7. Leer PCA filtrado ───────────────────────────────────
curl ".../pilates/voz/pca?segmento=mujeres_35_60"
# PASS: 1 segmento, canal_interaccion_profunda = "whatsapp"

# ── V8. Leer competidores ───────────────────────────────────
curl .../pilates/voz/competidores
# PASS: 2 competidores con fortalezas, debilidades, oportunidad_para_nosotros

# ── V9. Diagnóstico cruzado ─────────────────────────────────
curl .../pilates/voz/diagnostico
# PASS: resumen.canal_prioritario = "whatsapp"
# PASS: resumen.canal_a_reducir = canal con peor ROI
# PASS: acciones_inmediatas tiene >= 2 elementos
# PASS: oportunidades_competencia tiene >= 1 elemento
# PASS: datos_base.identidad_ok = true
```

---

## ROADMAP: SUB-BRIEFINGS PENDIENTES

Los siguientes sub-briefings se escribirán como archivos separados
(B-PIL-20b.md, etc.) con código completo, rutas exactas y tests PASS/FAIL
cuando llegue el momento de ejecutarlos. Lo que sigue es solo la descripción
de alto nivel de lo que cubrirá cada uno.

### B-PIL-20b: Motor Tridimensional — STATUS: PENDIENTE

Implementará:
- `calcular_estrategia()` — cruza Identidad × ACD × IRC × PCA × Estacionalidad
- `generar_propuestas_estrategicas()` — genera contenido alineado con los 3 ejes
- Reemplaza el `generar_propuestas()` táctico de B-PIL-15 (`src/pilates/voz.py`)
- System prompt estratégico con los 3 ejes documentados
- Poblar `om_voz_estrategia` y `om_voz_calendario`
- Endpoints: POST /pilates/voz/estrategia/calcular, GET /pilates/voz/estrategia

**Decisión pendiente para 20b:** ¿Cómo se obtiene el estado ACD actual del negocio?
Si viene de la tabla om_acd_diagnosticos (B-ACD) o se calcula ad-hoc.

### B-PIL-20c: Arquitecto de Presencia — STATUS: PENDIENTE

Implementará B2.8 §3.2 completo:
- `generar_perfil_canal(canal)` — genera configuración COMPLETA de perfil
- WhatsApp: descripción, catálogo, mensaje bienvenida, respuestas rápidas, etiquetas
- Google Business: descripción con queries reales, categorías, servicios, fotos, Q&A, posts
- Instagram: bio por posición matricial, highlights por estado, primeros 9 posts, hashtags
- Facebook: acerca de, botón CTA, post fijado
- Todo contextualizado por los 3 ejes del Motor Tridimensional
- Instrucciones paso a paso para lo que no se puede automatizar (bio IG, highlights)
- Poblar `om_voz_perfil_plantilla`
- Endpoints: POST /pilates/voz/perfil/{canal}/generar, GET /pilates/voz/perfil/{canal}

### B-PIL-20d: 5 Ciclos + ISP + Telemetría — STATUS: PENDIENTE

Implementará los 5 ciclos de B2.8 §3.1:
1. ESCUCHAR — detector de señales multi-canal → `om_voz_senales`
2. PRIORIZAR — 4 preguntas del motor de priorización cruzando 3 capas
3. PROPONER — propuestas contextualizadas por Motor Tridimensional
4. EJECUTAR — 3 modos (manual/semi-auto/auto) + Matriz de Automatización
5. APRENDER — telemetría → `om_voz_telemetria_canal` + retroalimentación IRC/PCA

ISP automático (B2.8 §5.4):
- Evaluación periódica de cada perfil contra configuración óptima
- Si cambia posición matricial → ISP recalcula
- Acciones automáticas + tareas asistidas por WA

### B-PIL-20e: Integración cockpit + cron + briefing — STATUS: PENDIENTE

- Tools del cockpit para Voz: "¿cuál es mi estrategia?", "prepárame posts"
- Sección Voz en briefing semanal con los 3 ejes
- Cron semanal: recalcular estrategia + IRC + generar calendario
- Cron diario: escuchar señales + procesar urgentes
- Módulo Voz en EstudioCockpit.jsx

**Decisión técnica pendiente para 20e:** Mecanismo de cron en fly.io.
Opciones: fly machine schedule, APScheduler dentro de FastAPI, cron externo
con curl a endpoints. Decidir antes de escribir el briefing detallado.

---

## NOTAS GENERALES

- **Coste por negocio/mes:** ~€3-10 en APIs externas (Perplexity ~€1, Outscraper ~€3, Open-Meteo/INE/BOE gratis)
- **Las fuentes de Capa A que NO implementamos ahora** (SparkToro, SOPRISM, Meta Ads API, Google Ads) se dejan como stubs con datos estimados. Se conectan cuando haya presupuesto/necesidad.
- **El PCA inicial es estimado.** Se refina con datos reales de WhatsApp + Instagram en los primeros 3 meses (ciclo APRENDER).
- **El IRC inicial es estimado.** Se recalibra semanalmente con datos de telemetría real.
- **La estrategia se recalculará cada lunes** (implementado en 20e).
- **om_voz_competidor es nuevo** — no existía en B-PIL-15. Permite almacenar inteligencia competitiva de forma estructurada (fortalezas, debilidades, oportunidades) en vez de JSONB opaco en capa_a.
- **om_voz_calendario es nuevo** — permite planificar contenido semanal con justificación de los 3 ejes, y medir resultado después de publicar. Cierra el ciclo PROPONER → EJECUTAR → APRENDER.
- **diagnosticar_presencia() es nuevo** — es la primera función que cruza todas las capas para producir un output accionable. Es la base del Motor Tridimensional que construirá 20b.
