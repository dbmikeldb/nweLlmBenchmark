import glob
import json
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "bootcheck" / "tasks"
RUNS_DIR = ROOT / "results" / "runs"


def load_tasks() -> dict[str, dict]:
    tasks = {}
    for path in sorted(TASKS_DIR.glob("*.yaml")):
        t = yaml.safe_load(path.read_text())
        tasks[t["id"]] = {
            "vendor": t["vendor"],
            "os_train": t["os_train"],
            "category": t["category"],
            "title": t["title"],
        }
    return tasks


def load_runs(date: str | None = None) -> list[dict]:
    runs = []
    for path in glob.glob(str(RUNS_DIR / "**" / "*.jsonl"), recursive=True):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if "error" in record:
                    continue
                if date is not None and record["timestamp"][:10] != date:
                    continue
                runs.append(record)
    return runs


def list_available_dates() -> list[str]:
    return sorted({run["timestamp"][:10] for run in load_runs()})


def list_runs(date: str | None = None) -> list[dict]:
    tasks = load_tasks()
    runs = []
    for path in glob.glob(str(RUNS_DIR / "**" / "*.jsonl"), recursive=True):
        p = Path(path)
        task_id = p.parent.name
        run_timestamp = p.stem
        run_date = datetime.strptime(run_timestamp, "%Y%m%dT%H%M%SZ").strftime("%Y-%m-%d")
        if date is not None and run_date != date:
            continue

        models = 0
        errors = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                models += 1
                if "error" in json.loads(line):
                    errors += 1

        task = tasks.get(task_id, {})
        runs.append({
            "run_id": f"{task_id}/{run_timestamp}",
            "task_id": task_id,
            "title": task.get("title", task_id),
            "vendor": task.get("vendor"),
            "os_train": task.get("os_train"),
            "timestamp": run_timestamp,
            "date": run_date,
            "models": models,
            "errors": errors,
        })

    runs.sort(key=lambda r: r["timestamp"], reverse=True)
    return runs


def load_run(run_id: str) -> dict | None:
    path = (RUNS_DIR / f"{run_id}.jsonl").resolve()
    if not path.is_relative_to(RUNS_DIR.resolve()) or not path.is_file():
        return None

    task_id = run_id.split("/")[0]
    task = load_tasks().get(task_id, {})

    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return {
        "run_id": run_id,
        "task_id": task_id,
        "title": task.get("title", task_id),
        "vendor": task.get("vendor"),
        "os_train": task.get("os_train"),
        "records": records,
    }


def build_leaderboard(date: str | None = None) -> list[dict]:
    tasks = load_tasks()
    runs = load_runs(date=date)

    groups: dict[tuple, dict] = {}
    for run in runs:
        task = tasks.get(run["task_id"])
        if task is None:
            continue

        key = (run["model"], task["vendor"], task["os_train"], task["category"])
        group = groups.setdefault(
            key,
            {
                "model": run["model"],
                "vendor": task["vendor"],
                "os_train": task["os_train"],
                "category": task["category"],
                "runs": 0,
                "passes": 0,
            },
        )
        group["runs"] += 1
        if run["grading"]["pass"]:
            group["passes"] += 1

    leaderboard = []
    for group in groups.values():
        group["pass_rate"] = group["passes"] / group["runs"] if group["runs"] else 0.0
        leaderboard.append(group)

    leaderboard.sort(key=lambda g: (g["model"], g["vendor"], g["os_train"], g["category"]))
    return leaderboard
