from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd
from scipy import sparse
from sklearn.neighbors import NearestNeighbors
from sqlalchemy import create_engine, inspect, text

# ----- CONFIG -----
DB_URL = os.getenv("DB_URL", "mysql+mysqlconnector://root:password@127.0.0.1:3306/movies")
FEATURE_WEIGHTS = {"genres": 1.0, "directors": 1.3, "actors": 1.1}
TOP_ACTORS_PER_FILM = 5
KNN_METRIC = "cosine"

_engine = None
_cache: Dict[str, Any] | None = None


@dataclass
class FilmRow:
    tmdb_id: int
    title: str
    poster_path: str | None
    overview: str | None
    directors: set
    actors: set
    genres: set


def _engine_once():
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL, pool_pre_ping=True)
    return _engine


# ---------- Helpers introspection ----------
def _inspector():
    return inspect(_engine_once())


def _table_exists(name: str) -> bool:
    try:
        return _inspector().has_table(name)
    except Exception:
        return False


def _has_cols(table: str, cols: list[str]) -> bool:
    try:
        names = {c["name"] for c in _inspector().get_columns(table)}
        return all(c in names for c in cols)
    except Exception:
        return False


def _read_sql_safe(sql: str) -> pd.DataFrame:
    try:
        return pd.read_sql(text(sql), _engine_once())
    except Exception:
        return pd.DataFrame()


# ---------- Chargement catalogue ----------
def _load_films_people_genres() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Retourne (films, directors, actors, genres) avec détection automatique des tables/colonnes disponibles."""
    # FILMS (obligatoire)
    films = _read_sql_safe("""
        SELECT f.tmdb_id, f.title, f.poster_path, f.overview
        FROM film f
    """)
    if films.empty:
        raise RuntimeError("Table 'film' introuvable ou vide : impossible de construire le catalogue.")

    # DIRECTORS
    directors = pd.DataFrame(columns=["film_tmdb_id", "director"])
    if _table_exists("directors") and _has_cols("directors", ["film_tmdb_id", "name"]):
        directors = _read_sql_safe("""
            SELECT d.film_tmdb_id AS film_tmdb_id, d.name AS director
            FROM directors d
        """)
    elif _table_exists("director") and _has_cols("director", ["film_tmdb_id", "name"]):
        directors = _read_sql_safe("""
            SELECT d.film_tmdb_id AS film_tmdb_id, d.name AS director
            FROM director d
        """)
    elif _table_exists("film_person") and _table_exists("person") and _has_cols("film_person", ["film_tmdb_id","person_tmdb_id","role"]):
        directors = _read_sql_safe("""
            SELECT fp.film_tmdb_id AS film_tmdb_id, p.name AS director
            FROM film_person fp
            JOIN person p ON p.tmdb_id = fp.person_tmdb_id
            WHERE fp.role = 'director'
        """)

    # ACTORS
    actors = pd.DataFrame(columns=["film_tmdb_id", "actor", "cast_order"])
    if _table_exists("actors") and _has_cols("actors", ["film_tmdb_id", "name"]):
        if _has_cols("actors", ["cast_order"]):
            actors = _read_sql_safe("""
                SELECT a.film_tmdb_id AS film_tmdb_id, a.name AS actor, a.cast_order
                FROM actors a
            """)
        else:
            tmp = _read_sql_safe("""
                SELECT a.film_tmdb_id AS film_tmdb_id, a.name AS actor
                FROM actors a
            """)
            if not tmp.empty:
                tmp["cast_order"] = None
                actors = tmp
    elif _table_exists("actor") and _has_cols("actor", ["film_tmdb_id", "name"]):
        tmp = _read_sql_safe("""
            SELECT a.film_tmdb_id AS film_tmdb_id, a.name AS actor
            FROM actor a
        """)
        if not tmp.empty:
            tmp["cast_order"] = None
            actors = tmp
    elif _table_exists("film_person") and _table_exists("person") and _has_cols("film_person", ["film_tmdb_id","person_tmdb_id","role"]):
        actors = _read_sql_safe("""
            SELECT fp.film_tmdb_id AS film_tmdb_id, p.name AS actor, fp.cast_order
            FROM film_person fp
            JOIN person p ON p.tmdb_id = fp.person_tmdb_id
            WHERE fp.role = 'actor'
        """)

    # GENRES
    genres = pd.DataFrame(columns=["film_tmdb_id", "genre"])
    if _table_exists("film_genre") and _table_exists("genre") and _has_cols("film_genre", ["film_tmdb_id","genre_id"]):
        genres = _read_sql_safe("""
            SELECT fg.film_tmdb_id, g.name AS genre
            FROM film_genre fg
            JOIN genre g ON g.id = fg.genre_id
        """)
    elif _table_exists("film_genres") and _has_cols("film_genres", ["film_tmdb_id","name"]):
        genres = _read_sql_safe("""
            SELECT fg.film_tmdb_id, fg.name AS genre
            FROM film_genres fg
        """)
    elif _table_exists("film") and _has_cols("film", ["tmdb_id","genres"]):
        tmp = _read_sql_safe("""
            SELECT tmdb_id AS film_tmdb_id, genres
            FROM film
            WHERE genres IS NOT NULL AND genres <> ''
        """)
        if not tmp.empty:
            rows = []
            for _, r in tmp.iterrows():
                for g in str(r["genres"]).split(","):
                    g = g.strip()
                    if g:
                        rows.append({"film_tmdb_id": int(r["film_tmdb_id"]), "genre": g})
            genres = pd.DataFrame(rows) if rows else genres

    return films, directors, actors, genres


def _prepare_rows() -> list[FilmRow]:
    films, directors, actors, genres = _load_films_people_genres()

    films["tmdb_id"] = films["tmdb_id"].astype(int)

    if not actors.empty:
        if "cast_order" in actors.columns and actors["cast_order"].notna().any():
            actors = actors.sort_values(["film_tmdb_id", "cast_order"], na_position="last")
            actors = actors.groupby("film_tmdb_id").head(TOP_ACTORS_PER_FILM)
        else:
            actors = actors.groupby("film_tmdb_id").head(TOP_ACTORS_PER_FILM)

    idx = films["tmdb_id"]

    if not directors.empty:
        dset = directors.groupby("film_tmdb_id")["director"].agg(lambda s: set(x for x in s if x)).reindex(idx)
        dset = dset.apply(lambda v: v if isinstance(v, set) else set())
    else:
        dset = pd.Series([set()] * len(idx), index=idx)

    if not actors.empty:
        aset = actors.groupby("film_tmdb_id")["actor"].agg(lambda s: set(x for x in s if x)).reindex(idx)
        aset = aset.apply(lambda v: v if isinstance(v, set) else set())
    else:
        aset = pd.Series([set()] * len(idx), index=idx)

    if not genres.empty:
        gset = genres.groupby("film_tmdb_id")["genre"].agg(lambda s: set(x for x in s if x)).reindex(idx)
        gset = gset.apply(lambda v: v if isinstance(v, set) else set())
    else:
        gset = pd.Series([set()] * len(idx), index=idx)

    rows: list[FilmRow] = []
    merged = films.set_index("tmdb_id")
    for tmdb_id, f in merged.iterrows():
        rows.append(FilmRow(
            tmdb_id=int(tmdb_id),
            title=(f.get("title") or "").strip(),
            poster_path=(f.get("poster_path") or None),
            overview=(f.get("overview") or None),
            directors=set(dset.loc[tmdb_id]) if tmdb_id in dset.index else set(),
            actors=set(aset.loc[tmdb_id]) if tmdb_id in aset.index else set(),
            genres=set(gset.loc[tmdb_id]) if tmdb_id in gset.index else set(),
        ))
    return rows


# ---------- Vectorisation ----------
def _one_hot(values: list[set]) -> Tuple[sparse.csr_matrix, list[str]]:
    uniq = sorted(set().union(*values)) if values else []
    col_index = {v: i for i, v in enumerate(uniq)}
    data, rows, cols = [], [], []
    for r, s in enumerate(values):
        for v in s:
            c = col_index.get(v)
            if c is not None:
                data.append(1.0)
                rows.append(r)
                cols.append(c)
    X = sparse.csr_matrix((data, (rows, cols)), shape=(len(values), len(uniq)), dtype="float32")
    return X, uniq


def _build_cache():
    rows = _prepare_rows()
    if not rows:
        raise RuntimeError("Catalogue vide : aucune recommandation possible.")

    G, gcols = _one_hot([r.genres for r in rows])
    D, dcols = _one_hot([r.directors for r in rows])
    A, acols = _one_hot([r.actors for r in rows])

    blocks = []
    if G.shape[1] > 0:
        blocks.append(G.multiply(FEATURE_WEIGHTS["genres"]))
    if D.shape[1] > 0:
        blocks.append(D.multiply(FEATURE_WEIGHTS["directors"]))
    if A.shape[1] > 0:
        blocks.append(A.multiply(FEATURE_WEIGHTS["actors"]))

    if not blocks:
        raise RuntimeError("Aucune feature (genres/réals/acteurs) disponible dans la base pour calculer des recommandations.")

    X = sparse.hstack(blocks, format="csr")
    knn = NearestNeighbors(metric=KNN_METRIC)
    knn.fit(X)

    id_to_row = {r.tmdb_id: i for i, r in enumerate(rows)}
    row_to_id = {i: r.tmdb_id for i, r in enumerate(rows)}

    return {
        "rows": rows,
        "X": X,
        "knn": knn,
        "id_to_row": id_to_row,
        "row_to_id": row_to_id,
        "feature_cols": {"genres": gcols, "directors": dcols, "actors": acols},
    }


def refresh_cache() -> int:
    """Reconstruit l'index KNN. Retourne le nombre de films indexés."""
    global _cache
    _cache = _build_cache()
    return len(_cache["rows"])


def _ensure_cache():
    global _cache
    if _cache is None:
        _cache = _build_cache()


def _normalize_vector(v: sparse.csr_matrix) -> sparse.csr_matrix:
    # petite normalisation L2 (évite la division par zéro)
    n = sparse.linalg.norm(v)
    if n == 0:
        return v
    return v / n


def _make_reason(rec: FilmRow, seed_rows: List[FilmRow]) -> str:
    seed_dirs = set().union(*(s.directors for s in seed_rows))
    seed_acts = set().union(*(s.actors for s in seed_rows))
    seed_genr = set().union(*(s.genres for s in seed_rows))

    common_dir = rec.directors & seed_dirs
    common_act = rec.actors & seed_acts
    common_gen = rec.genres & seed_genr

    if common_dir:
        return f"Même réalisateur : {next(iter(common_dir))}"
    if len(common_act) >= 2:
        sample = list(common_act)[:2]
        return "Acteurs en commun : " + ", ".join(sample)
    if common_act:
        return "Acteur en commun : " + next(iter(common_act))
    if common_gen:
        sample = list(common_gen)[:2]
        return "Genres proches : " + ", ".join(sample)
    return "Proximité de style et thématiques"


def recommend(seed_ids: List[int], k: int = 10) -> List[Dict[str, Any]]:
    """
    Retourne une liste de recommandations avec:
    - tmdb_id, title, poster_path, score (cosine), reason, overview
    """
    _ensure_cache()
    rows: List[FilmRow] = _cache["rows"]  # type: ignore[index]
    id_to_row = _cache["id_to_row"]       # type: ignore[index]
    X = _cache["X"]                        # type: ignore[index]
    knn: NearestNeighbors = _cache["knn"]  # type: ignore[assignment]

    seed_rows_idx = [id_to_row[i] for i in seed_ids if i in id_to_row]
    if not seed_rows_idx:
        return []

    P = sparse.csr_matrix((1, X.shape[1]), dtype="float32")
    for idx in seed_rows_idx:
        P += X[idx, :]
    P = _normalize_vector(P)

    n_neighbors = min(X.shape[0], k + len(seed_rows_idx) + 25)
    distances, indices = knn.kneighbors(P, n_neighbors=n_neighbors)
    distances, indices = distances[0], indices[0]

    seed_set = set(seed_rows_idx)
    results = []
    for dist, idx in zip(distances, indices):
        if idx in seed_set:
            continue
        r = rows[idx]
        score = float(1.0 - dist)
        results.append({
            "tmdb_id": r.tmdb_id,
            "title": r.title,
            "poster_path": r.poster_path,
            "overview": (r.overview or "")[:360].strip(),
            "reason": _make_reason(r, [rows[i] for i in seed_rows_idx]),
            "score": round(score, 4),
        })
        if len(results) >= k:
            break
    return results


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
