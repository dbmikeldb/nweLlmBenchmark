from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_ROOT = REPO_ROOT / "tasks"
RESULTS_ROOT = REPO_ROOT / "results"

RESERVED_KEYS = {"id", "vendor", "os_train", "tier", "category"}


def discover_task_paths() -> list[Path]:
    return sorted(TASKS_ROOT.glob("**/*.yaml"))


def metadata_from_path(path: Path) -> dict:
    rel = path.resolve().relative_to(TASKS_ROOT)
    parts = rel.parts
    if len(parts) != 5:
        raise ValueError(
            f"expected tasks/<tier>/<vendor>/<os_train>/<category>/<qualifier>.yaml, got {rel}"
        )

    tier, vendor, os_train, category, filename = parts
    qualifier = Path(filename).stem
    task_id = "-".join([tier, vendor, os_train, category, qualifier])

    return {
        "id": task_id,
        "tier": tier,
        "vendor": vendor,
        "os_train": os_train,
        "category": category,
        "qualifier": qualifier,
    }


def load_task(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())

    clash = RESERVED_KEYS & data.keys()
    if clash:
        raise ValueError(
            f"{path}: {sorted(clash)} must not be set in frontmatter — derived from the file's path"
        )

    return {**metadata_from_path(path), **data}


def load_all_tasks() -> dict[str, dict]:
    tasks: dict[str, dict] = {}
    for path in discover_task_paths():
        task = load_task(path)
        if task["id"] in tasks:
            raise ValueError(f"duplicate task id {task['id']!r}: {path}")
        tasks[task["id"]] = task
    return tasks


def results_dir_for(task: dict) -> Path:
    return (
        RESULTS_ROOT
        / task["tier"]
        / task["vendor"]
        / task["os_train"]
        / task["category"]
        / task["qualifier"]
    )


def metadata_from_run_path(path: Path) -> dict:
    rel = path.resolve().relative_to(RESULTS_ROOT)
    parts = rel.parts
    if len(parts) != 6:
        raise ValueError(
            "expected results/<tier>/<vendor>/<os_train>/<category>/<qualifier>/<timestamp>.jsonl, "
            f"got {rel}"
        )

    tier, vendor, os_train, category, qualifier, filename = parts
    task_id = "-".join([tier, vendor, os_train, category, qualifier])

    return {
        "id": task_id,
        "tier": tier,
        "vendor": vendor,
        "os_train": os_train,
        "category": category,
        "qualifier": qualifier,
        "run_timestamp": Path(filename).stem,
    }
