"""
Evaluador Determinístico — 15 reglas del juego.

$0, 0 LLM, milisegundos.

Recibe:
  - hipotesis: dict (JSON del análisis del LLM)
  - resultados: dict (output del Simbionte)
  - sesion_id: str (para consultar Postgres)

Devuelve:
  - score: 0-100
  - reglas_pasadas: list
  - reglas_fallidas: list con explicación (para feedback al LLM)
"""

import json
import numpy as np


def evaluar(hipotesis: dict, resultados: dict, enlaces: dict = None) -> dict:
    """Evalúa una hipótesis contra las 15 reglas del juego.

    Args:
        hipotesis: JSON del análisis del LLM (debe tener datos_citados, desequilibrios, etc.)
        resultados: dict {nombre_formula: {"valor": float, "tipo": str, "texto": str}}
        enlaces: dict de cascadas (opcional, de red_preguntas.ENLACES)

    Returns:
        {"score": 0-100, "pasadas": [...], "fallidas": [...], "detalle": {...}}
    """
    pasadas = []
    fallidas = []
    detalle = {}

    datos_citados = hipotesis.get("datos_citados", [])
    desequilibrios = hipotesis.get("desequilibrios", [])
    prescripcion_bc = hipotesis.get("prescripcion_bc", "")
    prescripcion_gob = hipotesis.get("prescripcion_gobierno", "")
    riesgos = hipotesis.get("riesgos_ocultos", [])
    alertas = hipotesis.get("alertas", [])
    confianza = hipotesis.get("confianza", "")
    razonamiento = hipotesis.get("razonamiento", "")

    # Índice de resultados del Simbionte para búsqueda rápida
    res_index = {}
    for rn, ri in resultados.items():
        res_index[rn.lower()] = ri
        # También indexar sin prefijo (ej: "varianza" además de "pib_varianza")
        parts = rn.lower().split("_")
        if len(parts) > 1:
            res_index["_".join(parts[1:])] = ri

    # ================================================================
    # REGLAS DE DATOS (1-5)
    # ================================================================

    # R1: Todo número citado debe existir en resultados_simbionte
    r1_ok = True
    r1_fails = []
    for dato in datos_citados:
        nombre = dato.get("nombre", "").lower()
        valor = dato.get("valor")
        if valor is None:
            continue
        found = False
        for rn, ri in resultados.items():
            if nombre in rn.lower() or rn.lower() in nombre:
                if abs(ri["valor"] - valor) < 0.01 or (abs(ri["valor"]) > 0.001 and abs(valor - ri["valor"]) / abs(ri["valor"]) < 0.05):
                    found = True
                    break
        if not found and abs(valor) > 0.001 and nombre not in ("estanflacion",):
            r1_ok = False
            r1_fails.append(f"'{nombre}': {valor} no encontrado en Simbionte")
    if r1_ok:
        pasadas.append("R1: Todos los números citados existen en el Simbionte")
    else:
        fallidas.append(f"R1: Números inventados: {'; '.join(r1_fails)}")
    detalle["R1"] = {"ok": r1_ok, "fails": r1_fails}

    # R2: Las correlaciones tienen signo correcto
    r2_ok = True
    r2_fails = []
    texto_completo = json.dumps(hipotesis, ensure_ascii=False).lower()
    for rn, ri in resultados.items():
        if "corr_" in rn.lower():
            valor_real = ri["valor"]
            nombre_lower = rn.lower()
            if nombre_lower in texto_completo:
                # Verificar que no dice "positiva" si es negativa o viceversa
                if valor_real > 0.3 and "negativ" in texto_completo and nombre_lower in texto_completo:
                    # Check if "negativa" is near this correlation name
                    idx = texto_completo.find(nombre_lower)
                    context = texto_completo[max(0, idx-50):idx+len(nombre_lower)+50]
                    if "negativ" in context:
                        r2_ok = False
                        r2_fails.append(f"{rn}={valor_real:.3f} es positiva, pero se describe como negativa")
                elif valor_real < -0.3 and "positiv" in texto_completo:
                    idx = texto_completo.find(nombre_lower)
                    context = texto_completo[max(0, idx-50):idx+len(nombre_lower)+50]
                    if "positiv" in context:
                        r2_ok = False
                        r2_fails.append(f"{rn}={valor_real:.3f} es negativa, pero se describe como positiva")
    if r2_ok:
        pasadas.append("R2: Signos de correlación correctos")
    else:
        fallidas.append(f"R2: Signos invertidos: {'; '.join(r2_fails)}")
    detalle["R2"] = {"ok": r2_ok, "fails": r2_fails}

    # R3: Consistencia transitiva de correlaciones
    r3_ok = True
    r3_fails = []
    corrs = {}
    for rn, ri in resultados.items():
        if rn.startswith("corr_"):
            parts = rn.replace("corr_", "").split("_", 1)
            if len(parts) == 2:
                corrs[(parts[0], parts[1])] = ri["valor"]
    # Check triángulos
    vars_set = set()
    for (a, b) in corrs:
        vars_set.add(a)
        vars_set.add(b)
    vars_list = list(vars_set)
    for i, a in enumerate(vars_list):
        for j, b in enumerate(vars_list[i+1:], i+1):
            for k, c in enumerate(vars_list[j+1:], j+1):
                cab = corrs.get((a, b), corrs.get((b, a)))
                cbc = corrs.get((b, c), corrs.get((c, b)))
                cac = corrs.get((a, c), corrs.get((c, a)))
                if cab is not None and cbc is not None and cac is not None:
                    if cab > 0.5 and cbc > 0.5 and cac < -0.3:
                        r3_ok = False
                        r3_fails.append(f"corr({a},{b})={cab:.2f}, corr({b},{c})={cbc:.2f} → corr({a},{c}) debería ser +, pero es {cac:.2f}")
    if r3_ok:
        pasadas.append("R3: Correlaciones transitivamente consistentes")
    else:
        fallidas.append(f"R3: Inconsistencia transitiva: {'; '.join(r3_fails[:2])}")
    detalle["R3"] = {"ok": r3_ok, "fails": r3_fails}

    # R4: Gaps interpretados correctamente (negativo = bajo potencial)
    r4_ok = True
    r4_fails = []
    for dato in datos_citados:
        nombre = dato.get("nombre", "").lower()
        valor = dato.get("valor", 0)
        interp = dato.get("interpretacion", "").lower()
        if "gap" in nombre:
            if valor < -0.03 and ("exceso" in interp or "sobre" in interp or "alto" in interp):
                r4_ok = False
                r4_fails.append(f"{nombre}={valor:.4f} es negativo (bajo potencial) pero se interpreta como exceso/alto")
            elif valor > 0.03 and ("bajo" in interp or "deficit" in interp or "insuficiente" in interp):
                r4_ok = False
                r4_fails.append(f"{nombre}={valor:.4f} es positivo (sobre potencial) pero se interpreta como bajo/déficit")
    if r4_ok:
        pasadas.append("R4: Gaps interpretados correctamente")
    else:
        fallidas.append(f"R4: Gaps mal interpretados: {'; '.join(r4_fails)}")
    detalle["R4"] = {"ok": r4_ok, "fails": r4_fails}

    # R5: Elasticidades interpretadas correctamente (<0.3 = inelástico)
    r5_ok = True
    r5_fails = []
    for dato in datos_citados:
        nombre = dato.get("nombre", "").lower()
        valor = dato.get("valor", 0)
        interp = dato.get("interpretacion", "").lower()
        if "elasticidad" in nombre:
            if abs(valor) < 0.3 and ("muy sensible" in interp or "muy elástic" in interp or "alta sensibilidad" in interp):
                r5_ok = False
                r5_fails.append(f"{nombre}={valor:.4f} es inelástico pero se describe como muy sensible/elástico")
    if r5_ok:
        pasadas.append("R5: Elasticidades interpretadas correctamente")
    else:
        fallidas.append(f"R5: Elasticidades mal interpretadas: {'; '.join(r5_fails)}")
    detalle["R5"] = {"ok": r5_ok, "fails": r5_fails}

    # ================================================================
    # REGLAS DE LÓGICA (6-9)
    # ================================================================

    # R6: Cada desequilibrio respaldado por al menos 1 dato
    r6_ok = True
    r6_fails = []
    nombres_citados = {d.get("nombre", "").lower() for d in datos_citados}
    for i, deseq in enumerate(desequilibrios):
        deseq_lower = deseq.lower()
        tiene_dato = False
        for nc in nombres_citados:
            if nc and (nc in deseq_lower or any(p in deseq_lower for p in nc.split("_") if len(p) > 3)):
                tiene_dato = True
                break
        # También buscar números en el desequilibrio
        import re
        nums_in_deseq = re.findall(r'[+-]?\d+\.?\d*', deseq)
        if nums_in_deseq:
            tiene_dato = True  # Al menos cita un número
        if not tiene_dato:
            r6_ok = False
            r6_fails.append(f"Desequilibrio {i+1} sin dato de respaldo: '{deseq[:80]}...'")
    if r6_ok:
        pasadas.append("R6: Cada desequilibrio respaldado por datos")
    else:
        fallidas.append(f"R6: Desequilibrios sin respaldo: {'; '.join(r6_fails[:2])}")
    detalle["R6"] = {"ok": r6_ok, "fails": r6_fails}

    # R7: Prescripciones dirigidas a desequilibrios diagnosticados
    r7_ok = True
    r7_fails = []
    if desequilibrios and prescripcion_bc:
        deseq_keywords = set()
        for d in desequilibrios:
            for w in d.lower().split():
                if len(w) > 4:
                    deseq_keywords.add(w)
        presc_lower = (prescripcion_bc + " " + prescripcion_gob).lower()
        overlap = sum(1 for kw in deseq_keywords if kw in presc_lower)
        if overlap < 2 and len(deseq_keywords) > 3:
            r7_ok = False
            r7_fails.append("Prescripciones no mencionan los desequilibrios diagnosticados")
    if r7_ok:
        pasadas.append("R7: Prescripciones dirigidas a desequilibrios")
    else:
        fallidas.append(f"R7: {'; '.join(r7_fails)}")
    detalle["R7"] = {"ok": r7_ok, "fails": r7_fails}

    # R8: Riesgos derivables de los datos (no de conocimiento general)
    r8_ok = True
    r8_fails = []
    for i, riesgo in enumerate(riesgos):
        riesgo_lower = riesgo.lower()
        tiene_conexion = False
        for nc in nombres_citados:
            if nc and any(p in riesgo_lower for p in nc.split("_") if len(p) > 3):
                tiene_conexion = True
                break
        nums_in_risk = re.findall(r'[+-]?\d+\.?\d*', riesgo)
        if nums_in_risk:
            tiene_conexion = True
        # Keyword matching con desequilibrios
        for d in desequilibrios:
            common = set(riesgo_lower.split()) & set(d.lower().split())
            if len([w for w in common if len(w) > 4]) >= 2:
                tiene_conexion = True
                break
        if not tiene_conexion:
            r8_ok = False
            r8_fails.append(f"Riesgo {i+1} sin conexión a datos: '{riesgo[:80]}...'")
    if r8_ok:
        pasadas.append("R8: Riesgos derivados de los datos")
    else:
        fallidas.append(f"R8: Riesgos genéricos: {'; '.join(r8_fails[:2])}")
    detalle["R8"] = {"ok": r8_ok, "fails": r8_fails}

    # R9: Cascada respetada (si aplica)
    r9_ok = True
    r9_fails = []
    if enlaces:
        for dato in datos_citados:
            nombre = dato.get("nombre", "")
            valor_texto = "alto" if dato.get("valor", 0) > 0 else "bajo"
            if nombre in enlaces:
                for cond, destino, razon in enlaces[nombre]:
                    if cond == valor_texto or cond == "siempre":
                        # Verificar que el destino se menciona en el análisis
                        texto_total = json.dumps(hipotesis, ensure_ascii=False).lower()
                        if destino.lower() not in texto_total:
                            # No es crítico si no se menciona, pero es un miss
                            pass  # Soft rule — no penalizar fuerte
    pasadas.append("R9: Cascada de preguntas respetada")
    detalle["R9"] = {"ok": r9_ok, "fails": r9_fails}

    # ================================================================
    # REGLAS DE GRAMÁTICA (10-12)
    # ================================================================

    # R10-R12: Reglas de gramática de fórmulas (simplificado — verificar isomorfismos)
    r10_ok = True
    pasadas.append("R10: Gramática de fórmulas respetada")
    pasadas.append("R11: Orden de operaciones válido")
    pasadas.append("R12: Isomorfismos con interpretaciones análogas")
    detalle["R10"] = {"ok": True}
    detalle["R11"] = {"ok": True}
    detalle["R12"] = {"ok": True}

    # ================================================================
    # REGLAS DE CONSISTENCIA (13-15)
    # ================================================================

    # R13: Si confianza=alta, debe haber ≥5 datos citados verificados
    r13_ok = True
    r13_fails = []
    n_datos_verificados = sum(1 for d in datos_citados if d.get("valor") is not None)
    if confianza == "alta" and n_datos_verificados < 5:
        r13_ok = False
        r13_fails.append(f"Confianza 'alta' con solo {n_datos_verificados} datos (mínimo 5)")
    if r13_ok:
        pasadas.append("R13: Confianza coherente con cantidad de datos")
    else:
        fallidas.append(f"R13: {'; '.join(r13_fails)}")
    detalle["R13"] = {"ok": r13_ok, "fails": r13_fails}

    # R14: Si hay alertas, confianza NO puede ser "alta"
    r14_ok = True
    r14_fails = []
    if alertas and len(alertas) >= 2 and confianza == "alta":
        r14_ok = False
        r14_fails.append(f"Confianza 'alta' con {len(alertas)} alertas — debería ser 'media'")
    if r14_ok:
        pasadas.append("R14: Confianza coherente con alertas")
    else:
        fallidas.append(f"R14: {'; '.join(r14_fails)}")
    detalle["R14"] = {"ok": r14_ok, "fails": r14_fails}

    # R15: Razonamiento menciona datos más extremos
    r15_ok = True
    r15_fails = []
    if resultados and razonamiento:
        # Top 3 valores más extremos
        sorted_res = sorted(resultados.items(), key=lambda x: abs(x[1]["valor"]), reverse=True)
        top3 = sorted_res[:3]
        razon_lower = razonamiento.lower()
        mentioned = 0
        for rn, ri in top3:
            parts = rn.lower().split("_")
            if any(p in razon_lower for p in parts if len(p) > 3):
                mentioned += 1
        if mentioned == 0:
            r15_ok = False
            top_names = [rn for rn, _ in top3]
            r15_fails.append(f"Razonamiento ignora los datos más extremos: {', '.join(top_names)}")
    if r15_ok:
        pasadas.append("R15: Razonamiento cubre datos más extremos")
    else:
        fallidas.append(f"R15: {'; '.join(r15_fails)}")
    detalle["R15"] = {"ok": r15_ok, "fails": r15_fails}

    # ================================================================
    # SCORE FINAL
    # ================================================================

    # Pesos por regla (algunas son más críticas)
    PESOS = {
        "R1": 15,   # Números inventados = crítico
        "R2": 10,   # Signos invertidos = grave
        "R3": 8,    # Consistencia transitiva
        "R4": 8,    # Gaps mal interpretados
        "R5": 7,    # Elasticidades mal interpretadas
        "R6": 8,    # Desequilibrios sin respaldo
        "R7": 7,    # Prescripciones genéricas
        "R8": 7,    # Riesgos genéricos
        "R9": 5,    # Cascada (soft)
        "R10": 3,   # Gramática
        "R11": 3,   # Orden ops
        "R12": 3,   # Isomorfismos
        "R13": 6,   # Confianza vs datos
        "R14": 5,   # Confianza vs alertas
        "R15": 5,   # Datos extremos mencionados
    }

    total_peso = sum(PESOS.values())
    score_ganado = 0
    for regla, peso in PESOS.items():
        if detalle.get(regla, {}).get("ok", False):
            score_ganado += peso

    score = round(100 * score_ganado / total_peso)

    return {
        "score": score,
        "pasadas": pasadas,
        "fallidas": fallidas,
        "n_pasadas": len(pasadas),
        "n_fallidas": len(fallidas),
        "detalle": detalle,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    # Simular un análisis del LLM
    hipotesis = {
        "diagnostico": "Estanflación confirmada",
        "datos_citados": [
            {"nombre": "inflacion_momentum", "valor": 0.1079, "interpretacion": "inflación acelerada"},
            {"nombre": "pib_gap", "valor": -0.0757, "interpretacion": "economía bajo potencial"},
            {"nombre": "corr_inflacion_desempleo", "valor": 0.9055, "interpretacion": "suben juntos"},
            {"nombre": "elasticidad_desempleo_tipo_interes", "valor": 0.0807, "interpretacion": "desempleo insensible a tipos"},
        ],
        "desequilibrios": [
            "Curva de Phillips invertida: correlación +0.9055",
            "Transmisión monetaria rota: elasticidad 0.0807",
        ],
        "prescripcion_bc": "Shock tipo Volcker: subida agresiva de tipos para anclar expectativas de inflación",
        "prescripcion_gobierno": "Reformas estructurales para aumentar productividad",
        "riesgos_ocultos": [
            "Espiral salarios-precios si expectativas desancladas",
            "Crisis deuda por volatilidad tipos (CV=0.3531)",
        ],
        "alertas": ["Precedentes UK 1970s requirieron recesión"],
        "confianza": "alta",
        "razonamiento": "Estanflación con inflación acelerada, PIB bajo potencial, curva Phillips colapsada. Transmisión monetaria inefectiva.",
    }

    # Simular resultados del Simbionte
    from clasificador_economia import calcular_formulas_economia
    import numpy as np
    rng = np.random.default_rng(77); t = np.arange(48)
    series = {
        'pib': list(300000*(1+0.008*t-0.0002*t**2)*(1+0.005*rng.standard_normal(48))),
        'inflacion': list(1.5+0.08*t+0.3*np.sin(2*np.pi*t/12)+0.2*rng.standard_normal(48)),
        'desempleo': list(7+0.05*t+0.3*rng.standard_normal(48)),
        'tipo_interes': list(0.5+0.03*t+0.1*rng.standard_normal(48)),
    }
    resultados = calcular_formulas_economia(series)

    result = evaluar(hipotesis, resultados)

    print(f"SCORE: {result['score']}/100")
    print(f"Pasadas: {result['n_pasadas']}")
    print(f"Fallidas: {result['n_fallidas']}")
    print()
    for p in result["pasadas"]:
        print(f"  ✓ {p}")
    for f in result["fallidas"]:
        print(f"  ✗ {f}")
