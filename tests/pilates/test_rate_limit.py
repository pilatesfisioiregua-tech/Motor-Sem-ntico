"""Tests rate_limit.py — semáforos y httpx singleton."""
import pytest
from src.pilates.rate_limit import semaforo_opus, semaforo_motor, get_http_client


class TestSemaforos:
    def test_opus_es_1(self):
        assert semaforo_opus._value == 1

    def test_motor_es_2(self):
        assert semaforo_motor._value == 2


class TestHttpClient:
    def test_singleton(self):
        c1 = get_http_client()
        c2 = get_http_client()
        assert c1 is c2

    def test_tiene_timeout(self):
        c = get_http_client()
        assert c.timeout.connect == 10.0
