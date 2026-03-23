"""Enjambre Cognitivo v2 — Diagnóstico en Nivel 1 (Repertorio INT×P×R).

NO mide lentes/funciones como termómetros independientes.
Diagnostica QUÉ configuración cognitiva INT×P×R tiene el negocio,
detecta disfunciones (IC2-IC6), y DERIVA por qué las lentes/funciones
están donde están.

MODELO CAUSAL 4 NIVELES:
  Nivel 1 (CAUSA):     Repertorio INT×P×R → QUÉ herramientas cognitivas usa el negocio
  Nivel 2 (MECANISMO): Distribución por lente → QUÉ produce ese repertorio
  Nivel 3 (EFECTO):    Perfil S×Se×C → estado diagnóstico
  Nivel 4 (SÍNTOMA):   7F×3L scores observables

La intervención opera en Nivel 1. Los números son SÍNTOMAS, no la causa.

Modelo: claude-sonnet-4.6 via OpenRouter
Frecuencia: semanal (lunes, después del diagnosticador numérico)
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import structlog
import httpx
from datetime import date

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4-6")


# ============================================================
# CONOCIMIENTO INYECTADO — El framework completo que los agentes DEBEN entender
# ============================================================

FRAMEWORK_CAUSAL = """
MODELO CAUSAL DE 4 NIVELES (OMNI-MIND ACD):

Nivel 1 (CAUSA): Repertorio cognitivo INT×P×R
  - QUÉ inteligencias están activas/atrofiadas
  - QUÉ pensamientos usa por defecto
  - QUÉ razonamientos emplea
  La distribución de este repertorio PRODUCE las lentes.

Nivel 2 (MECANISMO): Cada combinación INT×P×R genera preferentemente ciertas lentes
  - INT×P×R de ejecución (INT-01,02,05,07,10,11,16 + P07,P13 + R01,R07,R12) → genera S (Salud)
  - INT×P×R de cuestionamiento (INT-03,04,06,08,09,12,14,15,17,18 + P01-P03,P05,P06,P08,P15 + R02,R03,R05,R08,R10) → genera Se (Sentido)
  - INT×P×R de transferencia (INT-13 + secundarias 02,04,12,16,18 + P09,P12,P13 + R04,R12) → genera C (Continuidad)

Nivel 3 (EFECTO): Perfil de lentes S×Se×C → estado diagnóstico
  - E1 Muerte simétrica (todo <0.20)
  - E2 Latencia (0.20-0.40 equilibrado)
  - E3 Funcionalidad (0.40-0.60 equilibrado)
  - E4 Plenitud (>0.65 equilibrado)
  - 6 desequilibrados: operador_ciego (S↑Se↓C↓), visionario (S↓Se↑C↓), zombi (S↓Se↓C↑), genio_mortal (S↑Se↑C↓), autómata (S↑Se↓C↑), potencial_dormido (S↓Se↑C↑)

Nivel 4 (SÍNTOMA): 7F×3L = 21 scores observables

REGLAS DE DISFUNCIÓN (IC2-IC6):

IC2 MONOPOLIO: Una INT sin complementarias = disfunción.
  INT-01 sola sin INT-17 = formalismo sin sentido (Maginot)
  INT-07 sola sin INT-08 = rentabilidad sin coste humano (Boeing)
  INT-17 sola sin INT-16 = parálisis existencial

IC3 DESACOPLE INT-P: INT procesada con P incompatible = abortamiento.
  INT-17(Existencial) + P07(Convergente) = trivializa la pregunta
  INT-14(Divergente) + P07(Convergente) = cierra antes de explorar
  INT-16(Constructiva) + P08(Metacognición) = piensa sobre construir en vez de construir

IC4 DESACOPLE INT-R: INT con R incompatible = conclusión incorrecta.
  INT-03(Estructural) + R01(Deducción) = nunca descubre identidad real (necesita R03)
  INT-13(Prospectiva) + R01(Deducción) = futuro no se deduce (necesita R06 Contrafactual)
  INT-15(Estética) + R07(Bayesiano) = belleza no se probabiliza (necesita R10)

IC5 PARES COMPLEMENTARIOS P: Pensamientos son funcionales SOLO en pares.
  P06(Divergente) sin P07(Convergente) = generación infinita
  P07(Convergente) sin P06(Divergente) = cierre prematuro
  P05(Primeros principios) sin P04(Diseño) = deconstrucción sin reconstrucción
  P08(Metacognición) sin P11(Encarnado) = recursión infinita

IC6 VALIDACIÓN CRUZADA R: Razonamientos aislados amplifican sesgos.
  R01(Deducción) sola = certeza desde premisas no validadas
  R02(Inducción) sola = generalización sin testear excepciones
  R07(Bayesiano) con priors fijos sin R08(Dialéctico) = echo chamber

IC7 REQUISITO E4: ≥7 INT (3S+3Se+1C) + ≥4 P (P06+P07+P08+1Se) + ≥3 R (1S+R03+1C)

AFINIDAD INTELIGENCIA → LENTE:
  Generan S: INT-01(Lógica), 02(Computacional), 05(Estratégica), 07(Financiera), 10(Cinestésica), 11(Espacial), 16(Constructiva)
  Generan Se: INT-03(Estructural), 04(Ecológica), 06(Política), 08(Social), 09(Lingüística), 12(Narrativa), 14(Divergente), 15(Estética), 17(Existencial), 18(Contemplativa)
  Generan C: INT-13(Prospectiva) + secundarias: 02, 04, 12, 16, 18

AFINIDAD PENSAMIENTO → LENTE:
  Generan S: P07(Convergente), P11(Encarnado), P13(Computacional)
  Generan Se: P01(Lateral), P02(Sistémico), P03(Crítico), P05(Primeros principios), P06(Divergente), P08(Metacognición), P15(Integrativo)
  Generan C: P09(Prospectivo)
  Mixtas: P04(Diseño)=S+Se, P10(Reflexivo)=Se+C, P12(Narrativo)=Se+C, P14(Estratégico)=S+Se

AFINIDAD RAZONAMIENTO → LENTE:
  Generan S: R01(Deducción), R07(Bayesiano), R12(Transductivo)
  Generan Se: R02(Inducción), R03(Abducción), R05(Causal), R08(Dialéctico), R10(Retroductivo)
  Mixtas Se+C: R04(Analogía), R06(Contrafactual), R11(Modal)
  Mixta S+Se: R09(Eliminación)
"""

PERFILES_PATOLOGICOS = """
CONFIGURACIONES INT×P×R DE CADA PERFIL PATOLÓGICO:

OPERADOR CIEGO (S↑ Se↓ C↓):
  Activas: INT-01,02,05,07,16 + P07,P13,P14 + R01,R07,R12
  Ausentes: INT-17,18,03,08 + P08,P05,P03,P01 + R03,R08,R10
  Mecanismo: 100% herramientas de S. INCAPAZ de generar Se. No cuestiona premisas.

VISIONARIO ATRAPADO (S↓ Se↑ C↓):
  Activas: INT-17,03,06,15,14 + P02,P05,P08,P06 + R03,R08,R10,R05
  Ausentes: INT-16,10,02,05 + P07,P11,P13,P04 + R01,R12,R07
  Mecanismo: 100% herramientas de Se. INCAPAZ de ejecutar. Comprende pero no hace.

ZOMBI INMORTAL (S↓ Se↓ C↑):
  Herramientas DEGRADADAS/FOSILIZADAS. INT-13 en modo "seguiremos", P09 sin exploración.
  R04 como "como siempre" en vez de cross-dominio. El Se se evaporó con cada iteración.

GENIO MORTAL (S↑ Se↑ C↓):
  Repertorio RICO pero PRIVADO. Muchas INT, P, R activas. Falta: INT-12(Narrativa),
  INT-13(Prospectiva), P12(Narrativo), R04(Analogía). No puede TRANSFERIR.

AUTÓMATA ETERNO (S↑ Se↓ C↑) — EL MÁS PELIGROSO:
  Activas: INT-01,02,05,07,13(lineal),16 + P07,P09(lineal),P13,P14 + R01,R04(interna),R07(priors fijos),R12
  Ausentes: INT-17,18,08,14 + P08,P05,P01,P03 + R03,R08,R10,R06
  Mecanismo: S↑+C↑ PARECE sano. Pero las herramientas de ALARMA están ausentes.
  No puede DETECTAR su propio error. Amplifica y escala el error.

POTENCIAL DORMIDO (S↓ Se↑ C↑):
  Falta S: INT-10,16,11 + P11,P04,P07 + R01,R12,R07.
  El más simple de resolver: solo necesita HACER. Todo lo demás existe.
"""


# ============================================================
# CONTEXTO DEL NEGOCIO
# ============================================================

async def _contexto_completo() -> dict:
    """Recopila TODOS los datos reales para inyectar en los agentes."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        diag = await conn.fetchrow("""
            SELECT vector_pre, lentes_pre, estado_pre, metricas
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        clientes = await conn.fetch("""
            SELECT c.nombre, c.apellidos, ct.estado, ct.fecha_alta,
                (SELECT MAX(s.fecha) FROM om_asistencias a
                 JOIN om_sesiones s ON s.id=a.sesion_id
                 WHERE a.cliente_id=c.id AND a.estado='asistio') as ultima_asistencia,
                (SELECT co.tipo FROM om_contratos co
                 WHERE co.cliente_id=c.id AND co.estado='activo' LIMIT 1) as tipo_contrato
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id=c.id AND ct.tenant_id=$1
            WHERE ct.estado='activo'
        """, TENANT)

        grupos = await conn.fetch("""
            SELECT g.nombre, g.dias_semana, g.capacidad_max,
                (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocupadas
            FROM om_grupos g WHERE g.tenant_id=$1 AND g.estado='activo'
        """, TENANT)

        señales = await conn.fetch("""
            SELECT origen, tipo, payload, created_at
            FROM om_senales_agentes WHERE tenant_id=$1
            ORDER BY created_at DESC LIMIT 30
        """, TENANT)

        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto),0) FROM om_pagos
            WHERE tenant_id=$1 AND fecha_pago >= date_trunc('month', CURRENT_DATE)
        """, TENANT) or 0

        deuda = await conn.fetchval("""
            SELECT COALESCE(SUM(total),0) FROM om_cargos
            WHERE tenant_id=$1 AND estado='pendiente'
        """, TENANT) or 0

        identidad = await conn.fetchrow(
            "SELECT propuesta_valor, diferenciadores, tono FROM om_voz_identidad WHERE tenant_id=$1",
            TENANT)

        procesos = await conn.fetchval("SELECT count(*) FROM om_procesos WHERE tenant_id=$1", TENANT) or 0
        adn = await conn.fetchval("SELECT count(*) FROM om_adn WHERE tenant_id=$1 AND activo=true", TENANT) or 0

    return {
        "diagnostico_numerico": dict(diag) if diag else {},
        "clientes": [dict(c) for c in clientes],
        "grupos": [dict(g) for g in grupos],
        "señales_bus": [{"origen": s["origen"], "tipo": s["tipo"],
                         "payload": s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"])}
                        for s in señales[:15]],
        "ingresos_mes": float(ingresos),
        "deuda_pendiente": float(deuda),
        "identidad": dict(identidad) if identidad else {},
        "procesos": procesos,
        "adn": adn,
        "fecha": str(date.today()),
    }


# ============================================================
# AGENTE 1: DETECTOR DE REPERTORIO (Nivel 1)
# ============================================================

SYSTEM_DETECTOR_REPERTORIO = f"""Eres el DETECTOR DE REPERTORIO COGNITIVO del organismo OMNI-MIND.

Tu trabajo es el MÁS IMPORTANTE de todo el enjambre: diagnosticar QUÉ configuración
de Inteligencias × Pensamientos × Razonamientos está usando este negocio.

{FRAMEWORK_CAUSAL}

{PERFILES_PATOLOGICOS}

A partir de los DATOS REALES del negocio, infiere:
1. ¿Qué INT están ACTIVAS? (evidencia en comportamiento observable)
2. ¿Qué INT están AUSENTES/ATROFIADAS? (lo que NO se hace, no se pregunta, no se ve)
3. ¿Qué P usa el dueño por defecto? (cómo organiza su pensamiento)
4. ¿Qué R emplea habitualmente? (cómo llega a conclusiones)
5. ¿Cuál es la distribución por lente del repertorio? (%S, %Se, %C)

CÓMO INFERIR INT×P×R DESDE DATOS OBSERVABLES:
- Si el negocio calcula bien costes pero no cuestiona por qué → INT-07 activa, INT-17 ausente
- Si tiene procesos documentados pero son mecánicos → P13 activo, P08 ausente, herramientas FOSILIZADAS
- Si analiza problemas descomponiéndolos → P02 o P13, R01 o R05 activos
- Si sigue haciendo lo mismo sin cuestionar → R04 degradado ("como siempre"), R06 ausente
- Si 15/16 grupos infrautilizados y no cierra ninguno → INT-18 ausente (no depura), P03 ausente (no cuestiona)
- Si no hay procesos documentados → INT-12 ausente (no narra), P12 ausente, R04 ausente
- Si no monitoriza competencia → INT-04 ausente, INT-13 ausente
- Si 90 clientes con instructor único → INT-16 activa (construye), C baja (no transfiere)

Responde en JSON:
{{
    "repertorio_detectado": {{
        "INT_activas": [
            {{"id": "INT-XX", "evidencia": "comportamiento observable que lo demuestra", "lente": "S|Se|C"}}
        ],
        "INT_ausentes": [
            {{"id": "INT-XX", "evidencia": "qué NO se hace que lo demuestra", "lente": "S|Se|C"}}
        ],
        "P_activos": [{{"id": "PXX", "evidencia": "...", "lente": "S|Se|C"}}],
        "P_ausentes": [{{"id": "PXX", "evidencia": "...", "lente": "S|Se|C"}}],
        "R_activos": [{{"id": "RXX", "evidencia": "...", "lente": "S|Se|C"}}],
        "R_ausentes": [{{"id": "RXX", "evidencia": "...", "lente": "S|Se|C"}}]
    }},
    "distribucion_lentes": {{
        "pct_S": 0-100,
        "pct_Se": 0-100,
        "pct_C": 0-100,
        "explicacion": "por qué esta distribución produce el perfil de lentes observado"
    }},
    "perfil_probable": "operador_ciego|visionario|zombi|genio_mortal|automata|potencial_dormido|E1|E2|E3|E4",
    "confianza": 0.0-1.0,
    "razonamiento": "2-3 frases explicando la cadena causal Nivel 1 → Nivel 2 → Nivel 3"
}}"""


# ============================================================
# AGENTE 2: DETECTOR DE DISFUNCIONES (IC2-IC6)
# ============================================================

SYSTEM_DETECTOR_DISFUNCIONES = f"""Eres el DETECTOR DE DISFUNCIONES COGNITIVAS del organismo OMNI-MIND.

Recibes el repertorio INT×P×R detectado y buscas DISFUNCIONES según las reglas IC2-IC6.

{FRAMEWORK_CAUSAL}

REGLAS A VERIFICAR:

IC2 MONOPOLIO: ¿Alguna INT opera sin complementarias?
  Verifica: INT-01 tiene INT-17? INT-07 tiene INT-08? INT-16 tiene INT-15?
  Si hay monopolio → señalar QUÉ INT, QUÉ complementaria falta, QUÉ efecto produce.

IC3 DESACOPLE INT-P: ¿Alguna INT se procesa con P incompatible?
  Verifica tabla IC3. Si hay desacople → la INT se ABORTA, no produce su output normal.
  EJEMPLO: si el negocio tiene INT-17(Existencial) pero la procesa con P07(Convergente),
  las preguntas profundas se trivializan. La INT existe pero está NEUTRALIZADA.

IC4 DESACOPLE INT-R: ¿Alguna INT usa R incompatible?
  Verifica tabla IC4. Si hay desacople → la INT concluye MAL.
  EJEMPLO: si INT-13(Prospectiva) se procesa con R01(Deducción), el futuro se "deduce"
  del presente → extrapolación lineal, no exploración de escenarios.

IC5 PARES P: ¿Los P activos tienen su complementario?
  P06 sin P07? P07 sin P06? P05 sin P04? P08 sin P11?

IC6 VALIDACIÓN CRUZADA R: ¿Los R se validan entre sí?
  R01 sola? R02 sola? R07 con priors fijos?

IC7 REQUISITO E4: ¿El repertorio cumple mínimos para equilibrio?
  ≥7 INT (3S+3Se+1C)? ≥4 P (P06+P07+P08+1Se)? ≥3 R (1S+R03+1C)?

IMPORTANTE: Una disfunción NO es solo "falta X". Es "falta X Y ESO PRODUCE Y".
  Ejemplo correcto: "INT-07 en monopolio sin INT-08 → el negocio optimiza costes
  sin ver el impacto en relaciones con clientes → por eso hay 2 fantasmas"
  Ejemplo incorrecto: "Falta INT-08" (no explica consecuencia)

Responde en JSON:
{{
    "disfunciones": [
        {{
            "regla": "IC2|IC3|IC4|IC5|IC6|IC7",
            "descripcion": "qué disfunción hay",
            "int_afectada": "INT-XX",
            "mecanismo": "cómo la disfunción produce el síntoma observable",
            "efecto_lentes": "qué lente frena o distorsiona",
            "efecto_funciones": ["F3", "F5"],
            "gravedad": 1-5,
            "ejemplo_concreto": "dato específico del negocio que lo demuestra"
        }}
    ],
    "repertorio_sano": false,
    "distancia_a_E4": {{
        "INT_faltan": 0,
        "P_faltan": 0,
        "R_faltan": 0,
        "lente_mas_carente": "S|Se|C"
    }}
}}"""


# ============================================================
# AGENTE 3: MECANISMO CAUSAL (Nivel 2 → Nivel 3-4)
# ============================================================

SYSTEM_MECANISMO_CAUSAL = f"""Eres el agente de MECANISMO CAUSAL del organismo OMNI-MIND.

Recibes el repertorio INT×P×R Y las disfunciones detectadas.
Tu trabajo: explicar EXACTAMENTE por qué el negocio tiene las lentes y funciones que tiene.

{FRAMEWORK_CAUSAL}

NO repitas los datos. EXPLICA la cadena causal:
  "El negocio tiene INT-01,02,05,07,16 activas (todas de S) + P07,P13 (de S)
   + R01,R07 (de S). El 85% de su repertorio genera S. Solo INT-03 aporta algo
   de Se y está procesada con P07 (IC3: se aborta). Resultado: S=0.46, Se=0.34.
   El Se=0.34 NO es bajo por falta de datos. Es bajo porque las herramientas
   que generan Se están ausentes o neutralizadas."

Incluye:
1. La cadena causal completa (Nivel 1 → 2 → 3 → 4)
2. Qué síntomas (F scores bajos) se EXPLICAN por qué combinaciones INT×P×R
3. Qué síntomas NO se explican (pueden tener causa externa al repertorio)

Responde en JSON:
{{
    "cadena_causal": {{
        "nivel_1_causa": "resumen del repertorio",
        "nivel_2_mecanismo": "cómo ese repertorio produce el sesgo de lentes",
        "nivel_3_efecto": "perfil de lentes resultante y por qué",
        "nivel_4_sintomas": "qué F scores se explican causalmente"
    }},
    "funciones_explicadas": {{
        "F1": "qué INT×P×R produce este score de F1",
        "F3": "qué INT×P×R produce este score de F3"
    }},
    "sintomas_sin_explicar": ["síntoma que no se explica por el repertorio"],
    "prediccion": "si el repertorio no cambia, en 6 meses el negocio estará en..."
}}"""


# ============================================================
# 6 AGENTES PERCEPTIVOS (clusters INT×P×R)
# ============================================================

CLUSTERS = {
    "analitico_operativo": {
        "ints": "INT-01(Lógica), INT-02(Computacional), INT-05(Estratégica)",
        "ps": "P07(Convergente), P13(Computacional), P14(Estratégico)",
        "rs": "R01(Deducción), R07(Bayesiano), R09(Eliminación)",
        "lente_primaria": "S",
        "angulo": "Estructura, cálculo, eficiencia, secuencias. Tu cluster IMPULSA S pero puede FRENAR Se si domina sin contrapeso.",
    },
    "financiero_constructivo": {
        "ints": "INT-07(Financiera), INT-10(Cinestésica), INT-11(Espacial), INT-16(Constructiva)",
        "ps": "P04(Diseño), P11(Encarnado)",
        "rs": "R12(Transductivo), R07(Bayesiano)",
        "lente_primaria": "S",
        "angulo": "Recursos, prototipado, acción física, distribución espacial. Tu cluster EJECUTA pero puede crear inercia operativa sin reflexión.",
    },
    "comprension_profunda": {
        "ints": "INT-03(Estructural), INT-08(Social), INT-17(Existencial), INT-18(Contemplativa)",
        "ps": "P03(Crítico), P05(Primeros principios), P08(Metacognición)",
        "rs": "R03(Abducción), R08(Dialéctico), R10(Retroductivo)",
        "lente_primaria": "Se",
        "angulo": "Por qué, identidad, lo no dicho, urgencia falsa. Tu cluster genera Se puro. Sin él, el negocio opera sin comprender.",
    },
    "ecosistema_adaptacion": {
        "ints": "INT-04(Ecológica), INT-06(Política), INT-09(Lingüística), INT-14(Divergente)",
        "ps": "P01(Lateral), P02(Sistémico), P06(Divergente)",
        "rs": "R02(Inducción), R05(Causal), R06(Contrafactual)",
        "lente_primaria": "Se",
        "angulo": "Entorno, poder, lenguaje, opciones. Tu cluster conecta con el AFUERA. Sin él, el negocio es endogámico.",
    },
    "narrativa_identidad": {
        "ints": "INT-12(Narrativa), INT-15(Estética), INT-13(Prospectiva)",
        "ps": "P09(Prospectivo), P12(Narrativo), P15(Integrativo)",
        "rs": "R04(Analogía), R11(Modal), R06(Contrafactual)",
        "lente_primaria": "Se+C",
        "angulo": "Historia, patrón, futuro, belleza. Tu cluster transfiere Se a C. Sin él, la comprensión muere con el fundador.",
    },
    "reflexion_gobierno": {
        "ints": "INT-17(Existencial), INT-18(Contemplativa), INT-13(Prospectiva)",
        "ps": "P08(Metacognición), P10(Reflexivo), P05(Primeros principios)",
        "rs": "R10(Retroductivo), R08(Dialéctico), R11(Modal)",
        "lente_primaria": "Se (gobierno)",
        "angulo": "Gobierno del sistema: ¿las reglas siguen siendo válidas? ¿la urgencia es real? Tu cluster es la ALARMA. Sin él, el autómata eterno.",
    },
}

SYSTEM_CLUSTER = f"""Eres el cluster {{nombre}} del enjambre cognitivo de OMNI-MIND.

Tus herramientas cognitivas: {{ints}} + {{ps}} + {{rs}}
Tu lente primaria: {{lente_primaria}}
Tu ángulo de percepción: {{angulo}}

{FRAMEWORK_CAUSAL}

IMPORTANTE: No solo percibas el negocio desde tu ángulo. Diagnostica:
1. ¿Tus herramientas (INT×P×R) están ACTIVAS en este negocio? ¿Hay evidencia?
2. Si están activas, ¿están correctamente acopladas? (IC3, IC4, IC5, IC6)
3. Si están ausentes, ¿qué SÍNTOMA produce su ausencia en las lentes/funciones?
4. ¿Tu cluster IMPULSA o FRENA alguna función/lente en este negocio concreto?

Responde en JSON:
{{{{
    "cluster": "{{nombre}}",
    "herramientas_activas_en_negocio": [
        {{{{"id": "INT-XX/PXX/RXX", "activa": true/false, "evidencia": "dato concreto"}}}}
    ],
    "acoplamientos": [
        {{{{"int": "INT-XX", "p_o_r": "PXX/RXX", "estado": "correcto|desacoplado|ausente",
          "efecto": "qué produce este acoplamiento o desacoplamiento"}}}}
    ],
    "impulsa": [{{{{"funcion": "FX", "lente": "S|Se|C", "mecanismo": "cómo impulsa"}}}}],
    "frena": [{{{{"funcion": "FX", "lente": "S|Se|C", "mecanismo": "cómo frena"}}}}],
    "insights": ["insight que solo este cluster puede ver"],
    "preguntas_nuevas": ["pregunta que el negocio debería hacerse y no se hace"]
}}}}"""


# ============================================================
# MOTOR DE EJECUCIÓN
# ============================================================

async def _call_agente(system_prompt: str, user_prompt: str, nombre: str) -> dict:
    """Ejecuta un agente individual del enjambre."""
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                json={
                    "model": REASONING_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]

        # Parsear JSON tolerante a markdown fences y texto extra
        clean = raw.strip()
        if "```" in clean:
            parts = clean.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    try:
                        resultado = json.loads(part)
                        dt = round(time.time() - t0, 1)
                        log.info("enjambre_agente_ok", agente=nombre, tiempo=dt)
                        return resultado
                    except json.JSONDecodeError:
                        continue
        # Sin fences o fences sin JSON válido — buscar JSON directo
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            clean = clean[start:end + 1]
        resultado = json.loads(clean)
        dt = round(time.time() - t0, 1)
        log.info("enjambre_agente_ok", agente=nombre, tiempo=dt)
        return resultado

    except json.JSONDecodeError:
        # Intentar reparar JSON truncado cerrando llaves/corchetes abiertos
        try:
            import re
            repair = clean if 'clean' in dir() else raw
            # Contar llaves abiertas no cerradas y añadirlas
            opens = repair.count("{") - repair.count("}")
            repair = repair + "}" * max(opens, 0)
            opens_b = repair.count("[") - repair.count("]")
            repair = repair + "]" * max(opens_b, 0)
            resultado = json.loads(repair)
            log.info("enjambre_agente_repaired", agente=nombre)
            return resultado
        except Exception:
            pass
        raw_preview = raw[:300] if 'raw' in dir() else ""
        log.warning("enjambre_parse_error", agente=nombre, raw_preview=raw_preview[:150])
        return {"error": "parse_error", "raw": raw_preview}
    except Exception as e:
        log.warning("enjambre_agente_error", agente=nombre, error=str(e))
        return {"error": str(e)[:200], "agente": nombre}


async def ejecutar_enjambre() -> dict:
    """Ejecuta el enjambre cognitivo con modelo causal de 4 niveles.

    Secuencia (NO paralelo — cada agente alimenta al siguiente):
    1. Detector de Repertorio → identifica INT×P×R del negocio
    2. Detector de Disfunciones → aplica IC2-IC6
    3. Mecanismo Causal → explica por qué las lentes/funciones son lo que son
    4. 6 Clusters perceptivos → cada uno evalúa si sus herramientas están activas
    """
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY no configurada"}

    t0 = time.time()
    ctx = await _contexto_completo()
    ctx_str = json.dumps(ctx, ensure_ascii=False, indent=2, default=str)[:6000]

    resultados = {}

    # 1. DETECTOR DE REPERTORIO (Nivel 1)
    log.info("enjambre_fase1_repertorio")
    repertorio = await _call_agente(
        SYSTEM_DETECTOR_REPERTORIO,
        f"DATOS REALES DEL NEGOCIO:\n{ctx_str}",
        "Detector-Repertorio"
    )
    resultados["repertorio"] = repertorio

    # 2. DETECTOR DE DISFUNCIONES (IC2-IC6)
    log.info("enjambre_fase2_disfunciones")
    disfunciones = await _call_agente(
        SYSTEM_DETECTOR_DISFUNCIONES,
        f"REPERTORIO DETECTADO:\n{json.dumps(repertorio, ensure_ascii=False, indent=2, default=str)}\n\nDATOS REALES:\n{ctx_str}",
        "Detector-Disfunciones"
    )
    resultados["disfunciones"] = disfunciones

    # 3. MECANISMO CAUSAL (Nivel 2 → 3 → 4)
    log.info("enjambre_fase3_causal")
    causal = await _call_agente(
        SYSTEM_MECANISMO_CAUSAL,
        f"REPERTORIO:\n{json.dumps(repertorio, ensure_ascii=False, indent=2, default=str)}\n\nDISFUNCIONES:\n{json.dumps(disfunciones, ensure_ascii=False, indent=2, default=str)}\n\nDATOS REALES:\n{ctx_str}",
        "Mecanismo-Causal"
    )
    resultados["causal"] = causal

    # 4. 6 CLUSTERS PERCEPTIVOS (en paralelo — son independientes entre sí)
    log.info("enjambre_fase4_clusters")
    contexto_enriquecido = (
        f"REPERTORIO DETECTADO:\n{json.dumps(repertorio, ensure_ascii=False, indent=2, default=str)[:2000]}\n\n"
        f"DISFUNCIONES:\n{json.dumps(disfunciones, ensure_ascii=False, indent=2, default=str)[:1500]}\n\n"
        f"DATOS REALES:\n{ctx_str}"
    )

    tareas_clusters = []
    for cl_id, cl_def in CLUSTERS.items():
        prompt = SYSTEM_CLUSTER.format(
            nombre=cl_id, ints=cl_def["ints"], ps=cl_def["ps"],
            rs=cl_def["rs"], lente_primaria=cl_def["lente_primaria"],
            angulo=cl_def["angulo"])
        tareas_clusters.append(
            _call_agente(prompt, contexto_enriquecido, f"Cluster-{cl_id}")
        )

    resp_clusters = await asyncio.gather(*tareas_clusters)
    resultados["clusters"] = {}
    for cl_id, resp in zip(CLUSTERS.keys(), resp_clusters):
        resultados["clusters"][cl_id] = resp

    # --- EMITIR AL BUS ---
    from src.pilates.bus import emitir
    señales_emitidas = 0

    # Señal de repertorio
    try:
        await emitir("PERCEPCION_CAUSAL", "ENJAMBRE_REPERTORIO",
                      {"tipo": "repertorio", "resultado": repertorio}, prioridad=3)
        señales_emitidas += 1
    except Exception:
        pass

    # Señal de disfunciones
    try:
        await emitir("PERCEPCION_CAUSAL", "ENJAMBRE_DISFUNCIONES",
                      {"tipo": "disfunciones", "resultado": disfunciones}, prioridad=2)
        señales_emitidas += 1
    except Exception:
        pass

    # Señal causal
    try:
        await emitir("PERCEPCION_CAUSAL", "ENJAMBRE_CAUSAL",
                      {"tipo": "mecanismo_causal", "resultado": causal}, prioridad=3)
        señales_emitidas += 1
    except Exception:
        pass

    # Señales de clusters
    for cl_id, resp in resultados["clusters"].items():
        if "error" not in resp:
            try:
                await emitir("PERCEPCION_CAUSAL", f"ENJAMBRE_CLUSTER_{cl_id.upper()}",
                              {"tipo": "cluster", "cluster": cl_id, "resultado": resp}, prioridad=5)
                señales_emitidas += 1
            except Exception:
                pass

    # --- PERSISTIR ---
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_enjambre_diagnosticos
                (tenant_id, estado_acd_base, resultado_lentes, resultado_funciones,
                 resultado_clusters, señales_emitidas, tiempo_total_s)
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6, $7)
        """, TENANT,
            repertorio.get("perfil_probable", "desconocido"),
            json.dumps({"repertorio": repertorio, "disfunciones": disfunciones}, ensure_ascii=False, default=str),
            json.dumps(causal, ensure_ascii=False, default=str),
            json.dumps(resultados["clusters"], ensure_ascii=False, default=str),
            señales_emitidas,
            round(time.time() - t0, 0))

    dt = round(time.time() - t0, 1)
    errores = sum(1 for r in [repertorio, disfunciones, causal] if "error" in r)
    errores += sum(1 for r in resultados["clusters"].values() if "error" in r)

    log.info("enjambre_completo", agentes=9, señales=señales_emitidas,
             errores=errores, tiempo=dt, perfil=repertorio.get("perfil_probable"))

    return {
        "status": "ok",
        "agentes_ejecutados": 9 - errores,
        "errores": errores,
        "señales_emitidas": señales_emitidas,
        "tiempo_total_s": dt,
        "perfil_detectado": repertorio.get("perfil_probable"),
        "distribucion_lentes": repertorio.get("distribucion_lentes"),
        "disfunciones_encontradas": len(disfunciones.get("disfunciones", [])),
        "resultados": resultados,
    }
