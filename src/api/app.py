from __future__ import annotations

import logging
import os
from typing import List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Reco DB (si dispo)
try:
    from src.ml.recommender import recommend as recommend_db, refresh_cache, debug_stats
    HAS_DB_RECO = True
except Exception:
    HAS_DB_RECO = False
    def refresh_cache(): return 0  # no-op
    def debug_stats(): return {"warning": "db reco indisponible"}

# Reco “stateless” TMDb
from src.services.tmdb_simple_reco import recommend_simple as recommend_tmdb

# (Tes imports existants)
from src.core.tmdb_client import search_movie, popular, trending_day
from src.ingest.ingest_tmdb import ingest_one

log = logging.getLogger("api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Movie Recommender API", version="1.5.0")

# CORS
_allow_origins_env = os.getenv("ALLOW_ORIGINS", "*").strip()
_allow_origins = ["*"] if _allow_origins_env in ("", "*") else [o.strip() for o in _allow_origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendRequest(BaseModel):
    seed_ids: List[int]
    k: int = 10

@app.get("/health")
def health():
    return {"ok": True, "service": "api", "version": app.version, "db_reco": HAS_DB_RECO}

@app.post("/admin/refresh_cache")
def admin_refresh_cache():
    try:
        n = refresh_cache()
        return {"refreshed": True, "indexed": n}
    except Exception as e:
        log.exception("Refresh cache failed")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {e}") from e

@app.get("/admin/reco_stats")
def admin_reco_stats():
    try:
        return debug_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
def search(q: str = Query(..., min_length=1), page: int = 1):
    return search_movie(q, page=page)

@app.post("/recommend")
def post_recommend(body: RecommendRequest):
    k = max(1, min(50, int(body.k)))
    seed_ids = [int(x) for x in body.seed_ids][:5]
    try:
        s_recs = recommend_tmdb(seed_ids, k)
        return {"results": s_recs, "count": len(s_recs), "mode": "tmdb_simple"}
    except Exception as e:
        log.exception("Reco TMDb échouée")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {e}") from e


# ---- Ingestion (tes routes existantes) ----
@app.post("/ingest/add")
def ingest_add(tmdb_id: int = Query(...), do_refresh: bool = True):
    try:
        res = ingest_one(int(tmdb_id))
    except Exception as e:
        log.exception("Ingestion échouée")
        raise HTTPException(status_code=500, detail=f"Ingestion échouée: {e}") from e
    if do_refresh:
        try: refresh_cache()
        except Exception as e: log.warning("Refresh après ingestion échoué: %s", e)
    return {"ok": True, "id": res.get("ingested") or tmdb_id, "title": res.get("title"), "ingested": res}

@app.post("/ingest/search_and_add")
def ingest_search_and_add(q: str = Query(..., min_length=1), page: int = 1, do_refresh: bool = True):
    data = search_movie(q, page=page)
    results = data.get("results") or []
    if not results:
        raise HTTPException(status_code=404, detail="Aucun film trouvé pour cette recherche")
    top = results[0]
    try:
        res = ingest_one(int(top["id"]))
    except Exception as e:
        log.exception("Ingestion échouée")
        raise HTTPException(status_code=500, detail=f"Ingestion échouée: {e}") from e
    if do_refresh:
        try: refresh_cache()
        except Exception as e: log.warning("Refresh après ingestion échoué: %s", e)
    return {"ok": True, "id": res.get("ingested") or int(top["id"]), "title": res.get("title") or top.get("title"),
            "query": q, "selected": {"id": top.get("id"), "title": top.get("title")}, "ingested": res}

# ---- Alias tmdb/* (si ton front les utilise) ----
@app.get("/tmdb/health")
def tmdb_health(): return health()

@app.post("/tmdb/refresh")
def tmdb_refresh(): return admin_refresh_cache()

@app.get("/tmdb/search")
def tmdb_search(q: str = Query(..., min_length=1), page: int = 1): return search(q=q, page=page)

@app.post("/tmdb/recommend")
def tmdb_recommend(body: RecommendRequest): return post_recommend(body)

from src.core.tmdb_client import movie_details, similar_movies

@app.get("/tmdb/details")
def tmdb_details(id: int):
    return movie_details(int(id))

@app.get("/tmdb/similar")
def tmdb_similar(id: int, page: int = 1):
    return similar_movies(int(id), page=page)
