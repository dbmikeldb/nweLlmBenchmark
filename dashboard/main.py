from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from dashboard.data import build_leaderboard, list_available_dates, list_runs, load_run

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="LLM Network Benchmark Dashboard")


@app.get("/api/leaderboard")
def leaderboard(date: str | None = None) -> list[dict]:
    return build_leaderboard(date=date)


@app.get("/api/dates")
def dates() -> list[str]:
    return list_available_dates()


@app.get("/api/runs")
def runs(date: str | None = None) -> list[dict]:
    return list_runs(date=date)


@app.get("/api/runs/{run_id:path}")
def run_detail(run_id: str) -> dict:
    run = load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
