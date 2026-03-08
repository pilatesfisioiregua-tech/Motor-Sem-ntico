"""Cliente Anthropic con rotación de API keys y retry."""
import asyncio
import itertools
import structlog
from anthropic import AsyncAnthropic
from src.config.settings import ANTHROPIC_API_KEYS

log = structlog.get_logger()

class LLMClient:
    """Wrapper Anthropic con rotación de keys y backoff."""

    def __init__(self):
        if not ANTHROPIC_API_KEYS:
            raise ValueError("No ANTHROPIC_API_KEY_* configuradas")
        self._key_cycle = itertools.cycle(ANTHROPIC_API_KEYS)
        self._clients: dict[str, AsyncAnthropic] = {
            key: AsyncAnthropic(api_key=key) for key in ANTHROPIC_API_KEYS
        }
        self._total_cost: float = 0.0

    def _next_client(self) -> AsyncAnthropic:
        key = next(self._key_cycle)
        return self._clients[key]

    async def complete(
        self,
        model: str,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        retries: int = 3,
    ) -> str:
        """Envía mensaje y devuelve texto. Rota key en cada retry."""
        last_error = None
        for attempt in range(retries):
            client = self._next_client()
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": user_message}],
                )
                # Track cost (approximate)
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                self._total_cost += cost
                log.info("llm_complete", model=model, input_tokens=input_tokens,
                         output_tokens=output_tokens, cost=cost, attempt=attempt)
                return response.content[0].text
            except Exception as e:
                last_error = e
                log.warning("llm_retry", model=model, attempt=attempt, error=str(e))
                await asyncio.sleep(2 ** attempt)
        raise last_error

    @staticmethod
    def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimación de coste por modelo (USD)."""
        rates = {
            "claude-sonnet-4-20250514": (0.003, 0.015),
            "claude-haiku-4-5-20251001": (0.001, 0.005),
            "claude-opus-4-20250514": (0.015, 0.075),
        }
        input_rate, output_rate = rates.get(model, (0.003, 0.015))
        return (input_tokens * input_rate + output_tokens * output_rate) / 1000

    @property
    def total_cost(self) -> float:
        return self._total_cost

    def reset_cost(self):
        self._total_cost = 0.0


# Singleton (lazy — no falla al importar sin keys)
class _LazyLLM:
    """Proxy que instancia LLMClient solo al primer uso."""
    _instance: LLMClient | None = None

    def _get(self) -> LLMClient:
        if self._instance is None:
            self._instance = LLMClient()
        return self._instance

    def __getattr__(self, name: str):
        return getattr(self._get(), name)


llm = _LazyLLM()
