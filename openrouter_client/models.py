import os

import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def list_models(api_key: str | None = None, base_url: str = DEFAULT_BASE_URL) -> list[dict]:
    api_key = api_key or os.environ["OPENROUTER_API_KEY"]
    response = httpx.get(
        f"{base_url}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"]


def list_free_models(api_key: str | None = None, base_url: str = DEFAULT_BASE_URL) -> list[dict]:
    models = list_models(api_key, base_url)
    return [m for m in models if m["id"].endswith(":free")]
