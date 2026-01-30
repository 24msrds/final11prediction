from fastapi import FastAPI
from backend.selector import auto_best_xi

app = FastAPI(title="ODI AI Selector")

@app.get("/")
def root():
    return {"status": "ODI AI Selector is running"}

@app.get("/best-xi")
def best_xi(
    pitch_type: str = "neutral",
    opponent: str | None = None,
    venue: str | None = None
):
    return auto_best_xi(pitch_type, opponent, venue)
