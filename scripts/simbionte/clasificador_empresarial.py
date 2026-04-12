"""
Clasificador Funcional Empresarial — Base Tipo 6
Fecha: 2026-04-12

Convierte datos empresariales (CRM/ERP/dashboards) en secuencias de codigos funcionales.
Misma logica que clasificador_bursatil.py para mercado y clasificador_funcional.py para texto.
Cada metrica/departamento/trimestre recibe un codigo que representa su FUNCION en contexto.

Ref: BASE_TIPO_6_EMPRESARIAL.md

Niveles:
  N1: metricas individuales (cada calculo de formula = 1 token funcional)
  N2: departamentos (todas las metricas de 1 area funcional = 1 oracion)
  N3: trimestres (todos los departamentos en 1 trimestre = 1 parrafo)
  N4: empresa (todos los trimestres = el texto completo)

$0 total (datos sinteticos + compute local)
"""

import numpy as np
from collections import Counter


# ============================================================
# FORMULAS EMPRESARIALES → FUNCIONES SINTACTICAS (24 formulas)
# ============================================================

FORMULA_FUNCIONES = {
    "revenue":              0,   # Estado de ingresos
    "revenue_delta":        1,   # Cambio MoM de ingresos
    "arpu":                 2,   # Ingreso por usuario
    "ltv":                  3,   # Valor de vida del cliente
    "cac":                  4,   # Coste de adquisicion
    "ltv_cac":              5,   # Ratio valor/coste
    "churn":                6,   # Tasa de abandono
    "nrr":                  7,   # Retencion neta de revenue
    "conversion":           8,   # Tasa de conversion del funnel
    "pipeline":             9,   # Valor del pipeline comercial
    "ciclo_venta":          10,  # Tiempo medio de cierre
    "margen_bruto":         11,  # Rentabilidad directa
    "burn_rate":            12,  # Meses de runway restantes
    "cash_flow":            13,  # Flujo de caja operativo
    "nps":                  14,  # Net Promoter Score
    "actividad":            15,  # DAU/MAU ratio
    "tickets":              16,  # Volumen de soporte
    "concentracion":        17,  # % revenue en top 3 clientes
    "equipo_rotacion":      18,  # Rotacion anual del equipo
    "equipo_productividad": 19,  # Revenue por FTE
    "adoption":             20,  # Adopcion de features
    "time_to_value":        21,  # Dias hasta primer valor
    "payback":              22,  # Meses para recuperar CAC
    "expansion":            23,  # Expansion MRR %
}
N_FORMULAS = len(FORMULA_FUNCIONES)

# Cada resultado se clasifica en 5 niveles (quintiles)
N_NIVELES = 5
N_TOKENS_EMPRESA = N_FORMULAS * N_NIVELES  # 24 × 5 = 120 tipos posibles


# ============================================================
# GENERADOR DE DATOS SINTETICOS
# ============================================================

def generar_empresa(tipo="saas_growth", n_meses=12, seed=None):
    """Genera datos empresariales sinteticos realistas.

    Args:
        tipo: perfil de empresa
            - "saas_growth": SaaS en crecimiento (Series A/B)
            - "saas_mature": SaaS maduro (rentable, crecimiento moderado)
            - "saas_declining": SaaS en declive (churn alto, crecimiento negativo)
            - "smb_stable": PyME estable (margenes buenos, sin escala)
            - "startup_burn": Startup quemando cash (crecimiento agresivo)
            - "ecommerce": E-commerce (estacional, margenes bajos)
        n_meses: numero de meses a generar
        seed: semilla para reproducibilidad

    Returns:
        list[dict] — un dict por mes con todas las metricas
    """
    rng = np.random.default_rng(seed)

    # Perfiles base
    perfiles = {
        "saas_growth": {
            "mrr_base": 80_000, "mrr_growth": 0.08, "mrr_noise": 0.03,
            "churn_base": 0.025, "churn_noise": 0.005,
            "cac_base": 200, "cac_noise": 30,
            "arpu_base": 50, "arpu_noise": 5,
            "nps_base": 55, "nps_noise": 8,
            "conversion_base": 0.035, "conversion_noise": 0.008,
            "margen_base": 0.72, "margen_noise": 0.03,
            "equipo_base": 35, "equipo_growth": 0.05,
            "adoption_base": 0.55, "adoption_noise": 0.08,
            "concentracion_base": 0.25, "concentracion_noise": 0.05,
            "tickets_base": 80, "tickets_noise": 20,
        },
        "saas_mature": {
            "mrr_base": 500_000, "mrr_growth": 0.02, "mrr_noise": 0.01,
            "churn_base": 0.015, "churn_noise": 0.003,
            "cac_base": 350, "cac_noise": 40,
            "arpu_base": 120, "arpu_noise": 10,
            "nps_base": 68, "nps_noise": 5,
            "conversion_base": 0.028, "conversion_noise": 0.005,
            "margen_base": 0.78, "margen_noise": 0.02,
            "equipo_base": 120, "equipo_growth": 0.01,
            "adoption_base": 0.70, "adoption_noise": 0.05,
            "concentracion_base": 0.15, "concentracion_noise": 0.03,
            "tickets_base": 200, "tickets_noise": 30,
        },
        "saas_declining": {
            "mrr_base": 200_000, "mrr_growth": -0.03, "mrr_noise": 0.02,
            "churn_base": 0.055, "churn_noise": 0.01,
            "cac_base": 400, "cac_noise": 60,
            "arpu_base": 65, "arpu_noise": 8,
            "nps_base": 32, "nps_noise": 10,
            "conversion_base": 0.018, "conversion_noise": 0.005,
            "margen_base": 0.58, "margen_noise": 0.05,
            "equipo_base": 80, "equipo_growth": -0.02,
            "adoption_base": 0.35, "adoption_noise": 0.10,
            "concentracion_base": 0.45, "concentracion_noise": 0.08,
            "tickets_base": 300, "tickets_noise": 50,
        },
        "smb_stable": {
            "mrr_base": 25_000, "mrr_growth": 0.01, "mrr_noise": 0.02,
            "churn_base": 0.02, "churn_noise": 0.005,
            "cac_base": 100, "cac_noise": 20,
            "arpu_base": 80, "arpu_noise": 10,
            "nps_base": 62, "nps_noise": 6,
            "conversion_base": 0.045, "conversion_noise": 0.01,
            "margen_base": 0.65, "margen_noise": 0.04,
            "equipo_base": 8, "equipo_growth": 0.0,
            "adoption_base": 0.60, "adoption_noise": 0.07,
            "concentracion_base": 0.35, "concentracion_noise": 0.06,
            "tickets_base": 15, "tickets_noise": 5,
        },
        "startup_burn": {
            "mrr_base": 15_000, "mrr_growth": 0.15, "mrr_noise": 0.06,
            "churn_base": 0.04, "churn_noise": 0.01,
            "cac_base": 500, "cac_noise": 100,
            "arpu_base": 35, "arpu_noise": 8,
            "nps_base": 45, "nps_noise": 12,
            "conversion_base": 0.025, "conversion_noise": 0.008,
            "margen_base": 0.50, "margen_noise": 0.08,
            "equipo_base": 12, "equipo_growth": 0.08,
            "adoption_base": 0.40, "adoption_noise": 0.12,
            "concentracion_base": 0.30, "concentracion_noise": 0.08,
            "tickets_base": 40, "tickets_noise": 15,
        },
        "ecommerce": {
            "mrr_base": 150_000, "mrr_growth": 0.03, "mrr_noise": 0.05,
            "churn_base": 0.08, "churn_noise": 0.02,
            "cac_base": 25, "cac_noise": 8,
            "arpu_base": 45, "arpu_noise": 15,
            "nps_base": 40, "nps_noise": 10,
            "conversion_base": 0.022, "conversion_noise": 0.006,
            "margen_base": 0.35, "margen_noise": 0.05,
            "equipo_base": 20, "equipo_growth": 0.02,
            "adoption_base": 0.50, "adoption_noise": 0.10,
            "concentracion_base": 0.10, "concentracion_noise": 0.03,
            "tickets_base": 150, "tickets_noise": 40,
        },
    }

    p = perfiles.get(tipo, perfiles["saas_growth"])
    meses = []

    mrr = p["mrr_base"]
    equipo = p["equipo_base"]
    cash = mrr * 8  # 8 meses de cash inicial

    for m in range(n_meses):
        # Estacionalidad (Q4 mas fuerte, Q1 mas debil)
        estacionalidad = 1.0 + 0.05 * np.sin(2 * np.pi * (m - 3) / 12)

        # Revenue con tendencia + ruido + estacionalidad
        mrr_growth_actual = p["mrr_growth"] + rng.normal(0, p["mrr_noise"])
        mrr = mrr * (1 + mrr_growth_actual) * estacionalidad
        mrr = max(mrr, 1000)  # floor

        # Clientes (derivado de MRR/ARPU)
        arpu = max(p["arpu_base"] + rng.normal(0, p["arpu_noise"]), 5)
        n_clientes = max(int(mrr / arpu), 10)

        # Churn
        churn = max(p["churn_base"] + rng.normal(0, p["churn_noise"]), 0.001)

        # CAC
        cac = max(p["cac_base"] + rng.normal(0, p["cac_noise"]), 10)

        # LTV = ARPU / churn
        ltv = arpu / max(churn, 0.001)

        # Nuevos clientes este mes
        nuevos = max(int(n_clientes * (mrr_growth_actual + churn)), 0)
        gasto_adquisicion = nuevos * cac

        # Conversion
        leads = int(nuevos / max(p["conversion_base"] + rng.normal(0, p["conversion_noise"]), 0.005))
        conversion = nuevos / max(leads, 1)

        # Pipeline (3x revenue objetivo)
        pipeline = mrr * 3 * (1 + rng.normal(0, 0.2))

        # Ciclo de venta (dias)
        ciclo_venta = max(15 + rng.normal(0, 5) + (cac / 50), 5)

        # Margen bruto
        margen = min(max(p["margen_base"] + rng.normal(0, p["margen_noise"]), 0.1), 0.95)

        # Equipo
        equipo = max(int(equipo * (1 + p["equipo_growth"])), 3)
        rotacion = max(0.05 + rng.normal(0, 0.02), 0.0)
        productividad = (mrr * 12) / max(equipo, 1)

        # Cash flow
        gastos_ops = mrr * (1 - margen) + gasto_adquisicion + equipo * 4000
        cash_flow = mrr - gastos_ops
        cash += cash_flow
        burn_rate = max(cash / max(-cash_flow, 1), 0) if cash_flow < 0 else 999

        # NPS
        nps = min(max(p["nps_base"] + rng.normal(0, p["nps_noise"]), -100), 100)

        # Actividad (DAU/MAU proxy)
        actividad = min(max(0.3 + rng.normal(0, 0.08), 0.05), 0.90)

        # Tickets
        tickets = max(int(p["tickets_base"] + rng.normal(0, p["tickets_noise"])), 0)

        # Concentracion
        concentracion = min(max(p["concentracion_base"] + rng.normal(0, p["concentracion_noise"]), 0.05), 0.90)

        # Producto
        adoption = min(max(p["adoption_base"] + rng.normal(0, p["adoption_noise"]), 0.05), 0.95)
        ttv = max(2 + rng.normal(0, 1), 0.5)  # dias
        payback = max(cac / max(arpu, 1), 1)  # meses

        # NRR (Net Revenue Retention)
        expansion_pct = max(0.02 + rng.normal(0, 0.01), 0)
        nrr = (1 - churn + expansion_pct)

        mes = {
            "mes": m + 1,
            "revenue": round(mrr, 2),
            "revenue_delta": round(mrr_growth_actual, 4),
            "arpu": round(arpu, 2),
            "ltv": round(ltv, 2),
            "cac": round(cac, 2),
            "ltv_cac": round(ltv / max(cac, 1), 2),
            "churn": round(churn, 4),
            "nrr": round(nrr, 4),
            "conversion": round(conversion, 4),
            "pipeline": round(pipeline, 2),
            "ciclo_venta": round(ciclo_venta, 1),
            "margen_bruto": round(margen, 4),
            "burn_rate": round(min(burn_rate, 999), 1),
            "cash_flow": round(cash_flow, 2),
            "nps": round(nps, 1),
            "actividad": round(actividad, 4),
            "tickets": tickets,
            "concentracion": round(concentracion, 4),
            "equipo_rotacion": round(rotacion, 4),
            "equipo_productividad": round(productividad, 2),
            "adoption": round(adoption, 4),
            "time_to_value": round(ttv, 1),
            "payback": round(payback, 1),
            "expansion": round(expansion_pct, 4),
            # Metadata
            "_n_clientes": n_clientes,
            "_equipo": equipo,
            "_cash": round(cash, 2),
            "_nuevos": nuevos,
            "_leads": leads,
        }
        meses.append(mes)

    return meses


# ============================================================
# FORMULAS → SECUENCIA FUNCIONAL
# ============================================================

# Percentiles de referencia por tipo de empresa (SaaS mediano)
PERCENTILES_DEFAULT = {
    "revenue":              [30_000, 80_000, 200_000, 500_000],
    "revenue_delta":        [-0.02, 0.02, 0.06, 0.12],
    "arpu":                 [25, 50, 80, 150],
    "ltv":                  [500, 1500, 3000, 6000],
    "cac":                  [50, 150, 300, 500],
    "ltv_cac":              [1.5, 3.0, 5.0, 8.0],
    "churn":                [0.01, 0.02, 0.04, 0.07],  # invertido: bajo = bueno
    "nrr":                  [0.90, 0.98, 1.05, 1.15],
    "conversion":           [0.01, 0.025, 0.04, 0.06],
    "pipeline":             [50_000, 150_000, 400_000, 1_000_000],
    "ciclo_venta":          [10, 20, 35, 60],  # invertido: bajo = bueno
    "margen_bruto":         [0.40, 0.55, 0.70, 0.80],
    "burn_rate":            [6, 12, 18, 36],
    "cash_flow":            [-50_000, 0, 20_000, 80_000],
    "nps":                  [20, 40, 55, 70],
    "actividad":            [0.15, 0.25, 0.40, 0.55],
    "tickets":              [20, 60, 120, 250],  # invertido: bajo = bueno
    "concentracion":        [0.10, 0.20, 0.30, 0.45],  # invertido: bajo = bueno
    "equipo_rotacion":      [0.03, 0.06, 0.10, 0.18],  # invertido: bajo = bueno
    "equipo_productividad": [80_000, 120_000, 180_000, 300_000],
    "adoption":             [0.25, 0.40, 0.55, 0.70],
    "time_to_value":        [1, 3, 7, 14],  # invertido: bajo = bueno
    "payback":              [2, 5, 8, 14],   # invertido: bajo = bueno
    "expansion":            [0.0, 0.02, 0.05, 0.10],
}


def formulas_a_secuencia(datos_mes, percentiles_ref=None):
    """Convierte metricas de un mes en secuencia de codigos funcionales.

    Cada metrica se clasifica en 5 niveles (quintiles).
    Codigo final = formula_idx × 5 + nivel (0-119)

    Args:
        datos_mes: dict con las 24 metricas
        percentiles_ref: dict {nombre: [p20, p40, p60, p80]}

    Returns:
        list[int] — secuencia de codigos funcionales
    """
    if percentiles_ref is None:
        percentiles_ref = PERCENTILES_DEFAULT

    seq = []
    for formula_name, formula_idx in FORMULA_FUNCIONES.items():
        valor = datos_mes.get(formula_name, 0.0)
        if valor is None:
            valor = 0.0
        thresholds = percentiles_ref.get(formula_name, [0, 0, 0, 0])

        # Clasificar en quintil
        if valor <= thresholds[0]:
            nivel = 0  # muy bajo
        elif valor <= thresholds[1]:
            nivel = 1  # bajo
        elif valor <= thresholds[2]:
            nivel = 2  # normal
        elif valor <= thresholds[3]:
            nivel = 3  # alto
        else:
            nivel = 4  # muy alto

        codigo = formula_idx * N_NIVELES + nivel
        seq.append(codigo)

    return seq


# ============================================================
# CLASIFICADORES DE NIVEL (N2, N3, N4)
# ============================================================

TIPO_DEPARTAMENTO = {
    "motor_crecimiento":     0,
    "maquina_retencion":     1,
    "fabrica_eficiencia":    2,
    "laboratorio":           3,
    "tesoreria":             4,
    "en_crisis":             5,
    "en_transicion":         6,
    "estable":               7,
}
N_TIPO_DEPARTAMENTO = 8
DEPARTAMENTO_NAMES = list(TIPO_DEPARTAMENTO.keys())


def clasificar_departamento(datos_mes):
    """Clasifica el perfil de un mes por su funcion dominante."""
    rev_d = datos_mes.get("revenue_delta", 0)
    churn = datos_mes.get("churn", 0.03)
    margen = datos_mes.get("margen_bruto", 0.5)
    nps = datos_mes.get("nps", 50)
    adoption = datos_mes.get("adoption", 0.5)
    cash_flow = datos_mes.get("cash_flow", 0)
    burn = datos_mes.get("burn_rate", 999)

    # Crisis: multiples metricas rojas
    n_rojas = sum([
        rev_d < -0.03,
        churn > 0.06,
        margen < 0.30,
        nps < 20,
        burn < 6,
    ])
    if n_rojas >= 3:
        return "en_crisis"

    # Transicion: mezcla fuerte
    n_verdes = sum([
        rev_d > 0.05,
        churn < 0.02,
        margen > 0.70,
        nps > 60,
    ])
    if n_rojas >= 1 and n_verdes >= 2:
        return "en_transicion"

    # Motor de crecimiento
    if rev_d > 0.06 and datos_mes.get("conversion", 0) > 0.03:
        return "motor_crecimiento"

    # Maquina de retencion
    if churn < 0.02 and nps > 55:
        return "maquina_retencion"

    # Fabrica de eficiencia
    if margen > 0.70 and datos_mes.get("equipo_productividad", 0) > 150_000:
        return "fabrica_eficiencia"

    # Laboratorio
    if adoption > 0.60 and datos_mes.get("expansion", 0) > 0.04:
        return "laboratorio"

    # Tesoreria
    if cash_flow > 0 and burn > 24:
        return "tesoreria"

    return "estable"


TIPO_TRIMESTRE = {
    "expansion":       0,
    "contraccion":     1,
    "optimizacion":    2,
    "inversion":       3,
    "estancamiento":   4,
}
N_TIPO_TRIMESTRE = 5
TRIMESTRE_NAMES = list(TIPO_TRIMESTRE.keys())


def clasificar_trimestre(meses_q):
    """Clasifica un trimestre (3 meses) por su dinamica."""
    if len(meses_q) < 2:
        return "estancamiento"

    rev_inicio = meses_q[0].get("revenue", 0)
    rev_fin = meses_q[-1].get("revenue", 0)
    cambio_rev = (rev_fin - rev_inicio) / max(rev_inicio, 1)

    margen_medio = np.mean([m.get("margen_bruto", 0.5) for m in meses_q])
    churn_medio = np.mean([m.get("churn", 0.03) for m in meses_q])
    burn_medio = np.mean([m.get("burn_rate", 999) for m in meses_q])

    # Expansion: revenue creciendo + metricas saludables
    if cambio_rev > 0.05 and churn_medio < 0.04:
        return "expansion"

    # Contraccion: revenue cayendo + churn subiendo
    if cambio_rev < -0.02 or churn_medio > 0.05:
        return "contraccion"

    # Inversion: burn alto + crecimiento alto
    if burn_medio < 12 and cambio_rev > 0.08:
        return "inversion"

    # Optimizacion: revenue plano + margenes mejorando
    margen_trend = meses_q[-1].get("margen_bruto", 0.5) - meses_q[0].get("margen_bruto", 0.5)
    if abs(cambio_rev) < 0.03 and margen_trend > 0.02:
        return "optimizacion"

    return "estancamiento"


TIPO_CICLO = {
    "crecimiento":    0,
    "declive":        1,
    "estabilidad":    2,
    "transformacion": 3,
}
N_TIPO_CICLO = 4
CICLO_NAMES = list(TIPO_CICLO.keys())


def clasificar_ciclo(seq_trimestres):
    """Clasifica el ciclo empresarial segun secuencia de trimestres."""
    if len(seq_trimestres) < 2:
        return "estabilidad"

    expansiones = sum(1 for t in seq_trimestres if t == 0)  # expansion
    contracciones = sum(1 for t in seq_trimestres if t == 1)  # contraccion
    total = len(seq_trimestres)

    if expansiones / total > 0.5:
        return "crecimiento"
    if contracciones / total > 0.5:
        return "declive"
    if expansiones > 0 and contracciones > 0:
        return "transformacion"
    return "estabilidad"


# ============================================================
# PIPELINE COMPLETO: Datos empresa → Secuencias funcionales 4 niveles
# ============================================================

def procesar_empresa(meses, percentiles_ref=None):
    """Convierte datos mensuales de empresa en secuencias funcionales de 4 niveles.

    Args:
        meses: list[dict] — un dict por mes con las 24 metricas
        percentiles_ref: dict {nombre: [p20, p40, p60, p80]}

    Returns:
        dict con seq_n1, seq_n2, seq_n3, seq_n4 + metadata
    """
    if len(meses) < 3:
        return None

    # === N1: Metricas individuales ===
    seq_n1 = []
    for mes in meses:
        seq_mes = formulas_a_secuencia(mes, percentiles_ref)
        seq_n1.extend(seq_mes)

    # === N2: Cada mes = 1 tipo de departamento ===
    seq_n2 = []
    for mes in meses:
        tipo = clasificar_departamento(mes)
        seq_n2.append(TIPO_DEPARTAMENTO[tipo])

    # === N3: Cada trimestre = 1 tipo ===
    seq_n3 = []
    for i in range(0, len(meses) - 2, 3):
        q = meses[i:i+3]
        tipo = clasificar_trimestre(q)
        seq_n3.append(TIPO_TRIMESTRE[tipo])

    if not seq_n3:
        seq_n3 = [TIPO_TRIMESTRE["estancamiento"]]

    # === N4: Ciclo completo ===
    tipo_ciclo = clasificar_ciclo(seq_n3)
    # Dividir en tercios para tener secuencia
    n = max(len(seq_n3), 1)
    tercio = max(n // 3, 1)
    seq_n4 = []
    for start in [0, tercio, 2 * tercio]:
        chunk = seq_n3[start:start + tercio]
        if chunk:
            seq_n4.append(TIPO_CICLO[clasificar_ciclo(chunk)])
        else:
            seq_n4.append(TIPO_CICLO["estabilidad"])

    return {
        "seq_n1": seq_n1,
        "seq_n2": seq_n2,
        "seq_n3": seq_n3,
        "seq_n4": seq_n4,
        "n_tipos": {
            "N1": N_TOKENS_EMPRESA,
            "N2": N_TIPO_DEPARTAMENTO,
            "N3": N_TIPO_TRIMESTRE,
            "N4": N_TIPO_CICLO,
        },
        "metadata": {
            "n_meses": len(meses),
            "n_metricas_total": len(seq_n1),
            "n_trimestres": len(seq_n3),
            "ciclo": tipo_ciclo,
            "rev_inicio": meses[0].get("revenue", 0),
            "rev_fin": meses[-1].get("revenue", 0),
            "churn_medio": round(np.mean([m.get("churn", 0) for m in meses]), 4),
        },
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CLASIFICADOR EMPRESARIAL — Base Tipo 6")
    print("=" * 60)

    tipos = ["saas_growth", "saas_mature", "saas_declining", "smb_stable", "startup_burn", "ecommerce"]

    for tipo in tipos:
        print(f"\n--- {tipo.upper()} ---")
        meses = generar_empresa(tipo, n_meses=12, seed=42)
        result = procesar_empresa(meses)

        if result:
            print(f"  N1 (metricas): {len(result['seq_n1'])} tokens ({result['metadata']['n_meses']} meses × {N_FORMULAS} formulas)")
            print(f"  N2 (meses):    {len(result['seq_n2'])} → tipos: {dict(Counter(result['seq_n2']))}")
            print(f"  N3 (trimestres): {len(result['seq_n3'])} → tipos: {dict(Counter(result['seq_n3']))}")
            print(f"  N4 (ciclo):    {result['seq_n4']}")
            print(f"  Ciclo: {result['metadata']['ciclo']}")
            print(f"  Revenue: ${result['metadata']['rev_inicio']:,.0f} → ${result['metadata']['rev_fin']:,.0f}")
            print(f"  Churn medio: {result['metadata']['churn_medio']:.2%}")

            # Nombres de tipos para N2
            dept_names = {v: k for k, v in TIPO_DEPARTAMENTO.items()}
            print(f"  Perfil mensual: {[dept_names[t] for t in result['seq_n2']]}")
