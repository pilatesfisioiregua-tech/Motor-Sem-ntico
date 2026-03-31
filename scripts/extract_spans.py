#!/usr/bin/env python3
"""
extract_spans.py — Extracción de spans gramaticales para identificación de marco

Teoría (TEORIA_UNIFICADA §15):
  Razonamiento = función adjetival → sujeto + adjetivos predicativos
                 Los adjetivos son criterios de membresía en conjuntos
  Pensamiento  = función adverbial → sustantivos que modifican el verbo
                 Son nominalizaciones de procesos = vocabulario operacional

Output: JSON con spans + doble autenticación vs dims numéricas del DeBERTa

Uso:
  python extract_spans.py --text "La estrategia resulta ineficiente"
  python extract_spans.py --file textos.jsonl --output spans.jsonl
  python extract_spans.py --combine spans.jsonl dims.jsonl --output combined.jsonl
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    import spacy
except ImportError:
    print("ERROR: spacy no instalado. Ejecuta: pip install spacy")
    print("Luego: python -m spacy download es_dep_news_trf  (modelo transformer español)")
    print("O más rápido: python -m spacy download es_core_news_lg")
    sys.exit(1)


# ─────────────────────────────────────────────
# CARGA DE MODELO
# ─────────────────────────────────────────────

def load_model():
    """Carga el mejor modelo spaCy disponible para español."""
    models = [
        "es_dep_news_trf",    # transformer — mejor para dependency parsing
        "es_core_news_lg",    # CNN grande — bueno y rápido
        "es_core_news_md",    # CNN mediano — fallback
        "es_core_news_sm",    # CNN pequeño — último recurso
    ]
    for model_name in models:
        try:
            nlp = spacy.load(model_name)
            print(f"[spaCy] Modelo cargado: {model_name}", file=sys.stderr)
            return nlp
        except OSError:
            continue
    print("ERROR: No hay ningún modelo spaCy español instalado.", file=sys.stderr)
    print("Instala con: python -m spacy download es_core_news_lg", file=sys.stderr)
    sys.exit(1)


# ─────────────────────────────────────────────
# EXTRACCIÓN DE SPANS
# ─────────────────────────────────────────────

# Relaciones de dependencia spaCy que corresponden a cada posición gramatical
SUBJ_DEPS      = {"nsubj", "nsubj:pass", "csubj"}
ADJ_PRED_DEPS  = {"obj", "attr", "acomp", "xcomp"}  # adjetivos predicativos en español
ADV_OBL_DEPS   = {"obl", "obl:mod", "obl:arg"}       # complementos oblicuos (con prep)
VERB_DEPS      = {"ROOT", "conj", "advcl", "ccomp", "xcomp"}

# Categorías morfológicas
NOUN_POS   = {"NOUN", "PROPN"}
ADJ_POS    = {"ADJ"}
VERB_POS   = {"VERB", "AUX"}


def extract_spans(text: str, nlp) -> dict:
    """
    Extrae los spans gramaticales que revelan el marco del observador.

    Returns:
        {
          "razonamiento": {
            "sujetos": [...],           # entidades que el observador pone en el centro
            "adjetivales": [...],       # criterios de membresía en conjuntos
            "pares": [                  # sujeto → adjetivo (la asignación a conjunto)
              {"sujeto": "...", "adjetivo": "...", "verbo_copula": "..."}
            ]
          },
          "pensamiento": {
            "verbos": [...],            # procesos ejecutados
            "sustantivos_adverbiales": [...],  # vocab operacional (cómo se ejecutan)
            "pares": [
              {"verbo": "...", "modificador": "...", "prep": "..."}
            ]
          },
          "marco_proxy": {
            "vocabulario_sujeto": [...],    # palabras del sujeto → marco del observador
            "vocabulario_adverbial": [...], # palabras adverbiales → cómo opera
            "dominio_inferido": "..."       # inferencia simple de dominio
          }
        }
    """
    doc = nlp(text)
    result = {
        "razonamiento": {"sujetos": [], "adjetivales": [], "pares": []},
        "pensamiento":  {"verbos": [],  "sustantivos_adverbiales": [], "pares": []},
        "marco_proxy":  {"vocabulario_sujeto": [], "vocabulario_adverbial": [], "dominio_inferido": None}
    }

    for token in doc:

        # ── RAZONAMIENTO: sujetos + sus modificadores adjetivales ──────────────

        if token.dep_ in SUBJ_DEPS:
            subj_text = _get_span(token, include_det=True)
            subj_lemma = token.lemma_.lower()

            if subj_text not in result["razonamiento"]["sujetos"]:
                result["razonamiento"]["sujetos"].append(subj_text)
            if subj_lemma not in result["marco_proxy"]["vocabulario_sujeto"]:
                result["marco_proxy"]["vocabulario_sujeto"].append(subj_lemma)

            # Adjetivos predicativos: verbo copulativo/semi-copulativo → atributo/obj ADJ
            head = token.head
            if head.pos_ in VERB_POS:
                for child in head.children:
                    # En español: adjetivo predicativo puede ser dep=obj, attr, acomp, xcomp
                    if child.dep_ in ADJ_PRED_DEPS and child.pos_ in ADJ_POS:
                        adj_text = _get_span(child)
                        result["razonamiento"]["adjetivales"].append(adj_text)
                        result["razonamiento"]["pares"].append({
                            "sujeto":       subj_text,
                            "adjetivo":     adj_text,
                            "verbo_copula": head.text
                        })

            # Adjetivos atributivos: modifican directamente al sujeto
            for child in token.children:
                if child.dep_ in {"amod"} and child.pos_ in ADJ_POS:
                    adj_text = child.text
                    if adj_text not in result["razonamiento"]["adjetivales"]:
                        result["razonamiento"]["adjetivales"].append(adj_text)

        # ── PENSAMIENTO: verbos + sustantivos en función adverbial ─────────────

        if token.dep_ in VERB_DEPS and token.pos_ in VERB_POS:
            if not _is_copula(token):
                verb_text = token.lemma_
                if verb_text not in result["pensamiento"]["verbos"]:
                    result["pensamiento"]["verbos"].append(verb_text)

                # Modificadores del verbo: adverbios + oblicuos preposicionales
                for child in token.children:

                    # Adverbio simple
                    if child.dep_ == "advmod" and child.pos_ == "ADV":
                        mod_text = child.text
                        if mod_text not in result["pensamiento"]["sustantivos_adverbiales"]:
                            result["pensamiento"]["sustantivos_adverbiales"].append(mod_text)
                        result["pensamiento"]["pares"].append({
                            "verbo": verb_text, "modificador": mod_text, "prep": None
                        })

                    # Oblicuo preposicional: en español el NOUN tiene dep=obl y su prep
                    # es un hijo con dep=case. Estructura: trabaja → eficiencia(obl) → con(case)
                    if child.dep_ in ADV_OBL_DEPS and child.pos_ in NOUN_POS:
                        nom_lemma = child.lemma_.lower()
                        # Buscar la preposición (case) entre los hijos del sustantivo
                        prep_text = None
                        for grandchild in child.children:
                            if grandchild.dep_ == "case" and grandchild.pos_ == "ADP":
                                prep_text = grandchild.text
                                break
                        full_mod = f"{prep_text} {child.text}" if prep_text else child.text

                        if full_mod not in result["pensamiento"]["sustantivos_adverbiales"]:
                            result["pensamiento"]["sustantivos_adverbiales"].append(full_mod)
                        if nom_lemma not in result["marco_proxy"]["vocabulario_adverbial"]:
                            result["marco_proxy"]["vocabulario_adverbial"].append(nom_lemma)
                        result["pensamiento"]["pares"].append({
                            "verbo": verb_text, "modificador": full_mod, "prep": prep_text
                        })

                    # Objeto directo nominal → vocabulario del marco operacional
                    if child.dep_ in {"obj", "dobj"} and child.pos_ in NOUN_POS:
                        nom_lemma = child.lemma_.lower()
                        if nom_lemma not in result["marco_proxy"]["vocabulario_adverbial"]:
                            result["marco_proxy"]["vocabulario_adverbial"].append(nom_lemma)

    # ── INFERENCIA DE DOMINIO PROXY ────────────────────────────────────────────
    result["marco_proxy"]["dominio_inferido"] = _infer_domain(
        result["marco_proxy"]["vocabulario_sujeto"] +
        result["marco_proxy"]["vocabulario_adverbial"]
    )

    return result


def _get_span(token, include_det=False) -> str:
    """Obtiene el span completo de un token incluyendo modificadores relevantes."""
    if include_det:
        # Incluir determinante + adjetivos previos
        parts = []
        for child in sorted(token.children, key=lambda t: t.i):
            if child.i < token.i and child.dep_ in {"det", "amod"}:
                parts.append(child.text)
        parts.append(token.text)
        return " ".join(parts)
    return token.text


def _is_copula(token) -> bool:
    """Detecta verbos copulativos (ser, estar, parecer, resultar, etc.)."""
    COPULAS = {"ser", "estar", "parecer", "resultar", "quedar", "volverse",
               "hacerse", "convertirse", "seguir", "continuar", "permanecer",
               "mostrarse", "revelarse", "considerarse", "verse", "sentirse"}
    return token.lemma_.lower() in COPULAS


# Vocabulario proxy simple para inferencia de dominio
# (el LLM hace esto mejor — esto es solo una señal de baja resolución)
DOMAIN_VOCAB = {
    "financiero":    {"rentabilidad", "margen", "coste", "inversión", "retorno",
                      "beneficio", "deuda", "capital", "liquidez", "flujo"},
    "estratégico":   {"estrategia", "posición", "ventaja", "competencia", "mercado",
                      "diferenciación", "segmento", "cuota", "barrera"},
    "operativo":     {"proceso", "eficiencia", "implementación", "ejecución", "recurso",
                      "capacidad", "productividad", "operación", "sistema"},
    "social":        {"equipo", "persona", "relación", "confianza", "cultura",
                      "comunicación", "colaboración", "liderazgo", "cliente"},
    "computacional": {"algoritmo", "dato", "modelo", "sistema", "automatización",
                      "código", "función", "proceso", "variable", "output"},
    "ecológico":     {"ecosistema", "sostenibilidad", "interdependencia", "ciclo",
                      "energía", "flujo", "equilibrio", "regeneración"},
}

def _infer_domain(words: list) -> Optional[str]:
    """Inferencia de dominio de baja resolución. El LLM es el intérprete real."""
    if not words:
        return None
    scores = {domain: 0 for domain in DOMAIN_VOCAB}
    for word in words:
        for domain, vocab in DOMAIN_VOCAB.items():
            if word in vocab:
                scores[domain] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


# ─────────────────────────────────────────────
# COMBINACIÓN SPANS + DIMS (doble autenticación)
# ─────────────────────────────────────────────

def combine_with_dims(spans: dict, dims: dict) -> dict:
    """
    Combina spans gramaticales con dimensiones numéricas del DeBERTa.
    Detecta divergencias (la divergencia es el dato más valioso).
    """
    combined = {
        "spans": spans,
        "dims":  dims,
        "autenticacion": _compute_authentication(spans, dims)
    }
    return combined


def _compute_authentication(spans: dict, dims: dict) -> dict:
    """
    Calcula coherencia entre señal léxica (spans) y señal estructural (dims).
    Divergencia > 0.3 = señal de operación cognitiva de orden superior.
    """
    auth = {
        "convergencia": [],   # dims y spans apuntan al mismo marco
        "divergencia":  [],   # apuntan a marcos distintos → metáfora / reencuadre
        "score_global": None
    }

    # Proxy: comparar dominio inferido del span vs INT más alta del dim
    domain_span = spans.get("marco_proxy", {}).get("dominio_inferido")

    domain_dim = None
    if dims:
        int_dims = {k: v for k, v in dims.items() if k.startswith("int_")}
        if int_dims:
            top_int = max(int_dims, key=int_dims.get)
            # Mapeo simple INT → dominio
            INT_TO_DOMAIN = {
                "int_07_financiera":  "financiero",
                "int_05_estrategica": "estratégico",
                "int_16_operativa":   "operativo",
                "int_08_social":      "social",
                "int_02_computacional": "computacional",
                "int_03_ecologica":   "ecológico",
            }
            domain_dim = INT_TO_DOMAIN.get(top_int)

    if domain_span and domain_dim:
        if domain_span == domain_dim:
            auth["convergencia"].append(f"marco: {domain_span}")
            auth["score_global"] = 1.0
        else:
            auth["divergencia"].append({
                "span_dice":    domain_span,
                "dim_dice":     domain_dim,
                "interpretacion": f"Vocabulario de '{domain_span}' aplicado a estructura de '{domain_dim}' — posible reencuadre o metáfora de marco"
            })
            auth["score_global"] = 0.3  # baja convergencia = señal valiosa

    return auth


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extrae spans gramaticales como vocabulario de marco de referencia"
    )
    parser.add_argument("--text",    type=str, help="Texto directo a analizar")
    parser.add_argument("--file",    type=str, help="Archivo JSONL con campo 'text'")
    parser.add_argument("--output",  type=str, help="Archivo de salida JSONL")
    parser.add_argument("--combine", nargs=2, metavar=("SPANS_FILE", "DIMS_FILE"),
                        help="Combinar spans JSONL con dims JSONL para doble autenticación")
    parser.add_argument("--pretty",  action="store_true", help="Output JSON indentado")
    args = parser.parse_args()

    # ── Modo combinación ──────────────────────────────────────────────────────
    if args.combine:
        spans_path, dims_path = args.combine
        spans_data = [json.loads(l) for l in open(spans_path)]
        dims_data  = [json.loads(l) for l in open(dims_path)]

        out_lines = []
        for spans_row, dims_row in zip(spans_data, dims_data):
            combined = combine_with_dims(
                spans_row.get("spans", spans_row),
                dims_row.get("dims",  dims_row)
            )
            out_lines.append(combined)

        _write_output(out_lines, args.output, args.pretty)
        return

    # ── Carga modelo ─────────────────────────────────────────────────────────
    nlp = load_model()

    # ── Modo texto directo ────────────────────────────────────────────────────
    if args.text:
        result = extract_spans(args.text, nlp)
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
        return

    # ── Modo archivo JSONL ────────────────────────────────────────────────────
    if args.file:
        results = []
        with open(args.file) as f:
            for i, line in enumerate(f):
                row  = json.loads(line.strip())
                text = row.get("text", row.get("texto", ""))
                if not text:
                    continue
                spans = extract_spans(text, nlp)
                results.append({**row, "spans": spans})
                if (i + 1) % 100 == 0:
                    print(f"  {i+1} textos procesados", file=sys.stderr)

        _write_output(results, args.output, args.pretty)
        return

    # ── Modo stdin ────────────────────────────────────────────────────────────
    print("Introduce texto (Ctrl+D para terminar):", file=sys.stderr)
    text = sys.stdin.read().strip()
    if text:
        nlp = load_model()
        result = extract_spans(text, nlp)
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))


def _write_output(data: list, output_path: Optional[str], pretty: bool):
    indent = 2 if pretty else None
    if output_path:
        with open(output_path, "w") as f:
            for row in data:
                f.write(json.dumps(row, ensure_ascii=False, indent=indent) + "\n")
        print(f"[OK] {len(data)} registros → {output_path}", file=sys.stderr)
    else:
        for row in data:
            print(json.dumps(row, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
