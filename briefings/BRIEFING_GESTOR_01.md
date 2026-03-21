# BRIEFING_GESTOR_01 — Gestor v0: Compilador por arquetipo

**Fecha:** 2026-03-19
**Prioridad:** Alta — sin Gestor no hay Fase B (lookup) ni aprendizaje
**Ejecutar:** Claude Code (EN PARALELO con BRIEFING_TCF_07 — cero solapamiento de archivos)
**Prerequisito:** 59 tests passing (módulo TCF ya existe)

---

## CONTEXTO

El Maestro §6 describe el Gestor como "el sistema que mira hacia dentro — mantiene, poda, mejora y recompila la Matriz". Es el cuello de botella principal.

**Este briefing implementa Gestor v0 mínimo:**
- Compilar programa de preguntas por arquetipo (lookup de receta → INTs + modelos + orden)
- Catálogo de modelos con asignación modelo→celda
- Decidir tier de enjambre
- NO implementa aún: podar preguntas muertas, transferencia cross-dominio, Fase A→B automática

**Archivos que toca:** SOLO nuevos en `src/gestor/` y `tests/`. NO toca pipeline/, tcf/, config/ ni nada que TCF_07 modifica.

---

## ARCHIVOS A CREAR

```
src/gestor/
├── __init__.py
├── modelos.py        ← Catálogo de modelos + asignación modelo→celda
├── compilador.py     ← Compilar programa por scoring de arquetipo
├── programa.py       ← Dataclass ProgramaCompilado
└── tier.py           ← Decisión de tier de enjambre

tests/
├── test_compilador.py
└── test_tier.py
```

---

## 1. `src/gestor/__init__.py`

```python
"""Gestor de la Matriz — mira hacia dentro.

Mantiene, poda, mejora y compila la Matriz 3L×7F×18INT.
Alimenta al Motor vN, Exocortex y todo consumidor con
programas de preguntas compilados.

Maestro §6.
"""
```

---

## 2. `src/gestor/modelos.py` — Catálogo de modelos

Datos de: Maestro §4.1 (asignación modelo→celda validada en Exp 1+4)

```python
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
```

---

## 3. `src/gestor/programa.py` — ProgramaCompilado

```python
"""Programa compilado — output del Gestor para el Motor.

Un programa es la receta ejecutable: qué INTs, en qué orden,
con qué modelos, para qué funciones.

Maestro §6.4.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PasoPrograma:
    """Un paso del programa compilado."""
    orden: int                  # 1, 2, 3...
    inteligencia: str           # "INT-07"
    funcion_objetivo: str       # "F5" — la función que este paso ataca
    lente_objetivo: str         # "continuidad"
    modelo: str                 # "deepseek/deepseek-chat-v3-0324"
    operacion: str              # "individual", "composicion", "fusion"
    con_inteligencia: str | None = None  # para composición: A→B, B es con_inteligencia


@dataclass
class ProgramaCompilado:
    """Programa completo que el Motor ejecuta."""
    arquetipo_base: str             # "maquina_sin_alma"
    arquetipo_score: float          # 0.78
    tier: int                       # 1-5
    pasos: list[PasoPrograma]       # secuencia de ejecución
    frenar: list[str]               # funciones a FRENAR antes de ejecutar
    parar_primero: bool             # True solo para "quemado"
    lente_primaria: str             # "continuidad"
    mezcla: bool                    # True si receta mixta
    coste_estimado: float           # $ estimado
    tiempo_estimado_s: float        # segundos estimados

    def inteligencias(self) -> list[str]:
        """INTs únicas en el programa."""
        return list(dict.fromkeys(p.inteligencia for p in self.pasos))

    def modelos(self) -> list[str]:
        """Modelos únicos en el programa."""
        return list(dict.fromkeys(p.modelo for p in self.pasos))
```

---

## 4. `src/gestor/tier.py` — Decisión de tier

```python
"""Decisión de tier de enjambre.

Maestro §4.4:
  Tier 1 — Reflejo:      lookup precompilado, $0
  Tier 2 — Respuesta:    1 modelo barato, $0.01-0.05
  Tier 3 — Análisis:     3-5 modelos, $0.10-0.50
  Tier 4 — Profundo:     7+ modelos pizarra, $0.50-2.00
  Tier 5 — Cartografía:  exploración completa, $5-20
"""
from __future__ import annotations


def decidir_tier(
    modo: str,
    tiene_programa_precompilado: bool = False,
    forzar_tier: int | None = None,
    presupuesto_max: float = 1.50,
) -> int:
    """Decide el tier de enjambre según contexto.

    Maestro §4.4:
      ¿Respuesta precompilada? → TIER 1
      ¿Conversación normal?   → TIER 2
      ¿Análisis o decisión?   → TIER 3
      ¿Batch (nadie espera)?  → TIER 4
      ¿Dominio nuevo?         → TIER 5
    """
    if forzar_tier is not None:
        return max(1, min(5, forzar_tier))

    # Tier 1: lookup directo
    if tiene_programa_precompilado and modo == "conversacion":
        return 1

    # Tier 2: conversación sin programa previo
    if modo == "conversacion":
        return 2

    # Tier 3: análisis (default para la mayoría)
    if modo in ("analisis", "confrontacion", "generacion"):
        if presupuesto_max < 0.20:
            return 2
        return 3

    # Default
    return 3


# Costes y tiempos estimados por tier
TIER_CONFIG = {
    1: {"coste_est": 0.00,  "tiempo_est_s": 0.2,   "desc": "Reflejo (lookup)"},
    2: {"coste_est": 0.03,  "tiempo_est_s": 10,     "desc": "Respuesta (1 modelo)"},
    3: {"coste_est": 0.30,  "tiempo_est_s": 90,     "desc": "Análisis (3-5 modelos)"},
    4: {"coste_est": 2.00,  "tiempo_est_s": 2700,   "desc": "Profundo (pizarra)"},
    5: {"coste_est": 10.00, "tiempo_est_s": 10800,  "desc": "Cartografía (exploración)"},
}
```

---

## 5. `src/gestor/compilador.py` — El corazón del Gestor v0

```python
"""Compilador del Gestor — programa por arquetipo.

Dado un scoring multi-arquetipo:
1. Busca la receta mixta (de src/tcf/recetas.py)
2. Asigna modelos por celda (de src/gestor/modelos.py)
3. Decide tier de enjambre (de src/gestor/tier.py)
4. Produce un ProgramaCompilado que el Motor ejecuta

Maestro §6.1, §6.4.
"""
from __future__ import annotations

from src.tcf.arquetipos import ScoringMultiArquetipo
from src.tcf.campo import VectorFuncional
from src.tcf.recetas import generar_receta_mixta, RecetaResultado
from src.gestor.modelos import modelo_para_celda
from src.gestor.programa import ProgramaCompilado, PasoPrograma
from src.gestor.tier import decidir_tier, TIER_CONFIG


def compilar_programa(
    scoring: ScoringMultiArquetipo,
    vector: VectorFuncional | None = None,
    modo: str = "analisis",
    presupuesto_max: float = 1.50,
    forzar_tier: int | None = None,
) -> ProgramaCompilado:
    """Compila un programa de preguntas a partir del scoring de arquetipo.

    Este es el output principal del Gestor. El Motor recibe esto y ejecuta.

    Args:
        scoring: resultado del scoring multi-arquetipo
        vector: vector funcional del caso (para Regla 14 / FRENAR)
        modo: modo del pipeline (analisis, conversacion, etc.)
        presupuesto_max: presupuesto máximo en USD
        forzar_tier: si se quiere forzar un tier específico
    """
    # 1. Generar receta mixta
    receta = generar_receta_mixta(scoring, vector)

    # 2. Decidir tier
    tier = decidir_tier(
        modo=modo,
        tiene_programa_precompilado=False,  # v0: nunca hay precompilado aún
        forzar_tier=forzar_tier,
        presupuesto_max=presupuesto_max,
    )

    # 3. Construir pasos del programa
    pasos = _construir_pasos(receta, tier)

    # 4. Estimar coste y tiempo
    config_tier = TIER_CONFIG.get(tier, TIER_CONFIG[3])

    return ProgramaCompilado(
        arquetipo_base=receta.arquetipo_base,
        arquetipo_score=scoring.primario.score,
        tier=tier,
        pasos=pasos,
        frenar=receta.frenar,
        parar_primero=receta.parar_primero,
        lente_primaria=receta.lente,
        mezcla=receta.mezcla,
        coste_estimado=config_tier["coste_est"],
        tiempo_estimado_s=config_tier["tiempo_est_s"],
    )


def _construir_pasos(receta: RecetaResultado, tier: int) -> list[PasoPrograma]:
    """Traduce una receta en pasos ejecutables con modelos asignados."""
    pasos = []
    orden = 1

    # Emparejar INTs con funciones de la secuencia
    # La receta tiene secuencia de funciones y lista de INTs
    # Cada INT se asigna a la función que mejor cubre (según la receta)
    funciones = receta.secuencia if receta.secuencia else ["F5"]  # default F5
    ints = receta.ints if receta.ints else ["INT-01", "INT-08", "INT-16"]  # fallback
    lente = receta.lente or "salud"

    for i, int_id in enumerate(ints):
        # Asignar función: round-robin sobre la secuencia
        funcion = funciones[min(i, len(funciones) - 1)]

        # Asignar modelo según celda
        modelo = modelo_para_celda(funcion, lente)

        # Tier 2: solo 1 modelo, usar el de mayor cobertura
        if tier <= 2:
            modelo = "deepseek/deepseek-chat-v3-0324"

        pasos.append(PasoPrograma(
            orden=orden,
            inteligencia=int_id,
            funcion_objetivo=funcion,
            lente_objetivo=lente,
            modelo=modelo,
            operacion="individual",
        ))
        orden += 1

    return pasos
```

---

## 6. Tests

### `tests/test_compilador.py`

```python
"""Tests para src/gestor/compilador.py — Compilar programa por arquetipo."""
import pytest
from src.tcf.campo import VectorFuncional
from src.tcf.arquetipos import scoring_multi_arquetipo
from src.gestor.compilador import compilar_programa
from src.gestor.programa import ProgramaCompilado
from src.tcf.constantes import VECTOR_PILATES


@pytest.fixture
def vector_pilates():
    return VectorFuncional.from_dict(VECTOR_PILATES)


@pytest.fixture
def scoring_pilates(vector_pilates):
    return scoring_multi_arquetipo(vector_pilates)


class TestCompilarPrograma:
    def test_pilates_compila(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        assert isinstance(prog, ProgramaCompilado)
        assert prog.arquetipo_base == "maquina_sin_alma"
        assert prog.tier == 3  # modo analisis por defecto
        assert len(prog.pasos) > 0

    def test_pilates_lente_continuidad(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        assert prog.lente_primaria == "continuidad"

    def test_pilates_sin_frenar(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        assert len(prog.frenar) == 0

    def test_pilates_tiene_int16(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        assert "INT-16" in prog.inteligencias()

    def test_pilates_modelos_asignados(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        for paso in prog.pasos:
            assert paso.modelo != ""
            assert "/" in paso.modelo  # formato openrouter

    def test_conversacion_tier_2(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates, modo="conversacion")
        assert prog.tier == 2

    def test_forzar_tier(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates, forzar_tier=4)
        assert prog.tier == 4

    def test_presupuesto_bajo_baja_tier(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates, presupuesto_max=0.10)
        assert prog.tier <= 2

    def test_expansion_sin_cimientos_frenar(self):
        v = VectorFuncional(f1=0.30, f2=0.65, f3=0.30, f4=0.45, f5=0.25, f6=0.45, f7=0.75)
        scoring = scoring_multi_arquetipo(v)
        prog = compilar_programa(scoring, v)
        assert "F7" in prog.frenar

    def test_quemado_parar_primero(self):
        v = VectorFuncional(f1=0.25, f2=0.20, f3=0.20, f4=0.25, f5=0.35, f6=0.20, f7=0.15)
        scoring = scoring_multi_arquetipo(v)
        prog = compilar_programa(scoring, v)
        assert prog.parar_primero
```

### `tests/test_tier.py`

```python
"""Tests para src/gestor/tier.py — Decisión de tier."""
import pytest
from src.gestor.tier import decidir_tier


class TestDecidirTier:
    def test_conversacion_precompilado_tier1(self):
        assert decidir_tier("conversacion", tiene_programa_precompilado=True) == 1

    def test_conversacion_sin_precompilado_tier2(self):
        assert decidir_tier("conversacion") == 2

    def test_analisis_tier3(self):
        assert decidir_tier("analisis") == 3

    def test_confrontacion_tier3(self):
        assert decidir_tier("confrontacion") == 3

    def test_presupuesto_bajo_tier2(self):
        assert decidir_tier("analisis", presupuesto_max=0.10) == 2

    def test_forzar_tier(self):
        assert decidir_tier("conversacion", forzar_tier=5) == 5

    def test_forzar_tier_clamp(self):
        assert decidir_tier("analisis", forzar_tier=0) == 1
        assert decidir_tier("analisis", forzar_tier=99) == 5
```

---

## SECUENCIA DE EJECUCIÓN

```bash
# 1. Crear directorio
mkdir -p /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/src/gestor

# 2. Crear los 5 archivos del módulo
#    __init__.py, modelos.py, programa.py, tier.py, compilador.py

# 3. Crear los 2 archivos de test
#    tests/test_compilador.py, tests/test_tier.py

# 4. Ejecutar tests
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
python -m pytest tests/test_compilador.py tests/test_tier.py -v --tb=short

# 5. Verificar imports
python -c "from src.gestor.compilador import compilar_programa; print('OK')"
```

## CRITERIO PASS

- `tests/test_compilador.py`: 10/10 pass
- `tests/test_tier.py`: 7/7 pass
- Imports limpios sin errores
- NO rompe ningún test existente: `python -m pytest tests/ -v` → 0 failures

## NOTAS

- **NO toca ningún archivo existente** — solo crea archivos nuevos en `src/gestor/` y `tests/`
- Los modelos en `modelos.py` usan formato OpenRouter. Algunos son proxies (Maverick→V3.2, Kimi→V3.2) porque no todos están disponibles vía OpenRouter
- El `compilador.py` depende de `src/tcf/` (que ya existe y tiene tests pasando)
- La asignación modelo→celda es estática por ahora (datos de Exp 1). El Gestor v1 la recalculará con datos de `datapoints_efectividad`

---

**FIN BRIEFING_GESTOR_01**
