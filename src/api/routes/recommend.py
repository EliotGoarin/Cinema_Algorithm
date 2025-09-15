# src/api/routes/recommend.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, conlist
from typing import List, Any, Dict
from src.ml import recommender

router = APIRouter(prefix="", tags=["recommend"])

class RecommendIn(BaseModel):
    seed_ids: conlist(int, min_items=1, max_items=5)
    k: int = 10

@router.post("/recommend")
def recommend_body(payload: RecommendIn) -> Dict[str, Any]:
    try:
        results = recommender.recommend(payload.seed_ids, k=payload.k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/refresh_cache")
def refresh_cache() -> Dict[str, Any]:
    try:
        n = recommender.refresh_cache()
        return {"indexed": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def debug_stats() -> dict:
    _ensure_cache()
    rows = _cache["rows"]
    X = _cache["X"]

    has_genre = sum(1 for r in rows if r.genres)
    has_dir   = sum(1 for r in rows if r.directors)
    has_act   = sum(1 for r in rows if r.actors)

    return {
        "num_films": len(rows),
        "matrix_shape": [int(X.shape[0]), int(X.shape[1])],
        "nonzero": int(X.nnz),
        "films_with_genre": has_genre,
        "films_with_director": has_dir,
        "films_with_actor": has_act,
        "sample_row": rows[0].__dict__ if rows else None,
    }
