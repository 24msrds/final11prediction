from fastapi import FastAPI
from selector import auto_best_xi

app = FastAPI(title="ODI AI Selector")

@app.get("/")
def root():
    return {"status": "ODI AI Selector is running"}

@app.get("/best-xi")
def best_xi(
    opponent: str,
    venue: str
):
    return auto_best_xi(opponent=opponent, venue=venue)
