import numpy as np
from sklearn.neighbors import NearestNeighbors
from src.ml.features import load_catalog, build_feature_matrix

IMG_PREFIX = "https://image.tmdb.org/t/p/w200"

_df = None
_X  = None
_model = None

def refresh_cache():
    global _df, _X, _model
    _df = load_catalog()
    _X  = build_feature_matrix(_df)
    n_neighbors = min(len(_X), 11)  # k=10 -> k+1 voisins
    _model = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
    _model.fit(_X.values)

def _ensure_ready():
    if any(v is None for v in (_df, _X, _model)):
        refresh_cache()

def recommend(seed_ids: list[int], k: int = 10):
    _ensure_ready()
    if not seed_ids:
        return []

    seeds = [i for i in seed_ids if i in _X.index]
    if not seeds:
        return []

    vec = _X.loc[seeds].mean(axis=0).to_numpy().reshape(1, -1)
    dist, idxs = _model.kneighbors(vec)
    idxs = idxs.flatten().tolist()
    ids  = _X.index.to_numpy()[idxs].tolist()

    out, seen = [], set()
    for tmdb_id in ids:
        if tmdb_id in seeds or tmdb_id in seen:
            continue
        row = _df[_df["film_tmdb_id"] == tmdb_id].iloc[0]
        poster = row.get("poster_path")
        out.append({
            "tmdb_id": int(tmdb_id),
            "title": str(row["title"]),
            "poster_path": f"{IMG_PREFIX}{poster}" if poster else None
        })
        seen.add(tmdb_id)
        if len(out) >= k:
            break
    return out
