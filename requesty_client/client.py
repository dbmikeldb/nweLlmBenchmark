import os
import time
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_BASE_URL = "https://router.requesty.ai/v1"


@dataclass
class CallResult:
    model: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    raw: Any


class RequestyClient:
    def __init__(self, api_key: str | None = None, base_url: str = DEFAULT_BASE_URL):
        api_key = api_key or os.environ["REQUESTY_API_KEY"]
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, model: str, messages: list[dict], **kwargs) -> CallResult:
        start = time.perf_counter()
        parsed = self._client.chat.completions.create(model=model, messages=messages, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        usage = parsed.usage

        cost = getattr(usage, "cost", None)
        if cost is None:
            extra = getattr(usage, "model_extra", None) or {}
            cost = extra.get("cost", 0.0)

        return CallResult(
            model=parsed.model,
            content=parsed.choices[0].message.content,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost_usd=float(cost),
            latency_ms=elapsed_ms,
            raw=parsed,
        )
