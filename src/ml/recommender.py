# src/ml/recommender.py
import os
import pandas as pd
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from sklearn.neighbors import NearestNeighbors
from scipy import sparse
from sqlalchemy import create_engine, text

# ----- CONFIG -----
DB_URL = os.getenv("DB_URL", "mysql+mysqlconnector://root:password@localhost/movies")
FEATURE_WEIGHTS = {
    "genres": 1.0,
    "directors": 1.3,
    "actors": 1.1,
}
TOP_ACTORS_PER_FILM = 5  # limite acteurs par film pour éviter des vecteurs énormes
KNN_METRIC = "cosine"

_engine = None
_cache = None  # type: Dict[str, Any]


@dataclass
class FilmRow:
    tmdb_id: int
    title: str
    poster_path: str | None
    overview: str | None
    # sets
    directors: set
    actors: set
    genres: set


def _engine_once():
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL, pool_pre_ping=True)
    return _engine


def _try_read_sql_candidates(sqls: List[str]) -> pd.DataFrame:
    """Essaie plusieurs variantes de requêtes/tables (selon que tu utilises 'actor' ou 'actors', etc.)."""
    eng = _engine_once()
    last_err = None
    for s in sqls:
        try:
            return pd.read_sql(text(s), eng)
        except Exception as e:
            last_err = e
    raise last_err if last_err else RuntimeError("No SQL worked.")


def _load_films_people_genres() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Charge films, acteurs, réalisateurs, genres depuis la DB (tolérant sur les noms de tables)."""
    films = _try_read_sql_candidates([
        """
        SELECT f.tmdb_id, f.title, f.poster_path, f.overview
        FROM film f
        """,
    ])
    # Réalisateurs
    directors = _try_read_sql_candidates([
        # variante 1: table 'directors' (film_tmdb_id, name)
        """
        SELECT d.film_tmdb_id AS film_tmdb_id, d.name AS director
        FROM directors d
        """,
        # variante 2: table 'director' (film_tmdb_id, name)
        """
        SELECT d.film_tmdb_id AS film_tmdb_id, d.name AS director
        FROM director d
        """,
        # variante 3: table 'person' + role
        """
        SELECT fp.film_tmdb_id AS film_tmdb_id, p.name AS director
        FROM film_person fp
        JOIN person p ON p.tmdb_id = fp.person_tmdb_id
        WHERE fp.role = 'director'
        """,
    ])

    # Acteurs
    actors = _try_read_sql_candidates([
        # variante 1: table 'actors' (film_tmdb_id, name, cast_order)
        """
        SELECT a.film_tmdb_id AS film_tmdb_id, a.name AS actor, a.cast_order
        FROM actors a
        """,
        # variante 2: table 'actor' (film_tmdb_id, name)
        """
        SELECT a.film_tmdb_id AS film_tmdb_id, a.name AS actor, NULL as cast_order
        FROM actor a
        """,
        # variante 3: table 'film_person' + role
        """
        SELECT fp.film_tmdb_id AS film_tmdb_id, p.name AS actor, fp.cast_order
        FROM film_person fp
        JOIN person p ON p.tmdb_id = fp.person_tmdb_id
        WHERE fp.role = 'actor'
        """,
    ])

    # Genres
    genres = _try_read_sql_candidates([
        # film_genre + genre(name)
        """
        SELECT fg.film_tmdb_id, g.name AS genre
        FROM film_genre fg
        JOIN genre g ON g.id = fg.genre_id
        """,
        # film_genres avec nom déjà présent
        """
        SELECT fg.film_tmdb_id, fg.name AS genre
        FROM film_genres fg
        """,
    ])

    return films, directors, actors, genres


def _prepare_rows() -> list[FilmRow]:
    films, directors, actors, genres = _load_films_people_genres()

    # Normalisation types
    films["tmdb_id"] = films["tmdb_id"].astype(int)

    # Acteurs: limiter au TOP_ACTORS_PER_FILM selon cast_order si dispo
    if "cast_order" in actors.columns and actors["cast_order"].notna().any():
        actors = actors.sort_values(["film_tmdb_id", "cast_order"], na_position="last")
        actors = actors.groupby("film_tmdb_id").head(TOP_ACTORS_PER_FILM)
    else:
        actors = actors.groupby("film_tmdb_id").head(TOP_ACTORS_PER_FILM)

    # Agrégations en sets
    dset = directors.groupby("film_tmdb_id")["director"].agg(lambda s: set(x for x in s if x)).reindex(films["tmdb_id"]).fillna(set())
    aset = actors.groupby("film_tmdb_id")["actor"].agg(lambda s: set(x for x in s if x)).reindex(films["tmdb_id"]).fillna(set())
    gset = genres.groupby("film_tmdb_id")["genre"].agg(lambda s: set(x for x in s if x)).reindex(films["tmdb_id"]).fillna(set())

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


def _one_hot(values: list[set]) -> Tuple[sparse.csr_matrix, list[str]]:
    """
    Transforme une liste de sets (ex: genres par film) en matrice one-hot sparse + liste des colonnes.
    """
    # dictionnaire de feature -> colonne
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

    # Vecteurs
    G, gcols = _one_hot([r.genres for r in rows])
    D, dcols = _one_hot([r.directors for r in rows])
    A, acols = _one_hot([r.actors for r in rows])

    X = sparse.hstack([
        G.multiply(FEATURE_WEIGHTS["genres"]),
        D.multiply(FEATURE_WEIGHTS["directors"]),
        A.multiply(FEATURE_WEIGHTS["actors"]),
    ], format="csr")

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
    # normalisation L2 (évite la division par zéro)
    norm = sparse.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


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
    rows: List[FilmRow] = _cache["rows"]
    id_to_row = _cache["id_to_row"]
    X = _cache["X"]
    knn: NearestNeighbors = _cache["knn"]

    seed_rows_idx = [id_to_row[i] for i in seed_ids if i in id_to_row]
    if not seed_rows_idx:
        return []

    P = sparse.csr_matrix((1, X.shape[1]), dtype="float32")
    for idx in seed_rows_idx:
        P += X[idx, :]
    P = _normalize_vector(P)

    # On demande plus large pour pouvoir filtrer les seeds ensuite
    n_neighbors = min(X.shape[0], k + len(seed_rows_idx) + 25)
    distances, indices = knn.kneighbors(P, n_neighbors=n_neighbors)
    distances, indices = distances[0], indices[0]

    seed_set = set(seed_rows_idx)
    # Convertir distance cosine -> similarité (score)
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
