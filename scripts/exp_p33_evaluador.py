#!/usr/bin/env python3
"""EXP P33 Evaluador — Clasifica hallazgos del Motor vs monitoring existente."""

import json
import os
import re
from datetime import datetime, timezone

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datos", "exp_p33")

# =========================================================================
# CONOCIMIENTO EXISTENTE — baseline contra el que comparamos
# =========================================================================

# Lo que los endpoints del sistema ya reportan directamente
CONOCIDO_DIRECTO = [
    "616 preguntas activas",
    "preguntas activas",
    "ciclo_roto false",
    "ciclo roto false",
    "tasa_reciente 0.50",
    "tasa reciente 0.50",
    "gap_reciente 0.34",
    "4 programas",
    "programas compilados",
    "tasa_cierre_media 1.0",
    "tasa cierre 1.0",
    "tasa 100%",
    "flywheel 0 ciclos",
    "flywheel 1 ciclo",
    "4 modelos caidos",
    "modelos caidos",
    "modelos down",
    "4 healthy",
    "144 datapoints",
    "141 datapoints",
    "36 datapoints",
    "12 modelos activos",
    "21 celdas",
    "14 celdas con datos",
    "7 celdas vacias",
    "317 modelos candidatos",
    "42 conexiones",
    "124 endpoints",
    "61 herramientas",
    "version 3.4.0",
    "19 briefings",
    "costes $0.00",
    "proyeccion mensual",
    "presupuesto",
    "18 inteligencias",
    "617 preguntas",
    "20 aristas",
    "9 alertas",
    "alertas autopoiesis",
    "umbral poda",
    "temperatura 0.25",
    "orden rigido",
    "consistencia inconsistente",
    "datapoints huerfanos",
    "preguntas expiradas",
    "20 expiradas",
    "reactor 0 candidatas",
    "herramientas sin uso",
    "tools sin datos",
    "señales pid",
    "14 celdas con señales",
    "ConservarxSalud",
    "ReplicarxContinuidad",
    "2 exocortex piloto",
]

# Lo que Chief of Staff detectó cruzando datos manualmente (ver orden)
GAPS_CHIEF = [
    {
        "id": "chief_1",
        "desc": "autopoiesis dice ciclo_roto=false pero estigmergia tiene alertas autopoiesis_roto",
        "keywords": ["autopoiesis", "ciclo", "roto", "alerta", "contradiccion", "inconsisten"],
    },
    {
        "id": "chief_2",
        "desc": "programas tasa_cierre=1.0 cuando calibracion baja a 0.52 — inflacion",
        "keywords": ["tasa", "100%", "1.0", "inflad", "calibra", "sobreestim"],
    },
    {
        "id": "chief_3",
        "desc": "costes_llm solo captura MiMo, no Motor principal — registro incompleto",
        "keywords": ["cost", "registro", "incompleto", "mimo", "falt", "deepseek", "no aparec"],
    },
    {
        "id": "chief_4",
        "desc": "flywheel 0 ciclos — nunca ha aprendido autonomamente",
        "keywords": ["flywheel", "apren", "autonomo", "ciclo", "nunca", "0 ciclo"],
    },
    {
        "id": "chief_5",
        "desc": "tasa_media_global volatil sin patron — no converge",
        "keywords": ["volatil", "inestab", "oscila", "no converge", "erratic"],
    },
    {
        "id": "chief_6",
        "desc": "propiocepcion 0 ejecuciones 24h pero metricas muestran ~10 recientes",
        "keywords": ["propiocep", "ejecucion", "0 ejecucion", "inconsisten", "24h"],
    },
]


def _normalizar(text: str) -> str:
    """Normaliza texto para comparación: minúsculas, sin acentos, sin puntuación extra."""
    text = text.lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", "ü": "u",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def clasificar_hallazgo(hallazgo_text: str) -> dict:
    """Clasifica un hallazgo como CONOCIDO, REFORMULADO o CANDIDATO_NUEVO."""
    norm = _normalizar(hallazgo_text)

    # Check CONOCIDO: matches direct endpoint data
    for patron in CONOCIDO_DIRECTO:
        if _normalizar(patron) in norm:
            return {"nivel": "CONOCIDO", "match": patron, "razon": f"Dato directo de endpoint: '{patron}'"}

    # Check REFORMULADO: matches Chief's cross-data analysis
    for gap in GAPS_CHIEF:
        matches = sum(1 for kw in gap["keywords"] if kw.lower() in norm)
        if matches >= 2:  # At least 2 keywords match
            return {
                "nivel": "REFORMULADO",
                "match": gap["id"],
                "razon": f"Matchea gap del Chief: {gap['desc']} ({matches}/{len(gap['keywords'])} keywords)",
            }

    # If no match: CANDIDATO_NUEVO
    return {
        "nivel": "CANDIDATO_NUEVO",
        "match": None,
        "razon": "No matchea datos de endpoints ni gaps del Chief",
    }


def extraer_hallazgos_texto(resultado: dict) -> list:
    """Extrae SOLO hallazgos reales (no preguntas) del Motor.

    Filtra:
    - Preguntas (empiezan con ¿ o son numeradas tipo "1. **¿...")
    - Fragmentos demasiado cortos (<40 chars)
    - Enumeraciones de datos sin análisis
    """
    textos = []

    # From hallazgos array — only "Hallazgo:"-prefixed entries
    for h in resultado.get("hallazgos", []):
        if isinstance(h, dict):
            text = h.get("hallazgo", "")
        elif isinstance(h, str):
            text = h
        else:
            continue

        # Skip questions
        stripped = text.strip().lstrip("- *#")
        if stripped.startswith("¿") or stripped.startswith("1.") or stripped.startswith("2."):
            # But keep if it also contains "Hallazgo:"
            if "allazgo:" not in text:
                continue

        # Only keep if it's a finding (contains "Hallazgo:" or is substantive analysis >80 chars)
        is_finding = "allazgo:" in text
        is_substantive = len(text.strip()) > 80 and "¿" not in text[:20]

        if is_finding or is_substantive:
            textos.append(text.strip())

    # From sintesis — only substantial analytical sentences
    sintesis = resultado.get("sintesis", "")
    if sintesis:
        # Split into paragraphs, not sentences (preserve context)
        paragraphs = re.split(r'\n\n+', sintesis)
        for p in paragraphs:
            p = p.strip()
            # Skip question blocks and headers
            if p.startswith("[INT-") or p.startswith("SINTESIS") or "¿" in p[:20]:
                continue
            if len(p) > 80:
                textos.append(p)

    return textos


def evaluar_resultados():
    """Evalúa todos los resultados contra el baseline."""
    combined_path = os.path.join(OUTPUT_DIR, "resultados_completos.json")
    if not os.path.exists(combined_path):
        print("[evaluador] No se encontraron resultados. Ejecuta primero exp_p33_ejecutor.py")
        return None

    with open(combined_path) as f:
        data = json.load(f)

    resultados = data.get("resultados", [])
    ok_resultados = [r for r in resultados if r.get("status") == "ok"]

    if not ok_resultados:
        print("[evaluador] No hay resultados exitosos para evaluar")
        return None

    print(f"[evaluador] Evaluando {len(ok_resultados)} resultados...")

    clasificaciones = {"CONOCIDO": [], "REFORMULADO": [], "CANDIDATO_NUEVO": []}
    por_caso = {}

    for res in ok_resultados:
        caso_id = res["caso_id"]
        textos = extraer_hallazgos_texto(res)
        caso_cls = []

        for texto in textos:
            if len(texto.strip()) < 15:
                continue
            cls = clasificar_hallazgo(texto)
            cls["texto"] = texto[:300]
            cls["caso_id"] = caso_id
            clasificaciones[cls["nivel"]].append(cls)
            caso_cls.append(cls)

        por_caso[caso_id] = {
            "n_hallazgos_raw": res.get("n_hallazgos", 0),
            "n_textos_extraidos": len(textos),
            "clasificacion": {
                "CONOCIDO": len([c for c in caso_cls if c["nivel"] == "CONOCIDO"]),
                "REFORMULADO": len([c for c in caso_cls if c["nivel"] == "REFORMULADO"]),
                "CANDIDATO_NUEVO": len([c for c in caso_cls if c["nivel"] == "CANDIDATO_NUEVO"]),
            },
            "inteligencias": res.get("inteligencias", []),
            "tier": res.get("tier"),
            "coste_usd": res.get("coste_usd", 0),
            "tiempo_s": res.get("tiempo_s", 0),
        }

    # Determine verdict
    n_conocido = len(clasificaciones["CONOCIDO"])
    n_reformulado = len(clasificaciones["REFORMULADO"])
    n_nuevo = len(clasificaciones["CANDIDATO_NUEVO"])
    total = n_conocido + n_reformulado + n_nuevo

    if n_nuevo >= 3:
        veredicto = "VALIDADO"
        razon = f"Se encontraron {n_nuevo} hallazgos CANDIDATO_NUEVO (≥3 requeridos)"
    elif n_reformulado >= 5 and n_nuevo >= 1:
        veredicto = "PARCIAL"
        razon = (f"El Motor automatiza detección ({n_reformulado} reformulados) "
                 f"y encontró {n_nuevo} nuevo(s)")
    else:
        veredicto = "DESCARTADO"
        razon = (f"Solo {n_nuevo} nuevo(s) y {n_reformulado} reformulado(s). "
                 f"No supera umbral de ≥3 nuevos")

    evaluacion = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "total_hallazgos": total,
        "clasificacion": {
            "CONOCIDO": n_conocido,
            "REFORMULADO": n_reformulado,
            "CANDIDATO_NUEVO": n_nuevo,
        },
        "por_caso": por_caso,
        "hallazgos_nuevos": [
            {
                "caso": h["caso_id"],
                "hallazgo": h["texto"],
                "clasificacion": "CANDIDATO_NUEVO",
                "razon": h["razon"],
            }
            for h in clasificaciones["CANDIDATO_NUEVO"][:20]  # Top 20
        ],
        "hallazgos_reformulados": [
            {
                "caso": h["caso_id"],
                "hallazgo": h["texto"],
                "match": h["match"],
                "razon": h["razon"],
            }
            for h in clasificaciones["REFORMULADO"][:10]
        ],
        "veredicto_p33": veredicto,
        "razon": razon,
        "coste_total_usd": data.get("coste_total_usd", 0),
    }

    # Save evaluation
    eval_path = os.path.join(OUTPUT_DIR, "evaluacion_p33.json")
    with open(eval_path, "w") as f:
        json.dump(evaluacion, f, indent=2, ensure_ascii=False, default=str)

    # Generate RESUMEN
    generar_resumen(evaluacion, ok_resultados, clasificaciones)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  VEREDICTO P33: {veredicto}")
    print(f"  {razon}")
    print(f"{'='*60}")
    print(f"  Total hallazgos analizados: {total}")
    print(f"  CONOCIDO:         {n_conocido}")
    print(f"  REFORMULADO:      {n_reformulado}")
    print(f"  CANDIDATO_NUEVO:  {n_nuevo}")
    print(f"  Coste total:      ${data.get('coste_total_usd', 0):.4f}")
    print(f"{'='*60}")

    if clasificaciones["CANDIDATO_NUEVO"]:
        print(f"\n  Hallazgos NUEVOS:")
        for i, h in enumerate(clasificaciones["CANDIDATO_NUEVO"][:10], 1):
            print(f"    {i}. [{h['caso_id']}] {h['texto'][:120]}")

    return evaluacion


def generar_resumen(evaluacion: dict, resultados: list, clasificaciones: dict):
    """Genera RESUMEN_P33.md legible."""
    por_caso = evaluacion.get("por_caso", {})

    lines = [
        "# RESUMEN EXPERIMENTO P33 — El Sistema se Analiza a Sí Mismo",
        "",
        f"**Fecha:** {evaluacion['fecha']}",
        f"**Veredicto:** {evaluacion['veredicto_p33']}",
        f"**Razón:** {evaluacion['razon']}",
        f"**Coste total:** ${evaluacion.get('coste_total_usd', 0):.4f}",
        "",
        "---",
        "",
        "## 1. Tabla de Casos",
        "",
        "| Caso | INTs activadas | Hallazgos | Tier | Coste | Tiempo |",
        "|------|---------------|-----------|------|-------|--------|",
    ]

    for res in resultados:
        cid = res["caso_id"]
        ints = ", ".join(res.get("inteligencias", [])[:5])
        pc = por_caso.get(cid, {})
        lines.append(
            f"| {cid} | {ints} | {pc.get('n_textos_extraidos', 0)} | "
            f"{res.get('tier', '?')} | ${res.get('coste_usd', 0):.4f} | "
            f"{res.get('tiempo_s', 0):.1f}s |"
        )

    lines.extend([
        "",
        "## 2. Clasificación de Hallazgos",
        "",
        f"| Nivel | Count | % |",
        f"|-------|-------|---|",
    ])
    total = evaluacion["total_hallazgos"] or 1
    for nivel in ["CONOCIDO", "REFORMULADO", "CANDIDATO_NUEVO"]:
        n = evaluacion["clasificacion"][nivel]
        pct = n / total * 100
        lines.append(f"| {nivel} | {n} | {pct:.0f}% |")

    # Hallazgos NUEVOS
    lines.extend(["", "## 3. Hallazgos CANDIDATO_NUEVO (lo que el monitoring no detecta)", ""])
    nuevos = clasificaciones.get("CANDIDATO_NUEVO", [])
    if nuevos:
        for i, h in enumerate(nuevos[:15], 1):
            lines.append(f"{i}. **[{h['caso_id']}]** {h['texto'][:200]}")
            lines.append(f"   - *Razón:* {h['razon']}")
            lines.append("")
    else:
        lines.append("*Ninguno detectado.*")
        lines.append("")

    # Hallazgos REFORMULADOS
    lines.extend(["## 4. Hallazgos REFORMULADOS (automatizan lo que el Chief detecta manualmente)", ""])
    reformulados = clasificaciones.get("REFORMULADO", [])
    if reformulados:
        for i, h in enumerate(reformulados[:10], 1):
            lines.append(f"{i}. **[{h['caso_id']}]** {h['texto'][:200]}")
            lines.append(f"   - *Match:* {h.get('match', '?')} — {h['razon']}")
            lines.append("")
    else:
        lines.append("*Ninguno detectado.*")
        lines.append("")

    # Veredicto
    lines.extend([
        "## 5. Veredicto y Siguiente Paso",
        "",
        f"**Veredicto P33:** {evaluacion['veredicto_p33']}",
        "",
        f"{evaluacion['razon']}",
        "",
    ])

    if evaluacion["veredicto_p33"] == "VALIDADO":
        lines.extend([
            "### Gaps nuevos detectados y acciones:",
            "",
            "Los hallazgos CANDIDATO_NUEVO representan ángulos que ningún componente "
            "del sistema (autopoiesis, flywheel, FOK, monitoring) detecta hoy. "
            "Para cerrarlos se necesitaría:",
            "",
            "1. Implementar los checks específicos como nuevos SLOs en monitoring",
            "2. Integrar la detección cruzada que el Motor hace en el loop del Gestor",
            "3. Ejecutar P33 periódicamente como meta-diagnóstico del sistema",
            "",
            "### Recomendación CR0:",
            "P33 aporta valor diferencial. Integrar como endpoint `/gestor/auto-diagnostico` "
            "que ejecute el Motor sobre sus propios datos 1x/semana.",
        ])
    elif evaluacion["veredicto_p33"] == "PARCIAL":
        lines.extend([
            "### Valor parcial:",
            "El Motor automatiza la detección que hoy solo hace el Chief manualmente. "
            "Esto tiene valor operativo aunque no descubra gaps genuinamente nuevos.",
            "",
            "### Recomendación CR0:",
            "Integrar como automatización de detección, no como descubrimiento.",
        ])
    else:
        lines.extend([
            "### Conclusión:",
            "El Motor no añade capacidad de detección sobre lo que el monitoring ya provee. "
            "P33 se descarta como principio — el auto-análisis no genera valor diferencial.",
            "",
            "### Recomendación CR0:",
            "No invertir más en auto-análisis. Priorizar mejora de los controles existentes.",
        ])

    lines.extend([
        "",
        "---",
        "",
        f"*Generado automáticamente por exp_p33_evaluador.py — {evaluacion['fecha']}*",
    ])

    resumen_path = os.path.join(OUTPUT_DIR, "RESUMEN_P33.md")
    with open(resumen_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[evaluador] RESUMEN guardado en {resumen_path}")


if __name__ == "__main__":
    evaluar_resultados()
