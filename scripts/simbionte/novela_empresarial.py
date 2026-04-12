"""
Novela Empresarial — Cada metrica = un adjetivo, cada mes = una oracion,
cada trimestre = un parrafo, cada empresa = un capitulo, el portfolio = la novela.

Fecha: 2026-04-12

Pipeline:
  1. Generar/cargar datos de N empresas × M meses × K formulas
  2. Cada formula produce un adjetivo funcional (que funcion cumple el resultado)
  3. Secuenciar adjetivos como "texto empresarial"
  4. Aplicar 10 marcos × 4 niveles → geometria
  5. Decodificar → LLM

Niveles de la novela (portfolio de empresas):
  N1: metricas individuales de TODAS las empresas (cada calculo = 1 token funcional)
  N2: cada empresa-mes = 1 tipo de departamento (1 oracion)
  N3: cada sector/segmento de empresas = 1 parrafo
  N4: el portfolio completo como secuencia de movimientos

$0 total (datos sinteticos + compute local)
"""

import sys
import os
import time
import json
import numpy as np
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from marcos_matematicos import calcular_10_ejes, FEATURES_POR_NIVEL
from geometria_isomorfismo import calcular_geometria_completa
from clasificador_empresarial import (
    generar_empresa, procesar_empresa, formulas_a_secuencia,
    clasificar_departamento, clasificar_trimestre, clasificar_ciclo,
    FORMULA_FUNCIONES, N_FORMULAS, N_TOKENS_EMPRESA, N_NIVELES,
    TIPO_DEPARTAMENTO, N_TIPO_DEPARTAMENTO, DEPARTAMENTO_NAMES,
    TIPO_TRIMESTRE, N_TIPO_TRIMESTRE, TRIMESTRE_NAMES,
    TIPO_CICLO, N_TIPO_CICLO, CICLO_NAMES,
    PERCENTILES_DEFAULT,
)


# ============================================================
# PORTFOLIO DE EMPRESAS (equivalente a SECTORES en novela_financiera)
# ============================================================

PORTFOLIO = {
    "saas_early": {
        "tipo": "startup_burn",
        "n_empresas": 5,
        "descripcion": "SaaS early stage quemando cash",
    },
    "saas_growth": {
        "tipo": "saas_growth",
        "n_empresas": 8,
        "descripcion": "SaaS en crecimiento (Series A/B)",
    },
    "saas_mature": {
        "tipo": "saas_mature",
        "n_empresas": 5,
        "descripcion": "SaaS rentables y maduros",
    },
    "saas_declining": {
        "tipo": "saas_declining",
        "n_empresas": 3,
        "descripcion": "SaaS en declive",
    },
    "smb": {
        "tipo": "smb_stable",
        "n_empresas": 6,
        "descripcion": "PyMEs estables",
    },
    "ecommerce": {
        "tipo": "ecommerce",
        "n_empresas": 4,
        "descripcion": "E-commerce (estacional, margenes bajos)",
    },
}


def construir_novela(n_meses=12):
    """Construye la novela empresarial completa.

    Genera un portfolio de empresas sinteticas, calcula formulas,
    y aplica 10 marcos × 4 niveles + geometria.

    Args:
        n_meses: meses de historia por empresa

    Returns:
        (resumen_dict, geometria_dict)
    """
    print(f"{'='*60}")
    print(f"NOVELA EMPRESARIAL — {n_meses} meses")
    print(f"{'='*60}")

    # === GENERAR EMPRESAS ===
    empresas = {}
    empresa_sector = {}
    empresa_id = 0

    for sector, config in PORTFOLIO.items():
        for i in range(config["n_empresas"]):
            nombre = f"{sector}_{i+1}"
            seed = hash(nombre) % (2**31)
            datos = generar_empresa(config["tipo"], n_meses=n_meses, seed=seed)
            empresas[nombre] = datos
            empresa_sector[nombre] = sector
            empresa_id += 1

    n_total = len(empresas)
    print(f"\n  Portfolio: {n_total} empresas × {n_meses} meses = {n_total * n_meses} empresa-meses")
    for sector, config in PORTFOLIO.items():
        print(f"    {sector:<16s}: {config['n_empresas']} empresas ({config['descripcion']})")

    # === CALCULAR PERCENTILES REALES DEL PORTFOLIO ===
    print(f"\nCalculando percentiles de referencia del portfolio...")
    all_vals = defaultdict(list)
    for nombre, meses in empresas.items():
        for mes in meses:
            for formula_name in FORMULA_FUNCIONES.keys():
                val = mes.get(formula_name)
                if val is not None and np.isfinite(val):
                    all_vals[formula_name].append(val)

    percentiles_ref = {}
    for name, vals in all_vals.items():
        if vals:
            percentiles_ref[name] = [
                float(np.percentile(vals, 20)),
                float(np.percentile(vals, 40)),
                float(np.percentile(vals, 60)),
                float(np.percentile(vals, 80)),
            ]

    print(f"  Percentiles calculados sobre {sum(len(v) for v in all_vals.values())} datapoints")

    # === PROCESAR CADA EMPRESA ===
    print(f"\nProcesando empresas...")
    resultados = {}
    for nombre, meses in empresas.items():
        result = procesar_empresa(meses, percentiles_ref)
        if result:
            resultados[nombre] = result

    print(f"  {len(resultados)}/{n_total} empresas procesadas")

    # === CONSTRUIR LA NOVELA (4 NIVELES) ===
    print(f"\n{'='*60}")
    print(f"CONSTRUYENDO NOVELA (4 niveles)")
    print(f"{'='*60}")

    # N1: Todos los tokens de todas las empresas (secuencia plana)
    seq_n1 = []
    for nombre in sorted(resultados.keys()):
        seq_n1.extend(resultados[nombre]["seq_n1"])
    print(f"  N1 (metricas): {len(seq_n1)} tokens funcionales")

    # N2: Cada empresa-mes = 1 tipo de departamento
    seq_n2 = []
    empresa_perfiles = {}
    for nombre in sorted(resultados.keys()):
        seq_n2.extend(resultados[nombre]["seq_n2"])
        # Perfil dominante de la empresa
        tipos = resultados[nombre]["seq_n2"]
        moda = Counter(tipos).most_common(1)[0][0]
        empresa_perfiles[nombre] = moda
    print(f"  N2 (empresa-meses): {len(seq_n2)} → tipos: {dict(Counter(seq_n2))}")

    # N3: Cada sector = 1 tipo (basado en el perfil dominante de sus empresas)
    def clasificar_segmento(nombres_empresas, perfiles):
        """Clasifica un segmento de empresas por su perfil dominante."""
        tipos = [perfiles.get(n, 7) for n in nombres_empresas if n in perfiles]
        if not tipos:
            return 4  # estancamiento
        moda = Counter(tipos).most_common(1)[0][0]
        # Mapear tipo departamento → tipo trimestre
        if moda in (0, 3):   # motor_crecimiento, laboratorio
            return 0  # expansion
        elif moda in (5,):   # en_crisis
            return 1  # contraccion
        elif moda in (2, 4): # fabrica_eficiencia, tesoreria
            return 2  # optimizacion
        elif moda in (6,):   # en_transicion
            return 3  # inversion
        else:
            return 4  # estancamiento

    seq_n3 = []
    sector_tipos = {}
    for sector, config in PORTFOLIO.items():
        nombres = [f"{sector}_{i+1}" for i in range(config["n_empresas"])]
        tipo = clasificar_segmento(nombres, empresa_perfiles)
        seq_n3.append(tipo)
        sector_tipos[sector] = tipo
    print(f"  N3 (sectores): {len(seq_n3)} → tipos: {dict(Counter(seq_n3))}")

    # N4: Portfolio como secuencia (dividido en tercios temporales)
    # Usar metricas agregadas del portfolio por tercio temporal
    all_meses = []
    for nombre in sorted(resultados.keys()):
        all_meses.append(empresas[nombre])

    # Agregar revenue por tercio
    tercio = max(n_meses // 3, 1)
    seq_n4 = []
    for t in range(3):
        start = t * tercio
        end = min(start + tercio, n_meses)
        rev_sum_start = sum(e[start].get("revenue", 0) for e in all_meses if len(e) > start)
        rev_sum_end = sum(e[min(end-1, len(e)-1)].get("revenue", 0) for e in all_meses)
        cambio = (rev_sum_end - rev_sum_start) / max(rev_sum_start, 1)
        if cambio > 0.05:
            seq_n4.append(0)  # crecimiento
        elif cambio < -0.03:
            seq_n4.append(1)  # declive
        elif abs(cambio) < 0.02:
            seq_n4.append(2)  # estabilidad
        else:
            seq_n4.append(3)  # transformacion
    print(f"  N4 (portfolio): {seq_n4} → {[CICLO_NAMES[t] for t in seq_n4]}")

    # === 10 MARCOS × 4 NIVELES ===
    print(f"\nCalculando 10 marcos × 4 niveles...")
    t0 = time.time()
    v_n1 = calcular_10_ejes(seq_n1, N_TOKENS_EMPRESA)
    v_n2 = calcular_10_ejes(seq_n2, N_TIPO_DEPARTAMENTO)
    v_n3 = calcular_10_ejes(seq_n3, N_TIPO_TRIMESTRE)
    v_n4 = calcular_10_ejes(seq_n4, N_TIPO_CICLO)
    dt = time.time() - t0
    print(f"  Vector: {FEATURES_POR_NIVEL * 4}D en {dt*1000:.0f}ms")

    # === GEOMETRIA ===
    vectores = {"N1": v_n1, "N2": v_n2, "N3": v_n3, "N4": v_n4}
    geo = calcular_geometria_completa(vectores)
    print(f"  Geometria: {geo['n_features']}D")
    print(f"  Profundidad: {geo['profundidad_patron']}")

    # === LECTURA DE LA NOVELA ===
    print(f"\n{'='*60}")
    print(f"LECTURA DE LA NOVELA EMPRESARIAL")
    print(f"{'='*60}")

    for nivel in ["N1", "N2", "N3", "N4"]:
        g = geo["geometrias"][nivel]
        dom = g["forma"]["dominantes"]
        sym = g["forma"]["simetria"]
        coh = g["forma"]["coherencia"]
        print(f"\n  {nivel}:")
        if dom:
            print(f"    Dominantes: {dom}")
        print(f"    Simetria: {sym:.3f} | Coherencia: {coh:.3f}")

    for pair, s in geo["similaridades"].items():
        print(f"  {pair}: homomorfismo={s['homomorfismo']:.3f}")

    # Resumen por sector
    print(f"\n  POR SECTOR:")
    dept_names = {v: k for k, v in TIPO_DEPARTAMENTO.items()}
    trim_names = {v: k for k, v in TIPO_TRIMESTRE.items()}
    for sector, config in PORTFOLIO.items():
        nombres = [f"{sector}_{i+1}" for i in range(config["n_empresas"])]
        sector_empresas = {n: empresas[n] for n in nombres if n in empresas}
        if not sector_empresas:
            continue

        # Metricas agregadas del ultimo mes
        ultimos = [e[-1] for e in sector_empresas.values()]
        rev_medio = np.mean([m.get("revenue", 0) for m in ultimos])
        churn_medio = np.mean([m.get("churn", 0) for m in ultimos])
        ltv_cac = np.mean([m.get("ltv_cac", 0) for m in ultimos])
        nps_medio = np.mean([m.get("nps", 0) for m in ultimos])
        margen_medio = np.mean([m.get("margen_bruto", 0) for m in ultimos])

        tipo_sector = trim_names.get(sector_tipos.get(sector, 4), "?")
        perfiles = [dept_names.get(empresa_perfiles.get(n, 7), "?") for n in nombres if n in empresa_perfiles]
        perfil_moda = Counter(perfiles).most_common(1)[0][0] if perfiles else "?"

        print(f"    {sector:<16s}: rev=${rev_medio:,.0f} churn={churn_medio:.1%} LTV/CAC={ltv_cac:.1f} "
              f"NPS={nps_medio:.0f} margen={margen_medio:.0%} tipo={tipo_sector} perfil={perfil_moda} n={len(sector_empresas)}")

    # === POR EMPRESA (top 5 + bottom 5) ===
    print(f"\n  TOP 5 empresas (por LTV/CAC):")
    empresa_ltv_cac = {
        n: empresas[n][-1].get("ltv_cac", 0)
        for n in resultados.keys()
    }
    sorted_empresas = sorted(empresa_ltv_cac.items(), key=lambda x: x[1], reverse=True)
    for nombre, ltv_cac in sorted_empresas[:5]:
        ult = empresas[nombre][-1]
        perfil = dept_names.get(empresa_perfiles.get(nombre, 7), "?")
        print(f"    {nombre:<20s}: LTV/CAC={ltv_cac:.1f} rev=${ult['revenue']:,.0f} "
              f"churn={ult['churn']:.1%} perfil={perfil}")

    print(f"\n  BOTTOM 5 empresas (por LTV/CAC):")
    for nombre, ltv_cac in sorted_empresas[-5:]:
        ult = empresas[nombre][-1]
        perfil = dept_names.get(empresa_perfiles.get(nombre, 7), "?")
        print(f"    {nombre:<20s}: LTV/CAC={ltv_cac:.1f} rev=${ult['revenue']:,.0f} "
              f"churn={ult['churn']:.1%} perfil={perfil}")

    # === GUARDAR ===
    save = {
        "version": "novela_empresarial_v1",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "n_meses": n_meses,
        "n_empresas": len(resultados),
        "n_formulas": N_FORMULAS,
        "profundidad": geo["profundidad_patron"],
        "dominantes": {
            nivel: geo["geometrias"][nivel]["forma"]["dominantes"]
            for nivel in ["N1", "N2", "N3", "N4"]
        },
        "sectores": {
            sector: {
                "n": config["n_empresas"],
                "tipo_base": config["tipo"],
                "tipo_detectado": trim_names.get(sector_tipos.get(sector, 4), "?"),
                "rev_medio": float(np.mean([empresas[f"{sector}_{i+1}"][-1].get("revenue", 0)
                    for i in range(config["n_empresas"])
                    if f"{sector}_{i+1}" in empresas])),
            }
            for sector, config in PORTFOLIO.items()
        },
        "seq_n4": seq_n4,
        "percentiles_ref": percentiles_ref,
    }

    path = os.path.join(os.path.dirname(__file__), "../../data/novela_empresarial.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(save, f, ensure_ascii=False, indent=2)
    print(f"\n  Guardado en {path}")

    # Vector para pgvector
    vector_total = np.concatenate([v_n1, v_n2, v_n3, v_n4, geo["vector_pgvector"]])
    vpath = path.replace(".json", "_vector.npy")
    np.save(vpath, vector_total)
    print(f"  Vector: {vpath} ({len(vector_total)}D)")

    total_datapoints = n_total * n_meses * N_FORMULAS
    print(f"\n  TOTAL: {total_datapoints:,} datapoints procesados, $0")

    return save, geo


if __name__ == "__main__":
    novela, geo = construir_novela(n_meses=12)
