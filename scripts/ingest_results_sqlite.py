import json
import sqlite3
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "bootcheck" / "tasks"
RUNS_DIR = REPO_ROOT / "results" / "runs"
DB_PATH = REPO_ROOT / "results" / "bootcheck.db"

SCHEMA = """
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    task_id TEXT,
    title TEXT,
    vendor TEXT,
    os_train TEXT,
    category TEXT,
    tier TEXT,
    model TEXT,
    status TEXT,
    pass INTEGER,
    cost_usd REAL,
    latency_ms REAL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    error TEXT
);
"""


def load_tasks() -> dict:
    tasks = {}
    for path in TASKS_DIR.glob("*.yaml"):
        data = yaml.safe_load(path.read_text())
        tasks[data["id"]] = {
            "vendor": data.get("vendor"),
            "os_train": data.get("os_train"),
            "category": data.get("category"),
            "title": data.get("title"),
        }
    return tasks


def iterate_records():
    for path in sorted(RUNS_DIR.glob("**/*.jsonl")):
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main():
    tasks = load_tasks()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS runs")
    conn.executescript(SCHEMA)

    rows = []
    for record in iterate_records():
        task_meta = tasks.get(record["task_id"], {})
        is_error = "error" in record
        if is_error:
            status = "error"
            passed = None
        else:
            passed = bool(record.get("grading", {}).get("pass"))
            status = "pass" if passed else "fail"

        rows.append(
            (
                record.get("timestamp"),
                record.get("task_id"),
                task_meta.get("title"),
                record.get("vendor") or task_meta.get("vendor"),
                record.get("os_train") or task_meta.get("os_train"),
                task_meta.get("category"),
                record.get("tier"),
                record.get("model"),
                status,
                None if passed is None else int(passed),
                record.get("cost_usd"),
                record.get("latency_ms"),
                record.get("prompt_tokens"),
                record.get("completion_tokens"),
                record.get("error"),
            )
        )

    conn.executemany(
        """
        INSERT INTO runs (
            timestamp, task_id, title, vendor, os_train, category, tier,
            model, status, pass, cost_usd, latency_ms, prompt_tokens,
            completion_tokens, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    conn.close()
    print(f"Ingested {count} rows into {DB_PATH}")


if __name__ == "__main__":
    main()
