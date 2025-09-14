from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.ml.recommender_service import recommend, refresh_cache
from src.core.tmdb_client import search_movie, popular, trending_day
from src.ingest.ingest_tmdb import ingest_one

# ------------------ LOGGING ------------------
log = logging.getLogger("api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# ------------------ APP ------------------
app = FastAPI(title="Movie Recommender API", version="1.3.2")

# CORS large en dev (à restreindre en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ SCHEMAS ------------------
class RecommendRequest(BaseModel):
    seed_ids: List[int]
    k: int = 10

# ------------------ ROUTES OFFICIELLES ------------------
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/refresh")
def refresh():
    refresh_cache()
    return {"refreshed": True}

@app.get("/search")
def search(q: str = Query(..., min_length=1), page: int = 1):
    return search_movie(q, page=page)

@app.post("/recommend")
def post_recommend(body: RecommendRequest):
    recs = recommend(body.seed_ids, body.k)
    return {"results": recs, "count": len(recs)}

# -------- INGESTION DIRECTE (200 OK) --------
@app.post("/ingest/add")
def ingest_add(
    tmdb_id: int = Query(..., description="ID TMDb du film à ingérer"),
    do_refresh: bool = True
):
    """
    Ingestion d'un film par son ID TMDb. Réponse 200 + { ok, id, title } à la racine.
    """
    try:
        res = ingest_one(int(tmdb_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion échouée: {e}")
    if do_refresh:
        refresh_cache()
    return {
        "ok": True,
        "id": res["ingested"],
        "title": res.get("title"),
        "ingested": res,
    }

@app.post("/ingest/search_and_add")
def ingest_search_and_add(
    q: str = Query(..., min_length=1, description="Requête texte (titre du film)"),
    page: int = 1,
    do_refresh: bool = True
):
    """
    Recherche TMDb puis ingère le premier résultat. Réponse 200 + { ok, id, title }.
    """
    data = search_movie(q, page=page)
    results = data.get("results") or []
    if not results:
        raise HTTPException(status_code=404, detail="Aucun film trouvé pour cette recherche")
    top = results[0]
    try:
        res = ingest_one(int(top["id"]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion échouée: {e}")
    if do_refresh:
        refresh_cache()
    return {
        "ok": True,
        "id": res["ingested"],
        "title": res.get("title"),
        "query": q,
        "selected": {"id": top["id"], "title": top.get("title")},
        "ingested": res,
    }

# -------- ADMIN / BOOTSTRAP --------
@app.post("/admin/bootstrap")
def admin_bootstrap(
    source: str = Query("popular", pattern="^(popular|trending)$"),
    pages: int = 5
):
    """
    Ingestion rapide de films pour élargir le catalogue local.
    - source=popular ou trending
    - pages: nombre de pages TMDb à ingérer (≈20 films / page)
    """
    pages = max(1, min(50, int(pages)))
    ingested = 0
    for p in range(1, pages + 1):
        data = popular(page=p) if source == "popular" else trending_day(page=p)
        for m in data.get("results", []):
            ingest_one(int(m["id"]))
            ingested += 1
    refresh_cache()
    return {"source": source, "pages": pages, "ingested": ingested}

# ------------------ ALIAS /tmdb/* (compat front) ------------------
@app.get("/tmdb/health")
def tmdb_health():
    return health()

@app.post("/tmdb/refresh")
def tmdb_refresh():
    return refresh()

@app.get("/tmdb/search")
def tmdb_search(q: str = Query(..., min_length=1), page: int = 1):
    return search(q=q, page=page)

@app.post("/tmdb/recommend")
def tmdb_recommend(body: RecommendRequest):
    recs = recommend(body.seed_ids, body.k)
    return {"results": recs, "count": len(recs)}

@app.post("/tmdb/ingest/add")
def tmdb_ingest_add(tmdb_id: int = Query(...), do_refresh: bool = True):
    return ingest_add(tmdb_id=tmdb_id, do_refresh=do_refresh)

@app.post("/tmdb/ingest/search_and_add")
def tmdb_ingest_search_and_add(
    q: str = Query(..., min_length=1),
    page: int = 1,
    do_refresh: bool = True
):
    return ingest_search_and_add(q=q, page=page, do_refresh=do_refresh)
