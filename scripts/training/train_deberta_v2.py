#!/usr/bin/env python3
"""
OMNI-MIND Detector v2.1 — Entrenamiento DeBERTa 2-head + spans
================================================================
Evolución post-P48: categoricals eliminados. R/P/I son 3 floats independientes.

Cambios vs v2.0:
  - CATEGORICAL HEAD ELIMINADA (P48: R,P son partes de I, no clases excluyentes)
  - posicion_R, posicion_P, posicion_I ahora son floats en float_dims
  - DUAL LOSS: alpha×MSE + beta×BCE (no gamma×CE)
  - Restriccion ontologica verificable post-training: I>0 implica R>0 o P>0

2 heads:
  1. FLOAT HEAD: sigmoid → MSE loss (38 dims originales + 3 posicion R/P/I + profundidad)
  2. BINARY HEAD: sigmoid → BCE loss (10 sesgos cognitivos)

Uso:
  python train_deberta_v2.py \\
      --labels data/gold_set_v2_3000.jsonl \\
      --dims configs/v2_51_dims.json \\
      --output-dir experiments/v2/checkpoints \\
      --epochs 15 \\
      --lr 2e-5 \\
      --batch-size 8 \\
      --wandb-name v2.1_3000

Arquitectura:
  Texto
    ↓
  spaCy → span_features (n_sujetos, n_adjetivales, n_adverbiales, ...)
    ↓
  DeBERTa → CLS token (768d)
    ↓
  [CLS ⊕ span_features] (768 + span_dim)
    ↓
  ├── Float head:  Linear → sigmoid → MSE loss
  └── Binary head: Linear → sigmoid → BCE loss
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Dependencias ──────────────────────────────────────────────────────────
_missing = []
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
except ImportError:
    _missing.append("torch")
try:
    from transformers import AutoModel, AutoTokenizer
except ImportError:
    _missing.append("transformers")
try:
    import numpy as np
except ImportError:
    _missing.append("numpy")
try:
    from scipy.stats import pearsonr
except ImportError:
    _missing.append("scipy")
try:
    from sklearn.metrics import f1_score
except ImportError:
    _missing.append("scikit-learn")
try:
    import wandb
    HAS_WANDB = True
except ImportError:
    HAS_WANDB = False

if _missing:
    print(f"ERROR: Dependencias faltantes: {', '.join(_missing)}")
    sys.exit(1)

# PEFT/LoRA es opcional
try:
    from peft import LoraConfig, get_peft_model, TaskType
    HAS_PEFT = True
except ImportError:
    HAS_PEFT = False
    print("WARNING: peft no instalado. Sin LoRA. pip install peft")

# spaCy es opcional — si no está, skip span features
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    print("WARNING: spaCy no instalado. Sin span features. pip install spacy")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("train_deberta_v2")


# ── Span Feature Extractor ───────────────────────────────────────────────

SPAN_DIM = 12  # número de features extraídas por spaCy

def load_spacy_model():
    """Carga el mejor modelo spaCy disponible."""
    if not HAS_SPACY:
        return None
    for model_name in ["es_dep_news_trf", "es_core_news_lg", "es_core_news_md", "es_core_news_sm"]:
        try:
            nlp = spacy.load(model_name)
            log.info(f"spaCy modelo: {model_name}")
            return nlp
        except OSError:
            continue
    log.warning("No hay modelo spaCy español. Sin span features.")
    return None


def extract_span_features(text: str, nlp) -> list[float]:
    """
    Extrae features numéricas de los spans gramaticales.
    Basado en extract_spans.py pero produciendo un vector numérico fijo.

    Returns:
        Vector de SPAN_DIM floats normalizados [0, 1]
    """
    if nlp is None:
        return [0.0] * SPAN_DIM

    doc = nlp(text[:1000])  # limitar para velocidad
    total_tokens = len(doc) if len(doc) > 0 else 1

    # Contadores
    n_subj = 0          # sujetos
    n_adj_pred = 0      # adjetivos predicativos
    n_adj_attr = 0      # adjetivos atributivos
    n_verb_cop = 0      # verbos copulativos
    n_verb_act = 0      # verbos de acción
    n_adv = 0           # adverbios
    n_obl = 0           # oblicuos (sustantivos adverbiales)
    n_nom = 0           # nominalizaciones (heurística: sustantivos abstractos con sufijo)
    n_subord = 0        # subordinación (profundidad)
    max_depth = 0       # profundidad máxima del árbol

    COPULAS = {"ser", "estar", "parecer", "resultar", "quedar", "volverse",
               "hacerse", "convertirse", "seguir", "continuar", "permanecer"}
    NOM_SUFFIXES = {"ción", "sión", "miento", "ncia", "dad", "eza", "ura", "aje"}

    for token in doc:
        # Sujetos
        if token.dep_ in {"nsubj", "nsubj:pass", "csubj"}:
            n_subj += 1

        # Adjetivos predicativos
        if token.dep_ in {"obj", "attr", "acomp", "xcomp"} and token.pos_ == "ADJ":
            n_adj_pred += 1
        if token.dep_ == "amod" and token.pos_ == "ADJ":
            n_adj_attr += 1

        # Verbos
        if token.pos_ in {"VERB", "AUX"}:
            if token.lemma_.lower() in COPULAS:
                n_verb_cop += 1
            else:
                n_verb_act += 1

        # Adverbios
        if token.dep_ == "advmod" and token.pos_ == "ADV":
            n_adv += 1

        # Oblicuos (sustantivos en función adverbial)
        if token.dep_ in {"obl", "obl:mod", "obl:arg"} and token.pos_ in {"NOUN", "PROPN"}:
            n_obl += 1

        # Nominalizaciones (heurística por sufijo)
        if token.pos_ == "NOUN":
            for suf in NOM_SUFFIXES:
                if token.text.lower().endswith(suf):
                    n_nom += 1
                    break

        # Subordinación
        if token.dep_ in {"advcl", "ccomp", "acl", "relcl"}:
            n_subord += 1

        # Profundidad del árbol
        depth = 0
        t = token
        while t.head != t:
            depth += 1
            t = t.head
        max_depth = max(max_depth, depth)

    # Normalizar a [0, 1] dividiendo por total_tokens (excepto max_depth)
    features = [
        n_subj / total_tokens,                    # 0: densidad sujetos
        n_adj_pred / total_tokens,                 # 1: densidad adj predicativos
        n_adj_attr / total_tokens,                 # 2: densidad adj atributivos
        n_verb_cop / max(n_verb_cop + n_verb_act, 1),  # 3: ratio copulativos / total verbos
        n_verb_act / total_tokens,                 # 4: densidad verbos acción
        n_adv / total_tokens,                      # 5: densidad adverbios
        n_obl / total_tokens,                      # 6: densidad oblicuos (sust adverbiales)
        n_nom / total_tokens,                      # 7: densidad nominalizaciones
        n_subord / total_tokens,                   # 8: densidad subordinación
        min(max_depth / 10.0, 1.0),                # 9: profundidad normalizada (max ~10)
        n_verb_cop / total_tokens,                 # 10: densidad copulativos absoluta
        (n_adj_pred + n_adj_attr) / total_tokens,  # 11: densidad adjetival total
    ]

    return features


# ── Dataset ───────────────────────────────────────────────────────────────

class LabeledTextDatasetV2(Dataset):
    """Dataset con float + binary labels + span features. Sin categoricals (P48)."""

    def __init__(
        self,
        data: list[dict],
        tokenizer,
        float_dims: list[str],
        binary_dims: list[str],
        span_features: list[list[float]] | None = None,
        max_length: int = 512,
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.float_dims = float_dims
        self.binary_dims = binary_dims
        self.span_features = span_features
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item.get("text", item.get("texto", ""))
        labels = item.get("labels", {})

        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        float_values = [float(labels.get(d, 0.0) or 0.0) for d in self.float_dims]
        binary_values = [float(labels.get(d, 0.0) or 0.0) for d in self.binary_dims]

        # Span features
        if self.span_features is not None:
            spans = self.span_features[idx]
        else:
            spans = [0.0] * SPAN_DIM

        result = {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "float_labels": torch.tensor(float_values, dtype=torch.float32),
            "binary_labels": torch.tensor(binary_values, dtype=torch.float32),
            "span_features": torch.tensor(spans, dtype=torch.float32),
        }
        return result


# ── Modelo ────────────────────────────────────────────────────────────────

class MultiHeadDetectorV2(nn.Module):
    """
    DeBERTa con 2 cabezas (P48: sin categorical head):
      - Float head:  Linear(hidden + span_dim, n_float) + sigmoid
      - Binary head: Linear(hidden + span_dim, n_binary) + sigmoid
    """

    def __init__(
        self,
        model_name: str,
        n_float: int,
        n_binary: int,
        span_dim: int = SPAN_DIM,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        hidden_size = self.backbone.config.hidden_size
        combined_size = hidden_size + span_dim

        self.dropout = nn.Dropout(dropout)

        # Projection layer para combinar CLS + spans
        self.projection = nn.Sequential(
            nn.Linear(combined_size, hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Float head
        self.float_head = nn.Linear(hidden_size, n_float)

        # Binary head
        self.binary_head = nn.Linear(hidden_size, n_binary)

        # Init
        for head in [self.float_head, self.binary_head]:
            nn.init.xavier_uniform_(head.weight)
            nn.init.zeros_(head.bias)

    def forward(self, input_ids, attention_mask, span_features):
        outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]  # CLS token

        # Concatenar span features al CLS
        combined = torch.cat([cls_output, span_features], dim=1)
        combined = self.projection(combined)
        combined = self.dropout(combined)

        float_out = torch.sigmoid(self.float_head(combined))
        binary_logits = self.binary_head(combined)  # raw logits para BCEWithLogitsLoss

        return float_out, binary_logits


# ── Funciones auxiliares ──────────────────────────────────────────────────

def load_data(path: str) -> list[dict]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "labels" in obj:
                    data.append(obj)
            except json.JSONDecodeError:
                log.warning(f"Linea {i+1} no es JSON valido")
    return data


def split_data(data, ratios, seed=42):
    np.random.seed(seed)
    indices = np.random.permutation(len(data))
    n_train = int(len(data) * ratios[0])
    n_val = int(len(data) * ratios[1])
    return (
        [data[i] for i in indices[:n_train]],
        [data[i] for i in indices[n_train:n_train + n_val]],
        [data[i] for i in indices[n_train + n_val:]],
    )


def precompute_spans(data: list[dict], nlp) -> list[list[float]]:
    """Pre-computa span features para todo el dataset."""
    log.info(f"Pre-computando span features para {len(data)} textos...")
    spans = []
    for i, item in enumerate(data):
        text = item.get("text", item.get("texto", ""))
        spans.append(extract_span_features(text, nlp))
        if (i + 1) % 500 == 0:
            log.info(f"  {i+1}/{len(data)} spans extraídos")
    log.info(f"  Span features completos: {len(spans)} × {SPAN_DIM}")
    return spans


def compute_metrics_v2(model, dataloader, float_dims, binary_dims, device,
                       dim_difficulty: dict | None = None):
    """Métricas para las 2 cabezas (sin categorical).

    Args:
        dim_difficulty: opcional dict {dim_name: "easy"|"medium"|"hard"} para métricas por grupo.
    """
    model.eval()
    all_fp, all_fl = [], []
    all_bp, all_bl = [], []

    with torch.no_grad():
        for batch in dataloader:
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            spans = batch["span_features"].to(device)

            fo, bo = model(ids, mask, spans)

            all_fp.append(fo.cpu().numpy())
            all_fl.append(batch["float_labels"].numpy())
            # bo son logits raw — aplicar sigmoid para métricas
            all_bp.append(torch.sigmoid(bo).cpu().numpy())
            all_bl.append(batch["binary_labels"].numpy())

    fp = np.concatenate(all_fp)
    fl = np.concatenate(all_fl)
    bp = np.concatenate(all_bp)
    bl = np.concatenate(all_bl)

    metrics = {}

    # Float: Pearson + MAE
    corrs = []
    maes = []
    for i, name in enumerate(float_dims):
        mae = float(np.mean(np.abs(fp[:, i] - fl[:, i])))
        maes.append(mae)
        metrics[f"mae/{name}"] = mae
        if np.std(fl[:, i]) > 1e-6 and np.std(fp[:, i]) > 1e-6:
            corr, _ = pearsonr(fp[:, i], fl[:, i])
            if not np.isnan(corr):
                corrs.append(corr)
                metrics[f"corr/{name}"] = float(corr)

    # Binary: F1
    f1s = []
    bp_hard = (bp > 0.5).astype(int)
    for i, name in enumerate(binary_dims):
        f1 = f1_score(bl[:, i].astype(int), bp_hard[:, i], zero_division=0)
        f1s.append(f1)
        metrics[f"f1/{name}"] = float(f1)

    # Posicion R/P/I: métricas especiales
    rpi_names = ["posicion_R", "posicion_P", "posicion_I"]
    for rpi in rpi_names:
        if rpi in float_dims:
            idx = float_dims.index(rpi)
            metrics[f"mean/{rpi}"] = float(np.mean(fp[:, idx]))
            metrics[f"std/{rpi}"] = float(np.std(fp[:, idx]))

    # Verificar restriccion ontologica P48: I>0.1 implica R>0.1 o P>0.1
    if all(rpi in float_dims for rpi in rpi_names):
        idx_r = float_dims.index("posicion_R")
        idx_p = float_dims.index("posicion_P")
        idx_i = float_dims.index("posicion_I")
        i_active = fp[:, idx_i] > 0.1
        if np.sum(i_active) > 0:
            rp_active = (fp[i_active, idx_r] > 0.1) | (fp[i_active, idx_p] > 0.1)
            metrics["p48_compliance"] = float(np.mean(rp_active))

    metrics["corr_global"] = float(np.mean(corrs)) if corrs else 0.0
    metrics["mae_global"] = float(np.mean(maes)) if maes else 0.0
    metrics["f1_global"] = float(np.mean(f1s)) if f1s else 0.0

    # ── Métricas por grupo de dificultad ──────────────────────────────────
    if dim_difficulty:
        group_corrs = {"easy": [], "medium": [], "hard": []}
        all_dims = float_dims + binary_dims
        all_scores = []
        for name in float_dims:
            c = metrics.get(f"corr/{name}", 0.0)
            all_scores.append((name, c))
        for name in binary_dims:
            f = metrics.get(f"f1/{name}", 0.0)
            all_scores.append((name, f))

        for name, score in all_scores:
            group = dim_difficulty.get(name)
            if group in group_corrs:
                group_corrs[group].append(score)

        for group, scores in group_corrs.items():
            if scores:
                metrics[f"group_{group}_mean"] = float(np.mean(scores))
                metrics[f"group_{group}_count"] = len(scores)

    return metrics


def get_cosine_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps):
    def lr_lambda(current_step):
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(
            max(1, num_training_steps - num_warmup_steps))
        return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DeBERTa v2.1 dual-head + spans (sin categoricals)")
    parser.add_argument("--labels", required=True)
    parser.add_argument("--dims", required=True)
    parser.add_argument("--model", default="microsoft/deberta-v3-base")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--grad-accum", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--split", default="0.8,0.1,0.1")
    parser.add_argument("--wandb-name", default=None)
    parser.add_argument("--wandb-project", default="omni-mind-detector")
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--loss-alpha", type=float, default=0.7, help="Peso MSE (float dims)")
    parser.add_argument("--loss-beta", type=float, default=0.3, help="Peso BCE (binary dims)")
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--no-spans", action="store_true", help="Desactivar span features")
    # ── LoRA ──
    parser.add_argument("--lora", action="store_true", help="Activar LoRA sobre backbone (requiere peft)")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank (default: 16)")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha (default: 32)")
    parser.add_argument("--lora-dropout", type=float, default=0.05, help="LoRA dropout (default: 0.05)")
    parser.add_argument("--lora-target-modules", default=None,
                        help="Comma-separated target modules (default: auto-detect query/value projections)")
    # ── Curriculum ──
    parser.add_argument("--curriculum-phase", type=int, default=None, choices=[1, 2, 3],
                        help="Curriculum phase: 1=easy, 2=easy+medium, 3=all")
    parser.add_argument("--dim-difficulty", default=None,
                        help="JSON file mapping dim_name → easy|medium|hard")
    # ── KD (dormida) ──
    parser.add_argument("--kd-teacher-logits", default=None,
                        help="[DORMIDA] Path a JSONL con logits del teacher (Opus) para KD loss")
    parser.add_argument("--kd-alpha", type=float, default=0.5,
                        help="[DORMIDA] Peso de KD loss vs task loss (default: 0.5)")
    parser.add_argument("--kd-temperature", type=float, default=2.0,
                        help="[DORMIDA] Temperature para softened probabilities (default: 2.0)")
    # ── Heads por capa (dormida) ──
    parser.add_argument("--layer-heads", action="store_true",
                        help="[DORMIDA] Activar heads en capas intermedias (6/12/18/24) — Arquitectura C")
    parser.add_argument("--layer-heads-config", default=None,
                        help="[DORMIDA] JSON con mapping capa → dims (para Arquitectura C)")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    # Device
    if torch.cuda.is_available():
        device = torch.device("cuda")
        log.info(f"GPU: {torch.cuda.get_device_name(0)}")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        log.info("Device: Apple MPS")
    else:
        device = torch.device("cpu")

    # ── Cargar config dims ────────────────────────────────────────────────
    with open(args.dims) as f:
        dims_config = json.load(f)

    float_dims = dims_config["float_dims"]
    binary_dims = dims_config["binary_dims"]

    # ── Dim difficulty (para curriculum y métricas por grupo) ─────────────
    dim_difficulty = None
    if args.dim_difficulty:
        with open(args.dim_difficulty) as f:
            dim_difficulty = json.load(f)
        log.info(f"Dim difficulty loaded: {len(dim_difficulty)} dims clasificadas")

    # ── Curriculum: filtrar dims por fase ─────────────────────────────────
    if args.curriculum_phase is not None:
        if dim_difficulty is None:
            log.error("--curriculum-phase requiere --dim-difficulty")
            sys.exit(1)
        phase_map = {1: {"easy"}, 2: {"easy", "medium"}, 3: {"easy", "medium", "hard"}}
        allowed = phase_map[args.curriculum_phase]
        orig_float = len(float_dims)
        orig_binary = len(binary_dims)
        float_dims = [d for d in float_dims if dim_difficulty.get(d, "hard") in allowed]
        binary_dims = [d for d in binary_dims if dim_difficulty.get(d, "hard") in allowed]
        log.info(f"Curriculum phase {args.curriculum_phase}: "
                 f"float {orig_float}→{len(float_dims)}, binary {orig_binary}→{len(binary_dims)}")

    n_float = len(float_dims)
    n_binary = len(binary_dims)

    log.info(f"Dims: {n_float} float + {n_binary} binary = {n_float + n_binary} total")
    log.info(f"  Float dims incluyen posicion_R/P/I: {all(d in float_dims for d in ['posicion_R', 'posicion_P', 'posicion_I'])}")

    # ── Validar features dormidas ────────────────────────────────────────
    if args.kd_teacher_logits:
        log.warning("⚠ KD está DORMIDA. Se aceptan los args pero NO se aplica KD loss todavía.")
        log.warning("  Para activar: implementar KDLoss en el training loop (ver TODO abajo).")

    if args.layer_heads:
        log.warning("⚠ Layer heads (Arquitectura C) está DORMIDA. Se ignora --layer-heads.")
        log.warning("  Para activar: reemplazar MultiHeadDetectorV2 por LayerHeadDetector.")

    # ── Cargar datos ──────────────────────────────────────────────────────
    all_data = load_data(args.labels)
    log.info(f"Total muestras: {len(all_data)}")

    # ── spaCy span features ───────────────────────────────────────────────
    nlp = None
    all_spans = None
    use_spans = not args.no_spans and HAS_SPACY

    if use_spans:
        nlp = load_spacy_model()
        if nlp:
            all_spans = precompute_spans(all_data, nlp)
        else:
            use_spans = False

    actual_span_dim = SPAN_DIM if use_spans else 0
    log.info(f"Span features: {'ON' if use_spans else 'OFF'} (dim={actual_span_dim})")

    # ── Split ─────────────────────────────────────────────────────────────
    ratios = tuple(float(x) for x in args.split.split(","))
    train_data, val_data, test_data = split_data(all_data, ratios, args.seed)
    log.info(f"Split: {len(train_data)} train / {len(val_data)} val / {len(test_data)} test")

    # Split spans in same order
    train_spans, val_spans, test_spans = None, None, None
    if all_spans:
        np.random.seed(args.seed)
        indices = np.random.permutation(len(all_data))
        n_train = int(len(all_data) * ratios[0])
        n_val = int(len(all_data) * ratios[1])
        train_spans = [all_spans[i] for i in indices[:n_train]]
        val_spans = [all_spans[i] for i in indices[n_train:n_train + n_val]]
        test_spans = [all_spans[i] for i in indices[n_train + n_val:]]

    # ── Tokenizer y datasets ──────────────────────────────────────────────
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    train_ds = LabeledTextDatasetV2(train_data, tokenizer, float_dims, binary_dims, train_spans, args.max_length)
    val_ds = LabeledTextDatasetV2(val_data, tokenizer, float_dims, binary_dims, val_spans, args.max_length)
    test_ds = LabeledTextDatasetV2(test_data, tokenizer, float_dims, binary_dims, test_spans, args.max_length)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    # ── Modelo ────────────────────────────────────────────────────────────
    model = MultiHeadDetectorV2(
        args.model, n_float, n_binary,
        span_dim=actual_span_dim, dropout=args.dropout
    )

    # ── LoRA (opcional) ──────────────────────────────────────────────────
    if args.lora:
        if not HAS_PEFT:
            log.error("--lora requiere peft. pip install peft")
            sys.exit(1)

        # Auto-detect target modules para DeBERTa
        if args.lora_target_modules:
            target_modules = [m.strip() for m in args.lora_target_modules.split(",")]
        else:
            # DeBERTa-v3 usa query_proj, key_proj, value_proj en disentangled attention
            target_modules = ["query_proj", "key_proj", "value_proj"]

        lora_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=target_modules,
            bias="none",
            modules_to_save=["float_head", "binary_head", "projection"],  # heads se entrenan full
        )
        model = get_peft_model(model, lora_config)
        log.info(f"LoRA activado: r={args.lora_r}, alpha={args.lora_alpha}, "
                 f"targets={target_modules}")
        model.print_trainable_parameters()
    else:
        log.info("LoRA desactivado (full fine-tune)")

    model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log.info(f"Params: {total_params:,} total, {trainable:,} entrenables")

    # ── Calcular pos_weight para binary dims (weighted BCE) ──────────────
    log.info("Calculando pos_weight para dims binarias desde training data...")
    pos_counts = np.zeros(n_binary)
    neg_counts = np.zeros(n_binary)
    for item in train_data:
        labels = item.get("labels", {})
        for i, dim_name in enumerate(binary_dims):
            val = float(labels.get(dim_name, 0.0) or 0.0)
            if val >= 0.5:
                pos_counts[i] += 1
            else:
                neg_counts[i] += 1

    # pos_weight = neg_count / pos_count (clamped para evitar extremos)
    pos_weight = np.ones(n_binary)
    for i in range(n_binary):
        if pos_counts[i] > 0:
            pw = neg_counts[i] / pos_counts[i]
            pos_weight[i] = min(max(pw, 0.5), 20.0)  # clamp [0.5, 20]
            log.info(f"  {binary_dims[i]}: pos={int(pos_counts[i])}, neg={int(neg_counts[i])}, "
                     f"pos_weight={pos_weight[i]:.2f}")
        else:
            log.warning(f"  {binary_dims[i]}: 0 positivos en train — pos_weight=1.0")

    pos_weight_tensor = torch.tensor(pos_weight, dtype=torch.float32).to(device)

    # ── Optimizer, scheduler, losses ──────────────────────────────────────
    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr, weight_decay=0.01,
    )
    total_steps = len(train_loader) * args.epochs // args.grad_accum
    warmup_steps = int(total_steps * args.warmup_ratio)
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    mse_fn = nn.MSELoss()
    bce_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight_tensor)  # weighted BCE con logits

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # wandb
    if HAS_WANDB and args.wandb_name:
        wandb.init(project=args.wandb_project, name=args.wandb_name, config={
            "model": args.model, "epochs": args.epochs, "lr": args.lr,
            "batch_size": args.batch_size, "n_float": n_float,
            "n_binary": n_binary, "span_features": use_spans,
            "span_dim": actual_span_dim, "loss_alpha": args.loss_alpha,
            "loss_beta": args.loss_beta,
            "lora": args.lora, "lora_r": args.lora_r if args.lora else None,
            "lora_alpha": args.lora_alpha if args.lora else None,
            "curriculum_phase": args.curriculum_phase,
            "weighted_bce": True, "pos_weight_range": f"[{pos_weight.min():.1f}, {pos_weight.max():.1f}]",
            "train_size": len(train_data), "val_size": len(val_data),
            "version": "v2.2_lora_curriculum_wbce",
        })

    # ── Training loop ─────────────────────────────────────────────────────
    best_val_loss = float("inf")
    patience_counter = 0
    global_step = 0
    start_time = time.time()

    log.info(f"Training: {args.epochs} epochs, {total_steps} steps, "
             f"loss weights: α={args.loss_alpha} β={args.loss_beta}")

    for epoch in range(args.epochs):
        model.train()
        ep_loss = ep_f = ep_b = 0.0
        n_batches = 0

        for batch_idx, batch in enumerate(train_loader):
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            fl = batch["float_labels"].to(device)
            bl = batch["binary_labels"].to(device)
            spans = batch["span_features"].to(device)

            fo, bo = model(ids, mask, spans)

            loss_f = mse_fn(fo, fl)
            loss_b = bce_fn(bo, bl)

            loss = args.loss_alpha * loss_f + args.loss_beta * loss_b
            loss = loss / args.grad_accum
            loss.backward()

            if (batch_idx + 1) % args.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1

                if HAS_WANDB and args.wandb_name and global_step % 10 == 0:
                    wandb.log({
                        "train/loss": loss.item() * args.grad_accum,
                        "train/loss_float": loss_f.item(),
                        "train/loss_binary": loss_b.item(),
                        "train/lr": scheduler.get_last_lr()[0],
                    })

            ep_loss += loss.item() * args.grad_accum
            ep_f += loss_f.item()
            ep_b += loss_b.item()
            n_batches += 1

        # ── Validación ────────────────────────────────────────────────────
        model.eval()
        val_loss = 0.0
        val_n = 0
        with torch.no_grad():
            for batch in val_loader:
                ids = batch["input_ids"].to(device)
                mask = batch["attention_mask"].to(device)
                fl = batch["float_labels"].to(device)
                bl = batch["binary_labels"].to(device)
                spans = batch["span_features"].to(device)

                fo, bo = model(ids, mask, spans)
                lf = mse_fn(fo, fl)
                lb = bce_fn(bo, bl)

                val_loss += (args.loss_alpha * lf + args.loss_beta * lb).item()
                val_n += 1

        avg_val_loss = val_loss / val_n if val_n > 0 else float("inf")
        val_metrics = compute_metrics_v2(model, val_loader, float_dims, binary_dims, device, dim_difficulty)

        log.info(
            f"Epoch {epoch+1}/{args.epochs} — "
            f"train={ep_loss/n_batches:.4f} val={avg_val_loss:.4f} "
            f"corr={val_metrics['corr_global']:.3f} "
            f"f1={val_metrics['f1_global']:.3f} "
            f"mae={val_metrics['mae_global']:.3f}"
        )

        if HAS_WANDB and args.wandb_name:
            log_dict = {"epoch": epoch+1, "val/loss": avg_val_loss,
                       "val/corr_global": val_metrics["corr_global"],
                       "val/f1_global": val_metrics["f1_global"],
                       "val/mae_global": val_metrics["mae_global"]}
            if "p48_compliance" in val_metrics:
                log_dict["val/p48_compliance"] = val_metrics["p48_compliance"]
            for group in ["easy", "medium", "hard"]:
                key = f"group_{group}_mean"
                if key in val_metrics:
                    log_dict[f"val/{key}"] = val_metrics[key]
            wandb.log(log_dict)

        # Checkpoint
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            ckpt = output_dir / "best_model.pt"
            save_dict = {
                "epoch": epoch + 1,
                "model_state_dict": model.state_dict(),
                "val_loss": avg_val_loss,
                "val_metrics": val_metrics,
                "config": {
                    "model_name": args.model,
                    "n_float": n_float, "n_binary": n_binary,
                    "float_dims": float_dims, "binary_dims": binary_dims,
                    "span_dim": actual_span_dim,
                    "dropout": args.dropout,
                    "lora": args.lora,
                    "lora_r": args.lora_r if args.lora else None,
                    "curriculum_phase": args.curriculum_phase,
                    "pos_weight": pos_weight.tolist(),
                    "version": "v2.2_lora_curriculum_wbce",
                },
            }
            torch.save(save_dict, ckpt)
            log.info(f"  Best → {ckpt} (val_loss={avg_val_loss:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                log.info(f"Early stopping epoch {epoch+1}")
                break

    # ── Test final ────────────────────────────────────────────────────────
    log.info("Evaluando test set con mejor checkpoint...")
    ckpt = torch.load(output_dir / "best_model.pt", map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    test_metrics = compute_metrics_v2(model, test_loader, float_dims, binary_dims, device, dim_difficulty)

    total_time = time.time() - start_time

    final = {
        "experiment": args.wandb_name or "v2.1",
        "model": args.model,
        "epochs_run": epoch + 1,
        "best_epoch": ckpt["epoch"],
        "best_val_loss": best_val_loss,
        "test_metrics": test_metrics,
        "train_size": len(train_data),
        "val_size": len(val_data),
        "test_size": len(test_data),
        "span_features": use_spans,
        "total_time_s": round(total_time, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "v2.1_no_categoricals",
    }

    (output_dir / "final_metrics.json").write_text(
        json.dumps(final, indent=2, ensure_ascii=False))

    log.info(f"\n{'='*60}")
    log.info(f"RESULTADOS v2.2 (LoRA + curriculum + weighted BCE)")
    log.info(f"{'='*60}")
    log.info(f"  corr_global:  {test_metrics['corr_global']:.3f}  (target: >0.35)")
    log.info(f"  f1_global:    {test_metrics['f1_global']:.3f}  (target: >0.50)")
    log.info(f"  mae_global:   {test_metrics['mae_global']:.3f}")
    log.info(f"  Tiempo:       {total_time/60:.1f} min")
    log.info(f"  LoRA:         {'ON (r={})'.format(args.lora_r) if args.lora else 'OFF'}")
    log.info(f"  Curriculum:   {f'phase {args.curriculum_phase}' if args.curriculum_phase else 'OFF'}")
    log.info(f"  Weighted BCE: ON (range [{pos_weight.min():.1f}, {pos_weight.max():.1f}])")

    # Métricas por grupo de dificultad
    for group in ["easy", "medium", "hard"]:
        key = f"group_{group}_mean"
        if key in test_metrics:
            log.info(f"  {group:8s}:     {test_metrics[key]:.3f}  ({test_metrics[f'group_{group}_count']} dims)")

    # Posicion R/P/I
    log.info(f"\n  Posicion R/P/I:")
    for rpi in ["posicion_R", "posicion_P", "posicion_I"]:
        corr = test_metrics.get(f"corr/{rpi}", "N/A")
        mean = test_metrics.get(f"mean/{rpi}", "N/A")
        log.info(f"    {rpi}: corr={corr}, mean={mean}")
    if "p48_compliance" in test_metrics:
        log.info(f"    P48 compliance (I>0.1 → R>0.1 or P>0.1): {test_metrics['p48_compliance']:.1%}")

    # Top dims
    log.info(f"\n  Top correlaciones:")
    corr_dims = {k: v for k, v in test_metrics.items() if k.startswith("corr/")}
    for k, v in sorted(corr_dims.items(), key=lambda x: -x[1])[:10]:
        log.info(f"    {k}: {v:.3f}")

    if HAS_WANDB and args.wandb_name:
        wandb.log({"test/corr_global": test_metrics["corr_global"],
                   "test/f1_global": test_metrics["f1_global"]})
        if "p48_compliance" in test_metrics:
            wandb.log({"test/p48_compliance": test_metrics["p48_compliance"]})
        wandb.finish()

    log.info(f"\nCheckpoint: {output_dir / 'best_model.pt'}")
    log.info(f"Métricas: {output_dir / 'final_metrics.json'}")


# ══════════════════════════════════════════════════════════════════════════
# DORMIDAS — Preparadas para activar cuando toque
# ══════════════════════════════════════════════════════════════════════════


class KDLoss(nn.Module):
    """[DORMIDA] Knowledge Distillation loss.

    Combina task loss con soft-target loss del teacher (Opus).
    Para activar: cargar teacher_logits desde --kd-teacher-logits y añadir
    al training loop como:
        kd_loss = kd_fn(student_logits, teacher_logits_batch)
        total_loss = (1-kd_alpha) * task_loss + kd_alpha * kd_loss

    Ref: KD-LoRA (arxiv.org/abs/2410.20777) — evaluado en DeBERTa-v3.
    """

    def __init__(self, temperature: float = 2.0):
        super().__init__()
        self.temperature = temperature
        self.kl_div = nn.KLDivLoss(reduction="batchmean")

    def forward(self, student_logits: torch.Tensor, teacher_logits: torch.Tensor) -> torch.Tensor:
        """Calcula KL divergence entre softened distributions."""
        T = self.temperature
        student_soft = nn.functional.log_softmax(student_logits / T, dim=-1)
        teacher_soft = nn.functional.softmax(teacher_logits / T, dim=-1)
        return self.kl_div(student_soft, teacher_soft) * (T * T)


class LayerHeadDetector(nn.Module):
    """[DORMIDA] Arquitectura C — Heads en capas intermedias de DeBERTa.

    En lugar de solo usar CLS del último layer, extrae representaciones
    de capas 6, 12, 18, 24 y asigna diferentes dims a cada head.

    Para activar:
    1. Crear layer_heads_config.json: {"6": ["dim1", "dim2"], "12": [...], ...}
    2. Reemplazar MultiHeadDetectorV2 por LayerHeadDetector en main()
    3. Usar --layer-heads --layer-heads-config path/to/config.json

    Ref: 28 papers validan que layer-specific heads mejoran 1-4 F1.
    DeBERTa layers: 1-6 (sintaxis), 7-12 (semántica local), 13-18
    (semántica global), 19-24 (pragmática/discurso).
    """

    def __init__(
        self,
        model_name: str,
        layer_dims_config: dict[int, list[str]],
        span_dim: int = SPAN_DIM,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name, output_hidden_states=True)
        hidden_size = self.backbone.config.hidden_size
        self.dropout = nn.Dropout(dropout)

        # Un head por layer group
        self.layer_heads = nn.ModuleDict()
        self.layer_dims = OrderedDict()  # layer_idx → list of dim names

        for layer_idx_str, dim_names in layer_dims_config.items():
            layer_idx = int(layer_idx_str)
            n_dims = len(dim_names)
            self.layer_dims[layer_idx] = dim_names

            # Projection + head
            self.layer_heads[str(layer_idx)] = nn.Sequential(
                nn.Linear(hidden_size + span_dim, hidden_size),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size, n_dims),
            )

        total_dims = sum(len(d) for d in self.layer_dims.values())
        log.info(f"LayerHeadDetector: {len(self.layer_dims)} heads, {total_dims} dims total")
        for layer_idx, dims in self.layer_dims.items():
            log.info(f"  Layer {layer_idx}: {len(dims)} dims")

    def forward(self, input_ids, attention_mask, span_features):
        outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = outputs.hidden_states  # tuple of (batch, seq_len, hidden)

        all_logits = []
        for layer_idx in self.layer_dims:
            # CLS token de la capa específica
            layer_cls = hidden_states[layer_idx][:, 0, :]
            combined = torch.cat([layer_cls, span_features], dim=1)
            logits = self.layer_heads[str(layer_idx)](combined)
            all_logits.append(logits)

        # Concatenar todos los logits de todas las capas
        return torch.cat(all_logits, dim=-1)

    def get_dim_order(self) -> list[str]:
        """Retorna la lista ordenada de dims como salen del forward."""
        order = []
        for dims in self.layer_dims.values():
            order.extend(dims)
        return order


if __name__ == "__main__":
    main()
