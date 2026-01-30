from fastapi import FastAPI, Query
from selector import auto_best_xi

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/best-xi")
def best_xi(
    pitch_type: str = Query("neutral"),
    opponent: str = Query(None)
):
    return auto_best_xi(pitch_type=pitch_type, opponent=opponent)
