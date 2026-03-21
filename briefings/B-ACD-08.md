# B-ACD-08: Diagnóstico completo end-to-end

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-05 ✅, B-ACD-06 ✅, B-ACD-07 ✅ (necesita los 3 anteriores)
**Secuencial:** Último de Fase 2. No ejecutar hasta que 05, 06, 07 pasen.

---

## CONTEXTO

Integra los 4 pasos diagnósticos (P1-P4) en una sola función `diagnosticar()`. Orquesta: evaluador_funcional → campo → clasificador → repertorio.

---

## PASO 1: Extender diagnostico.py con DiagnosticoCompleto y diagnosticar()

**Archivo:** `@project/src/tcf/diagnostico.py` (ya existe de B-ACD-06)

**Leer primero.** Luego AÑADIR al final del archivo (no modificar lo existente):

```python
# ---------------------------------------------------------------------------
# DIAGNÓSTICO COMPLETO END-TO-END (B-ACD-08)
# ---------------------------------------------------------------------------


@dataclass
class DiagnosticoCompleto:
    """Resultado completo del pipeline diagnóstico ACD (P1-P4)."""
    # P1: Vector funcional
    scores_raw: dict[str, dict[str, float]]   # 21 scores F×L
    vector: VectorFuncional
    # P2: Estado del campo (lentes, coalición, perfil, toxicidad, atractor)
    estado_campo: EstadoCampo
    # P3: Estado diagnóstico (1 de 10) + flags
    estado: EstadoDiagnostico
    # P4: Repertorio cognitivo INT×P×R
    repertorio: RepertorioCognitivo


async def diagnosticar(caso_texto: str) -> DiagnosticoCompleto:
    """Pipeline diagnóstico ACD completo: texto → diagnóstico.

    Orquesta P1→P4:
      P1: evaluar_funcional(texto) → 21 scores + VectorFuncional
      P2: evaluar_campo(vector) → EstadoCampo (lentes, coalición, toxicidad, atractor)
      P3: clasificar_estado(lentes) → EstadoDiagnostico (1 de 10) + flags
      P4: inferir_repertorio(texto, vector) → RepertorioCognitivo + advertencias IC

    Args:
        caso_texto: Descripción del caso/sistema a diagnosticar.

    Returns:
        DiagnosticoCompleto con toda la información diagnóstica.

    Coste estimado: ~$0.005/caso (2 LLM calls Haiku: evaluador + repertorio).
    """
    import structlog
    log = structlog.get_logger()
    log.info("diagnosticar.start", caso_len=len(caso_texto))

    # P1: Derivar vector funcional desde texto
    from src.tcf.evaluador_funcional import evaluar_funcional
    scores_raw, vector = await evaluar_funcional(caso_texto)

    # P2: Evaluar campo completo (lentes, coalición, toxicidad, atractor)
    from src.tcf.campo import evaluar_campo
    estado_campo = evaluar_campo(vector)

    # P3: Clasificar estado diagnóstico (1 de 10) + flags
    # Extraer scores Se por función para flag monopolio_se
    scores_f_se = {fi: scores_raw[fi]["sentido"] for fi in scores_raw}
    estado = clasificar_estado(estado_campo.lentes, scores_f_se)

    # P4: Inferir repertorio cognitivo
    from src.tcf.repertorio import inferir_repertorio
    repertorio = await inferir_repertorio(caso_texto, vector)

    resultado = DiagnosticoCompleto(
        scores_raw=scores_raw,
        vector=vector,
        estado_campo=estado_campo,
        estado=estado,
        repertorio=repertorio,
    )

    log.info(
        "diagnosticar.ok",
        estado_id=estado.id,
        estado_nombre=estado.nombre,
        n_flags=len(estado.flags),
        n_ints_activas=len(repertorio.ints_activas),
        n_advertencias_ic=len(repertorio.advertencias_ic),
    )

    return resultado
```

**IMPORTANTE:** También necesitas añadir los imports al principio del archivo. Editar las líneas de import existentes para incluir:

**Añadir estos imports al bloque de imports existente:**
```python
from src.tcf.campo import VectorFuncional, EstadoCampo
from src.tcf.repertorio import RepertorioCognitivo
```

El archivo completo de imports (parte superior de diagnostico.py) debería quedar:
```python
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.tcf.campo import VectorFuncional, EstadoCampo
from src.tcf.constantes import UMBRAL_LENTE_ALTA, UMBRAL_LENTE_BAJA
from src.tcf.flags import FlagPeligro, detectar_todos_flags
from src.tcf.repertorio import RepertorioCognitivo
```

---

## PASO 2: Test end-to-end

**Pass/fail:**

```bash
cd @project/ && python3 -c "
import asyncio
from src.tcf.diagnostico import diagnosticar, DiagnosticoCompleto

async def test():
    caso = '''Estudio de Pilates con 8 años de operación en zona premium.
    Rentable: factura 12K/mes con 85% ocupación. Pero altamente dependiente de María,
    la instructora principal y dueña. Sin ella, las clases se cancelan.
    No hay manual de operaciones ni protocolo de sustitución.
    Los clientes vienen por María, no por la marca.
    Identidad clara: Pilates reformer premium, clientela fiel, boca a boca.
    No hay plan de expansión ni sistema de formación de nuevos instructores.
    No se han revisado procesos ni eliminado proveedores ineficientes en años.
    María trabaja 10 horas/día y no ha tomado vacaciones en 2 años.'''

    diag = await diagnosticar(caso)

    # Verificar tipo
    assert isinstance(diag, DiagnosticoCompleto), 'Tipo incorrecto'
    print(f'PASS 1: DiagnosticoCompleto creado')

    # Verificar P1: scores + vector
    assert len(diag.scores_raw) == 7, f'Expected 7 funciones, got {len(diag.scores_raw)}'
    d = diag.vector.to_dict()
    assert all(0.0 <= v <= 1.0 for v in d.values()), 'Vector fuera de rango'
    print(f'PASS 2: Vector = {d}')
    print(f'  Eslabón débil: {diag.vector.eslabon_debil()}')

    # Verificar P2: estado del campo
    ec = diag.estado_campo
    print(f'PASS 3: Campo — lentes={ec.lentes}, coalición={ec.coalicion}, perfil={ec.perfil_lente}')
    print(f'  Atractor: {ec.atractor_mas_cercano}, estable={ec.estable}')
    print(f'  Toxicidad total: {ec.toxicidad_total}')
    print(f'  Deps violadas: {len(ec.dependencias_violadas)}')

    # Verificar P3: estado diagnóstico
    est = diag.estado
    assert est.id is not None, 'Estado sin ID'
    assert est.tipo in ('equilibrado', 'desequilibrado'), f'Tipo inválido: {est.tipo}'
    print(f'PASS 4: Estado = {est.id} ({est.nombre}), tipo={est.tipo}')
    print(f'  Gap={est.gap}, Gradiente={est.gradiente}')
    print(f'  Flags: {[f.nombre for f in est.flags]}')

    # Verificar P4: repertorio
    rep = diag.repertorio
    assert len(rep.ints_activas) > 0, 'Cero INT activas'
    print(f'PASS 5: Repertorio — {len(rep.ints_activas)} activas, {len(rep.ints_atrofiadas)} atrofiadas, {len(rep.ints_ausentes)} ausentes')
    print(f'  INT activas: {rep.ints_activas}')
    print(f'  P activos: {rep.ps_activos}')
    print(f'  R activos: {rep.rs_activos}')
    print(f'  Advertencias IC: {rep.advertencias_ic}')

    # Coherencia mínima Pilates:
    # F7 (Replicar) debería ser bajo
    assert d['F7'] < 0.50, f'F7={d[\"F7\"]} debería ser < 0.50 para caso sin replicación'
    print(f'PASS 6: F7 baja (coherente con Pilates sin replicación)')

    print(f'\\n=== DIAGNÓSTICO COMPLETO PILATES ===')
    print(f'Estado: {est.id} — {est.nombre}')
    print(f'Descripción: {est.descripcion}')
    print(f'Vector: {d}')
    print(f'Lentes: {ec.lentes}')
    print(f'Flags: {[f\"{f.nombre} ({f.severidad})\" for f in est.flags]}')
    print(f'INT activas: {rep.ints_activas}')
    print(f'INT ausentes: {rep.ints_ausentes}')
    print(f'Advertencias: {rep.advertencias_ic}')

asyncio.run(test())
print('\\nTODOS LOS TESTS PASAN — PIPELINE ACD END-TO-END FUNCIONAL')
"
```

**CRITERIO PASS:**
1. DiagnosticoCompleto se crea sin crash
2. Vector tiene 7 grados válidos [0,1]
3. EstadoCampo tiene lentes, coalición, perfil, atractor
4. EstadoDiagnostico tiene ID + nombre + tipo + flags
5. Repertorio tiene INTs clasificadas + Ps + Rs
6. F7 baja para caso Pilates (coherencia)

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/diagnostico.py` | EDITAR — añadir imports + DiagnosticoCompleto + diagnosticar() |

## ARCHIVOS QUE NO SE TOCAN

evaluador_funcional.py, repertorio.py, campo.py, constantes.py, flags.py — se usan pero no se modifican.

## NOTAS

- Los imports de evaluar_funcional e inferir_repertorio son lazy (dentro de la función) para evitar importaciones circulares.
- El import de VectorFuncional, EstadoCampo y RepertorioCognitivo sí va en la cabecera (son tipos, no funciones async).
- Coste total: ~$0.005/caso (2 calls Haiku: evaluador + repertorio). Campo + clasificador + flags = $0 (código puro).
- Los scores_f_se para el flag monopolio_se se extraen directamente de los 21 scores raw del evaluador. Esto es un valor añadido de tener los 21 scores (no solo el vector de 7).
