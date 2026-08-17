import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bootcheck.grading import grade
from openrouter_client import OpenRouterClient
from openrouter_client import list_free_models as list_free_openrouter
from requesty_client import RequestyClient
from requesty_client import list_free_models as list_free_requesty

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "runs"

PROVIDERS = {
    "requesty": (RequestyClient, list_free_requesty),
    "openrouter": (OpenRouterClient, list_free_openrouter),
}


def load_task(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


async def acall_model(client: RequestyClient | OpenRouterClient, task: dict, model: str, provider: str) -> dict:
    prompt = task["llm_input"]["prompt"]

    try:
        result = await client.achat(model=model, messages=[{"role": "user", "content": prompt}])
    except Exception as exc:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task["id"],
            "vendor": task["vendor"],
            "os_train": task["os_train"],
            "tier": task["tier"],
            "provider": provider,
            "model": model,
            "error": str(exc),
        }

    grading = grade(result.content, task)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task["id"],
        "vendor": task["vendor"],
        "os_train": task["os_train"],
        "tier": task["tier"],
        "provider": provider,
        "model": model,
        "response": result.content,
        "grading": grading,
        "cost_usd": result.cost_usd,
        "latency_ms": result.latency_ms,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
    }


async def run(task_path: Path, models: list[str], provider: str = "requesty", concurrency: int = 5) -> None:
    task = load_task(task_path)
    client_cls, _ = PROVIDERS[provider]
    client = client_cls()

    task_results_dir = RESULTS_DIR / task["id"]
    task_results_dir.mkdir(parents=True, exist_ok=True)
    run_file = task_results_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.jsonl"

    semaphore = asyncio.Semaphore(concurrency)

    async def bound_call(model: str) -> dict:
        async with semaphore:
            return await acall_model(client, task, model, provider)

    records = []
    for coro in asyncio.as_completed([bound_call(model) for model in models]):
        record = await coro
        records.append(record)

        with run_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        if "error" in record:
            print(f"[ERROR] {record['model']}: {record['error']}")
            continue

        status = "PASS" if record["grading"]["pass"] else "FAIL"
        print(f"[{status}] {record['model']}  cost=${record['cost_usd']}  latency={record['latency_ms']:.0f}ms")

    if len(models) == 1 and "response" in records[0]:
        print("\n--- response ---")
        print(records[0]["response"])
        return

    passed = sum(1 for r in records if r.get("grading", {}).get("pass"))
    errored = sum(1 for r in records if "error" in r)
    total_cost = sum(r.get("cost_usd", 0.0) for r in records)
    print(f"\n{passed}/{len(models)} passed, {errored} errored, total cost ${total_cost:.4f}")
    print(f"Log: {run_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bootcheck task against one or all free-tier models.")
    parser.add_argument("--task", required=True, type=Path, help="Path to task YAML fixture")
    parser.add_argument(
        "--model",
        required=True,
        help="Provider model id, e.g. google/gemma-4-31b-it, or 'all_free' to sweep every free-tier model",
    )
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDERS),
        default="requesty",
        help="Which gateway to route calls through (default: requesty)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Max concurrent model calls in flight (default: 5)",
    )
    args = parser.parse_args()

    _, list_free_fn = PROVIDERS[args.provider]

    if args.model == "all_free":
        models = [m["id"] for m in list_free_fn()]
        print(f"Sweeping {len(models)} free models on {args.provider}...")
    else:
        models = [args.model]

    asyncio.run(run(args.task, models, provider=args.provider, concurrency=args.concurrency))


if __name__ == "__main__":
    main()
