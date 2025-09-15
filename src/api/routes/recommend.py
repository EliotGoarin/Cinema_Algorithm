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
