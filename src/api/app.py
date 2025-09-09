from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging

from src.ml.recommender_service import recommend, refresh_cache
from src.core.tmdb_client import search_movie
from src.ingest.ingest_tmdb import ingest_one

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("api")

# --- FastAPI app ---
app = FastAPI(title="Cinema Algorithm API")

# --- CORS configurable ---
origins = os.getenv(
    "ALLOW_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Healthcheck ---
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# --- Recommender ---
class RecommendRequest(BaseModel):
    seed_ids: list[int]
    k: int = 5

@app.post("/recommend")
def recommend_movies(req: RecommendRequest):
    recs = recommend(req.seed_ids, k=req.k)
    return {"recommendations": recs}


# --- Admin refresh cache ---
@app.post("/admin/refresh_cache")
def refresh_cache_route():
    refresh_cache()
    return {"status": "cache refreshed"}


# --- TMDb search ---
@app.get("/tmdb/search")
def tmdb_search(q: str):
    return search_movie(q)


# --- Ingest from TMDb ---
@app.post("/ingest/search_and_add")
def ingest_search_and_add(q: str):
    data = search_movie(q)
    results = data.get("results", [])
    if not results:
        return {"ingested": 0, "message": "Aucun résultat TMDB"}
    first = results[0]
    res = ingest_one(first["id"])
    refresh_cache()
    return {"ingested": 1, "movie": res}
