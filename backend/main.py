from fastapi import FastAPI
from selector import auto_best_xi


app = FastAPI()

@app.get("/best-xi")
def best_xi(
    pitch_type: str = "neutral",
    opponent: str | None = None,
    venue: str | None = None
):
    return auto_best_xi(
        pitch_type=pitch_type,
        opponent=opponent,
        venue=venue
    )
