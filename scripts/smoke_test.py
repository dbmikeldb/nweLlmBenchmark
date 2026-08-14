import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from requesty_client import RequestyClient, list_free_models


def main() -> None:
    free_models = list_free_models()
    if not free_models:
        print("No free models found.")
        return

    model_id = free_models[0]["id"]
    print(f"{len(free_models)} free models available. Using: {model_id}")

    client = RequestyClient()
    result = client.chat(
        model=model_id,
        messages=[{"role": "user", "content": "Say hello in one short sentence."}],
    )

    print(f"Response: {result.content}")
    print(f"Tokens: {result.prompt_tokens}+{result.completion_tokens}={result.total_tokens}")
    print(f"Cost: ${result.cost_usd}")
    print(f"Latency: {result.latency_ms:.0f} ms")


if __name__ == "__main__":
    main()
