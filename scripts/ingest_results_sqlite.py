import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bootcheck.tasks_lib import RESULTS_ROOT, load_all_tasks

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
    return {
        task_id: {
            "vendor": task.get("vendor"),
            "os_train": task.get("os_train"),
            "category": task.get("category"),
            "title": task.get("title"),
        }
        for task_id, task in load_all_tasks().items()
    }


def iterate_records():
    for path in sorted(RESULTS_ROOT.glob("**/*.jsonl")):
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
