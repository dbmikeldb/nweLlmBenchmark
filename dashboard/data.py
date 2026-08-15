import glob
import json
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


def load_runs() -> list[dict]:
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
                runs.append(record)
    return runs


def build_leaderboard() -> list[dict]:
    tasks = load_tasks()
    runs = load_runs()

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
