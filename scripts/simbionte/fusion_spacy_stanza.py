"""
Fusion spaCy + Stanza — Lo mejor de cada libreria
Fecha: 2026-04-12

spaCy (es_dep_news_trf):
  + Rapido (~80ms), buen modelo transformer (BETO)
  + POS/DEP/MORPH fiables para espanol
  - NO separa encliticos ("delegarselo" = 1 token)
  - Deps a veces superficiales en subordinadas complejas

Stanza (es_ancora):
  + MWT: separa encliticos ("delegarselo" → "delegar" + "se" + "lo")
  + Deps profundas en ancora (gold standard para espanol)
  - Mas lento (~200ms), menos mantenido que spaCy

Fusion: spaCy como base + Stanza para encliticos y deps profundas cuando detectadas.

Ref: CAPA_0_ESPECIFICACION.md §2 "Librerias NLP"
"""

import spacy
import stanza
import numpy as np
from typing import List, Dict, Optional, Tuple


class FusionNLP:
    """Procesador fusionado spaCy + Stanza."""

    def __init__(self, use_stanza=True):
        """Carga modelos.

        Args:
            use_stanza: Si True, usa Stanza para encliticos y deps profundas.
                       Si False, solo spaCy (modo rapido).
        """
        self.nlp_spacy = spacy.load("es_dep_news_trf")
        self.use_stanza = use_stanza

        if use_stanza:
            self.nlp_stanza = stanza.Pipeline(
                "es", package="ancora",
                processors="tokenize,mwt,pos,lemma,depparse",
                verbose=False
            )

    def process(self, texto: str) -> Dict:
        """Procesa texto con fusion spaCy + Stanza.

        Returns:
            dict con:
                - doc_spacy: documento spaCy original
                - tokens: lista unificada de tokens con campos fusionados
                - encliticos_expandidos: tokens expandidos por Stanza MWT
                - deps_profundas: deps de Stanza donde difieren de spaCy
                - stats: estadisticas de la fusion
        """
        # 1. spaCy (siempre, es la base)
        doc_spacy = self.nlp_spacy(texto)

        if not self.use_stanza:
            tokens = self._tokens_from_spacy(doc_spacy)
            return {
                "doc_spacy": doc_spacy,
                "tokens": tokens,
                "encliticos_expandidos": [],
                "deps_profundas": [],
                "stats": {"n_tokens_spacy": len(tokens), "n_encliticos": 0,
                          "n_deps_diff": 0, "modo": "spacy_only"},
            }

        # 2. Stanza (para encliticos + deps profundas)
        doc_stanza = self.nlp_stanza(texto)

        # 3. Detectar encliticos (MWT de Stanza)
        encliticos = self._detectar_encliticos(doc_stanza)

        # 4. Detectar deps profundas donde Stanza difiere de spaCy
        deps_diff = self._comparar_deps(doc_spacy, doc_stanza)

        # 5. Fusionar tokens
        tokens = self._fusionar(doc_spacy, doc_stanza, encliticos, deps_diff)

        return {
            "doc_spacy": doc_spacy,
            "tokens": tokens,
            "encliticos_expandidos": encliticos,
            "deps_profundas": deps_diff,
            "stats": {
                "n_tokens_spacy": len([t for t in doc_spacy if not t.is_punct and not t.is_space]),
                "n_tokens_fusion": len(tokens),
                "n_encliticos": len(encliticos),
                "n_deps_diff": len(deps_diff),
                "modo": "fusion",
            },
        }

    def _tokens_from_spacy(self, doc) -> List[Dict]:
        """Extrae tokens en formato unificado desde spaCy."""
        tokens = []
        for t in doc:
            if t.is_punct or t.is_space:
                continue
            tokens.append({
                "text": t.text,
                "lemma": t.lemma_,
                "upos": t.pos_,
                "dep": t.dep_,
                "head_text": t.head.text if t.head != t else "ROOT",
                "morph": str(t.morph),
                "i": t.i,
                "sent_i": t.sent.start if hasattr(t, 'sent') else 0,
                "source": "spacy",
                "is_enclitico": False,
            })
        return tokens

    def _detectar_encliticos(self, doc_stanza) -> List[Dict]:
        """Detecta MWT (Multi-Word Tokens) de Stanza = encliticos separados."""
        encliticos = []
        for sent in doc_stanza.sentences:
            for token in sent.tokens:
                # MWT real: el token tiene MAS de 1 word (enclitico expandido)
                if len(token.words) > 1:
                    partes = []
                    for word in token.words:
                        partes.append({
                            "text": word.text,
                            "lemma": word.lemma,
                            "upos": word.upos,
                            "dep": word.deprel,
                            "feats": word.feats or "",
                        })
                    encliticos.append({
                        "original": token.text,
                        "partes": partes,
                        "n_partes": len(partes),
                    })
        return encliticos

    def _comparar_deps(self, doc_spacy, doc_stanza) -> List[Dict]:
        """Compara deps de spaCy vs Stanza. Reporta donde difieren."""
        diffs = []

        # Alinear tokens por posicion (aproximado)
        spacy_toks = [(t.text.lower(), t.dep_, t.pos_) for t in doc_spacy if not t.is_punct and not t.is_space]

        stanza_toks = []
        for sent in doc_stanza.sentences:
            for word in sent.words:
                if word.upos not in ("PUNCT",):
                    stanza_toks.append((word.text.lower(), word.deprel, word.upos))

        # Comparar token a token (misma posicion)
        for i in range(min(len(spacy_toks), len(stanza_toks))):
            sp_text, sp_dep, sp_pos = spacy_toks[i]
            st_text, st_dep, st_pos = stanza_toks[i]

            if sp_text == st_text and sp_dep != st_dep:
                diffs.append({
                    "text": sp_text,
                    "pos": i,
                    "dep_spacy": sp_dep,
                    "dep_stanza": st_dep,
                    "pos_spacy": sp_pos,
                    "pos_stanza": st_pos,
                })

        return diffs

    def _fusionar(self, doc_spacy, doc_stanza, encliticos, deps_diff) -> List[Dict]:
        """Fusiona tokens: base spaCy + encliticos Stanza + deps profundas Stanza."""
        tokens = self._tokens_from_spacy(doc_spacy)

        # Marcar tokens que son encliticos no separados
        enclitico_texts = {e["original"].lower() for e in encliticos}
        for t in tokens:
            if t["text"].lower() in enclitico_texts:
                t["is_enclitico"] = True
                # Buscar las partes expandidas
                for enc in encliticos:
                    if enc["original"].lower() == t["text"].lower():
                        t["enclitico_partes"] = enc["partes"]
                        break

        # Actualizar deps donde Stanza tiene mejor analisis
        # Solo para deps que son "profundas" (subordinacion compleja)
        DEPS_PROFUNDAS = {"advcl", "ccomp", "xcomp", "acl", "acl:relcl", "csubj"}
        diff_map = {d["text"]: d for d in deps_diff}
        for t in tokens:
            key = t["text"].lower()
            if key in diff_map:
                diff = diff_map[key]
                # Si Stanza dice dep profunda y spaCy no, preferir Stanza
                if diff["dep_stanza"] in DEPS_PROFUNDAS and diff["dep_spacy"] not in DEPS_PROFUNDAS:
                    t["dep_original"] = t["dep"]
                    t["dep"] = diff["dep_stanza"]
                    t["source"] = "stanza_dep"

        return tokens


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import time

    print("Cargando modelos (spaCy + Stanza)...")
    t0 = time.time()
    fusion = FusionNLP(use_stanza=True)
    print(f"  Carga: {time.time()-t0:.1f}s")

    # Test con encliticos
    textos = [
        "Me gustaría delegárselo pero la gestión es compleja",
        "Dígamelo usted mismo cuando pueda confirmármelo",
        "La empresa había facturado 47 millones durante el período",
    ]

    for texto in textos:
        print(f"\n{'='*60}")
        print(f"INPUT: {texto}")
        t0 = time.time()
        result = fusion.process(texto)
        dt = time.time() - t0

        print(f"  Tiempo: {dt*1000:.0f}ms")
        print(f"  Stats: {result['stats']}")

        if result["encliticos_expandidos"]:
            print(f"  ENCLÍTICOS:")
            for enc in result["encliticos_expandidos"]:
                partes_str = " + ".join(f"{p['text']}({p['upos']})" for p in enc["partes"])
                print(f"    \"{enc['original']}\" → {partes_str}")

        if result["deps_profundas"]:
            print(f"  DEPS DIFERENTES:")
            for d in result["deps_profundas"]:
                print(f"    \"{d['text']}\": spaCy={d['dep_spacy']} vs Stanza={d['dep_stanza']}")
