from __future__ import annotations

import logging
import os
from typing import List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---- Imports robustes pour le moteur de reco ----
# On essaie d'abord la nouvelle implémentation (recommender.py),
# sinon on retombe sur l'ancienne (recommender_service.py) pour compat.
try:
    from src.ml.recommender import recommend, refresh_cache  # nouvelle version
except Exception:  # noqa: BLE001
    from src.ml.recommender_service import recommend, refresh_cache  # rétro-compat

from src.core.tmdb_client import search_movie, popular, trending_day
from src.ingest.ingest_tmdb import ingest_one

# ------------------ LOGGING ------------------
log = logging.getLogger("api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# ------------------ APP ------------------
app = FastAPI(title="Movie Recommender API", version="1.4.0")

# ------------------ CORS ------------------
# ALLOW_ORIGINS peut être "*", ou une liste CSV: "http://localhost:5173,https://mon-site.com"
_allow_origins_env = os.getenv("ALLOW_ORIGINS", "*").strip()
if _allow_origins_env == "*" or _allow_origins_env == "":
    _allow_origins = ["*"]
else:
    _allow_origins = [o.strip() for o in _allow_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
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
    return {"ok": True, "service": "api", "version": app.version}


@app.post("/refresh")
def refresh():
    """Reconstruit l'index KNN en mémoire (à appeler après ingestion)."""
    try:
        n = refresh_cache()
        return {"refreshed": True, "indexed": n}
    except Exception as e:  # noqa: BLE001
        log.exception("Refresh cache failed")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {e}") from e


@app.post("/admin/refresh_cache")
def admin_refresh_cache():
    """Alias explicite côté /admin."""
    return refresh()


@app.get("/search")
def search(q: str = Query(..., min_length=1), page: int = 1):
    return search_movie(q, page=page)


@app.post("/recommend")
def post_recommend(body: RecommendRequest):
    """
    Retourne les recommandations avec :
    - tmdb_id, title, poster_path, score, reason (explication brève), overview (description)
    """
    try:
        recs = recommend(body.seed_ids, body.k)
        # Le moteur renvoie déjà reason + overview (si tu as intégré la nouvelle version).
        # Rien à faire de plus ici côté API.
        return {"results": recs, "count": len(recs)}
    except Exception as e:  # noqa: BLE001
        log.exception("Recommendation failed")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {e}") from e


# -------- INGESTION DIRECTE --------
@app.post("/ingest/add")
def ingest_add(
    tmdb_id: int = Query(..., description="ID TMDb du film à ingérer"),
    do_refresh: bool = True,
):
    """
    Ingestion d'un film par son ID TMDb.
    Réponse { ok, id, title, ingested:{...} }.
    """
    try:
        res = ingest_one(int(tmdb_id))
    except Exception as e:  # noqa: BLE001
        log.exception("Ingestion échouée")
        raise HTTPException(status_code=500, detail=f"Ingestion échouée: {e}") from e
    if do_refresh:
        try:
            refresh_cache()
        except Exception as e:  # noqa: BLE001
            log.warning("Refresh après ingestion échoué: %s", e)
    return {
        "ok": True,
        "id": res.get("ingested") or tmdb_id,
        "title": res.get("title"),
        "ingested": res,
    }


@app.post("/ingest/search_and_add")
def ingest_search_and_add(
    q: str = Query(..., min_length=1, description="Requête texte (titre du film)"),
    page: int = 1,
    do_refresh: bool = True,
):
    """
    Recherche TMDb puis ingère le premier résultat.
    Réponse { ok, id, title, query, selected:{id,title}, ingested:{...} }.
    """
    data = search_movie(q, page=page)
    results = data.get("results") or []
    if not results:
        raise HTTPException(status_code=404, detail="Aucun film trouvé pour cette recherche")
    top = results[0]
    try:
        res = ingest_one(int(top["id"]))
    except Exception as e:  # noqa: BLE001
        log.exception("Ingestion échouée")
        raise HTTPException(status_code=500, detail=f"Ingestion échouée: {e}") from e
    if do_refresh:
        try:
            refresh_cache()
        except Exception as e:  # noqa: BLE001
            log.warning("Refresh après ingestion échoué: %s", e)
    return {
        "ok": True,
        "id": res.get("ingested") or int(top["id"]),
        "title": res.get("title") or top.get("title"),
        "query": q,
        "selected": {"id": top.get("id"), "title": top.get("title")},
        "ingested": res,
    }


# -------- ADMIN / BOOTSTRAP --------
@app.post("/admin/bootstrap")
def admin_bootstrap(
    source: str = Query("popular", pattern="^(popular|trending)$"),
    pages: int = 5,
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
            try:
                ingest_one(int(m["id"]))
                ingested += 1
            except Exception as e:  # noqa: BLE001
                log.warning("Échec ingestion id=%s: %s", m.get("id"), e)
    try:
        refresh_cache()
    except Exception as e:  # noqa: BLE001
        log.warning("Refresh après bootstrap échoué: %s", e)
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
    return post_recommend(body)


@app.post("/tmdb/ingest/add")
def tmdb_ingest_add(tmdb_id: int = Query(...), do_refresh: bool = True):
    return ingest_add(tmdb_id=tmdb_id, do_refresh=do_refresh)


@app.post("/tmdb/ingest/search_and_add")
def tmdb_ingest_search_and_add(
    q: str = Query(..., min_length=1),
    page: int = 1,
    do_refresh: bool = True,
):
    return ingest_search_and_add(q=q, page=page, do_refresh=do_refresh)
