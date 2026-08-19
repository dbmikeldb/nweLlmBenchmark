from pathlib import Path

import pytest

from bootcheck import tasks_lib


def _write_task(root: Path, rel_path: str, body: str = "title: Example\n") -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path


def test_metadata_from_path_derives_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks_lib, "TASKS_ROOT", tmp_path)
    path = _write_task(tmp_path, "bootcheck/cisco/iosxe/static-routing/tag-ipv4.yaml")

    meta = tasks_lib.metadata_from_path(path)

    assert meta == {
        "id": "bootcheck-cisco-iosxe-static-routing-tag-ipv4",
        "tier": "bootcheck",
        "vendor": "cisco",
        "os_train": "iosxe",
        "category": "static-routing",
        "qualifier": "tag-ipv4",
    }


def test_metadata_from_path_wrong_depth_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks_lib, "TASKS_ROOT", tmp_path)
    path = _write_task(tmp_path, "bootcheck/cisco/iosxe/tag-ipv4.yaml")

    with pytest.raises(ValueError, match="expected tasks/"):
        tasks_lib.metadata_from_path(path)


def test_load_task_merges_derived_metadata_and_file_content(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks_lib, "TASKS_ROOT", tmp_path)
    path = _write_task(
        tmp_path,
        "bootcheck/cisco/iosxe/static-routing/tag-ipv4.yaml",
        body="title: Static route with a route tag\ntags: [route-tag]\n",
    )

    task = tasks_lib.load_task(path)

    assert task["id"] == "bootcheck-cisco-iosxe-static-routing-tag-ipv4"
    assert task["category"] == "static-routing"
    assert task["title"] == "Static route with a route tag"
    assert task["tags"] == ["route-tag"]


@pytest.mark.parametrize("reserved_key", sorted(tasks_lib.RESERVED_KEYS))
def test_load_task_rejects_reserved_frontmatter_keys(tmp_path, monkeypatch, reserved_key):
    monkeypatch.setattr(tasks_lib, "TASKS_ROOT", tmp_path)
    path = _write_task(
        tmp_path,
        "bootcheck/cisco/iosxe/static-routing/tag-ipv4.yaml",
        body=f"title: Example\n{reserved_key}: should-not-be-here\n",
    )

    with pytest.raises(ValueError, match=reserved_key):
        tasks_lib.load_task(path)


def test_load_all_tasks_keys_by_derived_id(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks_lib, "TASKS_ROOT", tmp_path)
    _write_task(tmp_path, "bootcheck/cisco/iosxe/static-routing/tag-ipv4.yaml")
    _write_task(tmp_path, "bootcheck/cisco/iosxe/interface-config/vlan.yaml")

    tasks = tasks_lib.load_all_tasks()

    assert set(tasks) == {
        "bootcheck-cisco-iosxe-static-routing-tag-ipv4",
        "bootcheck-cisco-iosxe-interface-config-vlan",
    }


def test_load_all_tasks_raises_on_id_collision(tmp_path, monkeypatch):
    # id is a hyphen-join of path segments, so two distinct paths can still
    # produce the same id if a segment itself contains a hyphen — this is
    # exactly why load_all_tasks must guard against it rather than trust
    # id as a safe reverse-parsable key.
    monkeypatch.setattr(tasks_lib, "TASKS_ROOT", tmp_path)
    _write_task(tmp_path, "a/b-c/os/cat/q.yaml")
    _write_task(tmp_path, "a-b/c/os/cat/q.yaml")

    with pytest.raises(ValueError, match="duplicate task id"):
        tasks_lib.load_all_tasks()


def test_results_dir_for_mirrors_task_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks_lib, "RESULTS_ROOT", tmp_path)
    task = {
        "tier": "bootcheck",
        "vendor": "cisco",
        "os_train": "iosxe",
        "category": "static-routing",
        "qualifier": "tag-ipv4",
    }

    assert tasks_lib.results_dir_for(task) == (
        tmp_path / "bootcheck" / "cisco" / "iosxe" / "static-routing" / "tag-ipv4"
    )


def test_metadata_from_run_path_derives_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks_lib, "RESULTS_ROOT", tmp_path)
    run_path = tmp_path / "bootcheck/cisco/iosxe/static-routing/tag-ipv4/20260819T120000Z.jsonl"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.write_text("")

    meta = tasks_lib.metadata_from_run_path(run_path)

    assert meta == {
        "id": "bootcheck-cisco-iosxe-static-routing-tag-ipv4",
        "tier": "bootcheck",
        "vendor": "cisco",
        "os_train": "iosxe",
        "category": "static-routing",
        "qualifier": "tag-ipv4",
        "run_timestamp": "20260819T120000Z",
    }


def test_metadata_from_run_path_wrong_depth_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks_lib, "RESULTS_ROOT", tmp_path)
    run_path = tmp_path / "bootcheck/cisco/iosxe/20260819T120000Z.jsonl"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.write_text("")

    with pytest.raises(ValueError, match="expected results/"):
        tasks_lib.metadata_from_run_path(run_path)
