"""Test que el router aplica las 14 reglas."""
import pytest
from src.config.reglas import verificar_reglas, reglas_que_fallan


class TestReglasEnRouter:
    def test_seleccion_sin_cuantitativa_falla_r1(self):
        ints = ["INT-08", "INT-12", "INT-16"]
        fallos = reglas_que_fallan(ints, "analisis")
        reglas_fallidas = [f.regla for f in fallos]
        assert 1 in reglas_fallidas

    def test_seleccion_completa_pasa(self):
        ints = ["INT-01", "INT-08", "INT-07", "INT-14", "INT-16"]
        fallos = reglas_que_fallan(ints, "analisis")
        # Puede haber advertencias (no fallos duros) pero R1 debe pasar
        r1_fallos = [f for f in fallos if f.regla == 1]
        assert len(r1_fallos) == 0

    def test_cluster_redundante_falla_r5(self):
        ints = ["INT-01", "INT-03", "INT-04", "INT-08", "INT-16"]  # INT-03 + INT-04 = sistémicas
        fallos = reglas_que_fallan(ints, "analisis")
        reglas_fallidas = [f.regla for f in fallos]
        assert 5 in reglas_fallidas

    def test_int16_no_ultima_falla_r13(self):
        ints = ["INT-01", "INT-16", "INT-08", "INT-07"]  # INT-16 no es última
        fallos = reglas_que_fallan(ints, "analisis")
        reglas_fallidas = [f.regla for f in fallos]
        assert 13 in reglas_fallidas

    def test_frenar_detecta_f7_alta_sin_f5(self):
        vector = {"F1": 0.30, "F2": 0.65, "F3": 0.30, "F4": 0.45, "F5": 0.25, "F6": 0.45, "F7": 0.75}
        fallos = reglas_que_fallan(["INT-01", "INT-08", "INT-16"], "analisis", vector)
        r14_fallos = [f for f in fallos if f.regla == 14]
        assert len(r14_fallos) > 0
        assert "F7" in r14_fallos[0].mensaje

    def test_confrontacion_sin_existenciales_falla_r7(self):
        ints = ["INT-01", "INT-08", "INT-07", "INT-16"]
        fallos = reglas_que_fallan(ints, "confrontacion")
        reglas_fallidas = [f.regla for f in fallos]
        assert 7 in reglas_fallidas
