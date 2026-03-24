"""Voz Identidad — Capa 1 del Bloque Voz Estratégico.

Gestiona la identidad de comunicación del tenant:
quién eres, a quién hablas, cómo hablas, qué nunca dices.

Basado en B2.8 v3.0 — Bloque Voz: Presencia Inteligente.
"""
from __future__ import annotations
import json, structlog
from datetime import date

log = structlog.get_logger()
from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request


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
            "demanda": 0.8, "audiencia": 0.9, "conversion": 0.8,
            "coste": 0.8, "capacidad": 0.6, "afinidad": 0.9,
        },
        {
            "canal": "google_business",
            "demanda": 0.9, "audiencia": 0.8, "conversion": 0.7,
            "coste": 0.9, "capacidad": 0.6, "afinidad": 0.7,
        },
        {
            "canal": "instagram",
            "demanda": 0.5, "audiencia": 0.6, "conversion": 0.3,
            "coste": 0.3, "capacidad": 0.6, "afinidad": 0.5,
        },
        {
            "canal": "facebook",
            "demanda": 0.3, "audiencia": 0.5, "conversion": 0.2,
            "coste": 0.5, "capacidad": 0.6, "afinidad": 0.4,
        },
        {
            "canal": "web",
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

def _jparse(val):
    """Parse JSONB que puede venir como string o como objeto Python."""
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return val


async def diagnosticar_presencia() -> dict:
    """Genera un diagnóstico cruzado de la presencia digital.

    Cruza: Identidad x IRC x PCA x Competidores para producir
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

    # Parsear JSONB que puede venir como string
    formato_pref = _jparse(seg_principal.get("formato_preferido", []))
    temas_eng = _jparse(seg_principal.get("temas_que_enganchan", []))

    diagnostico = {
        "resumen": {
            "canal_prioritario": canal_top,
            "canal_prioritario_score": canal_top_score,
            "canal_a_reducir": canal_peor_roi,
            "segmento_principal": seg_principal.get("segmento", "desconocido"),
            "tono_recomendado": seg_principal.get("tono_que_resuena", ""),
            "formato_recomendado": formato_pref,
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
    if temas_eng and isinstance(temas_eng, list):
        temas = ", ".join(temas_eng[:3])
        diagnostico["acciones_inmediatas"].append(
            f"Centrar contenido en: {temas} (temas que enganchan a tu audiencia principal)"
        )

    return diagnostico
