import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bootcheck.grading import grade
from requesty_client import RequestyClient, list_free_models

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "runs"


def load_task(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def call_model(client: RequestyClient, task: dict, model: str) -> dict:
    prompt = task["llm_input"]["prompt"]

    try:
        result = client.chat(model=model, messages=[{"role": "user", "content": prompt}])
    except Exception as exc:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task["id"],
            "vendor": task["vendor"],
            "os_train": task["os_train"],
            "tier": task["tier"],
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
        "model": model,
        "response": result.content,
        "grading": grading,
        "cost_usd": result.cost_usd,
        "latency_ms": result.latency_ms,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
    }


def run(task_path: Path, models: list[str]) -> None:
    task = load_task(task_path)
    client = RequestyClient()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_file = RESULTS_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.jsonl"

    records = []
    for model in models:
        record = call_model(client, task, model)
        records.append(record)

        with run_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        if "error" in record:
            print(f"[ERROR] {model}: {record['error']}")
            continue

        status = "PASS" if record["grading"]["pass"] else "FAIL"
        print(f"[{status}] {model}  cost=${record['cost_usd']}  latency={record['latency_ms']:.0f}ms")

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
        help="Requesty model id, e.g. google/gemma-4-31b-it, or 'all_free' to sweep every free-tier model",
    )
    args = parser.parse_args()

    if args.model == "all_free":
        models = [m["id"] for m in list_free_models()]
        print(f"Sweeping {len(models)} free models...")
    else:
        models = [args.model]

    run(args.task, models)


if __name__ == "__main__":
    main()
