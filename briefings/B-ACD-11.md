# B-ACD-11: Secuenciación con prohibiciones formales

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** Ninguna (extiende recetas.py con filtro independiente, código puro $0)
**Paralelizable con:** B-ACD-10

---

## CONTEXTO

Las recetas (secuencia_universal, generar_receta_mixta) generan secuencias de funciones. Pero hay combinaciones que son TÓXICAS según las leyes de la TCF. Las prohibiciones son un filtro posterior que detecta violaciones ANTES de ejecutar.

**4 prohibiciones formales:**
1. NUNCA F7 sin Se previo — F7 con Se < 0.40 amplifica sin sentido
2. NUNCA F2 sin F3 antes — captar sin depurar = intoxicación (Ley 3)
3. NUNCA escalar (F7) con gap > 0.30 — amplifica desequilibrio
4. NUNCA F6 sin F5 — adaptar sin identidad = perder esencia (Ley 14)

**Ya existe:** `secuencia_universal()` y `aplicar_regla_14()` en recetas.py. Las prohibiciones son complementarias (no reemplazan).

---

## PASO 1: Añadir verificar_prohibiciones a recetas.py

**Archivo:** `@project/src/tcf/recetas.py` (ya existe)

**Leer primero.** Luego AÑADIR al final del archivo (después de `secuencia_universal()`):

```python
# ---------------------------------------------------------------------------
# §5. PROHIBICIONES FORMALES (Leyes TCF 3, 4, 13, 14)
# ---------------------------------------------------------------------------

@dataclass
class Prohibicion:
    codigo: str          # "PRH-01", "PRH-02", etc.
    descripcion: str     # Qué se viola
    funcion_afectada: str  # "F7", "F2", etc.
    severidad: str       # "critica" | "alta"


def verificar_prohibiciones(
    secuencia: list[str],
    lentes: dict[str, float],
) -> list[Prohibicion]:
    """Detecta prohibiciones formales en una secuencia de funciones.

    Filtra combinaciones tóxicas ANTES de ejecutar. Complementa
    Regla 14 (FRENAR) y secuencia_universal().

    Args:
        secuencia: Lista de funciones en orden de ejecución.
                   Puede incluir prefijos "SUBIR_", "FRENAR_" que se limpian.
        lentes: {salud: float, sentido: float, continuidad: float}

    Returns:
        Lista de Prohibicion violadas (vacía si todo OK).
    """
    violaciones = []

    # Limpiar prefijos para trabajar con funciones puras
    funcs = [f.replace("SUBIR_", "").replace("FRENAR_", "") for f in secuencia]

    se = lentes.get("sentido", 0.0)
    gap = max(lentes.values()) - min(lentes.values()) if lentes else 0.0

    # PRH-01: F7 sin Se previo (Se < 0.40)
    if "F7" in funcs and se < 0.40:
        # F7 aparece sin que Se esté suficientemente alto
        violaciones.append(Prohibicion(
            codigo="PRH-01",
            descripcion=f"F7 (Replicar) con Se={se:.2f} < 0.40. "
                        "Amplifica sin sentido: replica mecánicamente.",
            funcion_afectada="F7",
            severidad="critica",
        ))

    # PRH-02: F2 sin F3 antes (captar sin depurar)
    if "F2" in funcs and "F3" in funcs:
        idx_f2 = funcs.index("F2")
        idx_f3 = funcs.index("F3")
        if idx_f2 < idx_f3:
            violaciones.append(Prohibicion(
                codigo="PRH-02",
                descripcion="F2 (Captar) antes de F3 (Depurar). "
                            "Captar sin depurar = intoxicación (Ley 3).",
                funcion_afectada="F2",
                severidad="alta",
            ))
    elif "F2" in funcs and "F3" not in funcs:
        # F2 presente sin F3 en absoluto
        violaciones.append(Prohibicion(
            codigo="PRH-02",
            descripcion="F2 (Captar) sin F3 (Depurar) en secuencia. "
                        "Captar sin depurar = intoxicación (Ley 3).",
            funcion_afectada="F2",
            severidad="alta",
        ))

    # PRH-03: F7 con gap > 0.30 (escalar desequilibrio)
    if "F7" in funcs and gap > 0.30:
        violaciones.append(Prohibicion(
            codigo="PRH-03",
            descripcion=f"F7 (Replicar) con gap={gap:.2f} > 0.30. "
                        "Escalar amplifica el desequilibrio entre lentes.",
            funcion_afectada="F7",
            severidad="critica",
        ))

    # PRH-04: F6 sin F5 antes (adaptar sin identidad)
    if "F6" in funcs and "F5" in funcs:
        idx_f6 = funcs.index("F6")
        idx_f5 = funcs.index("F5")
        if idx_f6 < idx_f5:
            violaciones.append(Prohibicion(
                codigo="PRH-04",
                descripcion="F6 (Adaptar) antes de F5 (Frontera). "
                            "Adaptar sin identidad = perder esencia (Ley 14).",
                funcion_afectada="F6",
                severidad="alta",
            ))
    elif "F6" in funcs and "F5" not in funcs:
        violaciones.append(Prohibicion(
            codigo="PRH-04",
            descripcion="F6 (Adaptar) sin F5 (Frontera) en secuencia. "
                        "Adaptar sin identidad = perder esencia (Ley 14).",
            funcion_afectada="F6",
            severidad="alta",
        ))

    return violaciones
```

**IMPORTANTE:** También añadir el import de `Prohibicion` como export. No se necesita import extra — ya tiene `dataclass` importado.

---

## PASO 2: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
from src.tcf.recetas import verificar_prohibiciones, Prohibicion

# Test 1: F7 sin Se previo
vs = verificar_prohibiciones(
    secuencia=['F7', 'F2', 'F5'],
    lentes={'salud': 0.60, 'sentido': 0.20, 'continuidad': 0.30}
)
prh01 = [v for v in vs if v.codigo == 'PRH-01']
assert len(prh01) == 1, f'Expected PRH-01, got {[v.codigo for v in vs]}'
assert prh01[0].severidad == 'critica'
print(f'PASS 1: PRH-01 detecta F7 con Se=0.20 ({prh01[0].descripcion[:50]}...)')

# Test 2: F2 sin F3 antes
vs = verificar_prohibiciones(
    secuencia=['F2', 'F3', 'F5'],
    lentes={'salud': 0.50, 'sentido': 0.50, 'continuidad': 0.50}
)
prh02 = [v for v in vs if v.codigo == 'PRH-02']
assert len(prh02) == 1, f'Expected PRH-02, got {[v.codigo for v in vs]}'
print(f'PASS 2: PRH-02 detecta F2 antes de F3')

# Test 3: F2 sin F3 en absoluto
vs = verificar_prohibiciones(
    secuencia=['F2', 'F5'],
    lentes={'salud': 0.50, 'sentido': 0.50, 'continuidad': 0.50}
)
prh02 = [v for v in vs if v.codigo == 'PRH-02']
assert len(prh02) == 1
print(f'PASS 3: PRH-02 detecta F2 sin F3 en secuencia')

# Test 4: F7 con gap > 0.30
vs = verificar_prohibiciones(
    secuencia=['F5', 'F3', 'F7'],
    lentes={'salud': 0.70, 'sentido': 0.70, 'continuidad': 0.20}
)
prh03 = [v for v in vs if v.codigo == 'PRH-03']
assert len(prh03) == 1
assert prh03[0].severidad == 'critica'
print(f'PASS 4: PRH-03 detecta F7 con gap={0.70-0.20:.2f}')

# Test 5: F6 sin F5 antes
vs = verificar_prohibiciones(
    secuencia=['F6', 'F5', 'F3'],
    lentes={'salud': 0.50, 'sentido': 0.50, 'continuidad': 0.50}
)
prh04 = [v for v in vs if v.codigo == 'PRH-04']
assert len(prh04) == 1
print(f'PASS 5: PRH-04 detecta F6 antes de F5')

# Test 6: Secuencia limpia — cero violaciones
vs = verificar_prohibiciones(
    secuencia=['F5', 'F3', 'F2', 'F1'],
    lentes={'salud': 0.50, 'sentido': 0.55, 'continuidad': 0.45}
)
assert len(vs) == 0, f'Expected 0 violations, got {len(vs)}: {[v.codigo for v in vs]}'
print(f'PASS 6: Secuencia [F5,F3,F2,F1] con lentes equilibradas → 0 violaciones')

# Test 7: Caso combinado (B-ACD-11 prompt spec: [F7,F2,F5] con Se=0.20)
vs = verificar_prohibiciones(
    secuencia=['F7', 'F2', 'F5'],
    lentes={'salud': 0.60, 'sentido': 0.20, 'continuidad': 0.30}
)
codigos = [v.codigo for v in vs]
assert 'PRH-01' in codigos, 'Debería detectar PRH-01 (F7 sin Se)'
assert 'PRH-02' in codigos, 'Debería detectar PRH-02 (F2 sin F3)'
assert 'PRH-03' in codigos, 'Debería detectar PRH-03 (F7 con gap>0.30)'
print(f'PASS 7: Caso combinado [F7,F2,F5] Se=0.20 → {codigos}')

# Test 8: Prefijos SUBIR_ se limpian
vs = verificar_prohibiciones(
    secuencia=['SUBIR_F7', 'SUBIR_F2'],
    lentes={'salud': 0.60, 'sentido': 0.20, 'continuidad': 0.30}
)
assert any(v.codigo == 'PRH-01' for v in vs), 'Prefijos SUBIR_ no se limpiaron'
print(f'PASS 8: Prefijos SUBIR_ se limpian correctamente')

print('\\nTODOS LOS TESTS PASAN (8/8)')
"
```

**CRITERIO PASS:**
1. PRH-01: F7 con Se < 0.40 → detectado, severidad critica
2. PRH-02: F2 antes de F3 → detectado
3. PRH-02: F2 sin F3 → detectado
4. PRH-03: F7 con gap > 0.30 → detectado, severidad critica
5. PRH-04: F6 antes de F5 → detectado
6. Secuencia limpia → 0 violaciones
7. Caso combinado del spec → 3 violaciones
8. Prefijos SUBIR_/FRENAR_ se limpian

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/recetas.py` | EDITAR — añadir §5 Prohibiciones al final |

## ARCHIVOS QUE NO SE TOCAN

Todo lo demás. Las prohibiciones son un módulo aditivo — no cambian nada existente.

## NOTAS

- ~70 líneas añadidas, código puro, $0, ~0ms
- Las prohibiciones NO corrigen la secuencia — solo detectan violaciones
- El prescriptor (B-ACD-09) las usará para advertir y opcionalmente reordenar
- Los umbrales (Se < 0.40, gap > 0.30) son derivados de las leyes TCF
- PRH-01 y PRH-03 son "critica" porque producen daño activo. PRH-02 y PRH-04 son "alta" porque producen degradación
