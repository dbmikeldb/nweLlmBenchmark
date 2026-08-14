import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bootcheck.grading import grade
from requesty_client import RequestyClient

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "runs"


def load_task(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def run(task_path: Path, model: str) -> None:
    task = load_task(task_path)
    prompt = task["llm_input"]["prompt"]

    client = RequestyClient()
    result = client.chat(model=model, messages=[{"role": "user", "content": prompt}])

    grading = grade(result.content, task)

    record = {
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

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_file = RESULTS_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    with run_file.open("a") as f:
        f.write(json.dumps(record) + "\n")

    status = "PASS" if grading["pass"] else "FAIL"
    print(f"[{status}] {task['id']} | {model}")
    for key, value in grading.items():
        if key == "pass":
            continue
        print(f"  {key}: {value}")
    print(f"Cost: ${result.cost_usd}  Latency: {result.latency_ms:.0f} ms")
    print(f"Log: {run_file}")
    print("\n--- response ---")
    print(result.content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single bootcheck task against a single model.")
    parser.add_argument("--task", required=True, type=Path, help="Path to task YAML fixture")
    parser.add_argument("--model", required=True, help="Requesty model id, e.g. google/gemma-4-31b-it")
    args = parser.parse_args()

    run(args.task, args.model)


if __name__ == "__main__":
    main()
