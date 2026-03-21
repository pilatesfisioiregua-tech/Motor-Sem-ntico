# B-ACD-02: Crear razonamientos.json + load_razonamientos()

**Fecha:** 2026-03-19
**Ejecutor:** Claude Code
**Paralelizable con:** B-ACD-01 (sin conflicto — este usa anchor diferente en __init__.py)
**Dependencia:** Ninguna

---

## PASO 1: Crear razonamientos.json

**Crear archivo:** `@project/src/meta_red/razonamientos.json`

**Contenido EXACTO:**

```json
{
  "R01": {
    "id": "R01",
    "nombre": "Deducción",
    "descripcion": "De lo general a lo particular. Garantiza conclusiones si las premisas son verdaderas",
    "lente_preferente": "salud",
    "funciones_naturales": ["F1", "F3"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-01", "INT-02", "INT-07"],
    "genera": "Certeza operativa",
    "limite": "No genera nada nuevo. Si las premisas son falsas, conclusión perfecta pero inútil (Maginot)",
    "pregunta_activadora": "¿Qué se puede concluir con certeza desde lo que ya sabemos?"
  },
  "R02": {
    "id": "R02",
    "nombre": "Inducción",
    "descripcion": "De lo particular a lo general. Generaliza desde observaciones, produce hipótesis probables",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F2", "F5"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-04", "INT-13", "INT-02"],
    "genera": "Patrones generales",
    "limite": "Nunca es segura (cisne negro). Vulnerable al sesgo de confirmación",
    "pregunta_activadora": "¿Qué patrón emerge de las observaciones?"
  },
  "R03": {
    "id": "R03",
    "nombre": "Abducción",
    "descripcion": "La mejor explicación. Genera la hipótesis más plausible para un fenómeno. Razonamiento del diagnosticador",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F3", "F5"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-03", "INT-08", "INT-17"],
    "genera": "Mejor explicación (diagnóstico)",
    "limite": "Múltiples explicaciones plausibles. La 'mejor' depende de criterios no siempre explícitos",
    "pregunta_activadora": "¿Cuál es la explicación más plausible de lo que observamos?",
    "nota": "Razonamiento central del Motor: diagnosticar perfil desde scores es abducción"
  },
  "R04": {
    "id": "R04",
    "nombre": "Analogía",
    "descripcion": "Transferencia de estructura entre dominios. No compara contenido sino relaciones",
    "lente_preferente": "sentido+continuidad",
    "funciones_naturales": ["F7", "F5"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-15", "INT-12", "INT-14"],
    "genera": "Transferencia cross-dominio",
    "limite": "Puede ser superficial. Semejanza estructural no garantiza mismo mecanismo",
    "pregunta_activadora": "¿Qué problema resuelto en otro dominio tiene la misma estructura?"
  },
  "R05": {
    "id": "R05",
    "nombre": "Causal",
    "descripcion": "Establece relaciones causa-efecto y cadenas causales. Va más allá de correlación a mecanismo",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F3", "F4"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-01", "INT-03", "INT-04"],
    "genera": "Mecanismos de causa-efecto",
    "limite": "La causalidad es difícil de establecer. Confundir correlación con causa es error común",
    "pregunta_activadora": "¿Qué causa qué aquí, y por qué mecanismo?"
  },
  "R06": {
    "id": "R06",
    "nombre": "Contrafactual",
    "descripcion": "Imagina mundos alternativos. ¿Qué habría pasado si una variable cambiara?",
    "lente_preferente": "sentido+continuidad",
    "funciones_naturales": ["F6", "F3"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-13", "INT-05", "INT-14"],
    "genera": "Evaluación de importancia de factores",
    "limite": "No verificable. Los contrafactuales no tienen respuesta segura",
    "pregunta_activadora": "¿Qué habría pasado si esto hubiera sido diferente?"
  },
  "R07": {
    "id": "R07",
    "nombre": "Bayesiano",
    "descripcion": "Actualiza confianza en hipótesis a medida que llega nueva evidencia. Gradual, no binario",
    "lente_preferente": "salud",
    "funciones_naturales": ["F3", "F2"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-01", "INT-07", "INT-02"],
    "genera": "Confianza actualizable",
    "limite": "Los priors importan mucho. Priors incorrectos resisten mucha evidencia",
    "pregunta_activadora": "¿Cómo cambia mi confianza en esta hipótesis con la nueva evidencia?"
  },
  "R08": {
    "id": "R08",
    "nombre": "Dialéctico",
    "descripcion": "Tesis × Antítesis → Síntesis. Confronta posiciones opuestas para generar posición superior",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F5", "F6"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-17", "INT-06", "INT-15"],
    "genera": "Síntesis de opuestos",
    "limite": "No siempre hay síntesis. Algunos opuestos son genuinamente irreconciliables",
    "pregunta_activadora": "¿Qué posición superior integra lo válido de ambas posiciones opuestas?"
  },
  "R09": {
    "id": "R09",
    "nombre": "Eliminación",
    "descripcion": "Descarta candidatos hasta que quede lo posible. Reduce espacio de posibilidades",
    "lente_preferente": "salud+sentido",
    "funciones_naturales": ["F3"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-01", "INT-03", "INT-05"],
    "genera": "Reducción del espacio de búsqueda",
    "limite": "Requiere lista exhaustiva. Si faltan candidatos, conclusión incorrecta",
    "pregunta_activadora": "¿Qué opciones puedo descartar con certeza?"
  },
  "R10": {
    "id": "R10",
    "nombre": "Retroductivo",
    "descripcion": "Del efecto al mecanismo generador. ¿Qué estructura produciría necesariamente este fenómeno?",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F5"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-03", "INT-17", "INT-15"],
    "genera": "Estructura necesaria (descubrimiento profundo)",
    "limite": "Difícil y raro. Requiere pensamiento de alto nivel",
    "pregunta_activadora": "¿Qué estructura generaría necesariamente lo que observamos?"
  },
  "R11": {
    "id": "R11",
    "nombre": "Modal",
    "descripcion": "Distingue entre lo necesario, lo posible y lo contingente",
    "lente_preferente": "sentido+continuidad",
    "funciones_naturales": ["F5"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-17", "INT-18", "INT-03"],
    "genera": "Necesidad vs contingencia",
    "limite": "La frontera entre necesario y contingente es a veces borrosa",
    "pregunta_activadora": "¿Esto es necesario o contingente? ¿Podría ser de otra forma?"
  },
  "R12": {
    "id": "R12",
    "nombre": "Transductivo",
    "descripcion": "De particular a particular sin pasar por lo general. Razonamiento clínico del experto",
    "lente_preferente": "salud",
    "funciones_naturales": ["F7"],
    "nivel_logico": null,
    "ints_compatibles": ["INT-10", "INT-16", "INT-02"],
    "genera": "Transferencia caso a caso (rápida, pragmática)",
    "limite": "Anecdótico. Dos casos pueden parecer iguales y no serlo",
    "pregunta_activadora": "¿He visto algo parecido antes y qué funcionó?"
  }
}
```

**Pass/fail:**
```bash
python3 -c "
import json
data = json.load(open('@project/src/meta_red/razonamientos.json'))
assert len(data) == 12, f'Expected 12, got {len(data)}'
for rid in [f'R{i:02d}' for i in range(1, 13)]:
    assert rid in data, f'Missing {rid}'
    r = data[rid]
    for field in ['id', 'nombre', 'lente_preferente', 'funciones_naturales', 'genera', 'pregunta_activadora']:
        assert field in r, f'{rid} missing {field}'
print(f'PASS: {len(data)} razonamientos, todos con campos requeridos')
"
```

---

## PASO 2: Añadir load_razonamientos() a __init__.py

**Archivo:** `@project/src/meta_red/__init__.py`

**Acción:** Añadir AL FINAL del archivo (después de CUALQUIER función que ya exista — incluida load_pensamientos si B-ACD-01 ya corrió):

```python


_razonamientos: dict | None = None


def load_razonamientos() -> dict:
    """Carga razonamientos.json en memoria (singleton)."""
    global _razonamientos
    if _razonamientos is None:
        _razonamientos = json.loads((_BASE / "razonamientos.json").read_text())
    return _razonamientos
```

**ANCHOR PARA EDIT:** Leer `@project/src/meta_red/__init__.py` primero. Buscar la ÚLTIMA función definida (será `load_marco_linguistico` o `load_pensamientos` si B-ACD-01 ya corrió). Añadir DESPUÉS del último `return`.

**Si B-ACD-01 NO ha corrido aún:** anchor = `return _marco` (última línea actual).
**Si B-ACD-01 YA corrió:** anchor = `return _pensamientos`.

**Pass/fail:**
```bash
cd @project/ && python3 -c "
from src.meta_red import load_razonamientos
data = load_razonamientos()
assert len(data) == 12
assert data['R01']['nombre'] == 'Deducción'
assert data['R12']['nombre'] == 'Transductivo'
print('PASS: load_razonamientos() retorna 12 entradas')
"
```

---

## VERIFICACIÓN FINAL

```bash
cd @project/ && python3 -c "
from src.meta_red import load_inteligencias, load_marco_linguistico
i = load_inteligencias()
m = load_marco_linguistico()
print(f'{len(i)} INT + marco cargados')

# Razonamientos (este briefing)
from src.meta_red import load_razonamientos
r = load_razonamientos()
assert len(r) == 12

# Pensamientos (si B-ACD-01 ya corrió)
try:
    from src.meta_red import load_pensamientos
    p = load_pensamientos()
    print(f'PASS: {len(i)} INT + {len(p)} P + {len(r)} R cargados')
except ImportError:
    print(f'PASS: {len(i)} INT + {len(r)} R cargados (P pendiente de B-ACD-01)')
"
```

**CRITERIO:** Los tests de razonamientos pasan. La verificación final muestra 12 R.

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/meta_red/razonamientos.json` | CREAR (nuevo) |
| `src/meta_red/__init__.py` | AÑADIR función load_razonamientos() al final |
