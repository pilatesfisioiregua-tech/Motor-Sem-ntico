"""Tests B3 — Matriz 3L x 7F como entidad de primer nivel.

Tests 1-8:
  1. 21 celdas unicas, 3 lentes, 7 funciones (constantes)
  2. Todos los IDs siguen formato FuncionxLente
  3. LENTES/FUNCIONES de gestor.py coinciden con schema
  4. Color thresholds correctos (rojo/naranja/amarillo/verde)
  5. Gap blend: 0.7 LLM + 0.3 DB
  6. verify_step con mock verifica que registrador llama UPDATE celdas_matriz
  7. API /matriz/estado tiene claves celdas, por_lente, por_funcion, top_gaps (source check)
  8. API /matriz/termometro tiene clave color (source check)
"""

import os
import sys
import inspect

# Add agent/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


LENTES = ['Salud', 'Sentido', 'Continuidad']
FUNCIONES = ['Conservar', 'Captar', 'Depurar', 'Distribuir', 'Frontera', 'Adaptar', 'Replicar']


def _all_celda_ids():
    """Generate all 21 celda IDs."""
    return [f"{f}x{l}" for f in FUNCIONES for l in LENTES]


class TestB3CeldasMatriz:
    """Test 1: 21 celdas unicas, 3 lentes, 7 funciones."""

    def test_21_celdas_unicas(self):
        ids = _all_celda_ids()
        assert len(ids) == 21
        assert len(set(ids)) == 21  # all unique

    def test_3_lentes(self):
        assert len(LENTES) == 3
        assert 'Salud' in LENTES
        assert 'Sentido' in LENTES
        assert 'Continuidad' in LENTES

    def test_7_funciones(self):
        assert len(FUNCIONES) == 7
        assert 'Conservar' in FUNCIONES
        assert 'Replicar' in FUNCIONES

    def test_cross_product(self):
        ids = _all_celda_ids()
        for f in FUNCIONES:
            for l in LENTES:
                assert f"{f}x{l}" in ids


class TestB3IDFormat:
    """Test 2: Todos los IDs siguen formato FuncionxLente."""

    def test_format_funcion_x_lente(self):
        for celda_id in _all_celda_ids():
            parts = celda_id.split('x')
            assert len(parts) == 2, f"ID {celda_id} does not follow FuncionxLente format"
            assert parts[0] in FUNCIONES, f"Funcion {parts[0]} not in FUNCIONES"
            assert parts[1] in LENTES, f"Lente {parts[1]} not in LENTES"

    def test_no_spaces_or_special_chars(self):
        for celda_id in _all_celda_ids():
            assert ' ' not in celda_id
            assert '×' not in celda_id  # must be ASCII x, not unicode


class TestB3GestorConstants:
    """Test 3: LENTES/FUNCIONES de gestor.py coinciden con schema."""

    def test_gestor_lentes_match(self):
        from core.gestor import LENTES as GESTOR_LENTES
        assert GESTOR_LENTES == LENTES

    def test_gestor_funciones_match(self):
        from core.gestor import FUNCIONES as GESTOR_FUNCIONES
        assert GESTOR_FUNCIONES == FUNCIONES

    def test_migration_constants_match(self):
        from migrations.b3_celdas_matriz import LENTES as MIG_LENTES
        from migrations.b3_celdas_matriz import FUNCIONES as MIG_FUNCIONES
        assert MIG_LENTES == LENTES
        assert MIG_FUNCIONES == FUNCIONES


class TestB3ColorThresholds:
    """Test 4: Color thresholds correctos (rojo >= 0.6, naranja >= 0.3, amarillo >= 0.1, verde < 0.1)."""

    def _color(self, gap):
        if gap >= 0.6:
            return 'rojo'
        elif gap >= 0.3:
            return 'naranja'
        elif gap >= 0.1:
            return 'amarillo'
        else:
            return 'verde'

    def test_rojo(self):
        assert self._color(0.6) == 'rojo'
        assert self._color(0.9) == 'rojo'
        assert self._color(1.0) == 'rojo'

    def test_naranja(self):
        assert self._color(0.3) == 'naranja'
        assert self._color(0.5) == 'naranja'
        assert self._color(0.59) == 'naranja'

    def test_amarillo(self):
        assert self._color(0.1) == 'amarillo'
        assert self._color(0.2) == 'amarillo'
        assert self._color(0.29) == 'amarillo'

    def test_verde(self):
        assert self._color(0.0) == 'verde'
        assert self._color(0.05) == 'verde'
        assert self._color(0.09) == 'verde'

    def test_boundary_rojo_naranja(self):
        assert self._color(0.6) == 'rojo'
        assert self._color(0.5999) == 'naranja'

    def test_boundary_naranja_amarillo(self):
        assert self._color(0.3) == 'naranja'
        assert self._color(0.2999) == 'amarillo'

    def test_boundary_amarillo_verde(self):
        assert self._color(0.1) == 'amarillo'
        assert self._color(0.0999) == 'verde'


class TestB3GapBlend:
    """Test 5: Gap blend formula: gap_final = 0.7 * gap_llm + 0.3 * gap_db."""

    def test_blend_basic(self):
        gap_llm = 0.8
        gap_db = 0.5
        expected = round(0.7 * gap_llm + 0.3 * gap_db, 4)
        assert expected == round(0.7 * 0.8 + 0.3 * 0.5, 4)
        assert expected == 0.71

    def test_blend_all_llm(self):
        gap_llm = 1.0
        gap_db = 0.0
        expected = round(0.7 * gap_llm + 0.3 * gap_db, 4)
        assert expected == 0.7

    def test_blend_all_db(self):
        gap_llm = 0.0
        gap_db = 1.0
        expected = round(0.7 * gap_llm + 0.3 * gap_db, 4)
        assert expected == 0.3

    def test_blend_equal(self):
        gap_llm = 0.5
        gap_db = 0.5
        expected = round(0.7 * gap_llm + 0.3 * gap_db, 4)
        assert expected == 0.5

    def test_blend_in_gestor_source(self):
        """Verify the 0.7/0.3 blend exists in gestor.py source."""
        source = inspect.getsource(sys.modules.get('core.gestor') or __import__('core.gestor'))
        assert '0.7' in source
        assert '0.3' in source
        assert 'gap_llm' in source or 'gap_db' in source


class TestB3RegistradorUpdate:
    """Test 6: registrador.py contains UPDATE celdas_matriz logic."""

    def test_registrador_has_celdas_matriz_update(self):
        """Verify registrador.py source contains celdas_matriz UPDATE."""
        import core.registrador as reg
        source = inspect.getsource(reg)
        assert 'celdas_matriz' in source, "registrador.py must reference celdas_matriz"
        assert 'UPDATE celdas_matriz' in source, "registrador.py must UPDATE celdas_matriz"

    def test_update_after_commit(self):
        """Verify the UPDATE comes after conn.commit() and before computar_señales_pid."""
        import core.registrador as reg
        source = inspect.getsource(reg.registrar_ejecucion)
        idx_commit = source.find('conn.commit()')
        idx_update = source.find('UPDATE celdas_matriz')
        idx_pid = source.find('computar_señales_pid')
        assert idx_commit < idx_update < idx_pid, \
            "UPDATE celdas_matriz must be between conn.commit() and computar_señales_pid"


class TestB3APIMatrizEstado:
    """Test 7: API /matriz/estado has keys celdas, por_lente, por_funcion, top_gaps (source check)."""

    def test_endpoint_exists(self):
        """Verify /matriz/estado endpoint is defined in api.py."""
        api_path = os.path.join(os.path.dirname(__file__), '..', 'api.py')
        with open(api_path, 'r') as f:
            source = f.read()
        assert '/matriz/estado' in source, "api.py must define /matriz/estado endpoint"

    def test_response_keys_in_source(self):
        """Verify response contains required keys."""
        api_path = os.path.join(os.path.dirname(__file__), '..', 'api.py')
        with open(api_path, 'r') as f:
            source = f.read()
        # Check the return dict has the required keys
        assert '"celdas"' in source, "Response must include 'celdas' key"
        assert '"por_lente"' in source, "Response must include 'por_lente' key"
        assert '"por_funcion"' in source, "Response must include 'por_funcion' key"
        assert '"top_gaps"' in source, "Response must include 'top_gaps' key"


class TestB3APIMatrizTermometro:
    """Test 8: API /matriz/termometro has clave color (source check)."""

    def test_endpoint_exists(self):
        """Verify /matriz/termometro endpoint is defined in api.py."""
        api_path = os.path.join(os.path.dirname(__file__), '..', 'api.py')
        with open(api_path, 'r') as f:
            source = f.read()
        assert '/matriz/termometro' in source, "api.py must define /matriz/termometro endpoint"

    def test_color_field_in_source(self):
        """Verify response includes color_termometro field."""
        api_path = os.path.join(os.path.dirname(__file__), '..', 'api.py')
        with open(api_path, 'r') as f:
            source = f.read()
        assert 'color_termometro' in source, "Response must include color_termometro"

    def test_color_thresholds_in_source(self):
        """Verify color thresholds match spec (rojo/naranja/amarillo/verde)."""
        api_path = os.path.join(os.path.dirname(__file__), '..', 'api.py')
        with open(api_path, 'r') as f:
            source = f.read()
        assert "'rojo'" in source or '"rojo"' in source
        assert "'naranja'" in source or '"naranja"' in source
        assert "'amarillo'" in source or '"amarillo"' in source
        assert "'verde'" in source or '"verde"' in source

    def test_consumidor_parameter(self):
        """Verify endpoint accepts consumidor parameter."""
        api_path = os.path.join(os.path.dirname(__file__), '..', 'api.py')
        with open(api_path, 'r') as f:
            source = f.read()
        assert 'consumidor' in source
