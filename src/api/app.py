# src/api/app.py
from __future__ import annotations

import os
import logging
import asyncio
import numbers
from typing import List, Dict, Any, Iterable, Tuple, Optional

import requests
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.tmdb_client import search_movie, movie_details, similar_movies

# --- SQLAlchemy (DB) ---
try:
    from sqlalchemy import create_engine, text
except Exception:
    create_engine = None  # type: ignore
    text = None  # type: ignore

# ---------- Recommender (optionnel) ----------
try:
    from src.ml.recommender import recommend as recommend_db  # -> List[int] | List[dict] | mixed
    HAS_DB_RECO = True
except Exception:
    HAS_DB_RECO = False

# ---------- Logger ----------
log = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

# ---------- App & CORS ----------
app = FastAPI(title="Movie Algorithm API")

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class RecommendBody(BaseModel):
    seed_ids: List[int]
    k: int = 12

# ---------- Utils ----------
def normalize_movie(m: Dict[str, Any]) -> Dict[str, Any]:
    if not m:
        return {}
    return {
        "id": m.get("id"),
        "title": m.get("title") or m.get("original_title"),
        "poster_path": m.get("poster_path"),
        "release_date": m.get("release_date"),
        "overview": m.get("overview"),
        "genres": m.get("genres"),
        "local_score": m.get("local_score"),
    }

def hydrate_ids(ids: Iterable[int]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for mid in ids:
        try:
            d = movie_details(int(mid))
            nm = normalize_movie(d)
            if nm.get("title"):
                out.append(nm)
        except Exception as e:
            log.warning("Hydration failed for %s: %s", mid, e)
    return out

def _extract_id_from_dict(d: Dict[str, Any]) -> int | None:
    for key in ("id", "tmdb_id", "movie_id"):
        if key in d and d[key] is not None:
            try:
                return int(d[key])
            except Exception:
                return None
    return None

def coerce_to_id_list(candidates: Iterable[Any]) -> List[int]:
    ids: List[int] = []
    for x in candidates or []:
        if isinstance(x, numbers.Integral):
            ids.append(int(x))
        elif isinstance(x, str):
            try:
                ids.append(int(x))
            except ValueError:
                continue
        elif isinstance(x, dict):
            mid = _extract_id_from_dict(x)
            if mid is not None:
                ids.append(int(mid))
        else:
            try:
                if isinstance(x, float) and x.is_integer():
                    ids.append(int(x))
                else:
                    ids.append(int(x))
            except Exception:
                continue
    return ids

def dedup_preserve_order(seq: Iterable[int]) -> List[int]:
    seen = set()
    out: List[int] = []
    for v in seq:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out

def collect_similar_ids_from_tmdb(seeds: List[int], max_needed: int, max_pages: int = 5) -> List[int]:
    out: List[int] = []
    seen = set()
    for seed in seeds:
        for page in range(1, max_pages + 1):
            try:
                sim = similar_movies(int(seed), page=page) or {}
                results = sim.get("results") or []
                if not results:
                    break
                for m in results:
                    mid = m.get("id")
                    if isinstance(mid, int) and mid not in seen:
                        seen.add(mid)
                        out.append(mid)
                        if len(out) >= max_needed:
                            return out
            except Exception as e:
                log.warning("TMDb similar fetch failed for seed=%s page=%s: %s", seed, page, e)
                break
    return out

# ---------- DB helpers (Top-rated locaux) ----------
_DB_ENGINE = None

def _get_db_engine():
    global _DB_ENGINE
    if _DB_ENGINE is not None:
        return _DB_ENGINE
    db_url = os.getenv("DB_URL")
    if not db_url or create_engine is None:
        return None
    try:
        _DB_ENGINE = create_engine(db_url, pool_pre_ping=True)
    except Exception as e:
        log.warning("DB engine init failed: %s", e)
        _DB_ENGINE = None
    return _DB_ENGINE

def _score_scale() -> float:
    try:
        return float(os.getenv("CATALOG_SCORE_MAX", "100"))
    except Exception:
        return 100.0

def _query_top_rated_ids(limit: int) -> List[Tuple[int, float]]:
    """
    Renvoie [(tmdb_id, score_brut)] triés par score décroissant depuis TA base.
    Configure via env :
      - CATALOG_TABLE (ex: 'films')
      - CATALOG_ID_COL (ex: 'tmdb_id')
      - CATALOG_SCORE_COL (ex: 'avg_rating' ou 'score')
      - CATALOG_SCORE_MAX (ex: 100, 10, 5) -> scaling
    Sinon on essaie plusieurs combinaisons usuelles.
    """
    eng = _get_db_engine()
    if eng is None or text is None:
        return []

    t = os.getenv("CATALOG_TABLE")
    c_id = os.getenv("CATALOG_ID_COL")
    c_score = os.getenv("CATALOG_SCORE_COL")

    candidates: List[Tuple[str, str, str]] = []
    if t and c_id and c_score:
        candidates.append((t, c_id, c_score))

    candidates.extend([
        ("film", "tmdb_id", "score"),
        ("film", "tmdb_id", "rating"),
        ("film", "tmdb_id", "avg_rating"),
        ("films", "tmdb_id", "score"),
        ("films", "tmdb_id", "avg_rating"),
        ("movies", "tmdb_id", "score"),
        ("movies", "tmdb_id", "rating"),
        ("movies", "tmdb_id", "avg_rating"),
        ("movie", "tmdb_id", "score"),
        ("movie", "tmdb_id", "avg_rating"),
    ])

    for table, id_col, score_col in candidates:
        try:
            sql = text(
                f"SELECT {id_col} AS id, {score_col} AS s "
                f"FROM {table} "
                f"WHERE {id_col} IS NOT NULL AND {score_col} IS NOT NULL "
                f"ORDER BY {score_col} DESC "
                f"LIMIT :lim"
            )
            with eng.connect() as conn:
                rows = conn.execute(sql, {"lim": int(limit)}).fetchall()
            out: List[Tuple[int, float]] = []
            for r in rows:
                try:
                    mid = int(r[0]); sc = float(r[1])
                    out.append((mid, sc))
                except Exception:
                    continue
            if out:
                log.info("Top-rated fetched from %s (%s/%s): %d rows", table, id_col, score_col, len(out))
                return out
        except Exception:
            continue
    return []

def _load_top_ids_from_json(limit: int) -> List[Tuple[int, Optional[float]]]:
    """
    Fallback via JSON si DB indisponible :
    TOP_RATED_IDS_PATH (par défaut data/top_ids.json)
    JSON peut être:
      - [123,456,...] ou
      - [{"id":123,"score":97}, ...]
    """
    path = os.getenv("TOP_RATED_IDS_PATH", "data/top_ids.json")
    if not os.path.exists(path):
        return []
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        out: List[Tuple[int, Optional[float]]] = []
        for x in data:
            if isinstance(x, numbers.Integral):
                out.append((int(x), None))
            elif isinstance(x, dict):
                mid = _extract_id_from_dict(x)
                if mid is not None:
                    sc = x.get("score")
                    try:
                        scf = float(sc) if sc is not None else None
                    except Exception:
                        scf = None
                    out.append((mid, scf))
        return out[: int(limit)]
    except Exception as e:
        log.warning("Failed to read TOP_RATED_IDS_PATH: %s", e)
        return []

def _attach_local_scores(movies: List[Dict[str, Any]], id_to_pct: Dict[int, int]) -> None:
    for m in movies:
        mid = m.get("id")
        if isinstance(mid, int) and mid in id_to_pct:
            m["local_score"] = id_to_pct[mid]

# ---------- Health ----------
@app.get("/health")
def health():
    return {"ok": True}

# ---------- TMDb: Search / Details / Similar / Popular ----------
@app.get("/tmdb/search")
def tmdb_search(q: str = Query(..., min_length=1), page: int = 1):
    try:
        data = search_movie(q, page=page)
        results = [
            normalize_movie(m)
            for m in data.get("results", [])
            if (m.get("title") or m.get("original_title"))
        ]
        return {"query": q, "page": page, "results": results, "total_results": data.get("total_results")}
    except Exception as e:
        log.exception("Search failed")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}") from e

@app.get("/tmdb/details")
def tmdb_details(id: int):
    try:
        return normalize_movie(movie_details(int(id)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tmdb/similar")
def tmdb_similar(id: int, page: int = 1):
    try:
        data = similar_movies(int(id), page=page)
        results = [
            normalize_movie(m)
            for m in data.get("results", [])
            if (m.get("title") or m.get("original_title"))
        ]
        return {"id": id, "page": page, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tmdb/popular")
def tmdb_popular(page: int = 1):
    try:
        base = "https://api.themoviedb.org/3"
        params = {
            "api_key": os.getenv("TMDB_API_KEY"),
            "page": page,
            "language": os.getenv("TMDB_LANG", "fr-FR"),
        }
        r = requests.get(f"{base}/movie/popular", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = [
            normalize_movie(m)
            for m in data.get("results", [])
            if (m.get("title") or m.get("original_title"))
        ]
        return {"page": page, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Popular failed: {e}")

# ---------- Catalog: Top-rated (LOCAL DB/JSON) ----------
@app.get("/catalog/top-rated")
def catalog_top_rated(limit: int = 160):
    """
    Renvoie les films les mieux notés de TA base, hydratés TMDb + 'local_score' (0..100).
    Si DB vide/indispo -> JSON fallback (TOP_RATED_IDS_PATH ou data/top_ids.json). Sinon -> [].
    """
    try:
        limit = max(10, int(limit))
        pairs: List[Tuple[int, float]] = _query_top_rated_ids(limit)
        id_to_pct: Dict[int, int] = {}

        if not pairs:
            json_pairs = _load_top_ids_from_json(limit)
            if not json_pairs:
                return {"results": []}
            scale = _score_scale()
            for mid, sc in json_pairs:
                if sc is not None:
                    id_to_pct[int(mid)] = max(0, min(100, int(round(float(sc) / scale * 100))))
            ids = [int(mid) for mid, _ in json_pairs]
        else:
            scale = _score_scale()
            for mid, sc in pairs:
                id_to_pct[int(mid)] = max(0, min(100, int(round(float(sc) / scale * 100))))
            ids = [int(mid) for mid, _ in pairs]

        full = hydrate_ids(ids)
        if id_to_pct:
            _attach_local_scores(full, id_to_pct)

        return {"results": full}
    except Exception as e:
        log.exception("catalog_top_rated failed")
        raise HTTPException(status_code=500, detail=f"Top-rated failed: {e}") from e

# ---------- Recommendations ----------
@app.post("/recommend")
async def recommend(body: RecommendBody):
    seeds = [int(s) for s in body.seed_ids]
    if not seeds:
        raise HTTPException(status_code=400, detail="seed_ids is required")
    seed_set = set(seeds)
    try:
        candidate_ids: List[int] = []

        if HAS_DB_RECO:
            try:
                raw = await asyncio.wait_for(
                    asyncio.to_thread(recommend_db, seeds, body.k + len(seeds) * 2),
                    timeout=3.0,
                )
                candidate_ids = coerce_to_id_list(raw)
            except asyncio.TimeoutError:
                log.warning("DB recommender timeout -> fallback TMDb")
            except Exception as e:
                log.warning("DB recommender error -> fallback TMDb: %s", e)

        need = max(0, body.k + len(seeds) * 2 - len(candidate_ids))
        if need > 0:
            tmdb_ids = collect_similar_ids_from_tmdb(seeds, max_needed=need, max_pages=5)
            candidate_ids.extend(tmdb_ids)

        candidate_ids = dedup_preserve_order(candidate_ids)
        candidate_ids = [cid for cid in candidate_ids if cid not in seed_set]

        full = hydrate_ids(candidate_ids)
        full = full[: body.k]

        return {"seed_ids": seeds, "recommendations": full}

    except Exception as e:
        log.exception("Recommend failed")
        raise HTTPException(status_code=500, detail=f"Recommend failed: {e}") from e
