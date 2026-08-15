from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dashboard.data import build_leaderboard

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="LLM Network Benchmark Dashboard")


@app.get("/api/leaderboard")
def leaderboard() -> list[dict]:
    return build_leaderboard()


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
