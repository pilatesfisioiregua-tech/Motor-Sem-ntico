"""Capa A — Enriquecimiento de contexto via Perplexity Search.

Se ejecuta ANTES del Motor. Inyecta datos de entorno/mercado
relevantes para F5 (Identidad/Frontera) y F6 (Adaptación).

NO es un LLM — es una API de búsqueda que retorna resultados web estructurados.
Coste estimado: ~$1/mes por negocio.
"""

import os
import time
import httpx
import re
from datetime import datetime


# Precios Perplexity sonar ($/1M tokens) — ref: perplexity.ai/pricing marzo 2026
PERPLEXITY_PRECIO = {'input': 1.00, 'output': 1.00}

# Acumulador en memoria para estado rápido
_estado = {
    'busquedas': [],
    'coste_acumulado_usd': 0.0,
}


def _detectar_dominio(consumidor: str) -> str:
    """Extrae dominio de negocio del consumidor.

    Ej: 'exocortex:pilates' → 'pilates studio'
        'exocortex:restaurante_mexicano' → 'mexican restaurant'
        'motor_vn' → ''
    """
    if ':' not in consumidor:
        return ''
    _, dominio_raw = consumidor.split(':', 1)
    # snake_case → espacios, quitar prefijos técnicos
    dominio = dominio_raw.replace('_', ' ').strip()
    return dominio


class CapaA:
    """Capa A — Enriquecimiento de contexto via Perplexity Search."""

    def __init__(self):
        self.api_key = os.environ.get('PERPLEXITY_API_KEY', '')
        self.base_url = 'https://api.perplexity.ai/chat/completions'
        self.model = 'sonar'  # modelo de búsqueda, no chat

    async def enriquecer(self, input_texto: str, consumidor: str) -> dict:
        """Busca contexto de entorno/mercado relevante.

        Returns:
            {
                'contexto_f5': str,  # identidad/frontera del negocio en su mercado
                'contexto_f6': str,  # señales de adaptación/cambio en el entorno
                'fuentes': list,     # URLs de donde viene la info
                'coste_usd': float,
                'skip_reason': str,  # si se saltó, por qué
            }
        """
        resultado = {
            'contexto_f5': '',
            'contexto_f6': '',
            'fuentes': [],
            'coste_usd': 0.0,
            'skip_reason': '',
        }

        # Gate 1: API key
        if not self.api_key:
            resultado['skip_reason'] = 'no_api_key'
            return resultado

        # Gate 2: dominio detectable
        dominio = _detectar_dominio(consumidor)
        if not dominio:
            resultado['skip_reason'] = 'no_domain_in_consumer'
            return resultado

        año = datetime.now().year

        # 2 queries: F5 (identidad/frontera) y F6 (adaptación)
        queries = {
            'f5': f"{dominio} competitive landscape market position {año}",
            'f6': f"{dominio} industry trends changes {año}",
        }

        coste_total = 0.0
        fuentes_all = []

        for key, query in queries.items():
            try:
                texto, fuentes, coste = await self._buscar(query)
                resultado[f'contexto_{key}'] = texto
                fuentes_all.extend(fuentes)
                coste_total += coste
            except Exception as e:
                print(f"[WARN:capa_a] Perplexity {key} falló: {e}")
                # Motor continúa sin este contexto

        resultado['fuentes'] = list(dict.fromkeys(fuentes_all))  # dedup preservando orden
        resultado['coste_usd'] = round(coste_total, 6)

        # Registrar coste en sistema existente
        if coste_total > 0:
            self._registrar_coste(coste_total, consumidor)

        # Actualizar estado en memoria
        _estado['coste_acumulado_usd'] += coste_total
        _estado['busquedas'].append({
            'consumidor': consumidor,
            'dominio': dominio,
            'coste_usd': coste_total,
            'timestamp': datetime.now().isoformat(),
        })
        # Mantener solo últimas 50 búsquedas en memoria
        if len(_estado['busquedas']) > 50:
            _estado['busquedas'] = _estado['busquedas'][-50:]

        return resultado

    async def _buscar(self, query: str) -> tuple:
        """Ejecuta una búsqueda en Perplexity Search API.

        Returns:
            (texto: str, fuentes: list[str], coste_usd: float)
        """
        t0 = time.time()

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.base_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'Return factual search results only. No analysis or opinions. Be concise.',
                        },
                        {
                            'role': 'user',
                            'content': query,
                        },
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()

        # Extraer texto
        texto = ''
        if data.get('choices'):
            texto = data['choices'][0].get('message', {}).get('content', '')

        # Extraer fuentes (Perplexity retorna citations en el response)
        fuentes = data.get('citations', [])

        # Calcular coste
        usage = data.get('usage', {})
        tokens_in = usage.get('prompt_tokens', 0)
        tokens_out = usage.get('completion_tokens', 0)
        coste = (tokens_in / 1_000_000) * PERPLEXITY_PRECIO['input'] + \
                (tokens_out / 1_000_000) * PERPLEXITY_PRECIO['output']

        latencia_ms = int((time.time() - t0) * 1000)

        return texto, fuentes, coste

    def _registrar_coste(self, coste_usd: float, consumidor: str):
        """Registra coste Perplexity en el sistema de costes existente."""
        try:
            from .costes import registrar_coste
            # Perplexity no reporta tokens exactos en todos los casos,
            # estimamos ~500 tokens por búsqueda como proxy
            registrar_coste(
                modelo='perplexity/sonar',
                tokens_input=500,
                tokens_output=500,
                componente='capa_a',
                consumidor=consumidor,
                operacion='busqueda_entorno',
                provider='perplexity',
            )
        except Exception as e:
            print(f"[WARN:capa_a] No se pudo registrar coste: {e}")

    async def buscar_manual(self, query: str, consumidor: str) -> dict:
        """Búsqueda manual ad-hoc (para endpoint API)."""
        if not self.api_key:
            return {'error': 'no_api_key', 'contexto': '', 'fuentes': []}

        try:
            texto, fuentes, coste = await self._buscar(query)
            if coste > 0:
                self._registrar_coste(coste, consumidor)
                _estado['coste_acumulado_usd'] += coste

            return {
                'contexto': texto,
                'fuentes': fuentes,
                'coste_usd': round(coste, 6),
            }
        except Exception as e:
            return {'error': str(e), 'contexto': '', 'fuentes': []}


def get_estado() -> dict:
    """Retorna estado de Capa A para endpoint /capa-a/estado."""
    return {
        'api_key_configurada': bool(os.environ.get('PERPLEXITY_API_KEY', '')),
        'ultimas_busquedas': _estado['busquedas'][-10:],
        'coste_acumulado_usd': round(_estado['coste_acumulado_usd'], 6),
        'total_busquedas': len(_estado['busquedas']),
    }
