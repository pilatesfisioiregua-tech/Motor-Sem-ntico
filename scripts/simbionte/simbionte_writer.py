"""
OMC-95: Simbionte Writer — calcula y ESCRIBE en Postgres (no inyecta en prompt).

Flujo:
  1. Recibe series temporales (dict de arrays)
  2. Calcula todas las fórmulas aplicables (clasificador_economia)
  3. Enriquece con semántica (polos, presupuestos, razonamiento)
  4. Detecta patrones (isomorfismos)
  5. Calcula cascadas (red de preguntas)
  6. Escribe TODO en Postgres via REST endpoint /simbionte/escribir-batch
  7. Devuelve sesion_id para que el agente LLM lo use

$0 en LLM — todo es cálculo local + 1 POST HTTP.
"""

import sys, os, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from clasificador_economia import calcular_formulas_economia
from semantica_formulas import SEMANTICA, razonamiento_a_texto
from catalogo_finalidades import detectar_finalidad
from red_preguntas import ENLACES
from decodificador_economia import clasificar_nivel
from pipeline_completo import harness_seleccionar, ISOMORFISMOS_CATALOGO

import httpx

# URL del endpoint Simbionte en fly.io (o local para dev)
SIMBIONTE_URL = os.getenv(
    "SIMBIONTE_URL",
    "https://motor-semantico-omni.fly.dev"
)


def calcular_y_escribir(series_dict: dict, pregunta: str, modelo_llm: str = "unknown") -> dict:
    """Calcula con el Simbionte y escribe resultados en Postgres.

    Args:
        series_dict: {nombre_metrica: [valores...]}
        pregunta: pregunta del usuario
        modelo_llm: qué modelo consumirá estos datos

    Returns:
        {"sesion_id": UUID, "n_escritos": int, "dt": float, "finalidad": str}
    """
    t0 = time.time()

    # 1. Calcular todas las fórmulas
    resultados = calcular_formulas_economia(series_dict)

    # 2. Detectar finalidad
    finalidad_raw = detectar_finalidad(pregunta)
    finalidad = finalidad_raw[0] if isinstance(finalidad_raw, list) and finalidad_raw else str(finalidad_raw)

    # 3. Seleccionar top resultados (harness demand-driven)
    seleccion = harness_seleccionar(resultados, 30)

    # 4. Construir batch de resultados para Postgres
    batch = []

    # 4a. VALORES ABSOLUTOS de cada serie (último, mínimo, máximo, media)
    # El LLM SOLO puede citar estos valores, no inventar otros
    for nombre_serie, valores in series_dict.items():
        arr = np.array(valores, dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) < 2:
            continue
        # Último valor
        batch.append({
            "nombre": f"{nombre_serie}_ultimo",
            "tipo": "nivel",
            "categoria": "valor absoluto serie",
            "valor": float(arr[-1]),
            "valor_texto": f"último valor de {nombre_serie}",
            "texto_legible": f"Valor más reciente de la serie {nombre_serie}",
            "pregunta": f"¿Cuál es el valor actual de {nombre_serie}?",
            "polos": None, "presupuestos": None, "razonamiento": None,
            "datos_origen": {"serie": nombre_serie, "n_puntos": len(arr)},
            "finalidad": finalidad, "paso_protocolo": None,
            "patron_match": None, "isomorfismo": None, "precedentes": None,
            "prescripcion": None, "enlaces": None,
            "modelo_llm": modelo_llm, "coste_calculo": 0.0,
        })
        # Mínimo
        batch.append({
            "nombre": f"{nombre_serie}_minimo",
            "tipo": "nivel",
            "categoria": "valor absoluto serie",
            "valor": float(np.min(arr)),
            "valor_texto": f"mínimo histórico de {nombre_serie}",
            "texto_legible": f"Mínimo de la serie {nombre_serie} en el periodo",
            "pregunta": f"¿Cuál fue el mínimo de {nombre_serie}?",
            "polos": None, "presupuestos": None, "razonamiento": None,
            "datos_origen": {"serie": nombre_serie}, "finalidad": finalidad,
            "paso_protocolo": None, "patron_match": None, "isomorfismo": None,
            "precedentes": None, "prescripcion": None, "enlaces": None,
            "modelo_llm": modelo_llm, "coste_calculo": 0.0,
        })
        # Máximo
        batch.append({
            "nombre": f"{nombre_serie}_maximo",
            "tipo": "nivel",
            "categoria": "valor absoluto serie",
            "valor": float(np.max(arr)),
            "valor_texto": f"máximo histórico de {nombre_serie}",
            "texto_legible": f"Máximo de la serie {nombre_serie} en el periodo",
            "pregunta": f"¿Cuál fue el máximo de {nombre_serie}?",
            "polos": None, "presupuestos": None, "razonamiento": None,
            "datos_origen": {"serie": nombre_serie}, "finalidad": finalidad,
            "paso_protocolo": None, "patron_match": None, "isomorfismo": None,
            "precedentes": None, "prescripcion": None, "enlaces": None,
            "modelo_llm": modelo_llm, "coste_calculo": 0.0,
        })
        # Media
        batch.append({
            "nombre": f"{nombre_serie}_media",
            "tipo": "nivel",
            "categoria": "valor absoluto serie",
            "valor": float(np.mean(arr)),
            "valor_texto": f"media de {nombre_serie}",
            "texto_legible": f"Media de la serie {nombre_serie} en el periodo",
            "pregunta": f"¿Cuál es la media de {nombre_serie}?",
            "polos": None, "presupuestos": None, "razonamiento": None,
            "datos_origen": {"serie": nombre_serie}, "finalidad": finalidad,
            "paso_protocolo": None, "patron_match": None, "isomorfismo": None,
            "precedentes": None, "prescripcion": None, "enlaces": None,
            "modelo_llm": modelo_llm, "coste_calculo": 0.0,
        })

    # 4b. Resultados derivados (fórmulas del Simbionte)
    for nombre, info, score, reason, nivel_idx, nivel_texto in seleccion:
        # Semántica
        sem = SEMANTICA.get(info.get("tipo", ""), {})
        # Intentar semántica específica por nombre de fórmula
        base_name = nombre.rsplit("_", 1)[0] if "_" in nombre else nombre
        sem_especifica = SEMANTICA.get(base_name, sem)

        razon = razonamiento_a_texto(base_name) or razonamiento_a_texto(info.get("tipo", ""))

        # Enlaces/cascada
        enlaces_raw = ENLACES.get(base_name, ENLACES.get(info.get("tipo", ""), []))
        enlaces_serializados = None
        if enlaces_raw:
            enlaces_list = []
            for cond, destino, razon_enlace in enlaces_raw:
                sem_dest = SEMANTICA.get(destino, {})
                enlaces_list.append({
                    "condicion": cond,
                    "destino": destino,
                    "pregunta": sem_dest.get("pregunta", "?"),
                    "razon": razon_enlace,
                })
            enlaces_serializados = enlaces_list

        # Patrones/isomorfismos
        patron = None
        isomorfismo = None
        precedentes = None
        prescripcion_patron = None
        for iso_nombre, iso_info in ISOMORFISMOS_CATALOGO.items():
            for señal, (op, threshold) in iso_info.get("señales", {}).items():
                if señal in nombre:
                    v = info["valor"]
                    if (op == ">" and v > threshold) or (op == "<" and v < threshold):
                        patron = iso_nombre
                        isomorfismo = iso_info.get("isomorfismo", "")
                        precedentes = iso_info.get("precedentes", [])
                        prescripcion_patron = iso_info.get("prescripcion_historica", "")
                        break

        batch.append({
            "nombre": nombre,
            "tipo": info.get("tipo", "otro"),
            "categoria": reason,
            "valor": float(info["valor"]) if np.isfinite(info["valor"]) else None,
            "valor_texto": nivel_texto,
            "texto_legible": info.get("texto", ""),
            "pregunta": sem_especifica.get("pregunta", sem.get("pregunta")),
            "polos": list(sem_especifica.get("polos", sem.get("polos", ()))),
            "presupuestos": sem_especifica.get("presupuestos", sem.get("presupuestos")),
            "razonamiento": razon,
            "datos_origen": {"series": list(series_dict.keys())},
            "finalidad": finalidad,
            "paso_protocolo": None,  # precálculo
            "patron_match": patron,
            "isomorfismo": isomorfismo,
            "precedentes": precedentes,
            "prescripcion": prescripcion_patron,
            "enlaces": enlaces_serializados,
            "modelo_llm": modelo_llm,
            "coste_calculo": 0.0,
        })

    # 5. Añadir patrones detectados como resultados tipo "patron"
    for iso_nombre, iso_info in ISOMORFISMOS_CATALOGO.items():
        n_match = 0
        total_signals = len(iso_info.get("señales", {}))
        for señal, (op, threshold) in iso_info.get("señales", {}).items():
            for rn, ri in resultados.items():
                if señal in rn:
                    v = ri["valor"]
                    if (op == ">" and v > threshold) or (op == "<" and v < threshold):
                        n_match += 1
                    break
        if total_signals > 0 and n_match >= total_signals * 0.5:
            batch.append({
                "nombre": iso_nombre,
                "tipo": "patron",
                "categoria": f"{n_match}/{total_signals} senales",
                "valor": n_match / total_signals,
                "valor_texto": "match" if n_match >= total_signals * 0.7 else "parcial",
                "texto_legible": iso_info.get("descripcion", ""),
                "pregunta": f"Se parece a {iso_nombre}?",
                "polos": None,
                "presupuestos": None,
                "razonamiento": None,
                "datos_origen": {"series": list(series_dict.keys())},
                "finalidad": finalidad,
                "paso_protocolo": None,
                "patron_match": iso_nombre,
                "isomorfismo": iso_info.get("isomorfismo", ""),
                "precedentes": iso_info.get("precedentes", []),
                "prescripcion": iso_info.get("prescripcion_historica", ""),
                "enlaces": None,
                "modelo_llm": modelo_llm,
                "coste_calculo": 0.0,
            })

    # 6. Escribir en Postgres via REST
    payload = {"resultados": batch}

    try:
        r = httpx.post(
            f"{SIMBIONTE_URL}/simbionte/escribir-batch",
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        resp = r.json()
        sesion_id = resp["sesion_id"]
        n_escritos = resp["n_escritos"]
    except Exception as e:
        # Fallback: devolver batch en memoria (para dev local sin fly.io)
        import uuid
        sesion_id = str(uuid.uuid4())
        n_escritos = len(batch)
        print(f"  [WARN] No se pudo escribir en Postgres ({e}). Batch en memoria: {n_escritos} resultados.")

    dt = time.time() - t0

    return {
        "sesion_id": sesion_id,
        "n_escritos": n_escritos,
        "n_formulas_calculadas": len(resultados),
        "n_patrones_detectados": sum(1 for b in batch if b["tipo"] == "patron"),
        "finalidad": finalidad,
        "dt": dt,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    rng = np.random.default_rng(77); t = np.arange(48)
    series = {
        'pib': list(300000*(1+0.008*t-0.0002*t**2)*(1+0.005*rng.standard_normal(48))),
        'inflacion': list(1.5+0.08*t+0.3*np.sin(2*np.pi*t/12)+0.2*rng.standard_normal(48)),
        'desempleo': list(7+0.05*t+0.3*rng.standard_normal(48)),
        'tipo_interes': list(0.5+0.03*t+0.1*rng.standard_normal(48)),
        'consumo': list(0.58*300000+200*rng.standard_normal(48)),
        'inversion': list(0.22*300000+150*rng.standard_normal(48)),
        'exportaciones': list(0.30*300000+100*rng.standard_normal(48)),
        'importaciones': list(0.32*300000+100*rng.standard_normal(48)),
        'deuda_pib': list(95+0.8*t+0.5*rng.standard_normal(48)),
    }

    print("=" * 60)
    print("SIMBIONTE WRITER — Calcula + Escribe en Postgres")
    print("=" * 60)

    result = calcular_y_escribir(
        series,
        "Que deberia hacer el banco central ante esta estanflacion?",
        modelo_llm="claude-sonnet-4-20250514"
    )

    print(f"\n  Sesion ID: {result['sesion_id']}")
    print(f"  Formulas calculadas: {result['n_formulas_calculadas']}")
    print(f"  Escritos en Postgres: {result['n_escritos']}")
    print(f"  Patrones detectados: {result['n_patrones_detectados']}")
    print(f"  Finalidad: {result['finalidad']}")
    print(f"  Tiempo: {result['dt']:.2f}s")
