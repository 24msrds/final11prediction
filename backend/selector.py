from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# ✅ CORRECT IMPORT FOR RENDER
from selector import auto_best_xi

app = FastAPI(
    title="ODI AI Final XI Selector",
    version="1.0"
)

# -------------------------------------------------
# CORS (SAFE FOR STREAMLIT + RENDER)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------
@app.get("/")
def root():
    return {"status": "ODI AI Selector is running"}

# -------------------------------------------------
# BEST XI ENDPOINT
# -------------------------------------------------
@app.get("/best-xi")
def best_xi(
    pitch_type: str = Query("neutral"),
    opponent: str | None = Query(None),
    venue: str | None = Query(None),
):
    try:
        xi = auto_best_xi(
            pitch_type=pitch_type,
            opponent=opponent,
            venue=venue,
        )
        return xi
    except Exception as e:
        return {
            "error": "Internal Server Error",
            "details": str(e),
        }
