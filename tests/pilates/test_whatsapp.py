"""Tests whatsapp.py — clasificación de intención."""
from src.pilates.whatsapp import _clasificar_intencion


class TestClasificarIntencion:
    def test_precio(self):
        assert _clasificar_intencion("cuanto cuesta una clase?", "34666", None) == "consulta_precio"

    def test_horario(self):
        assert _clasificar_intencion("que horarios teneis?", "34666", None) == "consulta_horario"

    def test_reserva(self):
        assert _clasificar_intencion("quiero reservar clase", "34666", None) == "reserva"

    def test_cancelacion(self):
        assert _clasificar_intencion("no puedo, cancelo la clase", "34666", None) == "cancelacion"

    def test_queja(self):
        assert _clasificar_intencion("tengo un problema con el cobro", "34666", None) == "queja"

    def test_feedback(self):
        assert _clasificar_intencion("genial la clase de hoy!", "34666", None) == "feedback"

    def test_otro(self):
        assert _clasificar_intencion("hola que tal", "34666", None) == "otro"

    def test_boton_confirmar(self):
        assert _clasificar_intencion("si_voy", "34666", None) == "reserva"
