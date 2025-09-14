from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from src.ml.features import load_catalog, build_feature_matrix
from src.core.tmdb_client import similar_movies

IMG_PREFIX = "https://image.tmdb.org/t/p/w200"

_df: pd.DataFrame | None = None
_X: pd.DataFrame | None = None
_model: NearestNeighbors | None = None

def refresh_cache():
    """Recharge le catalogue + matrice de features + modèle KNN."""
    global _df, _X, _model
    _df = load_catalog()
    _X = build_feature_matrix(_df)
    if len(_X) == 0:
        _model = None
        return
    # k modèle = k demandé + marge; on prendra +10 pour réduire le bruit puis filtrer
    n_neighbors = min(max(2, len(_X)), 64)
    _model = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
    _model.fit(_X.values)

def _ensure_ready():
    if _df is None or _X is None or _model is None:
        refresh_cache()

def _neighbors_for(seed: int, pool_k: int) -> list[int]:
    """Renvoie des voisins par ID TMDB depuis la base locale (hors seed)."""
    if seed not in _X.index:
        return []
    vec = _X.loc[[seed]].values
    dists, idxs = _model.kneighbors(vec, n_neighbors=min(pool_k, len(_X)))
    ids = list(_X.index[idxs[0]])
    # le plus proche est souvent le seed lui-même → on l’exclut
    return [i for i in ids if i != seed]

def _unique_keep_order(items: Iterable[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def _rows_by_ids(ids: Iterable[int]) -> list[dict]:
    out = []
    for tmdb_id in ids:
        row = _df[_df["film_tmdb_id"] == tmdb_id]
        if row.empty:
            continue
        r = row.iloc[0]
        poster = r.get("poster_path")
        out.append({
            "tmdb_id": int(tmdb_id),
            "title": str(r["title"]),
            "poster_path": f"{IMG_PREFIX}{poster}" if poster else None
        })
    return out

def recommend(seed_ids: list[int], k: int = 10) -> list[dict]:
    """
    - Agrège des voisins locaux (KNN) sur le catalogue DB
    - Exclut strictement les seeds
    - Si < k résultats, complète via TMDB /similar (sans dupliquer, sans seeds)
    """
    _ensure_ready()
    if not seed_ids:
        return []

    # Ne garder que les seeds présents en base pour la partie KNN
    seeds_local = [i for i in seed_ids if _X is not None and i in _X.index]
    k = max(1, int(k))

    candidates: list[int] = []

    # 1) voisins locaux (pool enrichi)
    if seeds_local and _model is not None:
        pool_k = min(len(_X), max(16, 4 * k))  # large pool pour diversité
        for s in seeds_local:
            candidates += _neighbors_for(s, pool_k)
        # dédup + ordre de rencontre
        candidates = _unique_keep_order(candidates)

    # 2) enlever les seeds (toujours par ID)
    seeds_set = set(seed_ids)
    candidates = [c for c in candidates if c not in seeds_set]

    # 3) tronquer au besoin
    out_ids: list[int] = candidates[:k]

    # 4) fallback TMDB si on n’atteint pas k
    if len(out_ids) < k:
        seen = set(out_ids) | seeds_set
        for seed in seed_ids:
            try:
                data = similar_movies(seed)
                for m in data.get("results", []):
                    mid = int(m.get("id"))
                    if mid in seen:
                        continue
                    out_ids.append(mid)
                    seen.add(mid)
                    if len(out_ids) >= k:
                        break
            except Exception:
                # on ignore silencieusement le fallback défaillant pour un seed
                pass
            if len(out_ids) >= k:
                break

    # 5) mapper en objets (si film pas en DB, on renvoie au moins id+titre sans poster)
    local_map = {int(r["film_tmdb_id"]): r for _, r in _df.iterrows()}
    out: list[dict] = []
    for mid in out_ids[:k]:
        if mid in local_map:
            r = local_map[mid]
            poster = r.get("poster_path")
            out.append({
                "tmdb_id": mid,
                "title": str(r["title"]),
                "poster_path": f"{IMG_PREFIX}{poster}" if poster else None
            })
        else:
            # minimal depuis fallback (le front pourra recharger info TMDB si besoin)
            out.append({"tmdb_id": mid})

    return out
