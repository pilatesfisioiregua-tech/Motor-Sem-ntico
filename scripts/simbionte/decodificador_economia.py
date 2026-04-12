"""
Decodificador Económico — Ejecuta fórmulas + decodifica gramática para LLM.

Fecha: 2026-04-12

El Simbionte:
  1. Recibe datos económicos (series temporales)
  2. Ejecuta CADA fórmula del catálogo sobre los datos
  3. Para cada resultado, decodifica:
     a) El VALOR numérico
     b) La GRAMÁTICA (secuencia de operaciones primitivas)
     c) La LECTURA como oración
     d) El TIPO DE ADJETIVO que produce
  4. Inyecta todo en prompt caching para que el LLM piense sobre ello

El LLM no ve "varianza=0.034" — ve:
  "ACUMULAR→NORMALIZAR→COMPARAR→TRANSFORMAR→ACUMULAR→NORMALIZAR
   = cuánta dispersión por punto = 0.034 = dispersión baja"

Y puede razonar: "esta variable tiene la misma gramática que el output gap
(COMPARAR→NORMALIZAR), así que su dispersión se interpreta como distancia al potencial"

$0 total (compute local)
"""

import numpy as np
from collections import Counter, defaultdict

from clasificador_economia import (
    calcular_formulas_economia, TIPOS_FUNCIONALES, N_TIPOS
)
from gramatica_formulas import (
    FORMULAS, OPS, OPS_TEXTO, OPS_ROL, N_OPS,
    formula_a_secuencia, detectar_isomorfismos, decodificar_formula,
)


# ============================================================
# NIVELES PARA CADA TIPO FUNCIONAL
# ============================================================

NIVELES_TEXTO = {
    0: "muy bajo",
    1: "bajo",
    2: "normal",
    3: "alto",
    4: "muy alto",
}


def clasificar_nivel(valor, tipo):
    """Clasifica un valor en 5 niveles según su tipo funcional."""
    abs_val = abs(valor)

    # Umbrales específicos por tipo
    if tipo in ("tasa_cambio", "tasa_crecimiento", "aceleracion"):
        if abs_val < 0.005: return 0, "estancado"
        if abs_val < 0.02: return 1, "lento"
        if abs_val < 0.05: return 2, "moderado"
        if abs_val < 0.10: return 3, "rápido"
        return 4, "acelerado"

    elif tipo in ("elasticidad", "sensibilidad"):
        if abs_val < 0.2: return 0, "inelástico (insensible)"
        if abs_val < 0.5: return 1, "poco elástico"
        if abs_val < 1.0: return 2, "elástico unitario"
        if abs_val < 2.0: return 3, "elástico"
        return 4, "muy elástico (hipersensible)"

    elif tipo in ("correlacion",):
        if abs_val < 0.1: return 0, "sin relación"
        if abs_val < 0.3: return 1, "relación débil"
        if abs_val < 0.6: return 2, "relación moderada"
        if abs_val < 0.8: return 3, "relación fuerte"
        return 4, "relación muy fuerte"

    elif tipo in ("concentracion",):
        if abs_val < 0.2: return 0, "muy igualitario"
        if abs_val < 0.35: return 1, "moderadamente igualitario"
        if abs_val < 0.45: return 2, "desigualdad media"
        if abs_val < 0.60: return 3, "desigual"
        return 4, "muy desigual"

    elif tipo in ("ratio", "share", "margen"):
        if abs_val < 0.1: return 0, "mínimo"
        if abs_val < 0.3: return 1, "bajo"
        if abs_val < 0.6: return 2, "moderado"
        if abs_val < 0.8: return 3, "alto"
        return 4, "dominante"

    elif tipo in ("gap",):
        if abs_val < 0.01: return 2, "en equilibrio"
        if valor > 0:
            if abs_val < 0.03: return 3, "ligeramente sobre potencial"
            return 4, "significativamente sobre potencial"
        else:
            if abs_val < 0.03: return 1, "ligeramente bajo potencial"
            return 0, "significativamente bajo potencial"

    elif tipo in ("varianza", "desviacion", "coef_variacion"):
        if abs_val < 0.001: return 0, "estable (casi sin variación)"
        if abs_val < 0.01: return 1, "poco volátil"
        if abs_val < 0.05: return 2, "volatilidad normal"
        if abs_val < 0.15: return 3, "volátil"
        return 4, "muy volátil (impredecible)"

    elif tipo in ("persistencia",):
        if abs_val < 0.1: return 0, "transitorio (se disipa rápido)"
        if abs_val < 0.3: return 1, "poco persistente"
        if abs_val < 0.6: return 2, "moderadamente persistente"
        if abs_val < 0.8: return 3, "persistente"
        return 4, "muy persistente (estructural)"

    elif tipo in ("multiplicador",):
        if abs_val < 0.5: return 0, "efecto mínimo"
        if abs_val < 1.0: return 1, "efecto parcial"
        if abs_val < 1.5: return 2, "efecto proporcional"
        if abs_val < 2.5: return 3, "efecto amplificado"
        return 4, "efecto muy amplificado"

    # Default
    if abs_val < 0.01: return 0, "muy bajo"
    if abs_val < 0.05: return 1, "bajo"
    if abs_val < 0.15: return 2, "normal"
    if abs_val < 0.40: return 3, "alto"
    return 4, "muy alto"


# ============================================================
# DECODIFICADOR PRINCIPAL
# ============================================================

def decodificar_economia(series_dict, nombre_entidad=""):
    """Ejecuta todas las fórmulas y decodifica para el LLM.

    Args:
        series_dict: {nombre_metrica: [valor_t1, valor_t2, ...]}
        nombre_entidad: nombre del país/empresa/activo

    Returns:
        str: texto completo para prompt caching del LLM
    """
    # 1. Ejecutar fórmulas
    resultados = calcular_formulas_economia(series_dict)

    if not resultados:
        return "Sin datos suficientes para análisis económico."

    lines = []
    lines.append(f"# ANÁLISIS ECONÓMICO ESTRUCTURAL{' de ' + nombre_entidad if nombre_entidad else ''}")
    lines.append("")
    lines.append("Cada fórmula se descompone en operaciones primitivas (su gramática).")
    lines.append("Fórmulas con la misma gramática son ISOMORFAS: hacen lo mismo sobre dominios diferentes.")
    lines.append("")

    # 2. Agrupar por tipo funcional
    por_tipo = defaultdict(list)
    for nombre, info in resultados.items():
        por_tipo[info["tipo"]].append((nombre, info))

    # 3. Decodificar por tipo
    alertas = []

    for tipo in sorted(por_tipo.keys()):
        items = por_tipo[tipo]
        tipo_idx = TIPOS_FUNCIONALES.get(tipo, -1)

        lines.append(f"## {tipo.upper().replace('_', ' ')}")

        for nombre, info in items:
            valor = info["valor"]
            texto = info["texto"]
            nivel_idx, nivel_texto = clasificar_nivel(valor, tipo)

            # Buscar si esta fórmula tiene gramática en el catálogo
            nombre_base = nombre.split("_")[0] if "_" in nombre else nombre
            gramatica_match = None
            for f_nombre, f_info in FORMULAS.items():
                if nombre_base in f_nombre or f_nombre in nombre:
                    gramatica_match = f_info
                    break

            # Línea principal
            signo = "+" if valor >= 0 else ""
            line = f"  {nombre}: {signo}{valor:.4f} → {nivel_texto}"

            # Añadir gramática si existe
            if gramatica_match:
                ops_str = " → ".join(gramatica_match["ops"])
                line += f"\n    Gramática: {ops_str}"
                line += f"\n    Lectura: {gramatica_match['lectura']}"

            line += f"\n    ({texto})"
            lines.append(line)

            # Alertas para valores extremos
            if nivel_idx >= 4:
                alertas.append(f"[{tipo}] {nombre} = {valor:.4f} → {nivel_texto} — {texto}")
            elif nivel_idx == 0 and tipo in ("tasa_crecimiento", "gap"):
                alertas.append(f"[{tipo}] {nombre} = {valor:.4f} → {nivel_texto} — {texto}")

        lines.append("")

    # 4. Isomorfismos detectados
    # Buscar fórmulas en los resultados que comparten gramática
    isos = detectar_isomorfismos()
    iso_encontrados = []
    for seq, nombres_iso in isos.items():
        presentes = [n for n in nombres_iso if any(n in r_nombre for r_nombre in resultados.keys())]
        if len(presentes) >= 2:
            iso_encontrados.append((seq, nombres_iso))

    if iso_encontrados or isos:
        lines.append("## ISOMORFISMOS (fórmulas con la misma gramática)")
        lines.append("Cuando dos fórmulas comparten gramática, hacen lo MISMO sobre dominios diferentes.")
        lines.append("Esto es evidencia de que el mismo mecanismo opera en ambos contextos.")
        lines.append("")
        for seq, nombres_iso in isos.items():
            ops_nombres = [list(OPS.keys())[list(OPS.values()).index(s)] for s in seq]
            ops_str = " → ".join(ops_nombres)
            formulas_str = ", ".join(nombres_iso)
            ramas = set(FORMULAS[n]["rama"] for n in nombres_iso if n in FORMULAS)
            if len(ramas) > 1:
                lines.append(f"  🔗 {ops_str}")
                lines.append(f"    = {formulas_str}")
                lines.append(f"    Ramas: {', '.join(ramas)} — CROSS-DOMAIN")
            else:
                lines.append(f"  {ops_str} = {formulas_str}")
        lines.append("")

    # 5. Alertas
    if alertas:
        lines.append("## ⚠️ ALERTAS")
        for a in alertas:
            lines.append(f"  - {a}")
        lines.append("")

    # 6. Síntesis
    lines.append("## SÍNTESIS")
    lines.append(f"  {len(resultados)} fórmulas ejecutadas sobre {len(series_dict)} series.")
    lines.append(f"  {len(por_tipo)} tipos funcionales activos.")
    if alertas:
        lines.append(f"  {len(alertas)} alertas requieren atención.")
    lines.append(f"  {len(isos)} isomorfismos detectados en el catálogo.")
    lines.append("")
    lines.append("  Usa los isomorfismos para razonar por analogía:")
    lines.append("  si dos fórmulas comparten gramática, lo que sabes de una aplica a la otra.")

    return "\n".join(lines)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import time

    print("=" * 70)
    print("DECODIFICADOR ECONÓMICO — Test completo")
    print("=" * 70)

    # Simular economía española 48 trimestres
    np.random.seed(42)
    t = np.arange(48)
    pib = 300_000 * (1.005 ** t) * (1 + 0.01 * np.sin(2*np.pi*t/4) + 0.005 * np.random.randn(48))
    inflacion = 2.5 + 1.0 * np.sin(2*np.pi*t/8) + 0.3 * np.random.randn(48)
    desempleo = 12.0 - 0.15 * (pib / pib[0] - 1) * 100 + 0.8 * np.random.randn(48)
    tipo_interes = 1.5 + 0.4 * inflacion + 0.15 * np.random.randn(48)
    consumo = 0.58 * pib + 500 * np.random.randn(48)
    inversion = 0.21 * pib * (1 + 0.08 * np.random.randn(48))
    exportaciones = 0.35 * pib * (1 + 0.03 * np.random.randn(48))
    importaciones = 0.33 * pib * (1 + 0.03 * np.random.randn(48))
    deuda = 120 + 0.5 * t + 2 * np.random.randn(48)  # % del PIB

    series = {
        "pib": list(pib),
        "inflacion": list(inflacion),
        "desempleo": list(desempleo),
        "tipo_interes": list(tipo_interes),
        "consumo": list(consumo),
        "inversion": list(inversion),
        "exportaciones": list(exportaciones),
        "importaciones": list(importaciones),
        "deuda_pib": list(deuda),
    }

    t0 = time.time()
    contexto = decodificar_economia(series, "España (simulada)")
    dt = time.time() - t0

    print(contexto)
    print(f"\n{'='*70}")
    print(f"  {len(contexto)} chars, ~{len(contexto.split())} palabras, {dt*1000:.0f}ms")
    print(f"  Tokens estimados prompt caching: ~{len(contexto.split())*1.3:.0f}")
    print(f"{'='*70}")
