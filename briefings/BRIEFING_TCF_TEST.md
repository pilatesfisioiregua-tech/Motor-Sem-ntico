# BRIEFING_TCF_TEST — Ejecutar tests del módulo TCF

**Fecha:** 2026-03-19
**Prioridad:** INMEDIATA — validar que el código creado funciona
**Ejecutar:** Claude Code

---

## QUÉ HACER

Ejecutar pytest sobre los 4 archivos de test nuevos del módulo TCF.

## COMANDO

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico && python -m pytest tests/test_campo.py tests/test_arquetipos.py tests/test_recetas.py tests/test_lentes.py -v --tb=short 2>&1
```

## CRITERIO PASS/FAIL

- **PASS:** Todos los tests pasan (0 failures)
- **FAIL:** Cualquier test falla → leer el traceback y corregir el archivo correspondiente

## ARCHIVOS INVOLUCRADOS

Tests:
- `tests/test_campo.py` — 15 tests: VectorFuncional, lentes, coalición, perfil, deps, toxicidad, atractor
- `tests/test_arquetipos.py` — 9 tests: scoring Pilates, pre-screening 4 arquetipos
- `tests/test_recetas.py` — 9 tests: regla 14, receta mixta Pilates, secuencia universal
- `tests/test_lentes.py` — 8 tests: transferencia, impacto, Nash, perfiles

Código bajo test:
- `src/tcf/__init__.py`
- `src/tcf/constantes.py`
- `src/tcf/campo.py`
- `src/tcf/arquetipos.py`
- `src/tcf/recetas.py`
- `src/tcf/lentes.py`

## SI FALLA

1. Leer el traceback completo
2. Identificar si es error de import, de lógica, o de datos
3. Corregir el archivo fuente (NO el test, a menos que el test esté mal escrito)
4. Re-ejecutar pytest
5. Repetir hasta 0 failures

## NOTAS

- El proyecto usa Python 3.11+
- No hay dependencias externas necesarias para el módulo TCF (solo stdlib + dataclasses)
- pytest debe estar instalado
- Si falta pytest: `pip install pytest`
- Los imports usan `src.tcf.xxx` — asegurarse de que el PYTHONPATH incluya el directorio del motor-semantico o ejecutar desde ahí

---

**FIN BRIEFING**
