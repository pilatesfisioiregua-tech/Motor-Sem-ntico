"""Port-Miniport + Circuit Breaker + Cascade Routing.

Port-Miniport (Windows KMDF):
  Motor = port generico (cache, routing, retry, telemetria)
  Cada proveedor = miniport minimo (~50 lineas)

Circuit Breaker (Envoy):
  Cada proveedor tiene su propio breaker con estados CLOSED/OPEN/HALF_OPEN.
  Tras N errores → OPEN → cooldown → HALF_OPEN (1 probe) → CLOSED o OPEN.

Cascade Routing (ETH Zurich):
  Modelo barato primero → quality gate → escalar si necesario.
  40-85% ahorro sin perder calidad.
"""
from __future__ import annotations

import asyncio
import os
import random
import time
import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

log = structlog.get_logger()


# ============================================================
# MINIPORT: Interfaz minima de un proveedor LLM
# ============================================================

@dataclass
class RespuestaLLM:
    """Respuesta estandarizada de cualquier proveedor."""
    texto: str
    modelo: str
    tokens_input: int = 0
    tokens_output: int = 0
    coste_usd: float = 0.0
    latencia_ms: int = 0
    proveedor: str = ""


class Miniport(ABC):
    """Interfaz minima de un proveedor LLM (el 'driver').

    Cada proveedor implementa solo esto. El port (motor) se encarga
    de cache, retry, routing, telemetria, circuit breaking.
    """
    nombre: str = ""
    modelos_soportados: list[str] = []

    @abstractmethod
    async def enviar(self, modelo: str, system: str, user: str,
                     max_tokens: int = 4096, temperature: float = 0.1,
                     json_schema: dict = None, timeout: float = 90.0,
                     ) -> RespuestaLLM:
        """Envia prompt y devuelve respuesta."""
        ...

    def soporta(self, modelo: str) -> bool:
        """Verifica si este miniport soporta el modelo."""
        return any(modelo.startswith(p) for p in self.modelos_soportados)


class MiniportOpenRouter(Miniport):
    """Miniport para OpenRouter (acceso a 100+ modelos)."""
    nombre = "openrouter"
    modelos_soportados = ["deepseek/", "openai/", "anthropic/", "google/",
                          "meta-llama/", "mistralai/", "qwen/"]

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def enviar(self, modelo: str, system: str, user: str,
                     max_tokens: int = 4096, temperature: float = 0.1,
                     json_schema: dict = None, timeout: float = 90.0,
                     ) -> RespuestaLLM:
        import httpx

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada")

        body = {
            "model": modelo,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_schema:
            body["response_format"] = {"type": "json_schema", "json_schema": json_schema}

        t0 = time.time()
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "OMNI-MIND Motor",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("Sin choices en respuesta")

        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)

        return RespuestaLLM(
            texto=choices[0]["message"]["content"],
            modelo=modelo,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            coste_usd=_estimar_coste(modelo, tokens_in, tokens_out),
            latencia_ms=int((time.time() - t0) * 1000),
            proveedor=self.nombre,
        )


class MiniportLocal(Miniport):
    """Miniport para modelos locales (Ollama, vLLM, etc.)."""
    nombre = "local"
    modelos_soportados = ["local/"]

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def enviar(self, modelo: str, system: str, user: str,
                     max_tokens: int = 4096, temperature: float = 0.1,
                     json_schema: dict = None, timeout: float = 120.0,
                     ) -> RespuestaLLM:
        import httpx

        modelo_local = modelo.replace("local/", "")
        t0 = time.time()

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": modelo_local,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return RespuestaLLM(
            texto=data.get("message", {}).get("content", ""),
            modelo=modelo,
            tokens_input=data.get("prompt_eval_count", 0),
            tokens_output=data.get("eval_count", 0),
            coste_usd=0.0,  # Local es gratis
            latencia_ms=int((time.time() - t0) * 1000),
            proveedor=self.nombre,
        )


# ============================================================
# CIRCUIT BREAKER (Envoy pattern)
# ============================================================

class EstadoBreaker(str, Enum):
    CLOSED = "closed"       # Normal: trafico fluye
    OPEN = "open"           # Cortado: errores excesivos
    HALF_OPEN = "half_open" # Probando: 1 request de prueba


@dataclass
class CircuitBreaker:
    """Circuit Breaker por proveedor.

    CLOSED → (N errores) → OPEN → (cooldown) → HALF_OPEN → (1 ok) → CLOSED
                                                           → (1 error) → OPEN
    """
    nombre: str
    max_errores: int = 3
    cooldown_seg: float = 60.0
    estado: EstadoBreaker = EstadoBreaker.CLOSED
    errores_consecutivos: int = 0
    ultimo_error: float = 0.0  # timestamp
    total_exitos: int = 0
    total_fallos: int = 0

    def puede_pasar(self) -> bool:
        """Verifica si el circuito permite trafico."""
        if self.estado == EstadoBreaker.CLOSED:
            return True
        if self.estado == EstadoBreaker.OPEN:
            if time.time() - self.ultimo_error >= self.cooldown_seg:
                self.estado = EstadoBreaker.HALF_OPEN
                log.info("breaker.half_open", proveedor=self.nombre)
                return True
            return False
        if self.estado == EstadoBreaker.HALF_OPEN:
            return True  # Dejar pasar 1 probe
        return False

    def registrar_exito(self):
        """Registra un request exitoso."""
        self.total_exitos += 1
        if self.estado == EstadoBreaker.HALF_OPEN:
            self.estado = EstadoBreaker.CLOSED
            self.errores_consecutivos = 0
            log.info("breaker.cerrado", proveedor=self.nombre)
        else:
            self.errores_consecutivos = 0

    def registrar_error(self):
        """Registra un request fallido."""
        self.errores_consecutivos += 1
        self.total_fallos += 1
        self.ultimo_error = time.time()

        if self.estado == EstadoBreaker.HALF_OPEN:
            self.estado = EstadoBreaker.OPEN
            log.warning("breaker.reabrir", proveedor=self.nombre)
        elif self.errores_consecutivos >= self.max_errores:
            self.estado = EstadoBreaker.OPEN
            log.warning("breaker.abrir",
                        proveedor=self.nombre,
                        errores=self.errores_consecutivos)


# ============================================================
# CASCADE ROUTING (ETH Zurich)
# ============================================================

# Cadenas de cascade por complejidad
CADENA_CASCADE = {
    "baja": ["deepseek/deepseek-v3.2"],
    "media": ["deepseek/deepseek-v3.2", "openai/gpt-4o"],
    "alta": ["openai/gpt-4o", "anthropic/claude-opus-4"],
    "maxima": ["openai/gpt-4o", "anthropic/claude-opus-4"],
}

# Umbrales de quality gate por complejidad
UMBRAL_QUALITY_GATE = {
    "baja": 0.5,    # Casi todo pasa
    "media": 0.65,   # Necesita ser razonable
    "alta": 0.80,    # Necesita ser bueno
    "maxima": 0.90,  # Necesita ser excelente
}


def quality_gate(texto: str, funcion: str = "*",
                 umbral: float = 0.65) -> float:
    """Quality gate rapido ($0) — decide si escalar al modelo superior.

    Heuristicas rapidas (NO LLM):
      - Longitud minima (respuestas vacias/cortas fallan)
      - No placeholders genericos
      - Formato correcto si se pidio JSON
    """
    if not texto or len(texto.strip()) < 20:
        return 0.0

    score = 1.0

    # Penalizar respuestas genericas
    genericos = ["como asistente", "no puedo", "como modelo de lenguaje",
                 "es importante", "hay que tener en cuenta"]
    for g in genericos:
        if g.lower() in texto.lower():
            score -= 0.15

    # Penalizar respuestas demasiado cortas para complejidad alta
    if len(texto) < 100:
        score -= 0.2

    # Verificacion IC rapida
    from kernel.verificador import verificar
    v = verificar(texto, funcion=funcion)
    score = min(score, v.score)

    return max(0.0, score)


# ============================================================
# PORT: Motor de proveedores (el orquestador)
# ============================================================

class MotorProveedores:
    """Port generico que orquesta N miniports con circuit breaking + cascade.

    Es el 'driver framework' del OS: gestiona cache, routing, retry,
    circuit breaking, cascade, y telemetria. Los miniports solo envian.
    """

    def __init__(self):
        self.miniports: dict[str, Miniport] = {}
        self.breakers: dict[str, CircuitBreaker] = {}
        self._registrar_defaults()

    def _registrar_defaults(self):
        """Registra miniports por defecto."""
        self.registrar(MiniportOpenRouter())
        # MiniportLocal se registra solo si hay OLLAMA_URL
        if os.getenv("OLLAMA_URL"):
            self.registrar(MiniportLocal(os.getenv("OLLAMA_URL")))

    def registrar(self, miniport: Miniport):
        """Hot-plug: registra un nuevo miniport."""
        self.miniports[miniport.nombre] = miniport
        self.breakers[miniport.nombre] = CircuitBreaker(nombre=miniport.nombre)
        log.info("motor.miniport_registrado", nombre=miniport.nombre)

    def desregistrar(self, nombre: str):
        """Hot-unplug: desregistra un miniport."""
        self.miniports.pop(nombre, None)
        self.breakers.pop(nombre, None)
        log.info("motor.miniport_desregistrado", nombre=nombre)

    def _encontrar_miniport(self, modelo: str) -> Optional[tuple[str, Miniport]]:
        """Encuentra el miniport que soporta un modelo."""
        for nombre, mp in self.miniports.items():
            if mp.soporta(modelo):
                breaker = self.breakers[nombre]
                if breaker.puede_pasar():
                    return nombre, mp
        return None

    async def enviar(self, modelo: str, system: str, user: str,
                     max_tokens: int = 4096, temperature: float = 0.1,
                     json_schema: dict = None, timeout: float = 90.0,
                     ) -> RespuestaLLM:
        """Envia via miniport con circuit breaking + retry + jitter."""
        result = self._encontrar_miniport(modelo)
        if not result:
            raise ValueError(f"Sin miniport disponible para {modelo}")

        nombre, miniport = result
        breaker = self.breakers[nombre]

        for attempt in range(3):
            try:
                resp = await miniport.enviar(
                    modelo, system, user, max_tokens, temperature,
                    json_schema, timeout)
                breaker.registrar_exito()
                return resp
            except Exception as e:
                breaker.registrar_error()
                if attempt == 2 or not breaker.puede_pasar():
                    raise
                # Exponential backoff con jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                log.warning("motor.retry",
                            proveedor=nombre, modelo=modelo,
                            attempt=attempt, delay=round(delay, 1),
                            error=str(e)[:80])
                await asyncio.sleep(delay)

    async def enviar_cascade(self, cadena: list[str], system: str, user: str,
                              complejidad: str = "media",
                              funcion: str = "*",
                              **kwargs) -> RespuestaLLM:
        """Cascade routing: modelo barato → quality gate → escalar.

        Intenta cada modelo de la cadena. Si el quality gate aprueba
        la respuesta, la devuelve sin escalar al siguiente modelo.
        """
        umbral = UMBRAL_QUALITY_GATE.get(complejidad, 0.65)

        for i, modelo in enumerate(cadena):
            es_ultimo = (i == len(cadena) - 1)

            try:
                resp = await self.enviar(modelo, system, user, **kwargs)
            except Exception as e:
                log.warning("cascade.modelo_fallo",
                            modelo=modelo, error=str(e)[:80])
                continue  # Siguiente modelo en la cadena

            # Quality gate (solo si no es el ultimo modelo)
            if not es_ultimo:
                score = quality_gate(resp.texto, funcion=funcion, umbral=umbral)
                if score >= umbral:
                    log.info("cascade.aceptado",
                             modelo=modelo, score=round(score, 2),
                             posicion=i + 1, total=len(cadena))
                    return resp
                else:
                    log.info("cascade.escalar",
                             modelo=modelo, score=round(score, 2),
                             umbral=umbral, siguiente=cadena[i + 1])
                    continue  # No paso el gate, escalar
            else:
                return resp  # Ultimo modelo, devolver sin importar score

        raise ValueError("Cascade: todos los modelos fallaron")

    @property
    def estado_breakers(self) -> dict[str, str]:
        return {n: b.estado.value for n, b in self.breakers.items()}


# Instancia global (singleton lazy)
_motor_proveedores: Optional[MotorProveedores] = None


def get_motor_proveedores() -> MotorProveedores:
    global _motor_proveedores
    if _motor_proveedores is None:
        _motor_proveedores = MotorProveedores()
    return _motor_proveedores


# ============================================================
# COSTES (compartido)
# ============================================================

def _estimar_coste(modelo: str, tokens_in: int, tokens_out: int) -> float:
    rates = {
        "deepseek/deepseek-v3.2": (0.0003, 0.0008),
        "openai/gpt-4o": (0.0025, 0.01),
        "openai/gpt-4o-mini": (0.00015, 0.0006),
        "anthropic/claude-haiku-4-5": (0.0008, 0.004),
        "anthropic/claude-sonnet-4-6": (0.003, 0.015),
        "anthropic/claude-opus-4": (0.015, 0.075),
        "google/gemini-2.5-pro": (0.00125, 0.01),
    }
    in_rate, out_rate = rates.get(modelo, (0.003, 0.015))
    return (tokens_in * in_rate + tokens_out * out_rate) / 1000
