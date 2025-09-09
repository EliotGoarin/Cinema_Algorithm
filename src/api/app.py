from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.tmdb_client import search_movie
from src.ingest.ingest_tmdb import ingest_one
from src.ml.recommender_service import recommend, refresh_cache

# ----- Création de l'app -----
app = FastAPI(title="Cinema Algorithm API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Schémas Pydantic -----
class IngestRequest(BaseModel):
    tmdb_id: int

class RecommendRequest(BaseModel):
    seed_ids: list[int]
    k: int = 10

# ----- Routes -----
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tmdb/search")
def tmdb_search(q: str, page: int = 1):
    """Chercher un film sur TMDb"""
    return search_movie(q, page=page)

@app.post("/ingest/one")
def ingest_movie(req: IngestRequest):
    """Ingérer un film dans la base à partir de son tmdb_id"""
    res = ingest_one(req.tmdb_id)
    refresh_cache()
    return res

@app.post("/ingest/search_and_add")
def ingest_search_and_add(q: str):
    """
    Chercher un film sur TMDb et ingérer le 1er résultat directement
    Exemple: POST /ingest/search_and_add?q=Inception
    """
    data = search_movie(q)
    results = data.get("results", [])
    if not results:
        return {"ingested": 0, "message": "Aucun résultat TMDB"}
    first = results[0]
    res = ingest_one(first["id"])
    refresh_cache()
    return {"ingested": 1, "movie": res}

@app.post("/recommend")
def recommend_movies(req: RecommendRequest):
    """Obtenir des recommandations à partir d'une liste de films seed"""
    recs = recommend(req.seed_ids, k=req.k)
    return {"recommendations": recs}
