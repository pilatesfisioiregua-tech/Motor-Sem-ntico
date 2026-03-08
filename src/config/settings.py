"""Configuración central — lee de env vars."""
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic API keys (rotación)
ANTHROPIC_API_KEYS: list[str] = [
    k for k in [
        os.getenv("ANTHROPIC_API_KEY_1"),
        os.getenv("ANTHROPIC_API_KEY_2"),
        os.getenv("ANTHROPIC_API_KEY_3"),
        os.getenv("ANTHROPIC_API_KEY_4"),
    ] if k
]

# Database
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# Modelos LLM
MODEL_ROUTER: str = "claude-sonnet-4-20250514"
MODEL_EXTRACTOR: str = "claude-haiku-4-5-20251001"
MODEL_INTEGRATOR: str = "claude-sonnet-4-20250514"

# Límites
MAX_COST_USD: float = 1.50
MAX_TIME_S: int = 150
DEFAULT_INTELLIGENCES: int = 5
MIN_INTELLIGENCES: int = 3
MAX_INTELLIGENCES: int = 6

# Scoring
MIN_QUALITY_SCORE: float = 6.0
