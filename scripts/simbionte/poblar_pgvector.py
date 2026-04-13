"""
Poblar pgvector con catálogo completo.

Genera SQL INSERT para:
- 362 fórmulas con semántica
- 40 isomorfismos de gramática
- 69 enlaces de red de preguntas
- 8 patrones históricos

Ejecutar contra fly.io Postgres o guardar como .sql para deploy.

$0 total (genera SQL, no llama a API)
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from gramatica_formulas import FORMULAS
from semantica_formulas import SEMANTICA
from catalogo_finalidades import FINALIDADES, FORMULAS_MARCOS
from red_preguntas import ENLACES
from pipeline_completo import ISOMORFISMOS_CATALOGO


def generar_sql_formulas():
    """Genera INSERTs para catalogo_formulas."""
    lines = ["-- 362 fórmulas con semántica"]
    lines.append("DELETE FROM catalogo_formulas;")

    # Mapear fórmula → finalidades
    formula_finalidades = {}
    for fin_nombre, fin_info in FINALIDADES.items():
        for f in fin_info["formulas"]:
            if f not in formula_finalidades:
                formula_finalidades[f] = []
            formula_finalidades[f].append(fin_nombre)

    count = 0
    for nombre, gram in FORMULAS.items():
        sem = SEMANTICA.get(nombre, {})
        fins = formula_finalidades.get(nombre, ["DIAGNOSTICAR"])

        # Escapar comillas simples
        def esc(s):
            if s is None: return ""
            return str(s).replace("'", "''")

        formula_text = esc(gram.get("formula", ""))
        rama = esc(gram.get("rama", ""))
        gramatica = gram.get("ops", [])
        lectura = esc(gram.get("lectura", ""))
        resultado = esc(gram.get("resultado", ""))

        polos = sem.get("polos", ("bajo", "alto"))
        polo_bajo = esc(polos[0])
        polo_alto = esc(polos[1])
        eje = esc(sem.get("eje", ""))
        presupuestos = sem.get("presupuestos", [])
        razonamiento = sem.get("razonamiento", [])
        si_alto = esc(sem.get("si_alto", ""))
        si_bajo = esc(sem.get("si_bajo", ""))
        pregunta = esc(sem.get("pregunta", ""))

        # Construir arrays
        gram_arr = "ARRAY[" + ",".join(f"'{g}'" for g in gramatica) + "]" if gramatica else "ARRAY[]::TEXT[]"
        fins_arr = "ARRAY[" + ",".join(f"'{f}'" for f in fins) + "]"
        presup_arr = "ARRAY[" + ",".join(f"'{esc(p)}'" for p in presupuestos) + "]" if presupuestos else "ARRAY[]::TEXT[]"

        # Razonamiento como JSONB
        raz_json = json.dumps([{"paso": r[0], "operacion": r[1], "produce": r[2]} for r in razonamiento], ensure_ascii=False).replace("'", "''")

        lines.append(f"""INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('{esc(nombre)}', '{formula_text}', '{rama}', {fins_arr}, {gram_arr}, '{lectura}', '{resultado}', '{polo_bajo}', '{polo_alto}', '{eje}', {presup_arr}, '{raz_json}'::jsonb, '{si_alto}', '{si_bajo}', '{pregunta}')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;""")
        count += 1

    # También las fórmulas de marcos que no están en FORMULAS
    for marco, info in FORMULAS_MARCOS.items():
        for fn, fi in info.get("formulas_nuevas", {}).items():
            nombre_full = f"marco_{fn}"
            sem = SEMANTICA.get(nombre_full, {})
            if not sem:
                continue

            polos = sem.get("polos", ("bajo", "alto"))
            pregunta = esc(sem.get("pregunta", ""))
            fins = formula_finalidades.get(nombre_full, ["DIAGNOSTICAR"])
            fins_arr = "ARRAY[" + ",".join(f"'{f}'" for f in fins) + "]"

            lines.append(f"""INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, polo_bajo, polo_alto, eje, pregunta)
VALUES ('{esc(nombre_full)}', '{esc(fi.get("formula",""))}', '{marco}', {fins_arr}, ARRAY[]::TEXT[], '{esc(polos[0])}', '{esc(polos[1])}', '{esc(fi.get("eje",""))}', '{pregunta}')
ON CONFLICT (nombre) DO NOTHING;""")
            count += 1

    lines.insert(0, f"-- {count} fórmulas")
    return "\n".join(lines)


def generar_sql_isomorfismos():
    """Genera INSERTs para isomorfismos_gramatica."""
    from gramatica_formulas import detectar_isomorfismos, OPS

    lines = ["-- Isomorfismos de gramática"]
    lines.append("DELETE FROM isomorfismos_gramatica;")

    isos = detectar_isomorfismos()
    for seq, nombres in isos.items():
        ops_nombres = []
        for s in seq:
            for k, v in OPS.items():
                if v == s:
                    ops_nombres.append(k)
                    break

        ramas = list(set(FORMULAS[n]["rama"] for n in nombres if n in FORMULAS))
        es_cross = len(ramas) > 1
        gram_texto = "→".join(ops_nombres)

        def esc(s): return str(s).replace("'", "''")

        gram_arr = "ARRAY[" + ",".join(f"'{o}'" for o in ops_nombres) + "]" if ops_nombres else "ARRAY[]::TEXT[]"
        form_arr = "ARRAY[" + ",".join(f"'{n}'" for n in nombres) + "]"
        ramas_arr = "ARRAY[" + ",".join(f"'{r}'" for r in ramas) + "]"

        significado = f"Estas {len(nombres)} fórmulas comparten la gramática {gram_texto} — hacen la MISMA operación sobre dominios diferentes."
        if es_cross:
            significado += f" Cross-domain: {', '.join(ramas)}."

        lines.append(f"""INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES ({gram_arr}, '{esc(gram_texto)}', {form_arr}, {ramas_arr}, {len(nombres)}, {str(es_cross).lower()}, '{esc(significado)}');""")

    return "\n".join(lines)


def generar_sql_red():
    """Genera INSERTs para red_preguntas."""
    lines = ["-- Red de preguntas encadenadas"]
    lines.append("DELETE FROM red_preguntas;")

    for origen, enlaces in ENLACES.items():
        for condicion, destino, razon in enlaces:
            def esc(s): return str(s).replace("'", "''")
            lines.append(f"""INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('{esc(origen)}', '{esc(condicion)}', '{esc(destino)}', '{esc(razon)}')
ON CONFLICT DO NOTHING;""")

    return "\n".join(lines)


def generar_sql_patrones():
    """Genera INSERTs para patrones_historicos."""
    lines = ["-- Patrones históricos"]
    lines.append("DELETE FROM patrones_historicos;")

    for nombre, info in ISOMORFISMOS_CATALOGO.items():
        def esc(s): return str(s).replace("'", "''")
        señales_json = json.dumps(info["señales"], ensure_ascii=False).replace("'", "''")
        prec_arr = "ARRAY[" + ",".join(f"'{esc(p)}'" for p in info["precedentes"]) + "]"

        lines.append(f"""INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('{esc(nombre)}', '{esc(info["descripcion"])}', '{señales_json}'::jsonb, {prec_arr}, '{esc(info["prescripcion_historica"])}')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;""")

    return "\n".join(lines)


if __name__ == "__main__":
    print("Generando SQL para pgvector...")

    sql_formulas = generar_sql_formulas()
    sql_isos = generar_sql_isomorfismos()
    sql_red = generar_sql_red()
    sql_patrones = generar_sql_patrones()

    # Escribir archivo SQL completo
    sql_completo = "\n\n".join([
        "-- ============================================================",
        "-- CATÁLOGO COMPLETO — generado automáticamente",
        "-- Fecha: 2026-04-13",
        "-- ============================================================",
        "",
        sql_formulas,
        "",
        sql_isos,
        "",
        sql_red,
        "",
        sql_patrones,
    ])

    path = os.path.join(os.path.dirname(__file__), "../../data/poblar_catalogo_completo.sql")
    with open(path, "w") as f:
        f.write(sql_completo)

    # Stats
    n_formulas = sql_formulas.count("INSERT INTO catalogo_formulas")
    n_isos = sql_isos.count("INSERT INTO isomorfismos_gramatica")
    n_red = sql_red.count("INSERT INTO red_preguntas")
    n_patrones = sql_patrones.count("INSERT INTO patrones_historicos")

    print(f"  Fórmulas: {n_formulas}")
    print(f"  Isomorfismos: {n_isos}")
    print(f"  Enlaces red: {n_red}")
    print(f"  Patrones históricos: {n_patrones}")
    print(f"  SQL: {path} ({os.path.getsize(path) / 1024:.0f}KB)")
