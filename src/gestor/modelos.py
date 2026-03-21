"""Catálogo de modelos + asignación modelo→celda.

Fuente: Maestro §4.1, Exp 1 completo (12 modelos), Exp 4.1 (mesa especializada).
"""
from __future__ import annotations


# Catálogo de modelos disponibles con costes aproximados
CATALOGO_MODELOS = {
    "deepseek/deepseek-chat-v3-0324": {
        "alias": "V3.2-chat",
        "tier": "produccion",
        "coste_in": 0.27,    # $/M tokens input
        "coste_out": 1.10,
        "contexto": 128000,
        "roles": ["ejecutor_principal", "evaluador"],
    },
    "deepseek/deepseek-chat": {
        "alias": "V3.1",
        "tier": "produccion",
        "coste_in": 0.27,
        "coste_out": 1.10,
        "contexto": 128000,
        "roles": ["ejecutor_complementario", "evaluador"],
    },
    "deepseek/deepseek-reasoner": {
        "alias": "R1",
        "tier": "produccion",
        "coste_in": 0.55,
        "coste_out": 2.19,
        "contexto": 128000,
        "roles": ["razonador_profundo", "evaluador"],
    },
    "cognitivecomputations/dolphin3.0-r1-mistral-24b:free": {
        "alias": "Cogito-671b",
        "tier": "produccion",
        "coste_in": 0.50,
        "coste_out": 1.50,
        "contexto": 65536,
        "roles": ["sintetizador"],
    },
    "openai/gpt-4o": {
        "alias": "GPT-OSS",
        "tier": "produccion",
        "coste_in": 0.60,
        "coste_out": 0.60,
        "contexto": 225000,
        "roles": ["motor_pizarra", "evaluador"],
    },
}

# Panel de evaluación de producción (Maestro §4.1)
PANEL_EVALUADOR = ["deepseek/deepseek-chat-v3-0324", "deepseek/deepseek-chat", "deepseek/deepseek-reasoner"]

# Sintetizador por defecto
SINTETIZADOR_DEFAULT = "cognitivecomputations/dolphin3.0-r1-mistral-24b:free"


# Mejor modelo por celda (Maestro §4.1, Exp 1)
# Formato: "Fi×Lj" → modelo_id
ASIGNACION_MODELO_CELDA: dict[str, str] = {
    # Conservar
    "F1×salud":       "deepseek/deepseek-chat",         # V3.1 (2.8)
    "F1×sentido":     "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",  # Cogito (2.3)
    "F1×continuidad": "deepseek/deepseek-chat",         # V3.1 (2.4)
    # Captar
    "F2×salud":       "deepseek/deepseek-chat-v3-0324", # Maverick proxy → V3.2
    "F2×sentido":     "deepseek/deepseek-chat-v3-0324", # V3.2R (2.7)
    "F2×continuidad": "deepseek/deepseek-chat-v3-0324", # Qwen3 proxy → V3.2
    # Depurar
    "F3×salud":       "openai/gpt-4o",                  # GPT-OSS (2.6)
    "F3×sentido":     "openai/gpt-4o",                  # GPT-OSS (2.9)
    "F3×continuidad": "deepseek/deepseek-chat-v3-0324", # Qwen3.5 proxy → V3.2
    # Distribuir
    "F4×salud":       "deepseek/deepseek-chat-v3-0324", # Qwen3 proxy → V3.2
    "F4×sentido":     "openai/gpt-4o",                  # GPT-OSS (1.7)
    "F4×continuidad": "deepseek/deepseek-chat-v3-0324", # Qwen3 proxy → V3.2
    # Frontera
    "F5×salud":       "deepseek/deepseek-chat",         # V3.1 (2.6)
    "F5×sentido":     "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",  # Cogito (3.4)
    "F5×continuidad": "deepseek/deepseek-chat",         # V3.1 (2.9)
    # Adaptar
    "F6×salud":       "deepseek/deepseek-chat-v3-0324", # Kimi proxy → V3.2
    "F6×sentido":     "deepseek/deepseek-chat",         # V3.1 (2.4)
    "F6×continuidad": "deepseek/deepseek-chat-v3-0324", # V3.2R (2.8)
    # Replicar
    "F7×salud":       "deepseek/deepseek-chat",         # V3.1 (2.0)
    "F7×sentido":     "deepseek/deepseek-reasoner",     # R1 (1.7)
    "F7×continuidad": "deepseek/deepseek-reasoner",     # R1 (3.1)
}


def modelo_para_celda(funcion: str, lente: str) -> str:
    """Devuelve el mejor modelo para una celda Fi×Lj."""
    key = f"{funcion}×{lente}"
    return ASIGNACION_MODELO_CELDA.get(key, "deepseek/deepseek-chat-v3-0324")


def modelos_para_tier(tier: int) -> list[str]:
    """Devuelve los modelos a usar según el tier de enjambre."""
    if tier <= 1:
        return []  # Tier 1 = lookup, sin modelo
    if tier == 2:
        return ["deepseek/deepseek-chat-v3-0324"]  # 1 modelo barato
    if tier == 3:
        return PANEL_EVALUADOR  # V3.2 + V3.1 + R1
    # Tier 4-5: todos
    return list(CATALOGO_MODELOS.keys())
