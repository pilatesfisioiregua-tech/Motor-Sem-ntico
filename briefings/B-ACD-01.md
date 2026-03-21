# B-ACD-01: Crear pensamientos.json + load_pensamientos()

**Fecha:** 2026-03-19
**Ejecutor:** Claude Code
**Paralelizable con:** B-ACD-02 (sin conflicto si se sigue el anchor de __init__.py)
**Dependencia:** Ninguna

---

## PASO 1: Crear pensamientos.json

**Crear archivo:** `@project/src/meta_red/pensamientos.json`

**Contenido EXACTO:**

```json
{
  "P01": {
    "id": "P01",
    "nombre": "Lateral",
    "descripcion": "Busca soluciones fuera del marco habitual moviendo lateralmente a una línea distinta",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F6"],
    "razonamientos_asociados": ["R04", "R06"],
    "nivel_logico": 3,
    "ints_compatibles": ["INT-14", "INT-15", "INT-09"],
    "ints_incompatibles": ["INT-01"],
    "cuando_usar": "Sistema atrapado en marco que no funciona: operador ciego, autómata eterno, rigidez",
    "pregunta_activadora": "¿Qué pasaría si hicieras exactamente lo contrario?"
  },
  "P02": {
    "id": "P02",
    "nombre": "Sistémico",
    "descripcion": "Ve el todo en vez de las partes: feedback loops, efectos no lineales, emergencia",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F4", "F5"],
    "razonamientos_asociados": ["R05", "R03", "R08"],
    "nivel_logico": 4,
    "ints_compatibles": ["INT-03", "INT-04", "INT-10"],
    "ints_incompatibles": [],
    "cuando_usar": "Siempre como modo base. Especialmente en E3 donde los ciclos entre funciones están activos",
    "pregunta_activadora": "¿Cómo se conectan las partes entre sí?"
  },
  "P03": {
    "id": "P03",
    "nombre": "Crítico",
    "descripcion": "Examina premisas, detecta falacias, evalúa calidad de evidencia",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F3", "F5"],
    "razonamientos_asociados": ["R01", "R09", "R07"],
    "nivel_logico": 3,
    "ints_compatibles": ["INT-01", "INT-03", "INT-17"],
    "ints_incompatibles": [],
    "cuando_usar": "Siempre como filtro. Contra sesgo retrospectivo y colapso de Tipos Lógicos",
    "pregunta_activadora": "¿Qué evidencia sostiene esta afirmación?"
  },
  "P04": {
    "id": "P04",
    "nombre": "Diseño",
    "descripcion": "Ciclo iterativo centrado en el usuario: empatizar, definir, idear, prototipar, testear",
    "lente_preferente": "salud+sentido",
    "funciones_naturales": ["F5", "F2", "F3"],
    "razonamientos_asociados": ["R03", "R02", "R12"],
    "nivel_logico": 3,
    "ints_compatibles": ["INT-16", "INT-08", "INT-15"],
    "ints_incompatibles": [],
    "cuando_usar": "Problema mal definido. E2 latencia y visionario atrapado. Fuerza transición Se a S",
    "pregunta_activadora": "¿Qué necesita realmente la persona que vive este problema?"
  },
  "P05": {
    "id": "P05",
    "nombre": "Primeros principios",
    "descripcion": "Descompone hasta lo fundamental rechazando analogías y suposiciones",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F3", "F1"],
    "razonamientos_asociados": ["R01", "R10", "R09"],
    "nivel_logico": 4,
    "ints_compatibles": ["INT-01", "INT-17", "INT-03"],
    "ints_incompatibles": [],
    "cuando_usar": "Soluciones convencionales no funcionan. Descubre lo irreducible",
    "pregunta_activadora": "¿Qué sabemos que es necesariamente verdad aquí?"
  },
  "P06": {
    "id": "P06",
    "nombre": "Divergente",
    "descripcion": "Amplía el espacio de posibilidades sin evaluar. Genera muchas opciones",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F2", "F6"],
    "razonamientos_asociados": ["R04", "R06"],
    "nivel_logico": 2,
    "ints_compatibles": ["INT-14", "INT-13", "INT-09"],
    "ints_incompatibles": [],
    "cuando_usar": "Sistema ve 2 opciones y necesita ver 20. Perfil binario",
    "pregunta_activadora": "¿De cuántas formas podría hacerse esto?"
  },
  "P07": {
    "id": "P07",
    "nombre": "Convergente",
    "descripcion": "Estrecha el espacio seleccionando la mejor opción según criterios explícitos",
    "lente_preferente": "salud",
    "funciones_naturales": ["F3", "F4"],
    "razonamientos_asociados": ["R01", "R09", "R07"],
    "nivel_logico": 2,
    "ints_compatibles": ["INT-01", "INT-05", "INT-07"],
    "ints_incompatibles": [],
    "cuando_usar": "Después de P06. Ciclo divergente-convergente es el patrón más común",
    "pregunta_activadora": "¿Cuál de estas opciones resuelve mejor el criterio principal?"
  },
  "P08": {
    "id": "P08",
    "nombre": "Metacognición",
    "descripcion": "Observa el propio proceso de pensamiento. Pensar sobre el pensar",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F3", "F5"],
    "razonamientos_asociados": ["R11", "R06"],
    "nivel_logico": 5,
    "ints_compatibles": ["INT-17", "INT-18", "INT-03"],
    "ints_incompatibles": [],
    "cuando_usar": "Siempre como capa de supervisión. Nivel 5 Tipos Lógicos. Esencial contra autómata eterno",
    "pregunta_activadora": "¿Estoy usando el marco correcto para pensar esto?"
  },
  "P09": {
    "id": "P09",
    "nombre": "Prospectivo",
    "descripcion": "Proyecta múltiples futuros posibles y evalúa robustez de decisiones ante cada uno",
    "lente_preferente": "continuidad",
    "funciones_naturales": ["F7", "F6"],
    "razonamientos_asociados": ["R06", "R07", "R11"],
    "nivel_logico": 5,
    "ints_compatibles": ["INT-13", "INT-05", "INT-04"],
    "ints_incompatibles": [],
    "cuando_usar": "Autómata eterno (anticipar cambio de contexto). E4 plenitud (modo vigilancia)",
    "pregunta_activadora": "¿En qué escenarios futuros esta decisión sería un error?"
  },
  "P10": {
    "id": "P10",
    "nombre": "Reflexivo",
    "descripcion": "Revisa lo vivido para extraer aprendizaje. Destilación sistemática de experiencia",
    "lente_preferente": "sentido+continuidad",
    "funciones_naturales": ["F1", "F3"],
    "razonamientos_asociados": ["R02", "R03", "R05"],
    "nivel_logico": 5,
    "ints_compatibles": ["INT-12", "INT-08", "INT-17"],
    "ints_incompatibles": [],
    "cuando_usar": "Después de cada ciclo del Motor. Reactor v5 es pensamiento reflexivo",
    "pregunta_activadora": "¿Qué aprendí de esta experiencia que no sabía antes?"
  },
  "P11": {
    "id": "P11",
    "nombre": "Encarnado",
    "descripcion": "Integra información sensorial, proprioceptiva y motora en la cognición",
    "lente_preferente": "salud",
    "funciones_naturales": ["F1"],
    "razonamientos_asociados": ["R12", "R03"],
    "nivel_logico": 1,
    "ints_compatibles": ["INT-10", "INT-15", "INT-11"],
    "ints_incompatibles": ["INT-01"],
    "cuando_usar": "Pilates. Fisioterapia. Cualquier situación donde el cuerpo tiene información que la mente no tiene",
    "pregunta_activadora": "¿Qué dice el cuerpo que la mente no escucha?"
  },
  "P12": {
    "id": "P12",
    "nombre": "Narrativo",
    "descripcion": "Organiza experiencia en secuencias con personajes, conflictos y resoluciones",
    "lente_preferente": "sentido+continuidad",
    "funciones_naturales": ["F5", "F7"],
    "razonamientos_asociados": ["R05", "R04"],
    "nivel_logico": 2,
    "ints_compatibles": ["INT-12", "INT-09", "INT-08"],
    "ints_incompatibles": [],
    "cuando_usar": "Genio mortal (contar historia para transferir). E1 muerte (primera narrativa para existir)",
    "pregunta_activadora": "¿Cuál es la historia de este sistema?"
  },
  "P13": {
    "id": "P13",
    "nombre": "Computacional",
    "descripcion": "Descomponer, abstraer, reconocer patrones, algoritmizar",
    "lente_preferente": "salud+continuidad",
    "funciones_naturales": ["F4", "F7"],
    "razonamientos_asociados": ["R01", "R09", "R02"],
    "nivel_logico": 1,
    "ints_compatibles": ["INT-02", "INT-01", "INT-16"],
    "ints_incompatibles": [],
    "cuando_usar": "Problema grande que necesita descomponerse. Genio mortal para algoritmizar método",
    "pregunta_activadora": "¿Cómo descompongo esto en partes manejables?"
  },
  "P14": {
    "id": "P14",
    "nombre": "Estratégico",
    "descripcion": "Piensa en movimientos y contra-movimientos, evalúa posiciones, optimiza secuencias",
    "lente_preferente": "salud+sentido",
    "funciones_naturales": ["F4", "F6"],
    "razonamientos_asociados": ["R06", "R07", "R01"],
    "nivel_logico": 3,
    "ints_compatibles": ["INT-05", "INT-06", "INT-07"],
    "ints_incompatibles": [],
    "cuando_usar": "Competencia o secuencia temporal importa. Potencial dormido para elegir primer movimiento",
    "pregunta_activadora": "¿Cuál es el primer movimiento que abre más opciones?"
  },
  "P15": {
    "id": "P15",
    "nombre": "Integrativo",
    "descripcion": "Mantiene opuestos sin elegir hasta que emerge modelo superior que integra ambos",
    "lente_preferente": "sentido",
    "funciones_naturales": ["F5", "F6"],
    "razonamientos_asociados": ["R08", "R11", "R10"],
    "nivel_logico": 4,
    "ints_compatibles": ["INT-17", "INT-03", "INT-15"],
    "ints_incompatibles": [],
    "cuando_usar": "Soluciones existentes parecen mutuamente excluyentes. Síntesis de opuestos",
    "pregunta_activadora": "¿Y si ambas opciones opuestas son verdad a la vez?"
  }
}
```

**Pass/fail:**
```bash
python3 -c "
import json
data = json.load(open('@project/src/meta_red/pensamientos.json'))
assert len(data) == 15, f'Expected 15, got {len(data)}'
for pid in [f'P{i:02d}' for i in range(1, 16)]:
    assert pid in data, f'Missing {pid}'
    p = data[pid]
    for field in ['id', 'nombre', 'lente_preferente', 'funciones_naturales', 'razonamientos_asociados', 'nivel_logico', 'pregunta_activadora']:
        assert field in p, f'{pid} missing {field}'
print(f'PASS: {len(data)} pensamientos, todos con campos requeridos')
"
```

---

## PASO 2: Añadir load_pensamientos() a __init__.py

**Archivo:** `@project/src/meta_red/__init__.py`

**Acción:** Añadir DESPUÉS de la función `load_marco_linguistico()` (que termina con `return _marco`):

```python


_pensamientos: dict | None = None


def load_pensamientos() -> dict:
    """Carga pensamientos.json en memoria (singleton)."""
    global _pensamientos
    if _pensamientos is None:
        _pensamientos = json.loads((_BASE / "pensamientos.json").read_text())
    return _pensamientos
```

**ANCHOR PARA EDIT:** Buscar `return _marco` (última línea del archivo actual) y añadir DESPUÉS.

**Pass/fail:**
```bash
cd @project/ && python3 -c "
from src.meta_red import load_pensamientos
data = load_pensamientos()
assert len(data) == 15
assert data['P01']['nombre'] == 'Lateral'
assert data['P15']['nombre'] == 'Integrativo'
print('PASS: load_pensamientos() retorna 15 entradas')
"
```

---

## VERIFICACIÓN FINAL

```bash
cd @project/ && python3 -c "
from src.meta_red import load_inteligencias, load_marco_linguistico, load_pensamientos
i = load_inteligencias()
m = load_marco_linguistico()
p = load_pensamientos()
assert len(i) == 18, f'inteligencias: {len(i)}'
assert len(p) == 15, f'pensamientos: {len(p)}'
print(f'PASS: {len(i)} INT + {len(p)} P cargados correctamente')
"
```

**CRITERIO:** Los 3 tests pasan sin error.

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/meta_red/pensamientos.json` | CREAR (nuevo) |
| `src/meta_red/__init__.py` | AÑADIR función load_pensamientos() después de load_marco_linguistico() |
