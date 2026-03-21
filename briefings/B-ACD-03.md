# B-ACD-03: Crear estados.json + flags de peligro

**Fecha:** 2026-03-19
**Ejecutor:** Claude Code
**Dependencia:** Ninguna (independiente de B-ACD-01/02)

---

## PASO 1: Crear estados.json

**Crear archivo:** `@project/src/tcf/estados.json`

**Contenido EXACTO:**

```json
{
  "equilibrados": {
    "E1": {
      "id": "E1",
      "nombre": "Muerte simétrica",
      "tipo": "equilibrado",
      "descripcion": "No funciona, no comprende, no persiste — pero todo por igual. Semilla no germinada o colapso total.",
      "condicion": {
        "gap_max": 0.15,
        "gradiente_min": 0.00,
        "gradiente_max": 0.20
      },
      "semantica": "Ausencia total. No hay energía para que las leyes se activen.",
      "transiciones": [
        {"destino": "E2", "via": "primera_activacion", "nota": "Cualquier función que suba rompe E1"}
      ]
    },
    "E2": {
      "id": "E2",
      "nombre": "Latencia",
      "tipo": "equilibrado",
      "descripcion": "Algo funciona, algo se comprende, algo persiste — todo insuficiente. Chispas pero no fuego.",
      "condicion": {
        "gap_max": 0.15,
        "gradiente_min": 0.20,
        "gradiente_max": 0.40
      },
      "semantica": "Vulnerable. Atractor inestable. La primera función que suba determina el destino.",
      "peligro": "La secuencia de activación aquí determina todo. F2 primero → operador ciego. F3/Se primero → óptimo.",
      "transiciones": [
        {"destino": "E3", "via": "Se_primero", "nota": "Secuencia correcta: Se → S → C"},
        {"destino": "operador_ciego", "via": "S_primero", "nota": "F2 o F1 suben sin Se"},
        {"destino": "zombi_inmortal", "via": "C_primero", "nota": "F7 sube sin Se ni S"}
      ]
    },
    "E3": {
      "id": "E3",
      "nombre": "Funcional",
      "tipo": "equilibrado",
      "descripcion": "Funciona, comprende parcialmente, persiste parcialmente. Sistema suficiente.",
      "condicion": {
        "gap_max": 0.15,
        "gradiente_min": 0.40,
        "gradiente_max": 0.65
      },
      "semantica": "Equilibrio trampa: suficientemente bueno para no motivar cambio, débil ante crisis.",
      "transiciones": [
        {"destino": "E4", "via": "intervencion_deliberada", "nota": "Subir las 3 lentes coordinadamente"},
        {"destino": "E3", "via": "inercia", "nota": "Sin intervención permanece estable"},
        {"destino": "desequilibrio", "via": "tension_externa", "nota": "Modo B+N revela eslabón débil"}
      ]
    },
    "E4": {
      "id": "E4",
      "nombre": "Plenitud",
      "tipo": "equilibrado",
      "descripcion": "Funciona bien, comprende profundamente, persiste robustamente. Sistema sano.",
      "condicion": {
        "gap_max": 0.15,
        "gradiente_min": 0.65,
        "gradiente_max": 1.00
      },
      "semantica": "Homeostasis activa. Requiere vigilancia para mantener.",
      "requisito_minimo": ">=7 INT + >=4 P + >=3 R distribuidos entre las 3 lentes (Ley IC7)",
      "transiciones": [
        {"destino": "E4", "via": "homeostasis_vigilancia", "nota": "Mantenimiento activo"},
        {"destino": "E3", "via": "degradacion_gradual", "nota": "Sin vigilancia, baja lentamente"}
      ]
    }
  },
  "desequilibrados": {
    "operador_ciego": {
      "id": "operador_ciego",
      "nombre": "Operador ciego",
      "tipo": "desequilibrado",
      "perfil_lentes": "S↑ Se↓ C↓",
      "descripcion": "Taller lleno de herramientas de ejecución. Ninguna de cuestionamiento. Maginot.",
      "condicion": {
        "gap_min": 0.15,
        "S_alta": true,
        "Se_baja": true,
        "C_baja": true
      },
      "ints_tipicas_activas": ["INT-01", "INT-02", "INT-05", "INT-07", "INT-16"],
      "ints_tipicas_ausentes": ["INT-17", "INT-18", "INT-03", "INT-08"],
      "ps_tipicos": {"activos": ["P07", "P13", "P14"], "ausentes": ["P08", "P05", "P03", "P01"]},
      "rs_tipicos": {"activos": ["R01", "R07", "R12"], "ausentes": ["R03", "R08", "R10"]},
      "prescripcion_ps": ["P05", "P03", "P08"],
      "prescripcion_rs": ["R03", "R09", "R08"],
      "objetivo_prescripcion": "CUESTIONAR premisas",
      "transiciones": [
        {"destino": "automata_eterno", "via": "C_sube_sin_Se", "nota": "PEOR transición posible"},
        {"destino": "genio_mortal", "via": "Se_sube", "nota": "Luego E4 con C"}
      ]
    },
    "visionario_atrapado": {
      "id": "visionario_atrapado",
      "nombre": "Visionario atrapado",
      "tipo": "desequilibrado",
      "perfil_lentes": "S↓ Se↑ C↓",
      "descripcion": "Taller filosófico extraordinario. Cero herramientas de ejecución.",
      "condicion": {
        "gap_min": 0.15,
        "S_baja": true,
        "Se_alta": true,
        "C_baja": true
      },
      "ints_tipicas_activas": ["INT-17", "INT-03", "INT-06", "INT-15", "INT-14"],
      "ints_tipicas_ausentes": ["INT-16", "INT-10", "INT-02", "INT-05"],
      "ps_tipicos": {"activos": ["P02", "P05", "P08", "P06"], "ausentes": ["P07", "P11", "P13", "P04"]},
      "rs_tipicos": {"activos": ["R03", "R08", "R10", "R05"], "ausentes": ["R01", "R12", "R07"]},
      "prescripcion_ps": ["P04", "P13", "P07"],
      "prescripcion_rs": ["R01", "R12", "R07"],
      "objetivo_prescripcion": "EJECUTAR",
      "transiciones": [
        {"destino": "potencial_dormido", "via": "C_sube_sin_S", "nota": "Comprende y transfiere pero no ejecuta"},
        {"destino": "genio_mortal", "via": "S_sube", "nota": "Luego E4 con C"}
      ]
    },
    "zombi_inmortal": {
      "id": "zombi_inmortal",
      "nombre": "Zombi inmortal",
      "tipo": "desequilibrado",
      "perfil_lentes": "S↓ Se↓ C↑",
      "descripcion": "No es ausencia sino fosilización. Las herramientas perdieron capacidad de cuestionar.",
      "condicion": {
        "gap_min": 0.15,
        "S_baja": true,
        "Se_baja": true,
        "C_alta": true
      },
      "ints_tipicas_activas": ["INT-13", "INT-02", "INT-16"],
      "ints_tipicas_ausentes": ["INT-17", "INT-14", "INT-15", "INT-04"],
      "ps_tipicos": {"activos": ["P09", "P13"], "ausentes": ["P05", "P08", "P03", "P01"]},
      "rs_tipicos": {"activos": ["R04", "R12"], "ausentes": ["R03", "R10", "R08", "R06"]},
      "prescripcion_ps": ["P05", "P08", "P01"],
      "prescripcion_rs": ["R10", "R03", "R11"],
      "objetivo_prescripcion": "CUESTIONAR EXISTENCIA",
      "nota": "Las INT activas están DEGRADADAS (mecánicas, rutinarias). No ausentes sino fosilizadas.",
      "transiciones": [
        {"destino": "E1", "via": "auditoria_Se_muerte_deliberada", "nota": "FIN si Se revela que C no tiene sustancia"},
        {"destino": "E2", "via": "auditoria_Se_reconstruccion", "nota": "Volver a empezar desde latencia"}
      ]
    },
    "genio_mortal": {
      "id": "genio_mortal",
      "nombre": "Genio mortal",
      "tipo": "desequilibrado",
      "perfil_lentes": "S↑ Se↑ C↓",
      "descripcion": "Repertorio rico pero privado. Carencia específica: herramientas de transferencia.",
      "condicion": {
        "gap_min": 0.15,
        "S_alta": true,
        "Se_alta": true,
        "C_baja": true
      },
      "ints_tipicas_activas": ["INT-01", "INT-02", "INT-03", "INT-05", "INT-07", "INT-08", "INT-16", "INT-17"],
      "ints_tipicas_ausentes": ["INT-13", "INT-12"],
      "ps_tipicos": {"activos": ["P02", "P03", "P04", "P05", "P08", "P15"], "ausentes": ["P12", "P09"]},
      "rs_tipicos": {"activos": ["R01", "R02", "R03", "R05", "R08"], "ausentes": ["R04", "R12"]},
      "prescripcion_ps": ["P12", "P13", "P04"],
      "prescripcion_rs": ["R04", "R12", "R01"],
      "objetivo_prescripcion": "TRANSFERIR",
      "transiciones": [
        {"destino": "E4", "via": "C_sube_via_F7Se", "nota": "Replicar CON sentido"},
        {"destino": "visionario_atrapado", "via": "S_baja", "nota": "Pierde ejecución"},
        {"destino": "potencial_dormido", "via": "Se_baja", "nota": "Pierde comprensión"}
      ]
    },
    "automata_eterno": {
      "id": "automata_eterno",
      "nombre": "Autómata eterno",
      "tipo": "desequilibrado",
      "perfil_lentes": "S↑ Se↓ C↑",
      "descripcion": "EL MÁS PELIGROSO. Operador ciego + herramientas de continuidad. S+C PARECE sano. Las herramientas ausentes son exactamente las de ALARMA.",
      "condicion": {
        "gap_min": 0.15,
        "S_alta": true,
        "Se_baja": true,
        "C_alta": true
      },
      "flags": ["peligro_oculto", "invisible_metricas_convencionales"],
      "ints_tipicas_activas": ["INT-01", "INT-02", "INT-05", "INT-07", "INT-13", "INT-16"],
      "ints_tipicas_ausentes": ["INT-17", "INT-18", "INT-08", "INT-14"],
      "ps_tipicos": {"activos": ["P07", "P09", "P13", "P14"], "ausentes": ["P08", "P05", "P01", "P03"]},
      "rs_tipicos": {"activos": ["R01", "R04", "R07", "R12"], "ausentes": ["R03", "R08", "R10", "R06"]},
      "prescripcion_ps": ["P08", "P09", "P01"],
      "prescripcion_rs": ["R03", "R06", "R10"],
      "objetivo_prescripcion": "VER LO INVISIBLE",
      "transiciones": [
        {"destino": "E3", "via": "Se_sube_a_tiempo", "nota": "Luego E4"},
        {"destino": "colapso_catastrofico", "via": "Se_no_sube", "nota": "Boeing, Maginot"}
      ]
    },
    "potencial_dormido": {
      "id": "potencial_dormido",
      "nombre": "Potencial dormido",
      "tipo": "desequilibrado",
      "perfil_lentes": "S↓ Se↑ C↑",
      "descripcion": "EL MÁS FÁCIL. Solo necesita activar 2-3 herramientas de S y ejecutar.",
      "condicion": {
        "gap_min": 0.15,
        "S_baja": true,
        "Se_alta": true,
        "C_alta": true
      },
      "ints_tipicas_activas": ["INT-03", "INT-12", "INT-13", "INT-17", "INT-04"],
      "ints_tipicas_ausentes": ["INT-10", "INT-16", "INT-11"],
      "ps_tipicos": {"activos": ["P02", "P05", "P09", "P12"], "ausentes": ["P11", "P04", "P07"]},
      "rs_tipicos": {"activos": ["R03", "R05", "R08", "R04"], "ausentes": ["R01", "R12", "R07"]},
      "prescripcion_ps": ["P11", "P04", "P14"],
      "prescripcion_rs": ["R12", "R01", "R07"],
      "objetivo_prescripcion": "MOVER",
      "transiciones": [
        {"destino": "E4", "via": "S_sube", "nota": "El más fácil de resolver"}
      ]
    }
  }
}
```

**Pass/fail:**
```bash
python3 -c "
import json
data = json.load(open('@project/src/tcf/estados.json'))
eq = data['equilibrados']
deq = data['desequilibrados']
assert len(eq) == 4, f'Expected 4 equilibrados, got {len(eq)}'
assert len(deq) == 6, f'Expected 6 desequilibrados, got {len(deq)}'
for eid in ['E1', 'E2', 'E3', 'E4']:
    assert eid in eq, f'Missing {eid}'
    assert 'condicion' in eq[eid]
for did in ['operador_ciego', 'visionario_atrapado', 'zombi_inmortal', 'genio_mortal', 'automata_eterno', 'potencial_dormido']:
    assert did in deq, f'Missing {did}'
    assert 'prescripcion_ps' in deq[did]
    assert 'prescripcion_rs' in deq[did]
print(f'PASS: {len(eq)} equilibrados + {len(deq)} desequilibrados = 10 estados')
"
```

---

## PASO 2: Crear flags.py

**Crear archivo:** `@project/src/tcf/flags.py`

**Contenido EXACTO:**

```python
"""Flags de peligro oculto — detectan estados que métricas convencionales no ven.

Fuente: FRAMEWORK_ACD.md §3.3, §5 Paso 3.
3 flags:
  1. Autómata oculto: S↑ + C↑ + Se↓ — parece sano, es frágil
  2. Monopolio Se: una F con Se alto, resto Se bajo — rigidez de sentido
  3. Zona tóxica: Se_avg < 0.25 — cualquier operación que no inyecte Se es inerte o tóxica
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FlagPeligro:
    nombre: str
    detectado: bool
    detalle: str
    severidad: str  # "critico", "alto", "medio"


def es_automata_oculto(lentes: dict[str, float]) -> FlagPeligro:
    """S>0.60 + C>0.60 + Se<0.30 → sistema que parece sano pero es frágil.
    
    Invisible para métricas convencionales. Solo Se lo detecta.
    Ejemplos: Boeing pre-737MAX, Maginot pre-1940.
    """
    s = lentes.get("salud", 0)
    se = lentes.get("sentido", 0)
    c = lentes.get("continuidad", 0)
    
    detectado = s > 0.60 and c > 0.60 and se < 0.30
    
    return FlagPeligro(
        nombre="automata_oculto",
        detectado=detectado,
        detalle=(
            f"S={s:.2f} C={c:.2f} Se={se:.2f}. "
            f"{'PELIGRO: Sistema parece sano pero Se<0.30. Frágil ante cambio de contexto.'
              if detectado else 'No detectado.'}"
        ),
        severidad="critico" if detectado else "ninguno",
    )


def es_monopolio_se(scores_f_se: dict[str, float]) -> FlagPeligro:
    """Una función con Se>0.70 + resto Se<0.30 → sentido concentrado en un punto.
    
    Args:
        scores_f_se: dict con {F1: se_score, F2: se_score, ...} — score de Se por función.
                     Si no se tienen scores por función, pasar dict vacío.
    """
    if not scores_f_se:
        return FlagPeligro(
            nombre="monopolio_se",
            detectado=False,
            detalle="Sin datos de Se por función.",
            severidad="ninguno",
        )
    
    valores = list(scores_f_se.values())
    max_se = max(valores)
    otras = [v for v in valores if v < max_se]
    
    detectado = max_se > 0.70 and all(v < 0.30 for v in otras)
    
    funcion_monopolio = None
    if detectado:
        funcion_monopolio = max(scores_f_se, key=scores_f_se.get)
    
    return FlagPeligro(
        nombre="monopolio_se",
        detectado=detectado,
        detalle=(
            f"{'PELIGRO: Se concentrado en ' + funcion_monopolio + f' ({max_se:.2f}). Resto < 0.30. Rigidez de sentido.'
              if detectado else 'Se distribuido normalmente.'}"
        ),
        severidad="alto" if detectado else "ninguno",
    )


def es_zona_toxica(lentes: dict[str, float]) -> FlagPeligro:
    """Se_avg < 0.25 → cualquier operación que no inyecte Se es inerte o tóxica.
    
    Elemento absorbente del álgebra: Se baja absorbe cualquier intervención.
    """
    se = lentes.get("sentido", 0)
    
    detectado = se < 0.25
    
    return FlagPeligro(
        nombre="zona_toxica",
        detectado=detectado,
        detalle=(
            f"Se_avg={se:.2f}. "
            f"{'PELIGRO: Se < 0.25. Cualquier operación que no inyecte Se primero será inerte o dañina.'
              if detectado else 'Se suficiente.'}"
        ),
        severidad="critico" if detectado else "ninguno",
    )


def detectar_todos_flags(
    lentes: dict[str, float],
    scores_f_se: dict[str, float] | None = None,
) -> list[FlagPeligro]:
    """Ejecuta los 3 flags y devuelve solo los detectados."""
    flags = [
        es_automata_oculto(lentes),
        es_monopolio_se(scores_f_se or {}),
        es_zona_toxica(lentes),
    ]
    return [f for f in flags if f.detectado]
```

**Pass/fail:**
```bash
cd @project/ && python3 -c "
from src.tcf.flags import es_automata_oculto, es_monopolio_se, es_zona_toxica, detectar_todos_flags

# Test 1: Autómata oculto positivo
f1 = es_automata_oculto({'salud': 0.70, 'sentido': 0.20, 'continuidad': 0.65})
assert f1.detectado, 'Should detect automata oculto'
assert f1.severidad == 'critico'
print('PASS: automata oculto detectado')

# Test 2: Autómata oculto negativo (sistema sano)
f2 = es_automata_oculto({'salud': 0.70, 'sentido': 0.65, 'continuidad': 0.60})
assert not f2.detectado, 'Should NOT detect automata oculto when Se is high'
print('PASS: automata oculto no detectado en sistema sano')

# Test 3: Monopolio Se positivo
f3 = es_monopolio_se({'F1': 0.10, 'F2': 0.15, 'F3': 0.80, 'F4': 0.10, 'F5': 0.20, 'F6': 0.10, 'F7': 0.05})
assert f3.detectado, 'Should detect monopolio Se'
print('PASS: monopolio Se detectado')

# Test 4: Zona tóxica positiva
f4 = es_zona_toxica({'salud': 0.50, 'sentido': 0.20, 'continuidad': 0.40})
assert f4.detectado, 'Should detect zona toxica'
assert f4.severidad == 'critico'
print('PASS: zona toxica detectada')

# Test 5: Zona tóxica negativa
f5 = es_zona_toxica({'salud': 0.50, 'sentido': 0.55, 'continuidad': 0.40})
assert not f5.detectado, 'Should NOT detect zona toxica when Se > 0.25'
print('PASS: zona toxica no detectada con Se suficiente')

# Test 6: detectar_todos_flags integrado
flags = detectar_todos_flags(
    lentes={'salud': 0.70, 'sentido': 0.20, 'continuidad': 0.65},
    scores_f_se=None
)
assert len(flags) == 2, f'Expected 2 flags (automata + toxica), got {len(flags)}'
nombres = [f.nombre for f in flags]
assert 'automata_oculto' in nombres
assert 'zona_toxica' in nombres
print(f'PASS: detectar_todos_flags retorna {len(flags)} flags')

print('\\nTODOS LOS TESTS PASAN')
"
```

---

## PASO 3: Añadir carga de estados a tcf/__init__.py

**Archivo:** `@project/src/tcf/__init__.py`

**Leer primero.** Luego añadir al final:

```python
import json
from pathlib import Path

_TCF_BASE = Path(__file__).parent
_estados: dict | None = None


def load_estados() -> dict:
    """Carga estados.json en memoria (singleton)."""
    global _estados
    if _estados is None:
        _estados = json.loads((_TCF_BASE / "estados.json").read_text())
    return _estados
```

**Pass/fail:**
```bash
cd @project/ && python3 -c "
from src.tcf import load_estados
data = load_estados()
assert 'equilibrados' in data
assert 'desequilibrados' in data
assert len(data['equilibrados']) == 4
assert len(data['desequilibrados']) == 6
print('PASS: load_estados() retorna 10 estados')
"
```

---

## VERIFICACIÓN FINAL

```bash
cd @project/ && python3 -c "
# Test integrado: estados + flags + campo existente
from src.tcf import load_estados
from src.tcf.flags import detectar_todos_flags
from src.tcf.campo import VectorFuncional, evaluar_campo, calcular_lentes

# Usar vector Pilates como test
v = VectorFuncional(f1=0.50, f2=0.30, f3=0.25, f4=0.35, f5=0.65, f6=0.35, f7=0.20)
lentes = calcular_lentes(v)
print(f'Lentes Pilates: S={lentes[\"salud\"]:.2f} Se={lentes[\"sentido\"]:.2f} C={lentes[\"continuidad\"]:.2f}')

# Flags
flags = detectar_todos_flags(lentes)
print(f'Flags detectados: {[f.nombre for f in flags]}')

# Estados
estados = load_estados()
print(f'Estados cargados: {len(estados[\"equilibrados\"])} eq + {len(estados[\"desequilibrados\"])} deq')

print('\\nPASS: Integración estados + flags + campo funciona')
"
```

**CRITERIO:** Todos los tests pasan. El vector Pilates NO dispara autómata oculto (correcto — Pilates es genio mortal, no autómata).

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/estados.json` | CREAR (nuevo) |
| `src/tcf/flags.py` | CREAR (nuevo) |
| `src/tcf/__init__.py` | AÑADIR load_estados() al final |

## ARCHIVOS QUE NO SE TOCAN

Todo lo demás. No se modifica campo.py, constantes.py ni ningún archivo existente de tcf/.
