# backend/main.py

from fastapi import FastAPI
from backend.selector import auto_best_xi

app = FastAPI(title="ODI AI Selector API")


@app.get("/best-xi")
def get_best_xi(
    pitch_type: str = "neutral",
    opponent: str | None = None
):
    return auto_best_xi(
        pitch_type=pitch_type,
        opponent=opponent
    )
