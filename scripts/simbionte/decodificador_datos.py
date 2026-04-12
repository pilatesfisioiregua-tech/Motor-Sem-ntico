"""
Decodificador de Datos — Secuencias de lentes → texto para LLM

Fecha: 2026-04-12

Las 10 lentes producen secuencias de tokens legibles ("feedback_positivo",
"hub", "acantilado"). Este decodificador:
  1. Toma las 10 secuencias de lentes
  2. Cuenta frecuencias por lente
  3. Detecta patrones significativos (dominantes, ausentes, cambios)
  4. Traduce a texto estructurado que un LLM puede usar para razonar

Funciona sobre CUALQUIER dato que pase por las 10 lentes:
  - Series temporales de mercado (OHLCV → metricas rolling)
  - Datos empresariales (CRM/ERP → metricas mensuales)
  - Cualquier serie temporal con 4+ puntos

$0 total (compute local)
"""

import numpy as np
from collections import Counter

from lentes_matematicas import (
    LENTES, LENTE_ESTADISTICA, LENTE_CONJUNTOS, LENTE_GRAFOS,
    LENTE_MARKOV, LENTE_JUEGOS, LENTE_CIBERNETICA, LENTE_SISTEMAS,
    LENTE_TOPOLOGIA, LENTE_GEOMETRIA_DIFF, LENTE_CINEMATICA,
)

LENTE_DICTS = {
    "estadistica": LENTE_ESTADISTICA,
    "conjuntos": LENTE_CONJUNTOS,
    "grafos": LENTE_GRAFOS,
    "markov": LENTE_MARKOV,
    "juegos": LENTE_JUEGOS,
    "cibernetica": LENTE_CIBERNETICA,
    "sistemas": LENTE_SISTEMAS,
    "topologia": LENTE_TOPOLOGIA,
    "geometria_diff": LENTE_GEOMETRIA_DIFF,
    "cinematica": LENTE_CINEMATICA,
}

# ============================================================
# TRADUCCIONES: token de lente → significado para el LLM
# ============================================================

TRADUCCIONES = {
    "estadistica": {
        "entropia_baja": "distribución concentrada — pocas métricas dominan, sistema predecible",
        "entropia_media": "distribución moderada — sin concentración ni dispersión extrema",
        "entropia_alta": "distribución dispersa — muchas métricas activas, sistema complejo",
        "skew_negativo": "cola izquierda — riesgo de caída súbita mayor que potencial de subida",
        "skew_neutro": "distribución simétrica — riesgos equilibrados",
        "skew_positivo": "cola derecha — potencial de subida mayor que riesgo de caída",
        "kurtosis_baja": "colas ligeras — eventos extremos improbables",
        "kurtosis_alta": "COLAS PESADAS — eventos extremos más probables de lo normal",
        "concentracion": "alta concentración — pocos factores explican la mayoría de la variación",
        "dispersion": "baja concentración — muchos factores contribuyen, sistema diversificado",
        "estacionario": "sin tendencia — el sistema oscila alrededor de un nivel estable",
        "no_estacionario": "CON TENDENCIA — el sistema está cambiando de nivel",
    },
    "conjuntos": {
        "jaccard_alto": "períodos consecutivos similares — consistencia temporal alta",
        "jaccard_medio": "similitud moderada entre períodos",
        "jaccard_bajo": "períodos consecutivos DIFERENTES — algo cambió entre ellos",
        "cobertura_total": "todas las métricas activas — sistema funcionando a plena capacidad",
        "cobertura_parcial": "algunas métricas inactivas — capacidad parcial",
        "gap": "MÉTRICAS FALTANTES — hay un agujero en la cobertura del sistema",
        "simetria": "primera y segunda mitad del período iguales — estabilidad",
        "asimetria": "primera y segunda mitad DIFERENTES — hubo un cambio estructural",
        "inclusion": "un período contiene al otro — escalamiento",
        "disjuncion": "períodos completamente diferentes — ruptura de patrón",
    },
    "grafos": {
        "hub": "métrica CENTRAL conectada a muchas otras — nodo de influencia",
        "periferia": "métrica periférica — poca conexión con el resto",
        "cluster_denso": "grupo de métricas que se mueven JUNTAS — bloque correlacionado",
        "cluster_disperso": "métricas poco correlacionadas — independencia",
        "puente": "métrica que CONECTA dos grupos — punto de transmisión",
        "isla": "métrica AISLADA — no se correlaciona con ninguna otra",
        "estrella": "una métrica conectada a todas — dependencia central",
        "cadena": "correlaciones en secuencia — efecto dominó posible",
        "ciclo": "correlaciones circulares — feedback loop en la red",
        "desconexion": "grafo fragmentado — las métricas operan independientemente",
    },
    "markov": {
        "transicion_fuerte": "alta probabilidad de CAMBIAR de estado — sistema inestable",
        "transicion_debil": "baja probabilidad de cambiar — sistema estable en su estado",
        "estado_absorbente": "ESTADO TERMINAL — una vez que entra, no sale (churn terminal, techo de crecimiento)",
        "estado_transitorio": "estado temporal — el sistema pasará a otro estado",
        "diagonal_alta": "tendencia a PERMANECER en el mismo estado — inercia alta",
        "diagonal_baja": "tendencia a cambiar — volatilidad de régimen",
        "ergodicidad": "todos los estados son alcanzables — sistema flexible",
        "no_ergodicidad": "hay estados INALCANZABLES — barreras estructurales",
        "periodicidad": "patrón CÍCLICO en las transiciones — estacionalidad o loop",
        "aperiodico": "sin patrón cíclico — transiciones no predecibles",
    },
    "juegos": {
        "cooperacion": "métricas se REFUERZAN mutuamente — sinergia",
        "competencia": "métricas en TENSIÓN — cuando una sube, otra baja",
        "dilema": "DILEMA — optimizar una empeora otra (trade-off irreconciliable)",
        "suma_cero": "juego de suma cero — ganancia de una = pérdida de otra",
        "suma_positiva": "las métricas pueden mejorar JUNTAS — hay espacio de crecimiento",
        "suma_negativa": "AMBAS EMPEORAN simultáneamente — espiral destructiva",
        "nash": "equilibrio estable — nadie tiene incentivo a cambiar",
        "inestable": "sin equilibrio — el sistema OSCILA sin convergir",
        "dominancia": "una métrica DOMINA a la otra — asimetría de poder",
        "simetria_juego": "métricas en balance — poder equilibrado",
    },
    "cibernetica": {
        "feedback_positivo": "AMPLIFICACIÓN — el sistema se autorefuerza (crecimiento exponencial O colapso)",
        "feedback_negativo": "regulación — el sistema CORRIGE desviaciones (vuelta al equilibrio)",
        "sin_feedback": "métricas independientes — sin loops de retroalimentación",
        "delay_corto": "efecto inmediato — cambios se propagan rápido",
        "delay_largo": "efecto RETARDADO — cambios tardan 3+ períodos en manifestarse",
        "amplificacion": "la señal se AMPLIFICA con el tiempo — atención: puede ser inestable",
        "amortiguacion": "la señal se ATENÚA — el sistema absorbe perturbaciones",
        "oscilacion": "la señal OSCILA — el sistema no encuentra equilibrio",
        "saturacion": "la señal llegó a TECHO — rendimientos decrecientes",
        "runaway": "DIVERGENCIA — señal sin control, crecimiento o caída sin freno",
    },
    "sistemas": {
        "acoplamiento_fuerte": "subsistemas MUY INTERDEPENDIENTES — un fallo se propaga",
        "acoplamiento_debil": "subsistemas semi-independientes — fallos contenidos",
        "emergencia": "propiedad del TODO que no está en las partes — comportamiento emergente",
        "reducibilidad": "el todo = suma de partes — sin sorpresas",
        "anidacion": "subsistemas dentro de subsistemas — complejidad jerárquica",
        "plano": "sin jerarquía — estructura plana",
        "coherencia": "subsistemas ALINEADOS — van en la misma dirección",
        "conflicto": "subsistemas en CONTRADICCIÓN — fuerzas opuestas",
        "resiliencia": "el sistema se RECUPERA de perturbaciones — robusto",
        "fragilidad": "el sistema se ROMPE con perturbaciones — vulnerable",
    },
    "topologia": {
        "agujero": "GAP — métrica faltante o discontinuidad en los datos",
        "continuo": "flujo continuo — sin rupturas",
        "meseta": "zona PLANA prolongada — estancamiento o techo",
        "pico": "extremo aislado — evento puntual, no tendencia",
        "valle": "mínimo aislado — crisis puntual, no estructural",
        "pendiente": "cambio gradual sostenido — tendencia en curso",
        "acantilado": "CAMBIO BRUSCO — discontinuidad significativa",
        "compacto": "métricas en rango acotado — sistema contenido",
        "disperso": "métricas en rango amplio — alta variabilidad",
        "persistente": "patrón que NO DESAPARECE — estructural, no temporal",
    },
    "geometria_diff": {
        "curvatura_positiva": "tendencia CONVEXA — acelerándose (crecimiento exponencial)",
        "curvatura_negativa": "tendencia CÓNCAVA — desacelerándose (rendimientos decrecientes)",
        "curvatura_cero": "tendencia lineal — crecimiento constante",
        "inflexion": "PUNTO DE GIRO — la curvatura cambia de signo",
        "torsion": "el plano de curvatura cambia — complejidad de trayectoria",
        "geodesica": "camino más eficiente — evolución óptima",
        "desviacion": "lejos del camino óptimo — ineficiencia",
        "suave": "curva sin discontinuidades — evolución predecible",
        "rugoso": "MUCHOS CAMBIOS de dirección — evolución errática",
        "plano": "sin curvatura — estancamiento total",
    },
    "cinematica": {
        "acelerando": "velocidad CRECIENTE — momentum positivo",
        "desacelerando": "velocidad DECRECIENTE — momentum se agota",
        "velocidad_constante": "ritmo estable — sin aceleración",
        "reposo": "velocidad ≈ 0 — sistema parado",
        "retroceso": "velocidad NEGATIVA — el sistema retrocede",
        "coherente": "dirección CONSISTENTE — movimiento con propósito",
        "incoherente": "dirección cambiante — movimiento errático",
        "impulso": "cambio BRUSCO de velocidad — evento de impacto",
        "inercia": "resiste cambio — momentum alto difícil de frenar",
        "volatil": "velocidad FLUCTUANTE — impredecible",
    },
}


def decodificar_lentes(resultados_lentes, nombre_entidad="", metricas_crudas=None):
    """Decodifica las 10 secuencias de lentes a texto para LLM.

    Args:
        resultados_lentes: output de aplicar_10_lentes()
        nombre_entidad: nombre del ticker/empresa (opcional)
        metricas_crudas: dict {metrica: valor_actual} para contexto (opcional)

    Returns:
        str: texto decodificado para inyectar al LLM
    """
    lines = []
    lines.append(f"# ANÁLISIS ESTRUCTURAL{' de ' + nombre_entidad if nombre_entidad else ''}")
    lines.append("Cada hallazgo proviene de una lente matemática aplicada a los datos.\n")

    # Métricas crudas de contexto (si las hay)
    if metricas_crudas:
        lines.append("## MÉTRICAS CLAVE")
        for k, v in metricas_crudas.items():
            if isinstance(v, float):
                if abs(v) < 0.01:
                    lines.append(f"  {k}: {v:.4f}")
                elif abs(v) > 1000:
                    lines.append(f"  {k}: {v:,.0f}")
                else:
                    lines.append(f"  {k}: {v:.2f}")
            else:
                lines.append(f"  {k}: {v}")
        lines.append("")

    # Procesar cada lente
    hallazgos_totales = 0
    alertas = []

    for nombre_lente, res in resultados_lentes.items():
        lente_dict = LENTE_DICTS.get(nombre_lente, {})
        inv = {v: k for k, v in lente_dict.items()}
        tokens = [inv.get(t, f"desconocido_{t}") for t in res["secuencia"]]

        if not tokens:
            continue

        freq = Counter(tokens)
        total = len(tokens)

        # Solo hallazgos significativos (>20% del tiempo)
        hallazgos = []
        traducciones_lente = TRADUCCIONES.get(nombre_lente, {})

        for tok, count in freq.most_common():
            pct = count / total
            if pct < 0.15:
                continue

            traduccion = traducciones_lente.get(tok, tok.replace("_", " "))

            # Marcar si es alerta (palabras clave en traduccion)
            es_alerta = any(w in traduccion.upper() for w in
                           ["AMPLIFICACIÓN", "DIVERGENCIA", "TERMINAL", "ROMPE",
                            "COLAPSO", "BRUSCO", "GAP", "COLAS PESADAS",
                            "ESPIRAL", "DILEMA", "CONTRADICCIÓN"])

            hallazgo = f"  {'⚠️ ' if es_alerta else ''}{traduccion} ({pct:.0%} del período)"
            hallazgos.append(hallazgo)
            hallazgos_totales += 1

            if es_alerta:
                alertas.append(f"[{nombre_lente}] {traduccion}")

        if hallazgos:
            lines.append(f"### {nombre_lente.upper()}")
            lines.extend(hallazgos)
            lines.append("")

    # Resumen de alertas
    if alertas:
        lines.append("## ⚠️ ALERTAS ESTRUCTURALES")
        for a in alertas:
            lines.append(f"  - {a}")
        lines.append("")

    # Síntesis automática
    lines.append("## SÍNTESIS")
    lines.append(f"  {hallazgos_totales} hallazgos significativos detectados en 10 lentes.")
    if alertas:
        lines.append(f"  {len(alertas)} alertas requieren atención.")
    lines.append("  Usa estos hallazgos como evidencia para fundamentar tu análisis.")
    lines.append("  Si detectas un patrón recurrente, proponlo como isomorfismo.")

    return "\n".join(lines)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import sys, os, time
    sys.path.insert(0, os.path.dirname(__file__))
    from lentes_matematicas import aplicar_10_lentes
    from clasificador_empresarial import generar_empresa
    import yfinance as yf

    print("=" * 70)
    print("DECODIFICADOR DE DATOS — Test")
    print("=" * 70)

    # === TEST 1: Empresa sintética ===
    for tipo in ["saas_growth", "saas_declining", "startup_burn"]:
        meses = generar_empresa(tipo, n_meses=12, seed=42)
        metricas = ["revenue", "churn", "ltv_cac", "nps", "conversion",
                     "margen_bruto", "actividad", "adoption", "cash_flow",
                     "concentracion", "equipo_rotacion", "expansion"]
        series = {m: [float(mes.get(m, 0)) for mes in meses] for m in metricas}
        resultados = aplicar_10_lentes(series)

        crudas = {
            "Revenue": meses[-1].get("revenue", 0),
            "Churn": f"{meses[-1].get('churn', 0):.1%}",
            "LTV/CAC": meses[-1].get("ltv_cac", 0),
            "NPS": meses[-1].get("nps", 0),
            "Margen": f"{meses[-1].get('margen_bruto', 0):.0%}",
        }

        contexto = decodificar_lentes(resultados, f"Empresa {tipo}", crudas)
        print(f"\n{'='*70}")
        print(f"  {tipo.upper()}")
        print(f"{'='*70}")
        print(contexto)
        print(f"\n  [{len(contexto)} chars, ~{len(contexto.split())} palabras]")

    # === TEST 2: Ticker real ===
    print(f"\n{'='*70}")
    print("  DATOS REALES: NVDA")
    print(f"{'='*70}")

    df = yf.download("NVDA", period="1y", interval="1mo", progress=False)
    if hasattr(df.columns, 'levels'):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    import numpy as np
    c = df['Close'].values.astype(float)
    v = df['Volume'].values.astype(float)
    h = df['High'].values.astype(float)
    l = df['Low'].values.astype(float)
    r = np.diff(c) / np.where(np.abs(c[:-1]) > 1e-10, c[:-1], 1e-10)

    series = {
        'precio': list(c),
        'retorno': [0] + list(r),
        'volatilidad': [float(np.std(r[:max(i, 2)])) for i in range(len(c))],
        'momentum': [0] + [float(c[i] / c[max(i - 3, 0)] - 1) for i in range(1, len(c))],
        'volumen': list(v / max(np.mean(v), 1)),
        'rango': list((h - l) / np.where(c > 0, c, 1)),
        'sharpe': [0] + [float(np.mean(r[:i]) / max(np.std(r[:i]), 1e-10)) for i in range(1, len(r) + 1)],
        'drawdown': [0] + [float(min(0, c[i] / max(c[:i + 1]) - 1)) for i in range(1, len(c))],
        'trend': [0, 0] + [float(np.corrcoef(range(min(i, 3)), c[max(i - 3, 0):i])[0, 1]) if i >= 3 and np.std(c[max(i - 3, 0):i]) > 1e-10 else 0 for i in range(2, len(c))],
        'rsi': [0.5] + [float(np.sum(r[max(i - 3, 0):i] > 0) / max(min(i, 3), 1)) for i in range(1, len(r) + 1)],
        'skew': [0] * len(c),
        'autocorr': [0] * len(c),
    }
    min_len = min(len(sv) for sv in series.values())
    series = {k: sv[:min_len] for k, sv in series.items()}

    resultados = aplicar_10_lentes(series)
    crudas_nvda = {
        "Precio actual": f"${c[-1]:.2f}",
        "Retorno 1Y": f"{(c[-1] / c[0] - 1) * 100:+.1f}%",
        "Volatilidad": f"{np.std(r):.3f}",
        "Max Drawdown": f"{np.min((c - np.maximum.accumulate(c)) / np.maximum.accumulate(c)) * 100:.1f}%",
    }

    contexto = decodificar_lentes(resultados, "NVDA", crudas_nvda)
    print(contexto)
    print(f"\n  [{len(contexto)} chars, ~{len(contexto.split())} palabras]")
