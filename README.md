# nweLlmBenchmark

A benchmark harness for testing LLM correctness on network engineering
tasks.

## How it works

Each task in `bootcheck/tasks/*.yaml` describes a network config scenario
(prompt + context) and an expected-config answer key. The harness sends the
prompt to one or more models via [Requesty](https://requesty.ai) (an
OpenAI-compatible LLM gateway), then grades the response against the task's
`pass_criteria` in `bootcheck/grading.py`.

Run a single task against one model:

```
.venv/bin/python -m bootcheck.harness --task bootcheck/tasks/cisco-iosxe-vlan.yaml --model google/gemma-4-31b-it
```

Sweep a task across every free-tier model:

```
.venv/bin/python -m bootcheck.harness --task bootcheck/tasks/cisco-iosxe-vlan.yaml --model all_free
```
> [!WARNING]
> Sweeping across all free models can burn through provider rate limits fast (e.g. Requesty's free tier is capped at 200 requests/day).
> Consider targeting a single model or a subset before running `--model all_free`.

**N.B.: Future development will find a viable solution to this. (Likely moving away from Requesty)**

Each run appends a result to `results/runs/<task_id>/<timestamp>.jsonl`.

## Setup

```
cp .env.example .env   # add your REQUESTY_API_KEY
pip install -r requirements.txt
```

## Results dashboards

Two ways to browse `results/runs/`:
- **`dashboard/`** — a small FastAPI app with a static leaderboard UI.
  `.venv/bin/python -m uvicorn dashboard.main:app --host 127.0.0.1 --port 8000`
- **Grafana** — `scripts/ingest_results_sqlite.py` rebuilds
  `results/bootcheck.db` from `results/runs/*.jsonl`, queryable from Grafana
  via the `frser-sqlite-datasource` plugin.

  **N.B.: Future development will likely remove the local dashboard in favour of a Grafana dashboard, maintained in a seaprate repository.**

## Repo layout

- `bootcheck/tasks/` — task fixtures (prompt, context, expected config, pass criteria)
- `bootcheck/harness.py` — runs a task against one or more models
- `bootcheck/grading.py` — grades a response against a task's pass criteria
- `requesty_client/` — thin OpenAI-compatible client for the Requesty gateway
- `results/runs/` — one JSONL file per run, source of truth for all results
- `dashboard/` — FastAPI results viewer
- `scripts/` — one-off and support scripts (SQLite ingestion, smoke test)

See `CLAUDE.md` for task-authoring conventions and branching strategy.

## Roadmap
It may be evident already, but this project is still in the very early stages of development. An official roadmap is not yet available and this project will be maintained as long as it's enjoyable, or until it starts providing real value.

## Contributing
At this stage, the project is not available for 'open-source' style contrubtions. If this is a project you're interested in, please reach out via LinkedIn at: www.linkedin.com/in/mmyers-alba