"""Production Monitoring — SLOs, costes, alertas.

Patron Circuit Breaker (#60685): degradacion graceful cuando modelos fallan.
Patron SLO Tracking (#60686): seguimiento de objetivos de servicio.
Patron Budget Enforcement (#60687): control de costes.

SLOs del Motor:
  - Latencia Fase A: < 250ms (p95)
  - Latencia Fase B: < 120s (p95)
  - Coste por ejecucion: < $1.50
  - Error rate: < 5%
"""

import time
import json
from datetime import datetime, timezone
from collections import defaultdict


# SLO definitions
SLOS = {
    'latencia_fase_a_ms': {'objetivo': 250, 'tipo': 'max', 'percentil': 95},
    'latencia_total_s': {'objetivo': 120, 'tipo': 'max', 'percentil': 95},
    'coste_por_ejecucion_usd': {'objetivo': 1.50, 'tipo': 'max', 'percentil': 95},
    'error_rate_pct': {'objetivo': 5.0, 'tipo': 'max', 'percentil': None},
}


class Monitor:
    """Production monitoring con SLO tracking y cost enforcement."""

    def __init__(self):
        self.ejecuciones_recientes = []  # ultimas 100
        self.coste_acumulado_24h = 0.0
        self.presupuesto_diario = 50.0  # USD

    def registrar_ejecucion(self, resultado: dict):
        """Registrar metricas de una ejecucion."""
        entry = {
            'timestamp': time.time(),
            'latencia_s': resultado.get('latencia_total_s', 0),
            'coste_usd': resultado.get('coste_total_usd', 0),
            'error': resultado.get('error'),
            'modo': resultado.get('modo', 'unknown'),
            'tier': resultado.get('tier', 0),
            'n_inteligencias': resultado.get('n_inteligencias', 0),
        }
        self.ejecuciones_recientes.append(entry)
        if len(self.ejecuciones_recientes) > 100:
            self.ejecuciones_recientes = self.ejecuciones_recientes[-100:]

        self.coste_acumulado_24h += entry['coste_usd']

    def check_slos(self, conn=None) -> dict:
        """Verificar todos los SLOs contra datos recientes."""
        if not self.ejecuciones_recientes:
            return {'status': 'sin_datos', 'slos': {}}

        results = {}
        ejecuciones = self.ejecuciones_recientes

        # Latencia total
        latencias = sorted([e['latencia_s'] for e in ejecuciones if e['latencia_s'] > 0])
        if latencias:
            p95_idx = int(len(latencias) * 0.95)
            p95 = latencias[min(p95_idx, len(latencias) - 1)]
            results['latencia_total_s'] = {
                'p95': round(p95, 2),
                'objetivo': SLOS['latencia_total_s']['objetivo'],
                'cumple': p95 <= SLOS['latencia_total_s']['objetivo'],
            }

        # Coste
        costes = sorted([e['coste_usd'] for e in ejecuciones if e['coste_usd'] > 0])
        if costes:
            p95_idx = int(len(costes) * 0.95)
            p95 = costes[min(p95_idx, len(costes) - 1)]
            results['coste_por_ejecucion_usd'] = {
                'p95': round(p95, 4),
                'objetivo': SLOS['coste_por_ejecucion_usd']['objetivo'],
                'cumple': p95 <= SLOS['coste_por_ejecucion_usd']['objetivo'],
            }

        # Error rate
        total = len(ejecuciones)
        errores = sum(1 for e in ejecuciones if e.get('error'))
        error_rate = (errores / total * 100) if total > 0 else 0
        results['error_rate_pct'] = {
            'actual': round(error_rate, 2),
            'objetivo': SLOS['error_rate_pct']['objetivo'],
            'cumple': error_rate <= SLOS['error_rate_pct']['objetivo'],
        }

        all_ok = all(r.get('cumple', True) for r in results.values())
        return {'status': 'ok' if all_ok else 'alerta', 'slos': results}

    def check_budget(self) -> dict:
        """Verificar presupuesto gastado vs limite."""
        return {
            'coste_acumulado_24h': round(self.coste_acumulado_24h, 4),
            'presupuesto_diario': self.presupuesto_diario,
            'porcentaje_usado': round(self.coste_acumulado_24h / self.presupuesto_diario * 100, 2) if self.presupuesto_diario > 0 else 0,
            'dentro_presupuesto': self.coste_acumulado_24h <= self.presupuesto_diario,
        }

    def get_dashboard(self, conn=None) -> dict:
        """Dashboard con metricas agregadas."""
        ejecuciones = self.ejecuciones_recientes

        por_modo = defaultdict(list)
        for e in ejecuciones:
            por_modo[e['modo']].append(e)

        resumen_modos = {}
        for modo, execs in por_modo.items():
            resumen_modos[modo] = {
                'n': len(execs),
                'latencia_media_s': round(sum(e['latencia_s'] for e in execs) / len(execs), 2) if execs else 0,
                'coste_medio_usd': round(sum(e['coste_usd'] for e in execs) / len(execs), 4) if execs else 0,
                'errores': sum(1 for e in execs if e.get('error')),
            }

        return {
            'ejecuciones_totales': len(ejecuciones),
            'por_modo': resumen_modos,
            'slos': self.check_slos(),
            'budget': self.check_budget(),
        }


class CircuitBreaker:
    """Circuit Breaker para proteger contra modelos caidos.

    Estados: CLOSED (normal) -> OPEN (fallback) -> HALF_OPEN (probando)
    """

    def __init__(self, umbral_fallos: int = 5, timeout_s: int = 60):
        self.umbral_fallos = umbral_fallos
        self.timeout_s = timeout_s
        self.estados = {}  # modelo -> {'estado', 'fallos', 'ultimo_fallo'}

    def _get_estado(self, modelo: str) -> dict:
        if modelo not in self.estados:
            self.estados[modelo] = {
                'estado': 'CLOSED',
                'fallos': 0,
                'ultimo_fallo': 0,
            }
        return self.estados[modelo]

    def puede_llamar(self, modelo: str) -> bool:
        """Verificar si se puede llamar al modelo."""
        estado = self._get_estado(modelo)

        if estado['estado'] == 'CLOSED':
            return True
        elif estado['estado'] == 'OPEN':
            # Check timeout para pasar a HALF_OPEN
            if time.time() - estado['ultimo_fallo'] > self.timeout_s:
                estado['estado'] = 'HALF_OPEN'
                return True
            return False
        elif estado['estado'] == 'HALF_OPEN':
            return True
        return True

    def registrar_exito(self, modelo: str):
        """Registrar llamada exitosa."""
        estado = self._get_estado(modelo)
        estado['fallos'] = 0
        estado['estado'] = 'CLOSED'

    def registrar_fallo(self, modelo: str):
        """Registrar llamada fallida."""
        estado = self._get_estado(modelo)
        estado['fallos'] += 1
        estado['ultimo_fallo'] = time.time()

        if estado['fallos'] >= self.umbral_fallos:
            estado['estado'] = 'OPEN'

    def get_estados(self) -> dict:
        """Estado de todos los circuit breakers."""
        return {
            modelo: {
                'estado': info['estado'],
                'fallos_consecutivos': info['fallos'],
                'ultimo_fallo': datetime.fromtimestamp(
                    info['ultimo_fallo'], tz=timezone.utc
                ).isoformat() if info['ultimo_fallo'] else None,
            }
            for modelo, info in self.estados.items()
        }

    def get_modelo_fallback(self, modelo: str) -> str:
        """Obtener modelo fallback si el principal esta abierto."""
        fallbacks = {
            'deepseek/deepseek-chat-v3-0324': 'deepseek/deepseek-chat',
            'deepseek/deepseek-chat': 'xiaomi/mimo-v2-flash',
            'deepseek/deepseek-reasoner': 'deepseek/deepseek-chat-v3-0324',
            'deepcogito/cogito-v2.1-671b': 'deepseek/deepseek-chat-v3-0324',
            'openai/gpt-4o-mini': 'deepseek/deepseek-chat',
        }
        return fallbacks.get(modelo, 'deepseek/deepseek-chat')


# Singletons
_monitor = None
_breaker = None

def get_monitor() -> Monitor:
    global _monitor
    if _monitor is None:
        _monitor = Monitor()
    return _monitor

def get_circuit_breaker() -> CircuitBreaker:
    global _breaker
    if _breaker is None:
        _breaker = CircuitBreaker()
    return _breaker
