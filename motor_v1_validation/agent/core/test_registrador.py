"""Pruebas unitarias para el módulo registrador.py (SN-06)."""

import pytest
from unittest.mock import MagicMock, patch
from core.registrador import computar_señales_pid, PID_CONFIG


class TestRegistradorPID:
    """Pruebas para el cálculo de señales PID."""

    def test_computar_señales_pid_basico(self):
        """Test básico del cálculo de señales PID."""
        # Mock de la conexión a la base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Datos de ejemplo: 5 datapoints con gap_post decreciente
        # Orden: más reciente primero (timestamp DESC)
        mock_cursor.fetchall.return_value = [
            (0.4, 0.2, 0.50),  # gap_pre, gap_post, tasa_cierre (más reciente)
            (0.5, 0.3, 0.40),
            (0.6, 0.4, 0.33),
            (0.7, 0.5, 0.28),
            (0.8, 0.6, 0.25),  # más antiguo
        ]

        # Ejecutar la función
        señales = computar_señales_pid("ConservarxSalud", conn=mock_conn)

        # Verificar resultados
        assert señales['P'] == 0.2  # Último gap_post (más reciente)
        assert señales['I'] == 2.0  # Suma de gap_post (0.2+0.3+0.4+0.5+0.6)
        assert señales['I_anti_windup'] == 2.0  # Dentro del límite [-10, 10]
        assert señales['D'] == -0.2  # gap_post - gap_pre del más reciente: 0.2 - 0.4 = -0.2
        assert señales['n_total'] == 5
        assert 'señal_control' in señales

    def test_computar_señales_pid_anti_windup(self):
        """Test del anti-windup: I limitado a [-10, 10]."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Datos con gap_post muy alto (suma > 10)
        mock_cursor.fetchall.return_value = [
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
            (1.0, 0.9, 0.1),
        ]  # 11 puntos con gap_post=0.9 → suma=9.9

        señales = computar_señales_pid("ConservarxSalud", conn=mock_conn)

        # I debería ser 9.9 (dentro del límite)
        assert señales['I'] == 9.9
        assert señales['I_anti_windup'] == 9.9

        # Ahora con suma > 10
        mock_cursor.fetchall.return_value = [
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
        ]  # 11 puntos con gap_post=1.0 → suma=11.0

        señales = computar_señales_pid("ConservarxSalud", conn=mock_conn)

        # I debería ser 11.0, pero I_anti_windup debería estar limitado a 10.0
        assert señales['I'] == 11.0
        assert señales['I_anti_windup'] == 10.0  # Anti-windup activado

    def test_computar_señales_pid_derivada_filtrada(self):
        """Test del filtro de derivada: media móvil de 5 puntos."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Datos con ruido en la derivada
        mock_cursor.fetchall.return_value = [
            (0.5, 0.6, 0.2),  # diff = +0.1
            (0.6, 0.5, 0.2),  # diff = -0.1
            (0.5, 0.6, 0.2),  # diff = +0.1
            (0.6, 0.5, 0.2),  # diff = -0.1
            (0.5, 0.6, 0.2),  # diff = +0.1 (último)
        ]

        señales = computar_señales_pid("ConservarxSalud", conn=mock_conn)

        # D_raw debería ser +0.1 (último diff)
        assert señales['D'] == 0.1

        # D_filtrado debería ser la media móvil de los últimos 5 diffs
        # diffs = [+0.1, -0.1, +0.1, -0.1, +0.1] → media = 0.02
        assert señales['D_filtrado'] == 0.02

    def test_computar_señales_pid_vacia(self):
        """Test cuando no hay datapoints para la celda."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # No hay filas
        mock_cursor.fetchall.return_value = []

        señales = computar_señales_pid("ConservarxSalud", conn=mock_conn)

        # Todos los valores deberían ser 0
        assert señales['P'] == 0.0
        assert señales['I'] == 0.0
        assert señales['D'] == 0.0
        assert señales['n_total'] == 0
        assert señales['señal_control'] == 0.0

    def test_computar_señales_pid_config_ajustable(self):
        """Test que los parámetros PID son configurables."""
        # Guardar config original
        original_config = PID_CONFIG.copy()

        # Modificar config temporalmente
        PID_CONFIG['Kp'] = 2.0
        PID_CONFIG['Ki'] = 0.2
        PID_CONFIG['Kd'] = 0.1

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Datos ordenados: más reciente primero
        mock_cursor.fetchall.return_value = [
            (0.6, 0.4, 0.33),  # gap_pre, gap_post (más reciente)
            (0.7, 0.5, 0.28),
            (0.8, 0.6, 0.25),  # más antiguo
        ]

        señales = computar_señales_pid("ConservarxSalud", conn=mock_conn)

        # Verificar que usa los nuevos parámetros
        # P = 0.4 (último gap_post)
        # I = 0.4 + 0.5 + 0.6 = 1.5
        # D_raw = 0.4 - 0.6 = -0.2
        # D_filtrado = -0.2 (solo 1 punto en la ventana de filtro)
        # señal_control = 2.0*0.4 + 0.2*1.5 + 0.1*(-0.2) = 0.8 + 0.3 - 0.02 = 1.08
        assert abs(señales['señal_control'] - 1.08) < 0.01

        # Restaurar config original
        PID_CONFIG.update(original_config)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])