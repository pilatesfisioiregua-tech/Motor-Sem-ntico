"""Pruebas de integración para gestor.py → registrador.py (SN-06)."""

import pytest
from unittest.mock import MagicMock, patch
from agent.core.gestor import registrar_efectividad


class TestIntegracionGestorRegistrador:
    """Pruebas de integración entre gestor y registrador."""

    @patch('agent.core.registrador.registrar_ejecucion')
    def test_registrar_efectividad_delega_correctamente(self, mock_registrar_ejecucion):
        """Test que registrar_efectividad delega a registrar_ejecucion con los argumentos correctos."""
        # Configurar el mock para que devuelva un dict de señales
        mock_registrar_ejecucion.return_value = {
            'P': 0.5, 'I': 2.0, 'D': -0.1, 'señal_control': 0.45
        }

        # Llamar a registrar_efectividad
        resultado = registrar_efectividad(
            pregunta_id='INT-01-001',
            modelo='deepseek/deepseek-chat-v3-0324',
            caso_id='caso_test_001',
            consumidor='motor_vn',
            celda_objetivo='ConservarxSalud',
            gap_pre=0.8,
            gap_post=0.4,
            operacion='individual'
        )

        # Verificar que se llamó a registrar_ejecucion con el dict correcto
        mock_registrar_ejecucion.assert_called_once()
        args, kwargs = mock_registrar_ejecucion.call_args

        # El primer argumento debe ser un dict con los campos esperados
        datos = args[0]
        assert datos['pregunta_id'] == 'INT-01-001'
        assert datos['modelo'] == 'deepseek/deepseek-chat-v3-0324'
        assert datos['caso_id'] == 'caso_test_001'
        assert datos['consumidor'] == 'motor_vn'
        assert datos['celda_objetivo'] == 'ConservarxSalud'
        assert datos['gap_pre'] == 0.8
        assert datos['gap_post'] == 0.4
        assert datos['operacion'] == 'individual'

        # Verificar que el resultado es el que devolvió el mock
        assert resultado == {'P': 0.5, 'I': 2.0, 'D': -0.1, 'señal_control': 0.45}

    @patch('agent.core.registrador.registrar_ejecucion')
    def test_registrar_efectividad_conn_opcional(self, mock_registrar_ejecucion):
        """Test que registrar_efectividad pasa el parámetro conn correctamente."""
        mock_registrar_ejecucion.return_value = {'P': 0.0, 'I': 0.0, 'D': 0.0}

        mock_conn = MagicMock()

        registrar_efectividad(
            pregunta_id='INT-01-002',
            modelo='gpt-4',
            caso_id='caso_test_002',
            consumidor='motor_vn',
            celda_objetivo='CaptarxSentido',
            gap_pre=0.5,
            gap_post=0.3,
            conn=mock_conn
        )

        # Verificar que se pasó el conn a registrar_ejecucion
        args, kwargs = mock_registrar_ejecucion.call_args
        assert kwargs.get('conn') is mock_conn


if __name__ == '__main__':
    pytest.main([__file__, '-v'])