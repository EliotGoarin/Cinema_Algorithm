# src/api/app.py
from __future__ import annotations

import os
import logging
from typing import List, Dict, Any, Iterable
import asyncio
import numbers

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.tmdb_client import search_movie, movie_details, similar_movies

# --- Optionnel: moteur local de reco ---
try:
    from src.ml.recommender import recommend as recommend_db  # -> List[int] | List[dict]
    HAS_DB_RECO = True
except Exception:
    HAS_DB_RECO = False

# --- Logger ---
log = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

# --- App ---
app = FastAPI(title="Movie Algorithm API")

# --- CORS ---
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Models ----------
class RecommendBody(BaseModel):
    seed_ids: List[int]
    k: int = 12

# --------- Utils ----------
def normalize_movie(m: Dict[str, Any]) -> Dict[str, Any]:
    """Format stable pour le front."""
    if not m:
        return {}
    return {
        "id": m.get("id"),
        "title": m.get("title") or m.get("original_title"),
        "poster_path": m.get("poster_path"),
        "release_date": m.get("release_date"),
        "overview": m.get("overview"),
        "genres": m.get("genres"),
    }

def hydrate_ids(ids: Iterable[int]) -> List[Dict[str, Any]]:
    """Transforme une liste d'IDs en films normalisés (ignore ceux sans titre)."""
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
    """Tente de récupérer un ID TMDb depuis divers formats de dicts."""
    # essais courants: id, tmdb_id, movie_id
    for key in ("id", "tmdb_id", "movie_id"):
        if key in d and d[key] is not None:
            try:
                return int(d[key])
            except Exception:
                return None
    return None

def coerce_to_id_list(candidates: Iterable[Any]) -> List[int]:
    """Convertit une liste mixte (ints, str, dicts, numpy types) en liste d'ints TMDb."""
    ids: List[int] = []
    for x in candidates or []:
        if isinstance(x, numbers.Integral):
            ids.append(int(x))
        elif isinstance(x, str):
            try:
                ids.append(int(x))
            except ValueError:
                # chaîne non convertible -> ignore
                continue
        elif isinstance(x, dict):
            mid = _extract_id_from_dict(x)
            if mid is not None:
                ids.append(int(mid))
        else:
            # numpy types, etc.
            try:
                if isinstance(x, float) and x.is_integer():
                    ids.append(int(x))
                else:
                    # tenter cast générique
                    ids.append(int(x))  # peut lever -> on ignore
            except Exception:
                continue
    return ids

def dedup_preserve_order(seq: Iterable[int]) -> List[int]:
    """Déduplique en préservant l'ordre d'apparition."""
    seen = set()
    out: List[int] = []
    for v in seq:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out

# --------- Health ----------
@app.get("/health")
def health():
    return {"ok": True}

# --------- TMDb pass-through ----------
@app.get("/tmdb/search")
def tmdb_search(q: str = Query(..., min_length=1), page: int = 1):
    try:
        data = search_movie(q, page=page)
        results = [
            normalize_movie(m)
            for m in data.get("results", [])
            if (m.get("title") or m.get("original_title"))
        ]
        return {
            "query": q,
            "page": page,
            "results": results,
            "total_results": data.get("total_results"),
        }
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

# --------- Recommendations ----------
@app.post("/recommend")
async def recommend(body: RecommendBody):
    # seeds -> set d'ints
    seeds = [int(s) for s in body.seed_ids]
    if not seeds:
        raise HTTPException(status_code=400, detail="seed_ids is required")
    seed_set = set(seeds)

    try:
        candidate_ids: List[int] = []

        # 1) Essaye moteur local avec timeout 3s (peut renvoyer dicts/ints)
        if HAS_DB_RECO:
            try:
                raw = await asyncio.wait_for(
                    asyncio.to_thread(recommend_db, seeds, body.k + len(seeds)),
                    timeout=3.0,
                )
                candidate_ids = coerce_to_id_list(raw)
            except asyncio.TimeoutError:
                log.warning("DB recommender timeout -> fallback TMDb similar")
            except Exception as e:
                log.warning("DB recommender error -> fallback TMDb similar: %s", e)

        # 2) Fallback TMDb similar si vide
        if not candidate_ids:
            sim = similar_movies(seeds[0], page=1)
            fallback_raw = [m for m in (sim.get("results") or [])]
            candidate_ids = coerce_to_id_list(fallback_raw)

        # 3) Dédup + exclusion seeds
        candidate_ids = dedup_preserve_order(candidate_ids)
        candidate_ids = [cid for cid in candidate_ids if cid not in seed_set]

        # 4) Hydrater + limiter à k
        full = hydrate_ids(candidate_ids)
        full = full[: body.k]

        return {"seed_ids": seeds, "recommendations": full}

    except Exception as e:
        log.exception("Recommend failed")
        raise HTTPException(status_code=500, detail=f"Recommend failed: {e}") from e
